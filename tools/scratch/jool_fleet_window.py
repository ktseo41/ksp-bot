"""Jool fleet, part 7 (offline): the window's width (ejection + arrival cost against the departure day, flight time
re-optimised like the planner) and the Mun on the escape path: the UTs around the window at which an ejection from the
80 km equatorial parking orbit passes the Mun within 2 SOI radii (transfer_planet's own margin, _moon_clear_shift).
Run: uv run python tools/scratch/jool_fleet_window.py"""
import math
from jool_fleet_common import *  # noqa: F401,F403
from jool_fleet_transfer import plan, jool_cap, h
from kspbot.kepler import closest_approach

MUN_SOI = 2429559.0


def best(t_dep, pe_alt=62.5e6):
    T_h = 1152 * DAY
    rows = []
    for i in range(0, 161):
        T = T_h * (0.8 + 0.0025 * i)
        p = plan(T, t_dep=t_dep)
        if p:
            rows.append((eject_dv(p["vi_dep"]) + p["dv_pc"] + jool_cap(p["vi_arr"], pe_alt), p))
    return min(rows, key=lambda r: r[0])


def escape_path(t_b, vi1):
    """Escape hyperbola from the 80 km equatorial orbit whose asymptote is vi1 projected on the equator; periapsis
    (the burn) at t_b."""
    z = (0.0, 0.0, 1.0)
    u = _norm(sub(vi1, mul(z, _dot(vi1, z))))
    r0 = R_KERBIN + 80e3
    vinf = _mag(vi1)
    a = -MU_KERBIN / vinf ** 2
    e = 1 + r0 / -a
    th = math.acos(-1 / e)
    P = rotate(u, z, -th)  # the asymptote lies th ahead of the periapsis
    vp = math.sqrt(vinf ** 2 + 2 * MU_KERBIN / r0)
    return Orbit.from_state(MU_KERBIN, mul(P, r0), mul(_cross(z, P), vp), t_b)


if __name__ == "__main__":
    print("departure day against the window (UT 54,245,654): T best | eject | plane term | arrival v_inf | total | arrival UT")
    for d in (-30, -20, -10, -5, -2, 0, 2, 5, 10, 20, 30, 40):
        tot, p = best(T_WIN + d * DAY)
        print(f"  {d:+4d} d: T {p['T'] / DAY:6.0f} d, eject {eject_dv(p['vi_dep']):5.0f}, plane {p['dv_pc']:3.0f}, v_inf "
              f"{p['vi_arr']:5.0f}, planner total {tot:5.0f}, arrival UT {T_WIN + d * DAY + p['T']:.0f}")

    print("\nMun on the escape path: ejection UTs (burn at the periapsis of the escape hyperbola) blocked within 2 SOI")
    blocked = []
    t0, t1 = T_WIN - 3 * DAY, T_WIN + 8 * DAY
    t = t0
    cur = None
    while t <= t1:
        p = next(q for q in (plan(Td * DAY, t_dep=t) for Td in (1152, 1165, 1140, 1180)) if q)
        path = escape_path(t, p["vi1"])
        t_out = path.time_at_radius(12e6 + 3 * MUN_SOI, t) or t + 40000
        d, tc = closest_approach(path, mun, t, t_out, n=120)
        hit = d < 2 * MUN_SOI
        if hit and cur is None:
            cur = [t, t, d]
        elif hit:
            cur[1] = t
            cur[2] = min(cur[2], d)
        elif cur is not None:
            blocked.append(cur)
            cur = None
        t += 300.0
    if cur is not None:
        blocked.append(cur)
    for a, b, d in blocked:
        print(f"  UT {a:.0f} .. {b:.0f} ({(a - T_WIN) / 3600:+.1f} h .. {(b - T_WIN) / 3600:+.1f} h from the window, "
              f"{(b - a) / 60:.0f} min = {(b - a) / 1958:.1f} parking orbits): closest {d / 1e3:.0f} km")
    print(f"  Mun period {mun.period / 3600:.1f} h: one blocked slot per Mun orbit; parking orbit period "
          f"{2 * math.pi * math.sqrt((R_KERBIN + 80e3) ** 3 / MU_KERBIN):.0f} s")
    path = escape_path(T_WIN, next(q for q in (plan(Td * DAY) for Td in (1152, 1165, 1140)) if q)["vi1"])
    print(f"  time from the burn to the Mun's orbit radius: {(path.time_at_radius(12e6, T_WIN) - T_WIN) / 60:.0f} min; "
          f"to Kerbin's SOI edge: {(path.time_at_radius(SOI_KERBIN, T_WIN) - T_WIN) / 3600:.1f} h")
