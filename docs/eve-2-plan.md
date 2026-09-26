# Eve 2 — plan (uncrewed Eve satellite contract + Eve surface probe, Gilly if the Δv is left)

Spec: `crafts/eve-2.json` (built OK 2026-09-26: 72 parts, **136.55 t**, 104,968 funds, 7 stages, no warnings; pad limit
140 t / 36 m — the stack is ~35.5 m: Ike Station 1's launcher + 0.95 m of Skipper tank + 0.8 m of payload, so no
Jumbo-64 anywhere). Window Kerbin -> Eve **UT 41,166,705** (`ksp window Eve`: +263 d from UT 35.47 M, flight ~171 d).

Two vessels in one launch: the **carrier** (root OKTO; Poodle + X200-32 stays with it = the contract satellite) and, on top,
the **lander** (inflatable shield + probe body + its own Terrier deorbit stage), released *after* the contract is done.

## Goals -> numbers
| goal | what must be true | Δv (carrier, after LKO) |
|---|---|---|
| 1. contract "equatorial orbit of Eve" (302k) | new probe, antenna + power, Science Jr aboard, orbit inc 0 / ecc 0.05102 / sma 18,868,437 m (pe alt **17,206 km**, ap alt **19,131 km**, period 50.0 h) / argPe 330.23, within 5 %, 10 s | ejection ~1040 + mid-course 50-200 + capture ~180 + pe raise 444 + argPe/plane trims ≤ 100 |
| 2. Eve surface science, transmitted | lander enters from the contract orbit under Kerbin (direct RA-15 link), flying high/low + landed sets | lander's own Terrier: ~474 of 828 |
| 3. Gilly (optional) | only with ≥ 500 m/s left after the contract | ~200 transfer (12 deg fold) + 35 capture + 35 landing |

