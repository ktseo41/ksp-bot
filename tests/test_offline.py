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


class LandLink(unittest.TestCase):
    """land --min-elev: Kerbin's elevation from the landing site in the body's rotating frame."""
    E = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))  # directions of (0, 0), (0, 90 E), the north pole

    def assertVec(self, a, b, places=9):
        for x, y in zip(a, b):
            self.assertAlmostEqual(x, y, places=places)

    def test_surface_dir_turns_east(self):
        w = 2 * math.pi / 34800.0  # Dres
        self.assertVec(F._surface_dir(self.E, 0, 0, 0, w), (1, 0, 0))
        self.assertVec(F._surface_dir(self.E, 0, 90, 0, w), (0, 1, 0))
        self.assertVec(F._surface_dir(self.E, 90, 37, 0, w), (0, 0, 1))
        # a quarter turn later the prime meridian points where 90 E did; a fixed direction's longitude falls
        # (as _latlon_at: lon - w * dt), so the point at 90 W now faces (0, 0)
        self.assertVec(F._surface_dir(self.E, 0, 0, 8700.0, w), (0, 1, 0))
        self.assertVec(F._surface_dir(self.E, 0, -90, 8700.0, w), (1, 0, 0))
        self.assertVec(F._surface_dir(self.E, 45, 0, 8700.0, w), (0, math.sqrt(0.5), math.sqrt(0.5)))

    def test_elevation_from_the_ground(self):
        w = 2 * math.pi / 34800.0
        far = (1e10, 0.0, 0.0)  # Kerbin far along (0, 0)
        R = 138000.0
        self.assertAlmostEqual(F._elev_from(self.E, w, 0, 0, 0, far, R), 90.0, delta=0.001)
        self.assertAlmostEqual(F._elev_from(self.E, w, 45, 0, 0, far, R), 45.0, delta=0.001)  # parallax 0.0006
        self.assertAlmostEqual(F._elev_from(self.E, w, 0, 90, 0, far, R), 0.0, delta=0.001)
        self.assertAlmostEqual(F._elev_from(self.E, w, 0, 120, 0, far, R), -30.0, delta=0.001)
        # 60 deg west of the sub-Kerbin point now: overhead after 1/6 of a rotation, set a quarter turn later
        self.assertAlmostEqual(F._elev_from(self.E, w, 0, -60, 34800.0 / 6, far, R), 90.0, delta=0.001)
        self.assertAlmostEqual(F._elev_from(self.E, w, 0, -60, 34800.0 * 5 / 12, far, R), 0.0, delta=0.001)
        # parallax: Kerbin 12,000 km away on the Mun's horizon line from the centre is ~1 deg under it on the limb
        e = F._elev_from(self.E, 0.0, 0, 0, 0, (0.0, 12000e3, 0.0), 200e3)
        self.assertAlmostEqual(e, -math.degrees(math.asin(200 / math.hypot(12000, 200))), places=6)
        self.assertLess(e, -0.9)

    def test_descent_timeline_matches_a_simulation(self):
        hs, acc, g, h0, safety, max_decel = 250.0, 4.0, 1.13, 12000.0, 1.3, 3.0
        t = 1000.0
        start, td = F._descent_timeline(t, hs, acc, g, h0, safety, max_decel)
        self.assertAlmostEqual(start, t - hs / acc / 2 - 10)  # land()'s own start
        # step the kill (throttle min(1, hs/50) down to 5 m/s), the fall and the braking curve
        dt, tt, v = 0.001, start, hs
        while v > 5:
            v -= acc * min(1.0, v / 50) * dt
            tt += dt
        a_d = min((acc - g) / safety, max_decel)
        h, vs = h0, 0.0
        while h > 0:
            a = g if vs * vs < 2 * a_d * h else -a_d  # braking once on the curve
            vs += a * dt
            h -= vs * dt
            tt += dt
            if vs < 0:
                break
        self.assertAlmostEqual(td, tt, delta=2.0)

    def test_link_ok(self):
        self.assertTrue(F._link_ok(15, 25, 20))
        self.assertFalse(F._link_ok(9, 25, 20))   # the burn start under half of it
        self.assertFalse(F._link_ok(40, 19, 20))  # touchdown under it
        self.assertTrue(F._link_ok(None, None, 20))  # at Kerbin
        self.assertTrue(F._link_ok(-30, -50, 0))  # crewed: no condition

    def test_sky_grid_interpolates_and_caches(self):
        rate = math.radians(360 / 138984.0)  # Kerbin seen from the Mun: one turn per Mun orbit
        calls = []

        def fetch(t):
            calls.append(t)
            return (12e6 * math.cos(rate * t), 12e6 * math.sin(rate * t), 0.0), None
        f = F._sky_grid(fetch, 69.0)
        for t in (1000.0, 1010.5, 1030.0, 1034.0):
            k, s = f(t)
            self.assertIsNone(s)
            ang = math.degrees(math.atan2(k[1], k[0]))
            self.assertAlmostEqual(ang, math.degrees(rate * t), delta=0.001)
        self.assertEqual(sorted(calls), [966.0, 1035.0])  # two grid points, each fetched once

    def _fake_body(self, kerbin):
        """Dres-like: equatorial 2000-s orbit, 34800-s day, Kerbin far along inertial longitude `kerbin`; the burn
        starts 30 s before the site pass, the touchdown 200 s after it; the Sun opposite Kerbin."""
        n, w = 2 * math.pi / 2000.0, 2 * math.pi / 34800.0
        track = lambda t: (0.0, (math.degrees((n - w) * t) + 180) % 360 - 180)
        k = (1e10 * math.cos(math.radians(kerbin)), 1e10 * math.sin(math.radians(kerbin)), 0.0)
        sky = lambda t: (k, tuple(-x for x in k))  # the Sun on the other side
        f = F._site_sky(track, sky, self.E, w, 0.0, lambda t: (t - 30, t + 200), 150000.0, 138000.0)
        body = NS(name="Dres", equatorial_radius=138000.0)
        return track, f, NS(orbit=NS(body=body, period=2000.0))

    def _patched(self, v, run):
        saved = F.vessel, F.ut, F._slope, F._biome
        F.vessel, F.ut, F._slope, F._biome = (lambda: v), (lambda: 0.0), (lambda *a: 1.0), (lambda *a: "Midlands")
        try:
            return run()
        finally:
            F.vessel, F.ut, F._slope, F._biome = saved

    def test_find_site_waits_for_kerbin(self):
        # Kerbin opposite the vessel at t=0: at the site pass t the site faces n*t + w*200 at the touchdown, so
        # Kerbin >= 20 deg up needs n*t >= 107.93 deg (t >= 599.6 s); the burn start (>= 10 at t-30) is looser
        track, f, v = self._fake_body(180.0)
        ok = lambda t: F._link_ok(*f(t)[:2], 20.0)
        t = self._patched(v, lambda: F.find_site(None, track=track, ok=ok))
        self.assertEqual(t, 600.0)
        e_s, e_d, sun, ts, td = f(t)
        self.assertGreaterEqual(e_d, 20.0)
        self.assertLess(f(595.0)[1], 20.0)
        self.assertGreater(e_s, 10.0)
        self.assertAlmostEqual(sun, -f(t)[1], delta=0.01)  # the Sun as far down: night
        # without the link condition the first gentle site comes at once
        self.assertEqual(self._patched(v, lambda: F.find_site(None, track=track)), 120.0)
        # a window with no such site: None (land names the next one instead of flying)
        self.assertIsNone(self._patched(v, lambda: F.find_site(None, track=track, ok=ok, t_b=590.0)))

    def test_find_point_skips_the_pass_without_kerbin(self):
        # the point 110 W is under the track at t ~1474 (Kerbin 93 deg away), ~3596 (19.3 up at the touchdown: just
        # short) and ~5718 s (41 up): the third pass is the one
        track, f, v = self._fake_body(0.0)
        ok = lambda t: F._link_ok(*f(t)[:2], 20.0)
        t = self._patched(v, lambda: F.find_point(0.0, -110.0, track=track, ok=ok))
        self.assertAlmostEqual(t, 250 / math.degrees(2 * math.pi / 2000.0 - 2 * math.pi / 34800.0) + 2 * 360 /
                               math.degrees(2 * math.pi / 2000.0 - 2 * math.pi / 34800.0), delta=1.5)
        self.assertGreater(f(t)[1], 40.0)
        self.assertLess(f(t - 2122.0)[1], 20.0)
        # no link needed: the first pass
        t1 = self._patched(v, lambda: F.find_point(0.0, -110.0, track=track))
        self.assertAlmostEqual(t1, 1473.6, delta=1.5)


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


