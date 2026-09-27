# Transcript notes — KSP bot sessions (for the blog post)

Source files (both processed via python/jq, not read whole):
- `c58c5320-1c97-4130-8776-0d9f92853cec.jsonl` — self-identifies internally as session **"ksportal"**.
  Timestamps 2026-09-24T02:13:08Z – 05:58:13Z (UTC). 1928 lines, 542 assistant turns, 236 tool calls.
- `87c6169d-6dd3-41fc-9863-0360f5bf76bf.jsonl` — self-identifies internally as session **"ksp-bot-2f"**.
  Timestamps 2026-09-23T23:14:15Z – 2026-09-24T04:50:03Z (UTC). 1491 lines, 440 assistant turns, 201 tool calls.

**IMPORTANT correction to the task's file labels**: the task calls c58c5320 "earlier" and 87c6169d
"later", but the raw timestamps say the opposite. `87c6169d` ("ksp-bot-2f") starts at 23:14:15 on
2026-09-23 with the user's actual kickoff message and builds the whole system from scratch. At
02:13 it hands off the running career to `c58c5320` ("ksportal"), which then does almost all of the
actual mission-flying in this transcript pair (Minmus Lander deaths, Mun Lander deaths/success, the
survey bug). `87c6169d` does NOT stop after the handoff — it stays open another ~2h40m as a passive
"supervisor" the user keeps chatting with, checking on ksportal's progress via `git log`/`LOG.md`
rather than flying itself. `ksportal` in turn hands off to a **fourth** session, `orca-ksp`
(not given to us), at 05:56. So the true chain is:
`ksp-bot-2f` (=87c6169d, builds everything) → `ksportal` (=c58c5320, flies Minmus/Mun) → `orca-ksp`
(unseen, presumably flies the Minmus survey / Duna onward).
Below, sections are ordered by **actual wall-clock time**, and each item is tagged with which file
it came from using the session's self-chosen name (`ksp-bot-2f` / `ksportal`) plus the file's short
hash for cross-reference.

Both sessions ran entirely on **claude-opus-5-5** (not Sonnet) — every one of the 982 assistant
turns across both files used this model.

---

## 1. Every genuine user message, verbatim, in order

Genuine = plain-string or text-block `user`-type content that isn't a tool_result, system-reminder,
slash-command wrapper, or cross-session relay message. (The cross-session handoff at the very start
of `ksportal` is explicitly excluded here per the task's rules, but is quoted in §2 because it *is*
the genesis artifact that matters.)

1. **[ksp-bot-2f, 2026-09-23T23:14:15Z]**
   > 지금 steam으로 ksp (kerbal space program 1)을 다운 다 받았어. 현재 처럼 클로드 코드 세션을 통해(혹은 다른 llm 세션을 통해), ksp를 조작해서, 커리어모드를 제로부터 시작해서 우주선 조립 및 발사 및 조종 등을 통해서 플레이할 수 있게 해줘서. minmus까지 갈 수 있게 하고 차근차근 더 멀리 갈 수 있도록 할 수 있게 하는 시스템을 마련해줘. 그러니까 요구사항은 두개지. 직접 모든걸 다 해서 minmus까지 가기. 그리고 그걸 위한 방법(시스템)도 마련하기. 사실상 목표는 하나이긴하네 시스템은 부가적인거니까? 그리고 시스템이 너무 복잡하게 말고 딱 필요한 만큼만 해야하고 이건 아주 중요해 안그러면 시스템만 구축하다 끝나거든. 내 생각에는 모드를 별도로 만들어서 llm이 조작하기 쉽게 해줘야할거 같아. 아무튼 무슨 말인지 이해했지? 만약 결정해야하는게 더 있다면 나에게 물어보고.
   (This is the entire genesis prompt — the project's founding instruction, in full. Note the explicit
   two requirements stated as really one, and the explicit warning against over-building the system.)

