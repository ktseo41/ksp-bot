# Jool 1 — plan (uncrewed Jool orbiter, first outer-planet probe)

Spec: `crafts/jool-1.json` (built OK 2026-09-26: 46 parts, 87.14 t, 83,580 funds, 3 stages, no warnings; pad limit
140 t / 36 m). OKTO-controlled; the Nerv stage stays with the probe (capture + moon tour).

## Craft
| function | part | note |
|---|---|---|
| control | OKTO + Advanced Inline Stabilizer (30 kN.m) | 14 t stage, Nerv has no gimbal: the wheel steers every burn |
| propulsion | LV-N Nerv (60 kN, Isp 800) + 4 x Mk1 LF fuselage (1600 LF, 8 t) | LF only, no dead oxidizer; 1.25 m stack 9 joints, rigid + autostrut Root |
| comms | Communotron 88-88 x3 (deployable) | combined 100 x 3^0.75 = 228 G; with DSN 2 (50 G) range **107 Gm** (2 dishes: 92 Gm); max Kerbin-Jool ~86 Gm, at arrival ~73 Gm -> strength ~0.15-0.3 |
| power | Gigantor x3 (24.4 EC/s each at Kerbin, **~1 EC/s each at Jool**, flux 4 %) + Z-1k + Z-400 x4 + OKTO = **2,610 EC** | see budget |
| science | Science Jr, goo x2, 2HOT, PresMat, GRAVMAX, magnetometer boom | all surface-mounted on the top fuselage; ~140 Mits per full set |
| launcher | Mainsail + 2 x X200-32; Skipper + X200-32 + X200-16 | Rescue 5 / Minmus Lab 1 pattern with an X200-16 added |
| fins | AV-R8 x4 (Mainsail tank, -2.5), AV-R8 x4 (Skipper's X200-16, -0.6), AV-T1 x4 (bottom fuselage) | fins on every atmospheric stage; Gigantors on fuselage 3, dishes on 2, science on 1 |

## Stages (part stats; Isp SL/vac)
| stage | engine | fuel | m0 -> m1 (t) | dv SL / vac (m/s) | TWR SL / vac |
|---|---|---|---|---|---|
| 1 | Mainsail (1500 kN, 285/310) | 2 x X200-32 = 32 t | 87.1 -> 55.1 | 1279 / 1391 | **1.76** / 1.91 |
| 2 | Skipper (650 kN, 280/320) | X200-32 + X200-16 = 24 t | 44.6 -> 20.6 | 2122 / 2425 | 1.37 / 1.49 |
| 3 (probe) | Nerv (60 kN, 185/800) | 4 x Mk1 fuselage = 8 t LF | 14.04 -> 6.04 | - / **6615** | 0.44 (Kerbin) |
Launcher SL1 + vac2 = 3704 vs our LKO calibration 3250-3350: the Nerv should reach 80 km **untouched (6550-6620 m/s)**;
if `launch` prints the Nerv below ~6400 after circularize something burned that shouldn't have (checkpoint).
Nerv mass flow 7.65 kg/s: 1 m/s costs 1.8 kg at full mass; burn times below.

## Comm check (Require Signal for Control)
- LKO: OKTO's internal 5k antenna (~16 Mm) until `circularize` extends the dishes (flight code, also the burn guard).
- Cruise/Jool: 228 G x 50 G -> 107 Gm > 86 Gm worst case; Kerbin side must be a ground station (Keo relays are RA-2,
  2 G: sqrt(228 x 2) = 21 Gm only). Stock extra ground stations give near-continuous line of sight; if the link drops at
  Jool (KSC behind Kerbin) wait, never burn on a dead link (`burn_at` refuses control "none").
- Behind Jool (pe pass on the far side) or behind a moon: the link is gone for minutes; plan burns/transmits on the near side.

## Power budget (Jool)
| item | EC |
|---|---|
| supply, sunlit | 3 Gigantors ~3 EC/s (tracking) |
| OKTO + wheel holding attitude | ~0.05-0.5 EC/s |
| 88-88 transmit | 200 EC/s, 10 EC/Mit: full set 140 Mits = **1,400 EC** per biome-situation set (goo 10, Jr 25, thermo 8, baro 12, grav 20, mag 45 Mits, x2 goo) |
| eclipse | pe pass 250 km: ~20 min (<600 EC); 27 Mm circular: 63 min (<1,900 EC) |
Battery 2,610 EC: one full set per transmit, then ~8 min of sun to refill; **transmit only in sunlight with the panels
open**, one set at a time (KSP stalls a transmission when EC runs out; don't count on it resuming).

## Window and phases (expected numbers; compare after every phase)
Window UT **24,293,116** (`ksp window Jool`; now 23.68 M = +28.6 days), Hohmann flight ~1194 days, arrival ~UT 50.1 M.
Duna 1's return window (UT 22.9 M) is already past; Ike Station 1's window (25.05 M) comes 35 days later.

| phase | command | expect | Nerv dv left | real time |
|---|---|---|---|---|
| ascent + circularize | `ascent --alt 80000`, `circularize` | 79-80 x 80 km; stages 1+2 do it all, Nerv 6550-6620 | 6600 | ~10 min |
| ejection | `transfer Jool --pe 250000 --plan`, then `ksp node` | **1934 m/s Hohmann** (LKO 80 km, v_inf 2713); Lambert 1950-2100 with Jool's 1.3 deg plane; refused above 3441 (1.25x + 50). Burn **~400 s** at TWR 0.44-0.55: +/-40 deg of orbit -> ~5-8 % steering loss, expect 100-150 m/s over the node's figure; check v_inf and the Jool pe after it, not the node | ~4600 | 7 min burn |
| mid-course | `correct Jool --pe 250000` at the printed UT (node line); inside the SOI `--inc-to` if wanted | 10-80 m/s (Duna 1: 3.6 + 6.3); do fine pe trims inside the SOI (2.46 Gm radius, days of lead) | ~4550 | cruise 1194 d at 100000x ~5 min |
| Jool SOI | `soi` | v_inf **1760** (1700-1900), pe 250 km (atmosphere 200 km: **pe < 210 km = abort/raise**), check the patched conics for a moon encounter on the way in (Laythe 27.2 Mm, Vall 43.2, Tylo 68.5 Mm cross the approach) | | |
| capture | `capture --apo 100000000` | v_pe 9670 -> 9225: **~445 m/s**, 79 s burn; orbit 250 km x 100 Mm, period 6.7 d; the ap crosses all three inner moons: re-check for encounters next pass | ~4150 | |
| science | `science --transmit` at pe (Jool low space < 4 Mm) and at ap (high space) in sunlight | ~1,400 EC per set; goo/Jr transmit at 30-35 % | | |
| extended (optional) | at ap: `periapsis --alt 21200000` (pe to Laythe's radius) ~520; at pe: `capture` to circular 27.2 Mm ~820; then `transfer Laythe/Vall/Tylo --pe X --plan` from the circular orbit | Laythe-altitude circular orbit for ~1,340 total; ~2,800 m/s left for moon flybys (each 100-400 + return) | ~2800 | |
Direct capture into a 27 Mm apoapsis would cost 1097 + 1256 = 2350: the 445 + 520 + 820 route is 560 cheaper.

## Risks
- **Ascent flip**: 12 m of 1.25 m stack on a 2.5 m launcher is the Minmus Lab 1 shape. Fins on all three stages,
  Gigantors/dishes low, science instruments small. Stop rule: `attitude` events after the Mainsail separation -> revert.
- First Nerv flight: no gimbal, 0.44 TWR, 400 s ejection. `execute_node` holds the node vector, so the last minutes burn
  off-prograde; if the post-burn v_inf is >150 m/s off the plan, `correct` fixes it (cheap far out). Stop rule: the
  `_approve` gate refusing the node, or a burn > 2300 m/s.
- Nerv heat: 400 s at full thrust heats the engine (~1000 K, limit 2500). Adjacent Z-400s/fins on fuselage 4 are cold
  parts; `damage` events -> stop and diagnose.
- Long-coast link: a 1194-day cruise on rails; the dishes must be extended (they are after circularize and by the burn
  guard) or the probe is uncontrollable on arrival. Verify `signal` before every warp.
- Moon encounters: the incoming hyperbola and the 250 km x 100 Mm capture orbit both cross Laythe/Vall/Tylo. An unplanned
  Tylo pass can eject the probe; read the conics after `soi` and after `capture`, move the pe/timing a few m/s if needed.
- Encounter drift over the cruise (Minmus Lab 1: 15 -> 1660 km; Duna 1 fine after the fix): re-run `correct` inside the SOI.
- Steering losses: none of our commands split a burn; if the ejection comes out > 2200 m/s, stop (do not chase with a second
  node from an elliptical orbit: `transfer` needs near-circular).

## What the tooling lacks
- Split ejection (two-pass periapsis kick) for low-TWR stages: `transfer` plans a single node from a circular orbit.
- Moon transfers from an elliptical parent orbit (same gap as Ike Station 1) — hence the circularization at 27 Mm.
- Gravity assists (Tylo/Laythe capture help) are not planned by anything; capture is propulsive.
- No fairing support in the builder (AE-FF1/FF2 are researched): the science parts and dishes fly exposed, as on Keo Relay 3.
- `science` runs experiments where the craft is now; the pe/ap timing (low vs high space, sunlight) is by hand (`warp`).
- Transmission stall on empty batteries is not detected by the flight code: check `vessel` EC before transmitting.
