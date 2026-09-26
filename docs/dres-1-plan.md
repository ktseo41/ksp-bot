# Dres 1 — plan (uncrewed Dres orbiter + lander, first Dres visit)

Spec: `crafts/dres-1.json` (offline: **50 parts, 93.20 t** on the pad of 140, ~32 m of 36, ~105k funds incl. fuel; not yet
built in the VAB). OKTO-controlled, one way: everything is transmitted. Nobody has been to Dres: every experiment is new
(orbit high/low + surface) and the world firsts pay (Moho 1: ~300k). Window Kerbin -> Dres **UT 43,122,323**
(`ksp window Dres`, "flight 647 d" = its Hohmann estimate); the planner's own Lambert scan at the window (scratch
`tools/scratch/dres1_plan.py`, `kspbot.kepler` + `flight._lambert`, body constants read from the game) picks a slower,
cheaper path: **T ~747 d, arrival UT ~59.25 M** (see "Window and flight time"). The per-stage table is the rocket
equation on the exact part masses — `launch` must print the same numbers.

## Decisions
- **Moho 1's lander, Duna 1's launcher, an X200-32 under the Poodle.** The lander (OKTO, FL-T800 + FL-T400, Terrier,
  4 x LT-1, the same science set) landed on Moho upright and transmitted everything; the Mainsail / Skipper launcher flew
  3x (Duna 1, Eve 1, Minmus Science 2) and passed Duna 2's pad check. Changes to the lander: **RA-100** (fixed dish,
  100 G) instead of 2 x HG-55 (Dres is 30-60 Gm out: two HG-55s give strength 0.15 at the far end), one HG-55 kept as a
  backup, **RTG** + 2 x OX-STAT-XL (the Sun is 10x weaker at Dres), a second Z-1k (2,810 EC). The Poodle sits on an
  X200-32 (not Duna 2's X200-16): with the X200-16 the margin after LKO was ~16 %, with the X200-32 ~28 %.
- **Not the Twin-Boar / Moho 1 launcher**: 138 t and ~7,200 m/s after LKO for a ~4,100 need, and its Skipper flew at TWR
  0.85 (launch #46 lost in a flat ascent, #47 peaked at 880 K). Here the Skipper ignites at TWR 1.15 (SL) / 1.31 (vac).
- **Not a Spark / Ant lander engine** (researched 2026-09-27): the capture at Dres is ~1,350 m/s on a hyperbola with
  e ~26 (v_pe 1.8 km/s, r_pe 178 km: the Oberth window is ~2 min); a 20 kN Spark on 9 t would burn 10 min and lose most
  of it far from the periapsis. The Terrier (60 kN, 6.6-11 m/s2 over the burn) loses < 10 m/s (finite-burn integration
  in the scratch: 1,342 impulsive -> apo 1,159 km instead of 1,000). **Not a Nerv**: same Oberth argument as Moho 1.
- **Capture into 40 x 1,000 km, not 20 km**: Dres's terrain reaches 5.6 km (sampled on a 5 deg grid; `TERRAIN` has 5,700),
  far-out corrections have been off by hundreds of km (Jool 1, Eve 2), and the in-SOI trim has 5.3 h from the SOI edge to
  the periapsis. 40 km is 34 km of clearance. Low space at Dres is **below 25 km** (spaceAltitudeThreshold; wiki), so the
  low pass comes later: lower the pe to 20 km at the apoapsis (3.6 m/s), circularize at 20 km (120 m/s), then the whole
  orbit is "low" and the landing starts from it.
- **Prograde arrival pass** (about Dres's orbit normal; `vessel` inc < 90): at the periapsis Kerbin is **+55 deg** above
  the horizon and the ray to Kerbin clears Dres over the whole +-120 deg of true anomaly -> no blackout in the capture.
  A retrograde pass hides Kerbin from pe -46 s to pe +101 s: the burn. Set with `correct Dres --pe 40000 --inc-to 0`
  inside the SOI (Duna 1: 6.3 m/s).

## Craft
| function | part | mass (t) | note |
|---|---|---|---|
| control | OKTO (root) + Small Inline Reaction Wheel (5 kN.m) | 0.15 | Poodle (5 deg) / Terrier (4 deg) gimbal every burn; the wheel turns the craft between burns (~25 s per 90 deg on the 29 t stack) |
| lander tanks/engine | FL-T800 + FL-T400 (6 t LF/Ox) + Terrier (60 kN, 85/345) | 7.25 | **3,683 m/s vac** at 9.05 t; Terrier 6.6 m/s2 wet -> 19.7 dry (Dres g 1.13: TWR 5.9-17.5) |
| legs | 4 x LT-1 on the FL-T400 at height -0.7 (Moho 1 geometry: feet below the Terrier bell, landed upright) | 0.20 | crash tolerance 12 m/s |
| comms | **RA-100** (fixed relay dish, 100 G, 6 EC/Mit, 11.4 Mit/s) on the FL-T400 at angle 270 h 0.3 (low: off the nose, near the CoM); **HG-55** backup (15 G, deployable) on the FL-T800 at 90 h 1.5 | 0.73 | RA-100 to DSN 3 (250 G): **158 Gm**; combined with the HG-55 167 Gm. Kerbin-Dres 30-60 Gm over the mission -> strength 0.68-0.85 |
| power | RTG (0.75 EC/s, always) + 2 x OX-STAT-XL (2.8 x 0.104 = **0.29 EC/s each** at Dres, daylight) on the FL-T400 at 0/180 h 0.4, RTG at 90 h 0.4 | 0.16 | **2,810 EC** (2 x Z-1k + 2 x Z-400 + OKTO); a landed set is ~1,000-1,260 EC; recharge 0.75 (night) - 1.3 EC/s (day) |
| science | Science Jr (angle 90 h 0.4), 3 x goo (0/180/270 h 0.5), 2HOT, PresMat, GRAVMAX, Double-C seismic (45/135/225/315 h -0.6), magnetometer boom (180 h -1.3), all on the FL-T800 | 0.47 | 3 goos = high / low / landed; the Jr is spent landed (x8) |
| transfer stage | Poodle + **X200-32** (16 t), Rockomax adapter, TD-12 above, 4 x AV-T1 at h -1.4 | 20.04 | **2,742 m/s vac**: LKO top-up ~1,150, ejection ~1,600 (opens it at 250 kN; the Terrier finishes ~75) |
| launcher | Duna 1's: Mainsail + 2 x X200-32 (32 t), TD-25, 4 x AV-R8; Skipper + X200-32 (16 t), TD-25, 4 x AV-R8 | 64.12 | flown 3x; AV-R8s on the Skipper tank (Minmus Lab 1 lesson) |
Lander wet 9.045 t / dry 3.045 t; the 1.25 m stack (OKTO..Terrier, ~7.7 m, 8 joints) on a 2.5 m launcher: every stack
part rigid + autostrut Root, radial parts plain. The RA-100 (0.65 t) sits 0.6 m off the axis on the lower tank, the Jr +
HG-55 opposite: CoM ~3 cm off the axis, well inside the Terrier's gimbal. No blunt nose (bare OKTO top, as Moho 1 #47
and Duna 2 fly), so the Eve 2 tail-fin fix is not applied; fallback if the recorder shows AoA growing through Mach 1:
4 x Tail Fin on t1b at 45 deg to the AV-R8s (Eve 2 #49: +0.5 t, AoA <= 1.4 deg).

## Stages (rocket equation on part masses; Isp SL/vac) — the pad check
| stage | engine | fuel (t) | m0 -> m1 (t) | dv SL / vac (m/s) | TWR SL / vac | full burn |
|---|---|---|---|---|---|---|
| 1 | Mainsail (1379/1500 kN, 285/310) | 32 | 93.20 -> 61.20 | **1175** / 1279 | **1.51** / 1.64 | 65 s |
| 2 | Skipper (569/650 kN, 280/320) | 16 | 50.64 -> 34.64 | **1043** / 1192 | 1.15 / 1.31 | 77 s |
| 3 | Poodle (250 kN vac, 350) | 16 | 29.08 -> 13.08 | - / **2742** | 0.88 vac | 220 s |
| 4 (lander) | Terrier (60 kN vac, 345) | 6 | 9.05 -> 3.05 | - / **3683** | 0.68 vac | 338 s |
Launcher SL1 + SL2 = 2,218; Duna 1 on this launcher flew 92 % of the Mainsail's SL figure and 97 % of the Skipper's, plus
441 of Poodle = 3,259 to 80 km: here the launcher gives ~2,090 effective, the Poodle spends **~1,150** on the orbit ->
**Poodle 1,500-1,650 in LKO**, Terrier 3,683 untouched. Pad check: `launch` must print stage 1 ~1175 SL / TWR 1.51,
stage 2 ~1043 SL, Poodle ~2742 vac, Terrier ~3683 vac (the lander holds the root: KSP's readout follows it). Off by
> 3 % -> `recover` on the pad and diagnose.
Checkpoints in LKO: Poodle < 1,350 -> the Terrier finishes > 300 of the ejection (still fine, margin ~20 %);
Poodle < 1,000 -> margin gone: recover the mission plan (orbit only, no landing) or revert and redesign.

## Window and flight time (offline Lambert at UT 43,122,323, projected onto Kerbin's plane like `transfer_planet`)
| T (d) | eject from 80 km | plane change (planner term) | arrival v_inf (projected) | capture 40 x 1,000 | total | arrival UT |
|---|---|---|---|---|---|---|
| 450 | 1,783 | 262 | 2,841 | 2,426 | 4,471 | 52.86 M |
| 500 | 1,703 | 247 | 2,343 | 1,937 | 3,887 | 53.92 M |
| 550 | 1,657 | 228 | 1,968 | 1,571 | 3,456 | 55.00 M |
| 600 | 1,629 | 205 | 1,707 | 1,320 | 3,154 | 56.08 M |
| 647 (`window`'s Hohmann) | 1,613 | 180 | 1,554 | 1,173 | 2,965 | 57.10 M |
| **747 (planner's best)** | **1,602** | **114** | **1,492** | **1,114** | **2,830** | **59.25 M** |
| 850 | 1,634 | 31 | 1,670 | 1,284 | 2,949 | 61.48 M |
- The cost curve is flat from 650 to 800 d (2,830-2,970): the planner (0.6-1.4 x Hohmann grid + golden refine on
  ejection + circular capture + plane change) will land on **T ~740-760 d, arrival UT ~59.1-59.6 M**. A faster
  transfer buys little: 600 d saves 147 d for +324 m/s (margin 28 % -> 20 %), 500 d saves 247 d for +1,060 (no landing).
  There is no `--T` flag anyway (code gaps): fly the planner's T.
- Dres is **-1.3 Gm out of Kerbin's plane at arrival** (SOI 32.8 Mm): "no encounter by design"; the plane change is a
  mid-course burn at the planner's printed UT, **~56.2 M (dep + 606 d, 141 d before arrival)**, printed ~114 m/s. The
  planner's term overestimates a little (Eve 1: 413 printed, 372 burned) but the projected arrival v_inf underestimates:
  after the plane change the craft still meets Dres's out-of-plane velocity (up to ~450 m/s): plan the capture for
  **v_inf 1,600-1,750** (the unprojected 3D Lambert at the same T gives 1,731). Budget 250 for the mid-course.
- 3D alternative (Moho plan gap 5): the 3D Lambert needs a departure declination of 38 deg -> ejection 1,867: worse. No.
- Traffic during the cruise (all before the mid-course): Duna 2 launch 44.63 M / arrival 51.30 M, Eve 2 SOI 45.2 M,
  Jool 1 SOI 52.79 M, lab visits every ~1.08 M. Nothing overlaps the Dres phases (56.2 M, 59.2 M+).

## Δv budget (m/s, after LKO)
| item | expect | source |
|---|---|---|
| ejection | node **1,600-1,620**; executed ~1,650 (Poodle 250 kN on 29 t: ~130 s incl. the stage to the Terrier for the last ~75) | Lambert 1,602 at T 747 (1,601-1,613 over 650-800 d) |
| mid-course plane change | **100-250** at ~56.2 M (planner prints ~114; Moho 1's `correct` planned 390 where 77 did: see gaps) | z2 -1.3 Gm at R2 42 Gm, ~3,800 m/s |
| trims | 20-60 (20 d out + inside the SOI, `--inc-to 0`) | Duna 1 3.6 + 6.3; Eve 2 far-out lesson |
| capture 40 x 1,000 km | **1,250-1,350** (v_inf 1,600-1,750: v_pe 1.80 km/s -> 0.45); 1,030 at v_inf 1,400, 1,600 at 2,000 | hyperbola from v_inf; refused by `transfer` above 1.25 x 1,492 + 50 = 1,915 |
| pe 40 -> 20 km at the ap | 4 | |
| circularize 20 km | **120** (489 -> 369) | |
| landing from 20 km circular | **~680**, budget 750 (kill 369 + ~60 gravity loss during it + free fall 212 + hover ~40) | Moho 1: 1,335 for 783 + 367 free fall + hover (same code) |
| **total** | **~4,100** | vs Poodle ~1,575 + Terrier 3,683 = **~5,260: margin ~1,150 (28 %)** |
Sequence with masses: Poodle after LKO ~1,575 -> ejection burns it out and auto-stages to the Terrier (~75) ->
Terrier **~3,600** on the way -> mid-course 250 + trims 60 -> ~3,300 at the SOI -> capture 1,300 -> **~2,000 in the
40 x 1,000 km orbit** -> circularize -> ~1,890 -> landing ~680 -> **~1,200 left on the surface**. Landing rule: after
circularizing at 20 km the Terrier must show **>= 900 m/s** (`vessel`), else stay in orbit (the orbit science is the
base mission; the landing is the bonus).

## Arrival geometry (offline, stock elements at UT 59.25 M) — it decides the links
- Kerbin at arrival: **37.6 Gm** (Dres at 42.2 Gm from the Sun, true anomaly 249 deg, near its apoapsis side), 63 deg from
  Dres's prograde, **18 deg from the Sun** (Kerbin is on the sunward side). The probe arrives 151 deg from prograde
  (Dres catches it from behind, ship at aphelion), 89 deg from the Sun.
- Prograde hyperbola, pe 40 km (e 25.8): sub-periapsis point has **Kerbin +55 deg, Sun +62 deg** (daylight); the ray to
  Kerbin never crosses Dres between nu -120 and +120 deg -> **no blackout in the capture burn** (which spans ~pe +-100 s).
  Retrograde pass: Kerbin -60 deg, hidden nu -25..+46 deg = pe -46 s..+101 s: the whole burn. Rule: at the SOI entry
  `vessel` must read inc < 90 and `signal` > 0; else `correct Dres --pe 40000 --inc-to 0` first (5.3 h from the SOI
  edge to the pe at this v_inf: time enough, do it right after `soi`).
- 40 x 1,000 km: period 6.4 h (the ap is 1,000 km: nothing hides Kerbin for long); 20 km circular: v 369, period 44.9 min,
  Kerbin below the horizon ~20 of 45 min (transmit waits). Dres turns **37 deg/h** (9.67 h day): the sub-Kerbin point
  passes any longitude within 10 h; Kerbin's declination from Dres is within +-5 deg of Dres's equator (Dres has no
  axial tilt and sits 5 deg off Kerbin's plane): equatorial sites see Kerbin high every Dres day.
- Sun: the Sun-Dres-Kerbin angle stays > 3.8 deg over the cruise (min at dep + 360 d, Sun's disc 0.36 deg from Dres) and
  is 18 deg at arrival, but **Kerbin passes behind the Sun at dep + ~895 d = UT ~62.45 M** (0.07 deg; ~1 day of
  blackout). Finish the landing well before UT 62 M (arrival 59.25 M: 2.7 M s of slack).

## Link budget
| leg | antennas | range (DSN 3, 250 G) | need | strength |
|---|---|---|---|---|
| LKO, ejection | OKTO 5k | 35 Mm | < 700 km | 1.0 |
| cruise (49 -> 60 -> 31 Gm), mid-course at 32 Gm | RA-100 (+ HG-55 if extended) | 158 (167) Gm | <= 60 Gm | 0.68-0.85 |
| capture, orbit, landing, surface (37-46 Gm over the first 60 d) | RA-100 | 158 Gm | 38-46 Gm | ~0.8 |
The RA-100 is fixed: nothing to extend, nothing to retract for the landing, no `_antennas` dependence for control
(Eve 2 lesson). The HG-55 is extended by `circularize` / `science --transmit` (code) and stays out (Moho 1 landed with two
extended). Ground stations only: our relays are 2-15 G. Transmit cost: RA-100 6 EC/Mit (`_ec_per_mit` budgets by the
dearest antenna, the HG-55's 6.67: conservative).
Occlusion: none at the capture (above); Moho 1's landing-site rule applies (Kerbin > 20 deg up at touchdown, > 10 deg
150 s before: `Require Signal for Control` is ON — a landing burn with Kerbin below the horizon has no throttle).

## Science (Dres multipliers: high 6, low 7, landed 8; transmit fractions goo 0.3, Jr 0.35, thermo/baro 0.5, grav 0.4, seismic 0.45, mag 0.6)
| set | where | experiments -> science | Mits -> EC (6/Mit) |
|---|---|---|---|
| high (> 25 km: anywhere on 40 x 1,000) | right after the capture | thermo 24, baro 36, grav 48, mag 162, goo 18 -> **~290** | 135 -> 810 |
| low (< 25 km: the 20 km circular orbit) | after circularizing | thermo 28, baro 42, grav 56, mag 189, goo 21 -> **~335** | 135 -> 810 |
| landed | on the surface | thermo 32, baro 48, grav 64, seismic 72, goo 24, Jr 70 (+ mag 216 if it runs landed) -> **~310-525** | 165-210 -> 990-1,260 |
~930-1,150 sci + Dres world firsts (flyby, orbit, landing, surface science: Moho 1's firsts paid ~300k). Battery 2,810
covers each set in one go; `_transmit` waits per experiment for EC (RTG 0.75 + panels 0.58 in daylight ~ 1.3 EC/s:
a landed set recharges in ~15-25 min).

## Landing plan
Airless, g 1.13, v_circ 369 at 20 km, rotation 9.67 h (surface speed 25 m/s at the equator — `land` holds surface
retrograde, fine). Terrain up to 5.6 km: the 20 km orbit clears everything; Lowlands / Midlands are the flat biomes
(others: Highlands, Canyons, Ridges, Impact Craters, Impact Ejecta, Poles). `land --biome Lowlands Midlands --slope 4`
(the lander is a 7.7 m stack on 4 small legs, CoM ~3 m up: slope <= 4 deg matters, Moho 1 rule). Sequence in the code:
kill 369 m/s at 11-13 m/s2 (~30 s, falls ~1 km), warp most of the free fall from ~19 km (~180 s to ~200 m/s), suicide
burn capped at 3 m/s2 (Terrier 11-13 m/s2 available: throttled), legs out in `_powered_descent`, touchdown 1.5 m/s.
Expect **~650-750 m/s**, ~10 min real time. Site with the link: the far half of a 20 km orbit has no link; as on Moho 1
choose the pass with Kerbin's elevation > 20 deg at touchdown (scratch `tools/scratch/site.py`, gap 1) and `land --at`.
Panels are fixed OX-STAT-XL, the RA-100 is fixed, the HG-55 stays extended (6 m up the stack, folds to ~1 m).
Surface heat: none (0.1x sun, parts at ~200 K). Night landing is fine (RTG 0.75 EC/s; the landed set needs ~1,000 EC of
2,810; `science --transmit --all` waits for the link).

## Phases (expected numbers = the checkpoint's "Expect" line; compare after every phase)
Timeline: now UT ~42.35 M; launch ~1 day before the window (`warp-sc 43,090,000` from the space center, ~34 d, ~3 real
min); ejection ~43.12 M; mid-course ~56.2 M (planner prints the exact UT; the Kerbin-Dres distance is 32 Gm there);
trim ~58.8 M (20 d out); Dres SOI ~59.23 M; capture ~59.25 M; solar conjunction ~62.45 M.

| phase | command | expect | Poodle / Terrier left | real time |
|---|---|---|---|---|
| pad | `build crafts/dres-1.json`, `launch "Dres 1"` | 1175 SL, TWR 1.51 / 1043 SL / 2742 vac / 3683 vac; 50 parts, 93.2 t; `signal` 1.0 | 2742 / 3683 | 2 min |
| ascent + circularize | `ascent --alt 80000 && circularize` (background, full output; poll the file every minute) | Mainsail out ~65 s, Skipper out ~2:25 at 40-50 km (TWR 1.15: the t_apo guard may hold it level for a while, watch skin temps < 1,000 K); apoapsis >= 45 km at 3:00; 79-80 x 80 km; transonic AoA < 3 deg | **1,500-1,650** / 3683 | 12 min |
| ejection | `transfer Dres --pe 40000 --plan` -> read -> `ksp node` | Lambert: **T 720-780 d (Hohmann 647)**, v_inf dep ~2,160, ejection ~1,600, arrival v_inf **1,480-1,520** (projected), **Dres -1,000..-1,500 Mm out of plane**, plane change ~100-150, "no encounter by design ... `correct Dres --pe 40000` around UT ~56.2 M"; node **1,600-1,620**; refused > 1.5x + 20. The burn stages to the Terrier near its end (auto). After it: `vessel` -> Sun ap ~42 Gm (read as radius), Poodle gone or < 50 | 0 / **~3,550-3,650** | 8 min |
| cruise 1 | `scene space_center`, `warp-sc <t_pc - 3600>` (~13 M s: ~4 real min at 100,000x, lab visits and Duna 2 / Eve 2 / Jool 1 in between), `fly "Dres 1"` | link ~0.75 (RA-100 at 32 Gm) | | 5 min |
| mid-course | `correct Dres --pe 40000 --inc-to 0 --plan` -> compare with the planner's ~114 -> `ksp node` | **100-250 m/s**, Dres pe ~40 km, inc < 90; refused if far above the printed figure. If the seed "has no encounter" / picks a retrograde pass (Eve 2 lesson): build the node from the scratch projected Lambert (LOG 2026-09-27, Moho 1: 77 m/s) and settle >= 0.3 s per evaluation | 0 / ~3,300-3,450 | 5 min |
| trim 20 d out | `correct Dres --pe 40000 --inc-to 0 --plan` -> `node` | 5-40 m/s; pe 40 +-100 km; do NOT chase sub-km errors here | 0 / ~3,300 | 3 min |
| Dres SOI | `soi` (refuses pe < 6.7 km), then `correct Dres --pe 40000 --inc-to 0 --plan` -> `node` | v_inf **1,600-1,750**; pe 35-45 km (**< 15 km = raise first**); inc < 90 (prograde) and `signal` > 0; 1-20 m/s; **5.3 h to the pe** at 1000x | | 5 min |
| capture | `capture --apo 1000000` (background, full output) | **1,250-1,350 m/s**, ~190 s on the Terrier (6.6 -> 8.5 m/s2, `burn_lead` mass-correct centring), no blackout -> **40 x 1,000 km, period 6.4 h**; a burn stopping hyperbolic -> `capture` again at once | 0 / **~2,000** | 6 min |
| science high | `science --transmit --all` (anywhere: all > 25 km) | ~290 sci; 810 EC of 2,810 | | 3 min |
| lower the pe | at the ap: `periapsis --alt 20000` | **~4 m/s** -> 20 x 1,000 km | | 5 min (3 h warp) |
| circularize | at the pe: `capture` (no --apo) | **~120** -> 20 x 20 km, 44.9 min | 0 / ~1,890 | 5 min |
| science low | `science --transmit --all` (whole orbit < 25 km) | ~335 sci; 810 EC (charge first if < 1,000: 1.3 EC/s in daylight) | | 5 min |
| landing decision | `vessel` | Terrier >= 900 -> land; else the orbit mission is done | | |
| landing | site search with Kerbin's elevation (scratch site.py), `land --at LAT LON --slope 4` (background, full output) over Lowlands / Midlands | **~650-750 m/s**: horizontal kill 369 (~30 s), free-fall warp, suicide burn capped at 3 m/s2, touchdown 1.5 m/s, upright; no `damage`/`attitude` events | 0 / **~1,100-1,250** | 12 min |
| surface science | `science --transmit --all`, then `contracts -v` for new Dres contracts | ~310-525 sci; EC 2,810 -> ~1,600-1,800; RTG recharges | | 5 min |

## Code gaps (nothing blocks the launch; 1-3 are worth doing during the 740-d cruise)
1. **`land` has no link condition**: the site filter is biome + slope only (`find_site`); Moho 1 needed Kerbin's elevation
   (> 20 deg at touchdown, > 10 deg 150 s before) added by hand in `tools/scratch/site.py`. Fold it into `find_site`
   (an `--elev-body Kerbin --min-elev 20` filter: elevation of the body from the touchdown point at the touchdown UT, in
   the rotating frame). Needed before the Dres landing (Require Signal for Control).
2. **Far-out `correct` with no encounter** (the mid-course at 141 d out, ~114-250 m/s): opus's Lambert seed + dv-term
   grid chose a retrograde pass and "had no encounter" on Eve 2 (185 d out) because `_node_cost` settles 0.04 s between
   evaluations; Moho 1's mid-course was built by hand from the projected Lambert vector. Fix: settle >= 0.3 s far out,
   refuse a pass whose `inc_to` error > 90 deg, print the Lambert seed's own dv next to the tuned node so the checkpoint
   can compare them; `--max-dv` as a hard refusal.
3. **Capture link forecast** (Moho plan gap 3a) is still not in code; here the prograde pass has no blackout, the manual
   check at the SOI entry (`vessel` inc < 90, `signal` > 0) stands in for it.
4. `transfer` has no flight-time override (`--T`): it takes the cost-optimal ~747 d; a 600-d path (+324 m/s, -147 d) is
   not reachable from the CLI. Not needed here.
5. `_transmit` budgets the recharge time from solar panels only (`flow`): with an RTG the printed wait is pessimistic and
   "in the shade" waits still work (the RTG fills the battery); cosmetic. Also the transmit guard uses the dearest
   antenna's EC/Mit (HG-55 6.67 vs RA-100 6.0): conservative, fine.
6. `capture` at Dres runs ~190 s on the Terrier: `burn_lead` (mass-correct, multi-stage fallback via the mod's
   `RecalcDeltaV`) was fixed after Moho 1 #47; check the printed "~190 s, start ~100 s before" line before it warps
   (Moho 1: "131 s" was the Poodle-only fallback). Stop rule: a printed burn time < 150 s -> stop, `vessel`, rerun.
7. `land` kills all horizontal speed at the start point: ~60 m/s of gravity loss during the 30-s kill at Dres; a
   `--from-pe` mode (Moho plan gap 7) would save ~50. Not worth it here (margin 28 %).
8. `soi` refuses a predicted pe below `TERRAIN["Dres"]` + 1 km = 6.7 km: right for Dres (max sampled 5.6 km).

## Risks and stop rules
- **Pad numbers off** (1175 SL / 1.51, 1043 SL, 2742 vac, 3683 vac; 93.2 t, ~32 m): `recover`, fix the spec.
- **Ascent**: first flight of the 7.7 m lander stack + X200-32 Poodle stage on the Duna 1 launcher; Skipper TWR 1.15 at
  staging. AoA through Mach 1 > 5 deg or an `attitude` event -> revert to launch, add 4 x Tail Fin on t1b (Eve 2 #48 fix).
  Apoapsis < 45 km at 3:00 or OKTO skin > 1,000 K -> revert (Moho 1 #46 pattern). Poodle < 1,350 in LKO -> see the
  checkpoints above.
- **Ejection**: node 1,600-1,620; > 1,800 or projected arrival v_inf > 1,700 in the Lambert line -> do not burn, diagnose
  the window geometry. Burn ending > 50 m/s short -> `correct Dres --pe 40000 --plan` inside the SOI at once (Oberth).
  No encounter is expected at this point (Dres -1.3 Gm out of plane): read the Sun orbit (ap ~42 Gm) instead.
- **Mid-course**: expect 100-250; > 400 -> stop (3 attempts max: `--inc-to 0`, scratch Lambert seed, else keep the flyby
  and take flyby science). > 600 kills the landing, > 1,000 the capture.
- **Arrival**: pe after the in-SOI trim 35-45 km; < 15 km with < 1 h to pe -> raise it now (`correct --pe 40000`), never
  warp to a pe under the terrain. Retrograde pass -> flip with `--inc-to 0` (5 h). Signal 0 at the SOI entry (Kerbin
  behind Dres is impossible there: 32.8 Mm out) -> tooling: `vessel`/`scene` and retry, do not warp to the pe without it.
- **Capture**: 1,250-1,350 expected, ~190 s; a burn that stops with the craft still hyperbolic -> `capture` again at
  once (it burns past the pe); any bound orbit is a win (science from it). Budget for a late start: +100 m/s.
- **Landing**: only with Terrier >= 900 after the 20 km circularization, a slope <= 4 deg site with Kerbin > 20 deg up;
  touchdown `damage` events -> `log`, the orbit science is already home.
- **Link / power**: strength ~0.8 on the fixed RA-100, nothing deploys; the HG-55 is a backup. Transmit only with EC >=
  1,100 (the code waits per experiment). Solar conjunction ~UT 62.45 M: be landed and transmitted before ~62 M.