2. **[ksp-bot-2f, 23:17:01Z]** — answer to an `AskUserQuestion` (difficulty / mod stack / revert policy):
   > The user answered: "커리어 난이도는 어떻게 할까요?"="Normal (Recommended)", "기반 모드 구성은 어떻게 할까요? (MechJeb 같은 자동조종 모드는 쓰지 않고 궤도계산·비행 로직은 제가 직접 작성합니다)"="kRPC + 자작 보조모드 (Recommended)", "실패했을 때 리버트/퀵로드를 써도 될까요?"="기본적으로는 금지인데, 테스트시에나 (즉 발사 시도 자체 테스트가 아니라, 시스템 구축시) 버그같은걸로 안될때는 허용".
   (This is the literal origin of the revert rule, worded more precisely than either LOG.md or
   writeup.md: forbidden by default, except during *system-building* tests when something fails
   because of a bug — not during real launch attempts.)

3. **[ksportal, 2026-09-24T02:30:30Z]**
   > 어라 원래 목표는 minmus 까지 왕복하는건데, 그리고 버그로 죽은거 아니면 세이브로드 반복해서 하는건 하지 말고, 사실 이렇게 하면서 mun이랑 duna duna 위성들 등 더 많은 곳을 가고 뭐 그 외 것들도 하고 그러려고 하는건데 왜 실패했는데 멈춰버렸지?

4. **[ksportal, 02:43:10Z]**
   > 무슨 권한문제로 막혀? 내가 허용할게 settings.json에 추가해

5. **[ksportal, 02:43:10Z]** — `[Request interrupted by user for tool use]`

6. **[ksportal, 02:54:25Z]**
   > 생성했는데 됐어?

7. **[ksportal, 02:55:19Z]**
   > 좋아 다시 했어

8. **[ksportal, 02:56:19Z]** — `[Request interrupted by user for tool use]`

9. **[ksportal, 02:56:19Z]**
   > 내가 껐는데 그냥 한 화면에서 가만히 있길래 거의 40분동안

10. **[ksportal, 04:38:31Z]** — with an attached screenshot
    > [Image #1] 뭐야 이렇게 된거 아니야?

11. **[ksportal, 05:58:05Z]**
    > 응 근데 만약 연구가 더 필요 하다면 minmus mun 탐사하거나 미션 수행해서 과학점수랑 돈을 더 얻으면 될거 같은데 그렇게 하려고 했어? 괜히 내가 자율적인 게임 진행을 가이드하는거 같아서, 자유롭게 두고 싶긴 하거든

12. **[ksp-bot-2f, 02:39:03Z]** (this is the "supervisor" resuming after handing off to ksportal)
    > 근데 ksportal 이라는 세션에서는 한번 왕복시도인가 하고나서는 그냥 중단해버리는 느낌인데 지침이 제대로 간거 맞아? 내가 그래서 뭐라고 조정해주긴했느데 왜이렇게 됐지?

13. **[ksp-bot-2f, 02:43:00Z]**
    > 어 근데 내 맨 처음 지시가 뭐였는데?

14. **[ksp-bot-2f, 04:45:40Z]**
    > 지금 ksportal은 어떤걸 하고 있어? 잘 되고 있는거야?

15. **[ksp-bot-2f, 04:49:35Z]**
    > 응 시스템에서 허용하는 revert라면 괜찮아.

(16 total genuine turns across both files, including the two bare interruption signals.)

---

## 2. Project genesis: how the setup came together (timeline, all in `ksp-bot-2f` / 87c6169d)

All times UTC, 2026-09-23 unless noted.

- **23:14:15** — user's founding prompt (quoted in full in §1.1).
- **23:14:33–23:15:48** — locates the Steam KSP install under `/mnt/c/...`, checks for a WSL↔Windows
  dotnet/mono/msbuild toolchain (none found initially; later installs one).
- **23:16:05** — asks the user 3 `AskUserQuestion`s: difficulty (recommended Normal), mod stack
  (recommended kRPC + a small custom mod, vs. writing an HTTP server mod from scratch), and revert
  policy. User picks the recommended options but writes a more nuanced revert answer (§1.2).
- **23:17:05–23:17:50** — finds kRPC 0.6.0 on GitHub (latest release for KSP 1.12.5, dated
  2026-07-22), downloads and unzips it, reads its `KRPC.SpaceCenter.json` API surface, copies it
  straight into `GameData/`.
- **23:18:32** — launches KSP via `cmd.exe /c start steam://rungameid/220200` from WSL, and in
  parallel runs `uv init` + `uv add krpc==0.6.0` for the Python side.
- **23:20:22** — first screenshot mechanism: a **PowerShell script (`tools/screen.ps1`) using
  `System.Windows.Forms`/`System.Drawing` GDI calls to grab the whole Windows desktop**, then
  downscaled in Python with Pillow, since WSL can't see the Windows screen directly. (This was later
  dropped — see below — once they discovered kRPC has its own in-game screenshot call.)