class MoonLambert(unittest.TestCase):
    """transfer Gilly from Eve 2's equatorial orbit (17,209 x 19,098 km): plan_moon_intercept on stock elements."""
    MU, R = 8.1717302e12, 700e3

    def ship(self):
        rp, ra = self.R + 17209e3, self.R + 19098e3
        return F.kepler.Orbit(self.MU, (rp + ra) / 2, (ra - rp) / (ra + rp), math.radians(0.02), 0.0,
                              math.radians(30), 0.0, 0.0, "Eve 2")

    def gilly(self, m0=0.0):
        return F.kepler.Orbit(self.MU, 31.5e6, 0.55, math.radians(12), math.radians(80), math.radians(10), m0, 0.0,
                              "Gilly")

    def test_lambert_recovers_an_inclined_arc(self):
        o = F.kepler.Orbit(self.MU, 25e6, 0.3, math.radians(30), 1.0, 2.0, 0.4, 0.0)
        for dt in (20000.0, 90000.0, 150000.0):
            (r1, v1), (r2, v2) = o.state(1000.0), o.state(1000.0 + dt)
            sol = F._lambert(self.MU, r1, r2, dt, o.W)
            self.assertLess(math.dist(sol[0], v1), 0.01)
            self.assertLess(math.dist(sol[1], v2), 0.01)

    def test_gilly_plan(self):
        ship, aim = self.ship(), 16900.0
        for m0 in (0.0, 1.5, 3.0, 4.5):  # Gilly anywhere on its orbit at the start
            moon = self.gilly(m0)
            t0 = time.time()
            p = F.plan_moon_intercept(ship, moon, 600.0, 600.0 + 1.2 * moon.period, aim=aim)
            self.assertLess(time.time() - t0, 20.0)
            # the task's expectation: ~150-300 m/s for departure + capture (v_rel)
            self.assertTrue(150 < p["cost"] < 300, p["cost"])
            self.assertAlmostEqual(p["cost"], p["dv"] + p["v_rel"], delta=1e-6)
            self.assertAlmostEqual(math.sqrt(sum(x * x for x in p["burn"])), p["dv"], delta=1e-6)
            self.assertGreaterEqual(p["t1"], 600.0)
            self.assertLessEqual(p["candidates"][0][0], p["cost"] + 2.0)  # aimed 17 km aside: ~the same arc
            # the arc really passes the aim point: closest approach to Gilly = the impact parameter
            d, tc = F.kepler.closest_approach(p["transfer"], moon, p["t_arr"] - 3000, p["t_arr"] + 3000)
            self.assertAlmostEqual(d, aim, delta=0.02 * aim)
            self.assertLess(abs(tc - p["t_arr"]), 30)
            # and on the side that makes the pass prograde about our orbit normal
            r = tuple(a - b for a, b in zip(p["transfer"].position(tc), moon.position(tc)))
            w = tuple(a - b for a, b in zip(p["transfer"].velocity(tc), moon.velocity(tc)))
            self.assertGreater(F._dot(F._cross(r, w), ship.W), 0)

    def test_gilly_plan_arrives_near_the_far_node(self):
        # the cheapest arcs meet Gilly away from its periapsis (v_rel there ~300 m/s)
        moon = self.gilly(0.0)
        p = F.plan_moon_intercept(self.ship(), moon, 600.0, 600.0 + 1.2 * moon.period)
        self.assertGreater(moon.radius_at(p["t_arr"]), 35e6)
        self.assertLess(p["v_rel"], 150)

    def test_prefers_the_earlier_of_two_near_equal(self):
        moon = self.gilly(0.0)
        p = F.plan_moon_intercept(self.ship(), moon, 600.0, 600.0 + 1.2 * moon.period, prefer=1.0)
        cheap = [k for k in p["candidates"] if k[0] <= 2 * p["candidates"][0][0] + 2]
        self.assertEqual(p["t1"], min(k[1] for k in cheap))


