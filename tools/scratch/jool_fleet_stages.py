"""Jool fleet, part 4 (offline): the pad check. Rocket equation per stage on the exact part masses of
crafts/jool-*.json (part stats as `ksp parts` prints them, 2026-09-27), part count, cost, LKO calibration from the
flown stacks, and the dv budget walked through the stages.
Run: uv run python tools/scratch/jool_fleet_stages.py"""
import json
import math
import os

from jool_fleet_common import G0, ROOT

# name: (wet mass t, fuel t, cost)
PART = {
    "probeCoreOcto.v2": (0.1, 0, 450), "batteryBank": (0.05, 0, 880), "sasModule": (0.05, 0, 600),
    "advSasModule": (0.1, 0, 1200), "noseCone": (0.03, 0, 240),
    "fuelTank.long": (4.5, 4.0, 800), "fuelTank": (2.25, 2.0, 500), "fuelTankSmall": (1.125, 1.0, 275),
    "Rockomax8BW": (4.5, 4.0, 800), "Rockomax16.BW": (9.0, 8.0, 1550), "Rockomax32.BW": (18.0, 16.0, 3000),
    "Rockomax64.BW": (36.0, 32.0, 5750), "Size3SmallTank": (20.25, 18.0, 3250), "Size3MediumTank": (40.5, 36.0, 6500),
    "Size3LargeTank": (81.0, 72.0, 13000), "Size3To2Adapter.v2": (16.875, 15.0, 1623),
    "Size2LFB.v2": (42.5, 32.0, 17000),
    "liquidEngine3.v2": (0.5, 0, 390), "liquidEngine2-2.v2": (1.75, 0, 1300), "engineLargeSkipper.v2": (3.0, 0, 5300),
    "liquidEngineMainsail.v2": (6.0, 0, 13000), "Size3AdvancedEngine": (9.0, 0, 25000),
    "Size3EngineCluster": (15.0, 0, 39000),
    "HighGainAntenna": (0.075, 0, 1200), "RelayAntenna100": (0.65, 0, 3000), "commDish": (0.1, 0, 1500),
    "ksp.r.largeBatteryPack": (0.02, 0, 550), "LgRadialSolarPanel": (0.04, 0, 600), "solarPanels5": (0.005, 0, 75),
    "rtg": (0.08, 0, 23300),
    "science.module": (0.2, 0, 1800), "GooExperiment": (0.05, 0, 800), "sensorThermometer": (0.005, 0, 900),
    "sensorBarometer": (0.005, 0, 880), "sensorGravimeter": (0.005, 0, 8800), "sensorAccelerometer": (0.005, 0, 6000),
    "sensorAtmosphere": (0.005, 0, 6500), "Magnetometer": (0.05, 0, 2200),
    "landingLeg1": (0.05, 0, 440), "landingLeg1-2": (0.1, 0, 340), "parachuteRadial": (0.1, 0, 400),
    "InflatableHeatShield": (1.5, 0, 2400),
    "Decoupler.1": (0.04, 0, 200), "Decoupler.2": (0.16, 0, 300), "Decoupler.3": (0.36, 0, 375),
    "largeAdapter": (0.1, 0, 500),
    "winglet": (0.037, 0, 500), "R8winglet": (0.1, 0, 640), "tailfin": (0.125, 0, 600),
}
# engine: (vacuum thrust kN, Isp SL, Isp vac)
ENG = {"liquidEngine3.v2": (60, 85, 345), "liquidEngine2-2.v2": (250, 90, 350), "engineLargeSkipper.v2": (650, 280, 320),
       "liquidEngineMainsail.v2": (1500, 285, 310), "Size2LFB.v2": (2000, 280, 300),
       "Size3AdvancedEngine": (2000, 205, 340), "Size3EngineCluster": (4000, 295, 315)}


def load(slug):
    return json.load(open(os.path.join(ROOT, "crafts", slug + ".json")))


