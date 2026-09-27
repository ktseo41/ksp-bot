"""Jool fleet, part 3 (offline): flight.land() flown in a 2D simulation (polar coordinates, point mass, no rotation of
the body): the horizontal kill at the orbit height along surface retrograde (throttle x min(1, hs/50)), the free fall
(0.8 t_fall - 20 s of warp), then _powered_descent with _descent_accel (braking curve a_d = min((a - g) / safety,
max_decel), feedforward + 2/s on the speed error + 0.5 hs). Multi-stage: the engine list is burnt in order (auto_stage).
Also a tangent-steered variant for comparison (what a `land --from-orbit` would do).
Run: uv run python tools/scratch/jool_fleet_land.py"""
import math
from jool_fleet_common import *  # noqa: F401,F403


class Craft:
    """stages: [(thrust N, isp s, fuel kg, dry mass dropped with the stage kg)], burnt first to last; m_final: what is
    left after the last stage's fuel is gone (kg)."""

    def __init__(self, stages, m_final):
        self.stages = [list(s) for s in stages]
        self.m_final = m_final
        self.spent = 0.0

    @property
    def mass(self):
        return self.m_final + sum(s[2] + s[3] for s in self.stages[:-1]) + self.stages[-1][2] if self.stages else self.m_final

    def _drop(self):
        while len(self.stages) > 1 and self.stages[0][2] <= 0:
            self.stages.pop(0)

    @property
    def thrust(self):
        self._drop()
        return self.stages[0][0] if self.stages[0][2] > 0 else 0.0

    def total_mass(self):
        self._drop()
        return self.m_final + sum(s[2] for s in self.stages) + sum(s[3] for s in self.stages[:-1])

    def burn(self, acc, dt):
        """Thrust acceleration acc for dt: burns fuel, returns the dv delivered."""
        self._drop()
        s = self.stages[0]
        m = self.total_mass()
        f = min(acc * m, s[0])
        dm = f / (s[1] * G0) * dt
        dm = min(dm, s[2])
        s[2] -= dm
        self.spent += f / m * dt
        return f / m

    def dv_left(self):
        tot, m = 0.0, self.total_mass()
        st = [list(s) for s in self.stages if s[2] > 0]
        for i, s in enumerate(st):
            tot += s[1] * G0 * math.log(m / (m - s[2]))
            m -= s[2] + (s[3] if i < len(st) - 1 else 0.0)
        return tot


def landing_accel(a_max, g, cap=2.0, ratio=50.0):
    return min(a_max, g + cap) if a_max > ratio * g else a_max


def descent_accel(h, vs, hs, g, a_use, safety=1.3, final_speed=1.5, max_decel=3.0):
    a_d = min(max(a_use - g, 0.1) / safety, max_decel)
    curve = math.sqrt(max(0.0, 2 * a_d * (h - 2)))
    want = -max(final_speed, curve)
    ff = a_d if curve > final_speed else 0.0
    return g + ff + 2.0 * (want - vs) + 0.5 * hs


