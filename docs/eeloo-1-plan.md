# Eeloo 1 — plan (uncrewed Eeloo orbiter + lander, first Eeloo visit)

Spec: `crafts/eeloo-1.json` (offline: **52 parts, 138.70 t** on the pad of 140 (Moho 1's stack fit the pad box), ~113k funds
incl. fuel; not yet built in the VAB). **Dres 1's lander, unchanged, on Moho 1's transfer stage + launcher.** OKTO-controlled, one way:
everything is transmitted. Nobody has been to Eeloo: every experiment is new (orbit high/low + surface; Eeloo's multipliers
are the highest in the system: 10 / 12 / 15) and the world firsts pay. Window Kerbin -> Eeloo **UT 43,588,306**
(`ksp window Eeloo`, "flight 1168 d" = its Hohmann estimate); the offline Lambert scan at the window (scratch
`tools/scratch/eeloo1_plan.py`, `kspbot.kepler` + `flight._lambert`, body constants read from the game 2026-09-27, read-only)
picks **T ~1,191 d, arrival UT ~69.3 M**. The per-stage table is the rocket equation on the exact part masses — `launch`
must print the same numbers.

## Decisions
- **Why not Dres 1's stack as it is (5,442 m/s after LKO)**: Eeloo is 44 deg past its descending node and near its perihelion
  at arrival (r 69.5 Gm, true anomaly 324 deg, moving at ~4.6 km/s): the arrival v_inf is **~2,200 m/s** (Dres: 1,600-1,750)
  and Eeloo sits **-5.1 Gm out of Kerbin's plane** at arrival (Dres: -1.3 Gm). The honest budget after LKO — ejection 2,006,
  mid-course ~382 (see below), capture 1,660, circularize 170, landing ~1,000 — is **~5,450 with the budgets of this table**:
  margin -2 m/s on Dres 1's stack. An X200-8 under Dres 1's Poodle adds only ~200 net (the launcher pays for it), a bigger
  lander tank adds nothing (every stage carries it). Moho 1's stack (Twin-Boar / Skipper / Poodle each on X200-32 +
  X200-16) flew this same lander (minus 0.6 t of RA-100 / RTG / Z-1k) to LKO with the Poodle at 2,961 on launch #47:
  here **Poodle ~2,860 + Terrier 3,683 = ~6,545 after LKO, margin ~1,100 (20 %)**. The launcher's price is the Skipper's
  TWR 0.84 at staging and the OKTO's 880 K in the flat guard flight at 45-51 km on #47 (of 1,200): flown once, watch it.
- **The mid-course plane change is early, not at the planner's printed UT.** `transfer` projects Eeloo onto our plane and
  prices the plane change at ~90 deg of true anomaly before arrival "at the arrival speed" (~174 m/s printed). On this
  transfer (e 0.67, a 41.6 Gm) that point is only **127 d before arrival (UT ~66.57 M)** and the craft still moves at
  ~2.4 km/s with 5.1 Gm to lift: the real single burn there is **~1,900 m/s** (3D Lambert from the projected path to Eeloo's
  true position), 636 at dep + 800 d, and **382 at dep + 350-400 d** (flat 380-430 from dep + 250 to 550 d, i.e. UT 49.0-55.5
  M). `correct Eeloo --pe 70000` uses a direct 3D Lambert seed when the arc still to fly is < 120 deg (it is ~50 deg at
  dep + 370 d), so it should plan ~380-430 there. **Run it at dep + 350-400 d (UT ~51.2-52.2 M), never later than dep + 550 d.**
- **Lander unchanged from Dres 1**: Terrier on 9.05 t gives 6.6-19.7 m/s2 (Eeloo g 1.69: TWR 3.9-11.7, fine for a suicide
  burn); the RA-100 (100 G) reaches 158 Gm to DSN 3 vs 55-99 Gm over the mission (strength 0.32-0.72); the RTG carries the
  power (the Sun is 0.038x at Eeloo: the two OX-STAT-XL make 0.11 EC/s each — a bonus, not a source); 2,810 EC holds a
  science set (~810 EC) three times over. **No ion stage**: a Dawn (2 kN, 8.7 EC/s) on 9 t is 0.22 mm/s2 — the RTG cannot
  feed it and a 1,660 m/s capture would take two hours far from the periapsis. No second RA-100 (0.65 t on the lander
  costs the Terrier ~420 m/s; strength 0.3-0.7 is enough: any link > 0 gives full probe control, strength only sets the
  transmit rate). No nose cone / fairing (composites): the bare OKTO flew #47 and Dres 1; the fallback stays 4 x Tail Fin.