def groups(spec):
    """Parts grouped by the stage of the decoupler that drops them (0: never dropped), TD decouplers with the part
    below them; [(key, dict)] in firing order, the final vehicle last."""
    parts = spec["parts"]
    byid = {p["id"]: p for p in parts}

    def key(p):
        s, q = 0, p
        while q is not None:
            if q["part"].startswith("Decoupler"):
                st = q.get("stage", 0)
                s = st if s == 0 else min(s, st)
            q = byid.get(q.get("parent"))
        return s
    g = {}
    for p in parts:
        n = p.get("symmetry", 1)
        m, f, c = PART[p["part"]]
        d = g.setdefault(key(p), dict(mass=0.0, fuel=0.0, n=0, cost=0, eng=None, names=[]))
        d["mass"] += m * n
        d["fuel"] += f * n
        d["n"] += n
        d["cost"] += c * n
        d["names"].append(p["id"])
        if p["part"] in ENG:
            d["eng"] = (p["part"],) + ENG[p["part"]]
    order = sorted(k for k in g if k) + [0]
    return [(k, g[k]) for k in order]


def table(slug, names):
    spec = load(slug)
    gs = groups(spec)
    total = sum(d["mass"] for _, d in gs)
    n = sum(d["n"] for _, d in gs)
    cost = sum(d["cost"] for _, d in gs)
    print(f"\n=== {spec['name']} ({slug}.json): {n} parts, pad mass {total:.3f} t, cost {cost:,} funds (fuel included)")
    rows = []
    m0 = total
    for (k, d), name in zip(gs, names):
        if d["eng"] is None:
            print(f"  {name:10s} group {d['mass']:7.3f} t: no engine ({d['names']})")
            m0 -= d["mass"]
            continue
        part, thrust, isl, ivac = d["eng"]
        m1 = m0 - d["fuel"]
        dv_sl, dv_vac = isl * G0 * math.log(m0 / m1), ivac * G0 * math.log(m0 / m1)
        twr_sl, twr_vac = thrust * isl / ivac / (m0 * G0), thrust / (m0 * G0)
        bt = d["fuel"] * 1000 / (thrust * 1000 / (ivac * G0))
        print(f"  {name:10s} group {d['mass']:7.3f} t, fuel {d['fuel']:5.1f}: {m0:8.3f} -> {m1:8.3f} t, dv SL {dv_sl:5.0f} / "
              f"vac {dv_vac:5.0f}, TWR SL {twr_sl:.2f} / vac {twr_vac:.2f}, a {thrust / m0:.1f} -> {thrust / m1:.1f} m/s2, "
              f"burn {bt:.0f} s, cost {d['cost']:,}, parts {d['n']}")
        rows.append(dict(name=name, m0=m0, m1=m1, dv_sl=dv_sl, dv_vac=dv_vac, thrust=thrust, isp=ivac, fuel=d["fuel"],
                         mass=d["mass"]))
        m0 = m1 - (d["mass"] - d["fuel"])
    return rows, total, n, cost


def walk(rows, start, budget, first=None):
    """Spend the budget [(label, dv)] through the stages rows[start:], the first one holding `first` m/s (after the
    LKO top-up). Prints what is left after each item."""
    st = [dict(r) for r in rows[start:]]
    left = [r["dv_vac"] for r in st]
    if first is not None:
        left[0] = first
    i = 0
    for label, dv in budget:
        need = dv
        used = []
        while need > 1e-9 and i < len(st):
            take = min(need, left[i])
            left[i] -= take
            need -= take
            used.append(f"{st[i]['name']} {take:.0f}")
            if left[i] <= 1e-9 and need > 1e-9:
                i += 1
        print(f"    {label:28s} {dv:5.0f}: " + " + ".join(used) + " -> left "
              + " / ".join(f"{st[j]['name']} {left[j]:.0f}" for j in range(len(st)) if left[j] > 0.5)
              + ("   SHORT by %.0f" % need if need > 1e-9 else ""))
    tot = sum(d for _, d in budget)
    avail = (first if first is not None else st[0]["dv_vac"]) + sum(r["dv_vac"] for r in st[1:])
    print(f"    need {tot:.0f} vs {avail:.0f} after LKO: margin {avail - tot:.0f} m/s ({(avail - tot) / tot * 100:.0f} %)")
    return left


