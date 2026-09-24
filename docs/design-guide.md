# KSP 1.12 Career Rocket Design Guide (Stock, First Launch → Crewed Minmus Return)

## 0. Lessons from our own flights (highest priority — verified in this game)
- **TD-12 stays with the LOWER stage** when fired. The part above keeps nothing. (Sounding 2)
- **Science parts on the pod's side overheat on reentry** (goo/thermometer explode at 1200 K, data lost),
  even from LKO. Transmit their data before reentry, or mount them in the heat shield's shadow. (Orbiter 1)
- **No-gimbal first stages (SRBs) cannot pitch at high dynamic pressure**; the pod's reaction wheel is
  too weak against fins. Pitch over early (ascent turn_start 250 m, ~60 m/s) and let it follow prograde.
  A 3-Thumper cluster stayed at 87° pitch up to 14 km with target 73° → 2 km/s circularization. (Minmus Flyby 1)
- **SRB clusters without radial decouplers work well**: side Thumpers surface-attached directly to the core
  Thumper, all burn out together and drop with one TD-12 below the next stage — no separation collisions.
- Radial Thumpers ×4 on radial decouplers around a 1.25 m core destroyed the core at separation (sandbox).
- Maneuver nodes need **Tracking Station lvl 2** (not only Mission Control lvl 2); `burn_at` falls back
  to manual burns when nodes are locked.
- **SRB-first stacks need stiffness**: a 45 t 4-Thumper stack under a long upper stack had its thrust ~0.4° off the
  pod axis, giving 26 kN·m of torque against the Mk1's 5 kN·m wheel. It fell over in 8 s (two crashes, Jeb lost). Put `"rigid": true` and
  `"autostrut": "Root"` on the stack parts. Measure it on the pad before flying: sum of thruster positions × directions
  about the CoM (`thruster.thrust_position/direction(v.reference_frame)`) against `v.available_torque`. (Minmus Lander 1)
- **Never autostrut surface-attached side boosters**: the cluster breaks at spawn ("Structural failure on linkage", crew killed on the pad). Stack parts: rigid + autostrut Root is fine; side boosters: rigid only.
- **Proven heavy lifter (Mun Lander 2)**: 3 Kickbacks (sides rigid), 4 AV-R8 on the core's base, 2 inline wheels, Swivel + 4×FL-T400 → ~13 t to LKO with the upper stage full. The fins make the pitch-over controllable.
- Pad science: a pod with goo/thermo/baro/Science Jr on the pad gives ~18 science, risk-free.
- Don't make an uncontrollable rocket pitch over with a deliberate CoM offset: the torque grows as the SRBs burn down and flipped Mun Lander 1 (Jeb lost). Heavy SRB stacks (90 t, MoI ~6e6) need real authority (inline reaction wheels, AV-R8 fins).
- Capsule reentry: nothing heavy/draggy stacked under the pod without a heat shield at the very bottom, and always drogues. Pod + Science Jr flipped nose-first and hit the chute window at 960 m/s (Sounding 3, Bill lost).
- LT-05 legs: attach at tank height −1.05 (just past the FL-T400 bottom) → feet 25 cm below a Terrier bell.
- **EVA (KspBot `eva out|report|board`)**: the Mk1 pod hatch faces builder `angle: 90`. Any radial part there (or parts on all four sides) → "All hatches are obstructed". After exiting, the kerbal hangs at the hatch ("Ladder (Idle)", inside the airlock trigger), so EVA report and surface sample work from there and boarding back is legitimate right away. EVA data goes into the pod on boarding. Flags need ground contact (and a way back to the hatch), so not done yet. Surface sample worked on the KSC pad at R&D 1. (sandbox, Mun Lander 4)
- **EVA from a landed lander is dangerous**: deployed LT-05 legs near the hatch side knock the kerbal (Ragdoll on Kerbin; flung at ~1400 m/s in Minmus gravity, once also breaking the lander apart). EVA in orbit / with legs retracted is clean. Keep legs and radial tanks away from the hatch (angle 90) and verify on the ground in the sandbox before any landed EVA. (Mun Lander 5/6)
- Drogues alone do not slow a Mk1 pod below ~110 m/s at 6–9 km (Mk16 test contract window missed).

