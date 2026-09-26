"""Offline Dres 1 plan check (no kRPC): Lambert scan at the window (projected like transfer_planet, and 3D), the
mid-course plane change, arrival geometry (Kerbin / Sun vs the capture periapsis, blackout arc), link distances and
the Sun angle over the mission, capture / circularize / landing dv with a finite-burn estimate, and the per-stage
rocket equation on the exact part masses of crafts/dres-1.json. Body constants read from the game 2026-09-27."""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from kspbot.kepler import Orbit, _cross, _dot, _mag, _norm, rotate  # noqa: E402
from kspbot.flight import _lambert  # noqa: E402

MU_SUN = 1.1723327948324905e18
R_SUN = 261.6e6
MU_KERBIN, R_KERBIN = 3.5316e12, 600e3
MU_DRES, R_DRES, SOI_DRES, ROT_DRES = 21484488600.0, 138e3, 32832839.58, 34800.0
G_DRES = 1.1285
DAY = 21600.0
T_WIN = 43_122_323.0
T_NOW = 42_350_000.0
kerbin = Orbit(MU_SUN, 13_599_840_256, 0.0, 0.0, 0.0, 0.0, 3.14, 0.0, "Kerbin")
dres = Orbit(MU_SUN, 40_839_348_203, 0.145, math.radians(5.0), math.radians(280.0), math.radians(90.0), 3.14, 0.0, "Dres")


def eject_dv(vinf, mu=MU_KERBIN, r=R_KERBIN + 80e3):
    return math.sqrt(vinf ** 2 + 2 * mu / r) - math.sqrt(mu / r)


def capture_dv(vinf, pe_alt, apo_alt=None):
    rp = R_DRES + pe_alt
    v_pe = math.sqrt(vinf ** 2 + 2 * MU_DRES / rp)
    ra = rp if apo_alt is None else R_DRES + apo_alt
    return v_pe - math.sqrt(MU_DRES * (2 / rp - 2 / (rp + ra)))


def ang(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, _dot(_norm(a), _norm(b))))))


# ---------------------------------------------------------------- Lambert scan (planner style: projected)
a_t = (kerbin.a + dres.radius_at(0)) / 2
r1, v1k = kerbin.state(T_WIN)
h = kerbin.normal()
R1 = _mag(r1)


def plan(T, projected=True):
    r2, v2d = dres.state(T_WIN + T)
    z2 = _dot(r2, h)
    r2p = tuple(x - z2 * y for x, y in zip(r2, h)) if projected else r2
    sol = _lambert(MU_SUN, r1, r2p, T, h)
    if not sol:
        return None
    va, vb = sol
    vi1 = tuple(a - b for a, b in zip(va, v1k))
    vi2 = tuple(a - b for a, b in zip(vb, v2d))
    R2 = _mag(r2)
    # planner's plane-change term: tilt z2/R2 at ~arrival speed of the transfer ellipse
    dv_pc = abs(z2) / R2 * math.sqrt(MU_SUN * (2 / R2 - 2 / (R1 + R2))) if projected else 0.0
    return dict(T=T, vi1=vi1, vi_dep=_mag(vi1), vi_arr=_mag(vi2), z2=z2, dv_pc=dv_pc, R2=R2, va=va, vb=vb, r2=r2,
                v2d=v2d, vinf=vi2)


T_h = math.pi * math.sqrt(((R1 + dres.radius_at(dres.true_anomaly(T_WIN + 600 * DAY))) / 2) ** 3 / MU_SUN)
print(f"Hohmann-ish T {T_h / DAY:.0f} d (planner scans 0.6..1.4 x)")
print("projected scan: T d | v_inf dep | eject | plane chg | arrival v_inf | capture 40x1000 | total | Dres z Mm | arrival UT")
rows = []
for i in range(0, 41):
    T = T_h * (0.6 + 0.02 * i)
    p = plan(T)
    if not p:
        continue
    tot = eject_dv(p["vi_dep"]) + p["dv_pc"] + capture_dv(p["vi_arr"], 40e3, 1000e3)
    rows.append((T, tot, p))
    if i % 2 == 0:
        print(f"  {T / DAY:6.0f} {p['vi_dep']:6.0f} {eject_dv(p['vi_dep']):6.0f} {p['dv_pc']:6.0f} {p['vi_arr']:6.0f} "
              f"{capture_dv(p['vi_arr'], 40e3, 1000e3):6.0f} {tot:6.0f} {p['z2'] / 1e6:+8.0f} {T_WIN + T:12.0f}")
