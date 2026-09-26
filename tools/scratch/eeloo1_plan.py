"""Offline Eeloo 1 plan check (no kRPC): Lambert scan at the window (projected like transfer_planet, and 3D), the
mid-course plane change, arrival geometry (Kerbin / Sun vs the capture periapsis, blackout arc), link distances and
the Sun angle over the mission, capture / circularize / landing dv with a finite-burn estimate, and the per-stage
rocket equation on the exact part masses of crafts/eeloo-1.json. Body constants read from the game 2026-09-27 (read-only kRPC)."""
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
MU_DRES, R_DRES, SOI_DRES, ROT_DRES = 74410814527.05, 210e3, 119082941.65, 19460.0
G_DRES = 1.6879
DAY = 21600.0
T_WIN = 43_588_306.0
T_NOW = 43_370_000.0
kerbin = Orbit(MU_SUN, 13_599_840_256, 0.0, 0.0, 0.0, 0.0, 3.14, 0.0, "Kerbin")
dres = Orbit(MU_SUN, 90_118_820_000, 0.26, math.radians(6.15), math.radians(50.0), math.radians(260.0), 3.14, 0.0, "Eeloo")


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


T_h = 1168 * DAY  # `ksp window Eeloo` (planet_window flight_time): the planner scans 0.6..1.4 x this
print(f"Hohmann-ish T {T_h / DAY:.0f} d (planner scans 0.6..1.4 x)")
print("projected scan: T d | v_inf dep | eject | plane chg | arrival v_inf | capture 40x1000 | total | Eeloo z Mm | arrival UT")
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
      f"total {tot_best:.0f}; arrival UT {T_WIN + T_best:.0f}; Eeloo {pb['z2'] / 1e6:+.0f} Mm out of plane (SOI 119)")

# 3D (unprojected) Lambert at the same T: what the ejection would cost from an inclined parking orbit
p3 = plan(T_best, projected=False)
dec = math.degrees(math.asin(_dot(_norm(p3["vi1"]), h)))
print(f"3D Lambert at T {T_best / DAY:.0f} d: eject {eject_dv(p3['vi_dep']):.0f} (v_inf {p3['vi_dep']:.0f}, declination "
      f"{dec:+.1f} deg -> parking inc >= {abs(dec):.1f}), arrival v_inf {p3['vi_arr']:.0f}, capture "
      f"{capture_dv(p3['vi_arr'], 40e3, 1000e3):.0f}, total {eject_dv(p3['vi_dep']) + capture_dv(p3['vi_arr'], 40e3, 1000e3):.0f}")

# faster transfers
print("\nfaster transfers (projected): T d | eject | plane | arrival v_inf | capture | total | extra vs best | days saved")
for Td in (700, 800, 900, 1000, 1100):
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
print(f"\nARRIVAL UT {t_arr:.0f}: Eeloo at {_mag(r2) / 1e9:.1f} Gm from the Sun (true anomaly "
      f"{math.degrees(dres.true_anomaly(t_arr)) % 360:.0f} deg), Kerbin {_mag(d_kerbin) / 1e9:.1f} Gm away, "
      f"{ang(d_kerbin, prograde):.0f} deg from Eeloo prograde, {ang(d_kerbin, d_sun):.0f} deg from the Sun")
print(f"v_inf {_mag(vinf):.0f}: {ang(vinf, prograde):.0f} deg from prograde, {ang(vinf, d_sun):.0f} deg from the Sun, "
      f"{ang(vinf, dres.normal()):.0f} deg from Eeloo's orbit normal")
print(f"solar flux at Eeloo: {(kerbin.a / _mag(r2)) ** 2:.3f} x Kerbin; OX-STAT-XL 2.8 -> {2.8 * (kerbin.a / _mag(r2)) ** 2:.2f} EC/s each")


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


# the pass plane: the planner ends with the arrival in ~our (Kerbin) plane; Eeloo's own equator is tilted 5 deg from
# it. Prograde about Eeloo's orbit normal vs retrograde.
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
print("\nKerbin-Eeloo distance and the Sun angle (Sun's disc radius from Eeloo ~0.35 deg):")
for dd in range(0, 1700, 100):
    t = T_WIN + dd * DAY
    dk = tuple(a - b for a, b in zip(kerbin.position(t), dres.position(t)))
    dsun = tuple(-x for x in dres.position(t))
    print(f"  dep+{dd:3d} d (UT {t / 1e6:.2f} M): {_mag(dk) / 1e9:5.1f} Gm, Sun-Eeloo-Kerbin {ang(dsun, dk):5.1f} deg"
          + ("  <- arrival" if abs(dd * DAY - T_best) < 30 * DAY else ""))
