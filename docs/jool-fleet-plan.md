# Jool fleet — plan (five uncrewed one-way landers: Laythe, Vall, Tylo, Bop, Pol)

Specs: `crafts/jool-vall.json`, `jool-pol.json`, `jool-bop.json` (Dres 1's stack, unchanged), `jool-tylo.json` (new),
`jool-laythe.json` (Eve 2's lander + launcher, new capture stage). None is built in the VAB yet (designed offline while
another flight was running: only `ksp parts` and read-only kRPC were used). Window Kerbin -> Jool **UT 54,245,654**.
Offline numbers: `uv run python tools/scratch/jool_fleet_plan.py` (parts `transfer window arrival meet stages capture land
entry`; `kspbot.kepler` + `flight._lambert`; body constants, Laythe's air and the terrain read from the game 2026-09-27;
kepler on the game's elements gave the game's Kerbin-moon distances to < 1 m at four UTs). Live, read-only aids for the
pilot: `tools/scratch/jool_phase.py` (where is the moon when we are at the Jool periapsis) and
`tools/scratch/jool_retarget.py` (the burn to the moon inside Jool's SOI, least burn + capture).

| craft | stack | parts | pad mass | cost | dv after LKO | need | margin |
|---|---|---|---|---|---|---|---|
| Vall 1 | Dres 1's (flown #51) | 50 | 93.20 t | 99,060 | 1,759 + 3,683 = **5,442** | 4,648 | 794 (**17 %**) |
| Pol 1 | Dres 1's | 50 | 93.20 t | 99,060 | **5,442** | 3,745 | 1,697 (**45 %**) |
| Bop 1 | Dres 1's | 50 | 93.20 t | 99,060 | **5,442** | 3,875 | 1,567 (**40 %**) |
| Tylo 1 | new: Mammoth / Rhino / Poodle + Jumbo-64 / two-stage lander | 52 | 240.43 t | 163,385 | 3,032 + 2,739 + 2,675 = **8,446** | 6,865 | 1,581 (**23 %**) |
| Laythe 1 | Eve 2's launcher + Poodle X200-32 + Terrier FL-T800 + Eve 2's lander | 56 | 139.78 t | 111,763 | 2,824 + 2,154 = **4,978** | 3,536 | 1,441 (**41 %**) |

Total ~572k funds. Tylo 1 (240 t, ~42 m) and Laythe 1 (~37 m tall) need the level-3 pad; the three Dres stacks fit level 2.

## The architecture stands; five numbers of the brief change
1. **Arrival v_inf is ~1,760 m/s at this window, not 1,680** (Lambert at UT 54,245,654, T 1,152 d; Jool 1 left at another
   window). With the approach's 2.9 deg declination to the moons' plane the relative speeds at the moons are
   **Laythe 1,693, Vall 1,483, Tylo 1,349, Bop 1,403, Pol 1,337** (brief: 1,634 / 1,430 / 1,296 / - / 1,180). Bop and Pol are
   met where the arrival geometry puts the tangent point: near their apoapsis side (r 149 / 206 Mm), not at their periapsis.
2. **A Tylo landing with `land` as it is costs ~3,300 m/s from a 30 km orbit, not 2,600** (simulated: the code kills the
   horizontal speed at the orbit height, 2,200, falls 20 km and brakes at `max_decel` 3 m/s2 under 7.85 m/s2 of gravity:
   every m/s of the fall costs 3.6). Hence a two-stage lander and a 240 t rocket. `max_decel` 4.5-6 saves 140-220;
   a descent that brakes along the path would save ~500 (code gap 2): the margin grows, the design does not wait for it.
3. **Laythe: capture first, then `deorbit --under Kerbin` and `reentry`** (Eve 2's flown sequence). The direct entry is
   survivable (3,162 m/s at 50 km; any periapsis under 45 km lands in one pass on the 10 m shield; 10-22 g; heat 0.7-1.3 x
   Eve 2's flown peak) but it is blind: the periapsis of every possible pass has Kerbin at **-6 deg or lower**, the landing
   point (5-10 deg before it) at -4..+1 deg, and the site then turns away from Kerbin. With Require Signal for Control
   that is an entry with no attitude hold, no staging and no science until Kerbin rises ~7 h later. Capture + deorbit
   costs 1,316 m/s, which the stack has (margin 41 %).
4. **The Mun stands on the escape path at the window**: ejections from UT 54,241,754 to 54,259,754 (-1.1 h .. +3.9 h) pass
   it within 2 SOI (closest 6 km). The next blocked slot is UT 54,379,154-54,397,154 (+37.1 .. +42.1 h). All five ejections
   belong between the two: **UT 54,260,000-54,379,000**.
5. **`correct <Moon>` from the hyperbolic approach is not flown code** (gap 1): its Lambert seed weighs the burn only, not
   the capture, `_lambert` raises on some hyperbolic arcs, and Bop is routed to a trim of mm/s. The scratch aids stand in.

## Decisions
- **Vall, Pol, Bop on Dres 1's stack, unchanged** (the spec files differ in name and description only): pad numbers known
  to the m/s, flown ascent (Poodle 1,759 in LKO). Vall is the tight one (17 %); Eeloo 1's stack would give it 39 %
  (`crafts/eeloo-1.json` renamed; 138.7 t) and is the fallback if the pilot wants more. For Pol and Bop the surplus
  (40-45 %) also pays for a missed arrival phase (worst case 433 / 325 m/s inside the SOI, below).
- **Tylo 1's lander has two stages.** B (Terrier + FL-T400, 3.66 t, Duna 2's lander shape) alone has the thrust for 4.25 t
  at Tylo TWR 1.8, so it cannot carry 3,300 m/s; a single Poodle stage for capture + landing weighs 26 t. Stage A
  (Poodle + X200-16) under B finishes the capture, circularizes and opens the landing's horizontal kill; it runs dry in the
  kill (or early in the braking) and `land`'s auto-staging drops it (TD-12 + Terrier share stage 5). A always runs dry in
  the landing (it holds at most 2,739 and the landing takes > 3,000), so B's legs never meet A on the ground. Tylo TWR
  2.2 (A + B, full), 2.5 at the landing's start, 2.1 -> 4.6 (B alone).
- **Tylo 1's antennas are two Communotron 88-88** (0.2 t, 168 G combined: 205 Gm) instead of an RA-100 (0.65 t): 0.45 t
  on the lander is ~7 t in LKO. They are deployable: `circularize` opens them, the airless `land` leaves antennas alone.
  **Never run `liftoff`, `reentry` or `land` inside an atmosphere on Tylo 1**: they retract antennas, and a probe at Jool
  with its dishes in has no link to open them again (Eve 2 lesson). No Science Jr on Tylo (0.2 t landed = 250 m/s).
- **Laythe 1 flies Eve 2's launcher** (Twin-Boar + S3-3600 + ADTP, Skipper, tail fins): the stowed shield drum at the nose
  of a 1.25 m stack flipped Eve 2 #48 at Mach 1 on the first try; #49 flew with the tail fins (AoA <= 1.4 deg). Same nose
  here. The lander is Eve 2's with an RA-100 for the RA-15 (61 Gm would not reach), an RTG, 4 Mk2-R instead of 2 (Laythe's
  air is 8x thinner than Eve's: 6.5 m/s on four, 9.1 on two) and the atmosphere instrument. The root is the lander's OKTO:
  no vessel split before the entry, so the stages fire in order (Eve 2's accident came from the separated lander's stage
  counter). **The shield's own decoupler has stage 7 (last) and is never staged; the chutes have stage 6 alone.**
- **Every craft carries fixed solar panels** although the RTG feeds it: `_transmit` skips an experiment that does not fit
  the battery "with no solar panels" instead of waiting for the RTG.
- **No relay, no carrier, no gravity assist**: as decided. Direct links only (RA-100 x DSN 3: 158 Gm; strength 0.44-0.72
  over Kerbin-Jool 54-85 Gm).

## The transfer (all five)
Lambert at the window, projected on Kerbin's plane like `transfer_planet` (`jool_fleet_plan.py transfer`):
| T (d) | eject from 80 km | plane term | arrival v_inf | Jool out of plane | arrival UT |
|---|---|---|---|---|---|
| 1,000 | 1,949 | 53 | 1,877 | -1,554 Mm | 75.85 M |
| 1,100 | 1,933 | 54 | 1,775 | -1,563 Mm | 78.01 M |
| **1,152 (planner's best)** | **1,932** | 54 | **1,761** | **-1,557 Mm** | **79.12 M** |
| 1,200 | 1,935 | 54 | 1,767 | -1,545 Mm | 80.17 M |
| 1,300 | 1,961 | 53 | 1,824 | -1,501 Mm | 82.33 M |
- Jool is 1,557 Mm out of our plane at arrival but its SOI is 2,456 Mm: the planner finds an encounter and shapes the pass
  from LKO (Jool 1: Lambert 1,965 -> tuned 1,954 with pe 250 km). Expect the node at **1,935-1,980**.
- The window is wide: -5 d .. +10 d costs < 15 m/s of ejection (-10 d: +40, +20 d: +57). A day of delay at the departure
  moves the planner's arrival by ~6 days (flat optimum): the fleet will arrive within ~1.5 days of each other unless the
  mid-course spreads it.
- Finite burn (node direction held, ignition `burn_lead` before the node): Dres stack 146 s, loss 15 m/s; Laythe 1 167 s,
  loss 24; **Tylo 1 295 s on Poodle T (4.8 m/s2), loss 70-80 m/s, asymptote 0.8-1.0 deg off, lowest point 74 km**.
- Mid-course, single 3D burn from the in-plane path (what is left when the ejection carries no plane change):
  | at dep + | UT | dv | Kerbin | note |
  |---|---|---|---|---|
  | 200 d | 58.57 M | 130 | 25 Gm | |
  | 300 d | 60.73 M | 119 | 48 Gm | |
  | 400 d | 62.89 M | 121 | 60 Gm | **Kerbin behind the Sun at UT 62,068,454 (dep + 362 d): no burn within 2 d** |
  | **500 d** | **65.05 M** | **129** | 54 Gm | **recommended: UT 63.3-65.5 M** |
  | 700 d | 69.37 M | 170 | 58 Gm | Eeloo 1 arrives 69.1-69.4 M |
  | 900 d | 73.69 M | 292 | 76 Gm | |
  | 1,000 d | 75.85 M | 478 | 60 Gm | the planner's own "90 deg before arrival" is dep + 1,027 d (76.42 M): too late |
  With the planner's tuned ejection the real figure is lower (Jool 1: 2.5 m/s); budget 140.
- **The arrival time is set in the same burn** (the moon must stand at the tangent point when we pass): ~0.5 m/s of
  prograde / retrograde per hour of arrival shift at dep + 300-500 d, added in quadrature to the plane burn:
  | shift | +-15 h (Vall P/2) | +-29 h (Tylo P/2) | +-59 h | +-125 h (Pol P/2) |
  |---|---|---|---|---|
  | extra at dep + 300 d | 0.3 | 1.0 | 3.3 | 13 |
  | extra at dep + 500 d | 0.6 | 1.6 | 5.0 | 18 |
  | extra at dep + 900 d | 3.4 | 7.7 | 20 | 65 |
  | alone at Jool's SOI edge (58 d before the pe), worst phase | Laythe 37, Vall 67 | Tylo 150 | Bop 325 | Pol 433 |
  | same, mean over the phases | 18 / 33 | 73 | 113 | 150 |
  So: timing far out is nearly free, inside the SOI it is ~5 m/s per hour. Later than 30 d before the pe it doubles, at
  10 d it is 250-950: **the moon's phase is settled at the SOI entry or not at all.**
- Solar conjunctions (Kerbin behind the Sun seen from Jool, ~1 day of blackout): UT 62,068,454, 72,105,254, 82,192,454.
  The arrival (79.0-79.6 M) is clear: Sun-Jool-Kerbin 11 deg, Kerbin 65 Gm. Finish the landings before ~UT 82.0 M.

## Arrival at Jool (`jool_fleet_plan.py arrival meet`)
| | Laythe | Vall | Tylo | Bop | Pol |
|---|---|---|---|---|---|
| `--pe` for Jool (altitude of the tangent point) | 21,180 km | 37,150 km | 62,500 km | 142,000 km | 199,300 km |
| aim radius b at Jool | 75 Mm | 99 Mm | 131 Mm | 200 Mm | 255 Mm |
| SOI edge to the periapsis | 57.8 d | 58.1 d | 58.5 d | 59.1 d | 59.5 d |
| moon's period | 14.7 h | 29.4 h | 58.9 h | 151.3 h | 250.5 h |
| slots (UT of our periapsis with the moon there), nominal path | 79,102,848 + k x 52,981 | 79,088,186 + k x 105,962 | 79,049,406 + k x 211,926 | 79,061,914 + k x 544,507 | 78,691,896 + k x 901,903 |
| relative speed at the moon | 1,693 | 1,483 | 1,349 | 1,403 | 1,337 |
| moon's SOI edge to its periapsis | 29 min | 25 min | 1.7 h | 14.5 min | 13 min |
| capture periapsis (final) / first aim | 80 / 150 km | 100 / 150 km | 50 / 150 km | 40 / 100 km | 25 / 100 km |
| capture to | 80 x 2,000 km: **760** | 100 x 1,000 km: **908** | 50 x 1,000 km: **756** | 40 x 100 km: **~1,240** | 25 x 100 km: **1,226** |
| then | circularize 80 km: 504 | pe 20 km 23 + circularize 215 | circularize 50 km 401, to 30 km 20 | circularize 30-40 km ~20 | circularize 15 km ~25 |
| capture burn (craft's engine at arrival) | 55 s Poodle + Terrier (96 s Terrier alone), pe -51 .. +46 s | 104 s, pe -55 .. +48 s | 67 s (T 662 m/s + A), pe -36 .. +31 s | 133 s, pe -73 .. +61 s | 132 s, pe -72 .. +60 s |
| finite-burn result (node at the pe) | 80 x 2,006-2,033 km | 100 x 1,011 km | 50 x 1,004 km | 30 x 109 km (flown at 30 km in the simulation) | 25 x 109 km |
| Kerbin at the capture periapsis, prograde pass | **-8 deg**, hidden from pe + 110 s | +22 deg, never hidden | **-4 deg**, hidden from pe + 80 s | +46 deg, never | +55 deg, never |
| retrograde pass | -56 deg, hidden pe -75 .. +290 s | hidden pe -10 .. +435 s | hidden pe -180 .. +210 s | hidden pe -20 .. +140 s | hidden pe -5 .. +75 s |
- The slots are for the nominal v_inf direction; the flown path has its own: **read them with `jool_phase.py`**.
- Prograde pass = passing outside the moon's orbit, periapsis over the moon's far side (130-170 deg from the sub-Jool
  point). It is the only pass with a link over the burn at Laythe and Tylo (burn ends 64 / 49 s before the blackout;
  `capture`'s forecast, which counts the moon and Jool, moves it if not). The arrival plane holds the relative velocity,
  which lies 3-13 deg off the moons' equators (Laythe 12.8, Vall 10.6, Tylo 8.7, Bop 3.1, Pol 2.9): `--inc-to 0` will
  print "out of reach, closest ~3-13": that is expected, it only picks the side.
- The far-out corrections leave the moon pass off by ~100 km (0.05 m/s x 58 d): the first aim is 100-150 km, the final
  periapsis is set 3 d and ~6 h before the moon (1 m/s moves the pass 65 / 22 km there). Inside the small moons' SOIs
  there is no time for a trim (13-29 min): `capture` is started right after `soi`.
- Line to Kerbin vs Jool at the capture: clear for all five (Kerbin-moon-Jool angle 117-143 deg).

## Links and power
| | value |
|---|---|
| Kerbin-Jool over the mission | 54-85 Gm (cruise), 65 Gm at arrival, 57-82 Gm over the following 200 d |
| RA-100 (Dres stacks, Laythe 1), 100 G x DSN 250 G | 158 Gm: strength 0.44-0.72 |
| 2 x 88-88 (Tylo 1), 168 G | 205 Gm: strength 0.64-0.81; one alone 158 Gm |
| HG-55 backup (Dres stacks) | adds ~6 % range with the RA-100 |
| Sun at Jool | 0.039 x Kerbin: OX-STAT-XL 0.11 EC/s, OX-STAT 0.014: not a source |
| RTG | 0.75 EC/s always; 2,810 EC (Dres stacks, Laythe 1), 2,010 EC (Tylo 1) |
| a landed set | Dres stacks ~210 Mit x 6 = 1,260 EC; Tylo 1 ~185 Mit x 10 (88-88) = 1,850 EC, largest single 60 Mit = 600 EC: `_transmit` charges between experiments (41 min for a Tylo set) |
**Tidal lock**: every moon turns once per orbit, so Kerbin (a fixed direction over days) moves west around it at 360 deg per
period: Laythe 24.5 deg/h, Vall 12.2, Tylo 6.1, Bop 2.4, Pol 1.4. An equatorial site has Kerbin above 20 deg for 39 % of
the period in one stretch: **Laythe 5.7 h, Vall 11.5 h, Tylo 23 h, Bop 59 h, Pol 98 h**, then the same again dark. The
far side (away from Jool; longitudes Laythe +90, Vall +52, Tylo 180, Bop ~-157, Pol ~+63, from the sub-Jool longitudes
read in the game) sees Kerbin while the moon is on Kerbin's side of Jool and never has Jool in the way; the Jool-facing
side sees Kerbin in the other half, with Jool hiding it for up to 63 / 78 / 99 / 135 / 160 min in the middle. At the
capture the sub-Kerbin point lies 117-143 deg from the sub-Jool point (27-53 deg from the centre of the far side): **the
far side is the side to land on in the first half period after the arrival** (Kerbin 27-53 deg up there at the capture).
`land` checks Kerbin's elevation and Jool's disc by itself (`_link_ok`, `_parent_clear`); `deorbit` checks the elevation
only (gap 6). East / west of these offsets was not checked against the game's handedness: read the sub-Kerbin longitude
there.

## Vall 1, Pol 1, Bop 1 (Dres 1's stack)
Craft and stage tables: `docs/dres-1-plan.md` (identical parts). Pad check: **1175 SL, TWR 1.51 / 1043 SL / 2742 vac /
3683 vac; 50 parts, 93.2 t**. LKO: Poodle **1,650-1,800** (flown 1,759), Terrier 3,683. Lander 9.045 t wet / 3.045 dry;
Terrier 6.6 -> 19.7 m/s2.
| item | Vall | Pol | Bop | source |
|---|---|---|---|---|
| ejection (Poodle, the Terrier finishes ~220) | 1,980 | 1,980 | 1,980 | node 1,935-1,980 + loss 15 |
| mid-course (plane, pe, timing) | 140 | 140 | 140 | 3D Lambert 119-129 + timing |
| trim 20 d before the SOI | 30 | 30 | 30 | Dres / Eeloo plans |
| moon targeting at the SOI entry | 70 | 120 | 120 | phase table; Pol / Bop assume the timing was set far out |
| trims 3 d and 6 h before the moon | 30 | 30 | 30 | |
| capture | 908 | 1,226 | 1,250 | hyperbola from v_rel |
| lower / circularize | 23 + 215 | 20 | 15 | |
| landing (`land`, simulated as coded) | **1,250** (1,187 from 20 km, site at 1 km) | **200** (197 from 15 km) | **310** (304 from 30 km, site at 5 km) | `jool_fleet_plan.py land`; ideal 857 / 145 / 225 |
| **total** | **4,648** | **3,745** | **3,875** | vs 5,442 |
Terrier left on the surface: Vall ~790, Pol ~1,700, Bop ~1,570. Landing rules (Terrier, after the low orbit): Vall >=
1,400, Pol >= 300, Bop >= 450, else the orbit mission is the mission.
- **Vall** (g 2.31, R 300 km, SOI 2,406 km, high space above 90 km, terrain to 7.7 km sampled / 7,990 `TERRAIN`; biomes
  Lowlands, Midlands, Highlands, Mountains, Poles, Northeast / Northwest / Southern Basin, Southern Valleys): 100 x
  1,000 km (period 3.0 h, all high), 20 km circular (v 805, 41.6 min, all low), Terrier TWR 4.8-8 at the landing.
- **Pol** (g 0.373, R 44 km, SOI 1,042 km, high above 22 km, terrain to 4.2 km; Lowlands, Midlands, Highlands, Poles):
  25 x 100 km (2.4 h, all high), 15 km circular (v 111, 56 min). The Terrier passes 50 g near the end: `land` caps the
  throttle at g + 2 by itself (flown on Gilly).
- **Bop** (g 0.589, R 65 km, SOI 1,221 km, high above 25 km, **terrain to 21.4 km sampled / 21,750, equator 4.6-19.9
  km**; Valley, Slopes, Ridges, Peaks, Poles): capture at **40 km**, 30-40 km circular (v 162, 61 min). **No low-space
  orbit at Bop**: under 25 km the ridge is in the way; the low set is skipped. Sites lie 5-15 km up.

## Tylo 1
| function | part | mass (t) | note |
|---|---|---|---|
| control | OKTO (root) + Small Inline Reaction Wheel | 0.15 | Poodle 5 deg / Terrier 4 deg gimbal on every burn |
| lander B | FL-T400 (2 t) + Terrier | 2.75 | **2,675 m/s** at 3.66 t; 16.4 -> 36.1 m/s2 (Tylo TWR 2.1 -> 4.6) |
| legs | 4 x LT-1 on the FL-T400 at -0.7 (Moho 1 / Duna 2 geometry) | 0.20 | ~1.8 t at touchdown, 14 kN on Tylo (Moho 1 stood with 9.5 kN) |
| comms | 2 x Communotron 88-88 on the FL-T400, 90 / 270, h 0.5 | 0.20 | deployable; 10 EC/Mit |
| power | RTG + 2 x OX-STAT + 2 x Z-1k + OKTO = 2,010 EC | 0.19 | |
| science | 2 goo, 2HOT, PresMat, GRAVMAX, Double-C, magnetometer boom | 0.17 | goo: low orbit + landed |
| braking stage A | Poodle + X200-16 (8 t), Rockomax adapter, TD-12 above | 10.89 | **2,739 m/s** at 14.55 t; 17.2 -> 38.2 m/s2 |
| transfer stage T | Poodle + Jumbo-64 (32 t), TD-25 above, 4 x AV-T1 | 38.06 | **3,217 m/s** at 52.6 t; 4.8 -> 12.1 m/s2 |
| launcher 2 | Rhino + S3-7200 (36 t), TD-25 above, 4 x AV-R8 | 50.06 | |
| launcher 1 | Mammoth + S3-14400 + S3-7200 (108 t), TD-37 above, 4 x AV-R8 + 4 x Tail Fin | 137.76 | |
Every stack part rigid + autostrut Root, radial parts plain. The 3.75 m launcher parts and the TD-25 on a 3.75 m tank
top are new to the builder: read the pad photo.

| stage | engine | fuel (t) | m0 -> m1 (t) | dv SL / vac | TWR SL / vac | burn |
|---|---|---|---|---|---|---|
| 1 | Mammoth (3746 / 4000 kN, 295 / 315) | 108 | 240.43 -> 132.43 | **1725** / 1842 | **1.59** / 1.70 | 83 s |
| 2 | Rhino (2000 kN vac, 205 / 340) | 36 | 102.67 -> 66.67 | 868 / **1440** | 1.20 / 1.99 | 60 s |
| 3 (T) | Poodle | 32 | 52.61 -> 20.61 | - / **3217** | 0.48 vac | 439 s |
| 4 (A) | Poodle | 8 | 14.55 -> 6.55 | - / **2739** | 1.75 vac | 110 s |
| 5 (B) | Terrier | 2 | 3.66 -> 1.66 | - / **2675** | 1.67 vac | 113 s |
Launcher SL1 + vac2 = 3,165 against an LKO cost of 3,200-3,390 in these units (flown stacks): Poodle T spends 50-250 on
the orbit -> **Poodle T 2,950-3,150 in LKO**. Checkpoints: T < 2,700 -> margin 18 %, go; T < 2,300 -> the ejection
eats into A: revert / recover.

| item | dv | on | left after (T / A / B) |
|---|---|---|---|
| ejection (node ~1,935, 295 s) | 2,020 | T | 1,012 / 2,739 / 2,675 |
| mid-course | 140 | T | 872 |
| trim 20 d before the SOI | 30 | T | 842 |
| moon targeting at the SOI entry | 150 | T | 692 |
| trims before Tylo | 30 | T | 662 |
| capture 50 x 1,000 km | 760 | T 662 + A 98 | - / 2,641 |
| circularize 50 km | 405 | A | 2,236 |
| 50 -> 30 km circular | 20 | A | 2,216 |
| landing (`land` as it is, `max_decel` 3, 30 km orbit, site at 2 km) | 3,310 | A 2,216 + B 1,094 | - / - / **~1,580** |
| **total** | **6,865** | | vs 8,446: **margin 1,581 (23 %)** |
Landing, simulated as coded (kill at the orbit height, warped fall, braking curve), A with 2,250 m/s + B:
| orbit | `max_decel` 3.0 | 4.5 | 6.0 | impulsive |
|---|---|---|---|---|
| 25 km | 3,192 | 3,069 | 3,000 | 2,210 |
| **30 km** | **3,310** | 3,170 | 3,092 | 2,219 |
| 40 km | 3,502 | 3,336 | 3,243 | 2,236 |
| 60 km | 3,791 | 3,583 | 3,466 | 2,268 |
The kill takes 87-125 s and 80-90 km of ground and ends 6-11 km below the orbit with 30-190 m/s of sink (the more of
it stage B flies, the deeper). With A down to
1,500 m/s at the start the total is 3,376 (3.0); with 800 it is 3,309 and B lands with 170 left: **go / no-go before
`land`: A + B >= 3,650 (A >= 975)**. `max_decel` **4.5** is the value for Tylo once the flag exists; **never above 6**:
the curve is sized on the stage that burns, and B holds (16.4 - 7.85) / 1.3 = 6.6 (at 12 the simulation hits the ground at
186 m/s after A drops; at 9 it hovers at 3 m until the tanks are empty: gap 2).
Tylo: g 7.85, R 600 km, SOI 10,857 km, high space above 250 km, terrain **11.75 km sampled on a 5 deg grid (`TERRAIN`
has 11,290: raise it)**, equator 0.2-7.4 km; 30 km circular: v 2,118, period 31 min, link on half of it. Biomes:
Lowlands, Midlands, Mara, Highlands, Minor Craters, Gagarin / Galileio / Grissom / Tycho Crater.

## Laythe 1
| function | part | mass (t) | note |
|---|---|---|---|
| entry vehicle | OKTO (root), Advanced Inline Stabilizer (15 kN.m), nose cone, 2 x Z-1k, Science Jr in the shield's recess | 0.63 | Eve 2's stack, same order |
| shield | Heat Shield (10 m), inflatable | 1.50 | own stage 7 (never staged); `inflate` after the capture stage is gone |
| comms | RA-100 (fixed) on the upper Z-1k at 270 | 0.65 | the link through the entry |
| power | RTG (90), 2 x Z-400 (50 / 130), 2 x OX-STAT-XL: 2,810 EC | 0.20 | on the side away from the dish |
| chutes | 4 x Mk2-R on the OKTO, stage 6 alone | 0.40 | 6.5 m/s at sea level (shield alone 39, two chutes 9.1) |
| science | 3 goo (45 / 90 / 135), 2HOT, PresMat, atmospheric spectro-variometer, Double-C, GRAVMAX | 0.17 | |
| capture stage | Terrier + FL-T800 (4 t), TD-12 above (stage 5), TD-12 below (stage 4, with the Terrier) | 5.04 | **2,154 m/s** at 8.50 t; 7.1 -> 13.3 m/s2 |
| transfer stage | Poodle + X200-32 (16 t), Rockomax adapter, 4 x AV-T1 | 20.04 | **2,824 m/s** at 28.5 t |
| launcher | Eve 2's: Skipper + X200-32 + X200-16; Twin-Boar + S3-3600 + ADTP-2-3; AV-R8 x4 each, Tail Fin x4 | 111.25 | flown #49 |
Entry vehicle 3.455 t; the dish (0.65 t, ~1 m off the axis) against RTG, goo, Z-400 on the other side leaves the CoM
~12 cm off the axis (Eve 2: ~9 cm, flown at AoA <= 0.5 deg). On the pad measure it (parts' positions x masses in the
vessel frame); more than 15 cm -> move the goo / add a Z-1k opposite the dish.

| stage | engine | fuel (t) | m0 -> m1 (t) | dv SL / vac | TWR SL / vac | burn |
|---|---|---|---|---|---|---|
| 1 | Twin-Boar (1867 / 2000 kN, 280 / 300) | 65 | 139.78 -> 74.78 | **1718** / 1840 | **1.36** / 1.46 | 96 s |
| 2 | Skipper (569 / 650 kN, 280 / 320) | 24 | 59.09 -> 35.09 | **1431** / 1635 | 0.98 / 1.12 | 116 s |
| 3 | Poodle | 16 | 28.53 -> 12.53 | - / **2824** | 0.89 vac | 220 s |
| 4 | Terrier | 4 | 8.50 -> 4.50 | - / **2154** | 0.72 vac | 226 s |
Launcher SL1 + vac2 = 3,353 (Eve 2: 3,509 left the Poodle untouched): **Poodle 2,650-2,824 in LKO**.

| item | dv | on | left (Poodle / Terrier) |
|---|---|---|---|
| ejection | 1,980 | Poodle | 844 / 2,154 |
| mid-course, trims, moon targeting (40), trims | 270 | Poodle | 574 |
| capture 80 x 2,000 km | 765 | Poodle 574 + Terrier 191 | - / 1,963 |
| circularize 80 km | 505 | Terrier | 1,458 |
| deorbit to pe 25 km | 46 | Terrier | **1,412** |
| **total** | **3,536** | | vs 4,978: **margin 1,441 (41 %)** |
Entry from the 80 km orbit (drag area from Eve 2's recorder: 105-116 m2 hypersonic, 48 m2 below ~170 m/s, ~420 m2 per
open Mk2-R; Laythe's density from the game: 0.743 kg/m3 at sea level, 0.073 at 20 km, 0.0060 at 40 km):
| vacuum pe | burn | at 50 km | path angle | peak | heat vs Eve 2's peak | chutes | touchdown | from the edge |
|---|---|---|---|---|---|---|---|---|
| 40 km | 33 | 1,906 | -1.8 deg | 3.4 g at 45 km | 11 % | 4.0 km, 43 m/s | 6.5 m/s | 15 deg, 17 min |
| **25 km** | **46** | **1,893** | **-2.8 deg** | **3.8 g** | **13 %** | 4.0 km, 43 m/s | **6.5 m/s** | **12 deg**, 17 min |
| 0 km | 69 | 1,871 | -4.1 deg | 4.4 g | 13 % | | 6.5 m/s | 11 deg |
**The craft comes down ~76 deg before the periapsis that `deorbit` prints** (the vacuum periapsis lies 88 deg past the
edge of the air, the touchdown 12 deg). With `--under Kerbin --sunward 0` the periapsis is under Kerbin, so the touchdown
would have Kerbin only ~14 deg up. Put the periapsis **~60 deg downrange (east) of the sub-Kerbin point**: Kerbin 30 deg
up at the printed periapsis (the link check wants >= 20), ~74 deg up at the touchdown, 16 deg past the zenith; the
sub-Kerbin point moves west at 24.5 deg/h, so Kerbin sets ~4.3 h after the touchdown. How: `deorbit --pe 25000 --under
Kerbin --sunward 60 --plan` and `--sunward -60 --plan`; both print Kerbin ~30 deg up; take the one whose periapsis
longitude lies east of the `--sunward 0` one (or `--at UT`, 60 deg of orbit = 330 s later than the `--sunward 0` release).
A splashdown is the base case (equator: sea nearly everywhere, islands to 4.1 km); `surface_height` along the track 60-90
deg before the periapsis tells whether a Shores / Dunes island is in reach of a small shift.
Laythe: g 7.85, R 500 km, air to 50 km (flying high above 10 km), high space above 200 km, SOI 3,724 km; 80 km circular:
v 1,839, period 33 min; 80 x 2,000 km: 2.4 h.

## Launch order and the five ejections
1. Upgrade pad and VAB. Build all five, pad-check each (`launch` prints the stage numbers; off by > 3 % -> `recover`).
2. Launch in this order, each to 80 km (`ascent --alt 80000 && circularize`), leaving >= 600 s between two
   circularizations (they then sit >= 110 deg apart on the same orbit; vessels on rails do not collide):
   **Tylo 1** (unflown launcher: if it needs a redesign there is time), **Laythe 1** (the flip-prone nose), **Vall 1,
   Bop 1, Pol 1**. All five must be in orbit by **UT ~54,255,000**; a launch takes ~1 h of game time.
3. `scene space_center`, `warp-sc 54260000` (the Mun has left the path at 54,259,754).
4. For each craft, in the order **Pol 1, Bop 1, Tylo 1, Vall 1, Laythe 1** (the outer moons first: their slots are the
   rarest): `fly`, `transfer Jool --pe <PE> --plan`, read, `node`, then `vessel` and `jool_phase.py` before leaving
   Kerbin's SOI (8.4 h). `transfer` does not warp when the window is past; each ejection is 1-2 parking orbits (30-60 min
   of game time, ~10 real minutes). Five take ~5 h: done by **UT ~54,280,000**, far from the next Mun slot (54,379,154).
   A `transfer` that still reports "paths cross the Mun's SOI" shifts by itself (`_moon_wait`); two failures -> stop.
5. If a launch slips past UT 54,397,154 (the second Mun slot) nothing is lost: +10 d costs 15 m/s.

## Phases (expected numbers = the checkpoint's "Expect" line)
Common to all five; `<M>` the moon, `<PE>` the Jool altitude of the table above, `X` the craft.
| phase | command | expect | real time |
|---|---|---|---|
| pad | `build crafts/jool-<m>.json`, `launch "X"` | the craft's pad-check line; `signal` 1.0 | 2 min |
| ascent | `ascent --alt 80000 && circularize` (background, full output) | Dres stacks: as Dres 1 #51 (ap 47 km at 3:00, AoA <= 3). Laythe 1: as Eve 2 #49 (Twin-Boar out 96 s, AoA <= 1.4 deg through Mach 1). Tylo 1: Mammoth out 83 s at ~25 km, Rhino out ~2:25, apoapsis >= 45 km at 2:30, Poodle T finishes the orbit; 79-80 x 80 km | 12 min |
| ejection | `transfer Jool --pe <PE> --plan` -> `node` | "flight 1,140-1,170 d (Hohmann 1,120), departure v_inf ~2,710 -> ejection ~1,932, arrival v_inf ~1,760; Jool -1,560 Mm out of our plane (SOI 2,456), plane change ~54"; node **1,935-1,980**, Jool pe within 10 % of `<PE>`, arrival v_inf 1,650-1,800; burn 146 s (Dres stacks), 167 s (Laythe 1), 295 s (Tylo 1). After it: Sun ap 68-72 Gm (radius), Jool encounter | 8 min |
| phase check | `uv run python tools/scratch/jool_phase.py "X" <M>` | PROGRADE / RETROGRADE, periapsis radius vs the moon's orbit, "arrive a h EARLIER or b h LATER" | 1 min |
| mid-course | UT 63.3-65.5 M (not within 2 d of 62,068,454): timing by hand (below) or `--arrive` (gap 3), then `correct Jool --pe <PE> --inc-to 0 --plan` -> `node` | 5-140 m/s, mostly normal; Jool pe `<PE>` +- 5 %, **inc < 10 PROGRADE**; phase error after it < 3 h | 10 min |
| trim | 20 d before the SOI (UT ~77.4 M): `correct Jool --pe <PE> --inc-to 0 --plan` -> `node` | 1-30 m/s; do not chase the pe below +- 2,000 km here | 3 min |
| Jool SOI | `soi` (UT ~77.85 M) | v_inf 1,700-1,800, pe `<PE>` +- 5 %, inc < 10; link 0.6 | 3 min |
| moon targeting | at once: `jool_retarget.py "X" <M> --pe <final>`; `correct <M> --pe <first aim> --inc-to 0 --plan`, compare, `node` | burn: Laythe 3-50, Vall 3-105, Tylo 7-185, Bop / Pol 20-120 (timing set far out); the Lambert line's v_inf **within 5 % of the table's relative speed**; encounter with `<M>`, prograde | 10 min |
| trims | 3 d, then ~6 h before the moon: `correct <M> --pe <final> --inc-to 0 --plan` -> `node --thrust 0.2` | 1-10, then < 2 m/s; pe final +- 10 km; **Laythe >= 60 km, Tylo >= 25 km, Bop >= 30 km** before `soi` | 5 min each |
| moon SOI | `soi`, then at once `capture --apo <apo>` (background) | v_rel as the table; the capture line of the table; link forecast clear (Laythe / Tylo: burn ends >= 45 s before the blackout) | 6 min |
| science high | `science --transmit --all` near the apoapsis | one set, 810-1,850 EC | 5 min |
| low orbit | Vall: at the ap `periapsis --alt 20000`, at the pe `capture`; Tylo: `capture` at the pe, then `periapsis --alt 30000` + `capture`; Pol: `periapsis --alt 15000` + `capture`; Bop: `capture`; Laythe: `capture` | the "then" row of the table | 10 min |
| science low | `science --transmit --all` (not at Bop) | one set | 5 min |
| landing, airless | `vessel` (landing rule), `land --biome <flat biomes> --slope 4 --plan`, read the site (Kerbin >= 20 deg, Jool clear), then without `--plan` (background) | Vall 1,190-1,250; Pol ~200; Bop ~300; **Tylo 3,100-3,350: kill 2,200 in ~90 s (A drops in it or early in the braking: a `stage` event, parts 26 -> 22, then B alone at 16-20 m/s2), fall from ~20 km, touchdown 1.5 m/s** | 12 min |
| landing, Laythe | `deorbit --pe 25000 --under Kerbin --plan`, read the ground point, burn; `stage` (prints "TD-12": drops the capture stage; it must not name the shield); `inflate`; `reentry --science` (background) | 46 m/s; 1,893 m/s at 50 km, 3.8 g at 45 km, flying-high set above 10 km, chutes at 4 km / ~43 m/s, touchdown or splash 6-7 m/s ~17 min after the edge, 25 / 25 parts | 25 min at 1x-4x |
| surface science | `science --transmit --all`; `contracts -v` | one set; world firsts | 5-45 min |
**Timing by hand at the mid-course** (until gap 3 is closed): two trial nodes 120 s ahead, prograde +5 and -5 m/s, each
read with `jool_phase.py "X" <M> --node`: the arrival moves ~10 h per 5 m/s; interpolate to the wanted shift, burn that
node alone, then run `correct Jool` for plane and periapsis and read the phase again. Cost up to 15 m/s (Tylo), 60 (Pol).
**Arrival order**: give every craft a slot of its moon and keep two periapsis times >= 12 h apart (a capture plus the
first science and the orbit work is ~6 h of game time; a landing is another 2-6 h with the site wait). The slots of Pol
and Bop are fixed first, the inner three fit between them at no cost.

## Code gaps, in the order they bite
| # | gap | when | work |
|---|---|---|---|
| 1 | **`correct <Moon>` on the way in through Jool's SOI.** `_lambert_seed` scans +-5 % of the flight time around KSP's closest approach and a "Hohmann" time that means nothing on a hyperbola (369 d), and it minimises the burn alone: it can meet the moon off the tangent point (the capture pays: v_rel up to 300 m/s more). `_lambert` raises ValueError / ZeroDivisionError on part of the hyperbolic arcs (13,000 of the offline scan's tries). Bop (e 0.235, inc 15) is sent to `_moon_trim`, which moves mm/s, unless `--inc-to` is given; `transfer <Moon>` refuses an open orbit. Wanted: seed = scan of the arrival UT over +-1 moon period around our Jool periapsis, cost burn + capture (scratch `jool_retarget.py` / `jool_fleet_arrival.best_meeting`), exceptions caught, then the existing grid / tuner on KSP's patch with a dv term. Until then: the scratch's vector as a hand-built node, `correct` for the fine part | Jool SOI, UT ~77.85 M | ~0.5 day |
| 2 | **`land` on Tylo.** (a) `max_decel` and `safety` have no CLI flag (3.0 / 1.3 fixed): 140-220 m/s. (b) The braking law hovers for a_d > 2 x `final_speed`: feedforward a_d with gain 2 on the speed error balances where the curve's speed is a_d / 2, at h - 2 = a_d / 8 m; harmless at 3.0, fatal at 9 (simulated: all fuel burnt at 3 m). (c) a_d is sized on the burning stage: with a weaker next stage (Tylo 1's B) the curve cannot be held after the drop: size it on the weakest stage left. (d) `feet` is measured once, before a stage can drop. (e) The kill at the orbit height then a fall is the expensive way: braking along surface retrograde from the periapsis of a 30 x 12 km ellipse costs 2,710 in all, from 30 x 8 km 2,420-2,530 (simulated, site at 2 km; equatorial terrain reaches 7.4 km). The coded kill started at such a periapsis would do nearly as well, but its height loss (6-11 km) is not predicted anywhere: that guard is the work | Tylo landing, UT ~79.1 M | (a)-(d) ~0.5 day; (e) 1-2 days |
| 3 | **Arrival time in the far-out `correct`**: a cost term on the UT of the periapsis of the Jool patch (`--arrive UT`, or `--meet <Moon>`: the moon at the periapsis point, `jool_phase.py`'s angle). By hand it works (two trial nodes) | mid-course, UT 63.3-65.5 M | ~0.5 day |
| 4 | **The far-out search stays on the retrograde side** (Duna 2, LOG session 4). The planner's Jool passes came out retrograde on Jool 1 (110.7), Ike Station 1 (146.6), Duna 2 (169). Far out the flip is 2 b / lever: 10-30 m/s at dep + 500 d; inside Jool's SOI it is 120-430. Seeds across the centre (scale the best retrograde node until the pass flips) | mid-course | 2-3 h |
| 5 | `soi` / `_pe_floor` know terrain only: a Laythe pass at 30 km or a Jool pass at 100 km is not refused. Use max(terrain, atmosphere) + margin; `TERRAIN["Tylo"]` 11,290 -> 13,000 | Jool SOI | 15 min |
| 6 | `deorbit --under Kerbin` checks Kerbin's elevation at the periapsis, not Jool's disc (`land` does: `_parent_clear`), and an entry comes down ~76 deg before the printed periapsis on a draggy craft: print the touchdown estimate (periapsis angle minus `edge-to-ground` from a drag area) | Laythe entry | 2 h |
| 7 | `transfer` has no `--at` / `--T`: it warps to the window and then finds the Mun in the way; the pilot warps past the slot first. Nothing to write | ejection | - |
| 8 | `_transmit` prints solar charge times only (RTG ignored) and skips without panels: cosmetic, the specs carry panels | - | - |

## Risks and stop rules
- **Pad numbers off by > 3 %**: `recover`, fix the spec. Tylo 1 and Laythe 1 are new builds: look at the pad photo (`shot`)
  before the launch: Tylo 1's fins on the S3 tanks, the TD-25 on the 3.75 m tank; Laythe 1's drum under the lander, the
  dish on the side. Laythe 1: `stage` listing on the pad must show 7 stages with the shield alone in the last.
- **Tylo 1's ascent** (first Mammoth / Rhino flight, 42 m): `attitude` events or AoA > 5 deg before 30 km, apoapsis < 45
  km at 2:30 -> revert to launch. Sway (rate > 1 deg/s at 0.3 Hz) -> revert, autostrut check. Poodle T < 2,300 in LKO ->
  revert.
- **Laythe 1's ascent**: AoA > 3 deg through Mach 1 -> revert (the tail fins are already on; next: AV-R8 on the Poodle tank).
- **Ejection**: node > 2,100 or arrival v_inf > 1,900 in the Lambert line -> do not burn. Burn ending > 50 m/s short ->
  `correct Jool --pe <PE> --plan` inside Kerbin's SOI at once. Tylo 1: the 295 s burn dips to ~74 km: a periapsis under
  72 km in the node's orbit -> move the node half an orbit later and plan again.
- **Mid-course**: > 250 m/s -> stop (3 attempts: `--inc-to 0`, the retrograde flip by hand as on Duna 2, the scratch's 3D
  Lambert vector). After it the pass must be PROGRADE; a retrograde pass that reaches Jool's SOI costs the mission its
  landing (relative speed 5,400-8,100 m/s).
- **Moon targeting**: the Lambert line's v_inf > 1.05 x the table's relative speed, or burn + capture above the table's
  capture + the worst-case extra (37 / 67 / 150 / 325 / 433) -> do not burn; use `jool_retarget.py`. No encounter after two tries -> capture
  into Jool orbit is NOT available to the Dres stacks (a 250 km x moon-orbit capture costs 1,100-2,300 from these
  periapsis radii): the fallback is a flyby of the moon (science, world first) on the next pass of the phase, none if
  the craft leaves Jool's SOI. This phase is the mission: decide it at the SOI entry, not 10 days in.
- **Periapsis safety**: never `soi` into a moon with the pass under Laythe 60 km, Tylo 25, Vall 15, Bop 30, Pol 8 km.
- **Capture**: a burn that stops hyperbolic -> `capture` again at once. No link at the start -> the forecast should have
  moved it; `capture --early 40`. Any bound orbit is a win: the science from it is the base mission.
- **Tylo landing**: only with A + B >= 3,650 and a site with Kerbin >= 20 deg up; `land --plan` first. During the kill:
  radar altitude < 8 km with hs > 300 -> nothing can be done (the code holds surface retrograde); log it.
  Until gap 2 (b) is fixed fly `max_decel` <= 3 (the default).
- **Laythe entry**: `inflate` refused -> an engine is still aboard: `stage` once more only if it lists the TD-12, never the
  shield; `signal` 0 before the entry -> wait an orbit (33 min). Chutes: `reentry` stages them at 4 km; if the link was
  lost they stay closed: arm them by `stage` right after `inflate` (they open by pressure, 0.04 atm at ~21 km, 124 m/s).
- **88-88 on Tylo 1**: dishes retracted with no link = craft lost. `vessel` before every warp: signal > 0.
- **Workload**: five arrivals in ~5 days of game time. One craft at a time; the others wait on rails; never warp past
  another craft's periapsis UT (write the five periapsis UTs down at the SOI entries).

## Not verified
- None of the five was built (no `build` while the other flight ran): part names come from `ksp parts`, the node and
  surface-attach geometry of the 3.75 m parts, the fins on them and the TD-25 on a 3.75 m tank from nothing but the
  builder's rules. Costs are sums of the listed part prices (99,060 for the Dres stack; the Dres plan said ~105k).
- KSP's own dv readout for the Rhino stage at sea level (868) and the LKO cost of the Tylo launcher (3,200-3,390 assumed).
- LT-1 legs under 1.8 t on Tylo (14 kN); the landing legs' stance against Tylo's slopes (site filter 4 deg).
- The entry vehicle's CoM offset with the RA-100 and the dish's heating in the shield's wake (Eve 2 flew an RA-15 there).
- `land` and `capture` were simulated from their source, in 2D, without the body's rotation (Tylo 18 m/s), terrain
  relief or the control lag; Moho 1 flew 16 % over the simple sum, the simulation of the same code gives +32 % at Vall,
  +49 % at Tylo over the impulsive figure, so it is not optimistic, but it is not a flight.
- The arrival v_inf direction (and with it the slots, Bop's and Pol's meeting points and relative speeds, +-60 m/s
  over their orbits near the tangent point) depends on the flown transfer. Science multipliers were not read.
- East / west sign of the sub-Kerbin offsets; the moons' sub-Jool longitudes were read at one UT (Bop and Pol librate).
