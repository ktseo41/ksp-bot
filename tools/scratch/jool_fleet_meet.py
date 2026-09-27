"""Jool fleet, part 2b (offline): the best meeting point for each moon when the arrival time is free (set far out):
for every position of the moon on its orbit, the incoming hyperbola (v_inf vector of the arrival) through that point,
the relative velocity there and the capture burn. Also the link geometry at the capture (Kerbin hidden by the moon or by
Jool over the burn) and the moon's face that sees Kerbin.
Run: uv run python tools/scratch/jool_fleet_meet.py"""
import math
from jool_fleet_common import *  # noqa: F401,F403
from kspbot.flight import _hyperbola_through
from jool_fleet_arrival import VINF, T_ARR, LOW, Z

KERBIN_DIR = _norm(sub(kerbin.position(T_ARR), jool.position(T_ARR)))
SUN_DIR = _norm(mul(jool.position(T_ARR), -1.0))


def through(r, vinf=VINF):
    """Velocity at r of the incoming hyperbola (meeting point at or before the Jool periapsis), its periapsis radius,
    true anomaly at r (<= 0)."""
    s = _hyperbola_through(MU_JOOL, r, mul(vinf, -1.0))
    if s is None:
        return None
    vel, e, rp, nu = s
    return mul(vel, -1.0), rp, -nu, e


def scan(m, n=720):
    rows = []
    P = m.orbit.period
    for i in range(n):
        t = T_ARR + P * i / n
        r2, v2 = m.orbit.state(t)
        s = through(r2)
        if s is None:
            continue
        vel, rp, nu, e = s
        if rp < R_JOOL + ATM_JOOL + 100e3:
            continue
        vr = sub(vel, v2)
        rows.append((_mag(vr), t, r2, v2, vel, rp, nu, vr))
    return rows


