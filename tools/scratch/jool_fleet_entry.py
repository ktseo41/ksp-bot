"""Jool fleet, part 6 (offline): Laythe entry of the Eve 2 style lander (10 m inflatable shield). Drag area calibrated on
Eve 2's flown entry (recorder 2026-09-27: CdA 105-116 m2 hypersonic, 48 m2 below ~170 m/s, 2 Mk2-R open ~800-1,000 m2
with the shield), Laythe's density read from the game. Entry from the 80 km orbit (after `deorbit`) and, for comparison,
straight from the hyperbolic approach. Planar, non-rotating atmosphere (Laythe's equator turns at 59 m/s).
Run: uv run python tools/scratch/jool_fleet_entry.py"""
import math
from jool_fleet_common import *  # noqa: F401,F403

L = MOONS["Laythe"]
RHO = [(0, 0.74311), (2000, 0.676215), (5000, 0.573769), (10000, 0.300775), (15000, 0.15179), (20000, 0.072939),
       (25000, 0.040438), (30000, 0.024981), (35000, 0.012806), (40000, 0.006007), (45000, 0.001531), (50000, 0.0)]
EVE2_HEAT = 7.2e8  # sqrt(rho) v^3 at Eve 2's peak (70 km, 3,964 m/s, q 1,050 Pa), survived with 25/25 parts
EVE2_G = 60.3      # m/s2, Eve 2's peak deceleration


def rho(h):
    if h >= 50000:
        return 0.0
    if h <= 0:
        return RHO[0][1]
    for (h0, r0), (h1, r1) in zip(RHO, RHO[1:]):
        if h0 <= h <= h1:
            if r1 <= 0:
                return r0 * (h1 - h) / (h1 - h0) * 0.5
            return math.exp(math.log(r0) + (math.log(r1) - math.log(r0)) * (h - h0) / (h1 - h0))
    return 0.0


def cda(v, chutes=0):
    if v >= 400:
        c = 110.0
    elif v <= 170:
        c = 48.0
    else:
        c = 48.0 + (110.0 - 48.0) * (v - 170) / 230
    return c + 420.0 * chutes


def entry(mass, r0, v0, gamma0, chutes=4, chute_alt=4000.0, chute_speed=250.0, dt=0.05):
    """From the state at the atmosphere's edge (flight-path angle gamma0 < 0, rad) to the ground."""
    r, th, vr, vt = r0, 0.0, v0 * math.sin(gamma0), v0 * math.cos(gamma0)
    t, out = 0.0, dict(gmax=0.0, qmax=0.0, heat=0.0, hmin=1e9, skip=False)
    open_ = False
    load = 0.0
    while r > L.R and t < 40000:
        h = r - L.R
        v = math.hypot(vr, vt)
        d = rho(h)
        q = 0.5 * d * v * v
        if not open_ and ((h < chute_alt and v < chute_speed) or h < 2500):
            open_ = True
            out.update(chute_h=h, chute_v=v)
        a = q * cda(v, chutes if open_ else 0) / mass
        heat = math.sqrt(d) * v ** 3
        load += heat * dt
        if not open_ and a > out["gmax"]:
            out.update(gmax=a, g_h=h, g_v=v)  # the entry itself (the model opens the chutes at once: no shock figure)
        if heat > out["heat"]:
            out.update(heat=heat, heat_h=h, heat_v=v)
        out["qmax"] = max(out["qmax"], q)
        ar = -a * vr / v + vt * vt / r - L.mu / r ** 2
        at = -a * vt / v - vr * vt / r
        vr += ar * dt
        vt += at * dt
        r += vr * dt
        th += vt / r * dt
        t += dt
        if h > 50000 and vr > 0 and t > 10:
            e = v * v / 2 - L.mu / r
            out.update(skip=True, v_exit=v, bound=e < 0,
                       apo=(-L.mu / (2 * e) * 2 - r) - L.R if e < 0 else None)
            break
    out.update(t=t, downrange=math.degrees(th), v_touch=math.hypot(vr, vt), load=load)
    return out