best = min(rows, key=lambda r: r[1])
T_best, tot_best, pb = best
print(f"\nBEST projected: T {T_best / DAY:.0f} d, eject {eject_dv(pb['vi_dep']):.0f} (v_inf {pb['vi_dep']:.0f}), plane "
      f"change {pb['dv_pc']:.0f}, arrival v_inf {pb['vi_arr']:.0f}, capture {capture_dv(pb['vi_arr'], 40e3, 1000e3):.0f}, "
      f"total {tot_best:.0f}; arrival UT {T_WIN + T_best:.0f}; Dres {pb['z2'] / 1e6:+.0f} Mm out of plane (SOI 32.8)")

# 3D (unprojected) Lambert at the same T: what the ejection would cost from an inclined parking orbit
p3 = plan(T_best, projected=False)
dec = math.degrees(math.asin(_dot(_norm(p3["vi1"]), h)))
print(f"3D Lambert at T {T_best / DAY:.0f} d: eject {eject_dv(p3['vi_dep']):.0f} (v_inf {p3['vi_dep']:.0f}, declination "
      f"{dec:+.1f} deg -> parking inc >= {abs(dec):.1f}), arrival v_inf {p3['vi_arr']:.0f}, capture "
      f"{capture_dv(p3['vi_arr'], 40e3, 1000e3):.0f}, total {eject_dv(p3['vi_dep']) + capture_dv(p3['vi_arr'], 40e3, 1000e3):.0f}")

# faster transfers
print("\nfaster transfers (projected): T d | eject | plane | arrival v_inf | capture | total | extra vs best | days saved")
for Td in (400, 450, 500, 550, 600):
    p = plan(Td * DAY)
    if not p:
        continue
    tot = eject_dv(p["vi_dep"]) + p["dv_pc"] + capture_dv(p["vi_arr"], 40e3, 1000e3)
    print(f"  {Td:4d} {eject_dv(p['vi_dep']):6.0f} {p['dv_pc']:6.0f} {p['vi_arr']:6.0f} "
          f"{capture_dv(p['vi_arr'], 40e3, 1000e3):6.0f} {tot:6.0f} {tot - tot_best:+6.0f} {(T_best - Td * DAY) / DAY:6.0f}")

# where is the mid-course plane change (planner formula)
R2 = pb["R2"]
e_t = abs(R1 - R2) / (R1 + R2)
E = 2 * math.atan(math.sqrt((1 - e_t) / (1 + e_t)))
t_pc = T_WIN + T_best - (E - e_t * math.sin(E)) / math.pi * T_best
print(f"planner's mid-course UT ~{t_pc:.0f} (dep + {(t_pc - T_WIN) / DAY:.0f} d, {(T_WIN + T_best - t_pc) / DAY:.0f} d before arrival)")

# ---------------------------------------------------------------- arrival geometry (3D Lambert velocities)
t_arr = T_WIN + T_best
p = p3
r2, v2d, vinf = p["r2"], p["v2d"], p["vinf"]
rk = kerbin.position(t_arr)
d_kerbin = tuple(a - b for a, b in zip(rk, r2))
d_sun = tuple(-x for x in r2)
prograde = _norm(v2d)
print(f"\nARRIVAL UT {t_arr:.0f}: Dres at {_mag(r2) / 1e9:.1f} Gm from the Sun (true anomaly "
      f"{math.degrees(dres.true_anomaly(t_arr)) % 360:.0f} deg), Kerbin {_mag(d_kerbin) / 1e9:.1f} Gm away, "
      f"{ang(d_kerbin, prograde):.0f} deg from Dres prograde, {ang(d_kerbin, d_sun):.0f} deg from the Sun")
