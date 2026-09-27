# Career summary images

Shareable images for the user's blog/X posts, 1080×1350 @2x.
- **v2 (current, 10 cards)**: `docs/media/summary/v2/NN-slug.{html,png}`, scripts in `tools/summary/v2/`, plan in
  `docs/summary-cards-plan.md`.
- **v1 (day-1 snapshot)**: `docs/media/summary/0N-*.png` (2026-09-24, launches #1-#20). `img1-5.py` are kept as they are
  and can't be regenerated from today's `career.json` (hard-coded #1-#20 layout, fields v2 removed, `career-save.json`).

## v2: regenerate
`python3 tools/summary/v2/build.py` (or `... build.py 01 07` for some cards): crops the photos into
`docs/media/summary/v2/img/`, writes the ten HTML files, renders each with headless Chrome
(`--window-size=1080,1350 --force-device-scale-factor=2 --virtual-time-budget=8000`) and checks every PNG is 2160×2700.
Fonts (Space Grotesk, JetBrains Mono, Noto Sans KR) load from Google Fonts: offline, the text disappears, so open the
PNGs after a build. Never touches the game.

Cards: 01 scoreboard · 02 journey (map + what is flying) · 03 how (command pipeline) · 04/05 launches (first/second half)
· 06 crafts · 07 science · 08 crew · 09 failures · 10 game time.

Rules the scripts keep: every number and name on a card comes from `docs/record/career.json` (scripts hold only layout,
colours, icons, the photo/crop table in `common2.py` and the KSP calendar 21,600 s/day, 426 days/year); rendering is
rule-based (no per-launch layout); each headline is <= 18 characters (asserted); values derived from the current UT or
marked `approx` get a `~`.

## v2: keep the data current (at the end of every mission, in `docs/record/career.json`)
- `career_launches`: the new launch (`n, craft, slug, dest, stat, crew, result, date, note`; `revert_death_count`,
  `diverted_to` when they apply). Results: success, reverted, crew lost, failed, partial, in progress, en route.
- `career_now`: `ut`, `funds`, `science`, `reputation`, `facilities`, `real_days`, `date`; a `funds_timeline` point
  (`tick` "#n" or "facility" + `facility`; `funds` null when the LOG has no balance).
- `firsts` (a new first: `n, body, kind, who, label_ko`), `crafts` (only the six on card 06).
- `live_missions` (`type` probe/crewed/station/satellite, `body`, `from`/`to` while in transit, `next_ko`, `next_ut`,
  `sci_aboard`); remove a mission when it ends.
- `ut_anchors.past/future` (move an anchor to `past` once it happened), `real_days` (the last day's `ut_end`).
- `science_hauls` (big recoveries/transmissions), `science_aboard`, `research` (+ `research_names`).
- `kerbals.roster` (`status_ko`, `flights`, deaths), `kerbals.rescued`, `incidents` (`text_ko` <= 28 characters,
  `hidden` to keep one off card 09), `landings_by_body`.

## Pad photos (cards 04/05 show a placeholder when one is missing)
None missing as of #53. For a new design: `shoot_crafts.py` when the game is free, crop into
`docs/media/summary/crafts/<slug>.jpg` (`tools/summary/crop.py <slug>`: add its fractions to `C` first; with slugs it
crops only those), and add the slug to `_OLD` in `v2/common2.py`. A crewed pod without a probe core needs
`SHOOT_CREW="<name>"` (KSP otherwise stops at "Warning: No Control!"); in the sandbox hire a fresh kerbal per craft
(`ksp hire`: a kerbal just recovered isn't available again at once). `daylight()` waits for a morning sun (east,
behind the camera): an afternoon sun backlights the rocket.
Stand-ins in use: keo-relay-2/3 and mun-sat-1 show keo-relay-1, rescue-5/6 show rescue-3 (same design; Mun Sat 1 = Keo
Relay 3 + three small science parts, a sandbox photo of its own would be better); eve-1, minmus-lab-1,
minmus-science-1, polar-relay-1, keo-relay-1, rescue-1/3/4 use in-flight shots. jool-1, ike-station-1, mun-tanker-1,
rescue-2, salvage-1 and salvage-2 now have proper sandbox pad photos (`crop.py`), replacing the earlier
too-small/HUD-cropped stand-ins.
Milestone shots (crops in `CROPS`): card 02's Eve 2 row shows the carrier on Gilly (`eve-2-gilly`), card 07's Eve 2
haul the lander in Eve's sea (`eve-2-splash`).

## Record, pad photos, portraits (both sets)
- `docs/record/career.json` → `career_launches`: append one entry per career launch right after it ends
  (`n`, `craft`, `goal`, `result` = success | reverted | crew lost | pad test, `note`, plus crew, date, UT).
  Also update `kerbals`, `firsts`, `career_now` when they change. LOG.md stays the narrative journal.
- New craft design → pad photo in the sandbox right away:
  `uv run python tools/summary/shoot_crafts.py crafts/<spec>.json` (daylight, UI hidden, camera heading 270 = sun
  behind the camera) → `runs/craft-<slug>.png`; crop into `docs/media/summary/crafts/` (`crop.py`).
- After recovery at the space center: `uv run python tools/summary/extract_save.py` → `docs/record/career-save.json`.
- Crew portraits: `shoot_portraits.py` (sandbox; needs `UI_SCALE_CREW = 2` in KSP's settings.cfg, set while KSP is
  closed; the in-flight crew portrait is the only reliable real face shot).

## v1: regenerate (historical)
`python tools/summary/imgN.py` writes `docs/media/summary/0N-*.html`, then render:
`google-chrome --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 --window-size=1080,1350 --virtual-time-budget=8000 --screenshot=OUT.png file://ABS.html`
(`--virtual-time-budget` lets the web fonts load; without it text vanishes).
v1 is a snapshot: img1/img3/img4 need fields that v2 replaced (`science_by_body`, `funds_timeline_facility_markers`,
the #1-#20 layout) and img4/img5 read the 09-24 `career-save.json`; don't regenerate them.
