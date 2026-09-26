# Save NRE after `scene space_center` (2026-09-26 09:25) — diagnosis

Sources: Unity `Player-prev.log` (the run that ended 09:32; KSP.log was overwritten by the 09:48 restart),
`Player.log` (current run), decompiled Assembly-CSharp / KRPC.dll / KRPC.Core.dll / KRPC.SpaceCenter.dll
(`scratchpad/dec/`), repo code. Log path:
`/mnt/c/Users/<user>/AppData/LocalLow/Squad/Kerbal Space Program/Player-prev.log` (433 MB, 7.98 M lines).

## Timeline from the log (Player-prev.log line numbers)

| line | time | event |
|---|---|---|
| ~19400 | 09:22–09:24 | flight: `periapsis` burn after a 2006 s warp ("Packing/Unpacking Minmus Lab 1" = rails on/off, normal) |
| 19559 | 09:24:49 | KSP autosave "[AutoSave]: Game Backed Up and Saved" (normal) |
| 19610 | 09:25:04 | `cmd_scene` → kRPC `save("persistent")`: "Flight State Captured / Game State Saved" (OK) |
| 19643 | 09:25:04 | kRPC `set_GameScene` → "Scene Change : From FLIGHT to SPACECENTER (Async)" |
| 19650 | | **"Reference Frame: Rotating"** printed *after* the change request, while the flight scene is unloading |
| 19700 | | NRE `FlightGlobals.getFoR → FlightCamera.Startup` on the loadingBuffer scene |
| 19796 | 09:25:11 | NRE `FlightCamera.GetAutoModeForVessel(null)` on the SPACECENTER scene |
| 19822.. | 09:25:12→09:29:36 | 795 082 NREs: `Vessel.Update [0x15c]` (766 605 ≈ 49 vessels/frame), `AmbienceControl.Update`, `FlightGlobals.get_ship_velocity ← FloatingOrigin.FixedUpdate` (12 830 ≈ 257 s × 50 Hz) — every frame until the next scene change |
| (none) | 09:26–09:28 | the two `accept` + `save` calls: **no "Flight State Captured"** line → the saves threw before writing; kRPC returned the NRE to the client (kRPC doesn't log server-side RPC exceptions) |
| 7983830 | 09:29:36 | "Scene Change : From SPACECENTER to TRACKSTATION" (kRPC, no save) — spam stops |
| 7984022 | 09:29:44 | TRACKSTATION → SPACECENTER |
| 7984214 | 09:30:03 | `save` works: "Flight State Captured / Game State Saved" (writes the rolled-back state) |
| 7984352 | 09:31:44 | `load-save` saves again + main menu + reload (same rolled-back state) |

Healthy comparison: the FLIGHT→SPACECENTER switches at 08:35:38 (prev log 15198) and 10:04:09 / 10:10:26
(current log 13230 / 14291, same `cmd_scene` path) show *no* "Reference Frame" line, no FlightCamera NRE and
zero NREs afterwards.

## (a) What throws in `FlightState..ctor` and why

IL of `FlightState::.ctor` (dec/FlightState.il, method at RVA 0xa0724, code size 0x2c4):

```
IL_0287: ldsfld bool FlightGlobals::ready
IL_028c: brtrue.s IL_029b            ; !ready → activeVesselIdx = 0
IL_029b: ldarg.0
IL_029c: ldfld  List<ProtoVessel> FlightState::protoVessels
IL_02a1: call   Vessel FlightGlobals::get_ActiveVessel()
IL_02a6: dup / pop
IL_02a8: ldfld  ProtoVessel Vessel::protoVessel     ; <-- NRE: ActiveVessel == null
IL_02ad: callvirt List<ProtoVessel>::IndexOf
IL_02b4: stfld  int32 FlightState::activeVesselIdx
IL_02b9: ldstr  "Flight State Captured"
```

Decompiled: `activeVesselIdx = FlightGlobals.ready ? protoVessels.IndexOf(FlightGlobals.ActiveVessel.protoVessel) : 0;`.
So the NRE means exactly: **`FlightGlobals.ready == true` while `FlightGlobals.ActiveVessel == null`** in the
space-center scene. It is not a vessel/protoVessel with a null field: the per-vessel loop (`BackupVessel()`)
completed; nothing about Minmus Lab 1, the MPL, renamed vessels, `SetVesselType`, EVA/lab procedures or debris
is involved (the same 49 vessels saved fine at 09:25:04 and 09:30:03).

The same broken pair explains every other NRE in the spam, all on the `ready` guard:
- `Vessel.Update`: `if (!FlightGlobals.ready) return; if (this != FlightGlobals.ActiveVessel) { ... FlightGlobals.ActiveVessel.vesselTransform.position ... }` → NRE for all ~49 packed vessels each frame.
- `FloatingOrigin.FixedUpdate`: `if (!FlightGlobals.ready) return; ... FlightGlobals.ship_velocity` (= `ActiveVessel.rb_velocity`) → NRE.
- `FlightCamera.Startup`: `while (!FlightGlobals.ready) yield return null;` then `GetAutoModeForVessel(FlightGlobals.ActiveVessel)` → NRE at the very first frame of the space-center scene, i.e. `ready` was already true when the scene loaded — it **leaked from the flight scene**, it was not set in the space center.

How `ready` leaks (decompiled FlightGlobals):
- `OnSceneChange` (on `GameEvents.onGameSceneLoadRequested`, fired synchronously inside `HighLogic.LoadScene → SetLoadSceneEventsAndFlags`): `ready = false`.
- `FixedUpdate`: `if (activeVessel == null) return; UpdateInformation(); if (!ready) { ready = true; OnFlightGlobalsReady.Fire(true); }`.
- `OnDestroy`: `activeVessel = null; Vessels.Clear(); ...` — **does not reset `ready`**.
- `Awake` (new instance): `ready = false; activeVessel = null`.

So if **one more `FlightGlobals.FixedUpdate` runs in the flight scene after the load request but before Unity
tears the scene down**, `ready` flips back to true, then `OnDestroy` nulls `activeVessel`, and the space-center
scene (which evidently has no FlightGlobals `Awake` of its own to reset the static flag — inference from the
fact that the flag stayed true for 4 minutes, that the tracking-station scene did reset it, and that no code
outside FlightGlobals writes `ready`) inherits `ready == true, ActiveVessel == null`.

Evidence that the extra physics step happened only in the bad run: `"Reference Frame: Rotating"` is printed by
`OrbitPhysicsManager.setRotatingFrame`, which is only reached from `OrbitPhysicsManager.FixedUpdate` and that
method starts with `if (!FlightGlobals.ready) return;`. The line appears *after* the "Scene Change" line and
before the unload in the bad run, and never in the three healthy runs. So: a FixedUpdate ran after the request
with `ready == true` (already re-set by FlightGlobals.FixedUpdate in that same step).

Why kRPC makes this possible: `KRPC.Addon.FixedUpdate() → core.Update()` executes RPCs **inside FixedUpdate**
(dec/krpcmain, lines ~449–466). `set_GameScene` → `GameSceneSwitcher.LoadScene → HighLogic.LoadScene(SPACECENTER)`
(dec/krpcmain ~1520–1545). Unity performs the actual scene switch at the end of the frame; when the frame carries
more than one physics step (frame time > 20 ms, common after a warp with ~49 vessels), the remaining steps still
run the flight scene, including `FlightGlobals.FixedUpdate`. Stock leaves flight from the pause menu (OnGUI/Update
phase, after all physics steps of the frame) and, for the tracking station, `TrackingStationBuilding.OnClicked`
saves first (`GamePersistence.SaveGame` then `HighLogic.LoadScene`), so stock does not hit this ordering.
(Inference: script-execution order within one step puts FlightGlobals before KRPC.Addon, otherwise every kRPC
scene switch would break; the healthy runs show it does not.)

## (b) Why funds/UT rolled back while contract objects stayed "active"

1. `GamePersistence.SaveGame(name, folder, mode)` → `SaveGame(HighLogic.CurrentGame.Updated(), ...)`.
   `Game.Updated()`: `if (LoadedSceneHasPlanetarium) flightState = new FlightState();` **first**, then
   `Parameters/CrewRoster`, then `scenarios = ScenarioRunner.GetUpdatedProtoModules()` (Funding, ContractSystem,
   R&D... serialised into `HighLogic.CurrentGame.scenarios`). The NRE aborts before the scenarios step, so after
   09:25:04 `HighLogic.CurrentGame` never got the two accepts (+352k funds) nor any UT advance.
2. `ScenarioRunner.OnGameSceneLoadRequested` (on every scene change) does `DestroyImmediate(modules[i]); modules.Clear()`
   without updating the protos; the next scene instantiates its ScenarioModules from `HighLogic.CurrentGame.scenarios`.
   kRPC's `GameSceneSwitcher.LoadScene` calls `HighLogic.LoadScene` directly, with no save and no `Updated()`.
   So `scene tracking_station` at 09:29:36 rebuilt Funding/ContractSystem from the 09:25:04 snapshot: funds 1.368M,
   both contracts Offered, UT = `flightState.universalTime` of 09:25:04 (`HighLogic.CurrentGame.UniversalTime`
   is `flightState.universalTime`; `FlightState.Load()` calls `Planetarium.SetUniversalTime(universalTime)`).
   This is the same "leaving flight without a save rolls back" behaviour already noted in LOG.md line 51; here it
   was triggered from the space center because the save that was supposed to refresh `CurrentGame` had failed.
   (Exact KSC-scene call site that re-runs `FlightState.Load`/`SetProtoModules` not pinned in the ILSpy output —
   inference from the observed rollback + the decompiled `Game.Updated`/`ScenarioRunner` code.)
3. Contract objects "active but in the offered list": kRPC's `ObjectStore` maps objects to ids with a
   `Dictionary<object, ulong>` (dec/krpccore ~10384), and `KRPC.SpaceCenter.Services.Contract` overrides
   `Equals`/`GetHashCode` by `InternalContract.ContractID`. After the ScenarioRunner rebuilt ContractSystem, the new
   `Contracts.Contract` instances have the same ContractIDs, so kRPC handed back the **old wrappers** whose
   `InternalContract` is the dead, still-`Active` instance; `accept()` on it touches nothing the live ContractSystem
   knows about. `offered_contracts` enumerates the live system, so the ids overlapped. A KSP restart clears the
   ObjectStore; `load-save` (mod `LoadSave`) does not, because the kRPC server (static) survives the main-menu
   round trip. The game state itself was consistent from 09:30:03 on (that save wrote the rolled-back state,
   persistent.sfs = both Offered, funds 1.368M) — restart only cleared the stale kRPC wrappers.

## (c) Tooling or stock? Recurrence

- Root cause is an ordering hazard created by **kRPC executing `set_GameScene` from FixedUpdate** with KSP's
  `FlightGlobals.ready` not being reset on scene entry. Not KspBot code (nothing in `mod/KspBot` touches
  `FlightGlobals.ready`, `SetActiveVessel`, `DontDestroyOnLoad`; only `SetVesselType` touches vessels), not the
  Minmus Lab 1 craft, not the save file. Stock UI paths avoid it. So: kRPC usage pattern, probabilistic.
- Trigger: `scene space_center` (or any kRPC `game_scene = ...` away from FLIGHT) on a frame that runs ≥ 2 physics
  steps — more likely right after warps, with many loaded vessels, on a slow Windows (memory-pressure) machine.
  Observed 1 of 4 flight→KSC switches today; it will recur.
- Consequences chain only if a save is attempted before another scene change: `accept/launch/upgrade/research` all
  call `SaveGame` (cli `cmd_accept`, `cmd_launch`; mod `UpgradeFacility`, `SetCommNet`, `FlyVessel`, `LoadSave`);
  the accept itself succeeds, the save fails, the next kRPC scene change (or `fly`, which saves first and would
  also throw) rolls the ScenarioModules back. Money paid at KSC in that window (research, upgrades, hires, accepts)
  is lost/undone; nothing is corrupted on disk because no save is written while broken.
- The earlier "KSP quits silently at the first `launch`" is a different symptom (no evidence here).

## (d) Fix / guard options

Cheapest and most robust — a mod-side guard, since the broken state is a single static flag:
1. **KspBot `FixFlightGlobals()`** (or run it inside `Status()`/a `Save()` procedure): in a non-flight scene, if
   `FlightGlobals.ready && FlightGlobals.ActiveVessel == null` → `FlightGlobals.ready = false` (it is a
   `public static bool`), log it, return true. That stops the NRE spam and makes `SaveGame` work again
   (`activeVesselIdx = 0` path). Cost ~10 lines; can be called at the start of every save the mod/CLI makes.
2. **Save from the mod with try/catch** (`KspBot.Save()` wrapping `GamePersistence.SaveGame`) that returns
   `ok/error + FlightGlobals.ready/ActiveVessel` — gives the CLI a reliable failure signal instead of an opaque
   kRPC `RPCError`, and can apply guard 1 before retrying once.
3. **CLI**: on a failed save, stop the command (already done for `accept`: prints WARNING, no retry). Add: never
   change scene after a failed save until a save succeeds (a scene change discards everything since the last
   `Updated()`); `cmd_scene` from flight should verify the save wrote ("Flight State Captured" ⇔ return without
   exception) — it already does, the failure was later.
4. **Avoid the hazard at its source**: switch scenes from the mod on the Update phase instead of kRPC's
   FixedUpdate: a KspBot `LeaveFlight()` that does `GamePersistence.SaveGame(...)` and then schedules
   `HighLogic.LoadScene(SPACECENTER)` via a coroutine/`Update` (e.g. `StartCoroutine` → `yield return null`
   inside a MonoBehaviour, or `GameEvents.onGameSceneLoadRequested` is irrelevant here). This removes the extra
   FixedUpdate window entirely; still keep guard 1 as belt-and-braces because the ordering assumption is
   Unity-internal.

Worth it? Yes, but small: guard 1 (+ optionally 4) is ~30 lines of C# and removes a failure that silently undoes
KSC spending and needs a KSP restart to clear the kRPC object cache. A procedural rule alone ("after `scene
space_center` from flight, run `status`; if a save fails, restart KSP") works but costs a restart each time and
relies on noticing the failure; the CLI already sees the error, so the guard is the better fix.

Verification for the fix: after a flight→KSC switch, `KspBot.Status()` could report `flightGlobalsReady`;
the bad state is `ready == true` at the space center. In the log the signature is the "Reference Frame:" line
right after "Scene Change : From FLIGHT to SPACECENTER" followed by `FlightCamera.GetAutoModeForVessel` NRE.
