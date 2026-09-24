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

### Next steps (plan)
1. Research advRocketry (45 sci: Terrier + FL-T400) as soon as science allows; then basicScience (materials bay, batteries, probe core) or flightControl.
2. Science ideas: "Science data from space around Kerbin" contract; KSC biome/landed experiments; materials bay once researched. Put goo/thermometer where they survive reentry (or bring a battery/solar to transmit).
3. Minmus landing mission (contract offered: "Science data from surface of Minmus", 32k adv / 79k done): lander = heat-shielded Mk1 + Terrier + FL-T400s + LT-05/LT-1 legs, ≥2000 m/s after LKO. Verify on pad, recover if short.
4. Ascent fix (pitch-over at 250 m) and node steering are untested in career — watch the recorder on the next launch.
5. Mod change pending install (DismissDialogs, built not installed): run tools/install.sh kspbot at the space center.