worst = max(_mag(tuple(a - b for a, b in zip(kerbin.position(T_WIN + d * DAY), dres.position(T_WIN + d * DAY))))
            for d in range(0, 1700))
minsun = min((ang(tuple(-x for x in dres.position(T_WIN + d * DAY)),
                  tuple(a - b for a, b in zip(kerbin.position(T_WIN + d * DAY), dres.position(T_WIN + d * DAY)))), d)
             for d in range(int(T_best / DAY), 1700))
print(f"max Kerbin-Eeloo over dep..dep+1700 d: {worst / 1e9:.1f} Gm; min Sun-Eeloo-Kerbin after arrival "
      f"{minsun[0]:.2f} deg at dep+{minsun[1]} d (Sun's disc radius {math.degrees(math.atan(R_SUN / _mag(r2))):.2f} deg)")
DSN3 = 250e9
d_arr = _mag(d_kerbin)
for name, power in (("RA-100", 100e9), ("RA-100 + HG-55", 100e9 * (115 / 100) ** 0.75), ("2 x HG-55", 15e9 * 2 ** 0.75),
                    ("HG-55 alone", 15e9)):
    rng = math.sqrt(power * DSN3)
    for d in (d_arr, worst):
        s = max(0.0, 1 - d / rng)
        s = s * s * (3 - 2 * s)
        print(f"  {name:16s} range {rng / 1e9:5.0f} Gm: at {d / 1e9:.0f} Gm strength {s:.2f}")

# ---------------------------------------------------------------- capture / orbit / landing at Eeloo
vi = _mag(vinf)
print(f"\nEeloo: v_inf {vi:.0f}")
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
spec = json.load(open(os.path.join(ROOT, "crafts", "eeloo-1.json")))
MASS = {"probeCoreOcto.v2": 0.1, "batteryBank": 0.05, "sasModule": 0.05, "science.module": 0.2, "fuelTank": 2.25,
        "fuelTank.long": 4.5, "liquidEngine3.v2": 0.5, "GooExperiment": 0.05, "RelayAntenna100": 0.65,
        "HighGainAntenna": 0.075, "ksp.r.largeBatteryPack": 0.02, "sensorThermometer": 0.005,
        "sensorBarometer": 0.005, "sensorGravimeter": 0.005, "sensorAccelerometer": 0.005, "Magnetometer": 0.05,
        "LgRadialSolarPanel": 0.04, "rtg": 0.08, "landingLeg1": 0.05, "Decoupler.1": 0.04, "largeAdapter": 0.1,
        "Rockomax16.BW": 9.0, "liquidEngine2-2.v2": 1.75, "winglet": 0.037, "Decoupler.2": 0.16,
        "Rockomax32.BW": 18.0, "engineLargeSkipper.v2": 3.0, "Size2LFB.v2": 42.5, "R8winglet": 0.1, "liquidEngineMainsail.v2": 6.0}
COST = {"probeCoreOcto.v2": 450, "batteryBank": 880, "sasModule": 600, "science.module": 1800, "fuelTank": 500,
        "fuelTank.long": 800, "liquidEngine3.v2": 390, "GooExperiment": 800, "RelayAntenna100": 3000,
        "HighGainAntenna": 1200, "ksp.r.largeBatteryPack": 550, "sensorThermometer": 900, "sensorBarometer": 880,
        "sensorGravimeter": 8800, "sensorAccelerometer": 6000, "Magnetometer": 2200, "LgRadialSolarPanel": 600,
        "rtg": 23300, "landingLeg1": 440, "Decoupler.1": 200, "largeAdapter": 500, "Rockomax16.BW": 1550,
        "liquidEngine2-2.v2": 1300, "winglet": 500, "Decoupler.2": 300, "Rockomax32.BW": 3000,
        "engineLargeSkipper.v2": 5300, "Size2LFB.v2": 17000, "R8winglet": 640, "liquidEngineMainsail.v2": 13000}
