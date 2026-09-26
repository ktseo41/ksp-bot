# Ike Station 1 — plan (contract "Build a new orbital station around Ike", 905.6k on completion)

Spec: `crafts/ike-station-1.json` (built OK 2026-09-26: 44 parts, 134.04 t, 72,123 funds, 3 stages, no warnings;
pad limit 140 t / 36 m, stack height 33.6 m). Uncrewed launch (OKTO), 9 seats fly empty.

## Contract checklist -> part
| requirement | part |
|---|---|
| antenna | Communotron HG-55 x2 + RA-15 relay (all deployable: extend in vacuum, the burn guard does it) |
| docking port | Clamp-O-Tron (root, docking face up) |
| power | Gigantor x2 (must be deployed by hand via kRPC: no flight code does it) + OX-STAT-XL x6 (fixed, no deployment) ; 4 x Z-400 + cupola 200 EC |
| crew capacity >= 9 | cupola 1 + PPD-10 Hitchhiker x2 (8) |
| ISRU | Convert-O-Tron 125 (MiniISRU) |
| viewing cupola | PPD-12 (its top node carries the ISRU / wheel / OKTO / port stack: the builder cannot flip parts and the 1.25 m section up top saves two adapters, 1.9 m and 0.2 t) |
| stable 10 s | Advanced Inline Stabilizer 30 kN.m + cupola 9 kN.m |
| new vessel, in Ike orbit | launched after accepting; target 50 km circular Ike orbit (Ike terrain <= 12.7 km) |

## Stages (part stats; Isp SL/vac, tank fuel LF+Ox)
| stage | engine | tanks (fuel) | m0 -> m1 (t) | dv SL / vac (m/s) | TWR SL / vac |
|---|---|---|---|---|---|
| 1 | Twin-Boar (2000 kN vac / 1867 SL, 280/300 s) | own 32 t + S3-3600 18 t + ADTP-2-3 15 t = 65 t | 134.0 -> 69.0 | 1822 / 1953 | **1.42** / 1.52 |
| 2 | Skipper (650 kN, 280/320 s) | X200-32 + X200-8 = 20 t | 53.9 -> 33.9 | 1275 / 1457 | 1.08 / 1.23 |
| 3 (transfer, stays with the station) | Poodle (250 kN, 90/350 s) | X200-32 = 16 t | 27.8 -> 11.8 | 757 / **2943** | 0.24 / 0.92 |
Station dry (above the Poodle tank): 7.1 t. Launcher rocket-equation dv 1822 + 1457 = 3279; our calibration (Duna 1 and
Minmus Lab 1: ~3220-3400 with the first stage at SL Isp) says LKO 80 km costs 3250-3350, so the Poodle should keep
**2800-2940 m/s** after circularization (Duna 1's Poodle burned 410 of its 1607 during the ascent, i.e. that launcher
was 400 short; this one is sized so the Poodle burns <= ~150).
Fins: AV-R8 x4 on the Twin-Boar (-2.5 m), AV-R8 x4 on the Skipper's X200-32, AV-T1 x4 on the Poodle's X200-32 (Minmus
Lab 1 lesson: fins on every atmospheric stage; Gigantors/antennas/relay low on the Poodle tank). Whole stack rigid +
autostrut Root; no side boosters.

Why not the Nerv: no LF-only tanks are researched and the builder cannot set resource amounts, so a Nerv stage carries
dead oxidizer (Nerv + X200-32: 2220 m/s at 29 t) — the Poodle + X200-32 (2943 m/s at 28 t) is better and proven.
Nerv only wins with a Drain Valve dumping the oxidizer in LKO (3460 m/s at the same LKO mass): not worth new tooling.

