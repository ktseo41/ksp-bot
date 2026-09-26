"""Offline Duna 2 plan check: Lambert scan at the window, arrival geometry (Kerbin / Sun vs the capture periapsis),
capture and landing dv, and the per-stage rocket equation on the exact part masses of crafts/duna-2.json."""
import json
import math
import os
import sys

sys.path.insert(0, ".")
from kspbot.kepler import Orbit, _cross, _dot, _mag, _norm, rotate  # noqa: E402
from kspbot.flight import _lambert  # noqa: E402

MU_SUN = 1.1723328e18
MU_KERBIN, R_KERBIN = 3.5316e12, 600e3
MU_DUNA, R_DUNA, SOI_DUNA, ATMO_DUNA, ROT_DUNA = 3.0136321e11, 320e3, 47_921_949.0, 50e3, 65_517.859
DAY = 21600.0
T_WIN = 44_649_525.0
kerbin = Orbit(MU_SUN, 13_599_840_256, 0.0, 0.0, 0.0, 0.0, 3.14, 0.0, "Kerbin")
duna = Orbit(MU_SUN, 20_726_155_264, 0.051, math.radians(0.06), math.radians(135.5), 0.0, 3.14, 0.0, "Duna")

def eject_dv(vinf, mu=MU_KERBIN, r=R_KERBIN + 80e3):
    return math.sqrt(vinf ** 2 + 2 * mu / r) - math.sqrt(mu / r)

def ang(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, _dot(_norm(a), _norm(b))))))

# ---- Lambert scan like transfer_planet (0.6..1.4 x Hohmann, 2 % steps), cost = ejection + arrival v_inf / 10
a_t = (kerbin.a + duna.a) / 2
T_h = math.pi * math.sqrt(a_t ** 3 / MU_SUN)
r1, v1k = kerbin.state(T_WIN)
h = kerbin.normal()
best = None
rows = []
for i in range(41):
    T = T_h * (0.6 + 0.02 * i)
    r2, v2d = duna.state(T_WIN + T)
    sol = _lambert(MU_SUN, r1, r2, T, h)
    if not sol:
        continue
    va, vb = sol
    vi_dep = _mag(tuple(a - b for a, b in zip(va, v1k)))
    vi_arr = _mag(tuple(a - b for a, b in zip(vb, v2d)))
    cost = eject_dv(vi_dep) + vi_arr / 10
    rows.append((T / DAY, vi_dep, eject_dv(vi_dep), vi_arr, r2[2] / 1e6, cost))
    if best is None or cost < best[0]:
        best = (cost, T, vi_dep, vi_arr, va, vb, r2, v2d)
print(f"Hohmann T {T_h / DAY:.1f} d; scan (T d, vinf_dep, eject, vinf_arr, Duna z Mm, cost):")
for r in rows[::4]:
    print("  %6.1f %6.0f %6.0f %6.0f %8.1f %6.0f" % r)
cost, T, vi_dep, vi_arr, va, vb, r2, v2d = best
print(f"\nBEST: T {T / DAY:.1f} d, v_inf dep {vi_dep:.0f} -> eject {eject_dv(vi_dep):.0f} m/s from 80 km, "
      f"arrival v_inf {vi_arr:.0f}, arrival UT {T_WIN + T:.0f}, Duna z {r2[2] / 1e6:+.1f} Mm (SOI 47.9)")

# ---- arrival geometry in Duna's frame
t_arr = T_WIN + T
vinf = tuple(a - b for a, b in zip(vb, v2d))
rk = kerbin.position(t_arr)
d_kerbin = tuple(a - b for a, b in zip(rk, r2))
d_sun = tuple(-x for x in r2)
prograde = _norm(v2d)
dist_k = _mag(d_kerbin)
print(f"Kerbin from Duna at arrival: {dist_k / 1e9:.1f} Gm, {ang(d_kerbin, prograde):.0f} deg from Duna prograde, "
      f"{ang(d_kerbin, d_sun):.0f} deg from the Sun")
print(f"v_inf direction: {ang(vinf, prograde):.0f} deg from prograde, {ang(vinf, d_sun):.0f} deg from the Sun "
      f"(|v_inf| {_mag(vinf):.0f})")

def hyperbola_pe_dir(vinf, hn, r_pe, mu=MU_DUNA):
    """Periapsis direction of the hyperbola with this v_inf and orbit normal hn (prograde about hn)."""
    v = _mag(vinf)
    e = 1 + r_pe * v * v / mu
    th = math.acos(-1 / e)
    u_in = _norm(tuple(-x for x in vinf))  # where the craft comes from
    return rotate(u_in, hn, th), e, th

