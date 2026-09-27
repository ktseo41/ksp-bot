"""Jool fleet, part 2 (offline): inside Jool's SOI. For each moon: the tangent approach (Jool periapsis on the moon's
orbit), the relative speed there, the capture burn, and what the moon's phase costs: one burn at t_pe - tau that
retargets the path to the moon (Lambert in Jool's frame to the moon's position at t2, t2 scanned; cost = burn now +
capture at the moon), as a function of the phase error of the arrival (in moon periods).
Run: uv run python tools/scratch/jool_fleet_arrival.py"""
import math
from jool_fleet_common import *  # noqa: F401,F403

VINF = (-960.4, -1476.3, -88.7)  # jool_fleet_transfer.py: arrival v_inf after the mid-course (1,763 m/s)
T_ARR = 79_124_684.0
Z = (0.0, 0.0, 1.0)
LAMBERT_ERRORS = [0]
# (low circular orbit, capture periapsis, capture apoapsis) altitudes, m
LOW = {"Laythe": (80e3, 80e3, 2000e3), "Vall": (20e3, 100e3, 1000e3), "Tylo": (30e3, 50e3, 1000e3),
       "Bop": (30e3, 30e3, 100e3), "Pol": (15e3, 25e3, 100e3)}


def approach(moon, rp, t_pe, vinf=VINF, normal=Z):
    return incoming_hyperbola(MU_JOOL, vinf, rp, normal, t_pe, "approach")


def retarget(hyp, moon, t_c, t2, pe_alt):
    """Burn at t_c on hyp to meet the moon at t2: (dv now, v_rel at the moon, Jool periapsis radius of the new path or
    None if the meeting point comes before it)."""
    pos, vel = hyp.state(t_c)
    r2, v2 = moon.orbit.state(t2)
    best = None
    for hn in (Z, moon.orbit.normal()):
        try:
            sol = _lambert(MU_JOOL, pos, r2, t2 - t_c, hn)
        except (ValueError, ZeroDivisionError):  # flight._lambert: y(z) < 0 at the bisection's end (strongly hyperbolic arcs): no solution
            LAMBERT_ERRORS[0] += 1
            sol = None
        if not sol:
            continue
        dv = _mag(sub(sol[0], vel))
        vrel = _mag(sub(sol[1], v2))
        o = Orbit.from_state(MU_JOOL, pos, sol[0], t_c)
        nu2 = math.atan2(_dot(r2, o.Q), _dot(r2, o.P))
        pe = o.periapsis if nu2 > 0 else None
        if pe is not None and pe < R_JOOL + ATM_JOOL + 100e3:
            continue
        c = dv + moon.capture_dv(vrel, pe_alt)
        if best is None or c < best[0]:
            best = (c, dv, vrel, pe, nu2)
    return best


def best_meeting(hyp, moon, t_c, t_lo, t_hi, pe_alt, n=400):
    best = None
    for i in range(n + 1):
        t2 = t_lo + (t_hi - t_lo) * i / n
        r = retarget(hyp, moon, t_c, t2, pe_alt)
        if r and (best is None or r[0] < best[0]):
            best = r + (t2,)
    if best is None:
        return None
    # refine
    d = (t_hi - t_lo) / n
    lo, hi = best[5] - d, best[5] + d
    for _ in range(40):
        a, b = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        ra, rb = retarget(hyp, moon, t_c, a, pe_alt), retarget(hyp, moon, t_c, b, pe_alt)
        if ra is None or rb is None:
            break
        if ra[0] < rb[0]:
            hi = b
        else:
            lo = a
    r = retarget(hyp, moon, t_c, (lo + hi) / 2, pe_alt)
    return (r + ((lo + hi) / 2,)) if r and r[0] <= best[0] else best


if __name__ == "__main__":
    vi = _mag(VINF)
    print(f"arrival v_inf {vi:.0f} m/s; Jool SOI {SOI_JOOL / 1e6:.0f} Mm")
    print("\n== tangent approach (Jool periapsis on the moon's orbit), circular-orbit speeds")
    for name, m in MOONS.items():
        a = m.orbit.a
        for label, r in (("pe", m.orbit.periapsis), ("sma", a), ("ap", m.orbit.apoapsis)):
            if m.orbit.e < 0.01 and label != "sma":
                continue
            v = math.sqrt(vi ** 2 + 2 * MU_JOOL / r)
            vm = math.sqrt(MU_JOOL * (2 / r - 1 / a))
            # relative inclination adds a lateral component (moon's plane vs the approach plane ~ ecliptic)
            inc = m.orbit.inc
            vrel = math.sqrt(v * v + vm * vm - 2 * v * vm * math.cos(inc))
            pe_alt = LOW[name][0]
            hyp = approach(m, r, 0.0)
            t_soi = -hyp.time_of_nu(-math.acos((hyp.a * (1 - hyp.e ** 2) / SOI_JOOL - 1) / hyp.e))
            print(f"  {name:7s} r {r / 1e6:6.1f} Mm ({label}): craft {v:5.0f}, moon {vm:5.0f}, v_rel {v - vm:5.0f} in plane "
                  f"/ {vrel:5.0f} with the moon's {math.degrees(inc):.1f} deg; capture to {pe_alt / 1e3:.0f} km circular "
                  f"{m.capture_dv(vrel, pe_alt):5.0f}; SOI edge to pe {t_soi / DAY:.1f} d; e {hyp.e:.2f}")

    print("\n== moon phase: best single retargeting burn at t_pe - tau vs the arrival's phase error (fraction of the"
          "\n   moon's period; 0 = the moon is at the tangent point when we are). cost = burn + capture (low circular)")
    for name, m in MOONS.items():
        P = m.orbit.period
        pe_alt = LOW[name][0]
        rp = m.orbit.a
        # nominal: t_pe such that the moon is at the periapsis point: scan t_pe over one period for the ideal
        rows = {}
        for tau_d in (60, 30, 10, 3):
            tau = tau_d * DAY
            res = []
            for k in range(0, 24):
                t_pe = T_ARR + P * k / 24
                hyp = approach(m, rp, t_pe)
                b = best_meeting(hyp, m, t_pe - tau, t_pe - 0.75 * P, t_pe + 0.75 * P, pe_alt, n=300)
                res.append((k / 24, b))
            rows[tau_d] = res
        ideal = min(b[0] for _, b in rows[60] if b)
        print(f"\n  {name}: period {P / 3600:.1f} h = {P / DAY:.2f} d; ideal burn + capture {ideal:.0f} m/s")
        for tau_d, res in rows.items():
            cs = [b[0] - ideal for _, b in res if b]
            dvs = [b[1] for _, b in res if b]
            vr = [b[2] for _, b in res if b]
            print(f"    tau {tau_d:2d} d: extra over the ideal min {min(cs):5.0f} / mean {sum(cs) / len(cs):5.0f} / max "
                  f"{max(cs):5.0f} m/s; burn now {min(dvs):.0f}-{max(dvs):.0f}; v_rel {min(vr):.0f}-{max(vr):.0f}")
        worst = max((x for x in rows[60] if x[1]), key=lambda x: x[1][0])
        print(f"    worst phase at tau 60 d: {worst[0]:.2f} P -> burn {worst[1][1]:.0f}, v_rel {worst[1][2]:.0f}, meeting "
              f"at t_pe{(worst[1][5] - (T_ARR + P * worst[0])) / 3600:+.1f} h, nu {math.degrees(worst[1][4]):+.0f} deg")
    print(f"\nflight._lambert raised ValueError (math domain) on {LAMBERT_ERRORS[0]} of the hyperbolic arcs tried")
