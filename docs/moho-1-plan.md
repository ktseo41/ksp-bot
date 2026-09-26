# Moho 1 — plan (uncrewed Moho orbiter + lander, first Moho visit)

Spec: `crafts/moho-1.json` (built OK 2026-09-26: 52 parts, **138.08 t** (pad 140), 79,930 funds, 4 stages, no warnings).
OKTO-controlled, one way: everything is transmitted. Window UT **38,450,305** (`ksp window Moho`, +137.8 d from
UT 35.47 M), Hohmann flight 113 d, arrival ~UT 40.9 M. `build` writes the .craft only; the per-stage table below is the
rocket equation on the exact part masses (the pad sum 138.08 t matches KSP's) — `launch` must print the same numbers.

## Why not the Jool 1 Nerv orbiter
The numbers are not what the rough budget said (checked with `kspbot.kepler` + `flight._lambert`, the planner's own
projected Lambert, scratch `moho_plan.py`):
- At this window Moho is met **near its periapsis** (r 4.26 Gm, true anomaly 338 deg, 10x Kerbin's sunlight), which is the
  cheap side for the ejection (v_inf 2,870 -> **2,040 m/s** from 80 km) but the arrival is 7 deg off Moho's orbital plane
  at its ascending node: **arrival v_inf 3,450-3,550**, not 3,000. Capture into a 25 km orbit costs **~2,690** (elliptical
  25 x 1,000 km) / 2,900 (circular), plus a mid-course plane change **200-400** at the 90 deg point. Total from LKO
  ~5,200 (+ landing ~1,200 = 6,400, before losses).
- The capture hyperbola has e = 21: it is a straight line past Moho at 3.7 km/s, the Oberth window is ~2 minutes. A single
  Nerv (60 kN on 14 t) needs 12 minutes for 2,700 m/s -> most of it would be burned far from Moho, ~500 m/s lost and an
  unpredictable orbit. Capture needs chemical thrust: Poodle 250 kN first, Terrier 60 kN to finish (4.2 min total).
- A Nerv ejection stage for a 8.4 t lander would burn 2,100 m/s for 9-10 min from a 30-min orbit (+-60 deg of orbit:
  ~17 % cosine loss); two Nervs 6 min (~9 %). The Poodle does it in 4 min (~2 %) and is 8.7k cheaper. So: chemical.
- The one big saving left is in the planner, not the craft: an unprojected (3D) Lambert with the parking orbit launched
  into the departure plane (inc ~21 deg) gives eject 2,170 + arrival v_inf **2,570** (capture 2,010): **4,185 vs 5,222**
  (see code gaps). Not for this flight; the design has to carry the 5,222.

## Craft
| function | part | mass (t) | note |
|---|---|---|---|
| control | OKTO + Small Inline Reaction Wheel (5 kN.m) | 0.15 | Poodle (5 deg) and Terrier (4 deg) gimbal every burn; the wheel only turns the craft between burns (37 t stack: ~25 s per 90 deg) |
| lander tanks/engine | FL-T800 + FL-T400 (6 t LF/Ox) + Terrier | 7.25 | **4,218 m/s vac**, Terrier 7.1 m/s2 at 8.4 t, Moho TWR 4.9-7.7 on landing |
| legs | 4 x LT-1 on the FL-T400 at height -0.7 (sandbox lander test geometry, feet below the Terrier bell) | 0.20 | `land` measures the feet from the bounding box |
| comms | 2 x HG-55 (deployable, 15 G each, combined 25 G) high on the FL-T800 | 0.15 | with DSN 3 (250 G): range **79 Gm**; Kerbin-Moho max 19.0 Gm -> strength ~0.85 (one HG-55 alone: 61 Gm, 0.74). 6.67 EC/Mit, 133 EC/s |
| power | 4 x OX-STAT-XL (2.8 EC/s each at Kerbin, **~28 EC/s each at Moho**, 10.2x flux) + Z-1k + 2 x Z-400 + OKTO = **1,810 EC** | 0.30 | fixed panels: nothing to retract for the landing |
| science | Science Jr, 3 x goo, 2HOT, PresMat, GRAVMAX, Double-C seismic, magnetometer boom | 0.47 | all on the FL-T800 (Jr angle 0, goo 90/180/270, sensors at 45/135/225/315 h -0.6, boom 180 h -1.3) |
| ejection stage | Poodle + X200-32 + X200-16 (24 t), Rockomax adapter, TD-12 above, 4 x AV-T1 | 29.0 | **3,513 m/s**: LKO top-up, ejection, mid-course, then its rest opens the capture burn at 250 kN |
| launcher | Twin-Boar + X200-32 + X200-16 (56 t fuel); Skipper + X200-32 + X200-16 (24 t); TD-25 x2; AV-R8 x4 x2 | 100.6 | Ike Station 1's Twin-Boar pattern with 2.5 m tanks instead of the S3-3600/ADTP hump |
Lander dry 2.42 t; the 1.25 m stack (OKTO..Terrier) is ~7.5 m / 7 joints on a 2.5 m launcher: every stack part rigid +
autostrut Root, fins on all three atmospheric stages (Minmus Lab 1 / Jool 1 lesson).

## Stages (rocket equation on part masses; Isp SL/vac)
| stage | engine | fuel | m0 -> m1 (t) | dv SL / vac (m/s) | TWR SL / vac | full burn |
|---|---|---|---|---|---|---|
| 1 | Twin-Boar (1867/2000 kN, 280/300) | own 32 t + X200-32 + X200-16 = 56 t | 138.08 -> 82.08 | 1428 / 1530 | **1.38** / 1.48 | 82 s |
| 2 | Skipper (569/650 kN, 280/320) | X200-32 + X200-16 = 24 t | 68.02 -> 44.02 | 1195 / 1366 | **0.85** / 0.97 | 116 s |
| 3 | Poodle (250 kN vac, 350) | X200-32 + X200-16 = 24 t | 37.46 -> 13.46 | - / **3513** | 0.68 vac | 330 s |
| 4 (lander) | Terrier (60 kN vac, 345) | FL-T800 + FL-T400 = 6 t | 8.42 -> 2.42 | - / **4218** | 0.73 (Kerbin) | 338 s |
Launcher SL1 + vac2 = **2,794**; our LKO calibration is 3,250 (Jool 1 3,224, Ike Station 1 3,255) — with the Skipper at
TWR 0.85 count **3,300**: the Poodle spends ~500 finishing the orbit and should show **~2,950-3,050 m/s** in LKO
(checkpoint: < 2,750 -> the landing margin is gone, orbit-only mission; < 2,500 -> `recover`/revert and redesign).
Pad check: `launch` must print stage 1 ~1428 SL / TWR 1.38, stage 2 ~1195 SL, Poodle ~3513 vac, Terrier ~4218 vac.

## Δv budget (m/s)
| item | expect | source |
|---|---|---|
| LKO 80 km | 3,300 of the launcher + Poodle | calibration + 50 for the 0.85 TWR Skipper |
| ejection | node **2,030-2,050**, executed ~2,100 (4 min at 6.7-9 m/s2, ~2 % steering) | projected Lambert at the window, T 113.3 d (planner grid) |
| mid-course plane change | **200-400** at the 90 deg point (planner prints ~250-330; Eve 1 got 372 for a printed 413) | z2 = -40..-90 Mm at 4.3 Gm, ~16 km/s |
| trims | 5-30 (10 d out + inside the SOI) | Jool 1 / Duna 1 far-out burn errors |
| capture 25 x 1,000 km | **2,690** (v_pe 3,690 -> 1,003; v_inf 3,520); circular would be 2,900 | hyperbola from v_inf |
| circularize at pe | 280 (1,003 -> 783 at 25 km) | |
| landing from 25 km circular | **~1,200** (`land`: 783 horizontal kill + 367 free-fall from 25 km + ~50 hover); ~1,070 if `land` is started at the pe of a 25 x 8 km orbit | Moho g 2.70, terrain up to 6.8 km |
| **total after LKO** | ~6,600 | vs Poodle 3,000 + Terrier 4,218 = 7,200 -> **margin ~600** |
Sequence with masses: Poodle after LKO/ejection/mid-course ~580 m/s left (16 t, 15.7 m/s2, 34 s) -> Terrier 2,100 of the
capture (8.42 -> 4.52 t, 220 s) -> **Terrier ~2,110 left in the 25 x 1,000 km orbit**, ~1,830 after circularizing, **~630
after the landing**. Landing rule: after circularization the Terrier must show **>= 1,350 m/s** (`vessel`), else stay in
orbit (a 25 km orbit with all science is the base mission; the landing is the bonus).

## Window and phases (expected numbers; compare after every phase)
Timeline: now UT 35.47 M; window 38,450,305; mid-course ~40,455,500 (dep + 93 d, planner prints the exact UT); Moho SOI
~40,900,000; arrival/capture ~40,904,500 (+251 d from now). Other traffic: Minmus Lab visits every ~50 d; Jool 1 SOI 52.79 M.
Waiting in an 80 km orbit is 100x rails at best (138 d = 8 real hours): **warp from the space center** (`warp-sc 38300000`,
~1.7 d before the window), then launch.

| phase | command | expect | Poodle / Terrier dv left | real time |
|---|---|---|---|---|
| pad | `launch "Moho 1"` | numbers above; `signal` 1.0 (KSC) | 3513 / 4218 | 1 min |
| ascent + circularize | `ascent --alt 80000`, `circularize` | 79-80 x 80 km; Twin-Boar + Skipper ~2,800, Poodle finishes; HG-55s extend on circularize (code) | **2,950-3,050** / 4218 | ~10 min |
| ejection | `transfer Moho --pe 25000 --plan` -> read -> `ksp node` | Lambert line: T ~113 d, v_inf dep ~2,870, arrival v_inf **3,450-3,550**, Moho -40..-90 Mm out of plane, "no encounter by design", mid-course UT ~40,455,500; node **2,030-2,060**; refused above 3,100 (1.5x + 20) | ~850-950 / 4218 | 6 min |
| after ejection | `vessel`, conics | Sun pe ~4.2-4.3 Gm (read `_describe` pe as radius - 262 Mm), no Kerbin re-encounter | | |
| cruise 1 | `scene space_center`, `warp-sc <t_pc - 3600>`, `fly "Moho 1"` | link ~0.95 (HG-55 x2 at <= 14 Gm) | | 1 min |
| mid-course | `correct Moho --pe 25000 --plan` -> `ksp node` | **200-400 m/s**, Moho pe ~25 km, inc ~7-15 (any); refused if far above the printed plane-change figure | ~500-700 / 4218 | 3 min |
| trim | ~10 d before the SOI: `correct Moho --pe 25000 --plan` | 1-20 m/s (a far-out error of 1 m/s here moves the pe by ~1,000 km) | | |
| Moho SOI | `soi`, then at once `correct Moho --pe 25000 --inc-to 0 --plan` -> `node` | SOI 9.65 Mm, **45 min from entry to pe at 3.5-3.7 km/s**; pe must read 20-35 km (terrain 6.8 km); prograde pass (inc < 20) | | 10 min |
| capture | `capture --apo 1000000` (in the background, full output) | **~2,690 m/s**, ~4.2 min (Poodle 34 s -> stage -> Terrier 220 s), burn starts ~2 min before pe; result 25 x 1,000 km, period 2.8 h | 0 / **~2,100** | 6 min |
| science low | `science --transmit` at the pe (< 80 km = low space) in sunlight, EC > 1,100 | thermo 32, baro 48, grav 64, mag 216, goo 24 -> ~380 sci; 135 Mits = 900 EC | | |
| science high | `warp` to the ap (> 80 km), `science --transmit` | ~340 sci (x7) | | |
| circularize | at pe: `capture` (no --apo) | **~280** -> 25 x 25 km, period 37 min | 0 / ~1,830 | |
| landing decision | `vessel` | Terrier >= 1,350 -> land; else orbit mission done | | |
| landing | `land --biome <flat biome> --slope 4` (Central/Western Lowlands, Midlands) | **~1,200**: horizontal kill 783 (~80 s at 13 m/s2), free fall, suicide burn capped at 3 m/s2, touchdown 1.5 m/s | 0 / ~600 | 15 min |
| surface science | `science --transmit` (needs the fix in code gaps: goo/Jr are not transmitted today) | thermo 40, baro 60, grav 80, seismic 90, goo 30, Jr 88 -> ~390 sci; 165 Mits = 1,100 EC, battery 1,810 | | |
Expected science ~1,100 (Moho multipliers: high 7, low 8, landed 10; transmit goo 0.3, Jr 0.35, thermo/baro 0.5, grav 0.4,
seismic 0.45, mag 0.6; data sizes goo 10, Jr 25, thermo 8, baro 12, grav 60, seismic 50, mag 45 Mits) + the Moho world
firsts/contracts.

## Link budget and occlusion
- HG-55 x2: 25.2 G x DSN 250 G -> 79 Gm; Kerbin-Moho 13.8 Gm at arrival, 19.0 Gm max (+35 d). Strength 0.85-0.95.
  Ground stations only (our relays are 2-15 G: sqrt(25 x 15) = 19 Gm, marginal) — Kerbin's extra ground stations give
  continuous line of sight.
- **Sun**: the Sun-Moho-Kerbin angle peaks at 175.3 deg (+25 d); the Sun's disc is 2.9 deg from Moho -> never occulted.
- **Capture pass**: at arrival Kerbin sits ~100 deg from the Sun as seen from Moho, on Moho's retrograde side (Kerbin is
  ~70 deg behind Moho in longitude). A **prograde** pass (`--inc-to 0`) puts the periapsis on the anti-Sun/outward side;
  the ray to Kerbin from every point of the +-2 min burn arc moves away from Moho -> no occlusion. A retrograde pass has
  its pe on the sunward side and the ray grazes Moho's limb ~4 min after pe. So: prograde, and read `signal` at the SOI
  entry; if it is 0 there, wait for it before creating the capture node (45 min of lead). Behind Moho later (science
  passes): only the far-side half of each 25 km orbit (18 of 37 min) has no link; `science --transmit` waits for it.
- LKO parking: the OKTO's own antenna is enough near Kerbin; `circularize` extends the HG-55s.

## Landing plan
Airless, g 2.70 m/s2, v_circ 783 m/s at 25 km, rotation 1.21 Ms (surface speed 1.3 m/s, ignore). Terrain up to 6.8 km:
the 25 km orbit clears everything. `land` (kill all horizontal speed, warp the free fall, throttled 3 m/s2 curve): kill
783 m/s at 13-15 m/s2 = ~60 s (falls ~5 km meanwhile), free-fall from ~20 km reaches ~330 m/s, suicide burn ~360 m/s
+ hover -> **~1,150-1,250 m/s**. Legs LT-1 deploy in `_powered_descent`, feet measured from the bounding box. With
`--biome` the site filter waits for a pass over slope <= 4 deg (Moho is craggy; the lander is a 7.5 m stack on 4 small
legs, CoM ~3 m up: **slope <= 4 deg matters**). Cheaper variant (~1,070): `periapsis --alt 8000` then `warp` to the
periapsis and `land` there — only over a known-flat site, not worth the mountain risk on a first visit.
Panels are fixed OX-STAT-XL (nothing to break), antennas stay extended (HG-55 folds to ~1 m, 6 m up the stack).
Surface heat: parts at Moho sit at ~350-450 K (equilibrium for 13.7 kW/m2 is ~700 K), all limits >= 1,200 K: no radiator.

## Code gaps (fixes to make before the phases that need them; no flight code changed here)
1. **`science --transmit` never transmits goo / Science Jr** (`do_science`: only `e.rerunnable` experiments are sent, the
   rest is "kept for recovery"). A one-way probe loses them (Jool 1 too). Fix: a `--all` flag -> `if transmit and
   (e.rerunnable or all_)`. Needed before the first Moho science pass.
2. Transmit EC guard is `ec > 120`: a 900-1,100 EC set on 1,810 EC stalls when the battery empties (KSP does not resume).
   Fix: per experiment require `ec >= Mits x EC/Mit (HG-55 6.67, 88-88 10) + 100`, else wait in sunlight; then poll the
   science total until it rises (as `lab transmit` does now).
3. **Capture on an uncrewed craft with a dead link**: `execute_node` -> `_await_link` warps toward `node.ut + bt/2`,
   i.e. through the periapsis; a late start at Moho (e = 21) is a flyby. Fix: (a) before `capture`, forecast the link:
   sample the orbit over [t_pe - bt, t_pe + bt], test the Kerbin direction against Moho's disc (ray-sphere) and against the
   Sun; refuse early with "flip the pass side (`correct --inc-to 180`)"; (b) capture burns never pause: on a mid-burn
   link loss keep the loop running at throttle 1 without warping (thrust returns with the link).
4. `transfer_planet` scans the flight time on a 2 % grid (2.3 d): at Moho the projected cost is 5,268 at T 113.3 d but
   **5,094 at 114.75 d**, where Moho is only -6 Mm out of plane (inside the SOI: no mid-course needed). Fix: golden-section
   refine T around the best grid sample (+-1 step). Also the plane-change term (|z2|/R2 x v) overestimates what `correct`
   pays (Eve 1: 413 printed, 372 burned).
5. **3D departure (saves ~1,000 m/s at Moho, ~4,185 vs 5,222)**: unprojected Lambert (`plan()` without the z2 projection)
   + park in the plane that contains the required v_inf: inclination = |declination of v_inf| (~21 deg here), LAN from its
   right ascension (two choices), launched with `ascent --heading` at the time `wait_plane(inc, lan)` gives (KSC is on
   the equator, so the launch time sets the LAN at 1 deg/min). `_match_exit` already tunes prograde/normal/ut from any
   plane. A real project; do it for Moho 2 / Eeloo.
6. `correct` far out: burn errors of a few m/s put Jool 1's pe at -655 km. At Moho a -300 km error is an impact; the plan
   carries a second trim 10 d out and one inside the SOI (45 min). Tooling: after every far-out `correct` print the
   predicted pe again 60 s after the burn and refuse to `soi`-warp into a body when the pe is below the terrain height.
7. `land`: kills all horizontal speed where it is started; a `--from-pe` mode (deorbit burn to a low pe over the site,
   start the kill at the pe) would save ~130 m/s; the `--biome` filter is the only slope guard (needs biome names; Moho:
   Central Lowlands, Western Lowlands, Midlands, Highlands, Minor Craters, Northern/Southern Sinkhole Ridge, Canyon).
   Low-TWR is not the issue for this lander (Moho TWR 5-8); the 3 m/s2 decel cap keeps the burn gentle.
8. Real-time waits: `transfer` warps to the window from LKO (100x at 80 km: 8 hours for 138 d) — go through the space
   center (`warp-sc`); `warp_to` prints the estimate but does not refuse.
9. `transfer` handles the inclined target as designed: the arrival point is projected onto our plane, the plane change is
   left to `correct` at the printed UT (Eve 1 precedent, 372 m/s). It refuses if v_inf_dep > 1.3 x Hohmann + 50 (2,870
   vs 2,872: passes) and `_approve` refuses a node above 1.5 x expect + 20.

## Risks and stop rules
- **Pad numbers off** (Twin-Boar 1428 SL / TWR 1.38, Skipper 1195, Poodle 3513, Terrier 4218): `recover` on the pad, fix.
- **Ascent**: 7.5 m 1.25 m stack on a 2.5 m launcher, Skipper TWR 0.85 at staging. Stop: `attitude` events after the
  Twin-Boar separation -> revert to launch; Poodle < 2,750 in LKO -> orbit-only mission; < 2,500 -> revert/redesign.
- **Ejection**: node 2,030-2,060; > 2,300 or arrival v_inf > 4,000 in the Lambert line -> do not burn, diagnose (window
  geometry); a burn ending > 100 m/s short (Jool 1) -> `correct Moho --plan` at once while Oberth lasts, compare with the
  ~250-330 mid-course figure; if the fix exceeds 600 m/s the landing is off, if it exceeds 1,000 abort (Poodle can't).
- **Mid-course**: expect 200-400; > 600 -> stop (3 attempts max: retune with `--inc-to 0`, else keep the flyby).
- **Arrival**: pe after the in-SOI trim must be 20-35 km; < 10 km with < 20 min to pe -> raise it now (`correct --pe
  30000`), never warp to a pe under the terrain. Signal 0 at the SOI entry -> wait for it before the node (45 min lead).
- **Capture**: 2,690 expected, ~4.2 min; a burn that stops with > 300 m/s left (staging, link) -> immediately `capture`
  again if still hyperbolic (the code burns now when pe is past); if it fails, `vessel` and decide: any bound orbit is a
  win (science from it), a flyby is the loss.
- **Landing**: only with Terrier >= 1,350 after circularization and a slope <= 4 deg site; `damage` events on touchdown
  -> `log`, the orbit science is already home.
- **Heat/power**: none expected (10x sun, 1,810 EC, fixed panels). Transmit only with EC >= 1,200 and in sunlight.