def blackout(P, hn, e, r_pe, d_k, mu=MU_DUNA):
    """True-anomaly arc (deg, then seconds from pe) over which the ray to Kerbin passes through Duna."""
    Q = _cross(hn, P)
    p = r_pe * (1 + e)
    k = _norm(d_k)
    out = []
    for nu_deg in range(-90, 91):
        nu = math.radians(nu_deg)
        r = p / (1 + e * math.cos(nu))
        pos = tuple(r * (math.cos(nu) * a + math.sin(nu) * b) for a, b in zip(P, Q))
        behind = _dot(pos, k) < 0 and _mag(_cross(pos, k)) < R_DUNA
        out.append((nu_deg, behind, r))
    hidden = [n for n, b, _ in out if b]
    return (min(hidden), max(hidden)) if hidden else None

for label, hn in (("prograde", _norm(h)), ("retrograde", tuple(-x for x in _norm(h)))):
    for pe_alt in (100e3,):
        P, e, th = hyperbola_pe_dir(vinf, hn, R_DUNA + pe_alt)
        bo = blackout(P, hn, e, R_DUNA + pe_alt, d_kerbin)
        el = 90 - ang(P, d_kerbin)
        sun = 90 - ang(P, d_sun)
        print(f"{label} pass, pe {pe_alt / 1e3:.0f} km: e {e:.2f}, pe {ang(P, d_kerbin):.0f} deg from Kerbin "
              f"(Kerbin elevation at the sub-pe point {el:+.0f} deg), Sun elevation {sun:+.0f} deg, "
              f"pe {ang(P, prograde):.0f} deg from prograde; Kerbin hidden over nu {bo}")

# ---- capture / circularize / deorbit / entry numbers at pe 100 km
r_pe = R_DUNA + 100e3
for vi in (800, vi_arr, 1000, 1100):
    v_pe = math.sqrt(vi ** 2 + 2 * MU_DUNA / r_pe)
    r_ap = R_DUNA + 1000e3
    a = (r_pe + r_ap) / 2
    v_ell = math.sqrt(MU_DUNA * (2 / r_pe - 1 / a))
    v_circ = math.sqrt(MU_DUNA / r_pe)
    print(f"v_inf {vi:.0f}: v_pe {v_pe:.0f}, capture to 100 x 1000 km {v_pe - v_ell:.0f}, "
          f"circularize {v_ell - v_circ:.0f} (total {v_pe - v_circ:.0f}); e_hyp {1 + r_pe * vi * vi / MU_DUNA:.2f}")
v_circ = math.sqrt(MU_DUNA / r_pe)
r_low = R_DUNA + 8e3
a_d = (r_pe + r_low) / 2
v_deorb = v_circ - math.sqrt(MU_DUNA * (2 / r_pe - 1 / a_d))
v_entry = math.sqrt(MU_DUNA * (2 / (R_DUNA + ATMO_DUNA) - 1 / a_d))
t_coast = math.pi * math.sqrt(a_d ** 3 / MU_DUNA) / 2
P100 = 2 * math.pi * math.sqrt(r_pe ** 3 / MU_DUNA)
print(f"100 km circular: v {v_circ:.0f}, period {P100 / 60:.1f} min; deorbit to pe 8 km {v_deorb:.0f} m/s, "
      f"entry at 50 km {v_entry:.0f} m/s, ~{t_coast / 60:.0f} min from the burn; Duna rotates {360 / ROT_DUNA * 3600:.1f} deg/h")
# entry flight-path angle at 50 km
p = a_d * (1 - ((r_pe - r_low) / (r_pe + r_low)) ** 2)
e_d = (r_pe - r_low) / (r_pe + r_low)
nu = math.acos((p / (R_DUNA + ATMO_DUNA) - 1) / e_d)
fpa = math.degrees(math.atan(e_d * math.sin(nu) / (1 + e_d * math.cos(nu))))
print(f"entry flight-path angle at 50 km: {fpa:.1f} deg (e {e_d:.3f})")

# ---- Kerbin-Duna distance over the stay, Sun angle
for dd in (0, 30, 60, 120):
    t = t_arr + dd * DAY
    dk = tuple(a - b for a, b in zip(kerbin.position(t), duna.position(t)))
    print(f"  +{dd:3d} d: Kerbin-Duna {_mag(dk) / 1e9:.1f} Gm, Sun-Duna-Kerbin {ang(tuple(-x for x in duna.position(t)), dk):.0f} deg")