print(f"v_inf {_mag(vinf):.0f}: {ang(vinf, prograde):.0f} deg from prograde, {ang(vinf, d_sun):.0f} deg from the Sun, "
      f"{ang(vinf, dres.normal()):.0f} deg from Dres's orbit normal")
print(f"solar flux at Dres: {(kerbin.a / _mag(r2)) ** 2:.3f} x Kerbin; OX-STAT-XL 2.8 -> {2.8 * (kerbin.a / _mag(r2)) ** 2:.2f} EC/s each")


def hyperbola_pe_dir(vinf, hn, r_pe, mu=MU_DRES):
    v = _mag(vinf)
    e = 1 + r_pe * v * v / mu
    th = math.acos(-1 / e)
    u_in = _norm(tuple(-x for x in vinf))
    return rotate(u_in, hn, th), e, th


def blackout(P, hn, e, r_pe, d_k):
    Q = _cross(hn, P)
    pp = r_pe * (1 + e)
    k = _norm(d_k)
    hidden = []
    for nu_deg in range(-120, 121):
        nu = math.radians(nu_deg)
        r = pp / (1 + e * math.cos(nu))
        pos = tuple(r * (math.cos(nu) * a + math.sin(nu) * b) for a, b in zip(P, Q))
        if _dot(pos, k) < 0 and _mag(_cross(pos, k)) < R_DRES:
            hidden.append(nu_deg)
    return (min(hidden), max(hidden)) if hidden else None


# the pass plane: the planner ends with the arrival in ~our (Kerbin) plane; Dres's own equator is tilted 5 deg from
# it. Prograde about Dres's orbit normal vs retrograde.
hd = dres.normal()
for label, hn in (("prograde", hd), ("retrograde", tuple(-x for x in hd))):
    for pe_alt in (40e3,):
        P, e, th = hyperbola_pe_dir(vinf, hn, R_DRES + pe_alt)
        bo = blackout(P, hn, e, R_DRES + pe_alt, d_kerbin)
        el = 90 - ang(P, d_kerbin)
        sun = 90 - ang(P, d_sun)
        print(f"{label} pass, pe {pe_alt / 1e3:.0f} km: e {e:.1f}, Kerbin elevation at the sub-pe point {el:+.0f} deg, "
              f"Sun elevation {sun:+.0f} deg, pe {ang(P, prograde):.0f} deg from prograde; Kerbin hidden over nu {bo}")
        # time from pe to the hidden arc
        if bo:
            for nu_deg in bo:
                nu = math.radians(nu_deg)
                H = 2 * math.atanh(math.sqrt((e - 1) / (e + 1)) * math.tan(nu / 2))
                n = math.sqrt(MU_DRES / ((R_DRES + pe_alt) / (e - 1)) ** 3)
                print(f"    nu {nu_deg:+d} deg = pe {(e * math.sinh(H) - H) / n:+.0f} s")

# ---------------------------------------------------------------- link and Sun over the mission
print("\nKerbin-Dres distance and the Sun angle (Sun's disc radius from Dres ~0.35 deg):")
for dd in range(0, 900, 60):
    t = T_WIN + dd * DAY
    dk = tuple(a - b for a, b in zip(kerbin.position(t), dres.position(t)))
    dsun = tuple(-x for x in dres.position(t))
    print(f"  dep+{dd:3d} d (UT {t / 1e6:.2f} M): {_mag(dk) / 1e9:5.1f} Gm, Sun-Dres-Kerbin {ang(dsun, dk):5.1f} deg"
          + ("  <- arrival" if abs(dd * DAY - T_best) < 30 * DAY else ""))
worst = max(_mag(tuple(a - b for a, b in zip(kerbin.position(T_WIN + d * DAY), dres.position(T_WIN + d * DAY))))
            for d in range(0, 900))
