"""Jool fleet, part 1 (offline): the Kerbin -> Jool transfer at the window UT 54,245,654 as `transfer_planet` plans it
(Lambert to Jool's arrival position projected onto Kerbin's plane, flight time scanned 0.6..1.4 x Hohmann), the honest
3D mid-course, the arrival v_inf vector and geometry (Kerbin, Sun), link distances, the solar conjunctions.
Run: uv run python tools/scratch/jool_fleet_transfer.py"""
import math
from jool_fleet_common import *  # noqa: F401,F403

r1, v1k = kerbin.state(T_WIN)
h = kerbin.normal()
R1 = _mag(r1)


def plan(T, projected=True, t_dep=T_WIN):
    p1, vk = kerbin.state(t_dep)
    r2, v2 = jool.state(t_dep + T)
    z2 = _dot(r2, h)
    r2p = sub(r2, mul(h, z2)) if projected else r2
    sol = _lambert(MU_SUN, p1, r2p, T, h)
    if not sol:
        return None
    vi1, vi2 = sub(sol[0], vk), sub(sol[1], v2)
    R2 = _mag(r2)
    dv_pc = abs(z2) / R2 * math.sqrt(MU_SUN * (2 / R2 - 2 / (R1 + R2))) if projected else 0.0
    return dict(T=T, vi1=vi1, vi_dep=_mag(vi1), vi_arr=_mag(vi2), vinf=vi2, z2=z2, dv_pc=dv_pc, R2=R2, va=sol[0],
                vb=sol[1], r2=r2, v2=v2, p1=p1)


def jool_cap(vi, pe=250e3):  # the planner's capture term: circular at pe_alt (here only to rank flight times)
    return math.sqrt(vi ** 2 + 2 * MU_JOOL / (R_JOOL + pe)) - math.sqrt(MU_JOOL / (R_JOOL + pe))


def best_plan(pe_alt, t_dep=T_WIN):
    a_h = (kerbin.a + jool.radius_at(t_dep)) / 2
    T_h = math.pi * math.sqrt(a_h ** 3 / MU_SUN)
    rows = []
    for i in range(0, 401):
        T = T_h * (0.6 + 0.002 * i)
        p = plan(T, t_dep=t_dep)
        if p:
            rows.append((eject_dv(p["vi_dep"]) + p["dv_pc"] + jool_cap(p["vi_arr"], pe_alt), p))
    return min(rows, key=lambda r: r[0]), T_h


def midcourse(p, t_c, t_arr=None, target=None):
    """Single 3D burn at t_c on the projected transfer of plan p to reach Jool's real position (or target) at t_arr:
    (dv vector, arrival v_inf vector)."""
    tr = Orbit.from_state(MU_SUN, p["p1"], p["va"], T_WIN)
    t_arr = T_WIN + p["T"] if t_arr is None else t_arr
    pos, vel = tr.state(t_c)
    r2, v2 = jool.state(t_arr)
    sol = _lambert(MU_SUN, pos, r2 if target is None else target, t_arr - t_c, h)
    if not sol:
        return None
    return sub(sol[0], vel), sub(sol[1], v2), pos


