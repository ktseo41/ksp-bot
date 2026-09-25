# Mobile Processing Lab (Large.Crewed.Lab) — how it works in KSP 1.12.5

Research by an opus subagent, 2026-09-26, from decompiled Assembly-CSharp.dll / KRPC.SpaceCenter.dll and the part
configs. [V] = read in code/config, [I] = inferred. Code sketch for KspBot: `LabSketch.cs` (not built yet).

## Part (largeCrewedLab.cfg) [V]
CrewCapacity 2, 3.5 t, cost 4000 (advExploration, researched). ModuleScienceLab: dataStorage 750, crewsRequired 1,
SurfaceBonus 0.1, ContextBonus 0.25, homeworldMultiplier 0.1, cleaning 10 EC per baseValue. ModuleScienceConverter:
dataProcessingMultiplier 0.5, scientistBonus 0.25, researchTime 7, scienceMultiplier 5, scienceCap 500,
powerRequirement 5 EC/s.

## Data into the lab [V]
- Results dialog "lab" button -> `sendDataToLab` -> `ModuleScienceLab.ProcessData(data)` -> `StoreData`: adds the
  subjectID to `ExperimentData`, adds `labValue` to `dataStored`.
- Same vessel only (`ScienceLabSearch` walks `vessel.Parts`, loaded). The value uses `FlightGlobals.ActiveVessel` and
  `currentMainBody`: the station must be the active vessel (docked craft count).
- Sources: experiment modules, any ModuleScienceContainer (pods, Experiment Storage Unit).
- **Consumed**: experiments -> SetInoperable (non-rerunnable) + endExperiment; containers -> RemoveData. That copy
  can no longer be recovered/transmitted.
- **Each subject once per lab, forever** (`IsStorable`), and only while labValue + dataStored <= 750.
- `labValue = round(baseValue x subjectValue x gainMult x (1.1 if lab landed) x (1.25 if the subject is of the current
  body) x (0.1 if landed/splashed on Kerbin))` — independent of how much R&D already has for the subject.
- `labValue` is set only by the dialog UI: calling ProcessData from code needs our own computation (else 0) -> C#.

## Data into science (ModuleScienceConverter.PostProcess) [V]
- Per tick: dData = dt x 0.5 x S x dataStored / 1e7, science += 5 x dData; S = sum over scientists IN THE LAB PART of
  (1 + 0.25 x level). Exponential decay, tau = 2e7/S s (two level-0 scientists: 1.09 Kerbin years).
- Max rate with 750 data: ~3,450 sci/yr at S=2.
- **Cap 500 stored science**: processing stops when full (time passes, data not consumed). Full lab at S=2 fills it
  in ~62 Kerbin days. **Each visit yields at most 500.**
- Needs >= 1 scientist, "Start Research" once (IsActivated saved). 5 EC/s at 1x-100x warp; above 100x (and during
  catch-up) only >= 0.1 EC stored per tick (ResourceBroker scaling).
- Unloaded: nothing runs; on load `BaseConverter.GetDeltaTime` catches up from lastUpdateTime (chunks <= 21,600 s,
  ~9 s real per year [I]), also capped at 500.
- To R&D: `TransmitScience` ("sciencelab@Body") via the best transmitter: needs a CommNet link and a DIRECT/RELAY
  antenna (internal pod antennas can't). ~6 EC per science (500 sci ~ 3,000-3,300 EC). Recovery also credits it.

## Cleaning experiments [V]
`CleanModulesEvent` resets every inoperable experiment on the active vessel; shown with >= 1 scientist in the lab;
10 EC x baseValue drawn at ~10 EC/s (goo 100 EC, materials bay 250 EC); do it at 1x.

## kRPC 0.6.0 without mod changes
Start/stop research: ModuleScienceConverter events StartResourceConverter/StopResourceConverter ("Start Research");
transmit: ModuleScienceLab "TransmitScience"; clean: "CleanModulesEvent" (display name has a dynamic "(N)": use the
id); status fields sciString, datString, rateString, status, statusText. **Processing data needs C#**:
LabValue (the formula above), LabStatus() JSON, LabProcess(dryRun) — see LabSketch.cs.

## Yield (simulated, lab kept topped up, transmit before the cap)
Minmus low orbit supply: ~885 data (orbit only) -> S=2: 2,641 / 3,715 / 4,380 sci over 1 / 2 / 5 years; + high orbit
(1,239): 3,334 / 5,056 / 6,123; + 9 landed biomes (6,393): 3,459 / 6,909 / 17,261. Limits: 500 per visit (~6 visits
a year at full rate), finite supply (each subject once per lab), scientist count/level (levels rise on recovery [I]).
Minmus beats the Mun on every multiplier.

## Recommended station
MPL + command pod (or probe core), docking port for landers, 2 scientists in the lab, HG-55 or Communotron 16,
~4,000 EC batteries, >= 8 EC/s solar, on board: goo, materials bay, thermometer, barometer, magnetometer, storage
unit. Procedure: low Minmus orbit, run everything + EVA reports per biome, LabProcess, Start Research; every <= 60
Kerbin days focus the station (catch-up), Transmit, refill, clean experiments; later a reusable docking lander brings
~612 data per landed biome.