def simulate(moon, craft, h_orbit, h_site=0.0, max_decel=3.0, safety=1.3, max_accel=2.0, dt=0.05, mode="land",
             verbose=False, pe_start=None):
    """mode "land": the code as it is. mode "gravity": brake along surface retrograde from the orbit at full thrust,
    started so that it ends ~1 km over the site (searched by the caller through t_start), then the same powered descent.
    Returns dict(dv, v_touch, t, h_min_coast, ...)."""
    mu, R, g = moon.mu, moon.R, moon.g
    r = R + h_orbit
    vt, vr = math.sqrt(mu / r), 0.0  # circular
    th = 0.0
    t = 0.0
    out = {}
    hs0 = vt
    hs_end = max(1.0, min(5.0, 0.1 * hs0))
    # phase 1: horizontal kill
    while vt > hs_end:
        m = craft.total_mass()
        a_max = craft.thrust / m
        if a_max <= 0:
            out["fail"] = "out of fuel in the kill"
            break
        a = landing_accel(a_max, g, max_accel) * min(1.0, max(0.05, vt / 50))
        a = craft.burn(a, dt)
        sp = math.hypot(vt, vr)
        ar, at = -a * vr / sp, -a * vt / sp
        ar += vt * vt / r - mu / r ** 2
        at += -vr * vt / r
        vr += ar * dt
        vt += at * dt
        r += vr * dt
        th += vt / r * dt
        t += dt
        if r - R - h_site <= 0:
            out["fail"] = f"hit the ground during the kill at hs {vt:.0f}, vs {vr:.0f}"
            break
    out.update(t_kill=t, dv_kill=craft.spent, h_after_kill=r - R - h_site, vs_after_kill=vr, range_kill=th * R)
    if "fail" in out:
        out.update(dv=craft.spent, v_touch=math.hypot(vr, vt))
        return out
    # phase 2: free fall, warped
    m = craft.total_mass()
    a_use = landing_accel(craft.thrust / m, g, max_accel)
    a_d = min(max(a_use - g, 0.1) / safety, max_decel)
    h0 = r - R - h_site
    t_fall = math.sqrt(2 * a_d * h0 / (g * g + a_d * g))
    out["t_fall"] = t_fall
    if t_fall > 60:
        t_end = t + 0.8 * t_fall - 20
        while t < t_end:
            ar = vt * vt / r - mu / r ** 2
            at = -vr * vt / r
            vr += ar * dt
            vt += at * dt
            r += vr * dt
            t += dt
            if r - R - h_site <= 0:
                out.update(fail=f"hit the ground in the warped free fall at {vr:.0f} m/s", dv=craft.spent,
                           v_touch=abs(vr))
                return out
    out.update(h_descent=r - R - h_site, vs_descent=vr)
    # phase 3: powered descent
    feet = 2.0
    while True:
        h = r - R - h_site - feet
        if h <= 0:
            break
        m = craft.total_mass()
        a_max = craft.thrust / m
        if a_max <= 0:
            out["fail"] = f"out of fuel at {h:.0f} m, vs {vr:.0f}"
            # fall to the ground
            vr = -math.sqrt(vr * vr + 2 * g * h)
            break
        a_use = landing_accel(a_max, g, max_accel)
        acc = descent_accel(h, vr, abs(vt), g, a_use, safety, 1.5, max_decel)
        a = max(0.0, min(a_use, acc))
        a = craft.burn(a, dt) if a > 0 else 0.0
        sp = math.hypot(vt, vr)
        if sp > 2:
            ar, at = -a * vr / sp, -a * vt / sp
        else:
            ar, at = a, 0.0
        ar += vt * vt / r - mu / r ** 2
        at += -vr * vt / r
        vr += ar * dt
        vt += at * dt
        r += vr * dt
        t += dt
        if t > 5000:
            out["fail"] = "timeout"
            break
    out.update(dv=craft.spent, v_touch=math.hypot(vr, vt), t=t, dv_left=craft.dv_left(), m_end=craft.total_mass())
    return out


def ideal_landing(moon, h_orbit):
    """Impulsive: deorbit to a periapsis at the ground, kill the speed there."""
    mu, R = moon.mu, moon.R
    r1, r2 = R + h_orbit, R
    a = (r1 + r2) / 2
    v1 = math.sqrt(mu / r1)
    return v1 - math.sqrt(mu * (2 / r1 - 1 / a)) + math.sqrt(mu * (2 / r2 - 1 / a))


def report(name, mk_craft, heights, decels, h_site=0.0, safety=1.3):
    m = MOONS[name]
    c0 = mk_craft()
    print(f"\n{name}: g {m.g:.2f}; craft {c0.total_mass() / 1000:.2f} t, a0 {c0.thrust / c0.total_mass():.1f} m/s2 "
          f"(TWR {c0.thrust / c0.total_mass() / m.g:.2f}), dv {c0.dv_left():.0f}; site at {h_site / 1000:.1f} km")
    for h in heights:
        for md in decels:
            c = mk_craft()
            o = simulate(m, c, h, h_site, max_decel=md, safety=safety)
            print(f"   orbit {h / 1e3:5.0f} km, max_decel {md:4.1f}: ideal {ideal_landing(m, h - h_site):5.0f}; kill "
                  f"{o['dv_kill']:5.0f} in {o['t_kill']:4.0f} s -> {o['h_after_kill'] / 1e3:6.1f} km up, vs "
                  f"{o['vs_after_kill']:5.0f}, {o['range_kill'] / 1e3:4.0f} km of ground; "
                  + (f"FAIL: {o['fail']} (dv so far {o['dv']:.0f})" if "fail" in o else
                     f"total {o['dv']:5.0f} m/s, touchdown {o['v_touch']:.1f} m/s, {o['t']:.0f} s, left {o['dv_left']:.0f}"))


