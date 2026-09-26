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


class AimPointTurn(unittest.TestCase):
    """_turn_angles: the plane turns about a line in it (the line to the target inside its SOI) by the least angle
    that gives inc_to. Test frame right-handed, pole +z; KSP's normal sign is handled by the caller."""
    pole = (0.0, 0.0, 1.0)

    @staticmethod
    def plane(inc, lan=0.0, u=0.0):
        """(unit normal, unit in-plane direction at argument of latitude u), angles in deg."""
        i, l = math.radians(inc), math.radians(lan)
        n = (math.sin(i) * math.sin(l), -math.sin(i) * math.cos(l), math.cos(i))
        return n, F.kepler.rotate((math.cos(l), math.sin(l), 0.0), n, math.radians(u))

    def inc_after(self, n0, axis, phi):
        n = F.kepler.rotate(n0, axis, phi)
        return math.degrees(math.acos(max(-1.0, min(1.0, F._dot(n, self.pole)))))

    def test_mun_sat_turn_is_28_not_180(self):
        # Mun Sat 1: pass at inc 174 (retrograde), contract plane 146: turning about the node line takes 28 deg
        n0, axis = self.plane(174.0, lan=30.0, u=0.0)
        c = F._turn_angles(n0, axis, self.pole, 146.0)
        self.assertEqual(len(c), 2)
        self.assertAlmostEqual(abs(math.degrees(c[0][0])), 28.0, places=6)
        for phi, reached in c:  # both ways reach it, and the plane really is at 146 after the turn
            self.assertAlmostEqual(reached, 146.0, places=6)
            self.assertAlmostEqual(self.inc_after(n0, axis, phi), 146.0, places=6)
        # at the SOI edge (v_t ~154 m/s) that is ~75 m/s, not the 371 of the flip
        self.assertAlmostEqual(F._turn_estimate(154.0, c[0][0], 352.0, 0.0, 2.43e6), 74.5, delta=0.5)
        self.assertGreater(F._turn_estimate(154.0, math.pi, 352.0, 0.0, 2.43e6), 300)

    def test_axis_off_the_node_line(self):
        # the line to the target 40 deg past the node: a longer turn, still retrograde, still < 90 deg
        n0, axis = self.plane(174.0, lan=275.0, u=40.0)
        c = F._turn_angles(n0, axis, self.pole, 146.0)
        phi, reached = c[0]
        self.assertAlmostEqual(reached, 146.0, places=6)
        self.assertAlmostEqual(self.inc_after(n0, axis, phi), 146.0, places=6)
        self.assertLess(abs(math.degrees(phi)), 60.0)
        self.assertLessEqual(abs(c[0][0]), abs(c[1][0]))

    def test_inc_to_zero_from_three_is_small(self):
        # Eve 2: pass at inc 3, wants 0; the line to Eve on the node line: a 3 deg turn, a few m/s
        n0, axis = self.plane(3.0, lan=100.0, u=0.0)
        phi, reached = F._turn_angles(n0, axis, self.pole, 0.0)[0]
        self.assertAlmostEqual(abs(math.degrees(phi)), 3.0, places=4)
        self.assertAlmostEqual(reached, 0.0, places=4)
        self.assertLess(F._turn_estimate(100.0, phi, 900.0, 0.0, 85e6), 6.0)
        # 60 deg past the node the line to Eve is 2.6 deg off the equator: 0 is out of reach, the closest (2.6,
        # prograde) costs a turn under 3 deg, never a flip
        n0, axis = self.plane(3.0, lan=100.0, u=60.0)
        c = F._turn_angles(n0, axis, self.pole, 0.0)
        self.assertEqual(len(c), 1)
        phi, reached = c[0]
        dec = math.degrees(math.asin(abs(F._dot(axis, self.pole))))
        self.assertAlmostEqual(reached, dec, places=6)
        self.assertAlmostEqual(self.inc_after(n0, axis, phi), dec, places=6)
        self.assertLess(abs(math.degrees(phi)), 3.0)

    def test_side_kept_when_out_of_reach(self):
        # retrograde 174 asked for 179 with the axis 3.9 deg off the equator: closest on the retrograde side
        n0, axis = self.plane(174.0, u=40.0)
        (phi, reached), = F._turn_angles(n0, axis, self.pole, 179.0)
        self.assertGreater(reached, 170.0)
        self.assertAlmostEqual(self.inc_after(n0, axis, phi), reached, places=6)
        # no turn needed: zero
        n0, axis = self.plane(20.0, u=10.0)
        self.assertAlmostEqual(F._turn_angles(n0, axis, self.pole, 20.0)[0][0], 0.0, places=6)

    def seed_inside(self, mu, R, vinf, pe_alt, inc, r_now, inc_to, lan=275.0, argpe=40.0):
        """_aim_point_seed inside the SOI on a fake KSP: two-body patches (kepler), kRPC's left-handed frame
        (y = north: components (x, z, y) of a right-handed state), node axes prograde / normal / radial."""
        K = lambda p: (p[0], p[2], p[1])  # right-handed <-> kRPC (a swap: its own inverse)
        body = NS(name="Mun", gravitational_parameter=mu, equatorial_radius=R, non_rotating_reference_frame="f")

        class Patch:
            def __init__(self, kep):
                self.k, self.body, self.next_orbit = kep, body, None
                self.inclination, self.semi_major_axis, self.eccentricity = kep.inc, kep.a, kep.e
                self.periapsis_altitude = kep.periapsis - R

            def position_at(self, t, frame):
                return K(self.k.position(t))

        rp = R + pe_alt
        a = -mu / vinf ** 2
        e = 1 - rp / a
        hyp = F.kepler.Orbit(mu, a, e, math.radians(inc), math.radians(lan), math.radians(argpe), 0.0, 0.0)
        nu = -math.acos((a * (1 - e * e) / r_now - 1) / e)  # inbound at r_now
        r0, v0 = hyp.state_at_nu(nu)
        now = Patch(F.kepler.Orbit.from_state(mu, r0, v0, 0.0))

        class Node:
            ut = 120.0
            prograde = normal = radial = 0.0

            def axes(self):
                r, v = now.k.state(self.ut)
                pg = F._norm(v)
                nm = F._norm(F._cross(r, v))
                return pg, nm, F._cross(pg, nm)

            def dv(self):
                return tuple(self.prograde * a + self.normal * b + self.radial * c for a, b, c in zip(*self.axes()))

            def burn_vector(self, frame):
                return K(self.dv())

            delta_v = property(lambda self: math.sqrt(F._dot(self.dv(), self.dv())))

            @property
            def orbit(self):
                r, v = now.k.state(self.ut)
                return Patch(F.kepler.Orbit.from_state(mu, r, tuple(x + y for x, y in zip(v, self.dv())), self.ut))

        saved = F.vessel, F._node_cost.__globals__["time"].sleep
        F.vessel = lambda: NS(orbit=now)
        F._node_cost.__globals__["time"].sleep = lambda s: None
        try:
            node = Node()
            cost = lambda n: F._node_cost(n, body, pe_alt, None, inc_to)
            dv, est = F._aim_point_seed(node, body, pe_alt, cost, inc_to)
            return node, dv, est
        finally:
            F.vessel, F._node_cost.__globals__["time"].sleep = saved

    def test_seed_on_a_fake_patch(self):
        # Mun Sat 1 at the Mun SOI edge: v_inf 352, pe 458 km, inc 174 -> 146: a turn of ~28-40 deg, not the flip
        node, dv, est = self.seed_inside(6.5138398e10, 200e3, 352.0, 458e3, 174.0, 2.4e6, 146.0)
        o = node.orbit
        self.assertAlmostEqual(math.degrees(o.inclination), 146.0, delta=0.05)
        self.assertAlmostEqual(o.periapsis_altitude, 458e3, delta=100)  # a pure turn: same pe
        self.assertAlmostEqual(dv, est, delta=0.01 * est)
        self.assertLess(dv, 150.0)
        # Eve 2 inside Eve's SOI: inc 3 -> 0 (or the closest the line to Eve allows): a few m/s
        node, dv, est = self.seed_inside(8.1717302e12, 700e3, 900.0, 120e3, 3.0, 80e6, 0.0, lan=100.0, argpe=0.0)
        self.assertLess(math.degrees(node.orbit.inclination), 3.0)
        self.assertLess(dv, 10.0)


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