Numbers are stock KSP 1.12.x values pulled from the KSP wiki/forums (see Sources). `(?)` marks
figures that are community consensus but not verified against a primary in-game readout for
this doc. Always trust the in-game VAB Δv/TWR readout over any number here when they conflict.

## 1. Radial boosters: why they hit the core, and how to not do that

### Root causes (mechanism, not folklore)
- A radial decoupler almost always sits **below the booster's center of mass**. On separation
  this creates a **torque that rotates the booster inward** (nose swings away, tail/base swings
  toward the core). If the booster's engine has already burned out, the rocket clears this
  inward swing fast enough. If the engine is **still firing**, thrust keeps pushing the
  tilted booster back into the core — this is the single biggest cause of core-engine kills.
- SRBs (Flea/Hammer/Thumper/Kickback) **cannot be shut off**. You can only control *when* you
  decouple, never *when thrust stops*. Staging on a fixed altitude/time guess instead of actual
  burnout is a common mistake.
- Near-empty booster stages are light → high residual acceleration → they can **out-accelerate**
  and overtake the core after separation even without thrust, especially with a decent ejection
  force pushing them radially into the free-stream.
- High dynamic pressure (near max-Q, roughly 10–15 km altitude / ~25–40s into a typical stock
  ascent (?)) means drag differentials between core and boosters are large and unpredictable —
  a bad separation here is more violent than one at 20+ km.
- **Crowding**: mounting N boosters of diameter ≥ core diameter around a small core leaves almost
  no radial clearance. Four 1.25 m Thumpers around a 1.25 m FL-T800 core (this is effectively
  the reported failure case) means booster skins nearly touch the core skin — the decoupler's
  ejection force has to overcome torque, drag, *and* near-zero lateral clearance simultaneously.
  Thumper burn time is 35.2 s (1 atm) / 42.2 s (vacuum); staging at ~42 s on a mixed-altitude
  ascent is close to the *vacuum* burnout time, so a fixed-time stage plan risks either firing
  boosters (if actual local burn time is longer, e.g. deep atmosphere at low speed) or coasting
  dead boosters through a too-tight gap (if already burned out) — both fail when clearance is this
  small, so timing alone does not fix a crowding problem.

### Concrete rules
1. **Stage strictly after burnout, not on a fixed timer.** In a flight script, decouple when the
   booster's measured/derived thrust ≈ 0 (or `resources.solidFuel == 0` for that part), plus a
   ~1–2 s margin, rather than a hardcoded second count.
2. **Booster count vs core size**: on a 1.25 m core, use **at most 2** radial SRBs of Hammer/Thumper
   class. For 3, go to a 1.875 m core. For 4+, go to a 2.5 m core (Skipper/Poodle class) or split
   the boosters into two separate decouple events (2+2) a couple seconds apart so each pair has
   room. Prefer **pairs in symmetry (2, 4, 6)** over odd counts for CoM/CoP balance, but treat
   "4 boosters on 1.25 m" as *inherently marginal* regardless of timing — upsize the core first.
3. **Mount the radial decoupler as high as possible on the booster** — near or above the
   booster's own center of mass, not at its base. This minimizes/reverses the inward-torque
   effect described above; several experienced builders explicitly offset the booster upward on
   the decoupler attach node for this reason.
4. **Keep the booster's nozzle at or above the core engine's nozzle position** (don't let
   boosters hang lower than the core engine) — this way if a booster does drift inward, the core
   engine is already "below/past" it and clear.
5. **Nose cones on every booster.** Reduces drag-induced tumbling and gives the booster a cleaner
   aerodynamic separation once nose-first orientation reasserts itself.
6. **Add Sepratrons** radially on the booster (angled slightly outward/away from the core, not
   straight radial) for guaranteed positive separation Δv, especially once boosters exceed ~4-5 t.
   This is the standard stock fix when ejection force + torque isn't reliable.