if __name__ == "__main__":
    # Dres 1 / Eeloo 1 lander after the capture and the orbit work: ~5.0 t (3,045 kg dry), Terrier
    def dres_lander(fuel=2000.0):
        return Craft([(60e3, 345, fuel, 0.0)], 3045.0)
    report("Vall", lambda: dres_lander(2400.0), (12e3, 15e3, 20e3, 30e3), (3.0, 5.0), h_site=1000.0)
    report("Bop", lambda: dres_lander(1500.0), (30e3,), (3.0,), h_site=5000.0)
    report("Pol", lambda: dres_lander(1500.0), (15e3,), (3.0,), h_site=1000.0)
    import jool_fleet_stages as st
    for nm, mk in st.TYLO_LANDERS.items():
        print(f"\n--- Tylo lander variant: {nm}")
        report("Tylo", mk, (25e3, 30e3, 40e3, 60e3), (3.0, 4.5, 6.0), h_site=2000.0)
    print("\n--- the braking law above max_decel 3: a_d > 2 x final_speed leaves a hover point where the curve's speed is"
          "\n    a_d / 2 (feedforward a_d = 2 x speed error), h - 2 = a_d / 8 m: a craft that falls behind the curve settles there")
    report("Tylo", st.TYLO_LANDERS["A with 2,250 left + B (plan)"], (30e3,), (9.0, 12.0), h_site=2000.0)


def braking_descent(moon, mk_craft, ap_alt, pe_alt, h_site, h_end=1000.0, throttle=0.95, dt=0.05):
    """What gap 2 (e) would fly: from an ap_alt x pe_alt orbit, one burn along surface retrograde at `throttle`, its
    start searched so that the speed is gone h_end above the site; then the coded powered descent from there.
    Returns (dv of the braking, total dv, start angle before the periapsis in deg) or None."""
    mu, R = moon.mu, moon.R
    a = R + (ap_alt + pe_alt) / 2
    e = (ap_alt - pe_alt) / (2 * a)
    o = Orbit(mu, a, e, 0.0, 0.0, 0.0, 0.0, 0.0)

    def run(nu0):
        c = mk_craft()
        pos, vel = o.state_at_nu(math.radians(-nu0))
        r = _mag(pos)
        vr = _dot(pos, vel) / r
        vt = math.sqrt(max(0.0, _dot(vel, vel) - vr * vr))
        while math.hypot(vr, vt) > 5.0:
            m = c.total_mass()
            if c.thrust <= 0:
                return None, c, r, vr, vt
            acc = c.burn(throttle * c.thrust / m, dt)
            sp = math.hypot(vr, vt)
            ar = -acc * vr / sp + vt * vt / r - mu / r ** 2
            at = -acc * vt / sp - vr * vt / r
            vr += ar * dt
            vt += at * dt
            r += vr * dt
            if r - R - h_site < 50:
                return -1.0, c, r, vr, vt
        return r - R - h_site, c, r, vr, vt
    lo, hi = 0.5, 60.0  # a later start (small angle) ends lower
    best = None
    for _ in range(40):
        mid = (lo + hi) / 2
        h, c, r, vr, vt = run(mid)
        if h is None:
            return None
        if h < h_end:
            lo = mid
        else:
            hi = mid
            best = (mid, h, c, r, vr, vt)
    if best is None:
        return None
    nu0, h, c, r, vr, vt = best
    dv_brake = c.spent
    # the rest: the coded law from h
    g = moon.g
    t = 0.0
    while r - R - h_site - 2.0 > 0 and t < 600:
        m = c.total_mass()
        a_max = c.thrust / m
        if a_max <= 0:
            return None
        acc = descent_accel(r - R - h_site - 2.0, vr, abs(vt), g, a_max, 1.3, 1.5, 3.0)
        acc = c.burn(max(0.0, min(a_max, acc)), dt) if acc > 0 else 0.0
        sp = math.hypot(vr, vt)
        ar = (-acc * vr / sp if sp > 2 else acc) + vt * vt / r - mu / r ** 2
        at = (-acc * vt / sp if sp > 2 else 0.0) - vr * vt / r
        vr += ar * dt
        vt += at * dt
        r += vr * dt
        t += dt
    return dv_brake, c.spent, nu0, c.dv_left()


if __name__ == "__main__":
    print("\n--- gap 2 (e): braking along the path from a low ellipse (not in the code), Tylo 1's lander, site at 2 km")
    mk = st.TYLO_LANDERS["A with 2,250 left + B (plan)"]
    for ap, pe in ((30e3, 30e3), (30e3, 12e3), (30e3, 8e3)):
        for h_end in (1000.0, 300.0):
            r = braking_descent(MOONS["Tylo"], mk, ap, pe, 2000.0, h_end=h_end)
            if r:
                print(f"   {ap / 1e3:.0f} x {pe / 1e3:.0f} km, braking to {h_end:.0f} m over the site: burn {r[0]:.0f} m/s from "
                      f"{r[2]:.1f} deg before the periapsis, total with the final descent {r[1]:.0f} m/s, left {r[3]:.0f}"
                      + (f" (+ {ideal_landing(MOONS['Tylo'], ap) - ideal_landing(MOONS['Tylo'], ap):.0f})" if False else ""))
            else:
                print(f"   {ap / 1e3:.0f} x {pe / 1e3:.0f} km: no solution")
