# Career summary images

Shareable images for the user's blog/X posts (`docs/media/summary/0N-*.png`, 1080×1350 @2x, almost no text).

## Keep the record current (every mission, not at the end)
- `docs/record/career.json` → `career_launches`: append one entry per career launch right after it ends
  (`n`, `craft`, `goal`, `result` = success | reverted | crew lost | pad test, `note`, plus crew, date, UT).
  Also update `kerbals`, `firsts`, `career_now` when they change. LOG.md stays the narrative journal.
- New craft design → pad photo in the sandbox right away:
  `uv run python tools/summary/shoot_crafts.py crafts/<spec>.json` (daylight, UI hidden, camera heading 270 = sun
  behind the camera) → `runs/craft-<slug>.png`; crop into `docs/media/summary/crafts/` (`crop.py`).
- After recovery at the space center: `uv run python tools/summary/extract_save.py` → `docs/record/career-save.json`.
- Crew portraits: `shoot_portraits.py` (sandbox; needs `UI_SCALE_CREW = 2` in KSP's settings.cfg, set while KSP is
  closed; the in-flight crew portrait is the only reliable real face shot).

## Regenerate
`python tools/summary/imgN.py` writes `docs/media/summary/0N-*.html`, then render:
`google-chrome --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 --window-size=1080,1350 --virtual-time-budget=8000 --screenshot=OUT.png file://ABS.html`
(`--virtual-time-budget` lets the web fonts load; without it text vanishes).
TODO: img1–img3 still carry hard-coded launch data; make them read `docs/record/career.json` (and img5 now uses
`docs/media/summary/crew/*.png` portraits — edit img5.py to match the hand-edited 05-crew.html before regenerating).