if __name__ == "__main__":
    print(f"Kerbin from Jool at arrival: {ang(KERBIN_DIR, SUN_DIR):.1f} deg from the Sun, latitude "
          f"{math.degrees(math.asin(KERBIN_DIR[2])):+.2f} deg over the moons' plane")
    for name, m in MOONS.items():
        rows = scan(m)
        best = min(rows, key=lambda r: r[0])
        worst = max(rows, key=lambda r: r[0])
        vrel, t, r2, v2, vel, rp, nu, vr = best
        pe_alt, cap_pe, cap_ap = LOW[name]
        print(f"\n{name}: best meeting point r {_mag(r2) / 1e6:.1f} Mm (moon's true anomaly "
              f"{math.degrees(m.orbit.true_anomaly(t)) % 360:.0f} deg), our Jool pe {rp / 1e6:.1f} Mm, we are at nu "
              f"{math.degrees(nu):+.1f} deg; v_rel {vrel:.0f} (over the orbit {vrel:.0f}..{worst[0]:.0f}); capture to "
              f"{pe_alt / 1e3:.0f} km circular {m.capture_dv(vrel, pe_alt):.0f}, to {cap_pe / 1e3:.0f} x {cap_ap / 1e3:.0f} km "
              f"{m.capture_dv(vrel, cap_pe, cap_ap):.0f}")
        pe_alt = cap_pe
        # geometry at the moon: v_rel direction vs Kerbin / Sun / Jool; the moon-centred hyperbola, prograde about the
        # moon's orbit normal (the moon turns that way: tidally locked) or retrograde
        jool_dir = _norm(mul(r2, -1.0))
        print(f"   v_rel {ang(vr, v2):.0f} deg from the moon's prograde; Kerbin {ang(vr, KERBIN_DIR):.0f} deg from v_rel, "
              f"Jool {ang(vr, jool_dir):.0f} deg from v_rel; Kerbin-moon-Jool angle {ang(KERBIN_DIR, jool_dir):.0f} deg "
              f"(Jool's disc {math.degrees(math.asin(R_JOOL / _mag(r2))):.1f} deg radius)")
        for label, hn in (("prograde", m.orbit.normal()), ("retrograde", mul(m.orbit.normal(), -1.0))):
            rp_m = m.R + pe_alt
            hyp = incoming_hyperbola(m.mu, vr, rp_m, hn, 0.0)
            hidden = []
            for k in range(-600, 601, 5):
                pos = hyp.position(float(k))
                if _dot(pos, KERBIN_DIR) < 0 and _mag(_cross(pos, KERBIN_DIR)) < m.R + m.terrain:
                    hidden.append(k)
            el_k = 90 - ang(hyp.P, KERBIN_DIR)
            el_s = 90 - ang(hyp.P, SUN_DIR)
            lon_j = math.degrees(math.atan2(_dot(_cross(jool_dir, hyp.P), m.orbit.normal()), _dot(jool_dir, hyp.P)))
            print(f"   {label:10s} pass at {pe_alt / 1e3:.0f} km: e {hyp.e:.2f}, v_pe {math.sqrt(vrel ** 2 + 2 * m.mu / rp_m):.0f}; "
                  f"at the periapsis Kerbin {el_k:+.0f} deg, Sun {el_s:+.0f} deg; pe {lon_j:+.0f} deg east of the "
                  f"sub-Jool point; Kerbin hidden by {name} "
                  + (f"from pe{hidden[0]:+d} s to pe{hidden[-1]:+d} s" if hidden else "never within +-600 s"))
        # Jool between the moon and Kerbin at the capture?
        clear = _mag(_cross(mul(r2, -1.0), KERBIN_DIR)) if _dot(mul(r2, -1.0), KERBIN_DIR) > 0 else float("inf")
        print(f"   line moon -> Kerbin passes {clear / 1e6:.1f} Mm from Jool's centre (Jool radius 6.2 Mm with air): "
              f"{'BLOCKED by Jool' if clear < 6.2e6 else 'clear of Jool'}")
        # tidal lock: which face sees Kerbin when
        P = m.orbit.period
        occ = 2 * math.asin(min(1.0, R_JOOL / m.orbit.a)) / (2 * math.pi) * P
        print(f"   tidally locked, period {P / 3600:.1f} h: every site has Kerbin up for ~{P / 7200:.1f} h per orbit "
              f"({P / 7200 * 0.78:.1f} h above 20 deg at the equator); Jool hides Kerbin for up to {occ / 60:.0f} min per "
              "orbit, seen only from the Jool-facing side")

    # Laythe, straight in from the hyperbola: Kerbin's elevation along the pass (the landing lies 5-10 deg before the
    # vacuum periapsis); and for every moon where the sub-Kerbin point lies at the capture
    print("\nLaythe direct entry (prograde pass, vacuum pe 40 km): Kerbin / Sun elevation at the ground point under the path")
    m = MOONS["Laythe"]
    best = min(scan(m), key=lambda r: r[0])
    hyp = incoming_hyperbola(m.mu, best[7], m.R + 40e3, m.orbit.normal(), 0.0)
    for nu in (-30, -20, -14, -10, -5, 0, 10):
        u = hyp.state_at_nu(math.radians(nu))[0]
        print(f"   nu {nu:+4d} deg: Kerbin {90 - ang(u, KERBIN_DIR):+.0f} deg, Sun {90 - ang(u, SUN_DIR):+.0f} deg")
    best_el = max(90 - ang(incoming_hyperbola(m.mu, best[7], m.R + 40e3, rotate(m.orbit.normal(), _norm(best[7]), math.radians(k)), 0.0).P,
                           KERBIN_DIR) for k in range(0, 360, 5))
    print(f"   best Kerbin elevation at the periapsis over all pass planes: {best_el:+.0f} deg")
    print("\nsub-Kerbin point at the capture (degrees east of the sub-Jool point; the sub-Jool longitudes read from the game:"
          "\nLaythe -90, Vall -128, Tylo 0, Bop ~23 (librates), Pol ~-117 (librates)); it then moves west at 360 deg per orbit")
    SUBJ = {"Laythe": -90.1, "Vall": -128.4, "Tylo": -0.1, "Bop": 22.7, "Pol": -117.0}
    for name, m in MOONS.items():
        best = min(scan(m), key=lambda r: r[0])
        r2 = best[2]
        jd = _norm(mul(r2, -1.0))
        n = m.orbit.normal()
        east = math.degrees(math.atan2(_dot(_cross(jd, KERBIN_DIR), n), _dot(jd, KERBIN_DIR)))
        lon = (SUBJ[name] + east + 180) % 360 - 180
        rate = 360.0 / (m.orbit.period / 3600)
        print(f"   {name:7s}: sub-Kerbin {east:+.0f} deg from the sub-Jool point = lon {lon:+.0f}; moves west {rate:.2f} deg/h; "
              f"the far side (lon {(SUBJ[name] + 360) % 360 - 180:+.0f}) has Kerbin {90 - abs(abs(east) - 180):.0f} deg up at the capture")