## Craft
| function | part | note |
|---|---|---|
| carrier control | OKTO (root) + Advanced Inline Stabilizer (15 kN·m) + Z-1k | Poodle gimbal 5 deg does the burns |
| carrier propulsion | RE-L10 Poodle (250 kN, Isp 90/350) + X200-32 (16 t) | **3,287 m/s vac** with everything on top; ~2,450 left after the lander goes |
| carrier comms | RA-15 relay (fixed dish, 15 G) + 2 x HG-55 (deployable, 15 G each, 6.7 EC/Mit) | HG-55 x2 + RA-15 combined 15 x 3^0.75 = 34 G -> **92 Gm** to DSN 3 (250 G); Kerbin at arrival 7.9-9.0 Gm |
| carrier power | 4 x OX-4L 1x6 (1.64 EC/s each at Kerbin, x1.9 at Eve = **12.5 EC/s**) + Z-1k + 4 x Z-400 + OKTO = **2,610 EC** | opened by `circularize` (`_antennas`) |
| carrier science | Science Jr (contract), goo x2, 2HOT, PresMat, GRAVMAX | Eve 1 already took Eve high/low-space goo/thermo/baro (caps): new here = gravioli high+low (~96) + Jr low space (~61) |
| lander shield | **Heat Shield (10 m) inflatable**, 1.5 t, maxTemp 3250 / skin 3500, no ablator | heat face on the deorbit decoupler (`childNode: top`), lander body in the shield's `mid` recess (CoM 0.3-0.5 m behind the drag centre) |
| lander body | Science Jr (in the recess), 2 x Z-1k, OKTO, Advanced Inline Stabilizer (15 kN·m), nose cone; radial: 4 x Z-400, 4 x OX-STAT-XL (2.8 EC/s each at Kerbin; static, no deployment), 2 x Mk2-R, RA-15, goo x3, 2HOT, PresMat, Double-C seismic, GRAVMAX | 2.94 t with the shield, **3,610 EC**; ballistic coefficient ~37 kg/m^2 (78.5 m^2) |
| lander deorbit | TD-12 / FL-T200 / Terrier / TD-12 under the shield | 4.60 t all up, **828 m/s**, TWR 1.33 (Kerbin); dropped before the shield is inflated |
| lander comms | RA-15 (15 G, fixed: works through the entry, 12 EC/Mit) | direct to DSN 3: range 61 Gm, strength ~0.94 at 9 Gm; to the carrier's RA-15: 5.5 Gm |
| launcher | Twin-Boar + S3-3600 + ADTP-2-3 (Ike Station 1's, 65 t of fuel); Skipper + X200-32 + X200-16 | AV-R8 x4 on the Twin-Boar (-2.5), AV-R8 x4 on the X200-16 (-0.6), AV-T1 x4 on the Poodle tank (-1.5); whole stack rigid + autostrut Root |

Part masses (t): stage 1 80.03 (Twin-Boar 42.5, S3-3600 20.25, ADTP 16.875, fins 0.4) · stage 2 30.56 (Skipper 3, X200-32 18,
X200-16 9, TD-25 0.16, fins 0.4) · stage 3 19.91 (Poodle 1.75, X200-32 18, TD-25 0.16) · bus 1.45 · lander 4.605 (body 1.44,
shield 1.5, deorbit stage 1.665) = 136.55 (builder: 136.553).

## Stages (part stats; Isp SL/vac) — compare with `launch`
| stage | engine | fuel (t) | m0 -> m1 (t) | dv SL / vac (m/s) | TWR SL / vac |
|---|---|---|---|---|---|
| 1 | Twin-Boar (1867/2000 kN, 280/300) | 32 + 18 + 15 = 65 | 136.55 -> 71.55 | **1775** / 1901 | **1.39** / 1.49 |
| 2 | Skipper (569/650 kN, 280/320) | 24 | 56.53 -> 32.53 | 1518 / **1734** | 1.03 / 1.17 |
| 3 (carrier) | Poodle (250 kN, 90/350) | 16 | 25.97 -> 9.97 | 845 / **3287** | 0.28 / 0.98 |
| 5 (lander) | Terrier (60 kN, 85/345) | 1.0 | 4.605 -> 3.605 | - / **828** | 1.33 |
Launcher SL1 + vac2 = 3509 vs our LKO calibration 3250-3350 (Ike Station 1: 3279 with 24 m/s to spare): expect the
**Poodle untouched (3,250-3,290)** and 150-250 m/s left in the Skipper. Poodle mass flow 72.8 kg/s: ejection ~94 s,
capture ~14 s, pe raise ~30 s.
Stages: 1 Twin-Boar · 2 TD-25 + Skipper · 3 TD-25 + Poodle · 4 TD-12 (lander release) · 5 Terrier · 6 TD-12 (drop the
deorbit stage) · 7 Mk2-R x2. The inflatable shield is a ModuleAnimateGeneric (**not stageable**): its "Inflate Heat Shield"
event must be triggered via kRPC (see gaps).

## Arrival geometry (offline, kspbot/kepler.py, stock elements) — it decides the links
- Hohmann: v_inf dep 779 / arr 845, 170.4 d; ejection from 80 km **1037 m/s**. Eve at the 171-d arrival is **+155 Mm** out of
  Kerbin's plane (SOI 85 Mm) -> a mid-course plane change is needed (Eve 1: 347 Mm cost 372 m/s -> here ~150-200 at 171 d);
  at 184 d it is only +49 Mm (inside the SOI: nearly free). `transfer` scans 0.6-1.4 x Hohmann and picks the cheapest total:
  expect it to choose **T ≈ 180-190 d, ejection 1030-1060, arrival v_inf 850-950, mid-course 20-200**.
- Kerbin seen from Eve at arrival: 7.9 Gm (171 d) to 9.0 Gm (184 d), **170-177 deg from Eve's prograde** (Kerbin trails Eve),
  91-99 deg from the sunward direction. The probe overtakes Eve (v_inf along prograde), so the hyperbola's periapsis lies
  20-24 deg from prograde on the passing side: **the capture periapsis is ~155 deg from Kerbin = the far side. At 120 km the
  link is blocked from ~6 deg before the pe to ~55 deg after it (the first ~3 min after the pe).** Hence the capture burn
  must END ≥ 25 s before the pe (node at pe - 45 s; costs ~1 km of pe height, nothing in Δv). Ike Station 1's Ike capture
  failed exactly this way.
- The ap of the capture orbit is on the Kerbin side (31 deg off): pe-raise and match-orbit burns have the link.
- The lander is deorbited from the contract orbit at a point of our choosing: the entry periapsis goes where **Kerbin is
  ~55-60 deg above the horizon (30-35 deg sunward of the sub-Kerbin longitude: daylight, dusk 2 h later)**. Kerbin stays up
  ~3.5 h after touchdown, long enough for every transmission (17 s for the landed set). The carrier is *not* a usable relay
  during the descent (it is 110-120 deg behind the site and the site rotates away at 8.8 deg/h; it rises ~18 h later).

## Link budget
| leg | antennas | range | need | strength |
|---|---|---|---|---|
| carrier -> DSN 3 | HG-55 x2 + RA-15 combined 34 G x 250 G | 92 Gm | ≤ 10.5 Gm (200 d) | > 0.95 |
| lander -> DSN 3 (entry, descent, surface) | RA-15 15 G x 250 G, fixed dish, no deployment | 61 Gm | 8-9 Gm | ~0.94 |
| lander -> carrier (backup, when the carrier is up) | RA-15 x RA-15 | 5.5 Gm | ≤ 40 Mm | 1.0 |
| LKO | OKTO internal 5k (16 Mm to DSN 3... 35 Mm) until `circularize` opens the HG-55s | | | |
Occlusion: capture pe (above), Eve's shadow of the lander site after Kerbin sets (18 h dark, then the carrier/Kerbin return).

## Power budget
| item | EC |
|---|---|
| carrier transmit, HG-55 6.67 EC/Mit: low-space set (goo 10, Jr 25, thermo 8, baro 12, grav 20 = 75 Mits) | 500 of 2,610; refill 12.5 EC/s |
| lander transmit, RA-15 12 EC/Mit (69 EC/s): flying high 30 Mits, flying low 30, landed 95 (+ seismic) | 360 + 360 + 1,140 = **1,860 of 3,610**, no sun needed |
| lander coast 9.4 h holding retrograde (OKTO 0.02 + wheel ≤ 0.5 EC/s) | < 1,500 worst case; OX-STAT-XL x4 give ~21 EC/s in sunlight at Eve (x1.9), ~4-6 on the surface in daylight |
Transmit each set at once (KSP stalls a transmission when EC runs out); the landed set only after the two flying sets are
in, in that order.

## Lander entry plan
- Deorbit from the contract orbit (r ≈ 18.9 Mm, v 658): retro **~474 m/s** -> **pe 65 km** (Terrier, 4.6 t: 36 s). Coast
  **9.4 h** (half of a 65 km x 18.9 Mm ellipse). Drop the deorbit stage, inflate the shield, arm the chutes (stage 7),
  hold retrograde, in that order, right after the burn (link there: yes).
- Entry: **4,456 m/s at 90 km**, flight-path angle **~9 deg** (pe 65 km; pe 40 km would be 14 deg / ~13 g). Ballistic
  coefficient 37 kg/m^2 -> peak deceleration **~8-9 g at ~65-70 km** where the air is still 5e-4 kg/m^3: heat flux about a
  Mun-return capsule's (shield limit 3250 K; nothing ablates). Subsonic by ~50 km; terminal speed ~130 m/s at 45 km,
  ~30 m/s at 20 km, 14 m/s at sea level even without chutes. Mk2-R x2 semi-deploy at 0.04 atm (~45 km, "when safe"),
  full at 1 km AGL -> touchdown **3-5 m/s on the inflated shield** (crash tolerance 9 m/s). Descent ~25 min real time.
- Science: `science --transmit` at flying high (< 90 km, > 22 km: after the peak heating, ~60 km), flying low (< 22 km),
  landed. Expected transmitted: flying high 78, flying low 78, landed ~310 (goo 24, Jr 70, thermo 32, baro 48, seismic 72,
  gravioli 64) = **~465 sci** (Eve landed x8, flying x6; goo 30 %, Jr 35 %, sensors 40-50 %).
- Stability: the shield's drag acts 0.3-0.5 m ahead of the CoM (destabilising like every front shield); held by the 15 kN·m
  wheel (needs the link) and the recessed CoM. No fins on the lander: at the nose of the launcher they would cut the
  ascent's fin margin. Stop rule: `attitude` events (AoA > 20 deg) after 80 km -> nothing can be done; log the flip for
  the next design (AV-R8 skirt behind the shield, CoM lower).

## Mission phases (expected numbers = the checkpoint's "Expect" line)
| phase | command | expect | carrier dv left | real time |
|---|---|---|---|---|
| ascent + circularize | `ascent --alt 80000`, `circularize` | 79-80 x 80 km; Poodle **3,250-3,290** untouched, Skipper 150-250 spare; HG-55s + panels open, signal 1.0 | 3287 | ~10 min |
| wait for the window | space center, `warp-sc 41166705` | 263 d | | ~5 min |
| ejection | `transfer Eve --pe 120000 --plan`, read, `ksp node` | **1030-1100** (Hohmann 1037, v_inf 779; refused above 1.5x+20); T 175-190 d; arrival v_inf 850-950; the planner prints the mid-course UT + m/s (20-200); Poodle burn ~94 s at TWR 0.98 -> ≤ 2 % steering loss | ~2200 | 8 min |
| mid-course | `correct Eve --pe 120000 --inc-to 0 --plan` at the printed UT (~90 deg before arrival) | 20-200 m/s (analytic estimate printed; Eve 1: 372 for 347 Mm); stop rule > 450 or the tuner walking off (gap l) | ~2050 | cruise 180 d at 100000x ~5 min |
| Eve SOI | `soi`; inside: `correct Eve --pe 120000 --inc-to 0 --plan` | v_inf **850-950**; pe 120 +/- 10 km (**< 100 km = raise first**, atmosphere 90 km); inc < 3 deg; 1-20 m/s | ~2040 | 2.5 days of SOI at 1000x |
| capture | `capture --apo 19131000` with the node **45 s before the pe** | v_pe 4536-4564 -> **161-189 m/s** (v_inf 800-950), 14 s burn, ends ≥ 25 s before the pe (link blackout 0..+55 deg); -> **120 x 19,131 km**, period 20.3 h. No link at the burn start = burn is already late: retry `capture` every 30 s once the link is back (~3 min after the pe; +30-60 m/s) | ~1850 | |
| low-space science | at the pe pass: `science --transmit --all` (the transmit waits for the link, up to 7 h) | gravioli 56 + Jr 61 (+ goo/thermo/baro leftovers ~0) ; 500 EC | | |
| pe raise | at the ap (10.1 h later): `periapsis --alt 17206000` | v_ap 181 -> 625: **444 m/s**, 30 s -> 17,206 x 19,131 km, period 50.0 h | ~1400 | |
| contract orbit | `match-orbit --inc 0 --lan 0 --argpe 330.23 --sma 18868437 --ecc 0.05102 --plan`, `node`, repeat | plane ≤ 11 m/s per deg of inc; argPe rotation ≤ 67 m/s (2 e v); trims: **20-120 in all**; `_approve` refuses > 1.5x + 20 and any reversal. Then `contracts -v`: all four boxes ticked, **+301,888 funds** | ~1300 | |
| high-space science | anywhere > 400 km: `science --transmit --all` | gravioli 40 | | |
| lander release | at the computed UT (entry pe 30-35 deg sunward of the sub-Kerbin longitude; see gaps): `stage` (TD-12), switch to "Eve 2 Probe", `stage` (Terrier), retro to pe 65 km | **~474 m/s** of 828; carrier untouched (`stage` from the carrier: it keeps the root) | 1300 | |
| lander coast | `stage` (drop the deorbit stage), inflate the shield (kRPC event), `stage` (chutes armed), SAS retrograde, `warp` | 9.4 h; EC ≥ 2,000 at entry | | 3 min |
| lander entry + landing | `reentry` (no engine needed; it warps to 90 km, holds retrograde, stages the mains < 4 km / 250 m/s); `science --transmit --all` from a second shell at flying high, flying low, landed | 4,456 m/s at 90 km, ~8-9 g at 65-70 km, chutes ~45 km, touchdown 3-5 m/s; 465 sci; 1,860 EC | | 25 min at 1x |
| carrier again | `scene space_center`, `fly "Eve 2"` | | 1300 | |
| Gilly (optional, only if ≥ 500 left) | `transfer Gilly --pe 15000 --plan` (expect a refusal on the 12 deg plane: then `match-orbit` to Gilly's plane first) | aim at Gilly's **apoapsis (48.8 Mm)**: 132 m/s prograde + 12 deg fold = **~200**, 2.5 d, arrival v_inf ~30 (at its pe it would be ~300); capture ~35, land ~35 on the Poodle bell at < 2 m/s (no legs; Gilly g 0.049); Gilly landed goo (the 2nd goo) + thermo/baro/grav ~100 sci, low/high space ~100 | ~1000 | |

## Code gaps (all found in kspbot/flight.py, kspbot/cli.py; none written yet)
1. **`do_science(transmit=True)` transmits only rerunnable experiments** (`if transmit and e.rerunnable`): goo and Science
   Jr data are kept "for recovery" — both craft here are never recovered (~150 sci lost per craft). Fix: `science --all`
   -> transmit every experiment with data; before each transmit check EC ≥ Mits x EC/Mit of the antenna (Jool plan's stall).
2. **Capture-burn timing vs the link**: `capture` centres the burn on the pe; at Eve the pe is in Kerbin's shadow from -6 to
   +55 deg. Fix: `capture --early S` (node at pe - S) and `_await_link`'s mid-burn timeout 120 s -> ≥ 600 s (occultation
   exit), plus the LOG 4p prediction of the link over the burn window (Kerbin direction vs the body's disc from the burn point).
3. **No lander release / vessel switch step**: after `stage` the carrier (root) stays active; the lander becomes "Eve 2 Probe"
   (KSP's name) and is reached only via `scene space_center` + `fly`. Fix: `ksp switch NAME` (kRPC `sc.active_vessel = v`
   works in flight; both are loaded within 2.5 km right after separation). Never leave the lander unloaded inside the
   atmosphere (KSP deletes unloaded vessels below ~0.01 atm).
4. **Deorbit at an arbitrary time**: `periapsis --alt` burns at the next apoapsis; `land` (atmosphere) burns "now" to pe 5 km
   and then warps straight to the atmosphere (no chance to drop the deorbit stage / inflate) and, once the Terrier is gone,
   `_deorbit_now` loops forever with no thrust (`while pe > pe_alt` at throttle 1). Fix: `deorbit --pe X [--at UT]` =
   `_deorbit_now` alone, refusing when `available_thrust == 0`; `land_atmo(pe_alt=...)` exposed as `land --pe`. The release
   UT itself (entry pe under Kerbin) needs a small helper: burn when the vessel's position is 180 deg from
   (Kerbin direction rotated 30 deg sunward) in Eve's non-rotating frame.
5. **Inflatable heat shield**: nothing triggers part events. Fix: `_inflate(v)`: for the part "InflatableHeatShield",
   `modules` -> "ModuleAnimateGeneric" -> `trigger_event("Inflate Heat Shield")`; refuse if the deorbit stage is still on
   (the cone opens around it).
6. **Entry phase for an engine-less probe**: `reentry` works (coast, retrograde, stage the mains < 4 km / 250 m/s, no engine
   needed, pre-armed chutes tolerated) but runs no science; `land_atmo` needs an engine. Fix: `reentry --science` running
   `do_science(transmit=True, all)` at each situation change (flying high -> low -> landed) with the link wait; keep
   the chute logic (Mk2-R 0.04 atm is ~45 km on Eve; the 4 km / 250 m/s main-chute rule is fine under the shield, ~15 m/s).
7. **Gilly transfer**: `transfer` to a moon assumes a near-circular moon orbit in our plane and refuses when the moon is
   > 0.8 SOI (100 km for Gilly) out of plane; Gilly is e 0.55 / inc 12 deg. Fix: match Gilly's plane first (`match-orbit`
   with Gilly's inc 12 / LAN 80 and our sma/ecc), seed the transfer at Gilly's apoapsis (v_inf 30 instead of 300), tune on
   closest approach (LOG 4c).
8. `correct` far out: the aim-point seed + tuner can walk off (LOG 4l): always `--plan`, compare with the printed analytic
   estimate, stop rule 1.5x.
9. `match_orbit` measures argPe in our orbit's LAN frame; for the contract (inc 0, LAN 0) check `contracts -v` after the
   burns; if the argPe box stays open, rotate the apsides by hand (≤ 67 m/s) — cost2 has the 0.2 deg-weight only for e ≥ 0.05
   (ours 0.051: on the edge).
10. `transmit` EC check is `ec > 120` only: a 95-Mit set at 24 EC/Mit (RA-2) would stall; with the RA-15 (12) the budget
   above holds, but item 1's EC check is the real fix.

## Risks and stop rules
- **Ascent**: a 2.5 m stowed drum + 1.25 m lander body at the nose of a 1.25 m bus (draggy top, like Minmus Lab 1) — fins on
  all three atmospheric stages, none on the lander. Stop: any `attitude` event before 45 km -> revert to launch, add AV-R8s
  to the Poodle tank / move the lander lower.
- **Pad limits**: 136.55 t of 140, ~35.5 m of 36. If `launch` refuses the height: X200-16 -> X200-8 in stage 2 (-0.95 m,
  -200 m/s launcher margin, still ≥ Ike's).
- **Ejection**: Poodle TWR 0.98, 94 s: `execute_node` steers at the remaining vector; expect ≤ 1100. Stop: `_approve` refusal
  or > 1300 -> stop and diagnose (do not chase with a second node from an elliptical orbit).
- **Mid-course plane change** up to ~200 m/s far out: burn error leaves pe/inc off (Jool 1, Ike Station 1): fix inside the
  SOI (2.5 days of lead). Stop: no encounter after the burn -> `correct` again from the coarse search, budget 100 m/s.
- **Capture blackout** (the big one): burn ends ≥ 25 s before the pe; if `execute_node` reports "no CommNet link" at the burn
  start the pe is already in the shadow: run `capture` again every 30 s (it burns "now" past the pe) until it fires; budget
  +60 m/s. If the probe is still hyperbolic 10 min after the pe: it escapes — no second chance for the contract; the lander
  cannot fly on its own (828 m/s, v_inf 900): mission lost, LOG it.
- **Lander flip / burn-through**: the shield's 3250 K and ~8 g are within stock experience for BC ~40 (this is what the
  10 m shield is for). Stop rules: AoA > 20 deg sustained after 80 km (nothing to do), `damage` events on the OKTO/goos
  (1200 K) -> next design puts them deeper in the recess.
- **Chutes**: pre-armed at release (stage 7) so a lost link cannot leave them closed; `reentry` stages/deploys them anyway.
- **Science bookkeeping**: transmit sets in order (flying high, low, landed) and check EC before each; goo/Jr need gap 1.
- **Gilly**: only with ≥ 500 m/s after the contract; stop after 3 tuner attempts or any node > 300 m/s; landing on the bell
  only at ≤ 2 m/s (Poodle crash tolerance 7).

## OPEN / not yet verified (2026-09-26, session cut short by a PC restart)
- Pad check done (2026-09-26, career pad, recovered for a full refund): `launch` printed **1776 SL / 1526 SL / 3321 vac**
  (plan 1775 / 1518 / 3287) and accepted the height (sandbox photo: 35.3 m). The lander's Terrier stage shows no Δv:
  KSP's calculator follows the root (carrier OKTO) side of the TD-12, so the lander is dropped from it; part stats give
  828 vac (4.605 -> 3.605 t, Isp 345). Not a design fault.
- Shield orientation seen on the sandbox pad photo (runs/craft-eve-2.png, docs/media/summary/crafts/eve-2.jpg): the
  stowed drum sits between the deorbit stage (below) and the lander body (above), as specified. The inflate event is untested.
- `transfer Eve --plan` at the window is the real source of the ejection / mid-course / arrival numbers; the 171-184 d
  figures are offline Kepler (stock elements).
- The capture blackout (-6..+55 deg) uses the 184-d Kerbin direction; recompute from the live positions inside the SOI
  (Kerbin vs the vessel's pe direction in Eve's non-rotating frame) before choosing the node lead.
- Eve science values (x8 landed, x6 flying) and the transmit fractions are stock numbers, not read from this save.
- Gaps 1-6 are unwritten code; the lander phase cannot fly as-is (goo/Jr never transmitted, `land` would loop without an
  engine, no inflate, no vessel switch).

## What the tooling lacks (summary for the flight)
Gaps 1-6 are needed before the lander phase (1, 2 before the capture); 7-10 are conveniences. Nothing new is needed for
the launch, the transfer or the contract orbit itself.