def edge_state(o):
    """(r, v, gamma) where the orbit o (periapsis inside the air) crosses 50 km on the way in."""
    r = L.R + 50e3
    p = o.a * (1 - o.e ** 2)
    nu = -math.acos(max(-1.0, min(1.0, (p / r - 1) / o.e)))
    pos, vel = o.state_at_nu(nu)
    v = _mag(vel)
    gamma = math.asin(_dot(pos, vel) / (_mag(pos) * v))
    return r, v, gamma, nu


if __name__ == "__main__":
    mass = 3455.0
    print(f"lander {mass / 1000:.3f} t, ballistic coefficient {mass / 110:.0f} kg/m2 (CdA 110 m2); terminal speed at sea "
          f"level: shield alone {math.sqrt(2 * mass * L.g / (rho(0) * cda(10))):.1f} m/s, with 2 Mk2-R "
          f"{math.sqrt(2 * mass * L.g / (rho(0) * cda(10, 2))):.1f}, with 4 {math.sqrt(2 * mass * L.g / (rho(0) * cda(10, 4))):.1f}; "
          f"at 3 km on 4: {math.sqrt(2 * mass * L.g / (rho(3000) * cda(10, 4))):.1f}")
    print("\nfrom the 80 km circular orbit, deorbit burn to a vacuum periapsis of:")
    rc = L.R + 80e3
    for pe in (40e3, 35e3, 30e3, 25e3, 15e3, 0.0):
        a = (rc + L.R + pe) / 2
        dv = math.sqrt(L.mu / rc) - math.sqrt(L.mu * (2 / rc - 1 / a))
        o = Orbit(L.mu, a, (rc - L.R - pe) / (rc + L.R + pe), 0.0, 0.0, 0.0, math.pi, 0.0)
        r, v, g, nu = edge_state(o)
        e = entry(mass, r, v, g)
        print(f"  pe {pe / 1e3:4.0f} km ({dv:3.0f} m/s): {v:.0f} m/s at 50 km, path angle {math.degrees(g):.2f} deg; "
              + (f"SKIPS OUT at {e['v_exit']:.0f} m/s (apoapsis {e['apo'] / 1e3:.0f} km), comes back" if e["skip"] else
                 f"peak {e['gmax']:.0f} m/s2 ({e['gmax'] / 9.81:.1f} g) at {e['g_h'] / 1e3:.0f} km, q max {e['qmax']:.0f} Pa, heat "
                 f"{e['heat'] / EVE2_HEAT * 100:.0f} % of Eve 2's peak, chutes at {e['chute_h'] / 1e3:.1f} km / {e['chute_v']:.0f} m/s, "
                 f"touchdown {e['v_touch']:.1f} m/s after {e['t'] / 60:.0f} min, {e['downrange']:.0f} deg downrange of the edge "
                 f"(the vacuum pe lies {-math.degrees(nu):.0f} deg past the edge)"))
    print("\nstraight from the hyperbola (v_rel 1,693 m/s), vacuum periapsis:")
    for pe in (45e3, 42e3, 40e3, 35e3, 30e3, 20e3, 10e3):
        rp = L.R + pe
        ecc = 1 + rp * 1693.0 ** 2 / L.mu
        o = Orbit(L.mu, -L.mu / 1693.0 ** 2, ecc, 0.0, 0.0, 0.0, 0.0, 0.0)
        r, v, g, nu = edge_state(o)
        e = entry(mass, r, v, g)
        print(f"  pe {pe / 1e3:4.0f} km: {v:.0f} m/s at 50 km, path angle {math.degrees(g):.2f} deg; "
              + ((f"skips out at {e['v_exit']:.0f} m/s: " + (f"captured, apoapsis {e['apo'] / 1e3:.0f} km" if e["bound"]
                                                               else "NOT captured (flyby)")) if e["skip"] else
                 f"lands: peak {e['gmax']:.0f} m/s2 ({e['gmax'] / 9.81:.1f} g), heat {e['heat'] / EVE2_HEAT * 100:.0f} % of Eve 2's "
                 f"peak, touchdown {e['v_touch']:.1f} m/s, {e['downrange']:.0f} deg downrange of the edge (pe {-math.degrees(nu):.0f})"))
