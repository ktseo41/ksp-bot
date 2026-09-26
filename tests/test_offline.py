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


class MatchOrbit(unittest.TestCase):
    MUN = 6.5138398e10

    def test_argpe_off_like_ksp(self):
        # Mun Sat 1 after match-orbit: 17.8 deg off (window 3 % = 10.8)
        self.assertAlmostEqual(F._argpe_off(146.05, 275.9, 195.7, 146.04, 275.87, 177.93), 17.77, places=2)
        self.assertAlmostEqual(F._argpe_off(146.0, 275.9, 359.0, 146.0, 275.9, 1.0), 2.0, places=6)
        # the Eve contract (inc 0, LAN 0, argPe 330.23): KSP compares LAN + argPe; our LAN 100 is fine
        self.assertAlmostEqual(F._argpe_off(0.3, 100.0, 230.23, 0.0, 0.0, 330.23), 0.0, places=6)
        self.assertAlmostEqual(F._argpe_off(0.3, 100.0, 330.23, 0.0, 0.0, 330.23), 100.0, places=6)
        # retrograde equatorial: LAN - argPe
        self.assertAlmostEqual(F._argpe_off(179.6, 50.0, 20.0, 180.0, 0.0, 330.0), 0.0, places=6)

    def test_target_periapsis_on_our_orbit(self):
        pe = lambda i, l, w: F.kepler.Orbit(1.0, 1.0, 0.1, *map(math.radians, (i, l, w)), 0.0, 0.0).P
        # same plane: the argument of latitude is the target's argPe
        u = F._arg_of(math.radians(146.04), math.radians(275.87), pe(146.04, 275.87, 177.93))
        self.assertAlmostEqual(math.degrees(u) % 360, 177.93, places=6)
        # near the equator with our LAN at 100: 330.23 - 100, not 330.23 (the Eve 2 plan's gap 9)
        u = F._arg_of(math.radians(0.3), math.radians(100.0), pe(0.0, 0.0, 330.23))
        self.assertAlmostEqual(math.degrees(u) % 360, 230.23, delta=0.01)

    def test_apsides_turn_keeps_the_shape(self):
        # Mun Sat 1's hand fix: 457.9 x 746.7 km, argPe 195.7 -> 177.93: ~16 m/s radial at either crossing
        R, mu = 200e3, self.MUN
        rp, ra = R + 457.9e3, R + 746.7e3
        a, e = (rp + ra) / 2, (ra - rp) / (ra + rp)
        o = F.kepler.Orbit(mu, a, e, math.radians(146.05), math.radians(275.9), math.radians(195.7), 0.0, 0.0)
        dw = math.radians(177.93 - 195.7)
        turns = F._apsides_turns(mu, a * (1 - e * e), e, dw)
        self.assertEqual(len(turns), 2)
        for nu, dvr in turns:
            self.assertAlmostEqual(abs(dvr), 16.0, delta=1.0)
            r, v = o.state_at_nu(nu)
            n = F.kepler.Orbit.from_state(mu, r, tuple(x + dvr * y for x, y in zip(v, F._norm(r))), 0.0)
            self.assertAlmostEqual(math.degrees(n.argpe), 177.93, places=4)
            self.assertAlmostEqual(n.e, e, places=9)
            self.assertAlmostEqual(n.a, a, delta=1e-3)
            self.assertAlmostEqual(math.degrees(n.lan), 275.9, places=6)

    def test_placement_plans(self):
        # Eve 2's capture orbit, periapsis longitude 140 vs the contract's 330.23: our apoapsis + a turn is cheapest
        mu, R = 8.1717302e12, 700e3
        rp0, ra0 = R + 120e3, R + 19131e3
        sma, ecc = 18868437.0, 0.05102
        plans = F._placement_plans(mu, (rp0 + ra0) / 2, (ra0 - rp0) / (ra0 + rp0), math.radians(140.0),
                                   sma * (1 - ecc), sma * (1 + ecc), math.radians(330.23), True)
        self.assertEqual(plans[0][5], "at our apoapsis")
        self.assertLess(plans[0][0], 550)
        direct = [p for p in plans if p[5] == "at the target's periapsis"][0]
        self.assertGreater(direct[0], 800)
        self.assertEqual(direct[4], 0.0)
        # argPe ignored (e <= 0.05): no turn is costed
        plans = F._placement_plans(mu, (rp0 + ra0) / 2, (ra0 - rp0) / (ra0 + rp0), math.radians(140.0),
                                   sma * 0.97, sma * 1.03, math.radians(330.23), False)
        self.assertTrue(all(p[4] == 0.0 for p in plans))

    def placed(self, mu, R, ours, target):
        """match_orbit's burns 1 and 2 on two-body orbits: horizontal at the target's apoapsis and periapsis
        directions (found on our orbit by _arg_of). ours: (pe alt, ap alt, inc, lan, argpe); target: (inc, lan,
        argpe, sma, ecc)."""
        rp0, ra0 = R + ours[0], R + ours[1]
        o = F.kepler.Orbit(mu, (rp0 + ra0) / 2, (ra0 - rp0) / (ra0 + rp0), *map(math.radians, ours[2:]), 0.0, 0.0)
        ti, tl, tw, sma, ecc = target
        rp, ra = sma * (1 - ecc), sma * (1 + ecc)
        P = F.kepler.Orbit(mu, sma, ecc, *map(math.radians, (ti, tl, tw)), 0.0, 0.0).P
        for off, far in ((math.pi, rp), (0.0, ra)):
            nu = F._arg_of(o.inc, o.lan, P) + off - o.argpe
            r, v = o.state_at_nu(nu)
            rr = math.sqrt(F._dot(r, r))
            dv = F._horizontal_dv(r, v, math.sqrt(mu * (2 / rr - 2 / (rr + far))))
            o = F.kepler.Orbit.from_state(mu, r, tuple(x + y for x, y in zip(v, dv)), 0.0)
        return o, rp, ra

    def test_burns_place_the_periapsis(self):
        # Mun Sat 1 from its capture orbit (429 x 778 km) in the contract plane
        tgt = (146.04, 275.87, 177.93, 803347.0, 0.181)
        o, rp, ra = self.placed(self.MUN, 200e3, (429e3, 778e3, 146.04, 275.87, 150.0), tgt)
        self.assertAlmostEqual(o.periapsis, rp, delta=1.0)
        self.assertAlmostEqual(o.apoapsis, ra, delta=1.0)
        self.assertLess(F._argpe_off(*map(math.degrees, (o.inc, o.lan, o.argpe)), *tgt[:3]), 0.01)
        # the Eve 2 contract from a 120 x 19,131 km capture orbit at inc 0.3, LAN 100 (gap 9: LAN + argPe)
        tgt = (0.0, 0.0, 330.23, 18868437.0, 0.05102)
        o, rp, ra = self.placed(8.1717302e12, 700e3, (120e3, 19131e3, 0.3, 100.0, 40.0), tgt)
        self.assertAlmostEqual(o.periapsis, rp, delta=1.0)
        self.assertAlmostEqual(o.apoapsis, ra, delta=1.0)
        self.assertLess(F._argpe_off(*map(math.degrees, (o.inc, o.lan, o.argpe)), *tgt[:3]), 0.01)

    def fly_match(self, mu, R, ours, target, window):
        """match_orbit end to end on a fake KSP (two-body patches, kRPC's left-handed frame, burns exact at the
        node). ours: (pe alt, ap alt, inc, lan, argpe, true anomaly now); returns (final orbit, burns in m/s)."""
        K = lambda p: (p[0], p[2], p[1])
        body = NS(name="Body", gravitational_parameter=mu, equatorial_radius=R, non_rotating_reference_frame="f",
                  orbit=NS(body=NS(name="Kerbin", orbit=None)), has_atmosphere=False)
        clock = [0.0]

        class Orb:
            def __init__(self, k):
                self.k, self.body = k, body
                self.inclination, self.longitude_of_ascending_node = k.inc, k.lan
                self.argument_of_periapsis, self.eccentricity, self.semi_major_axis = k.argpe, k.e, k.a
                self.period, self.periapsis, self.apoapsis = k.period, k.periapsis, k.apoapsis
                self.periapsis_altitude, self.apoapsis_altitude = k.periapsis - R, k.apoapsis - R
                self.time_to_periapsis = k.time_of_nu(0.0, after=clock[0]) - clock[0]
                self.time_to_apoapsis = k.time_of_nu(math.pi, after=clock[0]) - clock[0]

            def ut_at_true_anomaly(self, nu):
                return self.k.time_of_nu(nu, after=clock[0])

            def radius_at(self, t):
                return self.k.radius_at(t)

            def position_at(self, t, frame):
                return K(self.k.position(t))

        rp0, ra0 = R + ours[0], R + ours[1]
        k0 = F.kepler.Orbit(mu, (rp0 + ra0) / 2, (ra0 - rp0) / (ra0 + rp0), *map(math.radians, ours[2:5]), 0.0, 0.0)
        state = {"o": Orb(F.kepler.Orbit.from_state(mu, *k0.state_at_nu(math.radians(ours[5])), 0.0))}

        class Node:
            def __init__(self, t, p=0.0, n=0.0, r=0.0):
                self.ut, self.prograde, self.normal, self.radial = t, p, n, r
                self.base = state["o"]

            def dv(self):
                r, v = self.base.k.state(self.ut)
                pg, nm = F._norm(v), F._norm(F._cross(r, v))
                return tuple(self.prograde * x + self.normal * y + self.radial * z
                             for x, y, z in zip(pg, nm, F._cross(pg, nm)))

            def burn_vector(self, frame):
                return K(self.dv())

            def remove(self):
                pass

            delta_v = property(lambda self: math.sqrt(F._dot(self.dv(), self.dv())))

            @property
            def orbit(self):
                r, v = self.base.k.state(self.ut)
                return Orb(F.kepler.Orbit.from_state(mu, r, tuple(x + y for x, y in zip(v, self.dv())), self.ut))

        burns = []

        def execute(node, **kw):
            burns.append(node.delta_v)
            clock[0] = node.ut
            state["o"] = node.orbit
        names = ("ut", "vessel", "_crewed", "_approve", "execute_node", "burn_lead", "burn_time")
        saved = [getattr(F, n) for n in names]
        class Vessel:
            control = NS(add_node=Node)
            orbit = property(lambda self: state["o"])
        v = Vessel()
        F.ut, F.vessel, F._crewed = lambda: clock[0], lambda: v, lambda v: True
        F._approve, F.execute_node = (lambda node, expect, *a, **kw: None), execute
        F.burn_lead, F.burn_time = lambda v, dv: 0.0, lambda v, dv: 1.0
        try:
            F.match_orbit(*target, window=window)
        finally:
            for n, f in zip(names, saved):
                setattr(F, n, f)
        return state["o"], burns

    def test_match_orbit_on_a_fake_ksp(self):
        # Mun Sat 1 after its plane change (429 x 778 km in the contract plane): the argPe lands without a rotation
        tgt = (146.04, 275.87, 177.93, 803347.0, 0.181)
        o, burns = self.fly_match(self.MUN, 200e3, (429e3, 778e3, 146.04, 275.87, 150.0, 20.0), tgt, 3.0)
        self.assertAlmostEqual(o.periapsis_altitude, 457.9e3, delta=500)
        self.assertAlmostEqual(o.apoapsis_altitude, 748.8e3, delta=0.01 * 748.8e3)  # burn 2 < 2 m/s: skipped
        self.assertLess(F._argpe_off(*map(math.degrees, (o.inclination, o.longitude_of_ascending_node,
                                                         o.argument_of_periapsis)), *tgt[:3]), 0.5)
        self.assertLessEqual(len(burns), 2)  # no rotation needed
        # the Eve contract from 120 x 19,131 km at inc 0.1 (no plane change), LAN 100: LAN + argPe on 330.23
        tgt = (0.0, 0.0, 330.23, 18868437.0, 0.05102)
        o, burns = self.fly_match(8.1717302e12, 700e3, (120e3, 19131e3, 0.1, 100.0, 40.0, 200.0), tgt, 5.0)
        self.assertLess(sum(burns), 550)  # our apoapsis + a 10 deg turn, not ~860 at the target's direction
        self.assertEqual(len(burns), 3)
        self.assertAlmostEqual(o.periapsis_altitude, 17206e3, delta=0.01 * 17206e3)
        self.assertAlmostEqual(o.apoapsis_altitude, 19131e3, delta=0.01 * 19131e3)
        self.assertLess(F._argpe_off(*map(math.degrees, (o.inclination, o.longitude_of_ascending_node,
                                                         o.argument_of_periapsis)), *tgt[:3]), 0.5)

    def test_rotation_skips_the_blocked_point(self):
        # _rotate_apsides on a fake KSP (kRPC's left-handed frame): the first crossing is behind the Mun, the
        # burn goes to the other one and lands the argPe on the target
        K = lambda p: (p[0], p[2], p[1])
        mu, R = self.MUN, 200e3
        mun = NS(name="Mun", gravitational_parameter=mu, equatorial_radius=R, non_rotating_reference_frame="f",
                 orbit=NS(body=NS(name="Kerbin", orbit=None)))

        class Orb:
            def __init__(self, k, t0=0.0):
                self.k, self.body, self.t0 = k, mun, t0
                self.inclination, self.longitude_of_ascending_node = k.inc, k.lan
                self.argument_of_periapsis, self.eccentricity, self.semi_major_axis = k.argpe, k.e, k.a
                self.period = k.period
                self.periapsis_altitude, self.apoapsis_altitude = k.periapsis - R, k.apoapsis - R

            def ut_at_true_anomaly(self, nu):
                return self.k.time_of_nu(nu, after=self.t0)

            def position_at(self, t, frame):
                return K(self.k.position(t))

        rp, ra = R + 457.9e3, R + 746.7e3
        a, e = (rp + ra) / 2, (ra - rp) / (ra + rp)
        now = Orb(F.kepler.Orbit(mu, a, e, math.radians(146.05), math.radians(275.9), math.radians(195.7), 0.0,
                                 0.0))

        class Node:
            prograde = normal = radial = 0.0

            def __init__(self, t, *c):
                self.ut = t

            def dv(self):
                r, v = now.k.state(self.ut)
                pg, nm = F._norm(v), F._norm(F._cross(r, v))
                return tuple(self.prograde * x + self.normal * y + self.radial * z
                             for x, y, z in zip(pg, nm, F._cross(pg, nm)))

            def burn_vector(self, frame):
                return K(self.dv())

            delta_v = property(lambda self: math.sqrt(F._dot(self.dv(), self.dv())))

            @property
            def orbit(self):
                r, v = now.k.state(self.ut)
                return Orb(F.kepler.Orbit.from_state(mu, r, tuple(x + y for x, y in zip(v, self.dv())), self.ut))

        dw = math.radians(177.93 - 195.7)
        first = min(now.ut_at_true_anomaly(nu) for nu, _ in F._apsides_turns(mu, a * (1 - e * e), e, dw))
        burned = []
        names = ("ut", "_crewed", "_link_forecast", "burn_lead", "burn_time", "_approve", "execute_node")
        saved = [getattr(F, n) for n in names]
        F.ut, F._crewed = lambda: -100.0, lambda v: False
        F._link_forecast = lambda o, occ: (lambda t: (-1.0 if abs(t - first) < 600 else 1e5, occ[0].name))
        F.burn_lead, F.burn_time = lambda v, dv: 1.0, lambda v, dv: 2.0
        F._approve = lambda node, expect, *a, **kw: None
        F.execute_node = lambda node, **kw: burned.append(node)
        try:
            v = NS(orbit=now, control=NS(add_node=Node))
            F._rotate_apsides(v, dw, 17.8, 3.2, (146.04, 275.87, 177.93))
            # never a link in the forecast (relays are not counted): the first point anyway
            F._link_forecast = lambda o, occ: (lambda t: (-1.0, occ[0].name))
            F._rotate_apsides(v, dw, 17.8, 3.2, (146.04, 275.87, 177.93))
            self.assertAlmostEqual(burned.pop().ut, first, delta=1e-6)
        finally:
            for n, f in zip(names, saved):
                setattr(F, n, f)
        self.assertEqual(len(burned), 1)
        n = burned[0]
        self.assertGreater(abs(n.ut - first), 600)
        self.assertLess(n.ut, first + now.period)  # the other crossing of the same orbit
        self.assertAlmostEqual(n.delta_v, 16.0, delta=1.0)
        o = n.orbit
        self.assertLess(F._argpe_off(*map(math.degrees, (o.inclination, o.longitude_of_ascending_node,
                                                         o.argument_of_periapsis)), 146.04, 275.87, 177.93), 0.1)
        self.assertAlmostEqual(o.periapsis_altitude, 457.9e3, delta=100)


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