COMMON = [("ejection (node ~1,935)", 1980), ("mid-course (plane, pe, timing)", 140), ("trim 20 d before the SOI", 30)]
BUDGET = {
    "jool-vall": COMMON + [("moon targeting in Jool's SOI", 70), ("trims before / in Vall's SOI", 30),
                           ("capture 100 x 1,000 km", 910), ("pe to 20 km at the ap", 23), ("circularize 20 km", 215),
                           ("landing (land, from 20 km)", 1250)],
    "jool-pol": COMMON + [("moon targeting in Jool's SOI", 120), ("trims before / in Pol's SOI", 30),
                          ("capture 25 x 100 km", 1225), ("circularize 15 km", 20), ("landing (land, from 15 km)", 200)],
    "jool-bop": COMMON + [("moon targeting in Jool's SOI", 120), ("trims before / in Bop's SOI", 30),
                          ("capture 30 x 100 km", 1250), ("circularize 30 km", 15), ("landing (land, from 30 km)", 310)],
    "jool-tylo": [("ejection (node ~1,935, 295 s burn)", 2020)] + COMMON[1:]
    + [("moon targeting in Jool's SOI", 150), ("trims before / in Tylo's SOI", 30),
       ("capture 50 x 1,000 km", 760), ("circularize 50 km", 405), ("50 -> 30 km circular", 20),
       ("landing (land as it is, 30 km)", 3310)],
    "jool-laythe": COMMON + [("moon targeting in Jool's SOI", 40), ("trims before / in Laythe's SOI", 30),
                             ("capture 80 x 2,000 km", 765), ("circularize 80 km", 505), ("deorbit to pe 25 km", 46)],
}
NAMES = {
    "jool-vall": ("Mainsail", "Skipper", "Poodle", "Terrier"),
    "jool-pol": ("Mainsail", "Skipper", "Poodle", "Terrier"),
    "jool-bop": ("Mainsail", "Skipper", "Poodle", "Terrier"),
    "jool-tylo": ("Mammoth", "Rhino", "Poodle T", "Poodle A", "Terrier B"),
    "jool-laythe": ("Twin-Boar", "Skipper", "Poodle", "Terrier", "lander"),
}
# Poodle (transfer stage) dv spent on the orbit: flown stacks. Dres 1 (#51): 2,742 -> 1,759 (983). Eve 2's launcher
# (#49): SL1 + vac2 3,260-3,300 reached LKO with the Poodle untouched and 150-250 in the Skipper; Duna 2: SL1 + vac2
# 3,201 + 0. Eeloo 1: 2,770 + 618. So LKO costs 3,200-3,390 in "SL of stage 1 + vac of the rest".
LKO = 3350.0


def tylo_lander(a_left, b_fuel=2000.0):
    """Craft for the landing simulation: stage A (Poodle) with a_left m/s left, then B (Terrier)."""
    from jool_fleet_land import Craft
    rows, _, _, _ = ROWS["jool-tylo"]
    A, B = rows[3], rows[4]
    m_b = B["m0"] * 1000
    a_dry = (A["mass"] - A["fuel"]) * 1000
    # mass of A's fuel for a_left m/s
    m1 = m_b + a_dry
    fuel_a = m1 * (math.exp(a_left / (350 * G0)) - 1)
    return Craft([(250e3, 350, fuel_a, a_dry), (60e3, 345, b_fuel, 0.0)], m_b - b_fuel)


ROWS = {}
if True:
    import io
    import contextlib
    quiet = __name__ != "__main__"
    for slug in NAMES:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            ROWS[slug] = table(slug, NAMES[slug])
        if not quiet:
            print(buf.getvalue(), end="")
            rows, total, n, cost = ROWS[slug]
            launcher = rows[0]["dv_sl"] + rows[1]["dv_vac"]
            top = max(0.0, LKO - launcher)
            spare = max(0.0, launcher - LKO)
            first = rows[2]["dv_vac"] - top
            if slug in ("jool-vall", "jool-pol", "jool-bop"):
                first = 1759.0  # flown: Dres 1 #51
            print(f"  launcher SL1 + vac2 = {launcher:.0f} vs LKO ~{LKO:.0f}: {rows[2]['name']} spends ~{rows[2]['dv_vac'] - first:.0f} on the "
                  f"orbit -> {first:.0f} in LKO" + (f" (stage 2 keeps ~{spare:.0f})" if spare else ""))
            walk(rows, 2, BUDGET[slug], first)

TYLO_LANDERS = {
    "A with 2,250 left + B (plan)": lambda: tylo_lander(2250.0),
    "A with 1,500 left + B": lambda: tylo_lander(1500.0),
    "A with 800 left + B": lambda: tylo_lander(800.0),
}