7. **Roll or angle the decoupler mounts so boosters are offset from the pitch plane**, and prefer
   separating at low pitch (near-vertical, before or after the bulk of the gravity turn) — pitching
   hard *during* booster burn increases the chance a booster swings into the flight path.
8. **Prefer serial/stacked staging over many radial parasites when the core is small.** A single
   larger stacked SRB (e.g., one Kickback below the core, decoupled straight down) or a 2-booster
   radial layout on a wider core is more reliable than 4 crowded radial boosters on a 1.25 m stack.
9. Reduce ejection-force risk by testing: symmetric decouplers should have **Ejection Force**
   cranked up (multiples of 10 N) in the tweakable — low default force is often insufficient once
   a booster is anything but nearly-empty.
10. Sanity-check mass budget before trusting a crowded design: 4× Thumper (7.65 t each = 30.6 t)
    plus an FL-T800 core (~4.5 t wet (?)) is already ~35 t+ — this exceeds the **Launch Pad level 1
    limit of 18 t**, so a design like this is only flyable after a Launch Pad upgrade; if still at
    level 1, the part count/mass limits force fewer/smaller boosters anyway (see §6).

## 2. Ascent stability

- **CoM vs CoP (Center of Lift)**: for aerodynamic stability the CoP must sit **behind (toward
  the tail from)** the CoM — like fletching on an arrow. If CoP is ahead of CoM, the rocket is a
  "reverse dart" and will flip once dynamic pressure builds.
- **Fins go at the bottom**, near the engine(s). They pull CoP rearward. Long, thin, finless
  rockets are the classic flip-on-ascent failure — add Basic Fins / AV-T1 winglets near the tail
  until CoP is clearly behind CoM in the VAB overlay.
- As fuel drains, CoM shifts (usually forward, toward the nose, for typical tank/engine stacking)
  — keep a stability margin at launch, not just a marginal pass, since it will get tighter through
  the burn on some designs.
- **Liftoff TWR target: 1.3–2.0** (stock cheat-sheet consensus; most stock rockets fly at
  1.5–2.0 off the pad). TWR < 1 means it will not leave the pad at all. TWR significantly above
  2.0 wastes fuel to drag/dynamic pressure and stresses the vehicle/crew.
- **Throttle near max-Q**: if TWR is high (>2), consider throttling back approaching max
  dynamic pressure (roughly 10-15 km on a typical stock ascent (?)) to reduce drag losses and
  structural stress, then throttle back up once through the thick lower atmosphere.
- **Gravity turn rule of thumb**: start pitching over at ~50–100 m/s (below ~1 km), tip 5–10°
  off vertical toward the east, then **follow the prograde marker** rather than hand-flying a
  pitch program; aim to be ~45° pitch by ~10 km and near-horizontal (prograde) by ~45 km, with
  apoapsis raised to ≥70 km before the core stage runs dry.
- **Heat**: reentry from LKO is mild; reentry from Mun/Minmus transfer speeds is hotter — carry
  an ablative heat shield for crewed Mun/Minmus return capsules, and keep periapsis in the
  35–45 km band on the final approach so aerobraking/reentry heating is gradual rather than a
  single deep dip.

## 3. Staging, sizing, and stock engine roles