FUEL = {"Size2LFB.v2": 32.0, "fuelTank": 2.0, "fuelTank.long": 4.0, "Rockomax16.BW": 8.0, "Rockomax32.BW": 16.0}
ENG = {"Size2LFB.v2": (2000, 280, 300), "liquidEngine3.v2": (60, 85, 345), "liquidEngine2-2.v2": (250, 90, 350), "engineLargeSkipper.v2": (650, 280, 320),
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
seq = [(2, "Twin-Boar"), (3, "Skipper"), (4, "Poodle"), (0, "Terrier")]
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
print(f"lander wet {lw:.3f} t, dry {ld:.3f} t; Terrier accel wet {60 / lw:.1f} m/s2, dry {60 / ld:.1f} (Eeloo g 1.69: TWR "
      f"{60 / lw / G_DRES:.1f}-{60 / ld / G_DRES:.1f})")
# Terrier dv left after each step of the sequence (masses)
def after(m, dv):
    return m / math.exp(dv / (345 * 9.80665))
# LKO calibration: Moho 1 flew this launcher + transfer stage (lander 8.42 t) to 79.3 x 79.6 with the Poodle at 2,961
# of 3,513 (spent 552 on the orbit); Dres 1's lighter stack spent 983 of its Poodle. Same lander here + 0.6 t.
poodle_vac = None
m0 = total
for key, name in seq[:3]:
    g = groups[key]
    m1 = m0 - g["fuel"]
    if name == "Poodle":
        poodle_vac = 350 * 9.80665 * math.log(m0 / m1)
        m_poodle_full = m0
    m0 = m1 - g["mass"] + g["fuel"]
poodle_lko = poodle_vac - 552
eject = eject_dv(pb["vi_dep"]) + 40
print(f"Poodle {poodle_vac:.0f} vac - 552 (Moho 1's orbit spend) -> Poodle ~{poodle_lko:.0f} in LKO (Dres 1's stack: 1,759)")
print("Sequence (Poodle then Terrier; masses from the spec):")
mP_dry = m_poodle_full - 16 - 8  # transfer stage dry incl. lander wet
m = m_poodle_full - (poodle_vac - poodle_lko) * 0  # start of the ejection: mass after the LKO spend
m = mP_dry * math.exp(poodle_lko / (350 * 9.80665))
budget = (("ejection", int(eject)), ("mid-course", 450), ("trims", 60), ("capture 70x1000", 1700), ("pe to 20 km", 8),
          ("circularize 20 km", 170), ("landing", 1050))
stage = "Poodle"
for label, dv in budget:
    if stage == "Poodle":
        poodle_left = 350 * 9.80665 * math.log(m / mP_dry)
        if dv <= poodle_left:
            m = m / math.exp(dv / (350 * 9.80665))
            left = 350 * 9.80665 * math.log(m / mP_dry)
            print(f"  {label:20s} {dv:5d} on the Poodle: {m:6.2f} t, Poodle {left:5.0f} + Terrier 3683 left")
            continue
        rest = dv - poodle_left
        stage = "Terrier"
        m = lw / math.exp(rest / (345 * 9.80665))
        left = 345 * 9.80665 * math.log(m / ld)
        print(f"  {label:20s} {dv:5d}: Poodle {poodle_left:.0f} then Terrier {rest:.0f}: {m:6.2f} t, Terrier {left:5.0f} left")
        continue
    m = after(m, dv)
    left = 345 * 9.80665 * math.log(m / ld)
    print(f"  {label:20s} {dv:5d} on the Terrier: {m:6.2f} t, Terrier {left:5.0f} left")
tot_need = sum(d for _, d in budget)
avail = poodle_lko + 3683
print(f"need {tot_need} after LKO vs available ~{avail:.0f}: margin {avail - tot_need:.0f} ({(avail - tot_need) / tot_need * 100:.0f} %)")
print(f"Dres 1's stack for comparison: 1,759 + 3,683 = 5,442: margin {5442 - tot_need}")

# ---------------------------------------------------------------- the mid-course, done honestly (3D)
# The planner flies the projected transfer (Eeloo's arrival position dropped onto our plane). At t_pc the craft is on
# that ellipse; a 3D Lambert from there to Eeloo's real position at t_arr gives the burn and the true arrival v_inf.
print("\nMID-COURSE (3D Lambert from the projected transfer at t_pc to Eeloo's real position at t_arr). The planner's"
      "\nformula puts it ~90 deg of true anomaly before arrival (dep + 1064 d here) and prices it at the arrival speed:"
      "\non this eccentric transfer (e 0.67) that point is 127 d out, where the offset (5.1 Gm) needs a big turn."
      "\nThe single burn is cheapest around dep + 250..550 d. `correct Eeloo` (direct 3D Lambert seed) must run there.")
transfer = Orbit.from_state(MU_SUN, r1, pb["va"], T_WIN)
print("  burn at dep+d | UT | dv (m/s) | of which normal | arrival v_inf 3D | capture 70x1000 | Kerbin-craft Gm")
for dd in (50, 150, 250, 300, 350, 370, 400, 450, 550, 650, 800, 1000, 1064, 1100):
    t_pc = T_WIN + dd * DAY
    if t_pc >= t_arr - DAY:
        continue
    pos, vel = transfer.state(t_pc)
    sol = _lambert(MU_SUN, pos, pb["r2"], t_arr - t_pc, h)
    if not sol:
        print(f"  {dd:4d}: no solution")
        continue
    dvv = tuple(a - b for a, b in zip(sol[0], vel))
    vi3 = tuple(a - b for a, b in zip(sol[1], pb["v2d"]))
    print(f"  {dd:4d} d | {t_pc:.0f} | {_mag(dvv):5.0f} | {abs(_dot(dvv, h)):5.0f} | {_mag(vi3):5.0f} | "
          f"{capture_dv(_mag(vi3), 70e3, 1000e3):5.0f} | {_mag(tuple(a - b for a, b in zip(pos, kerbin.position(t_pc)))) / 1e9:5.1f}")
print("honest total over T (eject + best single mid-course + capture 70x1000 at the 3D v_inf after it):")
print("  T d | eject | best t_pc dep+d | dv_pc | v_inf | capture | total | arrival UT")
for Td in (900, 1000, 1100, 1191, 1300, 1400):
    T = Td * DAY
    p = plan(T)
    if not p:
        continue
    tr = Orbit.from_state(MU_SUN, r1, p["va"], T_WIN)
    ta = T_WIN + T
    bestpc = None
    for dd in range(20, Td - 20, 10):
        t_pc = T_WIN + dd * DAY
        pos, vel = tr.state(t_pc)
        sol = _lambert(MU_SUN, pos, p["r2"], ta - t_pc, h)
        if not sol:
            continue
        dvv = _mag(tuple(a - b for a, b in zip(sol[0], vel)))
        vi3 = _mag(tuple(a - b for a, b in zip(sol[1], p["v2d"])))
        tot = eject_dv(p["vi_dep"]) + dvv + capture_dv(vi3, 70e3, 1000e3)
        if bestpc is None or tot < bestpc[0]:
            bestpc = (tot, dd, dvv, vi3)
    tot, dd, dvv, vi3 = bestpc
    print(f"  {Td:4d} | {eject_dv(p['vi_dep']):5.0f} | {dd:5d} | {dvv:5.0f} | {vi3:5.0f} | {capture_dv(vi3, 70e3, 1000e3):5.0f} | {tot:5.0f} | {ta:.0f}")
# capture at 70 km (the whole 70 x 1,000 km orbit is "high": Eeloo's low-space line is 60 km) vs 40 km
for vi_ in (2200, 2300):
    print(f"capture at v_inf {vi_}: pe 70 km -> x1000 {capture_dv(vi_, 70e3, 1000e3):.0f}, pe 40 km {capture_dv(vi_, 40e3, 1000e3):.0f}")
rp70, ra = R_DRES + 70e3, R_DRES + 1000e3
v_ap_70 = math.sqrt(MU_DRES * (2 / ra - 2 / (rp70 + ra)))
print(f"70x1000 -> 20x1000 at the ap: {v_ap_70 - v_ap_20:.1f} m/s (period 70x1000 {2 * math.pi * math.sqrt(((rp70 + ra) / 2) ** 3 / MU_DRES) / 3600:.2f} h); "
      f"surface speed at the equator {2 * math.pi * R_DRES / ROT_DRES:.0f} m/s")

# ---------------------------------------------------------------- conjunctions, hourly
print("\nSun-Eeloo-Kerbin angle, hourly, around the daily minima (Sun's disc from Eeloo ~0.22 deg, Kerbin's offset ~0.5 deg):")
for centre in (600, 1299):
    best = None
    for hh in range(-72 * 6, 72 * 6):
        t = T_WIN + centre * DAY + hh * 600
        dk = tuple(a - b for a, b in zip(kerbin.position(t), dres.position(t)))
        a = ang(tuple(-x for x in dres.position(t)), dk)
        if best is None or a < best[0]:
            best = (a, t)
    # Kerbin's angular offset from the Sun's centre as seen from Eeloo must exceed the Sun's angular radius
    rs = math.degrees(math.atan(R_SUN / _mag(dres.position(best[1]))))
    print(f"  dep+{centre} d: min {best[0]:.3f} deg at UT {best[1]:.0f} (Sun's radius {rs:.2f} deg -> "
          f"{'BLACKOUT' if best[0] < rs else 'clear'})")
