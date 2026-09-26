# Duna 2 — plan (uncrewed Duna surface probe, contract "Science data from surface of Duna")

Spec: `crafts/duna-2.json` (offline: 49 parts, **79.73 t** on the pad of 140, ~27 m of 36, ~75k funds; not yet built in the
VAB). OKTO-controlled, one way: everything is transmitted. Contract: **132,825 funds** for any surface experiment from Duna,
transmitted. Window Kerbin -> Duna **UT 44,649,525** (`ksp window Duna`); Lambert at the window (scratch `duna2_plan.py`,
stock elements): flight **308 d**, arrival **UT ~51,304,000**. The per-stage table is the rocket equation on the exact
part masses — `launch` must print the same numbers.

## Decision: capture first, then a chosen deorbit (not a direct entry)
- **Direct entry from the hyperbola is out.** At v_inf ~720 the entry speed at 50 km is ~1.6 km/s and the craft must lose
  ~280 m/s of it in the air to be captured at all. A 1.25 m stack with legs and dishes (ballistic coefficient ~1,500
  kg/m^2) sheds ~300 m/s at a 15 km periapsis and ~4x that at 8 km: the pe would have to sit within a few km of the right
  height over terrain that reaches 5-8 km, and the far-out corrections are known to be imprecise (LOG 2026-09-27: trim
  ~20 d out, then inside the SOI). One error = a flyby (no second chance) or a crater. The landing longitude would also be
  fixed by the hyperbola (Kerbin only 20 deg up at the sub-periapsis point).
- **Capture to 100 x 1,000 km (~350-520 m/s), circularize at 100 km (~200), then `deorbit --under Kerbin`** puts the entry
  where Kerbin is overhead in daylight, gives an orbit science pass, and lets us read the terrain under the predicted
  periapsis before committing. Cost ~600-700 m/s more than a direct entry; the Poodle's leftover pays most of it (Duna 1
  pattern: the Poodle ran dry inside the capture burn, the Terrier finished). Δv is not the constraint here (4,400 after
  LKO for a ~2,100 need), precision and the link are.
- Prograde arrival pass only: it has Kerbin +20 deg above the horizon at the periapsis and **no blackout** over the burn;
  the retrograde pass hides Kerbin from -41 to +39 deg of true anomaly around the pe (the whole burn). Set it inside the SOI
  with `correct Duna --pe 100000 --inc-to 0` (Duna 1: 6.3 m/s).