- **23:20:34** — "KSP는 떠 있는데 kRPC 서버가 자동 시작되지 않아서, 화면 클릭 없이 설정 파일로
  자동 시작/자동 승인을 켜려고 합니다." (kRPC's server doesn't auto-start; hunts through the DLL's
  strings and kRPC's own source (`git clone --depth 1 --branch v0.6.0`) for the `autoStartServers`
  config key to avoid ever needing a mouse click.)
- **23:21:13** — "모드(C#) 작성 전에 KSP 내부 API를 확인하려고 디컴파일러를 준비 중입니다." Installs
  `ilspycmd` via `dotnet tool install -g ilspycmd`. First attempt fails ("Settings file
  'DotnetToolSettings.xml' was not found"); pins version 8.2.0.7535; that installs but the actual
  decompile then fails needing .NET 6 runtime; fixed by setting `DOTNET_ROLL_FORWARD=Major` so the
  installed .NET 8 SDK can run the 6.0-targeted tool. Decompiles `Assembly-CSharp.dll` to
  `~/.../scratchpad/decomp/src`.
- **23:21:56–23:22:35** — reads the decompiled source directly to reverse-engineer game internals it
  needed for the mod: `MainMenu.CreateNewGame`/`GamePersistence` (to autoload a save with no click),
  `RDTech`/`ResearchAndDevelopment` (research API), `GameVariables` (facility level limits),
  `SpaceCenterBuilding` (facility upgrade flow), `ShipConstruct`/`ShipConstruction` (the `.craft`
  file format: `attN`, `srfN`, `link`, `istg`, `sym` fields).
- **23:22:40** — "KSP 에디터의 실제 규칙(`LookRotation(normal) * LookRotation(orient)`)을
  찾았습니다." — reverse-engineered from decompiled editor code exactly how KSP orients a
  surface-attached part, which the JSON→craft builder needed to replicate.
- **23:26:04** — "Now writing the mod." Creates `mod/KspBot/{KspBot.csproj, Json.cs, AutoLoad.cs,
  Service.cs, CraftBuilder.cs}` and builds with `dotnet build -c Release`. Two build-error fixes on
  the way (a missing `FinePrint.` namespace prefix on `ContractDefs.Instance`, then dropping a
  contract-refresh call it decided it didn't need). **Mod built and working within ~12 minutes of
  starting to write code.**
- **23:29:00** — writes `tools/install.sh` (build + install into `GameData` + kRPC settings + restart
  KSP), discovers the DLL can't be replaced while KSP is running so the script kills and restarts it.
  A bug in the KSP-process-detection `if` in the script is found and fixed a few minutes later.
- **23:30:23** — "연결 성공: Normal 커리어가 자동 생성됐고(자금 25,000) 자작 서비스도 응답합니다." —
  first successful kRPC + KspBot connection, career auto-created with 25,000 funds.
- **23:30:41** — "JsonUtility가 KSP 안에서 파싱을 못 해서, 작은 JSON 파서를 직접 넣겠습니다." Unity's
  built-in `JsonUtility` couldn't parse the craft-spec JSON inside KSP's Mono runtime, so they wrote
  a small hand-rolled JSON parser (`Json.cs`) instead of pulling in a library.
- **23:32:02–23:33:02** — writes `kspbot/core.py`, builds a first test craft ("Test Flea": pod +
  chute + Flea SRB) from JSON, launches it to the pad, confirms funds deduction, stage Δv reporting,
  and screenshot capture all work.
- **23:33:06–23:35:50** — first full test flight: ignite → parachute → recover, plus science
  experiments; "기본 루프 전부 작동(발사→과학 실험→낙하산 착륙→회수, 자금 90k·과학 21.5)."
- **23:35:52** — verifies research and facility-upgrade APIs; finds and fixes a facility-level
  off-by-one bug in `Service.cs` (`level = round(norm*(count-1))+1` → `round(norm*count)+1`).
- **23:38:24** — writes `kspbot/flight.py` (ascent, transfer, correct, capture, land, liftoff,
  return, reentry — the whole mission-phase library) in one shot, then `kspbot/cli.py`.
- **23:39:56** — adds a sandbox-save option to autoload (`kspbot-sandbox:sandbox`) specifically so
  the entire flight-software chain could be end-to-end tested with every part unlocked, before ever
  touching the real career.
- **23:41:15–23:42:50** — reverse-engineers surface-attach node orientation conventions by grepping
  every stock part's `.cfg` for `node_attach`/`rescaleFactor`, cross-checking against decompiled
  editor code, and patching `CraftBuilder.cs`'s symmetry-placement math accordingly.
- **23:42:56** — builds a first sandbox test rocket (`sandbox-minmus-test.json`) with ~6,100 m/s
  vacuum Δv and launches it.
- **23:44–23:53** — ascent/circularize test #1: has to relax the AoA clamp in `flight.py` (15° cap)
  and rebuild a bigger test rocket after the first one under-performed.
- **23:53:51–00:04:31 (Sep 24)** — **the ascent autopilot nearly loses the test rocket**: circularize
  overshot and periapsis sank back toward re-entry. Diagnosis (thinking block, verbatim): "지금은
  근지점이 15km로 낮아 로켓이 다시 떨어지는 중이라 먼저 순방향 분사로 구조하겠습니다." (periapsis
  is down at 15 km and the rocket is falling back in, so a manual prograde-burn rescue is fired
  first via a raw Python one-liner driving `auto_pilot`/`throttle` directly, bypassing the
  not-yet-reliable `circularize` phase). It then screenshots the failure state (`shot fail`) and
  rewrites `ascent()`'s horizontal phase as closed-loop before retrying (`revert_to_launch()` in the
  sandbox, no permission issue here since it's the sandbox).
  - Separately, in this same test window (~00:19), **a 4×BACC-Thumper radial-booster cluster on a
    1.25 m FL-T800 core separated near max-Q (~42 s) and the boosters/decoupler physically collided
    into the core's Swivel engine**, destroying it (`part count 31 -> 13`). This sandbox failure is
    the origin of the later career-wide rule "attach cluster boosters directly to the core, skip
    radial decouplers" (stated in writeup.md §6 as a design lesson with no origin story — this is
    that origin story).
