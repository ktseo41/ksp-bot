"""Offline check of the Eve -> Kerbin departure plan for Eve 1 (no game needed): runs flight.plan_departure on the
orbit elements read from the live game at UT 18,713,906, then flies the plan with pure Kepler propagation - the tilt
impulse at the apoapsis, the ejection impulse at the periapsis, the hyperbola to Eve's SOI edge, KSP's hand-over to
the Sun, the transfer to Kerbin - and prints the closest approach and the mid-course correction that puts the Kerbin
periapsis at --pe. Compare its numbers with what `ksp depart Kerbin` prints live.

    uv run python tools/plan_eve_return.py [--pe 30000] [--max-arrival 1600] [--top 8]
"""
import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kspbot.kepler import Orbit, _cross, _dot, _mag, _norm, closest_approach, rotate  # noqa: E402
from kspbot.flight import _describe_candidate, _solve3, plan_departure  # noqa: E402

MU_SUN = 1.1723328e18
MU_EVE, R_EVE, SOI_EVE, ATMO_EVE = 8.17173e12, 700e3, 85_109e3, 90e3
MU_KERBIN, R_KERBIN, SOI_KERBIN = 3.5316e12, 600e3, 84_159e3
UT0 = 18_713_906.0
T_WINDOW = 27_264_701.0  # planet_window('Kerbin') from Eve, live
DAY = 21600.0

eve = Orbit(MU_SUN, 9_832_684_544, 0.01, 0.036652, 0.261799, 0.0, 3.14, 0.0, "Eve")
kerbin = Orbit(MU_SUN, 13_599_840_256, 0.0, 0.0, 0.0, 0.0, 3.14, 0.0, "Kerbin")
ship = Orbit(MU_EVE, 20_752_245, 0.95941, 1.27554, 3.29892, 5.90174, 0.017955, 17_393_653.54, "Eve 1")


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def frame_components(dv, r, v):
    """(prograde, radial, normal) components of dv in the orbital frame at (r, v)."""
    pro = _norm(v)
    nrm = _norm(_cross(r, v))
    rad = _cross(pro, nrm)
    return _dot(dv, pro), _dot(dv, rad), _dot(dv, nrm)


def fly(c, tilt_scale=1.0):
    """Fly the candidate with impulses on Kepler orbits; returns the heliocentric transfer orbit, the exit time and
    the state after the ejection (for reporting)."""
    t_ap = c["t_pe"] - ship.period / 2
    r_ap, v_ap = ship.state(t_ap)
    # rotate the velocity about the apsis line; the sign must leave the plane containing the planned asymptote
    best = None
    for s in (1, -1):
        v2 = rotate(v_ap, _norm(r_ap), s * c["tilt"] * tilt_scale)
        o = Orbit.from_state(MU_EVE, r_ap, v2, t_ap)
        err = abs(_dot(o.W, _norm(c["u"])))
        if best is None or err < best[0]:
            best = (err, v2, o)
    _, v_ap2, tilted = best
    dv_tilt = sub(v_ap2, v_ap)
    t_pe = tilted.time_of_nu(0, t_ap)
    r_pe, v_pe = tilted.state(t_pe)
    # ejection: the planned components (prograde, radial, normal) applied in the tilted orbit's frame at the periapsis
    pro, rad, nrm = c["pe_burn"]
    e_pro = _norm(v_pe)
    e_nrm = _norm(_cross(r_pe, v_pe))
    e_rad = _cross(e_pro, e_nrm)
    dv_pe = tuple(pro * a + rad * b + nrm * d for a, b, d in zip(e_pro, e_rad, e_nrm))
    hyp = Orbit.from_state(MU_EVE, r_pe, add(v_pe, dv_pe), t_pe, "escape")
    t_x = hyp.time_at_radius(SOI_EVE, t_pe)
    rx, vx = hyp.state(t_x)
    helio = Orbit.from_state(MU_SUN, add(eve.position(t_x), rx), add(eve.velocity(t_x), vx), t_x, "transfer")
    return dict(t_ap=t_ap, dv_tilt=dv_tilt, tilt_comp=frame_components(dv_tilt, r_ap, v_ap), tilted=tilted, t_pe=t_pe,
                dv_pe=dv_pe, hyp=hyp, t_x=t_x, vx=vx, helio=helio)


