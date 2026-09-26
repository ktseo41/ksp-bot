"""Offline checks of the pure helpers in kspbot.flight (no KSP): `uv run python -m unittest discover tests`."""
import math
import time
import unittest
from types import SimpleNamespace as NS

from kspbot import flight as F

F.say = lambda msg, *a, **kw: None  # never reach for the game (core.say would connect to show the message)
F.FAR_SETTLE = 0.0


class FarCorrection(unittest.TestCase):
    def test_cost_terms(self):
        # 120 km wanted, pass at 170 km prograde, inc 4 wanted 0: 2 m/s + 0.02 x 50 km + 0.3 x 4 deg
        self.assertAlmostEqual(F._far_cost(2.0, 170e3, 4.0, 120e3, 0.02, inc_to=0.0, retro=False), 2 + 1 + 1.2)
        # the same pass retrograde (inc 176) with a prograde pass wanted: ruled out
        self.assertGreater(F._far_cost(2.0, 170e3, 176.0, 120e3, 0.02, inc_to=0.0, retro=False), 1000)
        # no side asked: only the inclination term counts
        self.assertAlmostEqual(F._far_cost(1.0, 120e3, 30.0, 120e3, 0.02, min_inc=40.0), 1 + 3.0)
        self.assertAlmostEqual(F._far_cost(1.0, 120e3, 150.0, 120e3, 0.02, min_inc=20.0), 1.0)

    def test_pattern_search_finds_minimum(self):
        f = lambda x: (x[0] - 1.3) ** 2 + 4 * (x[1] + 0.4) ** 2 + (x[2] - 0.05) ** 2
        c, x = F._pattern_search(f, [0, 0, 0], [0.1] * 3, [1.0] * 3, [0.001] * 3, iters=200)
        self.assertLess(c, 1e-4)
        for a, b in zip(x, (1.3, -0.4, 0.05)):
            self.assertAlmostEqual(a, b, delta=0.01)

    def test_pattern_search_step_cap(self):
        # a cost that falls forever along +x: the step may grow only to max_steps per iteration
        seen = []

        def f(x):
            seen.append(x[0])
            return -x[0]
        F._pattern_search(f, [0.0], [0.1], [0.5], [0.01], iters=20)
        self.assertLessEqual(max(b - a for a, b in zip(seen, seen[1:])), 0.5 + 1e-9)

    def test_far_search_on_a_fake_patch(self):
        # a linear "KSP": pe (km) and inc move with the burn; the zero node passes at 10,000 km, inc 3
        class Body:
            name = "Eve"
            orbit = type("O", (), {"body": type("B", (), {"name": "Sun"})()})()

        class Patch:
            body, next_orbit = Body(), None

            def __init__(self, n):
                self.periapsis_altitude = (10000 - 400 * n.prograde + 50 * n.radial) * 1000.0
                inc = 3 - 2 * n.normal
                self.inclination = math.radians(inc % 360 if inc >= 0 else -inc)

        class Node:
            prograde = normal = radial = 0.0
            orbit = property(lambda self: Patch(self))

        n = Node()
        r = F._far_search(n, Body(), 120e3, [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)], (0.8, 0.8, 0.8), 60.0, 0.02,
                          inc_to=0.0, retro=False)
        self.assertIsNotNone(r)
        dv, pe, inc = r
        self.assertAlmostEqual(pe / 1000, 120, delta=10)
        self.assertLess(inc, 1.0)
        # the least-dv burn is 24.3 prograde / -3.0 radial / 1.5 normal (24.5 m/s); a compass search stalls on the
        # diagonal pe valley a little above that (29 here): fine, the cap and _approve bound it
        self.assertLess(dv, 1.3 * 24.5)