- **00:12** — adds a `FlightEvents` kRPC procedure (KSP's own flight log) to the mod, then writes
  `kspbot/recorder.py` (the 1 Hz telemetry + anomaly recorder described in CLAUDE.md).
- **00:19–00:23** — rebuilds the test rocket around a 2.5 m Skipper/Rockomax-class booster instead of
  the small radial cluster; reaches a clean 112×112 km orbit with 3,348 m/s left.
- **00:23:55–01:05** — **flies the entire mission profile end-to-end in the sandbox, once, before
  ever trying it in the career**: transfer to Minmus → mid-course correction (14 m/s, after the
  first transfer burn's aim error lost the encounter) → SOI entry → capture (1,996 m/s left) →
  **powered landing, upright** → surface science → liftoff → return burn → SOI exit → Kerbin
  periapsis correction → reentry → splashdown. Total time for this full validation flight:
  **about 41 minutes** (00:23:55 to 01:05:01).
- **01:05:17** — launches the *only* subagent used in either transcript: a background `Agent` call
  (`model: sonnet`) to research KSP 1.12 stock-part career design know-how (radial-booster
  separation physics, ascent stability, delta-v map, tech-tree order, facility priorities) and write
  `docs/design-guide.md`. Before this, it says: "codex 사용량 한도에 걸려 deepseek 조사가
  실패했습니다. 대안으로 sonnet 서브에이전트에게 웹 조사와 가이드 작성을 백그라운드로
  맡기겠습니다." — a `codex exec`/deepseek research delegation was tried first and failed on a usage
  limit, so it fell back to a Sonnet subagent doing its own WebSearch/WebFetch.
- **01:05:25** — while the research agent runs in the background, writes `CLAUDE.md` itself: "조사가
  도는 동안 시스템 사용 설명서(`CLAUDE.md`)를 작성합니다. 어떤 LLM 세션이든 이 파일만 읽으면 이어서
  플레이할 수 있게 하는 게 목표입니다." (goal: any LLM session should be able to pick up the career
  from `CLAUDE.md` alone).
- **~01:22–02:12** — actually starts flying the real **career** save (Hopper 1, Sounding 2, Orbiter 1
  including its own SYSTEM BUG/revert already in LOG.md, Minmus Flyby 1) — this portion overlaps
  with what LOG.md already documents in detail, so it is not re-narrated here except for items in §3.
- **02:12:43–02:13:07** — writes the handoff to `ksportal` and sends it via the `SendMessage` tool
  (`to: "ksportal"`), explicitly saying "previous session ksp-bot-2f is ending at the user's
  request." This is the literal text quoted at the top of c58c5320 (see §3 for the process failure
  this handoff caused).