minsun = min((ang(tuple(-x for x in dres.position(T_WIN + d * DAY)),
                  tuple(a - b for a, b in zip(kerbin.position(T_WIN + d * DAY), dres.position(T_WIN + d * DAY)))), d)
             for d in range(int(T_best / DAY), 900))
print(f"max Kerbin-Dres over dep..dep+900 d: {worst / 1e9:.1f} Gm; min Sun-Dres-Kerbin after arrival "
      f"{minsun[0]:.2f} deg at dep+{minsun[1]} d (Sun's disc radius {math.degrees(math.atan(R_SUN / _mag(r2))):.2f} deg)")
DSN3 = 250e9
for name, power in (("RA-100", 100e9), ("RA-100 + HG-55", 100e9 * (115 / 100) ** 0.75), ("2 x HG-55", 15e9 * 2 ** 0.75),
                    ("HG-55 alone", 15e9)):
    rng = math.sqrt(power * DSN3)
    for d in (44e9, worst):
        s = max(0.0, 1 - d / rng)
        s = s * s * (3 - 2 * s)
        print(f"  {name:16s} range {rng / 1e9:5.0f} Gm: at {d / 1e9:.0f} Gm strength {s:.2f}")

# ---------------------------------------------------------------- capture / orbit / landing at Dres
vi = _mag(vinf)
print(f"\nDres: v_inf {vi:.0f}")
for pe_alt in (20e3, 40e3):
    rp = R_DRES + pe_alt
    v_pe = math.sqrt(vi ** 2 + 2 * MU_DRES / rp)
    print(f"  pe {pe_alt / 1e3:.0f} km: v_pe {v_pe:.0f}, e_hyp {1 + rp * vi * vi / MU_DRES:.1f}, capture to x1000 km "
          f"{capture_dv(vi, pe_alt, 1000e3):.0f}, circular {capture_dv(vi, pe_alt):.0f}; v_circ {math.sqrt(MU_DRES / rp):.0f}, "
          f"period {2 * math.pi * math.sqrt(rp ** 3 / MU_DRES) / 60:.1f} min")
    for vi2 in (1400, 1800, 2000):
        print(f"     at v_inf {vi2}: capture to x1000 {capture_dv(vi2, pe_alt, 1000e3):.0f}")
# SOI entry to pe
a_h = -MU_DRES / vi ** 2
e_h = 1 + (R_DRES + 40e3) * vi * vi / MU_DRES
nu_soi = math.acos((a_h * (1 - e_h * e_h) / SOI_DRES - 1) / e_h)
H = 2 * math.atanh(math.sqrt((e_h - 1) / (e_h + 1)) * math.tan(nu_soi / 2))
t_soi = (e_h * math.sinh(H) - H) / math.sqrt(MU_DRES / (-a_h) ** 3)
print(f"  SOI edge (32.8 Mm) to pe: {t_soi / 3600:.1f} h")
# 40 x 1000 -> lower pe to 20 km at the ap, circularize at 20 km
rp40, rp20, ra = R_DRES + 40e3, R_DRES + 20e3, R_DRES + 1000e3
v_ap_40 = math.sqrt(MU_DRES * (2 / ra - 2 / (rp40 + ra)))
v_ap_20 = math.sqrt(MU_DRES * (2 / ra - 2 / (rp20 + ra)))
v_pe_20e = math.sqrt(MU_DRES * (2 / rp20 - 2 / (rp20 + ra)))
v_c20 = math.sqrt(MU_DRES / rp20)
print(f"  40x1000 -> 20x1000 at the ap: {v_ap_40 - v_ap_20:.1f} m/s; circularize at 20 km: {v_pe_20e - v_c20:.0f} m/s "
      f"(period 40x1000: {2 * math.pi * math.sqrt(((rp40 + ra) / 2) ** 3 / MU_DRES) / 3600:.2f} h)")
# landing from 20 km circular: kill v_circ, free fall, suicide burn (3 m/s2 cap) + hover
h0 = 20e3
v_fall = math.sqrt(2 * G_DRES * h0)
print(f"  landing from 20 km circular: kill {v_c20:.0f} + free fall {v_fall:.0f} (+ gravity loss during the kill ~"
      f"{G_DRES * v_c20 / 7.0:.0f} at 7 m/s2) + hover ~40 -> ~{v_c20 + v_fall + G_DRES * v_c20 / 7.0 + 40:.0f} m/s")
