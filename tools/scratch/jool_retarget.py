"""Read-only planning aid for the Jool fleet (kRPC, no commands, no nodes): the single burn that takes a craft on its
way through Jool's SOI to a moon, chosen for the least burn + capture (flight.correct's Lambert seed minimises the burn
alone and may meet the moon off the tangent point). States are read from the game in Jool's non-rotating frame (the
craft's and the moon's, so one frame serves both); Lambert over the arrival time within one moon period around the
craft's Jool periapsis. Prints the burn in the node's axes (prograde, normal = r x v of that frame, radial), the arrival
UT, the relative speed and the capture burn: the numbers to hold `correct <Moon> --plan` against, or to set a node by.
Run: uv run python tools/scratch/jool_retarget.py "Tylo 1" Tylo [--pe 50000] [--at UT]"""
import argparse
import math
import os
import sys

import krpc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from kspbot.kepler import Orbit, _cross, _dot, _mag, _norm  # noqa: E402
from kspbot.flight import _lambert  # noqa: E402


def vel_at(o, t, frame):
    a, b = o.position_at(t - 1, frame), o.position_at(t + 1, frame)
    return tuple((y - x) / 2 for x, y in zip(a, b))


def solve(mu, pos, vel, moon, t_c, t2, cap):
    """(burn + capture, burn vector, v_rel, arrival before the Jool periapsis?) or None."""
    r2, v2 = moon.state(t2)
    best = None
    for hn in (_norm(_cross(pos, vel)), moon.normal()):
        try:
            sol = _lambert(mu, pos, r2, t2 - t_c, hn)
        except (ValueError, ZeroDivisionError):
            sol = None
        if not sol:
            continue
        dv = tuple(a - b for a, b in zip(sol[0], vel))
        vr = _mag(tuple(a - b for a, b in zip(sol[1], v2)))
        o = Orbit.from_state(mu, pos, sol[0], t_c)
        if o.periapsis < 6.3e6 and math.atan2(_dot(r2, o.Q), _dot(r2, o.P)) > 0:
            continue  # the path would dip into Jool's air before the meeting
        c = _mag(dv) + cap(vr)
        if best is None or c < best[0]:
            best = (c, dv, vr)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vessel")
    ap.add_argument("moon")
    ap.add_argument("--pe", type=float, default=50000.0, help="capture periapsis altitude at the moon (m)")
    ap.add_argument("--at", type=float, help="burn UT (default now + 600 s)")
    a = ap.parse_args()
    sc = krpc.connect(name="jool-retarget (read-only)").space_center
    v = next((x for x in sc.vessels if x.name == a.vessel), None)
    if v is None:
        sys.exit(f"no vessel named {a.vessel!r}")
    jool, moon_b = sc.bodies["Jool"], sc.bodies[a.moon]
    if v.orbit.body.name != "Jool":
        sys.exit(f"{a.vessel} is around {v.orbit.body.name}: run this inside Jool's SOI")
    frame = jool.non_rotating_reference_frame
    mu = jool.gravitational_parameter
    now = sc.ut
    t_c = a.at or now + 600
    pos, vel = v.orbit.position_at(t_c, frame), vel_at(v.orbit, t_c, frame)
    moon = Orbit.from_state(mu, moon_b.orbit.position_at(now, frame), vel_at(moon_b.orbit, now, frame), now, a.moon)
    err = math.dist(moon.position(now + 0.7 * moon.period), moon_b.orbit.position_at(now + 0.7 * moon.period, frame))
    ship = Orbit.from_state(mu, pos, vel, t_c)
    t_pe = ship.time_of_nu(0.0, after=t_c)
    rp, mum = moon_b.equatorial_radius + a.pe, moon_b.gravitational_parameter
    cap = lambda vr: math.sqrt(vr * vr + 2 * mum / rp) - math.sqrt(mum / rp)
    P = moon.period
    rows = []
    n = 600
    for i in range(n + 1):
        t2 = t_pe - P + 2 * P * i / n
        if t2 <= t_c + 3600:
            continue
        s = solve(mu, pos, vel, moon, t_c, t2, cap)
        if s:
            rows.append(s + (t2,))
    if not rows:
        sys.exit("no Lambert arc found")
    best = min(rows, key=lambda r: r[0])
    lo, hi = best[3] - 2 * P / n, best[3] + 2 * P / n
    for _ in range(40):
        m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        s1, s2 = solve(mu, pos, vel, moon, t_c, m1, cap), solve(mu, pos, vel, moon, t_c, m2, cap)
        if s1 is None or s2 is None:
            break
        if s1[0] < s2[0]:
            hi = m2
        else:
            lo = m1
    s = solve(mu, pos, vel, moon, t_c, (lo + hi) / 2, cap)
    if s and s[0] <= best[0]:
        best = s + ((lo + hi) / 2,)
    c, dv, vr, t2 = best
    pro = _norm(vel)
    nrm = _norm(_cross(pos, vel))
    rad = _cross(pro, nrm)
    tangent = min(rows, key=lambda r: r[2])
    day = 21600.0
    print(f"{a.vessel} -> {a.moon}: burn at UT {t_c:.0f} (in {(t_c - now) / 60:.0f} min), Jool periapsis of the present path "
          f"UT {t_pe:.0f} (in {(t_pe - now) / day:.1f} d), moon model error {err:.0f} m")
    print(f"  best: {_mag(dv):.1f} m/s (prograde {_dot(dv, pro):+.2f}, normal {_dot(dv, nrm):+.2f}, radial {_dot(dv, rad):+.2f}; "
          f"normal along r x v of kRPC's frame: check the sign on the node's burn_vector), arrival UT {t2:.0f} "
          f"({(t2 - t_pe) / 3600:+.1f} h from the present periapsis), v_rel {vr:.0f} m/s, capture to a {a.pe / 1e3:.0f} km "
          f"circular orbit {cap(vr):.0f}: total {c:.0f}")
    print(f"  lowest v_rel in the scan: {tangent[2]:.0f} m/s for a burn of {_mag(tangent[1]):.0f} (arrival UT {tangent[3]:.0f})")


if __name__ == "__main__":
    main()