| Engine | Type | Mass (t) | Cost | Thrust atm/vac (kN) | Isp atm/vac (s) | Tech node | Role |
|---|---|---|---|---|---|---|---|
| RT-5 "Flea" | SRB | 1.5 (0.45 dry) | 200 | 162.9 / 192 | 140 / 165, burn 7.5/8.8s | Start | tiny sounding-rocket booster |
| RT-10 "Hammer" | SRB | 3.56 (0.75 dry) | 400 | 197.9 / 227 | 170 / 195, burn 20.7/23.7s | Basic Rocketry | small booster, cheap first orbital attempts |
| BACC "Thumper" | SRB | 7.65 (1.5 dry) | 850 | 250 / 300 | 175 / 210, burn 35.2/42.2s | General Rocketry | mid booster, longer burn |
| LV-T30 "Reliant" | LFE | 1.25 | 1100 | 205.16 / 240 | 265 / 310 | General Rocketry | no gimbal — first-stage/booster-cluster core only |
| LV-T45 "Swivel" | LFE | 1.5 | 1200 | 167.97 / 215 | 250 / 320 | Basic Rocketry | 3° gimbal — default core/first-stage engine, gives control |
| LV-909 "Terrier" | LFE | 0.5 | 390 | 14.78 / 60 | 85 / 345 | Advanced Rocketry | vacuum-optimized — upper stage, **default Mun/Minmus lander engine** |
| RE-L10 "Poodle" | LFE | 1.75 | 1300 | 64.29 / 250 | 90 / 350 | Heavy Rocketry | large vacuum upper stage |
| RE-I5 "Skipper" | LFE | 3.0 | 5300 | 568.75 / 650 | 280 / 320 | Heavy Rocketry | mid-size atmospheric booster |
| 48-7S "Spark" | LFE | 0.13 | 240 | 16.56 / 20 | 265 / 320 | Propulsion Systems | tiny probes / micro landers |

- **Design targets**: first/booster stage TWR 1.3–2.0 at liftoff; upper/vacuum stage TWR ≥ 0.8–1.0
  is fine since there's no gravity-loss urgency in vacuum coast, but a **lander stage should have
  local-body TWR ≥ ~1.5–2** for a controllable powered descent (Mun g ≈ 1.63 m/s², so ~2.5–3 m/s²
  of deceleration min; Minmus g ≈ 0.49 m/s² is very forgiving — even a Terrier is heavily
  overpowered there).
- Reliant has **no thrust vectoring** — never use it as your only core engine unless fins/RCS/
  reaction wheels provide all control authority; Swivel's gimbal is the safer default for a
  single-engine core.
- Level 1 facility caps (see §6 for costs): **VAB 30 parts, Launch Pad 18 t / 20 m tall / 21.2 m
  wide.** Design your first few rockets under these caps — a 4-SRB cluster like the failure case
  in §1 already blows the mass cap and needs a Launch Pad upgrade regardless of the aero fix.

## 4. Delta-v map (stock Kerbin system)

| Leg | Δv (m/s) | Notes |
|---|---|---|
| Kerbin surface → 80 km LKO | ~3400 (real ascents often cost 3900–4500 with gravity/drag losses) | depends heavily on TWR/AoA discipline |
| LKO → Mun transfer (Hohmann) | 860 | raises apoapsis to Mun's orbit |
| Mun transfer → low Mun orbit (capture) | 310 | circularize at periapsis |
| Low Mun orbit → Mun surface (land) | 580 | more in practice unless suicide-burn-precise |
| Mun surface → low Mun orbit (ascend) | 580 | mirror of landing |
| Low Mun orbit → Kerbin reentry | 310 | Kerbin atmosphere does the rest (aerocapture) |
| LKO → Minmus transfer | ~800–1000 (?) | similar order of magnitude to Mun transfer |
| Minmus transfer → low Minmus orbit (capture) | ~160 (?) | much cheaper than Mun due to low g |
| Low Minmus orbit → Minmus surface (land) | 180 | |
| Minmus surface → low Minmus orbit (ascend) | 180 | |
| Low Minmus orbit → Kerbin reentry | 160 | |

- Minmus **lander-only** budget (orbit→land→orbit→return): 180+180+160 = 520 m/s, **+10% margin
  ≈ 572 m/s** — this is why a Terrier + small tank lander is so cheap on Minmus vs. Mun.
- Margin guidance from experienced players: add **10–20% on top of textbook Δv** for piloting
  error, plane-change corrections, and imperfect burns; some suggest 20–40% for less experienced
  ascent profiles.
- On the return leg you generally do **not** need a full Δv for reentry — Kerbin's atmosphere
  aerocaptures/aerobrakes you if periapsis is set to ~35–45 km, saving the "second half" of the
  outbound Δv.