class GillyLanding(unittest.TestCase):
    def test_accel_cap_only_for_absurd_twr(self):
        self.assertAlmostEqual(F._landing_accel(27.8, 0.049), 2.049)  # Poodle on Gilly, TWR ~570
        self.assertEqual(F._landing_accel(13.7, 0.49), 13.7)  # Minmus TWR 28 keeps full thrust
        self.assertEqual(F._landing_accel(8.0, 1.63), 8.0)  # Mun
        self.assertEqual(F._landing_accel(1.0, 0.049), 1.0)  # never above what the engine has

    def sim(self, g, a_max, a_use, tick, h=10000.0):
        """1-D descent from rest: the throttle law sampled every tick and applied one tick late (kRPC latency).
        Returns (touchdown vertical speed, highest vertical speed in the last 50 m, peak thrust acceleration)."""
        vs, t, thr, nxt, pend, climb, peak = 0.0, 0.0, 0.0, 0.0, [], -99.0, 0.0
        while h > 0 and t < 5000:
            if t >= nxt:
                acc = F._descent_accel(h, vs, 0.0, g, a_use)
                pend.append((t + tick, max(0.0, min(a_use, acc) / a_max)))
                nxt = t + tick
            while pend and pend[0][0] <= t:
                thr = pend.pop(0)[1]
            peak = max(peak, thr * a_max)
            vs += (thr * a_max - g) * 0.002
            h += vs * 0.002
            t += 0.002
            if h < 50:
                climb = max(climb, vs)
        return vs, climb, peak

    def test_gilly_touchdown_with_a_capped_poodle(self):
        g, a_max = 0.049, 27.8
        a_use = F._landing_accel(a_max, g)
        for tick in (0.1, 0.2, 0.3, 0.5):
            vs, climb, peak = self.sim(g, a_max, a_use, tick)
            self.assertTrue(-2.0 <= vs < 0, (tick, vs))  # <= 2 m/s on the Poodle bell (crash tolerance 7)
            self.assertLess(climb, 0.0)  # never hovers back up near the ground
            self.assertLessEqual(peak, a_use + 1e-9)
        # the same law at full thrust climbs back up near the ground once the latency reaches 0.3 s (why the cap)
        self.assertGreater(self.sim(g, a_max, a_max, 0.5)[1], 0.0)

    def test_throttle_law_unchanged_at_the_mun(self):
        # the old inline law, for a normal lander (a_use = a_max)
        g, a = 1.63, 8.0
        for h, vs, hs in ((5000, -80, 3), (300, -20, 0.5), (10, -2, 0.1), (1, -1.5, 0)):
            a_d = min(max(a - g, 0.1) / 1.3, 3.0)
            curve = math.sqrt(max(0.0, 2 * a_d * (h - 2)))
            ff = a_d if curve > 1.5 else 0.0
            old = g + ff + 2.0 * (-max(1.5, curve) - vs) + 0.5 * hs
            self.assertAlmostEqual(F._descent_accel(h, vs, hs, g, a), old)


if __name__ == "__main__":
    unittest.main()