- **Capture into 70 x 1,000 km, not 40**: Eeloo's low-space line is **60 km** (`space_high_altitude_threshold`, read from the
  game), so a 40 km periapsis makes the craft "low" for a few minutes around each pass and the high set would have to wait;
  at 70 km the whole capture orbit is high (the set runs right after the burn), the terrain (3.4 km sampled on a 5 deg grid;
  `TERRAIN` has 3,900) is 66 km down, and the Oberth price is +31 m/s. Then pe -> 20 km at the apoapsis (12 m/s),
  circularize at 20 km (168 m/s): the whole orbit is low, the landing starts from it (16 km over the highest terrain).
- **Prograde arrival pass** (about Eeloo's orbit normal; `vessel` inc < 90): Kerbin is **+60 deg** above the sub-periapsis
  point and the ray to Kerbin clears Eeloo over the whole +-120 deg of true anomaly -> no blackout in the capture. A
  retrograde pass hides Kerbin from pe -50 s to pe +111 s: the burn. `capture`'s link forecast (in code since Mun Sat 1)
  would move the burn earlier; do not let it: set the side with `correct Eeloo --pe 70000 --inc-to 0` inside the SOI.

## Craft
| function | part | mass (t) | note |
|---|---|---|---|
| control | OKTO (root) + Small Inline Reaction Wheel (5 kN.m) | 0.15 | Poodle (5 deg) / Terrier (4 deg) gimbal every burn; the wheel turns the craft between burns (~30 s per 90 deg on the 38 t stack) |
| lander tanks/engine | FL-T800 + FL-T400 (6 t LF/Ox) + Terrier (60 kN, 85/345) | 7.25 | **3,683 m/s vac** at 9.05 t; 6.6 m/s2 wet -> 19.7 dry (Eeloo g 1.69: TWR 3.9-11.7) |
| legs | 4 x LT-1 on the FL-T400 at height -0.7 (Moho 1 / Dres 1 geometry) | 0.20 | crash tolerance 12 m/s |
| comms | **RA-100** (fixed relay dish, 100 G, 6 EC/Mit, 11.4 Mit/s) on the FL-T400 at angle 270 h 0.3; **HG-55** backup (15 G, deployable) on the FL-T800 at 90 h 1.5 | 0.73 | RA-100 to DSN 3 (250 G): **158 Gm**; with the HG-55 167 Gm. Kerbin-Eeloo 55-99 Gm over the mission -> strength 0.32-0.72 |
| power | RTG (0.75 EC/s, always) + 2 x OX-STAT-XL (2.8 x 0.038 = **0.11 EC/s each** at Eeloo, daylight) on the FL-T400 at 0/180 h 0.4, RTG at 90 h 0.4 | 0.16 | **2,810 EC** (2 x Z-1k + 2 x Z-400 + OKTO); a set is ~810-1,260 EC; recharge 0.75 (night) - 0.97 EC/s (day): ~15-25 min per set |
| science | Science Jr (angle 90 h 0.4), 3 x goo (0/180/270 h 0.5), 2HOT, PresMat, GRAVMAX, Double-C seismic (45/135/225/315 h -0.6), magnetometer boom (180 h -1.3), all on the FL-T800 | 0.47 | 3 goos = high / low / landed; the Jr is spent landed (x15) |
| transfer stage | Poodle + **X200-32 + X200-16** (24 t), Rockomax adapter, TD-12 above, 4 x AV-T1 on the X200-16 at h -0.6 | 29.04 | **3,414 m/s vac**: LKO top-up ~550, ejection ~2,010, mid-course ~400, trims, the first ~350 of the capture at 250 kN; the Terrier finishes |
| launcher | Moho 1's: Twin-Boar (own 32 t) + X200-32 + X200-16 (24 t), TD-25, 4 x AV-R8; Skipper + X200-32 + X200-16 (24 t), TD-25, 4 x AV-R8 | 100.62 | flown once (Moho 1 #47, after #46 was lost in a flat ascent before the t_apo guard) |
Lander wet 9.045 t / dry 3.045 t; the 1.25 m stack (OKTO..Terrier, ~7.7 m, 8 joints) on a 2.5 m launcher: every stack
part rigid + autostrut Root, radial parts plain (as Dres 1, whose pad check matched to the m/s). CoM ~3 cm off the axis
(RA-100 vs Jr + HG-55), inside the Terrier's gimbal. Fallback if the recorder shows AoA growing through Mach 1:
4 x Tail Fin on t1b at 45 deg to the AV-R8s (Eve 2 #49: +0.5 t, AoA <= 1.4 deg) — pad mass then 139.2 t (limit 140).

## Stages (rocket equation on part masses; Isp SL/vac) — the pad check
| stage | engine | fuel (t) | m0 -> m1 (t) | dv SL / vac (m/s) | TWR SL / vac | full burn |
|---|---|---|---|---|---|---|
| 1 | Twin-Boar (1867/2000 kN, 280/300) | own 32 + X200-32 + X200-16 = 56 | 138.70 -> 82.70 | **1420** / 1521 | **1.37** / 1.47 | 82 s |
| 2 | Skipper (569/650 kN, 280/320) | 24 | 68.64 -> 44.64 | **1181** / 1350 | **0.84** / 0.97 | 116 s |
| 3 | Poodle (250 kN vac, 350) | 24 | 38.08 -> 14.08 | - / **3414** | 0.67 vac | 330 s |
| 4 (lander) | Terrier (60 kN vac, 345) | 6 | 9.05 -> 3.05 | - / **3683** | 0.68 vac | 338 s |
Moho 1 #47 on this launcher (pad 1430 / 1198 / 3513 / 4218): 79.3 x 79.6 km with the Poodle at 2,961, i.e. the Poodle
spent 552 on the orbit -> here **Poodle ~2,860 in LKO** (2,800-2,900), Terrier 3,683 untouched. Pad check: `launch` must
print stage 1 ~1420 SL / TWR 1.37, stage 2 ~1181 SL, Poodle ~3414 vac, Terrier ~3683 vac (the lander holds the root: KSP's
readout follows it); 52 parts, 138.7 t. Off by > 3 % -> `recover` on the pad and diagnose.
Checkpoints in LKO: Poodle < 2,600 -> margin ~15 %, still go; Poodle < 2,300 -> the landing is gone (orbit mission only:
decide before the ejection); Poodle < 2,050 -> revert / recover and redesign.

## Window and flight time (offline Lambert at UT 43,588,306, projected onto Kerbin's plane like `transfer_planet`)
The planner's own cost (ejection + projected capture + its plane-change term) and the honest cost (ejection + the best
single 3D mid-course + capture at the 3D v_inf after it), capture to 70 x 1,000 km:
| T (d) | eject from 80 km | planner's plane term | projected arrival v_inf | planner total | **honest: mid-course at dep+ (m/s)** | **v_inf after it** | **capture** | **honest total** | arrival UT |
|---|---|---|---|---|---|---|---|---|---|
| 900 | 2,039 | 88 | 3,021 | 4,542 | 250 d (260) | 3,007 | 2,438 | 4,736 | 63.03 M |
| 1,000 | 1,985 | 117 | 2,587 | 4,100 | 290 d (311) | 2,572 | 2,017 | 4,312 | 65.19 M |
| 1,100 | 1,963 | 148 | 2,323 | 3,855 | 330 d (352) | 2,308 | 1,764 | 4,079 | 67.35 M |
| **1,191 (planner's best)** | **1,967** | 174 | 2,212 | **3,781** | **370 d (382)** | **2,199** | **1,660** | **4,009** | **69.31 M** |
| 1,300 | 2,008 | 200 | 2,215 | 3,810 | 410 d (408) | 2,203 | 1,663 | 4,080 | 71.67 M |
| 1,400 | 2,092 | 227 | 2,313 | 4,057 | 450 d (423) | 2,301 | 1,757 | 4,272 | 73.83 M |
- Both cost curves bottom at **T ~1,190 d**: the planner (0.6-1.4 x 1,168 d grid + golden refine) will pick **T 1,170-1,220 d,
  arrival UT ~69.0-69.9 M**. Faster buys little: 1,100 d saves 91 d for +70 honest m/s (fine if the planner lands there),
  1,000 d saves 191 d for +303 (margin 20 % -> 14 %: no). There is no `--T` flag: fly the planner's T. 1,191 d = 25.7 M s
  = ~4.5 real minutes of rails warp from the space center.
- The 3D Lambert straight from the parking orbit needs a 73 deg departure declination (ejection 4,116): no. The plane
  change is the early mid-course above; what the planner prints ("do `correct Eeloo` around UT ~66.6 M, expect ~174 m/s")
  is **wrong for this transfer** — it would cost ~1,900 there. Ignore that line; the early burn is in the phase table.
- Traffic during the cruise: Duna 2 launch 44.63 M / arrival 51.30 M, Eve 2 SOI 45.2 M / pe 45.3 M, **Eeloo mid-course
  ~51.2-52.2 M**, Jool 1 SOI 52.79 M, Dres 1 mid-course ~56.2 M, **solar conjunction of Eeloo 56.55 M** (below), Dres 1
  SOI 59.23 M, lab visits every ~1.08 M. The Eeloo mid-course sits between Duna 2's arrival and Jool 1's SOI: do it at
  dep + 350 d (UT ~51.15 M) right before Duna 2's capture, or at dep + 400-450 d (52.2-53.3 M) after Jool 1: same price.

## Δv budget (m/s, after LKO)
| item | expect | source |
|---|---|---|
| ejection | node **1,960-2,000**; executed ~2,010-2,050 (Poodle 250 kN on 38 t: 6.6 m/s2, ~270 s, `burn_lead` mass-correct; all on the Poodle) | Lambert 1,967 at T 1,191 (1,963-2,008 over 1,100-1,300 d) |
| mid-course plane change | **380-430** at dep + 350-450 d (UT 51.2-53.3 M), budget 450; > 550 = wrong burn time or seed | 3D Lambert from the projected path: 382 at dep + 370 d |
| trims | 20-60 (20 d out + inside the SOI, `--inc-to 0`) | Dres plan; Eve 2 far-out lesson |
| capture 70 x 1,000 km | **1,650-1,750** (v_inf 2,150-2,300: v_pe 2.32 km/s -> 0.66); Poodle's last ~350 at 15 m/s2 then the Terrier ~1,350 at 6.6-10 m/s2, ~185 s; finite-burn loss ~15 | hyperbola from v_inf; `transfer` refuses above 1.25 x 2,212 + 50 = 2,815 |
| pe 70 -> 20 km at the ap | 12 | |
| circularize 20 km | **168** (737 -> 569) | |
| landing from 20 km circular | **~960**, budget 1,050 (kill 569 + ~90 gravity loss during it + free fall 260 + hover ~40; Moho 1 flew 16 % over the simple sum) | Moho 1: 1,335 for 783 + 367 free fall (same code) |
| **total** | **~5,450** | vs Poodle ~2,860 + Terrier 3,683 = **~6,545: margin ~1,100 (20 %)** |
Sequence with masses: Poodle after LKO ~2,860 -> ejection 2,010 -> **Poodle ~850** on the way -> mid-course 450 + trims 60
-> Poodle ~340 at the SOI -> capture: the Poodle burns out (auto-stage to the Terrier, ~35 s in) and the Terrier does
~1,350 -> **Terrier ~2,330 in the 70 x 1,000 km orbit** -> pe lowering + circularize -> ~2,150 -> landing ~1,000 ->
**~1,100 left on the surface**. Landing rule: after circularizing at 20 km the Terrier must show **>= 1,200 m/s** (`vessel`),
else stay in orbit (the orbit science is the base mission; the landing is the bonus).

## Arrival geometry (offline, stock elements at UT 69.3 M) — it decides the links
- Kerbin at arrival: **72.6 Gm** (Eeloo at 69.5 Gm from the Sun, true anomaly 324 deg, 44 deg past its descending node,
  near its perihelion), 72 deg from Eeloo's prograde, **11 deg from the Sun** (Kerbin is on the sunward side). The probe
  arrives 160 deg from prograde (Eeloo catches it from behind, ship near its aphelion), 99 deg from the Sun.
- Prograde hyperbola, pe 70 km (e ~19): sub-periapsis point has **Kerbin +60 deg, Sun +67 deg** (daylight); the ray to
  Kerbin never crosses Eeloo between nu -120 and +120 deg -> **no blackout in the capture burn**. Retrograde pass: Kerbin
  -63 deg, hidden nu -28..+50 deg = pe -50 s..+111 s: the whole burn. Rule: at the SOI entry `vessel` must read inc < 90
  and `signal` > 0; else `correct Eeloo --pe 70000 --inc-to 0` first (~15 h from the SOI edge (119 Mm) to the pe at this
  v_inf: time enough, do it right after `soi`).
- 70 x 1,000 km: period 4.1 h; 20 km circular: v 569, period 42.3 min, Kerbin below the horizon ~half the orbit (transmit
  waits). Eeloo turns **66.6 deg/h** (5.4 h day; 68 m/s at the equator — `land` holds surface retrograde, fine): the
  sub-Kerbin point passes any longitude within 5.4 h; Kerbin's declination from Eeloo is within +-6 deg of Eeloo's equator
  (no axial tilt; Eeloo 6.15 deg off Kerbin's plane): equatorial sites see Kerbin high every Eeloo day.
- Sun: **Kerbin passes behind the Sun at dep + 600 d = UT 56,548,906** (0.04 deg from the Sun's centre; disc 0.19 deg:
  ~1 day of blackout, nothing planned then — Dres 1's mid-course is at ~56.2 M, keep it > 2 days from 56.55 M); other
  minima 3.1 deg (dep + 400 d) and 0.81 deg at dep + 1,299 d (UT 71.65 M, after arrival; disc 0.22 deg: clear, but the
  link is weakest then). Finish the landing before ~UT 71.5 M (arrival 69.3 M: 2.2 M s of slack).

## Link budget
| leg | antennas | range (DSN 3, 250 G) | need | strength |
|---|---|---|---|---|
| LKO, ejection | OKTO 5k | 35 Mm | < 700 km | 1.0 |
| cruise (99 -> 79 -> 95 -> 66 Gm), mid-course at 56-60 Gm | RA-100 (+ HG-55 if extended) | 158 (167) Gm | <= 99 Gm | 0.32-0.72 |
| capture, orbit, landing, surface (73-82 Gm over the first 100 d) | RA-100 | 158 Gm | 73-82 Gm | ~0.45-0.56 |
The RA-100 is fixed: nothing to extend, nothing to retract for the landing, no `_antennas` dependence for control (Eve 2
lesson). The HG-55 is extended by `circularize` / `science --transmit` (code) and stays out. Ground stations only: our
relays are 2-15 G. Transmit cost: RA-100 6 EC/Mit (`_ec_per_mit` budgets by the dearest antenna, the HG-55's 6.67:
conservative); at strength 0.5 the RA-100 still moves a 135 Mit set in a few minutes.
Occlusion: none at the capture (above); Moho 1's landing-site rule applies (Kerbin > 20 deg up at touchdown, > 10 deg
150 s before: `Require Signal for Control` is ON — a landing burn with Kerbin below the horizon has no throttle).

## Science (Eeloo multipliers: high 10, low 12, landed 15; transmit fractions goo 0.3, Jr 0.35, thermo/baro 0.5, grav 0.4, seismic 0.45, mag 0.6)
| set | where | experiments -> science | Mits -> EC (6/Mit) |
|---|---|---|---|
| high (> 60 km: anywhere on 70 x 1,000) | right after the capture | thermo 40, baro 60, grav 80, mag 270, goo 30 -> **~480** | 135 -> 810 |
| low (< 60 km: the 20 km circular orbit) | after circularizing | thermo 48, baro 72, grav 96, mag 324, goo 36 -> **~575** | 135 -> 810 |
| landed | on the surface | thermo 60, baro 90, grav 120, seismic 135, goo 45, Jr 131 (+ mag 405 if it runs landed) -> **~580-985** | 165-210 -> 990-1,260 |
~1,650-2,050 sci + Eeloo world firsts (flyby, orbit, landing, surface science: Moho 1's firsts paid ~300k). Battery 2,810
covers each set in one go; `_transmit` waits per experiment for EC (RTG 0.75 + panels 0.22 in daylight ~ 0.97 EC/s: a
landed set recharges in ~20-25 min; the printed wait is pessimistic, gap 5).

## Landing plan
Airless, g 1.69, v_circ 569 at 20 km, rotation 5.4 h (68 m/s at the equator). Terrain up to 3.4 km (sampled): the 20 km
orbit clears everything. Biomes (from the game): Lowlands, Midlands, Highlands, Craters, Ice Canyons, Fragipan, Babbage
Patch, Mu Glacier, Northern / Southern Glaciers, Poles. `land --biome Lowlands Midlands --slope 4` (the lander is a 7.7 m
stack on 4 small legs, CoM ~3 m up: slope <= 4 deg matters, Moho 1 rule; Eeloo's canyons and glaciers are steep).
Sequence in the code: kill 569 m/s at 10-13 m/s2 (~50 s, falls ~2 km), warp most of the free fall from ~18 km (~150 s to
~250 m/s), suicide burn capped at 3 m/s2 (Terrier 10-19 m/s2 available: throttled), legs out in `_powered_descent`,
touchdown 1.5 m/s. Expect **~900-1,050 m/s**, ~10 min real time. Site with the link: the far half of a 20 km orbit has no
link; as on Moho 1 choose the pass with Kerbin's elevation > 20 deg at touchdown (`land --science` / the site finder
merged in session 3, else scratch `tools/scratch/site.py`) and `land --at`. Panels and RA-100 fixed, the HG-55 stays
extended. Surface heat: none (0.038x sun, parts at ~150 K; no part has a minimum temperature). Night landing is fine
(RTG 0.75 EC/s; the landed set needs ~1,000 EC of 2,810; `science --transmit --all` waits for the link).

## Phases (expected numbers = the checkpoint's "Expect" line; compare after every phase)
Timeline: now UT ~43.37 M; the window is 43.59 M (10 d): build and launch now, `transfer` warps to the window from orbit
(P/2 before it); ejection ~43.59 M; **mid-course dep + 350-450 d = UT 51.15-53.3 M** (not the planner's 66.6 M); trim
~68.9 M (20 d out); Eeloo SOI ~69.25 M; capture ~69.3 M; keep clear of the conjunction 56.55 M; landed before ~71.5 M.

| phase | command | expect | Poodle / Terrier left | real time |
|---|---|---|---|---|
| pad | `build crafts/eeloo-1.json`, `launch "Eeloo 1"` | 1420 SL, TWR 1.37 / 1181 SL, TWR 0.84 / 3414 vac / 3683 vac; 52 parts, 138.7 t; `signal` 1.0 | 3414 / 3683 | 2 min |
| ascent + circularize | `ascent --alt 80000 && circularize` (background, full output; poll the file every minute) | Twin-Boar out ~82 s, Skipper out ~3:20 at ~45 km (TWR 0.84: the t_apo guard flies almost level at 45-51 km for ~2 min on the Poodle at TWR 0.7 — Moho 1 #47: OKTO skin peaked 880 K, stop rule 1,000 K); apoapsis >= 45 km at 3:00; pitch ~27 at MET 120; 79-80 x 80 km; transonic AoA < 3 deg | **2,800-2,900** / 3683 | 12 min |
| ejection | `transfer Eeloo --pe 70000 --plan` -> read -> `ksp node` | Lambert: **T 1,170-1,220 d (Hohmann 1,168)**, v_inf dep ~2,760, ejection ~1,970, arrival v_inf **2,150-2,250** (projected), **Eeloo -4,500..-5,500 Mm out of plane**, plane change printed ~170-180 (ignore: see mid-course), "no encounter by design ... `correct Eeloo --pe 70000` around UT ~66.6 M" (ignore the UT); node **1,960-2,000**; refused > 1.3 x Hohmann + 50. Burn ~270 s on the Poodle alone (no staging). After it: `vessel` -> Sun ap ~69-70 Gm (read as radius), pe ~13.6 Gm, **Poodle ~800-870** | **~850** / 3683 | 8 min |
| cruise 1 | `scene space_center`, `warp-sc 51,100,000` (~7.5 M s: ~1.5 real min at 100,000x; lab visits, Duna 2, Eve 2 in between), `fly "Eeloo 1"` | link ~0.7 (RA-100 at 56 Gm) | | 5 min |
| **mid-course (early)** | at UT 51.15-53.3 M: `correct Eeloo --pe 70000 --inc-to 0 --plan` -> compare with **380-430** -> `ksp node` | far-out path, direct 3D Lambert seed (arc to fly ~50 deg): "far out (~820 d to go)... estimate ~380-430, cap ~1,200"; node **380-450**, pure normal (+ a few m/s in plane), Eeloo pe ~70 km, inc < 90, encounter shown. Poodle at 250 kN on 18 t: ~30 s. After it: `vessel` shows the Eeloo encounter, pe 0-500 km (far-out precision), inc < 90 | ~400 / 3683 | 8 min |
| cruise 2 | `scene space_center`, `warp-sc 68,900,000` (~16 M s: ~3 real min; Jool 1, Dres 1's phases in between), `fly "Eeloo 1"` | link ~0.5 (RA-100 at 75 Gm) | | 5 min |
| trim 20 d out | `correct Eeloo --pe 70000 --inc-to 0 --plan` -> `node` | 5-40 m/s; pe 70 +-100 km; do NOT chase sub-km errors here | ~370 / 3683 | 3 min |
| Eeloo SOI | `soi` (refuses pe < 4.9 km), then `correct Eeloo --pe 70000 --inc-to 0 --plan` -> `node` | v_inf **2,150-2,300**; pe 60-80 km (**< 15 km = raise first**); inc < 90 (prograde) and `signal` > 0; 1-20 m/s; **~15 h to the pe** at rails warp | | 5 min |
| capture | `capture --apo 1000000` (background, full output) | **1,650-1,750 m/s**, ~185 s: the printed burn time must be ~180-200 s and mention two stages (Poodle ~35 s, then the Terrier at 6.6 -> 10 m/s2); no link blackout -> **70 x 1,000 km, period 4.1 h**; a burn stopping hyperbolic -> `capture` again at once | 0 / **~2,300** | 6 min |
| science high | `science --transmit --all` (anywhere: all > 60 km) | ~480 sci; 810 EC of 2,810 | | 5 min |
| lower the pe | at the ap: `periapsis --alt 20000` | **~12 m/s** -> 20 x 1,000 km | | 5 min (2 h warp) |
| circularize | at the pe: `capture` (no --apo) | **~170** -> 20 x 20 km, 42.3 min | 0 / ~2,120 | 5 min |
| science low | `science --transmit --all` (whole orbit < 60 km) | ~575 sci; 810 EC (charge first if < 1,000: ~1 EC/s in daylight) | | 5 min |
| landing decision | `vessel` | Terrier >= 1,200 -> land; else the orbit mission is done | | |
| landing | `land --biome Lowlands Midlands --slope 4 --science` with Kerbin's elevation > 20 deg at touchdown (site finder / scratch site.py), `land --at LAT LON` (background, full output) | **~900-1,050 m/s**: horizontal kill 569 (~50 s), free-fall warp, suicide burn capped at 3 m/s2, touchdown 1.5 m/s, upright; no `damage`/`attitude` events | 0 / **~1,050-1,200** | 12 min |
| surface science | `science --transmit --all`, then `contracts -v` for new Eeloo contracts | ~580-985 sci; EC 2,810 -> ~1,600-1,800; RTG recharges | | 5 min |

## Code gaps (nothing blocks the launch; 1 and 2 matter before the mid-course at ~UT 51.2 M)
1. **`transfer`'s mid-course advice is wrong for eccentric transfers**: its plane term prices the tilt at the arrival speed
   ~90 deg of true anomaly before arrival; on a 0.67-e transfer that is 127 d out, 2.4 km/s and ~1,900 m/s for real. Fix:
   scan the single-burn 3D Lambert cost over the flight (as the scratch does) and print the cheapest UT and dv; use that
   cost in `dv_total` too (here it barely moves the best T). Until then the phase table's UT (dep + 350-450 d) stands.
2. **`correct` far out with no encounter** at 820 d to go: the direct 3D Lambert seed should win (arc to fly ~50 deg < 120),
   giving ~380-430 pure normal. Stop rule: the printed estimate or node > 550 -> do not burn; check the seed choice
   (`by_design` / in-plane seed would be the 174-m/s mistake with the plane left for later) and, if needed, build the node
   from the scratch's 3D Lambert vector as on Moho 1. Also the compass search's dv cap is 3 x estimate + 0.5: fine.
3. **Low-space threshold in `science`**: it reports the situation from KSP (fine), but `capture --apo` has no notion of
   Eeloo's 60 km line; the 70 km periapsis choice replaces a check. `TERRAIN["Eeloo"]` 3,900 vs 3,418 sampled: fine.
4. `transfer` has no flight-time override (`--T`): it takes the cost-optimal ~1,191 d; a 1,100-d path (+70, -91 d) is not
   reachable from the CLI. Not needed.
5. `_transmit` budgets the recharge time from solar panels only (`flow`): with an RTG the printed wait is pessimistic and
   "in the shade" waits still work; at Eeloo the panels give 0.22 EC/s, so the printed waits will look long. Cosmetic.
6. `capture` at Eeloo spans two stages (Poodle ~35 s, Terrier ~150 s): `burn_lead` (mass-correct, multi-stage via the
   mod's `RecalcDeltaV`) was fixed after Moho 1 #47 and Moho 1's capture auto-staged fine (38.7 x 999.6). Stop rule: a
   printed burn time < 150 s or > 260 s -> stop, `vessel`, rerun.
7. `land` kills all horizontal speed at the start point: ~90 m/s of gravity loss during the 50-s kill at Eeloo; a
   `--from-pe` mode (Moho plan gap 7) would save ~100-150. Not needed at margin 20 %; worth doing if the Poodle is < 2,600.
8. `soi` refuses a predicted pe below `TERRAIN["Eeloo"]` + 1 km = 4.9 km: right for Eeloo (max sampled 3.4 km).

## Risks and stop rules
- **Pad numbers off** (1420 SL / 1.37, 1181 SL / 0.84, 3414 vac, 3683 vac; 138.7 t, 52 parts): `recover`, fix the spec.
  Pad limit 140 t: the 4 x Tail Fin fallback (+0.5 t) still fits; nothing else may be added.
- **Ascent**: the Skipper ignites at TWR 0.84 (Moho 1 #46 was lost flat before the t_apo guard; #47 flew: apoapsis 46.8 km
  at 3:00, skin 880 K). AoA through Mach 1 > 5 deg or an `attitude` event -> revert to launch, add 4 x Tail Fin on t1b.
  Apoapsis < 45 km at 3:00 or OKTO skin > 1,000 K -> revert. Poodle < 2,600 in LKO -> see the checkpoints above.
- **Ejection**: node 1,960-2,000; > 2,150 or projected arrival v_inf > 2,400 in the Lambert line -> do not burn, diagnose
  the window geometry (the planner may pick T outside 1,100-1,300). A burn ending > 50 m/s short -> `correct Eeloo --pe
  70000 --plan` inside the SOI at once (Oberth). No encounter is expected at this point (Eeloo -5 Gm out of plane): read
  the Sun orbit (ap ~69-70 Gm, pe ~13.6 Gm) instead, then leave. **Do not follow the printed "correct around UT ~66.6 M".**
- **Mid-course** (UT 51.15-53.3 M): expect 380-450; > 550 -> stop (3 attempts max: `--inc-to 0`, the scratch's 3D Lambert
  vector as a hand-built node, else keep the in-plane path and settle for a flyby: it passes 5 Gm from Eeloo, so a flyby
  needs the burn anyway — this burn is the mission). Missing the window: each 100 d later costs ~+50 (dep + 550: 426, dep +
  800: 636 = the landing). Waiting past dep + 650 d ends the landing; past dep + 900 d the capture.
- **Arrival**: pe after the in-SOI trim 60-80 km; < 15 km with < 1 h to pe -> raise it now (`correct --pe 70000`), never
  warp to a pe under the terrain. Retrograde pass -> flip with `--inc-to 0` (15 h available). Signal 0 at the SOI entry
  (Kerbin behind Eeloo is impossible there: 119 Mm out) -> tooling: `vessel`/`scene` and retry, do not warp to the pe
  without it. Link strength ~0.5 is normal here, not a fault.
- **Capture**: 1,650-1,750 expected, ~185 s over two stages; a burn that stops with the craft still hyperbolic -> `capture`
  again at once (it burns past the pe); any bound orbit is a win (science from it). Budget for a late start: +100 m/s.
- **Landing**: only with Terrier >= 1,200 after the 20 km circularization, a slope <= 4 deg Lowlands / Midlands site with
  Kerbin > 20 deg up; touchdown `damage` events -> `log`, the orbit science is already home.
- **Link / power**: strength 0.3-0.7 on the fixed RA-100 over the whole mission, nothing deploys; the HG-55 is a backup that
  adds ~6 % range. Transmit only with EC >= 1,100 (the code waits per experiment). Solar conjunction 56.55 M (1 day, during
  the cruise: no burn within 2 days of it); after arrival the Sun angle stays > 0.8 deg (clear). Be landed and transmitted
  before ~71.5 M.