# finite-burn loss for the capture at Terrier acceleration: integrate a retrograde burn centred on the pe
def finite_capture(vi, pe_alt, accel, dv_target, apo_alt=1000e3):
    """Integrate a constant-acceleration retrograde burn of dv_target centred (by half-dv) on the pe; returns the
    resulting apoapsis altitude (km) and the impulsive dv that would give apo_alt."""
    rp = R_DRES + pe_alt
    e = 1 + rp * vi * vi / MU_DRES
    a = -MU_DRES / vi ** 2
    hyp = Orbit(MU_DRES, a, e, 0.0, 0.0, 0.0, 0.0, 0.0)
    T = dv_target / accel
    t0 = -T / 2
    pos, vel = hyp.state(t0)
    dt = 0.5
    t = t0
    while t < t0 + T:
        v_hat = _norm(vel)
        r = _mag(pos)
        acc = tuple(-MU_DRES * x / r ** 3 - accel * y for x, y in zip(pos, v_hat))
        vel = tuple(a_ + b * dt for a_, b in zip(vel, acc))
        pos = tuple(a_ + b * dt for a_, b in zip(pos, vel))
        t += dt
    o = Orbit.from_state(MU_DRES, pos, vel, t)
    return (o.apoapsis - R_DRES) / 1e3 if o.e < 1 else float("inf"), o.periapsis - R_DRES
for accel in (7.5, 12.0):
    dv_imp = capture_dv(vi, 40e3, 1000e3)
    for extra in (0, 30, 60, 100):
        apo, pe_after = finite_capture(vi, 40e3, accel, dv_imp + extra)
        print(f"  finite capture at {accel} m/s2, dv {dv_imp + extra:.0f} ({dv_imp:.0f} + {extra}): apo {apo:.0f} km, pe {pe_after / 1e3:.1f} km")

# ---------------------------------------------------------------- stages from the spec
spec = json.load(open(os.path.join(ROOT, "crafts", "dres-1.json")))
MASS = {"probeCoreOcto.v2": 0.1, "batteryBank": 0.05, "sasModule": 0.05, "science.module": 0.2, "fuelTank": 2.25,
        "fuelTank.long": 4.5, "liquidEngine3.v2": 0.5, "GooExperiment": 0.05, "RelayAntenna100": 0.65,
        "HighGainAntenna": 0.075, "ksp.r.largeBatteryPack": 0.02, "sensorThermometer": 0.005,
        "sensorBarometer": 0.005, "sensorGravimeter": 0.005, "sensorAccelerometer": 0.005, "Magnetometer": 0.05,
        "LgRadialSolarPanel": 0.04, "rtg": 0.08, "landingLeg1": 0.05, "Decoupler.1": 0.04, "largeAdapter": 0.1,
        "Rockomax16.BW": 9.0, "liquidEngine2-2.v2": 1.75, "winglet": 0.037, "Decoupler.2": 0.16,
        "Rockomax32.BW": 18.0, "engineLargeSkipper.v2": 3.0, "R8winglet": 0.1, "liquidEngineMainsail.v2": 6.0}
COST = {"probeCoreOcto.v2": 450, "batteryBank": 880, "sasModule": 600, "science.module": 1800, "fuelTank": 500,
        "fuelTank.long": 800, "liquidEngine3.v2": 390, "GooExperiment": 800, "RelayAntenna100": 3000,
        "HighGainAntenna": 1200, "ksp.r.largeBatteryPack": 550, "sensorThermometer": 900, "sensorBarometer": 880,
        "sensorGravimeter": 8800, "sensorAccelerometer": 6000, "Magnetometer": 2200, "LgRadialSolarPanel": 600,
        "rtg": 23300, "landingLeg1": 440, "Decoupler.1": 200, "largeAdapter": 500, "Rockomax16.BW": 1550,
        "liquidEngine2-2.v2": 1300, "winglet": 500, "Decoupler.2": 300, "Rockomax32.BW": 3000,
        "engineLargeSkipper.v2": 5300, "R8winglet": 640, "liquidEngineMainsail.v2": 13000}