# ---- stages from the spec
spec = json.load(open("./crafts/duna-2.json"))
MASS = {"probeCoreOcto.v2": 0.1, "batteryBank": 0.05, "sasModule": 0.05, "science.module": 0.2, "fuelTank": 2.25,
        "liquidEngine3.v2": 0.5, "parachuteRadial": 0.1, "GooExperiment": 0.05, "RelayAntenna50": 0.3,
        "ksp.r.largeBatteryPack": 0.02, "sensorThermometer": 0.005, "sensorBarometer": 0.005,
        "sensorGravimeter": 0.005, "sensorAccelerometer": 0.005, "LgRadialSolarPanel": 0.04, "rtg": 0.08,
        "landingLeg1": 0.05, "Decoupler.1": 0.04, "largeAdapter": 0.1, "Rockomax16.BW": 9.0,
        "liquidEngine2-2.v2": 1.75, "winglet": 0.037, "Decoupler.2": 0.16, "Rockomax32.BW": 18.0,
        "engineLargeSkipper.v2": 3.0, "R8winglet": 0.1, "liquidEngineMainsail.v2": 6.0}
FUEL = {"fuelTank": 2.0, "Rockomax16.BW": 8.0, "Rockomax32.BW": 16.0}
ENG = {"liquidEngine3.v2": (60, 85, 345), "liquidEngine2-2.v2": (250, 90, 350), "engineLargeSkipper.v2": (650, 280, 320),
       "liquidEngineMainsail.v2": (1500, 285, 310)}
parts = spec["parts"]
byid = {p["id"]: p for p in parts}

def sep_stage(p):
    """Stage at which this part leaves the root: the highest decoupler stage on its path to the root (a decoupler
    sits with the part below it: Decoupler stays with the lower stage when fired)."""
    s = 0
    q = p
    while q is not None:
        if q["part"].startswith("Decoupler"):
            s = q.get("stage", 0) if s == 0 else min(s, q.get("stage", 0))
        q = byid.get(q.get("parent")) if q.get("parent") else None
    return s

groups = {}
for p in parts:
    n = p.get("symmetry", 1)
    g = groups.setdefault(sep_stage(p), {"mass": 0.0, "fuel": 0.0, "eng": None, "n": 0, "cost": 0})
    g["mass"] += MASS[p["part"]] * n
    g["fuel"] += FUEL.get(p["part"], 0.0) * n
    g["n"] += n
    if p["part"] in ENG:
        g["eng"] = ENG[p["part"]]
total = sum(g["mass"] for g in groups.values())
print(f"\nparts {sum(g['n'] for g in groups.values())}, pad mass {total:.3f} t")
m = total
for s in sorted(groups, reverse=True):  # groups keyed by the separation stage; 0 = lander (never separates)
    pass
# burn order: the group that separates first (highest decoupler stage number among lower stages)... simpler: list
order = sorted(groups.items(), key=lambda kv: -kv[0]) if False else None
# stage numbering in the spec: 1 mainsail, 2 decA+skipper, 3 decB+poodle, 4 decC+terrier. The group below decA
# (sep 2) burns first, then sep 3, then sep 4, then the lander (sep 0).
seq = [(2, "Mainsail"), (3, "Skipper"), (4, "Poodle"), (0, "Terrier")]
m0 = total
for key, name in seq:
    g = groups[key]
    thrust, isp_sl, isp_vac = g["eng"]
    m1 = m0 - g["fuel"]
    dv_sl = isp_sl * 9.80665 * math.log(m0 / m1)
    dv_vac = isp_vac * 9.80665 * math.log(m0 / m1)
    twr_sl = thrust * isp_sl / isp_vac / (m0 * 9.80665)
    twr_vac = thrust / (m0 * 9.80665)
    bt = g["fuel"] * 1000 / (thrust * 1000 / (isp_vac * 9.80665))
    print(f"{name:8s} group mass {g['mass']:6.3f} t (fuel {g['fuel']:.1f}): {m0:7.3f} -> {m1:7.3f} t, "
          f"dv SL {dv_sl:5.0f} / vac {dv_vac:5.0f}, TWR SL {twr_sl:.2f} / vac {twr_vac:.2f}, burn {bt:.0f} s")
    m0 = m1 - g["mass"] + g["fuel"] if key != 0 else m1
print(f"lander wet {groups[0]['mass']:.3f} t, dry {groups[0]['mass'] - groups[0]['fuel']:.3f} t; "
      f"Terrier accel at Duna wet {60 / groups[0]['mass']:.1f} m/s2 (g 2.94), dry {60 / (groups[0]['mass'] - 2):.1f}")