def midcourse(helio, t_mc, t_arr, b_want, iters=6):
    """Least-norm impulse at t_mc that moves the Kerbin closest approach to the distance b_want (its direction free:
    2 equations, 3 unknowns), by a numerical Jacobian of the closest-approach vector, like flight._solve_dv."""
    def miss(o):
        d, t = closest_approach(o, kerbin, t_arr - 60 * DAY, t_arr + 60 * DAY, n=600)
        return sub(o.position(t), kerbin.position(t)), t

    r0, v0 = helio.state(t_mc)
    dv = (0.0, 0.0, 0.0)
    for _ in range(iters):
        o = Orbit.from_state(MU_SUN, r0, add(v0, dv), t_mc)
        b0, t_ca = miss(o)
        v_rel = sub(o.velocity(t_ca), kerbin.velocity(t_ca))
        s = _norm(v_rel)
        flat = lambda x: sub(x, tuple(_dot(x, s) * y for y in s))
        b0f = flat(b0)
        want = tuple(b_want * x for x in _norm(b0f)) if _mag(b0f) > 1.0 else (b_want, 0.0, 0.0)
        d = sub(want, b0f)
        if _mag(d) < 1e3:
            break
        cols = []
        h = 0.2
        for k in range(3):
            dvk = list(dv)
            dvk[k] += h
            ok = Orbit.from_state(MU_SUN, r0, add(v0, tuple(dvk)), t_mc)
            bk, _ = miss(ok)
            cols.append(flat(tuple((x - y) / h for x, y in zip(bk, b0))))
        JJt = [[sum(cols[k][i] * cols[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
        eps = 1e-9 * sum(JJt[i][i] for i in range(3))
        for i in range(3):
            JJt[i][i] += eps
        y = _solve3(JJt, d)
        dv = tuple(dv[k] + _dot(cols[k], y) for k in range(3))
    o = Orbit.from_state(MU_SUN, r0, add(v0, dv), t_mc)
    b, t_ca = miss(o)
    return dv, _mag(b), t_ca, o


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pe", type=float, default=30000, help="Kerbin periapsis altitude for the mid-course correction")
    ap.add_argument("--max-arrival", type=float, help="only candidates with arrival v_inf below this (m/s)")
    ap.add_argument("--top", type=int, default=8)
    ap.add_argument("--horizon", type=float, default=800.0, help="days ahead to search")
    ap.add_argument("--at", type=float, help="UT of the periapsis pass to fly (default: cheapest)")
    a = ap.parse_args()

    vp, va = _mag(ship.state_at_nu(0)[1]), _mag(ship.state_at_nu(math.pi)[1])
    print(f"Eve 1: pe {(ship.periapsis - R_EVE) / 1e3:.1f} km ap {(ship.apoapsis - R_EVE) / 1e3:.0f} km period "
          f"{ship.period / DAY:.2f} d, v_pe {vp:.0f} v_ap {va:.1f} m/s, v_esc(pe) {math.sqrt(2 * MU_EVE / ship.periapsis):.0f}")
    ecl = _norm(_cross(eve.position(T_WINDOW), eve.velocity(T_WINDOW)))
    print(f"apoapsis direction: {math.degrees(math.acos(_dot(tuple(-x for x in ship.P), _norm(eve.velocity(T_WINDOW))))):.0f} deg "
          f"from Eve's prograde at the window, ecliptic latitude {math.degrees(math.asin(-_dot(ship.P, ecl))):.0f} deg; "
          f"orbit plane {math.degrees(math.acos(abs(_dot(ship.W, ecl)))):.0f} deg from the ecliptic")
    T_h = math.pi * math.sqrt(((eve.a + kerbin.a) / 2) ** 3 / MU_SUN)
    cands = plan_departure(ship, eve, kerbin, MU_SUN, SOI_EVE, UT0 + 120, UT0 + a.horizon * DAY, T_h)
    if a.max_arrival:
        cands = [c for c in cands if c["arrival_v_inf"] <= a.max_arrival]
    print(f"\n{len(cands)} candidates (tangential periapsis burn + apoapsis tilt); cheapest {a.top}:")
    if not cands:
        print("none: no flight time puts the Lambert asymptote on the periapsis cone within the horizon / arrival cap")
        return
    for c in cands[:a.top]:
        print("  " + _describe_candidate(c, UT0, T_WINDOW))
    gentle = [c for c in cands if c["arrival_v_inf"] <= 1600]
    if gentle:
        print("cheapest with arrival v_inf <= 1600 (entry ~3.6 km/s): " + _describe_candidate(gentle[0], UT0, T_WINDOW))
    c = min(cands, key=lambda x: abs(x["t_pe"] - a.at)) if a.at else cands[0]

    print("\n=== chosen plan ===")
    print(_describe_candidate(c, UT0, T_WINDOW))
    print(f"departure periapsis UT {c['t_pe']:.0f}; flight {c['T'] / DAY:.1f} d; arrival UT {c['t_arr']:.0f}")
    print(f"tilt burn at the apoapsis UT {c['t_pe'] - ship.period / 2:.0f}: {c['dv_tilt']:.1f} m/s = prograde "
          f"{c['tilt_burn'][0]:+.1f}, normal {abs(c['tilt_burn'][1]):.1f} (sign: whichever KSP patch matches the plane)"
          f" -> plane inc {math.degrees(c['inc']):.2f} deg, LAN {math.degrees(c['lan']):.2f} deg")
    print(f"ejection at the periapsis UT {c['t_pe']:.0f}: {c['dv_pe']:.1f} m/s = prograde {c['pe_burn'][0]:+.1f}, radial "
          f"{c['pe_burn'][1]:+.1f}, normal {c['pe_burn'][2]:+.1f} (hyperbola true anomaly at the burn {math.degrees(c['nu_h']):+.2f} deg,"
          f" its periapsis {(c['pe_h'] - R_EVE) / 1e3:.1f} km)")
    print(f"required v_inf {c['v_inf']:.1f} m/s; speed at the SOI edge {c['exit_speed']:.1f} m/s (hand-over at UT "
          f"{c['exit'][0]:.0f}, {(c['exit'][0] - c['t_pe']) / DAY:.2f} d after the burn)")
    h = c["helio"]
    print(f"heliocentric transfer: pe {h.periapsis / 1e9:.2f} Gm ap {h.apoapsis / 1e9:.2f} Gm inc {math.degrees(h.inc):.2f} deg "
          f"(Eve 9.83, Kerbin 13.60); arrival v_inf {c['arrival_v_inf']:.0f} m/s -> Kerbin entry speed "
          f"{math.sqrt(c['arrival_v_inf'] ** 2 + 2 * MU_KERBIN / (R_KERBIN + 70e3)) :.0f} m/s at 70 km")

    print("\n=== flown with Kepler impulses ===")
    f = fly(c)
    print(f"tilt impulse {_mag(f['dv_tilt']):.1f} m/s (prograde {f['tilt_comp'][0]:+.1f} radial {f['tilt_comp'][1]:+.1f} "
          f"normal {f['tilt_comp'][2]:+.1f}) -> inc {math.degrees(f['tilted'].inc):.2f} LAN {math.degrees(f['tilted'].lan):.2f}, "
          f"pe {(f['tilted'].periapsis - R_EVE) / 1e3:.1f} km ap {(f['tilted'].apoapsis - R_EVE) / 1e3:.0f} km, "
          f"next periapsis UT {f['t_pe']:.0f} ({f['t_pe'] - c['t_pe']:+.0f} s vs plan)")
    hyp = f["hyp"]
    print(f"ejection impulse {_mag(f['dv_pe']):.1f} m/s -> hyperbola e {hyp.e:.4f} pe {(hyp.periapsis - R_EVE) / 1e3:.1f} km "
          f"v_inf {hyp.v_inf():.1f}; SOI exit UT {f['t_x']:.0f} at {_mag(f['vx']):.1f} m/s")
    helio = f["helio"]
    d, t_ca = closest_approach(helio, kerbin, c["t_arr"] - 60 * DAY, c["t_arr"] + 60 * DAY, n=600)
    print(f"transfer pe {helio.periapsis / 1e9:.2f} ap {helio.apoapsis / 1e9:.2f} Gm inc {math.degrees(helio.inc):.2f}; "
          f"Kerbin closest approach {d / 1e3:.0f} km at UT {t_ca:.0f} ({(t_ca - c['t_arr']) / DAY:+.1f} d vs plan; "
          f"SOI {SOI_KERBIN / 1e3:.0f} km) -> {'ENCOUNTER' if d < SOI_KERBIN else 'MISS'}")
    v_rel = sub(helio.velocity(t_ca), kerbin.velocity(t_ca))
    vinf = _mag(v_rel)
    rp = R_KERBIN + a.pe
    b_want = rp * math.sqrt(1 + 2 * MU_KERBIN / (rp * vinf ** 2))
    t_mc = f["t_x"] + 0.5 * (c["t_arr"] - f["t_x"])
    dv, b, t_ca2, o2 = midcourse(helio, t_mc, c["t_arr"], b_want)
    # periapsis from the impact parameter: rp = -mu/v^2 + sqrt((mu/v^2)^2 + b^2)
    k = MU_KERBIN / vinf ** 2
    rp2 = -k + math.sqrt(k * k + b * b)
    print(f"mid-course at UT {t_mc:.0f} ({(t_mc - f['t_x']) / DAY:.0f} d after exit, halfway): {_mag(dv):.2f} m/s "
          f"(prograde/radial/normal {frame_components(dv, *helio.state(t_mc))[0]:+.2f}/"
          f"{frame_components(dv, *helio.state(t_mc))[1]:+.2f}/{frame_components(dv, *helio.state(t_mc))[2]:+.2f}) "
          f"-> impact parameter {b / 1e3:.0f} km = Kerbin pe {(rp2 - R_KERBIN) / 1e3:.1f} km (want {a.pe / 1e3:.0f}), "
          f"arrival v_inf {vinf:.0f}")
    # sensitivity: a 1 m/s prograde error at the ejection
    print("\nsensitivity (closest approach without correction):")
    for label, scale, dpro in (("tilt 1 % short", 0.99, 0.0), ("ejection +1 m/s prograde", 1.0, 1.0),
                               ("ejection -1 m/s prograde", 1.0, -1.0)):
        cc = dict(c)
        cc["pe_burn"] = (c["pe_burn"][0] + dpro, c["pe_burn"][1], c["pe_burn"][2])
        ff = fly(cc, tilt_scale=scale)
        dd, tt = closest_approach(ff["helio"], kerbin, c["t_arr"] - 60 * DAY, c["t_arr"] + 60 * DAY, n=600)
        print(f"  {label:<26} closest approach {dd / 1e3:>9.0f} km ({(tt - c['t_arr']) / DAY:+.1f} d)")
    total = c["dv"] + _mag(dv)
    print(f"\nTOTAL: tilt {c['dv_tilt']:.0f} + ejection {c['dv_pe']:.0f} + mid-course ~{_mag(dv):.0f} (+ a few m/s of trims) "
          f"= ~{total:.0f} m/s of the 3760 aboard")


if __name__ == "__main__":
    main()