## Window and mission phases (expected numbers)
Offline (kspbot/kepler.py, planet_window logic, stock elements; reproduced Duna 1's window at UT 5,108,742 vs 5,098,000
flown): **Kerbin -> Duna window UT 25,054,465** (day 1160, +260 days from UT 19.44 M), synodic 909.5 d, flight ~309 d,
arrival ~UT 31.73 M with Duna at 21.29 Gm (near its apoapsis: Hohmann v_inf dep 972, arr 868 — 100 m/s more than
Duna 1's window). Duna 1's return window (UT 22,895,340) comes first.

| phase | command | expect | dv left after |
|---|---|---|---|
| ascent + circularize | `ascent --alt 80000`, `circularize` | 79-80 x 80 km, Poodle 2800-2940 m/s | 2800-2940 |
| ejection at the window | `transfer Duna --pe 60000 --plan` (Lambert, broken plane) | 1080-1120 m/s, v_inf ~970, Duna pe 60 km, Sun ap ~21.3 Gm; refused if v_inf > 1.25 x Hohmann + 50 | ~1750 |
| mid-course | `correct Duna --pe 60000` at the printed UT, then `--inc-to 0` inside the SOI | 10-50 m/s (Duna 0.06 deg off-plane; Duna 1: 3.6 + 6.3) | ~1700 |
| Duna capture | `capture` at pe 60 km (v_inf ~870: v_pe 1530 -> 890 circular) | **~640 m/s** to 60 km circular | ~1060 |
| Ike transfer | `transfer Ike --pe 50000 --plan` (moon path: Ike's parent = Duna, needs a near-circular orbit) | ~300 m/s (Hohmann 380 -> 3200 km radius), Ike v_inf ~170 | ~760 |
| Ike capture | `soi`, `capture` at 50 km | ~170 m/s to ~50 km circular (v_pe ~500 -> 320) | ~590 |
| contract | SAS on, 10 s, check `contracts` | funds +905.6k | |
Nominal 2250 m/s vs 2800+ available: margin 25 %+. Cheaper variant (not supported by `transfer` from an elliptical orbit):
capture to 60 x ~2900 km (~340 m/s) and let Ike's 1050 km SOI catch the apoapsis (total ~1850).

## Risks
- First flight of the Twin-Boar (gimbal 1.5 deg, 134 t) and of a 3.75 m tank sitting flat on a 2.5 m part (ADTP + S3-3600
  hump low on the stack: CoP moves down, drag a bit higher). Fallback: `recover` on the pad if `launch` prints stage dv
  or TWR far from the table above.
- Skipper TWR 1.08 (SL) / 1.23 (vac) at staging: gravity losses if stage 1 ends low; the Poodle covers up to ~500 m/s of
  ascent shortfall before the 20 % mission margin is gone.
- Require Signal for Control: 2 x HG-55 + RA-15 combined ~34 G x DSN 2 (50 G) -> ~41 Gm, Kerbin-Duna max 35 Gm: OK, but
  all three must be extended (burn guard) and Kerbin's line of sight relies on the Keo relays at night.
- Electric: Gigantors need `part.solar_panel.deployed = True` by hand (no flight code deploys panels); the six OX-STAT-XL
  give ~2-4 EC/s at Duna without it. Ike eclipses are short (orbit ~1 h at 50 km).
- Encounter drift on a 309-day cruise (Minmus Lab 1's pe drifted 15 -> 1660 km): re-check `correct` inside the SOI.
- Duna capture is the biggest burn (640 m/s at TWR 0.9 -> ~70 s): start on time, the periapsis is 60 km over a 50 km
  atmosphere; use `--apo` only with the elliptical variant.
- Ike's SOI is a third of its orbit radius: `transfer Ike` closest-approach tuning and the arrival geometry are untested
  (Mun/Minmus SOIs are small); expect a messy first encounter, `correct Ike --pe 50000` after the burn.

## What the tooling lacks
- Moon transfer from an elliptical parent orbit (`transfer` needs near-circular; LOG Survey 1 Mun -> Minmus notes): the
  cheap capture variant is not flyable yet.
- Solar panel deployment in the flight code (extend panels after LKO like `_antennas`).
- The builder cannot flip parts (childNode on a reversed adapter overlapped both ADTPs in the first build) and cannot set
  resource amounts (no LF-only Nerv stages).
- A real-time estimate for the 309-day cruise warp and the window wait (+260 days) — do them from the space center /
  a high orbit, not from a low orbit.