if __name__ == "__main__":
    print("== planner's flight-time scan (projected), capture term for three periapsis radii")
    for label, pe in (("Laythe r 27.2 Mm", 27.184e6 - R_JOOL), ("Tylo r 68.5 Mm", 68.5e6 - R_JOOL),
                      ("Pol r 180 Mm", 179.89e6 - R_JOOL)):
        (tot, p), T_h = best_plan(pe)
        print(f"  --pe {pe / 1e3:9.0f} km ({label}): T {p['T'] / DAY:6.1f} d (Hohmann {T_h / DAY:.0f}), v_inf dep "
              f"{p['vi_dep']:.0f}, eject {eject_dv(p['vi_dep']):.0f}, arrival v_inf {p['vi_arr']:.0f} (projected), Jool "
              f"{p['z2'] / 1e6:+.0f} Mm out of plane (SOI {SOI_JOOL / 1e6:.0f}), plane term {p['dv_pc']:.0f}; arrival UT "
              f"{T_WIN + p['T']:.0f}")
    print("\n== T scan (pe at Tylo's radius): T d | eject | plane term | v_inf arr | z2 Mm | arrival UT")
    for Td in range(800, 1500, 50):
        p = plan(Td * DAY)
        if p:
            print(f"  {Td:5d} {eject_dv(p['vi_dep']):6.0f} {p['dv_pc']:5.0f} {p['vi_arr']:6.0f} {p['z2'] / 1e6:+7.0f} "
                  f"{T_WIN + Td * DAY:12.0f}")
    (tot, pb), T_h = best_plan(68.5e6 - R_JOOL)
    T = pb["T"]
    t_arr = T_WIN + T
    p3 = plan(T, projected=False)
    dec = math.degrees(math.asin(_dot(_norm(p3["vi1"]), h)))
    print(f"\n3D Lambert from the parking orbit at T {T / DAY:.0f} d: eject {eject_dv(p3['vi_dep']):.0f} (declination "
          f"{dec:+.1f} deg), arrival v_inf {p3['vi_arr']:.0f}")
    print("\n== honest mid-course (single 3D burn on the projected transfer): dep+d | dv | normal part | v_inf after | Kerbin Gm")
    for dd in (100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1050):
        t_c = T_WIN + dd * DAY
        if t_c > t_arr - 20 * DAY:
            continue
        m = midcourse(pb, t_c)
        if m:
            print(f"  {dd:5d} d (UT {t_c / 1e6:.2f} M): {_mag(m[0]):6.1f} | {abs(_dot(m[0], h)):6.1f} | {_mag(m[1]):6.0f} | "
                  f"{_mag(sub(m[2], kerbin.position(t_c))) / 1e9:5.1f}")
    # planner's own mid-course UT
    R2 = pb["R2"]
    e_t = abs(R1 - R2) / (R1 + R2)
    E = 2 * math.atan(math.sqrt((1 - e_t) / (1 + e_t)))
    t_pc = t_arr - (E - e_t * math.sin(E)) / math.pi * T
    print(f"planner's printed mid-course UT ~{t_pc:.0f} (dep + {(t_pc - T_WIN) / DAY:.0f} d), term {pb['dv_pc']:.0f} m/s")

    print("\n== arrival timing: cost of moving the arrival by dt with one burn at dep+d (dv of the 3D mid-course that"
          "\n   also moves the arrival, minus the plain one), and the v_inf it leaves")
    for dd in (300, 500, 700, 900, 1000):
        t_c = T_WIN + dd * DAY
        base = midcourse(pb, t_c)
        row = []
        for dth in (-125, -59, -29, -15, 15, 29, 59, 125):  # hours: +-half periods of Laythe 7.4, Vall 14.7, Tylo 29.4, Bop 75.6, Pol 125.3
            m = midcourse(pb, t_c, t_arr + dth * 3600)
            row.append(f"{dth:+d}h {_mag(m[0]) - _mag(base[0]):+6.1f} (vinf {_mag(m[1]):.0f})")
        print(f"  dep+{dd} d (base {_mag(base[0]):.1f}, vinf {_mag(base[1]):.0f}): " + " | ".join(row))

    m = midcourse(pb, T_WIN + 500 * DAY)
    vinf = m[1]
    r2, v2 = jool.state(t_arr)
    rk = kerbin.position(t_arr)
    d_k, d_s = sub(rk, r2), mul(r2, -1.0)
    print(f"\n== ARRIVAL UT {t_arr:.0f} ({t_arr / 1e6:.2f} M): Jool {_mag(r2) / 1e9:.1f} Gm from the Sun, Kerbin "
          f"{_mag(d_k) / 1e9:.1f} Gm away, Sun-Jool-Kerbin {ang(d_k, d_s):.1f} deg")
    print(f"v_inf {_mag(vinf):.0f} m/s: {ang(vinf, v2):.0f} deg from Jool's prograde, {ang(vinf, d_s):.0f} deg from the "
          f"Sun line, {ang(vinf, d_k):.0f} deg from the Kerbin line, declination to the moons' plane "
          f"{math.degrees(math.asin(_dot(_norm(vinf), (0, 0, 1)))):+.2f} deg")
    print(f"vinf vector {tuple(round(x, 1) for x in vinf)}; Kerbin dir {tuple(round(x, 4) for x in _norm(d_k))}; "
          f"Sun dir {tuple(round(x, 4) for x in _norm(d_s))}")
    print(f"solar flux at Jool: {(kerbin.a / _mag(r2)) ** 2:.3f} x Kerbin")
    print("\nKerbin-Jool distance and Sun-Jool-Kerbin angle over the mission:")
    for dd in range(0, 1700, 100):
        t = T_WIN + dd * DAY
        dk = sub(kerbin.position(t), jool.position(t))
        print(f"  dep+{dd:4d} d (UT {t / 1e6:.2f} M): {_mag(dk) / 1e9:5.1f} Gm, angle {ang(mul(jool.position(t), -1), dk):5.1f} deg, "
              f"RA-100 strength {strength(_mag(dk), 100e9):.2f}, RA-15 {strength(_mag(dk), 15e9):.2f}, 2xRA-100 {strength(_mag(dk), 100e9 * 2 ** 0.75):.2f}")
    print("conjunctions (Kerbin behind the Sun seen from Jool; Sun's radius from Jool ~0.22 deg):")
    prev = None
    for k in range(int(T_WIN), int(T_WIN + 1800 * DAY), 3600):
        dk = sub(kerbin.position(k), jool.position(k))
        a = ang(mul(jool.position(k), -1), dk)
        if prev and prev[1] < prev[0][1] and prev[1] < a and prev[1] < 1.0:
            rs = math.degrees(math.atan(R_SUN / _mag(jool.position(k))))
            print(f"  UT {prev[2]:.0f} (dep+{(prev[2] - T_WIN) / DAY:.0f} d): min angle {prev[1]:.3f} deg, Sun radius {rs:.2f} -> "
                  f"{'BLACKOUT ~1 d' if prev[1] < rs else 'clear'}")
        prev = ((prev[2] if prev else k, prev[1] if prev else a), a, k)