class CaptureLink(unittest.TestCase):
    def test_ray_clearance(self):
        R = 700e3
        # Kerbin far along +x, the vessel 1000 km beside the body's centre line: clears by 300 km
        self.assertAlmostEqual(F._ray_clearance((0, 1000e3, 0), (1e10, 1000e3, 0), (0, 0, 0), R), 300e3, delta=1)
        # the vessel behind the body: blocked
        self.assertLess(F._ray_clearance((-1000e3, 100e3, 0), (1e10, 0, 0), (0, 0, 0), R), 0)
        # the body behind the vessel (Kerbin on the other side): clear by the vessel's own height
        self.assertAlmostEqual(F._ray_clearance((1000e3, 0, 0), (1e10, 0, 0), (0, 0, 0), R), 300e3, delta=1)

    def test_blackout_start(self):
        link = lambda t: (1.0 if t < 1003.2 or t > 1140 else -1.0, "Moho")
        tb, worst = F._blackout(link, 900, 1200)
        self.assertAlmostEqual(tb, 1003.2, delta=0.01)
        self.assertEqual(worst[0], -1.0)
        # already blocked at the window start: traced back to where it began
        tb, _ = F._blackout(link, 1050, 1100)
        self.assertAlmostEqual(tb, 1003.2, delta=0.01)
        self.assertIsNone(F._blackout(link, 1150, 1300)[0])

    def test_shift_earlier(self):
        # burn 100 s centred on t (lead 50); blackout 1000..1140; the burn must end by 975
        blackout = lambda a, b: 1000.0 if a < 1140 and b > 1000 else None
        window = lambda t: (t - 50, t + 50)
        t = F._link_safe_centre(1000.0, window, blackout, earliest=0.0)
        self.assertLessEqual(window(t)[1], 975.0)
        self.assertGreater(window(t)[1], 970.0)
        # a burn that grows off the periapsis (+0.5 s per s earlier) still converges
        window2 = lambda t: (t - 50 - 0.25 * (1000 - t), t + 50 + 0.25 * (1000 - t))
        t2 = F._link_safe_centre(1000.0, window2, blackout, earliest=0.0)
        self.assertLessEqual(window2(t2)[1], 975.0)
        # no room before the blackout: refused
        self.assertIsNone(F._link_safe_centre(1000.0, window, blackout, earliest=900.0))
        # clear: unchanged
        self.assertEqual(F._link_safe_centre(800.0, window, blackout, earliest=0.0), 800.0)


class Deorbit(unittest.TestCase):
    def test_toward_keeps_the_sign(self):
        k, h = (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)
        for sd in ((0.0, 1.0, 0.0), (0.0, -1.0, 0.0)):  # the Sun on either side of k
            side = math.copysign(1.0, F._plane_angle(k, sd, h))
            for deg in (30.0, -30.0):
                r = F._toward(k, sd, h, deg)
                self.assertAlmostEqual(F._plane_angle(k, r, h), side * deg, places=6)
                # sunward (deg > 0) comes closer to the Sun, anti-sunward farther away
                closer = F._dot(r, sd) > F._dot(k, sd)
                self.assertEqual(closer, deg > 0)

    def test_elevation(self):
        self.assertAlmostEqual(F._elevation((0, 0, 5), (1, 0, 1)), 45.0)
        self.assertAlmostEqual(F._elevation((0, 0, 1), (0, 0, -3)), -90.0)
        self.assertAlmostEqual(F._elevation((0, 2, 0), (1, 0, 0)), 0.0)


class LandScience(unittest.TestCase):
    def test_background_sets_do_not_block(self):
        calls = []

        def slow(v, label, queue):
            time.sleep(0.5)  # _entry_science waits up to 8 s for the reports
            calls.append(label)
        saved = F._entry_science, F._await_queue, F.do_science, F.ut
        F._entry_science, F.ut = slow, lambda: 0.0
        F._await_queue = lambda v, q: calls.append("settle")
        F.do_science = lambda **kw: calls.append("landed")
        try:
            v = NS(situation=NS(name="sub_orbital"), orbit=NS(body=NS(flying_high_altitude_threshold=18000)))
            fl = NS(mean_altitude=60000)
            tick, finish = F._entry_science_bg(v, fl)
            worst = 0.0
            for name, alt in (("sub_orbital", 60000), ("flying", 30000), ("flying", 25000), ("flying", 12000),
                              ("flying", 5000)):
                v.situation.name, fl.mean_altitude = name, alt
                for _ in range(12):
                    t0 = time.time()
                    tick()
                    worst = max(worst, time.time() - t0)
                    time.sleep(0.1)
            self.assertLess(worst, 0.05)
            finish()
            self.assertEqual(calls, ["flying high", "flying low", "settle", "landed"])
        finally:
            F._entry_science, F._await_queue, F.do_science, F.ut = saved


if __name__ == "__main__":
    unittest.main()