## Craft
| function | part | mass (t) | note |
|---|---|---|---|
| control | OKTO (root) + Small Inline Reaction Wheel (5 kN.m) | 0.15 | Terrier/Poodle gimbal for burns; the wheel holds retrograde in the entry (4.6 t: fine, Moho 1 same) |
| lander tank/engine | FL-T400 (2 t LF/Ox) + Terrier (60 kN, Isp 85/345) | 2.75 | **1,947 m/s vac**; Duna accel 13.1 m/s2 wet -> 23 dry (g 2.94: TWR 4.5-8) |
| legs | 4 x LT-1 on the FL-T400 at height -0.7 (Moho 1 geometry: feet below the Terrier bell, landed upright) | 0.20 | crash tolerance 12 m/s |
| chutes | 3 x Mk2-R on the upper Z-1k, **own stage (5)** — Duna 1 lesson: never on the engine's stage | 0.30 | Mk2-R opens below 0.04 atm = ~3 km ASL on Duna, full at 1 km AGL: they take the last km only. 3 Mk2-R held Duna 1's 7.4 t at 13 m/s (sandbox) -> **~8 m/s for this 2.6 t** (v ∝ sqrt(m)): a chute-only touchdown survives the legs (12) if the engine were lost |
| comms | 2 x RA-15 (fixed dishes, 15 G each, combined 25 G, 12 EC/Mit) on the Science Jr, angle 90/270 | 0.60 | fixed = link through the entry (Eve 2 lesson: retracted HG-55s leave the OKTO's 5k = no control at Duna). Range to DSN 3: **79 Gm** (one alone 61); Kerbin-Duna 24.3 Gm at arrival, 33 Gm at +120 d |
| power | RTG (0.75 EC/s always) + 2 x OX-STAT-XL (2.8 x 0.43 = 1.2 EC/s each at Duna, daylight) + 2 x Z-1k + 2 x Z-400 + OKTO = **2,810 EC** | 0.24 | landed set 165 Mits x 12 = 1,980 EC in one go; fixed panels, nothing to deploy or break |
| science | Science Jr (inline), goo, 2HOT, PresMat, GRAVMAX, Double-C seismic | 0.27 | sensors on the Jr at 45/135/225/315 h -0.2; goo on the Z-1k at 180 (chutes 0/120/240) |
| transfer stage | Poodle + X200-16 (8 t), Rockomax adapter, TD-12 above, 4 x AV-T1 | 11.04 | **2,466 m/s**: LKO top-up, ejection, trims, then opens the capture at 250 kN |
| launcher | Duna 1's: Mainsail + 2 x X200-32 (32 t), TD-25, 4 x AV-R8; Skipper + X200-32 (16 t), TD-25, 4 x AV-R8 | 64.12 | flown 3x in the career (Duna 1, Eve 1, Minmus Science 2); AV-R8s added on the Skipper tank (Minmus Lab 1 lesson: fins on every atmospheric stage) |
Lander wet 4.57 t / dry 2.57 t. Every stack part rigid + autostrut Root; radial parts plain. No blunt nose (a flat
1.25 m top with the 0.625 m OKTO, as Moho 1 #47 flew), so the Eve 2 tail-fin fix is not applied; it is the fallback (4 x
Tail Fin on t1b at 45 deg to the AV-R8s) if the recorder shows AoA growing through Mach 1.

## Stages (rocket equation on part masses; Isp SL/vac) — the pad check
| stage | engine | fuel (t) | m0 -> m1 (t) | dv SL / vac (m/s) | TWR SL / vac | full burn |
|---|---|---|---|---|---|---|
| 1 | Mainsail (1379/1500 kN, 285/310) | 32 | 79.73 -> 47.73 | **1434** / 1560 | **1.76** / 1.92 | 65 s |
| 2 | Skipper (569/650 kN, 280/320) | 16 | 37.17 -> 21.17 | **1546** / 1767 | 1.56 / 1.78 | 77 s |
| 3 | Poodle (250 kN vac, 350) | 8 | 15.61 -> 7.61 | - / **2466** | 1.63 vac | 110 s |
| 4 (lander) | Terrier (60 kN vac, 345) | 2 | 4.57 -> 2.57 | - / **1947** | 1.34 vac | 113 s |
Launcher SL1 + vac2 = 2,980 vs the LKO calibration 3,250 (Duna 1 with this launcher: 1,324 + 1,494 + 441 of Poodle =
3,259). Expect the Poodle to spend ~250-350 finishing the orbit: **Poodle 2,100-2,250 in LKO**, Terrier 1,947 untouched.
Pad check: `launch` must print stage 1 ~1434 SL / TWR 1.76, stage 2 ~1546 SL, Poodle ~2466 vac, Terrier ~1947 vac
(the lander holds the root, so KSP's readout follows it). Off by > 3 % -> `recover` on the pad and diagnose.
Checkpoints in LKO: Poodle < 1,900 -> the capture must come from the Terrier (still fine: 1,947 vs ~950 needed);
Poodle < 1,300 -> the ejection is short: revert/recover and redesign.

## Δv budget (m/s, after LKO)
| item | expect | source |
|---|---|---|
| ejection | node **1,090-1,130**; executed within +2 % (Poodle 250 kN on 15.6 t: ~65 s) | Lambert 1,101 at T 308 d (scan 302-326 d is flat: 1,101-1,106); Duna 1 burned 1,055 for a Lambert ~1,040 |
| plane change | **none** (Duna +4.8 Mm out of plane at arrival, SOI 47.9) | offline Kepler; the planner projects it |
| trims | 5-30 (~20 d before the SOI) + 5-20 inside the SOI (pe 100 km, inc-to 0, Ike avoidance) | Duna 1: 3.6 + 6.3; Eve 2/Moho 1 far-out lessons |
| capture 100 x 1,000 km | **353** (v_inf 717: v_pe 1,396 -> 1,043); 400 at v_inf 800, 520 at 1,000 | hyperbola from v_inf; refused by `transfer` above 946 (1.25x + 50) |
| circularize 100 km | **196** (1,043 -> 847) | |
| deorbit to pe 8 km | **54** (847 -> 793) | |
| landing | **450-650**, budget 700: full brake from 12 km AGL at ~900 m/s, 13-23 m/s2 | Duna 1 career: 656 for 8 t at net 4.5 m/s2 with no chutes; sandbox 738 -> 13 m/s with 3 Mk2-R semi-open. Lighter, 3x the acceleration, more drag -> less |
| **total** | ~1,750-1,950 | vs Poodle ~2,150 + Terrier 1,947 = ~4,100: **margin > 2,000** |
Sequence with masses: Poodle after LKO/ejection/trims **~950-1,100 left** -> it opens the capture (250 kN on ~9.5 t = 26
m/s2, ~13-15 s for 353: the Oberth window is minutes wide at e 1.7) and normally finishes it; auto-staging brings the
Terrier in if it runs dry. Circularize with whatever is left, then **`stage` in orbit** (TD-12 + Terrier share stage 4)
before the deorbit; `vessel` must show the Terrier alone with **>= 1,000 m/s** (need 54 + 700).

## Arrival geometry (offline, kspbot/kepler.py, stock elements) — it decides the links
- Kerbin at arrival: **24.3 Gm**, 57 deg from Duna's prograde, **34 deg from the Sun** (Kerbin is on the sunward side,
  ahead of Duna). Sun-Duna-Kerbin shrinks to 17 deg by +120 d: the Sun's disc (0.6 deg) never occults Kerbin.
- The probe arrives along -prograde (v_inf 178 deg from prograde: Duna catches it from behind, ship at aphelion), 91 deg
  from the Sun. Prograde hyperbola, pe 100 km (e 1.72): **periapsis 70 deg from the Kerbin direction** = Kerbin +20 deg
  above the horizon there, Sun +54 deg (daylight); the ray to Kerbin clears Duna over the whole +-90 deg of true anomaly
  -> **no blackout during the capture burn**. Retrograde pass: pe 178 deg from Kerbin, hidden -41..+39 deg = the whole
  burn. Rule: at the SOI entry `vessel` must read **inc < 90 (prograde)** and `signal` > 0; else `correct --inc-to 0`
  first (~15 h from the SOI edge to the pe at this v_inf: time enough).
- 100 km circular orbit: v 847, period 51.9 min. Duna turns **19.8 deg/h** (18.2 h day); the sub-Kerbin point moves with
  it, so any longitude comes under Kerbin within 18 h.
- Ike (3,200 km, SOI 1,050 km, tidally locked): unknown phase offline; `transfer`/`correct` penalise a path through
  its SOI (sandbox: 48 m/s to dodge it inside the SOI). Read the arrival patch list at the SOI entry: an Ike encounter
  before the pe -> `correct` at once.

## Link budget
| leg | antennas | range | need | strength |
|---|---|---|---|---|
| LKO, ejection | OKTO 5k (35 Mm to DSN 3) | | < 700 km | 1.0 |
| cruise, capture, orbit, entry, surface | 2 x RA-15 combined 25 G x DSN 250 G | 79 Gm | 24-33 Gm | ~0.85-0.9 (one dish: 61 Gm, ~0.75) |
Both dishes are fixed: no `_antennas` step, nothing to retract before the entry (land_atmo retracts nothing anyway).
Occlusion: none at the capture (above); in the 100 km orbit Kerbin is below the horizon for ~24 of 52 min (transmit waits
for it); at the landing site Kerbin is ~65 deg up at touchdown and sets ~3.3 h later.

## Landing plan
- Deorbit: `deorbit --pe 8000 --under Kerbin --sunward 0 --plan`, read, then without `--plan` (54 m/s, ~10 s Terrier;
  `_await_link` first). `release_ut` puts the *periapsis* under the Kerbin direction; the powered descent starts 12 km
  AGL = ~30 deg of true anomaly **before** the pe (r 333 km on the 100 x 8 km ellipse, e 0.123) and kills ~900 m/s in
  ~60 s (~5 deg of ground): **touchdown ~25 deg uprange of the periapsis**. Kerbin lies between prograde and the Sun
  (57 / 90 deg from prograde), so uprange of the sub-Kerbin point is *toward* the Sun: at the touchdown **Kerbin ~65 deg
  up, Sun ~80 deg up** (daylight), Kerbin sets ~3.3 h later (19.8 deg/h). A positive `--sunward` would move the pe
  uprange too (Kerbin lower); a negative one is silently made positive (`math.copysign` in `release_ut`, gap 2) — use 0.
  Read the printed "new periapsis lies +x deg" line and the predicted pe lat/lon. Stop rule: Kerbin elevation at the
  predicted touchdown < 30 deg or the site in darkness -> wait one Duna rotation (18 h) and replan.
- Terrain: the equatorial belt is Lowlands/Midlands (0-3 km) with Highlands to ~5 km; the 8 km pe is never reached (the
  brake starts at 12 km AGL wherever the ground is), so terrain only matters for slope at touchdown. Before the burn read
  `body.surface_height` along +-15 deg of the predicted track (scratch, kRPC) and avoid Craters/Highlands slopes.
- Entry: 907 m/s at 50 km, flight-path angle 7 deg, ~11 min from the burn to the atmosphere. `land --pe 8000` (land_atmo;
  the pe is already 8 km so it skips its own deorbit burn) warps to the atmosphere, holds surface retrograde (engine
  first: heavy tank ahead, light draggy top behind = passively stable; Duna 1 flew this twice at 925-930 m/s), arms the
  3 Mk2-R at 30 km (they open when safe, ~3 km), powered descent from 12 km AGL: full retrograde brake until the vertical
  speed meets the 3 m/s2 curve, legs out, touchdown 1.5 m/s. Expect **450-650 m/s**, ~10 min real time.
- Surface: `science --transmit --all` (landed goo 24, Jr 70, thermo 32, baro 48, seismic 72, gravioli 64 -> **~310 sci**
  at Duna's x8 and the transmit fractions; 165 Mits = 1,980 EC of 2,810) -> **contract complete on the first
  transmission**. Then `contracts -v`.

## Phases (expected numbers = the checkpoint's "Expect" line; compare after every phase)
Timeline: now UT ~41.2 M; launch just before the window 44,649,525 (`warp-sc 44600000` from the space center, ~160 d,
~5 real min); Eve 2 SOI 45.17 M (after the ejection); trim ~50.87 M (20 d out); Duna SOI ~51.29 M; arrival/capture
~51.30 M; Jool 1 SOI 52.79 M (after). Lab visits every ~1.08 M s meanwhile.

| phase | command | expect | Poodle / Terrier left | real time |
|---|---|---|---|---|
| pad | `build crafts/duna-2.json`, `launch "Duna 2"` | 1434 SL, TWR 1.76 / 1546 SL / 2466 vac / 1947 vac; 49 parts, 79.7 t; `signal` 1.0 | 2466 / 1947 | 2 min |
| ascent + circularize | `ascent --alt 80000 && circularize` (background, full output; poll the file every minute) | Mainsail out ~65 s, Skipper out ~2:30 at 45-55 km; apoapsis >= 45 km at 3:00; 79-80 x 80 km; transonic AoA < 3 deg | **2,100-2,250** / 1947 | 10 min |
| ejection | `transfer Duna --pe 100000 --plan` -> read -> `ksp node` | Lambert: T 302-326 d, v_inf dep ~1,020, **arrival v_inf 700-800**, Duna in plane (no mid-course line or < 30 m/s); node **1,090-1,130**; refused > 1.5x + 20. After the burn, BEFORE leaving the SOI: `vessel` shows a Duna encounter, pe within +-2,000 km of 100 | ~1,000-1,150 / 1947 | 8 min |
| cruise | `scene space_center`, `warp-sc <t_SOI - 20 d>`, `fly "Duna 2"` | link ~0.9 (RA-15 x2) | | 5 min |
| trim 20 d out | `correct Duna --pe 100000 --inc-to 0 --plan` -> `node` | 5-30 m/s; pe 100 +-50 km; prograde; do NOT chase sub-km errors here (Eve 2 lesson) | ~950-1,100 / 1947 | 3 min |
| Duna SOI | `soi`; then `correct Duna --pe 100000 --inc-to 0 --plan` -> `node` | v_inf **700-800**; pe 95-110 km (**< 60 km = raise first**, atmosphere 50 km); inc < 10 prograde; no Ike patch; 1-20 m/s; ~15 h to pe at 1000x | | 5 min |
| capture | `capture --apo 1000000` (background, full output) | **353-400 m/s**, Poodle 13-15 s centred on the pe (`burn_lead` mass-correct), link forecast: Kerbin +20 deg, no blackout -> 100 x 1,000 km, period 3.2 h | ~600-750 / 1947 | 5 min |
| science high/low | `science --transmit --all` at the ap (> 140 km = high) and at the pe (low) | high: grav 48, Jr 52, goo 18, thermo 24 (~140); low: grav 56, Jr 61 (+ goo/thermo leftovers) (~120); 750 EC per set | | |
| circularize | at the pe: `capture` (no --apo) | **196** -> 100 x 100 km, 51.9 min | 0-500 / 1947 | |
| drop the Poodle | `stage`, `vessel` | Terrier alone, **>= 1,000 m/s**, 4.57 t; the empty stage drifts (no debris concern at 100 km for weeks) | - / 1947 | |
| deorbit | `deorbit --pe 8000 --under Kerbin --sunward 0 --plan`, read, then burn | **54 m/s**, burn UT within one orbit; pe lat ~0, lon under Kerbin; touchdown ~25 deg uprange: Kerbin ~65 deg up, daylight | - / ~1,890 | 15 min (52-min orbit at 4-50x) |
| entry + landing | `land --pe 8000` (background, full output) | 907 m/s at 50 km, chutes armed at 30 km, powered descent from 12 km AGL at ~900 m/s, **450-650 m/s**, touchdown 1.5 m/s, upright; no `damage`/`attitude` events | - / **~1,200-1,400** | 12 min |
| surface science | `science --transmit --all`, `contracts -v` | ~310 sci, EC 2,810 -> ~830 -> recharges at 3.2 EC/s; **contract +132,825** | | 5 min |
Expected science ~570 (landed 310, low ~120, high ~140; Duna 1 already took some goo/thermo caps) + the contract.

## Code gaps (nothing here blocks the flight; 1-2 are worth doing before the landing)
1. **`land_atmo` runs no entry science** (`reentry --science` has `_entry_science` but no powered descent). Flying high/low
   sets at Duna are ~100 sci: add `--science` to `land` (call `_entry_science` on situation changes inside land_atmo's
   loops, as `reentry` does). Optional.
2. **Predicted periapsis ground point and terrain**: `deorbit --plan` prints the burn only. Print the pe lat/lon in the
   rotating frame at the pe UT, the Kerbin/Sun elevations there and `surface_height` along +-15 deg of the track; refuse
   when Kerbin is < 20 deg up (the Moho 1 site search did this in a scratch; it belongs in `deorbit`/`land`). Also
   `release_ut` drops the sign of `sunward` (`math.copysign(radians(sunward), plane_angle)`): an anti-sunward offset is
   impossible today; not needed for this flight (use `--sunward 0`).
3. Mk2-R `minAirPressureToOpen` is 0.04 atm (opens ~3 km ASL on Duna); the builder has no tweakables. kRPC
   `Module.set_field_float("minAirPressureToOpen", 0.01)` on the pad would open them at ~10 km (drag from 10 km at ~500
   m/s: Mk2-R semi-deployed drag is small, the gain is < 50 m/s). Not needed; note only.
4. Link forecast for captures (Moho plan gap 3a) is still not in code; not needed here (no blackout on the prograde pass),
   but the SOI-entry check (inc < 90, signal > 0) is manual.
5. `transfer` scans T on a 2 % grid and refines: fine here (flat cost 302-326 d). The arrival-v_inf refusal is 946.

## Risks and stop rules
- **Pad numbers off** (1434 SL / 1.76, 1546 SL, 2466 vac, 1947 vac): `recover`, fix the spec.
- **Ascent**: first flight of a 4.5 m probe stack on the Duna 1 launcher; AoA through Mach 1 > 5 deg or an `attitude`
  event -> revert to launch, add 4 x Tail Fin on t1b (Eve 2 #48 fix). Skipper TWR 1.56: no t_apo issue expected
  (apoapsis >= 45 km at 3:00; below -> revert).
- **Ejection**: node 1,090-1,130; > 1,300 or arrival v_inf > 900 in the Lambert line -> do not burn, diagnose the
  window geometry. Burn ending > 50 m/s short -> `correct Duna --pe 100000 --plan` inside the SOI at once (Oberth).
  Always read the Duna encounter before leaving Kerbin's SOI (Moho 1 #47 miss).
- **Arrival**: pe after the in-SOI trim 95-110 km; < 60 km with < 30 min to pe -> raise it; retrograde pass -> flip
  with `--inc-to 0` (it has 15 h). Ike patch before the pe -> `correct`.
- **Capture**: 353-400 expected, ~15 s; a burn that stops with the craft still hyperbolic -> `capture` again at once
  (it burns past the pe); any bound orbit is a win. Budget for a late start: +100 m/s.
- **Deorbit / landing**: Terrier < 1,000 after the Poodle drop -> still land (need ~750) but skip the low/high science
  transmits' EC drain first; touchdown `damage` events -> `log`; the landed transmit needs EC >= 2,000 (charge first,
  3.2 EC/s in daylight; the transmit code waits per experiment).
- **Link**: strength 0.85 at 24 Gm on two fixed dishes; nothing deploys. If `signal` is 0 at the SOI entry (Kerbin
  behind Duna is impossible there: 47.9 Mm out) -> tooling, `vessel`/`scene` and retry, do not warp to the pe without it.
