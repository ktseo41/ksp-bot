"""Offline checks of the pure helpers in kspbot.flight (no KSP): `uv run python -m unittest discover tests`."""
import math
import unittest

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


if __name__ == "__main__":
    unittest.main()
