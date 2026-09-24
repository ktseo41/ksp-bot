# ksp-bot — play a KSP1 career from an LLM session

KSP 1.12.5 (Steam, Windows) is driven from WSL through **kRPC 0.6.0** plus a small helper mod
**KspBot** (`mod/KspBot`, C#) that adds what kRPC lacks: craft building from JSON, tech research,
facility upgrades, crew hiring, KSP's flight event log, save autoload. Python side: `kspbot/`
(`core.py` connection, `flight.py` mission phases, `recorder.py` flight recorder, `cli.py` commands).

## The job (user's original request — this outranks any checklist or handoff note)
Play the career yourself, from zero: design, build, launch and fly everything, reach Minmus, then keep
going farther step by step (Minmus round trip → Mun → Duna and beyond). The system exists only to make
that possible — keep it as small as the missions need.

**Operating mode: autonomous and continuous.**
- A finished mission is not a stopping point: log it, pick the next goal, keep flying in the same turn.
- A failed mission (lost craft, dead crew) is not a stopping point either: read the recorder, find the
  cause, write it in `LOG.md`, fix the design or code, fly again. Don't ask the user what to do next.
- Questions to the user are only for pre-agreed settings or real blockers you cannot resolve
  (game won't start, career financially stuck with no way out). Not for routine mission decisions.
- Reverting is allowed whenever the game offers it (see rules below); after that, keep going.

## Rules of play (career save `kspbot`, Normal difficulty)
- **Revert: allowed when the game offers it** (Revert to Launch / VAB, `revert_to_launch()`); log each
  revert and its reason in `LOG.md`. **Quickload** only when our tooling caused the failure. If the revert
  window is gone, the loss stands. Test new flight code in the sandbox save `kspbot-sandbox`
  (`tools/install.sh kspbot-sandbox:sandbox`), never in the career.
- No autopilot mods (MechJeb etc.). Flight logic is ours (`kspbot/flight.py`).
- Pay for everything the normal way (launch cost, research, upgrades). `sandbox-orbit` is refused in career.
- Keep `LOG.md` (career journal) updated after every mission: what flew, result, money/science, lessons.
  Read it first when resuming.

## Start / resume
```
tools/install.sh kspbot     # builds mod, (re)starts KSP (kills a running one!), autoloads save 'kspbot'
uv run ksp wait             # blocks until the save is loaded
uv run ksp status
```
Only restart KSP from the space center (a restart loses an unsaved flight). kRPC listens on 127.0.0.1:50000.

## Commands (`uv run ksp <cmd> -h` for options)
Space center: `status`, `contracts [-v]`, `accept N`, `decline N`, `tech [--all]`, `research ID`,
`facilities`, `upgrade ID` (e.g. MissionControl), `hire`, `parts [filter] [--all]`, `build SPEC.json`,
`launch CRAFT`, `recover`, `scene space_center|tracking_station`, `shot [name]` (game screenshot → runs/NAME.png, view it with Read).
Flight phases (each returns when the phase is done): `ascent --alt 80000`, `circularize`,
`transfer Minmus --pe 15000` (plans, burns, auto-corrects), `correct BODY --pe X`, `soi`,
`capture [--apo X]`, `land`, `science [--transmit]`, `liftoff --alt 15000`, `return --pe 30000`,
`reentry`, `periapsis --alt X`, `node`, `stage`, `warp +SECONDS`, `vessel`, `log`.
Long phases (transfer, soi, capture, reentry) may exceed 10 min: run them in the background.

## Flight recorder — always read it
Every flight command records `runs/flights/<date>_<vessel>.jsonl` (1 Hz telemetry + events) and prints
events as `!! [kind] ...`: `damage` (collisions/explosions/overheating from KSP's log), `parts` (which
parts disappeared), `stage`, `attitude` (tumbling/high AoA), `soi`, `situation`. After any surprise run
`uv run ksp log` and diagnose from data before changing code or design. Damage lines about jettisoned
stages burning up on reentry are normal.

## Designing a craft
Read `docs/design-guide.md` first. Spec = JSON list of parts, first part is the root:
```json
{"name": "Hopper 1", "parts": [
  {"id": "pod", "part": "mk1pod.v2"},
  {"id": "chute", "part": "parachuteSingle", "parent": "pod", "node": "top", "stage": 2},
  {"id": "srb", "part": "solidBooster.sm.v2", "parent": "pod", "node": "bottom", "stage": 1},
  {"id": "fins", "part": "basicFin", "parent": "srb", "symmetry": 3, "height": -0.5}]}
```
- `node`: parent's stack node (`top`/`bottom`/...); the child uses the opposite node unless `childNode`.
- no `node` → surface attach at parent-local `height` (m from parent center), `angle` (deg), `symmetry` N,
  optional `radius`. A surface child of a surface part (booster on radial decoupler) goes straight outward.
- `rigid: true` / `autostrut: "Root"|"Heaviest"|"Grandparent"`: stiffen tall stacks (SRB stacks fall over without them).
- `stage`: 1 fires at launch, 2 next, ... (contiguous). Decoupler + next engine may share a stage.
  Chutes last. Parts without staging actions ignore `stage`.
- Part names/nodes/stats: `uv run ksp parts`. Only researched parts are accepted in career.
- Verify on the pad before flying: `launch` prints per-stage Δv/TWR computed by KSP. If it's wrong,
  `recover` on the pad (full refund) and redesign. Past specs live in `crafts/`.

## Rough Δv budget (stock)
Kerbin→LKO 80 km ≈ 3400 · LKO→Minmus transfer ≈ 930 · capture ≈ 160 · land ≈ 180 · takeoff ≈ 180 ·
return ≈ 160 (reentry free). Mun: transfer ≈ 860, capture ≈ 310, land/takeoff ≈ 580 each.
Upper stage for a Minmus landing mission: ≥ 2000 m/s after LKO, lander TWR (Minmus) > 1.

## Facility gates that matter
Maneuver nodes need Mission Control lvl 2 AND Tracking Station lvl 2 (patched conics, encounter
prediction for `transfer`/`correct`/`return`). Without them burns fall back to manual (`manual_burn`).
Astronaut Complex lvl 2 → EVA outside KSC. Level-1 pad: 18 t, VAB: 30 parts. `uv run ksp facilities`.

## Dev notes
- Mod changes: edit `mod/KspBot/*.cs`, run `tools/install.sh` (rebuilds, restarts KSP).
- Decompiled KSP source helps (ilspycmd 8.2 + `DOTNET_ROLL_FORWARD=Major`) — don't commit it.
- kRPC API reference: `GameData/kRPC/KRPC.SpaceCenter.json` in the KSP folder.