## 5. Minmus-specific lander notes

- **6° inclination**: Minmus orbits ~6° off Kerbin's equatorial plane. Correct inclination either
  (a) cheaply during the Kerbin-departure burn by biasing normal/antinormal into the ejection
  burn, or (b) after capture, at the ascending/descending node of your orbit relative to Minmus'
  orbital plane, using a normal/antinormal burn. Matching inclination *before* the SOI transfer
  (not after) is generally cheaper and simpler to plan with maneuver nodes.
- **Landing site**: pick a flat biome (e.g., the "Greater Flats"/"Flats" biomes) for a safe
  touchdown and an easy powered ascent — Minmus' terrain is far gentler than Mun's craters/hills.
- **Lander design for low gravity (0.49 m/s²)**: a Terrier is comfortably overpowered here, so
  favor **more control authority and stability over raw TWR** — wide-stanced landing legs (3–4
  legs, e.g. LT-05 Micro Landing Struts), a **low CoM** (mount tanks/engine low, probe core/battery
  low), and enough SAS/RCS to null horizontal velocity before final descent. Low local gravity
  means it's forgiving of imperfect suicide burns but easy to tip over on a narrow base.
- **Descent profile**: null horizontal velocity while still high (burn retrograde until roughly
  vertical descent), fall to ~2 km, then burn to bring vertical speed under ~20 m/s, throttle down
  for a gentle touchdown under ~3 m/s.
- **Return/reentry**: an ablative heat shield is recommended but not strictly required for a
  Mk1 pod if control surfaces manage a shallow reentry AoA; standard practice is heat shield +
  Mk16 (or Mk16-XL for heavier pods) parachute, deployed only once the parachute readout says
  "safe" and generally under ~1000 m altitude for reliability.

## 6. Career progression toward a crewed Minmus landing

### Tech tree order (node: cost in science → key unlocked parts)
1. **Start** (0): Mk1 Command Pod, RT-5 Flea SRB, Mystery Goo, Mk16 Parachute, EVA/personal chute.
2. **Basic Rocketry** (5, needs Start): LV-T45 Swivel, RT-10 Hammer SRB, FL-T100 tank.
3. **Engineering 101** (5, needs Start): TD-12 stack decoupler, 2HOT thermometer, antenna.
4. **Survivability** (15, needs Engineering 101): heat shields (0.625/1.25 m), **LT-05 Micro
   Landing Strut** (cheap early legs), PresMat barometer.
5. **Stability** (18, needs Basic Rocketry or Engineering 101): **TT-38K radial decoupler**,
   aerodynamic nose cone, AV-T1 winglet — this is the node that unlocks radial boosters at all.
6. **General Rocketry** (20, needs Basic Rocketry): LV-T30 Reliant, BACC Thumper SRB, FL-T200 tank.
7. **Advanced Rocketry** (45, needs General Rocketry): **LV-909 Terrier** (the Mun/Minmus lander
   engine), FL-T400 tank, Mk-55 Thud.
8. **Fuel Systems** (90, needs Advanced Rocketry or General Construction): FL-T800 and Rockomax
   X200 tanks — bigger cores.
9. **Heavy Rocketry** (90, needs Advanced Rocketry): Poodle, Skipper, Kickback SRB — only needed
   once payloads grow past what Swivel/Reliant clusters comfortably lift.

Minimum practical path to a crewed Minmus round trip: **Start → Basic Rocketry → Engineering 101
→ Survivability (legs+shields) → Stability (radial decoupler+fins) → General Rocketry
(Reliant/Thumper) → Advanced Rocketry (Terrier)**. Fuel Systems and Heavy Rocketry are
quality-of-life, not hard requirements — a Terrier + FL-T400 stack lander is enough for Minmus.

### Cheap early science
- **Biome-hop without leaving the ground**: the Launch Pad, Runway, KSC grounds, surrounding
  land, and the adjacent sea each count as **separate biomes**. Crew Report + EVA Report +
  Mystery Goo + (later) Materials Bay at each = free science with zero flight risk.
