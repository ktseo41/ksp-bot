# Career log (save: kspbot, Normal)

Newest entries at the bottom. One entry per mission: goal, craft, result, funds/science after, lessons.

## 2026-09-24 — early flights
- **Hopper 1** (pod+Flea+goo): hop to 16 km, crew report + goo in flight. Contracts "first launch", "gather science". Funds 25k → 110k (world-first milestones), sci 25.5.
- Bought Mission Control lvl2 (75k: maneuver nodes, 7 contracts). Researched basicRocketry, engineering101.
- **Sounding 2** (Hammer / Swivel+3×FL-T100): vertical to 208 km, space science (crew/goo/thermo). "Escape the atmosphere" done. Haul-TD-12 contract NOT met: passed 62–66 km too fast (>790 m/s); also TD-12 leaves with the lower stage. Funds 136k, sci 54.5.
- Researched generalRocketry, survivability, stability.
- **Orbiter 1** (Thumper / Swivel+3×FL-T200 / Reliant+2×FL-T200, 17.3 t): SYSTEM BUG — ascent phase 2 kept full thrust at −10° pitch from 33 km (apoapsis 75 km was 65 s ahead), reached 2.5 km/s at 40 km, science parts burned up, orbit 12×745 km. **Reverted to launch (allowed: tooling bug).** Fix: phase 2 only when t_apo < 35 s, pitch ≥ 0, stop at target+10 km.
- **Orbiter 1 (relaunch)**: LKO 71×140 km with a manual circularization (maneuver nodes turned out to need Tracking Station lvl 2). "Orbit Kerbin" done. Goo burned up on reentry (data lost). Drogues didn't get the pod under 110 m/s at 6–9 km → Mk16 test not met. Funds 212k.
- Bought Tracking Station lvl2 (nodes + patched conics) and Launch Pad lvl2 (140 t). Funds 13.7k.
- **Minmus Flyby 1** (3×Thumper cluster / Swivel+5×FL-T200 / Reliant+3×FL-T200 + heat shield, 29 parts, 11.6k): cluster staging clean. Ascent too steep again (no-gimbal SRBs can't pitch at high q) → circularization cost ~2 km/s; orbit 73×96 km with ~1.3 km/s left. Fix: pitch-over at 250 m; node burns steer to the remaining vector.
- **Minmus Flyby 1 (cont.)**: transfer 929 m/s → encounter; course correction 6.7 m/s to pe 20 km; science in space near Minmus (crew 20, goo 40, thermo 32); Kerbin return correction 94 m/s → pe 28.6 km; splashdown, Jeb safe. Goo exploded on reentry again (1215 K) despite heat shield — its data was lost. Mk1 pod has no power generation (EC 50): no transmitting. After recovery: funds 121.8k, sci 26.5 (check that recovered science landed), rep 67.

- Researched advRocketry (Terrier, FL-T400) and basicScience. Accepted "Science data from surface of Minmus" and "Science data from space around Kerbin". Game sounds set to 20% at every start (install.sh); install.sh now saves before killing KSP (a restart had lost contract acceptances).
- **Minmus Lander 1** (4×Thumper cluster / Swivel+3×FL-T400 / Terrier+2×FL-T400 lander, LT-05 legs at tank height −1.05 = 25 cm below the bell, 30 parts, 12.8k). Attempt 1: the rocket rotated east from t=1 s (rate up to 7°/s) and hit the sea at 1:02. **Jebediah Kerman killed** (revert was blocked by the tool permission, so the loss stands). Found a builder bug (symmetry copies got different surface radii, 1.285 vs 1.372 m), fixed it. Attempt 2 (Bill, symmetric cluster): same rotation, crashed. **Reverted to launch** (the user allows the game's revert). Real cause, measured on the pad: the Thumper thrust points about 0.3–0.4° off the pod axis (stack flex + lean), a 26 kN·m torque against a 5 kN·m pod wheel with no gimbal. Fix: `rigid` + `autostrut: Root` on the stack parts (new spec keys) → 11 kN·m, tilt direction east. Attempt 3: clean gravity turn, 79×81 km LKO with 3193 m/s left in the lander.

- **Minmus Lander 1 (attempt 3, cont.)**: transfer 936 m/s + 44 m/s correction, captured 15×15.5 km (2012 m/s left). Landing: touched down at about 15 m/s and tipped onto its side. TOOLING BUG in `land()`: the velocity loop had no feedforward, so the speed lagged the braking curve by a_d/Kp ≈ 7 m/s, and more at Minmus TWR 28 (reproduced offline). Surface science was collected while lying down (crew 25, goo 50, thermo 40). Then MY mistake: I tried to thrust off the ground while the reaction wheel had the craft spinning; it skidded into terrain and **Bill was killed**. Reverted to launch because the lander was already lost to the `land()` bug. Fix: constant-decel curve capped at 3 m/s² + feedforward, height measured from the feet (sim: 1.5 m/s touchdown for TWR 1.5–28). Lesson: never thrust while lying on the ground. A tipped lander stays put; plan a rescue instead.
- After the revert the autostrutted craft blew apart on the pad at t=0 (twice, even on a fresh VAB launch). Reverted, restarted KSP, and it was fine again. Several reverts in a row seem to corrupt KSP's physics state, so restart KSP after a revert before launching an autostrutted craft.

- **Minmus Lander 1 (final)** after a KSP restart: LKO 79×81 km (3203 m/s), transfer + 35 m/s correction, SOI, 4 m/s correction, captured 15×15.5 km (2031 m/s). Warped until over the Great Flats, then the fixed `land()` set it down upright with all 3 legs grounded (CoM 3.7 m above the feet). Surface science: crew 25, goo 50, thermo 40. Liftoff to a 14×16 km orbit (1511 m/s), return 179 m/s → Kerbin pe 31.9 km, reentry OK (goo/thermo at pod height +0.15 survived; only the jettisoned lander stage burned), splashdown, Bill safe. **First crewed Minmus landing and return.** "Science data from surface of Minmus" done. After recovery: funds 385.3k, sci 171.8, rep 90.

- Researched heavyRocketry + generalConstruction, upgraded the VAB to level 2 (225k).
- **Mun Lander 1** (3×Kickback / Swivel+4×FL-T400 / Terrier+3×FL-T400, 91 t): the pad torque was ~0, so the pod wheel (5 kN·m, MoI 5.8e6) couldn't have pitched it over. I added a full FL-T200 as ballast on the core's east side (26.5 kN·m). It pitched too fast (60° at 14 s), flipped at q 27 kPa and crashed. **Jebediah killed. DESIGN ERROR (mine), stands.** Lesson: don't fake a pitch-over with an offset torque; it grows as the SRBs burn down and can't be controlled. Get real authority (flightControl: inline reaction wheels, AV-R8 fins).
- **Sounding 3** (Sounding 2 + Science Jr under the pod, no drogues, no heat shield), vertical to 170 km for science to buy flightControl: on the way down the pod + Science Jr flipped nose-first at 7.8 km (960 m/s), the main chute staged at 2.5 km far too fast, and it crashed. **Bill killed. DESIGN ERROR (mine), stands.** Lesson: anything stacked under the pod changes its reentry aero. Keep a heat shield at the bottom and drogues on every capsule.
- Process change: new designs that change aero or control authority fly in the sandbox first; the career only flies proven designs.

- **Spawn breakups** (Minmus Lander 1 craft relaunched for a Mun orbit): "Structural failure on linkage between Thumper and Thumper" at t=0, repeatedly, even after a KSP restart. Crew killed on the pad (Jeb twice, Bob, Valentina), all **reverted** (the game offered it). Leftover debris was a red herring. Uncrewed probe-core pad tests: **autostrut on the surface-attached side boosters** (any mode) breaks them at spawn; rigid-only or none spawns fine. It had worked twice before by luck. `launch` now also tries to clear landed vessels near the pad.
- **Pad Lab** (pod + goo/thermo/baro/Science Jr sitting on the pad): 18 science from the LaunchPad biome at no risk. Researched flightControl (AV-R8, inline wheel = only 5 kN·m).
- **Mun Lander 2** (Mun Lander 1 without ballast; side Kickbacks rigid only; 4 AV-R8 at the core's base; 2 inline wheels + battery in the Swivel stage; 40 parts, 92 t): pad torque ≈ 0, control torque 15 kN·m. Textbook gravity turn (84° at 500 m, 50° at 9 km); the Kickbacks alone raised the apoapsis to 80 km. LKO 75×83 km with Swivel 474 + lander 3874 m/s.

- Mun Lander 2 landed softly (1.4 m/s) in the Mun Lowlands but **tipped over**: CoM 4.6 m above the feet, legs only 0.65 m out → tips at ~6°. **Reverted** (allowed). Wide lander, tested uncrewed on the pad (probe core + unmanned Mk1): FL-T200 core + 3 radial FL-T400 with 6 LT-05 legs (±50° on each radial tank): 1.74 m out, CoM 1.9 m high → tips at 33° with full tanks.
- **Mun Lander 3** (Mun Lander 2 lifter + the wide lander, 43 parts, 93 t, Bob): LKO 79×80 km. The user saw it wobble on the way up; data: AoA ±3°, heading 85–95°, rate up to 7.6°/s above 5.7 km (q ~40 kPa) and the recorder didn't flag it → recorder now logs roll/roll rate and alerts on spin and AoA oscillation; ascent autopilot time_to_peak 3→5 s. Transfer, pe 31 km, captured 31 km, **landed upright on the Mun** (Midlands, 6° tilt, all 6 legs down), science (crew 20, goo 40, thermo 32), liftoff to 20 km (1496 m/s left), return 274 m/s → pe 34 km, splashdown, Bob safe. **First crewed Mun landing and return.** After recovery: funds 342.8k, sci 148, rep 105.

- Research fuelSystems. Accepted "Conduct temperature surveys of Minmus" (77k adv / 143k): 3 sites X7MM-7 (2.2, -21.3), S53V1Q (35.4, 124.5), K-QXM (36.8, -90.1), thermometer "in spaceflight above ~3-4 km" within the lateral trigger range (decompiled: HIGH band = MaximumTriggerRange 15 km). New `survey` phase: predicts the ground track, warps to passes, runs the thermometer (UNTESTED yet).
- **Mun Lander 3 (Minmus survey flight, Jeb)**: the softer ascent autopilot works (heading steady at 90.0, AoA ≈ 0 at high q, no oscillation alerts). The LKO crew report is worth 0 (done before) and the pod has no transmitter. TOOLING BUG: `_encounter` accepted a Minmus encounter that came after a Mun flyby, so the craft ended up in high Mun orbit. Fixed (only the first SOI counts; `correct` refuses to burn without an encounter). **Reverted** to launch and recovered on the pad.

- **Mun Lander 3 (Minmus survey, 2nd try, Jeb)**: LKO 79×81 km (4109 m/s in the lander). The transfer burn (922 m/s, 49 s) drifted and the path grazed the Mun SOI (pe 1733 km at the Mun). A 20 m/s correction moved the Mun pass only ~135 km, so I let it fly by, and the flyby flung the orbit to an apoapsis of 102,000 km, Minmus closest approach 31,000 km. The small-step `correct` found nothing → TOOLING FIX: a coarse prograde×radial grid seed when there's no encounter nearby, plus a cost penalty for entering another body's SOI first. It found a 52 m/s correction to a Minmus encounter; new `correct --inc 45` tilted the arrival to 54° for the survey sites at lat 35–37°. Captured 20×20.4 km (173 m/s).
- `survey --dist 12000` (first real test): S53V1Q at 826 m lateral, K-QXM at 10.6 km, X7MM-7 at 7.6 km (missed it once at 36 km, the next pass worked). **Contract complete** (funds 420k → 606k). The scan is slow (one kRPC call per track point, minutes at 1x). kRPC's all_contracts kept showing it "active": `contracts` now drops anything in completed_contracts.
- Goo in low Minmus orbit (40). Landed in Minmus Lowlands (site picked by ground-track biome + terrain-slope sampling < 5°), upright at 6.5°, on the night side. Surface science: crew 25, thermo 40 (the crew report was blocked by the old worthless orbit report → `science` now resets data worth 0 first). Liftoff 15 km, return 242 m/s (Kerbin pe came out 290 km) + 14 m/s correction to 30.6 km, reentry, landed in the Grasslands, Jeb safe. After recovery: funds 609k, sci 178, rep 122.

- Researched landing (Mk16-XL, LT-1, 1.875 m shield) and electrics (OX-STAT, Z-200); Astronaut Complex → level 2 (EVA off Kerbin). Pad EVA in the career: EVA report 2.4 + surface sample 9 (surface sample worked at R&D 1, at least on Kerbin), recovered → sci 100.
- EVA built and tested in the sandbox: `ksp eva out|report|board|state|flag`. Mk1 hatch faces builder angle 90 (Mun Lander 3 had parts on all four sides: "All hatches are obstructed"). The kerbal hangs at the hatch after exiting, can do EVA report + surface sample there, and boards back legitimately. Flags need ground contact (not done).
- Duna window: phase now 99°, needed 44° → ~139 days from UT 1.79M (≈ UT 4.79M).

- **Mun Lander 5 (Minmus biome tour, Jeb)**: LKO, transfer + `correct --inc 60` → captured 20×20.5 km at 66.7°. My mistake: `science` in orbit also used up the goo on low-value data (9). `land --biome ...` picked Greater Flats but touched down 2.5 km off, in Lowlands (11° tilt, fine). **`eva out` → the lander broke apart at the instant Jeb left** ("Structural failure on linkage" heat shield↔pod, tanks↔core, Terrier↔core) and Jeb was flung off at 1400 m/s, escaping Minmus. The lander was sitting still before (rate ~1°/s). The same EVA worked on the pad in the sandbox and career. **Reverted to launch** (offered by the game; physics blow-up triggered by our new EVA call) and recovered on the pad. To do: reproduce on a landed lander in the sandbox; suspect rigid/autostrut joints being rebuilt when the crew changes.

- **EVA investigation (sandbox)**: the fling is not autostrut. Mun Lander 6 (no rigid/autostrut on lander parts; ascent clean) still flung the kerbal at ~1400 m/s on the Minmus surface (twice), with no structural failure; in orbit and on the pad (legs retracted) EVA is always clean ("Ladder (Idle)", in the hatch trigger, boards fine). On the pad with **legs deployed** the kerbal went Ragdoll and fell → a deployed LT-05 leg near the hatch side knocks the kerbal; in Minmus gravity the collision flings it. First fix: radial tanks at 30/150/270 (hatch gap at 90) and legs at ±90 on each tank (legs at 0/60/120/...): on the pad with legs deployed the kerbal no longer ragdolls but slides to "Ladder (End Reached)", outside the hatch trigger (can't board). Not verified on Minmus yet (sandbox ran out of crew; `hire` now creates kerbals in sandbox). Conclusion for now: **no EVA on landed craft in the career** until a sandbox test shows Ladder (Idle) + airlock on the ground. EVA in orbit is fine.

- **Mun Lander 6 (Minmus survey + biome tour, Jeb)**: LKO 79×80, transfer + `correct --inc 45` → captured 20×20.6 km at 63°. My mistake again: `science --transmit` in LKO ran the goo (2.3) → `science` now keeps single-use experiments unless ≥ 8 science is left in the subject. Survey contract 1 (crew reports at 4 sites, `survey --kind observational`) done → funds 899k. Survey contract 2 accepted mid-flight: KSP only registers its waypoints on a scene load, so no pass counted (and I misread `contracts | head` as 3 done). New `ksp fly NAME` (KspBot FlyVessel from the space center) re-enters the vessel with waypoints registered → done, funds 1.28M. `scene space_center` from flight did not save and rolled the game back ~53 min to the last autosave (nothing gained/lost; `scene` now saves first). Survey was slow (1x during kRPC-per-point track scans and whole passes) → `_track` (Kepler in Python, calibrated) + warp to the closest pass: 25 s per site.
- Biome hops: Midlands (1.8° tilt; the Communotron was never extended, so transmits had silently failed before → `science --transmit` extends antennas and warps until KSC is above the horizon), Greater Flats, then a "Poles" site that turned out to be Lowlands: **kRPC 0.6 `biome_at` passes degrees to KSP's GetAtt, which wants radians** → every biome-targeted landing so far looked up the wrong spot; `_biome()` passes radians (verified against Vessel.biome). Landing burn now starts 10 s earlier (touchdowns were 1.4–1.7 km past the site; after the fix 160 m) and the free fall is warped. Lesser Flats. Science transmitted per biome: crew 25 + thermo 20.

- Highlands landing, liftoff, return 178 m/s → Kerbin pe 34 km, reentry, splashdown, Jeb safe. Biomes surfaced this flight: Midlands, Greater Flats, Lesser Flats, Highlands (+ Lowlands again). After recovery: funds 1.30M, sci 255.5, rep 181. Minmus surface biomes still missing: Slopes, Flats, Poles.
- Upgraded R&D → level 2 (451k); researched heavierRocketry (Mainsail, Twin-Boar, Thoroughbred) and spaceExploration (ladder, storage containers). Funds 849k, sci 5.5.
- KspBot `OpenFacility` / `UiList` / `UiPress` (open a building's screen, press a UI tab) for the user's screenshots: Mission Control, R&D tech tree, R&D archives → Minmus. Inside a facility kRPC's scene switch is refused; close with the ExitButton (`UiPress('.../ExitButton')`).

- Windows became unusably slow (user). Measured: 2 GB of 15.3 GB RAM free, commit 29/33 GB, nonpaged pool 1.64 GB. After a reboot: commit 14.6, pool 0.82; with KSP 20.8 / 0.92; one more KSP restart changed nothing (22.9→22.7, 1.00→1.01), so the restart-leak idea is unconfirmed. install.sh now runs KSP at 30 fps, shadows 1, BelowNormal priority; `ksp load-save` switches saves without a restart.
- **Mun Lander 7 EVA test (sandbox)**: legs moved away from the hatch (one LT-05 per tank, outward). Pad: no ragdoll, "Ladder (End Reached)" 0.5 m below the trigger → `eva board` now accepts a hatch within 2 m. **Minmus ground: Ladder (Idle) in the airlock, EVA report + surface sample + board all work.** Landed EVA is cleared for the career with the ML7 layout. (Sandbox launch hung when no crew was available: preflight "NoControlSources"; `hire` first.)

- Summary images for the user's post (docs/media/summary, 5 images + Korean post.md); all crafts photographed on the sandbox pad (daylight, UI hidden, camera heading 270); real crew portraits from the in-flight portrait (UI_SCALE_CREW = 2). The record now lives as data in docs/record + tools/summary (see its README).
- **Duna 1 redesigned** (crafts/duna-1.json): ML7 lander + 3 Mk2-R, Poodle/X200-16 transfer stage, Skipper/X200-32 second stage, Mainsail/2×X200-32 first stage, 42 parts, 84.8 t. Sandbox ascent: LKO 79×80 km with Poodle 1196 + lander 3893 m/s. KSP time warp is capped ~100x in LKO → waiting for a window in orbit is impractical: warp at the space center with `ksp warp-sc UT` (new KspBot WarpTo), launch shortly before the window.
- KSP restarts: memory measured around 3 restarts, nonpaged pool 1.04→1.05, 1.08→1.08 GB: no per-restart leak seen.

## 2026-09-25 — Duna rehearsal (sandbox)
- `ksp fly "Duna 1"` focused an asteroid: FlyVessel indexed flightState.protoVessels, but StartAndFocusVessel wants the index into FlightGlobals.Vessels (what the tracking station's Fly button uses). Fixed in KspBot.
- **Window bug**: `window` extrapolated today's phase angle linearly ~200 days ahead against a circular-orbit Hohmann angle; with Duna near periapsis that was off by ~5° (≈13 days), and `transfer` then warped toward the NEXT window (896 days). Rewritten: the window is the departure t where the target, at arrival t+T, sits 180° from the origin's position at t, using the real orbits (bisection over one synodic period; it may report a window a few days in the past). It moved the sandbox window by ~8 days.
- Transfer: ejection 1063 m/s (Poodle), encounter pe 60 km found by the tuner; after the burn the pass had moved to 12,222 km → `transfer` now corrects right after an interplanetary ejection too (3 m/s). After the SOI change the pe read 112 km and the path ran **through Ike's SOI** before Duna periapsis; avoiding Ike inside Duna's SOI took 48 m/s → node cost now penalises a moon SOI in the arrival patch (also during the heliocentric correction, where it's cheap).
- Capture 581 m/s planned: the Poodle ran dry mid-burn, the Terrier stage lit and its plume blew up the dropped stage's reaction wheel (harmless debris), orbit came out 31×96 km. `land_atmo` now deorbits whenever the periapsis is above pe_alt+5 km (a 31 km grazing pe would skip).
- **Duna landing (land_atmo, first test)**: deorbit to pe 5 km, entry at 930 m/s, 3 Mk2-R armed at 30 km, powered descent from 12 km at 738 m/s, chutes held it at 13 m/s, touchdown 1.4 m/s in Lowlands. Fixed before the test: land_atmo armed ALL chutes, including the capsule's Mk16/drogues needed at Kerbin; now only chutes that get decoupled later (the lander's). KSP cut the Mk2-Rs on landing by itself; `liftoff` also cuts deployed chutes.
- Duna surface: science OK; **EVA OK with the ML7 layout** (Ladder (Idle) in the airlock, EVA report + surface sample + board).
- **Duna liftoff (first test)**: ascent() to 60 km, circularize → 59×60 km. Used ~1450 m/s; ~1090 left.
- Duna→Kerbin window 615 days later (warped in the tracking station). Ejection 741 m/s (Hohmann estimate 616) + 2 m/s correction → Kerbin pe 29 km, ~350 m/s left.

- Chute deploy in `reentry` threw an RPC error after the mains staged (a part gone); now tolerated. Rehearsal complete: **Duna landing + return works end to end in the sandbox.**
- Career: Duna window recomputed with the new method: **UT 5,108,742** (the old estimate said ~4.79M). 130 days to spare → a Minmus science trip first.

## 2026-09-25 — career
- **Mun Lander 7 (Minmus Poles/Flats/Slopes, Jeb)**, accepted "Science data from space around Minmus". LKO 79×81, transfer 928 + 30 m/s correction, `correct --inc 85` 0.5 m/s → captured 18×19 km at 89°. `science` spent the goo in low orbit for 9.2 (threshold for single-use experiments raised 8 → 15). Landed at Poles (77.1 N), crew report 25 + thermo 40 transmitted. **`eva out` flung Jeb at ~400 m/s onto a Minmus escape path and knocked the empty lander over** (it was upright, pitch 87.6°, during the science just before). Same ML7 layout had worked in the sandbox on Minmus and Duna → intermittent KSP physics blow-up at EVA spawn (KspBot calls the stock spawnEVA). **Reverted to launch** (offered by the game). Rule from now on: no EVA on other bodies' surfaces in the career. Recovered on the pad, restarted KSP (revert + autostrut lesson), relaunched.

- **Mun Lander 7 relaunch (Jeb)**: same path, captured 21×21 km at 90.6°. Orbital EVA report (32, "space just above Minmus' Midlands") → contract done on recovery. Landed at **Poles** (80.4 N; crew 25 + thermo 40 transmitted, goo 50 kept), hop to **Flats** (a ~4×8 km patch at lat −20..−28, lon 170–174: with 8 orbits of search the polar track never crossed it; new `land --orbits N`, found it within 60), hop to **Slopes** (1.8° site). Every Minmus surface biome is now visited. Liftoff, return 175 m/s → pe 33.6 km, landed on Kerbin (1.8 km up in the hills, chutes fine), Jeb safe. After recovery: funds 913k, sci 246.8, rep 188.
- My tooling mistake: my `until ! pgrep -f "ksp land"` wait loops matched their own shell command line and never ended (only their 10-min timeout did). Wait on the background task's notification instead.

- Researched miniaturization (Clamp-O-Tron Jr etc.), sci 156.8.
- **Mun Lander 7 (Mun biomes, Bob)**: LKO, transfer 854 + 10, captured 15×15.4 km at 5.7°. Orbit science (crew 15, goo 30, thermo 24) + orbital EVA report 24. Landed in **Lowlands** (−2.4, 142.1; upright 6°), crew 20 + thermo 32 transmitted. Hop to **Farside Crater** (2.52, −60.11), crew 20 + thermo 32 → sci 274. **My planning mistake**: the hop used 1434 m/s (the old airless liftoff went ~vertical to the apoapsis and then circularized: ~850 m/s instead of ~600), leaving **891 m/s — about the theoretical minimum (~890) for surface → Kerbin return**. Bob is sitting landed; the revert window is gone (I left the flight scene to test in the sandbox).
- New airless `liftoff`: fly low, climb with orbital speed (alt_want = target·(v/v_circ)², never below terrain on the next 45 s of track + 600 m), stop when pe ≥ 0.85·target; `execute_node` now stops after 3 s with no thrust (it used to loop forever when fuel ran out). UNTESTED — sandbox test was in progress (ML7 teleported to Mun orbit with `sandbox-orbit`, landing in a crater).

## 2026-09-25 — sandbox: airless liftoff tests (for Bob)
- The earlier sandbox ML7 loss: after the `sandbox-orbit` teleports the craft came off rails spinning at ~875 deg/s (teleport/kraken, test artifact), `land` burned the whole lander stage while tumbling, then `auto_stage` saw no thrust and staged the Kerbin-return decoupler → bare pod hit the Mun at 557 m/s. Fix: `auto_stage` never stages away the last engine. New test craft `crafts/sandbox-ml7-lander.json` (ML7 lander + capsule only, Terrier active before the teleport); teleports were clean from then on.
- Liftoff tests from Farside Crater (target 9 km), dv from mass (Isp 345):
  1. untested version from last session: kept climbing at 80 m/s with pitch clamped ≥ 0, periapsis criterion → **escaped the Mun, 1289 m/s**.
  2. "burn low until ap ≥ target and the coast clears the terrain": orbital at 2.6 km with ~700 m/s (100 m/s wasted on a vertical start), then ap jumped 3 → 220 km in 2 s before the check passed.
  3. + climb with speed: 765 m/s, pitch oscillating +72/−30 (gain too high), cut at low speed after a rim climb (circ 194).
  4. lower gain + "cut only if circularization < 8% v_circ": the altitude target rose faster than the craft could climb → burned past escape.
  5. + vertical speed capped by the ballistic apex at the target (apoapsis held at the target, periapsis rises): **704 m/s** (7.9 t, TWR 4.6), orbit 11×11 km.
  6. same code at Bob's mass (3.8 t, fuel burned off in orbit first): **~695 m/s** (657 + 38 circularization), orbit 17×17. The crater rim forces a steep climb at ~200 m/s; theory would be ~570.
- `return --pe 30000` from a 9 km Mun orbit: **275 m/s** (measured by mass).
- **Bob can't fly home directly**: ~695 + 275 ≈ 970 > 891. He stays landed (fuel kept) until a rescue: Bob lifts to Mun orbit (~200 m/s left), a tanker with a Klaw grabs his lander and transfers fuel (kRPC ResourceTransfer), then he flies home. Needs rendezvous + Klaw/actuators tech; the station needs rendezvous/docking anyway.

- Career: researched advConstruction + actuators (Klaw: GrapplingDevice, smallClaw), sci 274 → 24. CommNet requireSignalForControl = False in this save → an unmanned OKTO tanker keeps control behind the Mun.

- Rules (user): **no more sandbox rehearsals** — new code debuts in the career; quickload exception for tooling bugs kept; protect kerbals first (new code on uncrewed craft first) and **revert a clearly lost flight at once** instead of waiting for the crash.
- **Mun Tanker 1** (OKTO + Klaw + 2×FL-T400 + Terrier on the ML7 launcher, 19.3k): the lighter upper stage let the Kickbacks alone reach ap 80 km, so `ascent` ended with the spent SRBs still attached; `circularize` computed a 0 s burn time (no thrust), started the 1077 m/s burn at the apoapsis instead of around it → 51×129 km, and `transfer` then planned from that orbit while the tanker sank to 48 km. **Reverted to launch** (tooling bug, game-offered). Fixes: burns stage a spent stage before timing; circularize burns prograde at once if the periapsis is left in the atmosphere; transfer refuses from an atmospheric orbit. Relaunch: 85×90 km.

- Mun Tanker 1 relaunch: LKO 85×90, transfer 875 m/s. At the transfer burn start (still on the Swivel stage) the craft spun up to ~60 deg/s within 7 s; after staging, `execute_node` kept "burning" at 2% throttle while tumbling and never ended (killed after ~8 min). SAS stopped the spin in 6 s. Fixes: `execute_node` damps a tumble (> 11 deg/s) with SAS and re-points; a burn that runs > 3× its time + 60 s stops. Cause of the spin-up itself not found yet (watch the next Swivel-stage burns). Dropped-stage debris: the Swivel stage's reaction wheel overheated in the Terrier plume (harmless). Correction 4.7 m/s, captured **30×31 km around the Mun, inclination 179° (retrograde)**, LF 304 / Ox 371 (~4.4 km/s), funds 886k.

- **Bob liftoff** (Mun Lander 7, Farside Crater, `liftoff --alt 15000 --heading 270`, quicksave first as tooling insurance): orbit **34.7×35.3 km, inc 177.5°** (tanker at 179.0°, relative 2.0°). Used ~750 m/s, ~140 left (LF 11.2 / Ox 13.7). Overshoot again (sandbox: 9 → 17 km): the climb held vs at the 150 m/s cap until ~4 km, because `vs_apex` uses today's g_eff, which falls as the horizontal speed grows, so the real apex ends far above the target; the cut then accepts any apoapsis ≥ target if the circularization is cheap. Fix later (cap the cut apoapsis, predict the apex with the orbit).

- **Rendezvous (first career use)**, tanker as chaser: plane change 1.98° = 18.3 m/s; phasing wait 56,312 s (20.7 orbits, the orbits were only 4.5 km apart); intercept 9.1 m/s (closest 14 m) + an immediate correction of 24.6 m/s (large for a 50 m pass; the closest-approach solver between near-identical orbits is noisy, watch it); killed relative velocity at 115 m (0.45 m/s), `approach` held **27.9 m, 0.27 m/s**. Tanker used ~70 m/s in total.
- **Grab**: Klaw armed, drifted in; "grabbed" after ~1 min, 33 parts, no damage. (`grab` then crashed on the stale vessel object: fixed.) **`transfer-fuel`** moved LF 292.5 / Ox 357.5 into Bob's tanks, `release`, Bob separated at 0.6 m/s.
- **Bob's return burn spun the lander at ~10–17 deg/s** and `execute_node` looped on "damping with SAS" (killed by hand, pe at the Mun stayed 32 km). Two causes: (1) `transfer_fuel` filled Bob's radial FL-T400s one after another (180 / 30 / 3 LF) → centre of mass 0.36 m off the thrust axis, more torque than the Mk1 pod's wheel + Terrier gimbal can hold; (2) **Bob is a scientist: no SAS** (Mk1 pod has none), so `_damp` did nothing. Fixes: `balance_fuel` (even fill levels, also run after every transfer; `ksp balance-fuel`), `_damp` holds the attitude with the autopilot (roll included) when SAS can't be enabled. The tanker's earlier Swivel-stage spin-up is a different case (OKTO has SAS, tanks symmetric) and stays open.
- Return from 32×76 km: 255 m/s, clean, Kerbin pe 30 km → `soi` pe 33 km → `reentry`: splashed down at Shores, **Bob home** (UT 2,925,382). Photos: docs/media/2026-09-25_bob-rescue_*.png. After recovery: funds 965k (886k before; likely world-first rendezvous + recovery), sci 30.4, rep 202.5.
- New contract on offer: "Rescue Halden from orbit of Kerbin" (24k + 58k), a cheap next use of the rendezvous code (orbital EVA only).

- **Minmus Science 1 (Jeb)**, craft `crafts/minmus-science-1.json`: ML7 + 2× SC-9001 Science Jr stacked under the lander decoupler, 2 more goo, barometer + Experiment Storage Unit on the pod's side (30.3k, 52 parts). Accepted "Conduct observational surveys of Minmus" (94k + 166k). Ascent left the Swivel with 104 m/s → circularize 98 m/s, LKO 79×80; dropped the 7 m/s Swivel stage by hand before the transfer. Transfer 992 + 2 m/s, `correct --inc 80` 2.6 m/s → arrival inc 99°, capture 334 m/s → 14.1×14.6 km, lander 2379 m/s.
- Orbit science: **both Science Jrs ran in low Minmus orbit** (materials 100 each; the second copy is nearly worthless). `--min-single 110` didn't hold them (the subject had more than 110 left) and `do_science` ran every copy of an experiment. Fix: one experiment per subject per run. Surface materials (125 each) lost; lesson for the next science craft: only land-worthy single-use parts, or run orbit science with a threshold above the orbit value.
- **Experiment Storage Unit**: the "Collect All" *event* is inactive in flight; the *action* (`set_action("Collect All")`) works. The unit refuses a second copy of a subject, which stays in its experiment → `_collect` resets rerunnable leftovers so they don't block the next biome. `do_science` now collects after every run unless transmitting.
- **Observational survey with altitude caps** ("below 5,100 m near ..."): the 14 km orbit passes didn't count. Decompiled `SurveyWaypointParameter`: checked on `OnExperimentDeployed`; band LOW if `vessel.altitude` (ASL) ≤ the cap; lateral distance (at the vessel's altitude) < TriggerRange(LOW) = (500 + 15000)/2 = **7,750 m** (HIGH: 15 km, no gravity scaling). New `_dip` in `survey`: half an orbit before the pass lower the periapsis to 1000..300 m under the cap (lowest that keeps the arc 800 m above the terrain), a quarter orbit before turn the plane so the periapsis passes over the site, raise the periapsis back at the next apoapsis. Palmer's Jest (6.5 km off, 4.4 km) and then Zone 6-4Z (735 m), KH9ZD (43 m) completed; ~10–25 m/s per site.
- **kRPC shows contract parameters as incomplete when they are done** (again): the reliable sign is the waypoint disappearing from `waypoint_manager` (the game removes it on completion). Research for this (user asked): decompiled code + a grok web search (deepseek no longer used, user).
- Surveys done (all 4 waypoints gone) → funds 1.31M, sci 105, rep 229. Landed in **Lowlands** (43.1, −63.2, upright): goo 50, baro 60 and materials 100 (the second Science Jr's orbit duplicate had been reset as worthless, so it ran again on the ground), collected into the storage unit.
- **Quickload (tooling bug)**: the first liftoff from Lowlands (target 10 km) escaped Minmus at 667 m/s (~800 m/s burned). My overshoot fix (thrust ≤ horizon once the apoapsis reaches the target) left only the periapsis criterion, which can't pass while the craft is below the target; the cheap-circularization cut was checked once a second, and at TWR 18 (Minmus) one second is 7% of orbital speed. Fixes: acceleration capped at max(3 g, v_circ/30), the cut test runs every step (terrain coast check ≤ 1/s), stop at once if the apoapsis passes 1.5× target or the path is hyperbolic. Quickloaded to the pre-liftoff save (landed, science collected), relaunched: **14.7×15.1 km for ~230 m/s**.
- Liftoffs with the fixed code: ~230 m/s each, orbits 14.7×15.1 km (the 1.5× apoapsis stop). Landed **Greater Flats** (baro 60, thermo 13, materials 100, goo 50), **Midlands** (same, 223; daylight photo docs/media/2026-09-25_minmus-science-1_midlands.png), **Great Flats** (baro 60, materials 100). Unexpected: after "Collect All" the Science Jr works again (4 surface materials studies from 2 bays).
- Return 177 m/s → Kerbin pe 33.7 km, `reentry --main-alt 9000 --main-speed 110` for the Mk16 test contract: the pod only fell below 110 m/s at 3 km, not met again. Splashed down, **Jeb safe**. Recovery: **sci 105 → 670 (+565)**, funds 1.308M (surveys + recovery). `recover` printed before the rewards landed; now it waits for them.
- Researched precisionEngineering (HG-5 relay, DTS-M1, hex core), advFuelSystems, **nuclearPropulsion (LV-N Nerv)**. Sci 50.

## 2026-09-25 — Rescue 1, lost contracts, Polar Relay 1
- Accepted Rescue Beafrod (Kerbin orbit), Rescue Haidorf (Minmus orbit), Minmus synchronous satellite; advances +173k.
- Decompiled: a rescue's "Save X" (AcquireCrew) completes on onPartCouple (the Klaw grab); kRPC `TransferCrew` moves the kerbal (new `ksp transfer-crew`, untested). Specific-orbit check (VesselUtilities.VesselAtOrbit): PeA/ApA within the deviation %, inclination within dev % of 90 deg, LAN and argPe (e > 0.05) within dev % of 360 deg.
- `launch` with no names seats the default crew (Jeb sat in the empty rescue pod; recovered): `--crew none` launches uncrewed.
- **Rescue 1** (crafts/rescue-1.json, uncrewed OKTO service module, empty Mk1 pod with a Klaw on the nose, radial Mk2-R + drogues; Tanker launcher): LKO 77.8x83.5. KSP restart + PC reboot mid-mission (user; memory: commit 32.7 -> 14.6 GB, nonpaged pool 1.78 -> 0.88 GB after the reboot; 21.4 GB / KSP 3.9 GB with KSP running). **CommNet Require Signal for Control ON** (user; new KspBot `SetRequireSignal`). Rendezvous: intercept 1.7 m/s, closest 9 m, held 8.6 m.
- **Grab hit the target**: the 12 m stack (Swivel stage still on) swung at 4-16 deg/s for 90 s at 8.6 m (grab turns to each correction and back to the target) and its nose hit the cabin; grabbed anyway, no damage. **Beafrod's cabin was empty and all three accepted contracts were gone**: kRPC `LaunchVessel` goes to flight without saving, so the flight scene came up with the contracts back as "offered" (autosave backups show it), the rescue kerbal gone, advances kept. Fixes: `accept` and `launch` save persistent first; `intercept` aims the pass at the hold distance (25 m); `grab` won't turn freely inside (Klaw-to-CoM arm + 8 m) and refuses to start closer. Released the cabin.
- CommNet consequence: the OKTO's internal antenna (5k) reaches sqrt(5e3 x 50e9) = 15.8 Mm with TS 2; Minmus is 47 Mm away -> uncrewed Minmus craft need an antenna (HG-5).
- New `reentry --keep-until ALT` for uncrewed pods whose probe core is in the service module: engine first, drogues armed/mains deployed directly, service module decoupled under chutes. Rescue 1 (Swivel stage used to deorbit, then dropped): mains at 4 km 235 m/s, service module off at 299 m, pod landed in the grasslands, recovered.
- Accepted "Recover Module 761V7 from orbit of Minmus" (a Mk-55 Thud, 0.9 t, ~118 km; kRPC doesn't list the vessel yet, type Unknown) and "Position satellite in a polar orbit of Kerbin".
- **Polar Relay 1** (crafts/polar-relay-1.json: OKTO, RA-2, Science Jr, goo, FL-T400 + Terrier on the Tanker launcher): target inc 90, LAN 205.3, 1259 x 1883 km, argPe 104.7 (7 %). Launch timed on the pad's inertial longitude (lan+argpe+nu of the pad "orbit", 176.4 -> waited 1610 s to 203.3), heading 356: LKO 78x84, inc 85.2, LAN 204.1. First `match-orbit`: plane 4.9 deg 198 m/s (the tuner's radial freedom dropped the periapsis into the air - it flew briefly), far-side 489, apoapsis 573 m/s -> pe 1092 km (13 % low); 30 m/s periapsis burn -> 1258 x 1883, inc 89.99, LAN 205.3, argPe 106.8. **Contract done**, first relay satellite. Fixes: plane-change cost keeps the periapsis, a final periapsis correction when > 1 % off. Funds 1.72M, sci 60.7, rep 253.6.

## 2026-09-25 — Salvage 1 (Klaw vs a loose Thud), RCS researched
- kRPC hides type-Unknown vessels (the contract's "Module 761V7"): new KspBot `SetVesselType` (like the stock rename dialog) -> Probe.
- **Salvage 1** (crafts/salvage-1.json, Jeb; crewed because with Require Signal on an uncrewed craft is blind behind Minmus): LKO 76x82, transfer 985 m/s (the Swivel stage's wheel exploded in the Terrier plume after staging, debris), arrival inc 156 deg retrograde vs the target's 25 deg -> new `correct --inc-to` (grid seed over normal/radial, crossing the impact path) 7.7 m/s -> 62.8 deg prograde. Capture 318 m/s -> 59x60 km. Rendezvous: plane 71 deg 151 m/s, intercept 2.2 + 6.8 m/s, held 28 m.
- **Grab failed for hours**: bumps at 0.15-0.3 m/s, never captured; the Thud spun up to 160 deg/s after the bumps. Decompiled ModuleGrappleNode: capture = a 0.1 m ray from the Klaw's node along its axis hits the target within 43 deg of square (captureMinFwdDot 0.733), relative speed < 1 m/s. Stock KSP zeroes the spin of a vessel going on rails -> `grab` stops a spinning target with a moment of rails warp (160, 13, 17, 20, 30 deg/s -> 0). kRPC raycasts mapped the Thud: its -z mounting side is a rounded ridge (only +-0.1 m passes), +z is a flat plane 13 deg off axis (normal 0,0.24,1), -y has the nozzle sticking out. `grab --face` stations on a face axis and drifts in square to it; still bounced (no sideways correction possible inside the Klaw's turning circle without RCS). Research (grok + opus subagent): the Thud is grabbable (Steam thread 2016: 0.3 m/s, push again right after a bounce; both used RCS); only wheels are known ungrabbable.
- Jeb home: return, pe 30 km, splashdown-free landing, recovered; sci 62.7 -> 75.2 (crew report high over Minmus) -> 95.2 (recovery). **Researched advFlightControl (RCS)**, sci 5.2.
- **Salvage 2** (crafts/salvage-2.json = Salvage 1 + 4x RV-105 + 2x Stratus-V, Jeb): `grab --face` uses RCS when present (Klaw held square by the autopilot, RCS steers the offset and closing speed; axis signs from test pulses: right +x, forward +y, up -z). Transfer: the Swivel ran out mid-ejection, auto-correction 65 m/s; `--inc-to 25` 7.6 m/s; capture 65x66 km. **Rendezvous plane change (90 deg, 206 m/s) put it on a Minmus escape**: rendezvous.match_plane tuned only the relative inclination (now also keeps the semi-major axis). My recovery burn then used `orbital_speed_at` on the hyperbola (returned 19.9 m/s) and burned 98 m/s the WRONG way (ecc 4.06); a closed-loop retrograde burn on the measured speed recaptured it (49x93 km). ~245 m/s wasted.
- RCS approach: along the Thud's +z plane normal, off-axis 0.02-0.09 m, 0.15 m/s - and every contact (centre distance 4.6 m = Klaw 3.14 + pad 1.08 + face 0.41, i.e. the pad touches the face) bounced back at 0.5 m/s with no capture, ~8 times, until the monopropellant ran out (the first RCS run also drifted away 400 m: "not in front of the face" backed off instead of going round - fixed; RCS also spent mono on attitude). New KspBot `GrappleDebug(target)`: Klaw armed (progress 1), FSM Ready, capture ray starts 1.3 cm behind the pad face (node y 1.067), captureRange 0.1, minDot 0.733; Thud colliders THUDCol (convex mesh) + GimbalCol (box), layer 0, in the Klaw's mask. By the code it should capture ~0.6 s before touching; why it doesn't is still unknown -> next time log GrappleDebug every tick in the last metre.
- Return 406 m/s (inclined 49x93 orbit), splashdown, Jeb home. Sci 8.5, funds 1.70M, UT 4,165,147 (Duna window in ~43.7 days).


- **Salvage 3** (uncrewed, for an LKO adapter-recovery contract as a Klaw diagnostic): `circularize` left 62x84 km and the "burn prograde now" periapsis fallback ran 2 min at full thrust: periapsis +9 km, apoapsis hyperbolic. **Reverted to launch** (tooling bug, game-offered). Fix: raise a low periapsis at the apoapsis when it comes first; the burn-now fallback stops if the apoapsis runs away. The user then stopped the salvage effort (recovered on the pad): **rule: no "Recover part" contracts for small/curved parts** (docs/design-guide.md section 0, memory). Contracts left active: Module 761V7 (Minmus Thud), Unit G-P87T (LKO 2.5 m adapter) - far deadlines.
- KSP restart before Duna: commit 21.4 -> 23.6 GB, nonpaged pool 1.22 -> 1.25 GB, KSP 4.39 -> 3.94 GB, available 3.6 -> 2.3 GB (the restart freed nothing overall). UT 4,165,818, funds 1.73M, sci 8.5, rep 257.6.

## 2026-09-25 — Duna 1 (career, Valentina)
- Built Duna 1 in the career VAB (42 parts, 84.8 t, 42.9k), `warp-sc 5098000`, launched with Valentina. LKO 79x80, Poodle 1197 + lander 3893 m/s (same as the sandbox).
- Transfer: ejection 1072 + 2.7 m/s correction -> Duna pe 60 km, but arrival inc 124 (retrograde). In solar orbit `correct --inc-to 10`
  stalled at a 0.1 m/s local optimum (inc 50): out there 0.1 m/s moves the Duna pass ~3,500 km, so the 0.5 m/s seed grid stepped
  over the whole target. Added a 0.05 m/s grid pass -> inc 9.7 for 0.4 m/s (burn error left pe 4.6 km, trimmed later). Fine pe
  trims from 48 days out chase noise (a few mm/s from turning the craft moves the pass by 100s of km): do them inside the SOI.
- **Duna SOI: arrival v_inf 1364 m/s** (sandbox ~760): capture to 60 km would cost 966 m/s, leaving about -50 m/s for the landing +
  return (sandbox: landing ~900, liftoff ~1450, ejection ~740). Cause (tooling): `transfer_planet` sized the ejection for Duna's
  semi-major axis (20.7 Gm) while Duna would be near periapsis (19.7-20.2 Gm); with the extra energy the pe-only tuner twisted the
  ejection so the path cut across Duna's orbit early (194-day flight instead of 295, heliocentric pe 13.33 Gm < Kerbin's orbit).
  **Reverted to launch** (game-offered, tooling bug, crew safety). Fix: ejection sized for the target's radius at arrival, the tuner
  cost adds arrival v_inf / 10, and the burn is refused if v_inf > 1.25x the Hohmann value + 50.

- Relaunch (same UT): ejection 1055 m/s (seed from the arrival radius, v_inf 868 planned), tuned arrival v_inf 1037, correction
  3.6 m/s, inc 9.3 prograde. Duna SOI: v_inf 1067, `correct --inc-to 10` inside the SOI 6.3 m/s -> pe 59.5 km.
- **Capture to 59 x 1007 km** (539 m/s; the Poodle ran dry and staged, the Terrier finished): an elliptical capture instead of
  a 60 km circle saves ~220 m/s and costs nothing for the landing (`periapsis --alt 5000` at the apoapsis, 19 m/s).
  Orbit science 161 (crew 35, goo 70, thermo 56) + orbital EVA report 56 ("space just above Duna's Lowlands"), kept aboard.
- **Landing**: `land` died at 28 km (1120 m/s, tumbling at 33 deg/s once): kRPC `Parachute.deployed` throws a
  NullReferenceException on the lander's 3 Mk2-R (they share the Terrier's stage, so they went active in vacuum at capture;
  their "Safe to deploy?" field is gone). Emergency script (chute calls guarded, same `_powered_descent`): powered descent from
  12 km AGL at 925 m/s, **landed at 15.71 N, 156.21 E, Midlands, 1.4 m/s, tilt 9.4 deg**; the Mk2-Rs never opened (it
  landed on the engine alone). Landing ~656 m/s by mass. Fix: `_chute_deployed()` tolerant of that error (land, liftoff).
  Design lesson: give the lander's chutes their own stage, not the engine's.
- Surface science 161 (crew 35, goo 70, thermo 56) kept aboard. Lander left: LF 376.8 / Ox 460.6, 7.43 t, **~2800 m/s**
  (vac) for liftoff ~1450 + ejection ~740. Photos: docs/media/2026-09-25_duna-1_{pad,orbit,descent,powered-descent,landed}.png.
- Duna->Kerbin window **UT 22,895,340** (600.8 days, flight 297 d). Valentina waits on the surface; other missions meanwhile.

## 2026-09-25 — keosynchronous relays (while Valentina waits on Duna)
- KSP restart at the space center: commit 24.2 -> 23.7 GB, nonpaged pool 1.356 -> 1.357 GB, available 2.34 -> 2.27 GB,
  KSP 2.75 -> 2.31 GB (right after load). Funds 2.03M after the Duna milestones.
- Accepted both "keosynchronous orbit of Kerbin" contracts (goo + thermometer; orbits from persistent.sfs
  SpecificOrbitParameter: A inc 33.95, e 0.104, LAN 24.64, argPe 252.3; B inc 22.03, e 0.0069, LAN 177.82; sma 3,463 km).
  crafts/keo-relay-1/2.json = Polar Relay 1 without the Science Jr, FL-T800, + thermometer (22.3k, sat stage 4594 m/s).
- New `wait-plane --inc --lan`: warps on the pad until the pad's inertial longitude (lan + argpe + nu of the pad "orbit")
  reaches a node of the plane, returns the surface heading (inertial azimuth minus the pad's rotation). A: descending node,
  heading 126.6 -> inc 31.6, LAN 24.4; B: ascending node, heading 66.2 -> inc 20.5, LAN 177.9.
- **Spent SRBs carried to 70 km** (user spotted it): the Kickbacks burned out exactly as the apoapsis reached 80 km, `ascent`
  switched to coasting, and the coast loop only staged while topping up -> the empty casings rode along until circularize.
  Fix: the coast loop drops dry engines at once (Keo Relay 2: dropped at 1:02, right after burnout).
- **Keo Relay 1**: match-orbit plane 92 + 643 + 523 + 7 m/s -> 2502 x 3222 km, inc 33.95, LAN 24.6, argPe 242.7 (5 % = 18 deg
  allowed): **contract done**, 4339 m/s left.
- **Keo Relay 2**: match-orbit's apoapsis burn (1602 m/s) **flipped the orbit retrograde** (inc 158, LAN 357.8 = same plane
  backwards): its cost weighted argPe error even for a near-circular target (e 0.007, the contract ignores argPe below 0.05)
  and had no inclination term. Revert gone (launched via the space center, hours in). Fixed the cost (argPe only if
  e >= 0.05, + 10 x relative inclination). Recovery: bi-elliptic reversal - ap raised to 9,000 km (212), velocity reversed at
  the apoapsis (1150; `execute_node` overshot ~140 m/s: the node frame flips with the orbit when the speed passes zero, so
  don't use it for reversals) -> 9102 x 21867 km prograde; far side lowered 277, `capture --apo` at the periapsis ->
  2843 x 2890 km, inc 22.02, LAN 177.82. Contract done once SAS stopped a 1 deg/s spin ("stability for ten seconds").
  Funds 2.36M, sci 39.5, rep 326.5.

## 2026-09-25 — Rescue Gwenbro (Rescue 2 engine-only, Rescue 3 RCS): Klaw still won't capture
- Accepted "Explore Duna" (Valentina's data should complete it on recovery) and "Rescue Gwenbro from orbit of Kerbin"
  (a Mk1 Lander Can, 77.5 x 80.2 km equatorial).
- **Rescue 2** (= Rescue 1, engine-only): rendezvous 8 + 21 + 4 m/s, held 60 m, Swivel dropped; `grab --face +y` bounced
  at 5.3 m centre distance (0.13 m/s in, 0.17 out), target spun 71 / 27 deg/s (stopped by rails warp), repositioned 3x.
  User: revert and use RCS -> **reverted to launch**, recovered on the pad.
- **Rescue 3** (crafts/rescue-3.json: + 4x RV-105, FL-R120): rendezvous held 52 m; RCS face approach off-axis 0.03-0.07 m,
  0.14 m/s: **2 contacts, both bounced** (-0.37, -0.43 m/s). GrappleDebug at contact: ray from the Klaw node hits the Lander
  Can at **0.010 m, dot 1.000** for several seconds (capture needs < 0.1 m and dot > 0.733), FSM stays "Ready". So the
  geometric conditions hold and the capture still doesn't fire. Remaining conditions in ModuleGrappleNode.on_contact
  (decompiled): FindContactParts' 0.1 m ray finding the part (otherPart != null), IsAdjusterBlockingGrappleGrab(), and
  |klaw rb velocity - other rb velocity| < captureMaxRvel. Next: extend KspBot GrappleDebug to evaluate exactly those
  (call FindContactParts, read otherPart / hit / adjusterCache / rb velocities, invoke on_contact.OnCheckCondition) at contact.
  Rescue 1 did capture once (a swinging, off-axis nose hit), Salvage 1/2 and Rescue 2/3 square contacts never did.
- **Orbit decayed unnoticed**: the station/bounce manoeuvres left Rescue 3 at 64.8 x 80.7 km (density at 65 km 1.2e-5 kg/m3,
  q ~30 Pa, apoapsis falling ~0.7 km/min near periapsis). Fixes: `grab` stops when the periapsis is within 2 km of the
  atmosphere; every flight command ends with an orbit check that logs an `orbit` event if the periapsis is in the air.
- Recorder: `say()` messages now go into the flight log as `say` events (the user asked whether attempts, reasons and
  elapsed time were logged: they were only in stdout); `grab` logs "contact N: bounced at d m, v m/s, t s in" and
  "grabbed after N bounce(s)". Long diagnostics stay off the game screen (`say(..., screen=False)`), screen text <= 100 chars.
- Ascent review (user asked; grok research into MechJeb2 source + forums): liftoff TWR 2.0 -> 6 g, max Q 51 kPa at 9 km,
  drag ~440 m/s to 40 km (typical whole-ascent drag 170-340); MechJeb classic ascent: turn start 500 m / 50 m/s, end 60 km,
  shape 0.4, Limit Q 20 kPa and acceleration 40 m/s2 (off by default, throttle only). New `ascent --twr 1.5` thrust-limits
  the first stage's SRBs on the pad (untested). SRB separation dipped the pitch 29.6 -> 15.6 deg for ~3 s (not yet fixed:
  hold attitude 2-3 s after staging).

## 2026-09-25 — review of the decision process (user request; fable-5 independent diagnosis)
- Pattern behind incidents 1-9 (HANDOFF of e3b326e): the command's own "done" line was read as mission success
  (Duna 1's ejection printed an arrival inc 123.6 and was warped past; Keo Relay 2's 1602 m/s was printed 78 min ahead,
  vs 523 m/s for the same burn on Relay 1); no expected numbers stated before a step, so nothing could look wrong;
  planners burned their own tuned nodes (the two costliest errors were decided by code); retries without a hypothesis
  or cap; side work (code, docs) during running phases; 9 of 14 memories were one-incident rules, and the three that
  said "check state / weigh options" weren't followed. Not mainly long context (the Duna error came 13 min into a
  fresh session).
- Applied (user agreed to all): CLAUDE.md "How to decide" checkpoint (expect / cost / options incl. revert / stop
  rule; compare every phase's result with the expectation). Memories revert-early, weigh-options-before-acting,
  observe-before-fixing folded into it (decision-checkpoint). Code: `_approve` gate on every planner's tuned node
  (Δv > 1.5x the analytic estimate + 20, orbit reversal, periapsis into the air -> REFUSED, node left); `--plan` on
  transfer/correct/match-orbit/return (stop at the node, burn with `ksp node`); `correct` won't trim < 1 m/s around
  the Sun; `grab --max-contacts 3`; land/land_atmo/reentry fall back to chutes + powered descent on an exception while
  coming down; warp_to says the real-time cost of a wait inside an atmosphere. Offline-tested with mock orbits
  (the Keo Relay 2 flip node is refused); first live use comes next.

## 2026-09-26 — Rescue Gwenbro done: the Klaw bug was ours (no MODULE nodes in built .craft files)
- KSP restart for the extended GrappleDebug: commit 25.7 -> 24.9 GB, nonpaged pool 1.52 -> 1.51 GB, available
  3.2 -> 2.1 GB, KSP 4.75 -> 3.91 GB. **Rescue Gwenbro and Explore Duna were back to "offered"** (autosave backups:
  already during Rescue 2's flight, despite accept/launch saving first): re-accepted (+55.6k advances), checked they
  stayed active through a scene switch and in flight. Root cause still unknown.
- **Rescue 3** again (uncrewed): `ascent --twr 1.5` (first use): max Q 51 -> 36.5 kPa at 9 km, speed at 40 km 1410 vs
  1424 m/s (no loss), pitch dip after SRB staging 23 -> 17 deg (was 28 -> 15). Circularize 594 m/s -> 89 x 90 km.
- Rendezvous: `intercept` announced a 96-orbit phasing wait (185,664 s; rails warp is x50 at 90 km = ~1 h real) and
  simply waited: my checkpoint said "vacuum, warp OK" without computing the wait (user caught it). Stopped it. New
  `phase_orbit`: raise the apoapsis for N orbits, circularize back, so the target arrives at the departure point
  (planned 6 orbits, apoapsis 176 km, 2 x 66 m/s). **Its return burn went +172 m/s instead of -66**: kRPC
  `Orbit.orbital_speed_at(UT)` returns another point's speed for future times (asked +600 s it gave the +0/+1200 s
  values) -> the eccentric 89 x 482 km orbit made the intercept 129 m/s + a 342 m/s "correction"; 709 m/s used vs
  ~140 planned (2441 left, enough). Fixes: `flight.speed_at` (vis-viva from radius_at, verified) replaces every
  orbital_speed_at (match_orbit burns 1/2 and the plane-change crossing too: likely part of Keo Relay 2's 1602 m/s);
  rendezvous intercept/correction burns go through `_approve` (would have refused 129 vs ~6 and 342 m/s);
  phase_orbit refuses to continue if the return leaves an eccentric orbit. Held 51.7 m.
- **Klaw diagnosis**: at contact the capture condition was fully TRUE (ray 0.010 m, dot 1.000, adjusters 0, rvel
  0.39-0.50 < 1 m/s, on_contact.OnCheckCondition true) yet the FSM stayed Ready. **KSP.log**: every FixedUpdate
  "[Grapple Module] Grabbing on to Mk1 Lander Can" then `NullReferenceException at ModuleGrappleNode.Grapple`.
  Decompiled: `grappleNode` (AttachNode) is created only in OnLoad (flight scene); our CraftBuilder wrote no MODULE
  nodes (0 in Rescue 3.craft), so KSP never called the modules' OnLoad at launch -> null grappleNode -> NRE ->
  the "bounce". This explains Salvage 1/2 and Rescue 2/3; Rescue 1's single grab came after a KSP restart
  (vessel reloaded from the save, which has MODULE nodes). Lesson: read KSP.log first when a stock mechanism
  "doesn't fire" — hours went into geometry/speed before anyone looked.
- Test: space center -> `fly` (reload) -> **grabbed on the first contact, 0 bounces, no NRE**. `transfer-crew`
  then threw (kRPC TransferCrew uses crew.seat.part; Gwenbro had no seat object after the merge); a second reload
  fixed it. Contract "Save Gwenbro" was already Complete in the save (our `contracts` shows kRPC's
  parameter.completed = false: display bug, not fixed). Released the can, `periapsis --alt 30000` 48 m/s ->
  30.2 x 89 km, `reentry --keep-until 300`: drogues 20 km, mains 4 km 227 m/s, service module off at 301 m,
  splashdown, recovered: **Rescue Gwenbro done**, funds 2.52M, rep 340. Photos: docs/media/2026-09-26_rescue-3_*.
- Root fixes (user asked for the root fix, not the reload workaround): CraftBuilder writes one MODULE node per
  part module, saved from the prefab like the VAB (208 in Rescue 3.craft; pad test: same stage dv/TWR,
  GrappleDebug grappleNode = True on a fresh launch); KspBot `MoveCrew` moves a kerbal by the parts' crew lists
  (not the seat) and fires onCrewTransferred; `transfer-crew --to mk1pod.v2` uses it (untested in flight).
- (Mun Tanker 1's first-try grab of Bob's lander fits the Klaw finding: the tanker had been unloaded and reloaded
  while Bob's lander was flown, so its Klaw's OnLoad ran.)
- Ascent sway (user saw Rescue 4's long stack wobble; fable + opus research): upper 1.25 m stack had no struts ->
  rescue-4.json upper stack rigid + autostrut Root, design-guide section 0 rule, `ascent` pitch command
  rate-limited to 1.5 deg/s. Side boosters stay rigid-only (guide: autostrutted side boosters broke on the pad).

## 2026-09-26 — Rescue 4: Mitbro from Minmus orbit (first flight with MODULE-node crafts)
- crafts/rescue-4.json = Rescue 3 + Communotron 16-S (OKTO's internal antenna can't reach Minmus). Launch before the
  sway fix (the user saw the stack wobble; see above). LKO 78.7 x 80.5, 622 + 2623 m/s left. Contracts stayed active.
- `transfer Minmus --pe 190000 --plan`: 930 m/s (expected 921), Minmus pe 504 km, arrival inc 95 -> `ksp node`.
  The burn staged the Swivel mid-way and lost the encounter (ap 54,967 vs 56,849 km planned); correction 27 m/s
  right away -> pe 190 km. Mid-course `correct --inc-to 21.5`: best 3.2 m/s -> inc 47.6 (grid didn't reach 21.5).
- Minmus: pe 156 km, v_inf 278; capture 218 m/s (expected 216) -> 156 x 158 km. Rendezvous: plane 57.3 deg 90.7 m/s
  (expected ~85), intercept 9.9 + 23.0 m/s correction (gate allowed: <= 35), held 52 m; 175 m/s total, 1893 left.
- **Grab: first contact, no reload, no NRE** (grappleNode = True on the freshly launched craft): the MODULE-node fix
  works. `transfer-crew` (KspBot MoveCrew, first use) moved Mitbro Crew Cabin -> Mk1 pod; the save shows
  AcquireCrew Complete (our onCrewTransferred event reached the contract).
- Return: the gate REFUSED `return --plan` (224 m/s vs "expected 40"): the estimate was wrong, not the burn —
  (v_esc - v_circ) ignored the v_inf needed to drop the Kerbin periapsis. Now: Hohmann v_inf from the moon's orbit
  to pe_alt + escape from here (174 m/s; 224 includes the 21.5 deg plane). Burned: Kerbin pe 33.3 km (kept),
  reentry --keep-until 300 (drogues 20 km 1090 m/s, mains 4 km 203 m/s), landed in the grasslands at night,
  recovered. **Rescue Mitbro done**: funds 2.84M, sci 45.3, rep 368.

## 2026-09-26 — Eve 1 (attempt 1 reverted: hatch blocked, planner can't reach an inclined planet)
- Science is the bottleneck (45; next nodes 160-550). Research (opus, save-parsed): Minmus surface materials bay
  0/125 in all 9 biomes (Minmus Science 1's ~500 were apparently lost: the storage unit's Collect All took the
  non-rerunnable Science Jr data - keep single-use data in its part until understood); no high-orbit science
  anywhere; orbital EVA reports are per biome (low orbit); EVA Experiments Kit (unlocked) gives 25 x multiplier
  per body/situation at 100% transmit; funds->science strategies are worthless (~1 sci / 10k); Science Lab =
  advExploration 160 + advElectrics 160 (power). R&D 2 caps nodes at 500 sci. Plan: Eve 1 -> Minmus biome hopper
  (~1600) -> EVA kit support -> lab -> Mun.
- crafts/eve-1.json = Duna 1 minus legs / lander chutes + a second goo/thermometer + 2 barometers (high + low
  space), whole stack strutted. 84.6 t, 40 parts, 44.5k, Jeb. Ascent: rate sd 0.19 deg/s, max 1.6 (250 m - 15 km),
  max Q 33 kPa: smooth. LKO 79.4 x 79.7, Poodle 1251 + Terrier 4105 m/s.
- `transfer Eve --pe 120000 --plan`: no encounter; the closest-approach tuner inflated the ejection to 1172 m/s
  (v_inf 943 vs Hohmann ~780, heliocentric pe 9.14 Gm < Eve's 9.83) and its radial freedom put the escape
  periapsis at 67 km: `_approve` REFUSED it (first real catch). Cause: Eve is inclined 2.1 deg; the in-plane
  seed + closest-approach cost can't find the out-of-plane path (Duna, 0.06 deg, never showed it).
- `eva out` in LKO: "hatch obstructed" - my barometer sat at angle 90 = the Mk1 hatch (design-guide already says
  so; I didn't check). **Reverted to launch** (game-offered; flight couldn't do its EVA science, planner needs a
  fix anyway), recovered. Instruments moved to 225/270/315 at two heights; pad test: EVA out + board OK.
- Planner fix (fable): folding Eve's plane into the ejection is impossible from an equatorial LKO (at the Eve window
  Eve arrives 347 Mm out of our plane, SOI 85 Mm; a single-burn 3-D Lambert needs asymptote declination 48-66 deg,
  reachable only for ~2180 m/s). `transfer_planet` now does a broken-plane transfer: universal-variable Lambert to
  the target's arrival position projected onto our plane (flight time scanned 0.6-1.4 x Hohmann, min of ejection +
  capture + mid-course plane-change estimate), node tuned (prograde/ut/normal, no radial -> the escape periapsis
  stays at the burn altitude) to match the required exit velocity vector; if the target is outside its SOI of our
  plane it prints the mid-course `correct` UT and expected m/s instead of trimming. Offline check (bodies only):
  Kepler propagation error <= 0.0013 km; Eve window: T 184 d, v_inf 790 -> ejection ~1040, plane change ~413 at
  ~UT 14,211,384, arrival v_inf 919; Duna window: T 278 d, ejection 1085, arrival v_inf 778, only 20.5 Mm off-plane
  (old path). Untested live: `node.orbit.time_to_soi_change` on a node patch (falls back to bisection).
- Eve 1 recovered on the pad (safe state for a session handoff). Eve window UT 11,823,553 (now ~11,790,000).

## 2026-09-26 — Eve 1 (attempt 2, Jeb): at Eve, ~1000 sci aboard, waiting for the return window
- KSP had quit silently at the first `launch` connection (KSP.log just stops; nothing lost, saved at the space
  center a minute before). Restarted with tools/install.sh.
- LKO 79.4 x 79.7, Poodle 1252 + Terrier 4105 (as expected). **Lambert transfer, first live run**: "flight 184 d,
  v_inf 790, ejection ~1040, Eve -347 Mm out of plane, plane change ~413" = the offline numbers; tuned node
  1027 m/s, v_inf error 0.0, Kerbin pe 79.6 km, Sun pe radius 9.80 Gm (Eve 9.73-9.93), ap 13.60 Gm -> burned.
  (_approve prints Sun pe/ap as altitudes above the Sun's 261.6 Mm radius - read them as radius - 262 Mm.)
- Kerbol "space high": crew 10 + thermo 16 + baro 24 transmitted (sci 45 -> 65), orbital EVA report 16 kept.
- Mid-course at UT 14,210,478 (planned 14,211,457): `correct Eve --pe 120000 --plan` 371.6 m/s (expected <= 413)
  -> Eve pe 147 km, v_inf 815 (planned 919), inc 10. Poodle ran out mid-burn, staged to the Terrier: encounter
  held (pe 146.7 km). Note: correct's `_approve` compared the node with itself (no gate); now the inc-to seed's
  analytic dv is the expectation.
- **No link from Eve**: Communotron 16 (500 km) x DSN lvl 2 = ~159 Mm range, Kerbin was 9.5 Gm away -> nothing
  can be transmitted; everything comes home in the pod. Future interplanetary science craft: a bigger antenna
  (HG-5 / DTS-M1 ...) or accept recovery-only.
- Eve SOI: high-space set 1 (crew 25, goo 50, thermo 40, baro 60). Return window Eve->Kerbin is UT 27,264,701
  (528 d), so a biome tour was worth it: `correct Eve --inc-to 90` found only 0.9 m/s -> inc 11 (the +-6 m/s grid
  can't turn the aim point); new `_aim_point_seed` (turn the impact vector about the incoming asymptote, 36
  angles judged by KSP's patch, then tune): seed 73 m/s, tuned 68.5 m/s -> inc 73.1 (tuner stopped short of 90:
  pe km vs inc/5 weighting), pe 142 km. Capture `--apo 40000000` 127 m/s (expected 127) -> 142 x 40,200 km, 3762 left.
- Low space at the capture pass: set 2 (goo 70, thermo 56, baro 84) + EVA reports. Tour script (scratchpad): per
  pe pass warp to 395 km, EVA out, report at every new biome below 400 km, board. 7 passes: **11 of 15 biomes**
  x 56 (Foothills, Lowlands, Shallows, Explodium Sea, Midlands, Highlands, Poles, Peaks, Impact Ejecta, Crater
  Lake, Eastern Sea); Olympus, Craters, Akatsuki Lake, Western Sea not crossed (stop rule: 3 dry passes).
  Aboard: experiments 385 + EVA 616 + 16 = ~1017 sci, recovered only if Jeb gets home.
- Return plan: from this 142 x 40,000 km polar orbit the ejection asymptote is fixed by the pe; at the apoapsis
  (slow) rotate the orbit so the pe lies under the required asymptote, then eject at pe (~200 m/s) and a
  broken-plane mid-course change. transfer_planet assumes a circular parking orbit: needs work before UT 27.2M.

## 2026-09-26 — Minmus Science 2 (Bob): 5 biomes of surface science, +1166 sci
- Why: the save had no `mobileMaterialsLab@MinmusSrfLanded*` at all (Minmus Science 1's surface materials never
  arrived). Decompiled ModuleScienceContainer/Experiment: Collect All handles goo and materials identically (goo
  from that flight was credited), so the mechanism is fine; MS1's printed "materials 100" at each biome was the
  orbit duplicate (InSpaceLow value) still held, not surface data. This time: check the storage unit's
  "Review Stored Data (N)" after every biome.
- crafts/minmus-science-2.json: Eve 1 launcher + Duna 1 lander with legs + 5 Science Jrs stacked under the pod
  decoupler, 6 goo, baro, thermo, Experiment Storage Unit at 135 deg. 85.9 t, 56.5k. LKO 79.3 x 79.5, Poodle 1010
  (expected ~1130), lander 3296. Jeb was on Eve 1: the launch with his name hung (exit 124), relaunched with Bob.
- Accepted "temperature surveys of Minmus near Zone 5LC3PS" (4 surface sites) before reading the rule: GROUND
  band trigger range = MinimumTriggerRange = **500 m** (SurveyWaypointParameter.TriggerRange); our landings land
  within ~2 km. Left unflown (money isn't the bottleneck). New `land --at LAT LON` (find_point: first pass within
  2 km of a point) exists but wasn't flown.
- Transfer 936 (expected 921), encounter off after the burn again (ap 57,553 vs 59,298 km planned, like Rescue 4),
  3 m/s fixed pe; inside the SOI `correct --inc-to 90` (aim-point seed) 23 m/s -> inc 91. Capture 207 m/s
  (expected 207) -> 12 x 16 km polar, lander 3135.
- **`eva out` failed twice ("hatch obstructed?", spawnEVA null)**: the only side part new vs Eve 1 is the storage
  unit at 135 deg (45 deg from the hatch). And **`eva report` then ran every experiment on the ship** (it didn't
  check for an EVA kerbal): 5 Science Jrs + 6 goo spent in high space. Recovery: the stock "Reset" event (active
  for a deployed, non-rerunnable, resettable experiment whose data hasn't been collected; decompiled) cleared them
  all, operable again; kept one goo's 25. `eva report` now refuses unless the active vessel is an EVA kerbal.
- Landings (`land --biome ...`, liftoff --heading 0 back to a polar orbit between): Lowlands 250 m/s, Poles
  (83 N, tilt 10 deg) 515, Flats 537, Highlands 520, Lesser Flats 521 per liftoff + landing; each: materials 125,
  goo 50 (11.5 where done), baro 60, thermo 13; storage 4 -> 9 -> 14 -> 19 -> 24 -> 29. Slopes left (no Science
  Jr / fuel for a sixth).
- Return: `return --plan` 229 m/s with a RETROGRADE Kerbin arrival (inc 133) vs expected 163: the seed was
  (v_esc - v_circ) x 1.15 = 70 m/s so its burn time was random, and the cost didn't tell the roots apart. Fix:
  seed at the expected size, retrograde arrival costs 1e4. Replan: 164 m/s, inc 32. Kerbin pe 36 -> 2 m/s trim ->
  30 km, reentry: storage unit skin 1774 K (limit 2900; the other side parts ~460 K), splashdown, Bob safe.
  **Science 84 -> 1250.** Researched advExploration (lab), advElectrics, electronics (HG-55, magnetometer),
  specializedConstruction (docking), scienceTech (ATM analyzer), advLanding -> 10 left.
- Eve 1 note (for its return): its goo/thermo/baro data (385) sit in pod-side parts; MS1/MS2's pod-side parts
  survived Minmus-speed entries (skin ~460 K). The Mk1 pod's container can't Collect All (canTransferInVessel
  false); an EVA kerbal's "Take Data" has a GUI range of 1.5 m only (the call itself has no range check): measure
  hatch-to-part distances before relying on it.

## 2026-09-26 — Survey 1 (Bob): orbit-only science at Kerbin/Mun/Minmus, +1601 sci
- Idea: the save had almost no in-space subjects (Mun/Minmus EVA per biome, magnetometer 45 x body multiplier,
  high-space sets); one crewed orbiter can take them all without landing. crafts/survey-1.json = Eve 1 stack with
  pod side parts only at 225/270/315/0 (hatch clear; storage unit at 315, -0.15), 3 Science Jrs, magnetometer boom
  on the Terrier tank. Pad EVA test: out fine, but Bob floated off the pod and fell to the pad (Ragdoll, alive):
  **reverted to launch** (game-offered) to get him back in. LKO fine, Poodle ~1050 + Terrier 3623.
- Mun: transfer 865 (expected 857) -> pe -5.6 km after the burn, arrival retrograde equatorial. Aim-point seed v1
  (straight line b/t) from Kerbin orbit gave inc 167 only: outside the SOI a burn doesn't move the aim point by
  dv x t. v2: least-norm burn from a numerical Jacobian of KSP's own predicted impact vector (3 trial nodes,
  re-linearised once), 36 aim angles judged by the real patch: 116 m/s -> inc 98 (a normal burn near the node line
  right after TLI has little leverage; accepted: dv budget ~3800 vs ~1200 needed). Kerbin high: all 7 subjects incl.
  magnetometer 67.5. Mun high + low, capture 279 (expected 279) -> 14 x 17 km.
- **Magnetometer takes ~7 s to report**: `do_science` collected after 1.5 s and the next call reset the half-done
  experiment as "worthless" -> lost the Mun low reading once; now waits (<= 20 s) until every started experiment
  has data. Re-ran: 135.
- Mun biome tour (new scratch script: predict the next entry into a missing biome from the ground track, warp to
  the middle of that pass, EVA, report, board): **all 17 Mun biomes** now have low-orbit EVA reports. The printed
  report titles lagged the real subjects (a save showed PolarLowlands/NorthwestCrater stored under other titles);
  a duplicate made the pod refuse the kerbal's data -> KSP's "Cannot store experiments / Board anyway" popup
  (KerbalEVA.checkExperiments) and `eva board` silently did nothing: dumped the duplicate, boarded, dismissed.
- **Mun -> Minmus**: `transfer Minmus` from Mun orbit reached transfer_planet (generalised to moons), but (1)
  planet_window's 40-day lookback picked a window 5 synodic periods old (Mun->Minmus every 7.4 d; lookback now
  <= 0.15 synodic), (2) from a POLAR Mun orbit the needed escape direction (along the Mun's velocity) was 76 deg
  out of our plane: it lines up twice per Mun orbit (1.8, 5.0, 8.2, 11.4, 14.6 d) and the window came at 14.8 d,
  (3) transfer_planet matches the velocity at the SOI edge, which for a small SOI isn't v_inf (Mun: 2mu/r_SOI =
  53,600 m2/s2 ~ v_inf^2): its plan went to ap 31,773 km, inc 23 -> not burned. Raised the orbit to 400 km (117 +
  90 m/s) so the 14.2-day wait warped fast, then a scratch closest-approach tune from a 159 m/s seed: 161 m/s ->
  Minmus pe 21.5 km, inc 80 (Kerbin orbit inc 22, arrival v_inf 233 -> capture 165 instead of ~100).
- Minmus: high magnetometer 112.5 + EVA 20; inc-to-90 trim (22.6 m/s) skipped, 80 deg reached the Poles; capture
  165 -> 21 x 22 km; low magnetometer 180; biome tour: all 8 missing biomes (Midlands already done).
- Return: gate REFUSED 365 m/s (expected 163): same plane geometry (Minmus' velocity 58 deg out of the polar plane).
  Waited 8.2 d for the alignment - in the 22 km orbit that cost **36 real minutes** of warp (raise the orbit
  first next time) - then 160 m/s -> Kerbin pe 36 km (+6 km after every moon return burn, 3rd time) -> 1.8 m/s trim
  -> 30 km, reentry, landed in the Highlands. **Science 11 -> 1613.** Storage unit held 44 items.
- R&D upgraded to level 3 (1.69M; nodes > 500 sci), researched fieldScience, advScienceTech (ISRU, drills,
  gravimeter), largeVolumeContainment (3.75 m), commandModules (Mk1-3 pod), largeElectrics. Funds 1.26M, sci 3.
- Lessons: polar orbits around a moon lock the escape direction: plan departures by plane alignment (twice per
  moon orbit) or leave from an equatorial orbit; before a long wait, raise the orbit for fast warp.

## 2026-09-26 — Rescue 5: three kerbals in one flight (Gwenbro, Daphrick, Jedgard)
- Found "Gwenbro's Derelict" still orbiting WITH Gwenbro (roster: Assigned) although Rescue 3 had "recovered" her:
  two vessels carry that name; the empty one is the can Rescue 3 released. Accepted "Rescue Daphrick" (Scientist)
  and "Rescue Jedgard" (Pilot); all three sat in equatorial LKO 75-88 km.
- crafts/rescue-5.json: Mk1-3 pod (3 seats, 2.5 m bottom) + Klaw on top, HeatShield2, 3 Mk2-R + 3 drogues; uncrewed:
  OKTO in a 1.25 m service stack under a C7 2.5->1.25 adapter tank (RCS on it), Terrier; Eve 1 launcher. First
  build had the pod decoupler in the Terrier's stage (would have dropped the pod at ignition): fixed before launch.
  LKO 79.6 x 79.9, Poodle 887 (dropped) + Terrier 2158.
- Grab 1 caught the EMPTY can (kRPC resolved the name to it): released, renamed it "Empty Can (Rescue 3)", flew to
  the real one. Every grab: first contact, 0 bounces (MODULE-node fix holds). `transfer-crew --to mk1-3pod` x3.
- `rendezvous` refused twice "orbits too similar to phase: change altitude by >= 5 km": raised to 95 / 110 km
  circular first. Found: our CLI prints "ERROR: ..." but exits 0, so `a && b && c` chains ran grab/transfer after
  a refused rendezvous (harmless here). Rendezvous ~110-160 m/s each (phasing orbits 2 x 45-60 m/s).
- periapsis 30 km, reentry --keep-until 300, splashdown, recovered: both rescue contracts done, funds 1.33 -> 1.44M,
  rep 407. Crew now: Bob, Gwenbro, Daphrick (scientists), Bill (engineer), Mitbro, Jedgard (pilots); Jeb on Eve 1,
  Valentina on Duna.
- Eve 1 return designed offline by fable (merged: kspbot/kepler.py, `depart`, tools/plan_eve_return.py): from the
  142 x 40,000 km orbit the escape cone is tied to the apoapsis direction (138 deg off Eve's prograde at the Hohmann
  window); the cheap option is 8 periapsis passes after the window: tilt the plane at the apoapsis (105 m/s, UT
  28,925,295) and a tangential periapsis burn (215 m/s, UT 29,029,189) -> 298-day arc, arrival v_inf 2142 (entry
  ~3.9 km/s), ~320 m/s total. Lab mechanics researched (opus): docs/lab/README.md + docs/lab/LabSketch.cs.

## 2026-09-26 — Minmus Lab 1: science station in a 14 km polar Minmus orbit (Bob, Gwenbro)
- Tooling first: the CLI already exits 1 on "ERROR" (tested); Rescue 5's `a && b` chains ran on because of `| tail` pipes.
  KspBot: LabStatus / LabProcess(dryRun) / LabAction(start|stop|transmit|clean) (docs/lab/LabSketch.cs, labValue computed
  like the results dialog) -> `ksp lab status|dry|process|start|stop|transmit|clean`.
- crafts/minmus-lab-1.json: Clamp-O-Tron, OKTO, Science Jr, 3 Z-1k, reaction wheel, Rockomax adapter, MPL-LG-2, C7 adapter
  tank (2 goo, thermo, baro, gravimeter, storage unit, HG-55), wheel, FL-T400 (2 Gigantors, magnetometer, 2 Z-400),
  Terrier; Rescue 5 launcher. 87 t, 75k.
- **Pad EVA test killed Bob and Gwenbro twice** (reverted both times): the moment the kerbal spawns at the MPL hatch
  (airlock_l, part-frame angle 90, r 1.5 m) the stack gets a kick (tilt 0 -> 3.6 deg, 1 m/s within 0.5 s) and the 87 t
  rocket topples onto the pad. New `eva check` / EvaCheck: airlock position + other parts' colliders within 1 m (none
  here); EvaSpawn now refuses when parts overlap the hatch. In LKO, measured: EVA from the MPL adds ~6 deg/s and
  ~0.08 m/s to the free station (baseline 0.02 deg/s); with the station's SAS on it damps to ~2 deg/s in 8 s and the
  kerbal stays on the ladder -> orbital EVAs are fine with SAS on; **no pad/landed EVA from the MPL** (the same kick
  probably explains the earlier "landed EVA flung the kerbal" incidents). Each kick moves the orbit: at Minmus
  apoapsis (7.5 m/s) one EVA dropped the periapsis 14 -> -5.5 km; 9 tour EVAs left 13 x 15 -> 7.8 x 15 km.
- **Ascent 1 flipped** at the Mainsail separation (14 km, q 24 kPa: 94 deg/s in 5 s), crashed in the sea, crew killed:
  **reverted**. The long, light payload (MPL + 1.25 m stack + Gigantors on top) moved the centre of pressure forward;
  Rescue 5's compact pod flew the same launcher fine. Fix: AV-R8 x4 on the Skipper tank, AV-T1 x4 on the Poodle tank,
  Gigantors moved down to the FL-T400. Ascent 2 clean. LKO 79.3 x 79.5, Poodle 791 + Terrier 2200.
- Kerbin low (EVA Grasslands, goo, materials, thermo, baro, gravity, magnetometer) and high sets straight into the lab
  (159 + 240 data), `lab clean` resets goo/materials (lab needs ~70 s at 1x). Transfer 922 (expected 921).
- Minmus SOI: pe 1660 km instead of 15 (encounter drift again, plus an EVA kick in Kerbin high space). Option chosen
  (cheaper than a 170 m/s aim-point change): capture at the 1660 km pass into 1653 x 2062 km (204 m/s), at the apoapsis
  one burn to a polar plane with pe 15 km (27.2 m/s, scratch script: plane through the axis and the position), pe fixed
  after the EVA kick (2.1 m/s), circularize 61 m/s -> 12.9 x 13.3 km, inc 92.7. Terrier left 1774 m/s.
- **The first capture burn never fired**: throttle 1, thrust 0, control "none". Require Signal for Control is on and I
  never extended the HG-55: the OKTO's own antenna (5k x DSN 2 -> ~16 Mm) can't reach Minmus (47 Mm). Extending it
  (allowed without control) gave signal 1.0 and full control. Lucky: 6000 s before leaving the SOI. `burn_at` should
  refuse / warn when control is none (next steps).
- Minmus high set + low set + all 9 low-orbit biomes (EVA report + gravity scan each, tour script with SAS and a 6 s
  settle) -> lab 720/750 data, 9.7 sci/day, rest (~1,500 lab data: magnetometer 225/141, materials 125, gravity 9 x 100,
  EVA reports) kept in the storage unit for top-ups or a ferry pickup (gravity transmits at 40 % only). Lab transmit:
  **science 2.6 -> 146.4**. Periapsis raised to 13.6 km (3 m/s). Photo: docs/media/2026-09-26_minmus-lab-1_orbit.png.
- Lab throughput: at 720 data the lab eats ~2 data/day (tau ~92 days at S = 2.5): a full lab makes ~10 sci/day,
  so ~500 per 50 days; visit (switch to it, transmit) every <= 50 days.

## 2026-09-26 — contracts mix-up (Ike station accepted), Keo Relay 3 (gravioli keosynchronous contract)
- `accept "keosynchronous"` accepted, but the save right after threw an NRE (FlightState ctor, first save after the
  flight), the CLI printed ERROR, I retried with `accept 4` - the list had shifted and it took **"Build a new orbital
  station around Ike"** instead. A scene switch then half-reloaded the old save (funds back to 1.368M, contracts
  "active" objects stuck in the offered list, accept() did nothing); `load-save` didn't clear it, a KSP restart did
  (both contracts offered again, nothing lost). Then accepted both on purpose: keosynchronous (48.5k + 124k) and
  **Ike station** (303.6k advance, 905.6k on completion, failure 349k, deadline ~41 years: 9 kerbals, ISRU, cupola,
  antenna, docking port, power, in Ike orbit - fits the Duna + Ike goal). `accept` now prints the title first and
  only warns if the save fails.
- crafts/keo-relay-3.json = Keo Relay 2 with a GRAVMAX instead of the goo (30.3k). Target inc 4.24, e 0.057,
  sma 3463 km, LAN 95.64, argPe 299.63. wait-plane: heading 85.4; LKO 82.6 x 87.7, inc 3.94; match-orbit plane 12.9,
  periapsis side 647 (expected 643-647), apoapsis 457 -> sma 3461.7, e 0.0567, inc 4.24, LAN 95.67, argPe 299.73:
  **contract done**, funds 1.72 -> 1.81M, sci 146 -> 154. `--plan` stopped on sub-1 m/s trims of the first burn
  over and over: match_orbit now skips trims < 2 m/s. Keo Relay 3 keeps 4617 m/s (spare relay / tug).

## 2026-09-26 — Minmus Lab visit, Duna 1 liftoff, the save NRE diagnosed and fixed (then a PC restart)
- Lab visit at UT 22.85M: "Science Full" 497.9 (40 days) -> `lab transmit` (~2,000 EC, ~1 min): **sci 154 -> 652**;
  topped up with materials 125 from the storage unit (745/750 data).
- Ike Station 1 designed offline by fable: crafts/ike-station-1.json + docs/ike-station-plan.md (134 t, 72k, Twin-Boar
  + S3-3600 / Skipper / Poodle transfer stage that stays on; cupola + 2 Hitchhikers = 9 seats, Convert-O-Tron 125,
  2 HG-55 + RA-15, Clamp-O-Tron). **Window Kerbin -> Duna UT 25,054,465**; budget ~2250 of ~2900 m/s after LKO.
  Not flown yet. Tooling gaps it lists: solar panel deployment, moon transfer from an elliptical orbit.
- **Duna 1 liftoff** (Valentina): `liftoff --alt 60000 --heading 90` -> 59.2 x 59.5 km, inc 15.7, used 1421 m/s
  (expected ~1450), 1386 left. `transfer Kerbin --pe 30000 --plan` then sat warping toward the window (UT 22,895,340,
  2.1 days) at ~4x effective: 5,800 game s in 25 real minutes (60 km Duna orbit warp cap), killed by its timeout.
  Lesson (next step 4b): wait for a far window from the space center (`scene space_center`, `warp-sc`, `fly`).
- **The save NRE** (user: find the cause first, fix only if needed; fable diagnosed, opus fixed; full write-up:
  docs/save-nre-diagnosis.md): kRPC switches scenes from inside a physics FixedUpdate; when that frame has a second
  physics step, FlightGlobals.FixedUpdate re-arms `FlightGlobals.ready` after OnSceneChange cleared it, and the
  space center keeps `ready == true` with no active vessel. Every SaveGame then throws in FlightState..ctor (IL 0x2a6:
  ActiveVessel.protoVessel), and a scene change after a failed save rolls the career back to the last good save
  (Game.Updated fails before refreshing the scenarios). That was the contract mix-up at 09:25-09:50 and it happened
  again after the Duna 1 flight (`fly` saves first -> NRE). 2 of 6 flight -> space center switches today. Log
  signature: "Reference Frame: Rotating" right after "Scene Change : From FLIGHT to SPACECENTER". Recovery without the
  fix: tracking station -> space center bounce (resets the flag; loses what was done since the last good save).
  Fix (KspBot + CLI): SceneGuard addon clears the stale flag every Update outside flight; `Save` procedure (never
  throws, JSON ok/error) used by every CLI save, failures stop the command; `SwitchScene` saves and loads the space
  center / tracking station from a coroutine in the Update phase; `ksp scene` waits for the load and test-saves.
  `recover` still switches from FixedUpdate (the guard repairs the flag at the space center).
- Recovered with the bounce (UT back to 22,856,293, only a KSC warp lost), save OK, installed the fix: install.sh
  saved persistent ("saved persistent") and killed KSP, but **KSP didn't come back up** (second time today; the
  Steam launch after taskkill sometimes does nothing). The user is restarting the PC (Windows memory: available
  5.4 GB, commit 20.3 / 33.8 GB, nonpaged pool 1.81 GB - high again, see memory note).

## 2026-09-26 — PC restart, save fix verified, Duna 1 heads home, Rescue 6 (Elfry + Barzor with his lander can)
- KSP back up (Windows before start: commit 15.4 GB, nonpaged pool 0.89 GB, available 3.6 GB). **Save-NRE fix verified live**:
  `status` flightGlobalsReady false; `scene tracking_station` / `scene space_center` and flight -> space center all print
  "test save ok" (8 switches today, no failure).
- **Duna 1 ejection** (Valentina): `warp-sc 22893000`, `fly`, `transfer Kerbin --pe 30000 --plan`: Lambert 675, tuned
  **762 m/s** (expected ~740), Kerbin encounter pe 9,121 km inc 88.6 -> burned, residual 0.2; 623 m/s left. After the Duna
  SOI exit Kerbin pass pe 11,514 km, inc 56.5, Kerbin SOI at UT 29,273,095.
- `correct Kerbin --pe 30000` from there planned **80 m/s**. Cause: we left from Duna's aphelion side and the arrival point is
  178 deg ahead, on the line a normal burn tilts the plane about, so Kerbin's 14 Mm out-of-plane offset can't be removed
  cheaply (fine grids +-1 and +-15 m/s: pe only 11.5 -> 8.5 Mm). Not burned. Mid-course 90 deg before arrival: **UT
  26,854,269** (~10 m/s expected, the Lambert print said plane change ~10). `correct` now refuses > 20 m/s far out when the
  arrival is > 135 deg ahead and prints that UT. The aim-point seed crashed there (all 36 tries lost the encounter).
- Tooling: solar panels open with the antennas after `circularize` (in orbit) and fold before `land` (panels only).
- Contracts: accepted Rescue Elfry (LKO, 52k) and Recover Barzor + Barzor's hulk (Mk1 lander can, 6.7 x 7.7 km equatorial
  Minmus orbit, 204k). crafts/rescue-6.json = Rescue 5. `launch` auto-crewed the pod (Bill, Mitbro, Daphrick): recovered
  on the pad, relaunched `--crew none`. (`launch`'s pad check prints "skipped: not available in SpaceCenter": runs too early.)
- **Attempt 1 reverted to launch** (tooling): grab of Elfry's pod OK, but `transfer-crew --to mk1-3pod` treated Elfry's own
  Mk1-3 pod as "ours" (same part name) and moved nobody, then `release` let her go. A scratch RCS back-off script (grab
  refused "too close to turn") left SAS and RCS on; the next grab's autopilot fought them for 10 min (5-28 deg/s swings):
  monopropellant 150 -> 0, battery 360 -> 0, control none, spinning 12 deg/s in the dark. Without RCS the Minmus grab
  wasn't possible -> revert. Fixes: transfer_crew takes the crew only from the parts below the Klaw and checks they
  arrived; grab turns SAS/RCS off first and backs off with RCS translation (`_back_off`) when too close.
- Attempt 2: 99.4 x 99.7 km (Poodle 856 + Terrier 2158), rendezvous ~100 m/s, grab 0 bounces, Elfry moved, released.
  `transfer Minmus --plan` gave **1094 m/s** (Kerbin escape): Minmus was 3.9 Mm out of Kerbin's equatorial plane at
  arrival (inc 6 deg, SOI 2.25 Mm); the offset is < 0.4 Mm for departures 17-18 days later -> waited at the space center
  (warp-sc +16.6 d): **930 m/s** (Minmus v_inf 276, as Rescue 4). The Poodle ran dry mid-burn -> pe 84.6 km inc 61;
  `correct Minmus --pe 15000 --inc-to 0` 9.7 m/s -> pe 12.2 km, inc 6.3. In the SOI `--inc-to 0` wanted 9.2 m/s for no
  inclination change: skipped. Capture 193 m/s (expected 193) -> 12.2 x 12.6 km; rendezvous plane 17 m/s.
- **Burns refused behind Minmus: "no control (partial)"**. The user saw the node time go positive (passed) and asked:
  fable diagnosed it: stock "No Pilot" (ModuleCommand: crew without the Pilot trait + no CommNet link =
  KerbalPartial, which locks only map node editing; throttle, staging, SAS work). Elfry is an Engineer. Our burn guard
  refused it: fixed (partial with a kerbal control source passes). Finished with kill_relative + approach (965 m pass,
  held 28 m), grab 0 bounces, Barzor moved into our pod, the can kept on the Klaw.
- Lab visit on the way (UT 23.456M): 273 sci transmitted, **sci 652 -> 925**; topped up from storage to 730/750.
- Return 167 m/s (expected 162) -> Kerbin pe 36.7 km (the +6 km bias again, 4f), trimmed 1.5 m/s -> 30.8 km; reentry
  with the can on top: fine (the can stayed cool in the pod's wake), splashdown, recovered: **both contracts done, funds
  1.93 -> 2.19M**, rep 438. Crew +2: Elfry (engineer), Barzor.

## 2026-09-26 — Jool 1: uncrewed Nerv orbiter on its way (Kerbin->Jool window UT 24,293,116)
- Research: aviation (45: Mk0/Mk1 LF-only fuselages, so Nerv stages carry no dead oxidizer) and automation (550:
  Communotron 88-88, RA-100). Sci 925 -> 330.
- Designed offline by fable: crafts/jool-1.json + docs/jool-1-plan.md (46 parts, 87.1 t, 83.6k): OKTO, stabilizer,
  4 Mk1 LF fuselages + Nerv (6615 m/s), 3 x 88-88 (228 G -> 107 Gm with DSN 2; Kerbin-Jool max ~86 Gm), 3 Gigantors
  (~1 EC/s each at Jool), 2,610 EC, science set (Jr, 2 goo, thermo, baro, gravioli, magnetometer); Skipper + Mainsail
  launcher, fins on all three stages. Pad numbers matched the plan table (1280 SL / 2127 SL / 6615 vac).
- Ascent clean: 79.4 x 79.6 km with the Skipper still holding 480 m/s. The new circularize code opened the three dishes
  and three Gigantors (signal 1.0). Warped to the window from the space center.
- `transfer Jool --pe 250000 --plan`: Lambert 1965, tuned **1954 m/s** (expected 1934-2100), Jool pe 250 km, v_inf 1583.
  **The burn stopped 601 m/s short**: burn_time used the current stage (Skipper, "~54 s"), the Skipper staged after
  480 m/s and the "3 x estimate + 60 s" guard stopped the Nerv. Tooling bug; fixed: burn_time walks KSP's per-stage
  delta-v readout. Right away (checkpoint: Oberth fading, revert possible but the craft was whole and had ~5,000 m/s)
  601 m/s prograde -> Sun ap only 62.3 Gm (72.9 needed); `correct Jool --plan` 278.5 m/s (hand estimate 120-150; the
  tuner has no dv term) -> Jool encounter. After the Kerbin SOI 3.5 m/s -> Jool pe 250 km, but the burn error left
  **pe 76.6 km (inside the 200 km atmosphere), inc 110.7**: fix both at the geometric mid-course, **UT 27,263,628**
  (90 deg before arrival), `correct Jool --pe 250000 --inc-to 0 --plan`. Jool SOI **UT 52,787,080**. Nerv left
  ~4,540 m/s (plan after capture: ~3,800 for a moon tour). Lost to the short burn: ~130-280 m/s.

## 2026-09-26 — Ike Station 1 launched toward Duna (window UT 25,054,465)
- Pad numbers matched docs/ike-station-plan.md exactly (1824 SL / 1277 SL / 2942 vac, TWR 1.42). First Twin-Boar flight:
  clean ascent, 79.7 x 79.9 km with the **Poodle still full (2942)** + Skipper 24. Both Gigantors, two HG-55 and the
  RA-15 opened on circularize (new code), signal 1.0. Photo: docs/media/2026-09-26_ike-station-1_pad.png.
- `transfer Duna --pe 60000 --plan`: **1085 m/s** (expected 1080-1120), v_inf 829 (plan 868), Duna pe 60 km but
  arrival inc 146.6 (retrograde): accepted against my stop rule because Duna 1 flipped a 124 deg arrival far out for
  0.4 m/s. The burn ran through the Skipper-to-Poodle staging to the end (burn_time fix works). After it the Duna pass
  missed by 61.9 Mm (SOI 47.9); after the Kerbin SOI `correct Duna --pe 60000 --inc-to 10 --plan` 27.1 m/s -> pe 59.8,
  inc 52.9 (not 10); burned -> pe 279.6 km, inc 41.7. Poodle ~1,850 m/s left (plan ~1,700 after mid-course).
  **Duna SOI UT 30,679,045**: trim pe 60 km + inclination inside the SOI, capture ~640, then Ike.

## 2026-09-26 — mid-course burns (Duna 1, Jool 1), lab visit
- Duna 1 at UT 26,853,909 (90 deg before arrival): `correct Kerbin --pe 30000 --plan` **7.0 m/s** (expected ~10) ->
  burned; the far-out burn error left Kerbin pe 204 km (inc 85): trim inside Kerbin's SOI (UT 29,268,764).
- Jool 1 at UT 27,263,200: `correct Jool --pe 250000 --inc-to 0 --plan` **2.5 m/s** -> inc 110.7 -> 15.9 (the 90 deg
  point makes the plane nearly free); burn error left pe -655 km: trim inside Jool's SOI (2.46 Gm, days of lead).
- **Lab visit late (my arithmetic)**: from 23.456M at ~9.3 sci/day the 500 cap came at ~24.62M, not ~27.5M as I wrote;
  the lab sat full ~120 days (~1,000 sci of production lost). The first `lab transmit` did nothing (EC 1,793 < ~2,000
  needed; no error); with a full battery the second worked: **sci 330 -> 829**. Topped up to 731/750. Next visit before
  ~UT 28.43M (54 days at ~9.3/day). Tooling: `lab transmit` should check EC first and wait until science rises.

## 2026-09-26 — Eve 1 leaves Eve, Duna 1 home (Valentina), science into the pod
- Lab visit UT 28.40M: 485 sci transmitted, **sci 829 -> 1314**, topped up to 734/750.
- **Eve 1 (Jeb)**, fable's offline plan to the metre: `depart Kerbin --pe 30000 --plan` tilt 104.6 m/s at the apoapsis
  (expected 105), dry-run ejection 215 (planned 215) -> burned; run 2 `--at 29029189` 214.8 m/s -> escaping, Eve SOI exit
  UT 29,087,752, Sun ap 15.96 Gm. `correct Kerbin` then found **no encounter** (coarse search 48 m/s, "no encounter").
  The orbit passes Kerbin at 39 Mm (SOI 84) on UT ~35,464,577, and even a test node bringing the closest approach to
  0.26 Mm showed no Kerbin patch. fable diagnosed (decompiled PatchedConics._CheckEncounter / Orbit._SolveClosestApproach,
  reproduced with kspbot/kepler.py): the solver seeds from the first of the two orbit-crossing points (+23 d, 308 Mm);
  the second candidate time is wrapped to (-P/2, P/2] and the gap (4,303,298 s) exceeds P/2 by 10 h, so it lands in
  the past and the real pass (+73 d) is never examined. **SOI switching does not depend on the prediction**
  (OrbitDriver.CheckDominantBody by position, on rails and at 1x). Once UT > ~31.2M the first crossing is in the
  past and the game shows the encounter: then `correct Kerbin --pe 30000 --plan` (~9 m/s) and check it against kepler.py.
- **Duna 1 home**: Kerbin SOI UT 29,268,764 with pe 204 km. `correct` stopped at pe 64.7 (10 m/s): lower paths cross the
  Mun's SOI on the way in (inbound, before the periapsis) and the tuner's moon penalty blocks them (right here; a
  change I made to ignore moons after an atmospheric periapsis doesn't apply to this case). Scratch grid: no Mun-free
  path under 57 km; **via a 2,200 km Mun flyby** 1.2 m/s gives the final Kerbin pe 30 km -> burned, 31.0 km after the
  Mun. Reentry, splashdown, **Valentina recovered: funds 2.35 -> 2.53M, sci 1,329 -> 1,626 (+297)**, "Explore Duna" done.
  The "surface science from Duna" contract stayed open: the Duna surface goo and thermometer data sat on the lander
  stage that `reentry` jettisons (~80 sci lost). Fix: KspBot `StoreScience` moves every experiment's data into the
  root part's container (the Mk1 pod's own "Collect All" is disabled: canTransferInVessel = false), called by
  `collect_science` before the jettison (crewed). Tested on Eve 1: 7 items stored, 11 held in the pod.
- KSP restarted for the mod (Windows before: commit 24.8 GB, nonpaged pool 1.20 GB, available 3.1 GB; at session start
  15.4 GB / 0.89 GB / 3.6 GB). Sandbox photo shoot for the summary cards (shoot_crafts.py): 6 of 8 crafts (Minmus
  Science 2 and Survey 1 timed out on launch).
- Progress cards v2 (user request: fable leads, opus builds): docs/summary-cards-plan.md, tools/summary/v2/,
  docs/media/summary/v2/ (10 cards), career.json extended.

## 2026-09-26 — Ike Station 1 in Ike orbit: contract done (+905.6k)
- Lab visit UT 29.55M: +492, **sci 1,626 -> 2,118**, 736/750.
- Duna SOI (UT 30.68M): `correct Duna --pe 60000 --inc-to 0 --plan` 16.0 m/s (expected ~10) -> pe 60.3, inc 1.3.
  Capture **586 m/s** (hand estimate 586: v_inf 770) -> 58 x 63 km, 1,243 m/s left (plan ~1,060).
- `transfer Ike --pe 50000 --plan` **310 m/s** (plan ~300), Ike v_inf 48, arrival retrograde (165 deg; fine for the
  contract) -> Ike pe 47.5 km.
- **Ike capture never fired**: "burn is taking far too long", residual 135.8 = the whole burn. The probe had control
  "none", signal 0: the uncrewed station lost its CommNet link near the Ike periapsis (Kerbin hidden; the guard only
  checks at the start). Recovery (checkpoint: escaping Ike, SOI exit 4,381 s away; v_inf only 48 so ~5-15 m/s binds it;
  worst case a Duna orbit with 933 m/s and a second try): scratch script warped in 60 s steps until the link came back
  (at 82 km, a minute later) and burned retrograde to ecc 0.6 -> **Ike orbit 33.7 x 523.5 km**. The contract completed
  at once: **funds 2.53 -> 3.53M**. Tooling: before an uncrewed burn, predict the link over the burn window (or at
  least fail loudly and retry when the link returns, instead of timing out).

## 2026-09-26 — Eve 1 home (Jeb): +620 sci; lab visits; a KSP crash
- Lab visits: UT 30.75M +498 (sci 2,118 -> 2,620), 33.0M +495 (-> 3,114); **31.88M and 34.1M transmitted nothing**
  (EC 2,056 / 2,102: the silent-fail threshold is between 2,102 and 2,425 EC); retried 34.1M after warping in sunlight to
  EC 3,176: -> 3,590. Rule until `lab transmit` checks it (4q): charge to > 3,000 EC first.
- KSP was found closed (kRPC connect timeout) after the lab script; restarted at UT 34,100,165, nothing lost (last save
  at the space center). Windows: commit 25.7 GB, nonpaged pool 1.52 GB (0.89 at session start: still rising).
- **Eve 1**: after UT 31.2M the game showed the Kerbin encounter as fable predicted (pe ~39 Mm): `correct` 3.6 m/s ->
  pe 28.5 planned, 1,809 km after the burn error; at UT 34.5M 3.2 m/s -> **pe 30.3 km** (no Mun on the way in).
  Reentry from v_inf 2,126 (collect_science: 0 new, 11 held in the pod), drogues 20 km at 771 m/s, landed in the
  Grasslands, **Jeb recovered: sci 3,594 -> 4,214 (+620), funds 3.61 -> 3.64M**.

## 2026-09-26 — Lab visit, research + Tracking Station 3, Moho 1 designed, Eve 2 in design (before a PC restart)
- Lab visit UT 35.47M (~63 days after the last: late, the lab sat at the 500 cap): EC 2,249 -> warped 1 h in sunlight to
  3,810, `lab transmit` (new: refuses < 3,000 EC, waits for the science) **+500, sci 4,214 -> 4,714**; `lab process`
  +100 data -> 723/750 (storage unit still holds ~1,000 data: magnetometer 366, gravity 400, EVA 200). Next visit
  **before UT 36.55M**.
- Research: heavyLanding, veryHeavyRocketry, advancedMotors, specializedElectrics (sci 4,714 -> 2,764). **Tracking
  Station level 3** (563k, DSN 250G). Funds 3.18M.
- Contract accepted: **Eve equatorial satellite** (302k): Eve, inc 0, ecc 0.05102, sma 18,868,437 m, LAN 0, argPe 330.23,
  deviation 5 %, Science Jr on the satellite (elements read from persistent.sfs SpecificOrbitParameter TargetBody 5).
- `window Moho` failed ("no window found"): Moho's eccentric orbit put the zero 137.5 d out, past the search end
  (synodic 135 d + 2): search 1.5 synodic periods. **Moho window UT 38,450,305**, flight 113 d. Windows: Eve 41,166,705,
  Dres 43,122,323, Jool 44,258,005, Duna 44,649,525.
- Tooling: `_await_link` in execute_node/manual_burn (wait for the CommNet link before ignition, pause mid-burn),
  untested in flight. fable warns: for a CAPTURE burn a pause loses the Oberth window; plan the pass so the link holds.
- **Moho 1** designed by fable (crafts/moho-1.json, docs/moho-1-plan.md): chemical, not Nerv (capture hyperbola e ~21:
  a ~2-min Oberth window; a Nerv would lose ~500 m/s). Twin-Boar / Skipper / Poodle / Terrier lander, 138.08 t, 80k.
  Budget from LKO ~5,200 (eject ~2,040, mid-course 200-400 at UT ~40,455,500, capture ~2,690 to 25 x 1,000 km) +
  landing ~1,200; margin ~600. **Pad check on the pad matched the plan** (1430 SL / 1198 SL / 3513 vac / 4218 vac),
  recovered (full refund). Pad photo was at night: redo in the sandbox (shoot_crafts.py).
- **Eve 2** designed by fable (crafts/eve-2.json, docs/eve-2-plan.md; 72 parts, 136.55 t, 105k, 7 stages): carrier =
  contract satellite (Poodle, RA-15 + 2 HG-55, Science Jr); lander with a 10 m inflatable shield and its own Terrier
  deorbit stage, released after the contract. Capture ~161-189 m/s to 120 x 19,131 km, pe raise ~444, match-orbit
  20-120. **The capture pe is on Eve's far side from Kerbin: link blocked from ~6 deg before pe -> the burn must END
  >= 25 s before pe.** Lander: retro 474 from the contract orbit, entry 4,456 m/s, ~465 sci. Code gaps listed in the
  plan (science --all, capture --early, vessel switch after staging, deorbit --at, shield inflate event, reentry
  science). Not yet verified: pad Δv/height (`launch`), inflate event, live transfer numbers (plan's OPEN list).
  Note: RA-15/RA-2 are fixed antennas (an earlier LOG line said "RA-15 opened": wrong).
- Records: writeup 7.19-7.24 (opus), career.json fixes, card 02 past-event ETA, cards rebuilt.
- Windows before the PC restart (KSP up ~6 h this run): commit 32.8 GB, nonpaged pool 1.57 GB, available 1.9 GB.

## 2026-09-26 — Moho 1 lost on ascent (reverted), Eve 2 pad check, code gaps for Moho 1 + Eve 2 (before a PC restart)
- KSP start after the PC restart: commit 18.6 -> 26.0 GB, nonpaged pool 1.18 -> 1.22 GB, available 3.1 -> 1.6 GB.
  Before this PC restart (KSP up ~1.5 h): commit 26.2 GB, pool 1.28 GB, available 2.4 GB.
- **Eve 2 pad check** (career pad, recovered, full refund): 1776 SL / 1526 SL / 3321 vac (plan 1775 / 1518 / 3287), height
  accepted. The lander's Terrier stage shows no Δv: KSP's calculator follows the root (carrier) side of the TD-12;
  part stats give 828 vac. Sandbox pad photos of Moho 1 and Eve 2 (daylight) cropped for the cards; the shield drum
  sits between the deorbit stage and the lander body as specified.
- Lab visits: UT 36.45M **+417** (charged 1 h to 3,810 EC first), UT 37.50M **+456** -> sci **3,636**; data topped up
  to 739 / 728 of 750. Next visit **before UT ~38.58M** (~10 sci/day, 500 cap).
- Code (opus): `science --all` (goo/Jr transmitted), EC-aware per-experiment transmit (charges in sunlight, waits for
  the science), capture never pauses/warps for a lost link + `capture --early S`, transfer T golden-section refine,
  `soi` refuses a predicted pe below terrain (`--force`), far-out `correct` re-reads the pe 60 s after the burn.
  Eve 2 gaps 3-6 (opus, worktree, merged): `switch NAME`, `deorbit --pe X [--at UT | --under Kerbin --sunward 30]
  [--plan]`, `inflate`, `reentry --science`; `_deorbit_now` no longer loops without thrust; reentry holds retrograde
  through the heat pulse even with pre-staged chutes. **Eve 2 sequence changes** (see docs/eve-2-plan.md "Lander
  sequence (code)"): after dropping the deorbit stage the SPENT Terrier stage stays active -> `switch "Eve 2 Probe"` again.
  None of this new code has flown yet.
- **Moho 1 launch #46 (UT 38,425,025): lost at 3:58, reverted to launch, recovered (full refund).** Pad numbers matched
  (1430 / 1198 / 3513 / 4218). Recorder: Twin-Boar staged at 15.5 km / 638 m/s, pitch 38; the Skipper (TWR 0.85) kept
  following the altitude pitch program (12 deg at 34 km) while the apoapsis crept 24 -> 38 km: the craft flew level at
  38 km, 2 km/s, the top OKTO reached 1206/1200 K and exploded (OX-STAT-XLs 1452 K). **Cause: ascent guidance** — phase 1
  has no time-to-apoapsis guard; earlier launchers staged higher so it never showed. **Fix (committed 7c10f00, untested):**
  above 12 km and inside the atmosphere, pitch += 1.5 x (45 - t_apo) when t_apo < 45 s (still clamped to AoA 15).
  Also my chain ran `circularize` after `ascent` exited 2 (`;` instead of `&&`): always chain flight phases with `&&`.
  The user spotted the explosion on screen while I waited for the background notice: poll the background output
  every minute or two during an ascent (read the file), don't only wait for the end.

## 2026-09-27 — Moho 1 flies (#47): ascent OK, ejection missed by 420,000 km (burn timing bug), fixed with 77 m/s
- KSP start (after a PC restart): commit 20.1 -> 24.9 GB, nonpaged pool 1.20 -> 1.19 GB, available 3.5 -> 1.6 GB.
  (`tools/install.sh` printed "KSP not ready" once: Steam was still starting; KSP came up a minute later.)
- **Moho 1 launch #47 (UT 38,426,090)**: pad 1430 / 1198 / 3513 / 4218 (as planned). Ascent with the new t_apo guard:
  pitch 27.7 at MET 120 (flight #46: 18.4), apoapsis 46.8 km at 3:00 (stop rule 45), Skipper out at 3:18 / 45 km; then
  the guard held t_apo ~45 s by flying almost level at 45-51 km (pitch 1-6, the Poodle at TWR 0.7): OKTO skin peaked
  **~880 K of 1200** at 51 km, then cooled on the coast. 79.3 x 79.6 km, **Poodle 2,961** (plan 2,950-3,050).
  The guard works but keeps a low-TWR stage in the upper air for ~2 min: fine for this craft, watch skin temps.
- Ejection (`transfer Moho --pe 25000 --plan`): T refined 113.3 -> 114.9 d, Moho **in our plane at arrival (no
  mid-course plane change, the 200-400 of the plan saved)**, node 2,040 (plan 2,030-2,060), arrival v_inf 3,652, pass
  retrograde (inc 142). Burned: Poodle 881 left, Sun pe/ap within 150 / 2,300 km of the plan, **but no Moho encounter**:
  closest approach 331,674 km, the ship ~420,000 km behind Moho along its path at arrival.
- **Cause (recorder): burn timing.** `burn_time` scaled the stage's burn time linearly with dv (2040/2961 x 253 = 174 s);
  the real burn was 196-204 s, and the half-dv point comes ~113 s after ignition (the craft gets lighter), not bt/2 = 87:
  the dv was centred ~26 s late, ~5 deg further round the 80 km orbit. **Fixed (1ccddd5):** mass-correct `burn_time`
  (propellant fraction), `burn_lead` = time to half the dv, used by execute_node / manual_burn / the capture link wait.
  Also a process miss: I read the command's "residual 0.2 m/s" as success and warped out of Kerbin's SOI before
  checking the encounter; inside the SOI the fix would have cost a few m/s. After any ejection: read the target
  encounter before leaving the SOI.
- `correct Moho --pe 25000 --inc-to 0 --plan` (no encounter, far out) planned **390 m/s** (v_inf 3,174, inc 98): not
  flown. The tuner has no dv term (old gap 4l). Scratch Lambert instead (projected onto our plane, like the planner):
  in-plane 76 m/s now (+10 d: 90, +20 d: 107) + ~7 plane later; the plane at arrival is only -92 km off.
  Built the node from the Lambert vector (almost pure radial-in, 76.95 m/s), fine grid +-0.12 m/s prograde/normal for
  pe 25-40 km and the prograde side (normal barely moves the pass from here: inc 56 or 137 only). **Burned: Moho pe
  1,056 km, inc 54 (prograde), Poodle 805.** Trim ~10 d before the SOI (~0.5-2 m/s, thrust-limited Poodle).
  Moho SOI ~UT 40,929,000.
- Minmus Lab visit (UT 38.48M): research drains EC (2,802 -> 1,150 in 1 h with the lab running): `lab stop`, charge
  30 min to 3,810, transmit **+420 -> sci 4,057**, `lab start`. Next visit before UT ~39.55M (~10 sci/day, 500 cap).

- Lab visits: UT 39.50M **+444** (sci 4,501), UT 40.45M **+412** (sci 4,913; the first transmit found no link and
  failed, the retry worked). Next visit before UT ~41.45M.
- **Trim 10 d out (UT 40.71M)**: my scratch grid +-1 m/s found nothing; the pass moves only ~200 km per m/s here. Local
  search with a dv term: 4.55 m/s -> pe 24.8 km, inc 61. `ksp node` (tol 0.2) left **pe 59.9** (0.2 m/s ~ 35 km).
  A second 0.16 m/s trim via my own python at 1 % thrust **went wrong**: the craft swung past 11 deg/s, the tumble guard
  cut and restarted the engine over and over for 400 s, my `timeout 400` killed the process with the throttle at
  0.68: Moho pe -87 km, ~10 m/s wasted. Lesson: burns only through the CLI (recorder), never a python one-off.
  Causes found: (1) kRPC's autopilot `time_to_peak` was (1,1,1) (its default; only ascent sets 5): the flexible stack
  swung +-20 deg even under SAS; 8 s settled a 110 deg turn to 0.5 deg in 30 s. (2) execute_node aimed in the node's
  own frame, which turns with the orbit being changed: the rate climbed ~1 deg/s per s in the last 5 m/s of every burn.
  **Fixes**: `ksp node --tol --thrust` (thrust limit restored + throttle 0 in a finally), execute_node sets
  time_to_peak 8 s during the burn and steers in the body's inertial frame (commits after 1ccddd5). Re-trim 1.0 m/s at
  5 %: **Moho pe 23.9 km, inc 69.8 (prograde)**. Merged opus's far-out `correct` (Lambert seed + dv-term grid;
  untested in flight).
- **Moho SOI (UT 40,929,000)**: pe 23.9, inc 69.8, 44 min to pe, signal 0.92. Link forecast (ray to Kerbin vs Moho's
  disc, positions from the patches): **blocked from pe-10 s to pe+130 s** — the second half of the capture burn.
  Early burns were no way out (a retrograde burn before the pe drags the pe underground; +300 m/s). **Raised the pe to
  175 km (70 m/s, 35 min before pe): ray clears Moho by >= 41 km.**
- **Capture**: `capture --apo 1000000` printed "~131 s, start 80 s before": KSP had no stage delta-v for the vessel
  ("Delta-v has not been calculated", after `fly` from the space center) so `burn_time` fell back to the Poodle alone;
  the real burn was 278 s (Poodle 694 + Terrier 2,293, half-dv 144 s after ignition). I stopped the command to rerun
  with `--early`, but it had already warped to the start: **117 s to pe**. Burned at once by hand (autopilot
  retrograde, full throttle, auto-staging, stop at ap < 1,000 km): **captured 38.7 x 999.6 km**, Terrier **1,843**
  (plan ~2,100: the late start cost the pe (175 -> 39 km) and ~150 m/s of Oberth, plus the 70 m/s pe raise).
- Science high (UT 40.93M) **+556**, circularize at pe 210 m/s -> **38.0 x 38.3 km** (no tumble: steering fix works),
  science low **+537**. Terrier 1,631.
- **Landing site with the link in view**: the far half of a 38 km orbit has no link, so the site search added Kerbin's
  elevation (> 20 deg at touchdown, > 10 deg 150 s before) to biome/slope: Midlands 56.9, -168.0. `land --at` took the
  pass one orbit earlier (1.4 km off, elevation 54-62). **Landed on Moho at 55.50, -169.24 (UT ~40.953M)**, upright,
  27/27 parts, Terrier **296 m/s left** (landing ~1,335). Surface science **+423 -> sci 6,432**. Funds 3.10M -> 3.40M
  (Moho firsts). Screenshot runs/moho1-landed.png (night side). **Moho 1 done: ~1,516 sci + ~300k funds.**
- Open: KSP's stage delta-v missing after `fly` (burn_time needs a multi-stage fallback or a forced recalculation);
  site finder with the link condition belongs in `land` (scratch site.py); link forecast for captures in code (plan
  gap 3a).
## 2026-09-27 (cont.) — delta-v fix in the mod, Eve 2 flies (#48 flipped, #49 up), Eve encounter
- Opus: `KspBot.RecalcDeltaV()` (mod) + `_burns_from_parts` multi-stage fallback in `burn_time`/`burn_lead`; `vessel`
  retries through the mod. KSP restarted at the space center to install it (commit 26.9 -> 25.7 GB, pool 1.26 GB both,
  available 0.76 -> 0.84 GB: little free RAM). Tested: after `fly "Moho 1"` the stage lines are there.
- Research: experimentalElectrics (RTG) + highPerformanceFuelSystems (S3 large tank): sci 6,432 -> 4,882.
- Records merged (opus): career.json #46/#47 + missing lab hauls, cards rebuilt (Moho added), writeup 7.25-7.27.
- **Eve 2 launch #48 (UT 41,150,000): flipped at MET 55, 8 km, ~335 m/s (transonic, q 24 kPa)**: the nose pitched up
  against the command (AoA -1 -> -15 -> -39 deg in 6 s), exactly the plan's ascent risk (blunt 2.5 m shield drum at
  the nose). Reverted to launch, recovered (full refund). Fix: 4 x Tail Fin on the S3-3600 at 45 deg to the AV-R8s
  (+0.5 t, 137.05 t, 76 parts). **#49**: transonic AoA <= 1.4 deg, rate <= 2 deg/s; 79.3 x 79.5 km, Poodle **3,321
  untouched**, Skipper 99 left (plan 150-250: the fins' mass/drag).
- Ejection: `transfer Eve --pe 120000 --plan`: T 190 d, node 1,026, arrival v_inf **1,103** (plan 850-950: capture
  ~224 instead of 161-189), Eve in plane. Burned (Skipper 99 then Poodle). Checked the Eve miss *before* leaving
  Kerbin's SOI this time: 34,000 km (SOI 85,109). Outside: **Eve pe 29,486 km, inc 34**, Poodle 2,390.
- `correct Eve --pe 120000 --inc-to 0 --plan` (opus's new far-out code): Lambert 7.9 m/s, but its seed "had no
  encounter" in KSP and the grid ended at 30.8 m/s with a RETROGRADE pass (inc 156): not flown. My local search
  (dv term) from the Lambert seed: 7.71 m/s "pe 120.1, inc 27.4" -> burned -> **actual pe 10,358 km, inc 2.8**.
  Cause (probable): 185 d out, KSP's encounter prediction for a *node's* trajectory differs by thousands of km from the
  patch of the real orbit after the burn (and 0.04 s is too short for the patches to settle between evaluations:
  runs gave inconsistent costs). Far-out fine trims are meaningless here: trim ~20 d before the SOI (~8 m/s est.).
  Eve SOI ~UT 45.17M, pe ~45.30M.
## 2026-09-27 (session 3) — code fixes merged, Dres 1 designed, lab visit, Mun Sat 1 and a stale contract system
- Merged (opus, offline tests in tests/test_offline.py): `correct` far-out compass search (0.3 s settle, dv term, side
  penalty, dv cap); `capture` link forecast (moves the burn earlier before a Kerbin blackout); `deorbit` pe ground point +
  Kerbin/Sun elevation + refusal < 20 deg, `release_ut` sunward sign; `land --science`. Dres 1 designed (fable):
  crafts/dres-1.json, docs/dres-1-plan.md; pad check matched exactly (1177 SL / 1045 SL / 2742 / 3683), recovered.
- Lab visit UT 42.35M: +400 (sci 5,671); research propulsionSystems (Spark/Ant) -> 5,581. Accepted "Science data from
  surface of Eve" (Eve 2 lander). CommNet Require Signal is already ON in the save.
- **Mun Sat 1** (crafts/mun-sat-1.json = Keo Relay 3 + goo/magnetometer/accelerometer) for "specific orbit of the Mun"
  (inc 146.04, e 0.181, sma 803 km, LAN 275.9, argPe 177.9, 3 %): LKO 85 x 87 (the ascent coasted to 80 km and the
  Swivel circularized with 1,091 m/s); `transfer Mun --pe 458000` 874 (plan 852) -> pe 453 km, inc 174 retro.
  `correct Mun --inc-to 146` planned a 370 m/s 180-deg flip (near-path seed still assumes a half turn): not flown.
  `capture --apo 748750`: **first link forecast in flight**: Kerbin hidden from pe -183 s -> burn moved 216 s earlier,
  225 m/s -> 429 x 778 km. `match-orbit` plane 34.6 deg 165.5 (plan 167) + 16 + 19 -> argPe still 195.7 (17.8 off);
  rotated the apsides by hand (node from a script, 16 m/s radial at the orbits' intersection; the pe-side one had no
  link -> `node` refused, used the ap-side one), pe trim 1 m/s: all elements inside KSP's windows (checked against the
  decompiled VesselUtilities.VesselAtOrbit). **Contract never completed: the save held both Mun contracts as Offered**
  while kRPC listed them active and the advances (70.9k) had been paid. Cause: a stale ContractSystem after the lab
  flight's FLIGHT -> SPACECENTER switch (the offered list had changed completely too). A KSP restart cleared it (memory:
  commit 27.2 -> 25.7 GB, pool 1.31 GB, available 454 -> 778 MB). Mun Sat 1 (launchID 79) can't satisfy a contract
  accepted now (VesselLaunchedAfterID), and a re-accept would pay the advances twice: both Mun contracts skipped, the
  70.9k windfall noted here. Mun Sat 1 stays as a Mun relay (RA-2, 4,264 m/s). Fix: `accept` now compares the save's
  Active count with kRPC's and errors on a mismatch.
- Merged (opus): `correct` near-path seed (rotation about the line to the target, both ways, capped; Mun 174->146 now
  ~82 m/s offline instead of the 370 flip) and `match-orbit` argPe placement by the target periapsis direction + a final
  shape-keeping apsides turn at the intersection that has the link; `match-orbit --window` (Eve contract: 5).
- **Dres 1 launched** (UT 43.09M): ascent clean (ap 47 km at 3:00, AoA <= 3.0 at staging), 79.4 x 79.6 km, **Poodle
  1,759** (plan 1,500-1,650), Terrier 3,683. `transfer Dres --pe 40000 --plan`: 1,590 (plan 1,600-1,620), T 744 d,
  arrival v_inf 1,490, Dres +1,332 Mm out of plane (by design), mid-course ~116 m/s at **UT 56,159,878**. Burned on
  the Poodle alone (160 left). Sun orbit 13.34 x 42.70 Gm (plan 42.74). Arrival ~UT 59.19M.
- Lab visit UT 43.37M +441 (sci 6,022; storage unit empty: `lab process` added nothing). Research unmannedTech,
  composites, advMetalworks, ionPropulsion -> sci 4,572. Contract sync check after the scene switch: 6 = 6.
### Next steps (plan)
**State (2026-09-27, session end): KSP at the space center, UT ~41.40M, funds 3.30M, sci 5,270, rep 543.
In flight: Eve 2 (#49) cruising to Eve: SOI ~UT 45.20M, pe ~45.30M; Eve pe 10,358 km, inc 2.8, Poodle 2,390, lander
attached. Moho 1 landed (done). Jool 1 cruising (SOI 52.79M). Minmus Lab 1 (Bob, Gwenbro) running.
Timeline:** lab visits before UT 42.40M / 43.40M / 44.40M (`lab stop`, charge to 3,810, `lab transmit` (retry after
20 min if "no science arrived": link), `lab process`, `lab start`); **Duna 2** (crafts/duna-2.json, docs/duna-2-plan.md,
pad check matched 1436/1549/2466/1947) launch ~UT 44.63M for the window 44,649,525; **Eve 2 trim ~UT 44.77M** (20 d
before the SOI): scratch local search with a dv term (see LOG 2026-09-27 cont.), settle >= 0.3 s per evaluation,
target pe 120 km, inc < 5; inside the SOI a link forecast for the capture (scratch occl.py pattern: vessel position
from the patch in Eve's frame, Kerbin from orbits in the Sun frame) and `capture --apo 19131000 --early S` so the burn
ends >= 25 s before any blackout; then docs/eve-2-plan.md phases (pe raise, match-orbit, lander sequence).
Code to fix before they bite: `correct` far-out (opus's Lambert seed "no encounter" + grid chose a retrograde pass;
`_node_cost` 0.04 s settle is too short far out); `land` site finder with a Kerbin-elevation condition (scratch
site.py); capture link forecast in code; `land_atmo --science` (Duna 2 plan gap 1).
Records TODO (opus): career.json #48 (Eve 2 flipped at Mach 1, reverted) and #49 (Eve 2 flying); Duna 2 photo.

**State (2026-09-26, before a 2nd PC restart): KSP saved at the space center, UT 38,425,858, funds 3.18M, sci 3,636,
rep 528. Nothing in flight needs attention; no burns pending. Moho 1 is NOT flying (reverted + recovered, craft file
unchanged). Next: relaunch Moho 1 at once (window UT 38,450,305 is ~24,000 s away: fine); watch the ascent's new
t_apo guard (expect apoapsis rising steadily after the Skipper takes over, no flat flight at 38 km; stop rule: any
`damage`/`attitude` event or apoapsis < 45 km at 3:00 -> revert). Then transfer per docs/moho-1-plan.md.
Lab visit before UT ~38.58M (during Moho cruise: `scene space_center`, `warp-sc`, `fly "Minmus Lab 1"`).
Record TODO (opus): career.json launch #46 Moho 1 (result reverted, note: OKTO overheated in a flat ascent), then
#47 for the reflight; cards; writeup (current through 7.24).**
Older state (before the first PC restart, kept for reference):
State (2026-09-26, before a PC restart): KSP saved at the space center, UT ~35.476M, funds 3.18M, sci 2,764, rep 528.
All crews home except Bob + Gwenbro (Minmus Lab 1). No burns pending, nothing in flight that needs attention.
Timeline (UT): **lab visit before 36.55M** (then every ~1.08M, charge > 3,000 EC first); **Moho 1 launch for the window
38,450,305** (warp from the space center; launch ~1 day before, don't wait days in LKO: 8 real hours at 100x);
**Eve 2 window 41,166,705**; Dres 43.12M; Jool 44.26M; Duna 44.65M (Duna surface science contract open);
**Jool 1 Jool SOI 52,787,080** (pe -655 km, inc 15.9: trim pe to 250 km inside the SOI, then `capture --apo 100000000`
~445 m/s; docs/jool-1-plan.md).
Before Moho 1 flies, fix (docs/moho-1-plan.md "code gaps"): `science --transmit` skips goo/Science Jr (one-way probes
lose them: add `--all`), transmit EC guard 120 EC vs ~1,000 per set, transfer_planet's 2 % T grid (golden-section
refine, ~170 m/s), refuse to warp into a sub-terrain periapsis after a far-out correct. Then Eve 2's gaps (its plan:
capture --early, vessel switch, deorbit --at, shield inflate, reentry science) and its pad check.
Jool 1 (uncrewed, ~4,540 m/s) cruising. Ike Station 1 in Ike orbit 33.7 x 523.5 km, ~920 m/s (contract done).
Minmus Lab 1 (Bob, Gwenbro) 723/750 data. Keo Relay 3 spare (4617 m/s) in keosynchronous orbit.
Active contracts: Eve equatorial satellite (Eve 2), Duna surface science, Minmus temperature survey (will lapse), two
part-recovery contracts (skip, small parts rule). Offered: Gilly station (12 kerbals, ISRU, 6,000 LF: 1.25M), Sun
orbit probe, Minmus outpost, Kerbin polar satellite, Minmus satellite repair.
Crew at KSC: Jeb, Valentina, Daphrick (scientist), Bill, Elfry (engineers), Mitbro, Jedgard (pilots), Barzor.
0. CLAUDE.md "How to decide": expected numbers incl. real time before each phase; --plan for big burns.
1. (done: Duna 1 home.) Duna surface science contract still open (needs surface data from Duna: Ike Station can't).
2. (done: Eve 1 home, +620 sci.) Old plan text: **Eve 1 return** (fable's plan, see Rescue 5 entry): `depart Kerbin --pe 30000 --plan` (expect "pe pass UT
   29029189 ... tilt ... 105 m/s + ejection 215 = 320"; tilt at the apoapsis UT 28,925,295, dry-run v_inf error
   < ~5 m/s) -> node; then `depart Kerbin --pe 30000 --at 29029189 --plan` (~215 m/s, encounter) -> node; after the
   SOI exit `correct Kerbin --pe 30000` (a few m/s); reentry at ~3.9 km/s: pod-side goo/thermo/baro hold ~385 sci:
   before entry measure hatch-to-part distances; if <= 1.5 m, EVA "Take Data" into the pod.
3. **Lab station**: flying (Minmus Lab 1). Visit every <= 50 days: `ksp fly "Minmus Lab 1"`, `lab status`, `lab transmit`,
   top up with `lab process` when dataStored drops (storage unit has ~1,500 lab data). Later: a ferry with a docking
   port to swap scientists (levels rise only on recovery) and bring home the storage unit's data.
4. Tooling fixes found in the 2026-09-26 Q&A with the user (do before they bite again):
   a. (done: the CLI already exits 1/2/3; the chains ran on because of `| tail` pipes: use `set -o pipefail` or no pipes)
   b. (partly done: warp_to prints the real-minute estimate from the rails cap when > 5 min) Real-time guard for waits: warp_to should estimate real minutes from the rails-warp cap at the current
      altitude; long waits in a low orbit (Minmus 22 km: 8.2 d took 36 real minutes) -> raise the orbit first
      (Mun: 400 km, fast) or at least say it. Lesson is only in LOG so far.
   c. Moon-to-moon transfers in code: transfer_planet from a moon matches the velocity at the SOI edge, wrong for
      small SOIs (Mun: 2mu/r_SOI ~ v_inf^2) -> for moons use a closest-approach tune seeded with the analytic
      ejection (Survey 1's scratch: 161 m/s, worked); from a polar moon orbit wait for the plane alignment (twice
      per moon orbit) — same for `return` from polar orbits (Minmus: 365 vs 160 m/s).
   d. Science bookkeeping check in do_science: after each collect, verify the storage count rose by the number of
      new data; the cause of Minmus Science 1's lost surface materials is still unconfirmed (hypothesis: the
      printed "100" was orbit data re-listed, the surface runs never happened/stored).
   e. tools/biometour.py -> a CLI command (`eva-tour`); the report title can lag the real subject.
   f. Moon return burns end with Kerbin pe +6 km every time (MS2, Survey 1): find the bias (finite burn?).
   g. aim-point seed + tuner stops short of the wanted inclination (73 of 90 at Eve): weight inc vs pe.
   h. burn_at with control "none" (no CommNet link) waited out the whole burn at throttle 1 / thrust 0 (Minmus Lab 1):
      refuse before the burn, extend antennas automatically after launch (deployable HG-55/DTS need extending).
   i. capture from a hyperbola just after the periapsis: time_to_periapsis points to the past -> burn now instead.
   k. Solar panel deployment in the flight code (after LKO, like the antennas); Ike Station 1 needs its Gigantors.
   j. EVA kicks from the MPL (~0.08 m/s, 6 deg/s): eva out should turn the station's SAS on first and wait; near an
      apoapsis re-check the periapsis after every EVA.
   l. `correct` far out: the aim-point seed crashed (all 36 tries lost the encounter, best None: now falls back) and the
      plain tuner walks off to 80 m/s (its step grows 1.5x per success and the cost has no dv term): add a dv term / cap the step.
   m. (done: the "pad check" is the pad-area debris sweep, flight-scene only; now it just runs only in flight)
   n. (done: `transfer` to a moon refuses when the moon will be > 0.8 SOI out of our plane at arrival and names the
      day offset of the next good departure; Rescue 6's tuner had planned a 1094 m/s escape path)
   o. (done: kill_relative / approach / grab call _ensure_control first)
   p. (done: execute_node/manual_burn wait for the link before ignition and pause mid-burn; untested in flight) Uncrewed burns: the link can drop during the wait/burn (Ike capture): re-check control right before ignition,
      and if it's lost, wait for it (warp in small steps) up to a deadline instead of burning into the timeout.
   q. (done: refuses under 3,000 EC, waits for the science to arrive, exits 1 if nothing comes) `lab transmit`: check EC >= ~2,000 first and wait until science rises (a transmit with 1,793 EC did nothing).
5. Precision landing to within 500 m (`land --at` exists but only picks the closest pass, ~2 km): targeted
   deorbit timing + horizontal correction in the descent, short hops — needed for surface survey contracts.
6. Small: `contracts` parameter display (kRPC completed flag); duplicate vessel names (kRPC picks one).
7. Long-term (user): Duna + Ike, refuelling station (docking), relay constellation, Eve landing, Moho, Jool.