FUEL = {"fuelTank": 2.0, "fuelTank.long": 4.0, "Rockomax16.BW": 8.0, "Rockomax32.BW": 16.0}
ENG = {"liquidEngine3.v2": (60, 85, 345), "liquidEngine2-2.v2": (250, 90, 350), "engineLargeSkipper.v2": (650, 280, 320),
       "liquidEngineMainsail.v2": (1500, 285, 310)}
parts = spec["parts"]
byid = {p["id"]: p for p in parts}


def sep_stage(p):
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
    g["cost"] += COST[p["part"]] * n
    if p["part"] in ENG:
        g["eng"] = ENG[p["part"]]
total = sum(g["mass"] for g in groups.values())
print(f"\nSPEC: parts {sum(g['n'] for g in groups.values())}, pad mass {total:.3f} t, cost {sum(g['cost'] for g in groups.values())} "
      f"(+ fuel ~{sum(g['fuel'] for g in groups.values()) * 1000 / 9 * 0.8 * 0.9:.0f})")
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
    print(f"{name:8s} group {g['mass']:6.3f} t (fuel {g['fuel']:.1f}): {m0:7.3f} -> {m1:7.3f} t, dv SL {dv_sl:5.0f} / vac "
          f"{dv_vac:5.0f}, TWR SL {twr_sl:.2f} / vac {twr_vac:.2f}, burn {bt:.0f} s")
    m0 = m1 - g["mass"] + g["fuel"] if key != 0 else m1
lw, ld = groups[0]["mass"], groups[0]["mass"] - groups[0]["fuel"]
print(f"lander wet {lw:.3f} t, dry {ld:.3f} t; Terrier accel wet {60 / lw:.1f} m/s2, dry {60 / ld:.1f} (Dres g 1.13: TWR "
      f"{60 / lw / G_DRES:.1f}-{60 / ld / G_DRES:.1f})")
# Terrier dv left after each step of the sequence (masses)
def after(m, dv):
    return m / math.exp(dv / (345 * 9.80665))
# LKO calibration: Duna 1 on this launcher flew Mainsail 1,324 of 1,434 SL (0.923), Skipper 1,494 of 1,546 SL (0.966),
# Poodle 441: 3,259 to a 80 km orbit
sl = {}
m0 = total
for key, name in seq[:3]:
    g = groups[key]
    thrust, isp_sl, isp_vac = g["eng"]
    m1 = m0 - g["fuel"]
    sl[name] = (isp_sl * 9.80665 * math.log(m0 / m1), isp_vac * 9.80665 * math.log(m0 / m1))
    m0 = m1 - g["mass"] + g["fuel"]
launcher_eff = 0.923 * sl["Mainsail"][0] + 0.966 * sl["Skipper"][0]
poodle_lko = sl["Poodle"][1] - (3259 - launcher_eff)
print(f"launcher effective ~{launcher_eff:.0f} (Duna 1 calibration) -> Poodle spends ~{3259 - launcher_eff:.0f} on the "
      f"orbit -> Poodle ~{poodle_lko:.0f} in LKO; ejection ~1,650 executed -> Terrier finishes ~{max(0, 1650 - poodle_lko):.0f}")
print("Terrier sequence (lander alone from the ejection remainder):")
m = lw
for label, dv in (("ejection remainder", int(max(0, 1650 - poodle_lko))), ("mid-course plane change", 250), ("trims", 60), ("capture 40x1000", 1250),
                  ("pe to 20 km", 8), ("circularize 20 km", 150), ("landing", 650)):
    m = after(m, dv)
    left = 345 * 9.80665 * math.log(m / ld)
    print(f"  after {label:24s} {dv:5d}: mass {m:.2f} t, Terrier {left:5.0f} m/s left")