- Suborbital hops from KSC reach nearby biomes (Grasslands, Shores, Highlands, Mountains, Desert)
  cheaply — repeat the same experiment suite in each for more science per part unlocked.
- A Scientist kerbal can **reset (clean) Goo/Materials Bay** experiments in the field for reuse,
  avoiding the need to carry multiples.
- Prioritize **crew reports + EVA reports** (free, no part cost) over instrument science early —
  they're pure profit once a kerbal can leave the capsule.

### Contracts
- Early "launch/build/test a part" and "reach altitude/orbit X" contracts are reliable, low-risk
  funds+science. **Avoid contracts requiring a part test under a narrow flight condition** (e.g.
  specific altitude+speed window for a specific part) — community consensus is these pay poorly
  for the dedicated-launch effort they demand.
- Getting off Kerbin (orbit, then Mun/Minmus) is worth far more science per mission than
  Kerbin-surface-only contract grinding — treat early Kerbin contracts as funding for the first
  orbital/Mun/Minmus vehicle, not as an end in themselves.

### Facility upgrades (exact costs, level 1→2)
| Facility | L1 limit | L2 cost | L2 unlock | Priority |
|---|---|---|---|---|
| Mission Control | 2 active contracts, **no maneuver nodes** | 75,000 | **flight planning (maneuver nodes)**, 7 contracts | Buy first — you cannot reliably fly precise Mun/Minmus transfers without maneuver nodes. |
| Astronaut Complex | 5 kerbals, EVA/flag **unavailable** away from KSC | 75,000 | 12 kerbals, EVA+flag planting away from KSC | Buy before a crewed landing — needed for surface EVA/flag science and reports on Mun/Minmus (?). |
| Tracking Station | orbits visible only | 150,000 | **patched conics** (SOI-change preview) | Buy before first Mun/Minmus attempt — makes transfer/capture planning far more reliable. |
| Launch Pad | 18 t / 20 m / 21.2 m | 75,000 | 140 t / 36 m / 39.6 m | Buy once your lander+transfer stack exceeds 18 t (common for a crewed Mun/Minmus vehicle). |
| VAB | 30 parts | 225,000 | 255 parts | Buy once part count is the binding constraint, usually alongside/after Launch Pad. |
| R&D | 100 science banked | 451,000 | 500 science banked | Lower priority — only blocks you once you're stockpiling >100 unspent science. |

Rough funding order: Mission Control L2 (75k) → Tracking Station L2 (150k) → Astronaut Complex L2
(75k) → Launch Pad L2 (75k) → VAB L2 (225k), funded by early contracts + recovering all craft
after each flight (do not skip recovery — it's a major funds source). R&D L2 (451k) and any L3
upgrades typically come after the first successful Mun/Minmus round trips.

## Sources
- https://wiki.kerbalspaceprogram.com/wiki/Decoupler_and_separator
- https://forum.kerbalspaceprogram.com/topic/122534-when-staging-radial-boosters-they-blow-up-my-main-stage-how-to-prevent/
- https://wiki.kerbalspaceprogram.com/wiki/Cheat_sheet
- https://forum.kerbalspaceprogram.com/topic/155423-delta-v-map-reading/
- https://wiki.kerbalspaceprogram.com/wiki/Minmus_101:_Landing_on_Minmus_and_coming_back
- https://wiki.kerbalspaceprogram.com/wiki/Tutorial:Career_mode_(Richmountain112)
- https://wiki.kerbalspaceprogram.com/wiki/Technology_tree
- https://wiki.kerbalspaceprogram.com/wiki/Kerbal_Space_Center
- https://wiki.kerbalspaceprogram.com/wiki/LV-T45_%22Swivel%22_Liquid_Fuel_Engine (and sibling engine/SRB pages: LV-T30 Reliant, LV-909 Terrier, RE-L10 Poodle, RE-I5 Skipper, 48-7S Spark, RT-5 Flea, RT-10 Hammer, BACC Thumper)