**Genesis-to-first-crewed-landing-in-sandbox elapsed time: about 1h51m** (23:14 kickoff to 01:05
research-agent launch, by which point ascent/transfer/capture/land/liftoff/return/reentry had *all*
already been proven once, uncrewed, in the sandbox). The mod itself (`KspBot.csproj` through a
working `dotnet build`) took roughly 12 minutes to write and compile from a standing start with the
decompiled source already in hand.

---

## 3. Turning points and difficulties NOT already covered in LOG.md / writeup.md

### The multi-session handoff that silently reverted the "keep playing" policy
This is the single most blog-worthy thing in these transcripts and is **not mentioned anywhere** in
LOG.md or writeup.md, because writeup.md's "사람이 개입한 지점" section frames the autonomous-mode
rule as something the user simply stated once. In fact:

- At 02:12–02:13 `ksp-bot-2f` hands the running career off to `ksportal` with a checklist-style
  handoff message (quoted in full at the top of c58c5320, §"cross-session-message" — this transcript
  literally contains that handoff, machine-relayed) that lists concrete next steps ("design a Minmus
  landing mission... fly it") but never states "keep going after a mission ends or fails."
- `ksportal` follows the checklist, flies Minmus Lander 1, Jeb dies, and — lacking any instruction to
  keep going — **stops and asks the user what to do**, exactly the behavior the user's original
  instruction (§1.1) had asked to avoid.
- The user notices from a *different, still-open* session (`ksp-bot-2f`, i.e. the supervisor) at
  02:39: "근데 ksportal 이라는 세션에서는 한번 왕복시도인가 하고나서는 그냥 중단해버리는 느낌인데
  지침이 제대로 간거 맞아?"
- `ksp-bot-2f` diagnoses its **own** handoff as the bug, in a striking bit of self-critique (verbatim,
  02:39:48Z): "네, 인계 메시지는 도착했고 ksportal도 그대로 따랐습니다. 문제는 **메시지 자체에
  '멈추지 말고 계속 플레이하라'는 지시가 빠져 있었다는 것**이고, 이건 제 인계서 작성 실수입니다."
  It then lists four concrete causes: (1) it wrote the handoff as a checklist that terminates once
  the checklist is done, (2) it gave a revert rule but no rule for what to do about *non-bug*
  failures (design mistakes, crew deaths), so an ambiguous case defaulted to "ask the user," (3) its
  own handoff message modeled stopping behavior ("previous session is ending") which the receiving
  session imitated, and (4) a structural point about Claude Code itself: "Claude Code 대화형 세션은
  할 일이 끝났거나 결정이 필요해 보이면 그 자리에서 턴을 끝내고 사용자 입력을 기다립니다."
- The user then asks (02:43:00Z) "어 근데 내 맨 처음 지시가 뭐였는데?" and the session reconstructs
  and quotes back the entire original founding prompt (§1.1) almost verbatim, then rewrites
  `CLAUDE.md`'s opening section to state the original goal and "autonomous, continuous" operating
  mode explicitly, so future handoffs can't drop it again — this is exactly the "## The job" section
  now at the top of CLAUDE.md.
- The fix, notably, is committed only to `CLAUDE.md` on `main` — it does **not** retroactively reach
  the already-running `ksportal` session ("새 규칙은 새로 여는 세션부터 자동 적용되고, 지금 돌고 있는
  ksportal에는 반영되지 않습니다"). The supervisor session has to explicitly offer to message
  `ksportal` about it.
- The same pattern happens again with the revert-rule relaxation: the user tells `ksp-bot-2f` at
  04:49:35Z "응 시스템에서 허용하는 revert라면 괜찮아" (revert-rule policy question was actually
  something `ksp-bot-2f` had prompted about after reviewing `ksportal`'s Jeb-death revert), and again
  the fix is written to memory + CLAUDE.md but doesn't automatically propagate to `ksportal`, which
  is "지금 작업 중(busy)" at the time.
- Net effect: **the multi-agent relay architecture (handoff notes as inter-session memory) is fragile
  by construction** — a dropped clause in a handoff note silently changed the bot's behavior for a
  full sub-session (an entire Minmus-lander arc with two crew deaths), and policy fixes decided
  mid-flight don't reach the session that's actually flying until someone manually re-messages it.

### The permission classifier blocked the revert *and* blocked self-fixing the block
Writeup.md mentions this in one line ("Claude Code의 권한 분류기가 revert 호출을 막은 적이 있다").
The transcript has much more texture:
- `ksportal` tried `revert_to_launch()` via kRPC after Jeb's death; blocked. Diagnosis: "The permission
  system classified it as **'Irreversible Local Destruction'**, because it wipes the current flight
  state." (02:44:41Z)
- It then tried to **write its own permission rule** into `.claude/settings.local.json` to unblock
  future reverts; that was *also* blocked, this time classified as **"Self-Modification."**
- It had no way to escalate its own permissions, so it asked the user to run a literal shell one-liner
  itself: `! printf '%s\n' '{"permissions":{"allow":["Bash(uv run ksp:*)","Bash(uv run
  python:*)"]}}' > .../settings.local.json` (the `!` prefix meaning "run this directly in the
  terminal, not through me").
- The user tried this twice ("생성했는데 됐어?" / "좋아 다시 했어") and it still hadn't taken effect
  each time — the settings file kept coming back empty, needing several rounds of `cat
  .claude/settings.local.json` verification before it stuck.
- Net effect on the career: Jeb's death from Minmus Lander 1 attempt #1 **stands as permanent** in
  the timeline specifically because of this permission deadlock, not because the user's rules
  required it.

### A 40-minute hang nobody detected until the user manually killed it
Around 02:55–02:56, a sandbox re-test of Minmus Lander 1 was launched via `uv run ksp launch ... &&
uv run ksp ascent ...` with **no timeout on the command**. KSP had actually gone unresponsive/closed
in the background, so the command sat blocked indefinitely; the assistant had no liveness signal and
did not notice. The user had to intervene: "내가 껐는데 그냥 한 화면에서 가만히 있길래 거의 40분동안"
(I killed it — it had just been sitting on one screen doing nothing for almost 40 minutes). Its own
diagnosis afterward: "KSP가 꺼져 있어서 샌드박스의 launch 단계가 진행되지 못하고 멈춰 있었던 것
같습니다. 이번에는 타임아웃을 걸고 멈추는 시점에 스크린샷을 찍어 원인을 확인해보겠습니다." From this
point on, commands consistently get explicit `timeout N` wrappers (visible throughout the rest of
both transcripts) — this incident appears to be the origin of that habit, not something planned from
the start.

### kRPC's server doesn't auto-start; had to be reverse-engineered from strings + source
Not mentioned in either doc: to get kRPC running with zero mouse clicks, the session ran `strings -el
KRPC.dll | grep -iE "auto|background|pause|confirm|..."` against the compiled kRPC plugin, then
`git clone --depth 1 --branch v0.6.0 https://github.com/krpc/krpc.git` to read the actual
`autoStartServers` setting-key source, and checked KSP's own `settings.cfg` for a background/focus
setting — all to write a `settings.cfg` for kRPC's `PluginData` that starts the server automatically
at KSP boot without any manual "Start Server" click in a GUI Claude can't see.

### Decompiling KSP wasn't a one-off — it happened twice, for two different reasons
Section "Dev notes" in CLAUDE.md mentions decompiling as a technique but not why or how often it
recurred:
1. **Genesis (23:21, ksp-bot-2f)**: to learn the `.craft` save format, the RD-tech API, facility
   upgrade flow, and surface-attach orientation math before writing the mod at all.
2. **End of the ksportal session (05:41:55–05:42:11Z)**, to debug the new Minmus temperature-survey
   contract: `ilspycmd -t FinePrint.Contracts.Parameters.SurveyWaypointParameter ...` was rerun (had
   to reinstall `ilspycmd`, which wasn't cached anywhere — "ilspycmd not found") to read
   `TriggerRange(FlightBand)` and find that a HIGH-band thermometer's `MaximumTriggerRange` is 15 km,
   a number nowhere in KSP's UI or wiki that the survey-flight-planning code needed exactly.

### The expansion-pack ad popup blocking headless play
Writeup.md's "팝업 대화상자가 진행을 막았다" is generic; the actual popup was **KSP's own DLC/expansion
ad shown at the start of every flight**. The mod's `DismissDialogs()` docstring says exactly this:
"Close popup dialogs (e.g. **the expansion ad shown at flight start**). Returns how many." — added
around 01:59Z of the ksp-bot-2f session, after presumably hitting it enough times to bother writing a
kRPC procedure that calls `UnityEngine.Object.FindObjectsOfType<PopupDialog>()` and dismisses all of
them.

### Screenshot mechanism was replaced mid-project
Genesis started with a fragile **Windows-side PowerShell desktop screenshot** (`tools/screen.ps1`,
using `System.Windows.Forms`/GDI to grab the whole Windows desktop, downscaled with Pillow) because
WSL can't see the Windows screen. This was dropped in favor of kRPC's built-in in-game screenshot
call once discovered — the git log line found while re-orienting in a later commit range literally
reads "Drop desktop screenshot script (kRPC captures the game view)". Not mentioned in either doc.

### A structural-failure debugging pass used systematically named uncrewed probes
LOG.md's "Spawn breakups" entry states the conclusion (autostrut on surface-attached side boosters
breaks them at spawn) but not the method. The transcript shows a methodical isolation test: five
separate uncrewed "Probe A" through "Probe E" launches, each with a different autostrut
configuration, checked via `parts` count and the KSP flight-event log
(`'Structural failure on linkage between BACC "Thumper" Solid Fuel Booster and BACC "Thumper" Solid
Fuel Booster.'`) to isolate exactly which autostrut mode on which part caused the spawn-time
breakup, rather than guessing from a single failed launch.

### JsonUtility couldn't parse the mod's own input format
Small but concrete engineering fact absent from both docs: Unity's built-in `JsonUtility` (the
obvious choice inside a KSP/Unity mod) **failed to parse the craft-spec JSON** at runtime inside KSP,
so the mod ships a small hand-written JSON parser (`Json.cs`) instead of a library dependency.

### Facility level math had an off-by-one bug found within minutes of first use
`Service.cs`'s facility-level reporting used `Mathf.RoundToInt(norm * (count - 1)) + 1` /
`maxLevel = count`, immediately fixed on first real use to `RoundToInt(norm * count) + 1` /
`maxLevel = count + 1` — caught before it ever reached the career (during the very first sandbox
smoke test at 23:30:36Z), so it never shows up as a career incident in LOG.md, but is a real "ship
fast, catch fast" moment worth a line.

---

## 4. Stats

| metric | ksp-bot-2f (87c6169d) | ksportal (c58c5320) | combined |
|---|---|---|---|
| wall-clock start (UTC) | 2026-09-23 23:14:15 | 2026-09-24 02:13:08 | 2026-09-23 23:14:15 |
| wall-clock end (UTC) | 2026-09-24 04:50:03 | 2026-09-24 05:58:13 | 2026-09-24 05:58:13 |
| span | ~5h36m (but only ~1h51m of it is active building/flying; the rest is passive supervision of ksportal) | ~3h45m, essentially all active flying | ~6h44m total, with ~50 min of overlap where both sessions were open at once |
| assistant turns | 440 | 542 | 982 |
| total tool calls | 201 | 236 | 437 |
| Bash calls | 175 | 214 | 389 |
| Read calls | 8 | 12 | 20 |
| Write calls | 10 | 1 | 11 |
| Edit calls | 2 | 5 | 7 |
| `uv run ksp <subcommand>` invocations (regex count, undercounts chained `&&` commands) | 64 | 120 | ≥184 |
| most-used subcommands | ascent (6), status (5), wait (5) | build (15), status (13), recover (10) | — |
| screenshots viewed (`Read` on a `.png`) | 7 | 10 | 17 |
| sub-agents / research tasks launched | 1 (`Agent`, model=sonnet, background, KSP design-guide research) | 0 | 1 |
| model used | claude-opus-5-5 (100%) | claude-opus-5-5 (100%) | claude-opus-5-5 (100%) |
| cross-session `SendMessage` calls | 1 (handoff to `ksportal`) | 1 (handoff to `orca-ksp`) | 2 |
| `ListAgents` calls | 2 | 1 | 3 |
| `AskUserQuestion` calls | 1 (genesis: difficulty/mods/revert) | 0 | 1 |

Notes on the screenshot count: of the 7 in ksp-bot-2f, 1 is a downscaled full-desktop PowerShell
capture (genesis, before kRPC's own screenshot call was adopted) and 1 is a user-supplied image
([Image #1], §1.10) rather than a `ksp shot` output; the rest across both files are `runs/*.png`
game-view captures from `uv run ksp shot`.

The failed deepseek/codex research delegation (§2, 01:05:06Z) is a near-miss data point for stats
purposes: it counts as an attempted but failed research delegation, with the Sonnet `Agent` call at
01:05:17Z as the fallback that actually produced `docs/design-guide.md`.

---

## 5. Mod ideas / standalone-mod candidates mentioned

Beyond writeup.md §8's four items (JSON→craft builder, kRPC career-extension service, save
autoloader, Python flight recorder) and its two "future" bullets (EVA control, real struts), the
transcripts don't surface additional *new* mod-ification ideas — the handoff at the end of ksportal
(05:56:27Z) restates the same two future items nearly verbatim:
1. **EVA support** — kRPC has no EVA API at all; the plan is small additions to KspBot:
   `FlightEVA.fetch.spawnEVA`, `KerbalEVA.PlantFlag`, the EVA kerbal's own science-experiment modules,
   and re-boarding. Explicitly scoped down: "Walking control isn't needed" — just enough for an EVA
   report, a surface sample, and a flag plant. Gated on Astronaut Complex level 2 (75k) for EVA
   outside Kerbin.
2. **Real EAS-4 struts in the craft builder** — would need decompiling the `CompoundPart`/
   `CModuleStrut` save-file format (same `ilspycmd`/`DOTNET_ROLL_FORWARD=Major` toolchain used for
   everything else). Explicitly deprioritized: "Only if wobble becomes a problem; the current fins +
   autostrut fly clean" — i.e., not worth building unless a real failure demands it, consistent with
   the project's stated minimalism principle from the founding prompt.

One item that *could* be read as an implicit mod idea but wasn't framed that way in-session: the
`DismissDialogs()` popup-killer and the `FlightEvents` KSP-log-stream procedure are both small,
generically useful kRPC-adjacent utilities (not KSP-bot-specific) that would work for *any* headless/
scripted KSP control project, not just this one — worth floating in the post as "these two are
probably useful to any kRPC automation, not just ours" even though the transcripts never say that
explicitly.

---

