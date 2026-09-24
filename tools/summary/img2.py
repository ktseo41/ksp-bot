from common import *

# career crafts, first-appearance order, deduped -- straight from docs/record/career.json career_launches
career = list(dict.fromkeys(slug for _, slug, *_ in LAUNCHES))
# photographed sandbox crafts, in record order (only entries with a "crafts" list get a card here)
sandbox = [c['slug'] for entry in RECORD.get('sandbox_test_crafts', []) for c in entry.get('crafts', [])]

rec = {}
for n, slug, r, *_ in LAUNCHES:
    rec.setdefault(slug, []).append((n, r))
assert sum(len(v) for v in rec.values()) == len(LAUNCHES)

css = '''
.hdr{display:flex;justify-content:space-between;align-items:flex-end}
.title{font-size:70px}
.title small{font-size:34px;color:var(--muted);font-weight:500;margin-left:10px;letter-spacing:0}
.grid{display:grid;grid-template-columns:repeat(6,1fr);gap:12px 10px;margin-top:24px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;overflow:hidden;display:flex;flex-direction:column}
.card .ph{position:relative;height:254px;overflow:hidden}
.card .ph img{width:100%;height:100%;object-fit:cover;display:block}
.card .ph .cnt{position:absolute;top:7px;right:7px;background:rgba(7,11,23,.78);border-radius:8px;padding:3px 8px;font-size:17px;font-weight:700;display:flex;align-items:center;gap:4px}
.card .nm{font-size:16.5px;font-weight:700;padding:9px 9px 0;white-space:nowrap;letter-spacing:-.01em}
.card .pills{display:flex;flex-wrap:wrap;gap:4px;padding:8px 9px 10px;min-height:80px;align-content:flex-start}
.pill{width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:700;position:relative}
.pill.first{box-shadow:0 0 0 2.5px var(--gold)}
.pill .st{position:absolute;top:-9px;right:-9px}
.pill .sk{position:absolute;top:-8px;right:-8px;background:#070b17;border-radius:50%;padding:2px;display:flex}
.grp{display:flex;align-items:center;gap:12px;margin-top:18px;font-size:20px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
.grp .ln{flex:1;height:1px;background:var(--line)}
.grid2{display:grid;grid-template-columns:repeat(4,1fr) 44px 1fr;gap:10px;margin-top:14px;align-items:stretch}
.sb{border:1px dashed rgba(120,170,255,.35);background:rgba(60,110,220,.07);border-radius:16px;overflow:hidden}
.sb .ph{height:238px;position:relative;overflow:hidden}
.sb .ph img{width:100%;height:100%;object-fit:cover;display:block;filter:grayscale(1) contrast(1.1) brightness(.9)}
.sb .ph::after{content:"";position:absolute;inset:0;background:
  linear-gradient(rgba(120,170,255,.16) 1px,transparent 1px) 0 0/18px 18px,
  linear-gradient(90deg,rgba(120,170,255,.16) 1px,transparent 1px) 0 0/18px 18px,
  rgba(30,80,200,.38);mix-blend-mode:normal}
.sb .nm{font-size:15.5px;font-weight:600;color:#b9c9ec;padding:7px 9px 8px;line-height:1.15}
.arrow{display:flex;align-items:center;justify-content:center;color:var(--dim)}
.duna{border:2px dashed #ff9d73;border-radius:16px;overflow:hidden;position:relative;background:rgba(217,102,62,.08)}
.duna .ph{height:238px;position:relative;overflow:hidden}
.duna .ph img{width:100%;height:100%;object-fit:cover;display:block;filter:saturate(.9)}
.duna .nm{display:flex;align-items:center;gap:8px;font-size:18px;font-weight:700;color:#ffb08e;padding:8px 10px 10px}
.duna .tag{position:absolute;top:8px;left:8px;font-size:15px;font-weight:700;letter-spacing:.14em;color:#2a0e04;background:#ff9d73;border-radius:999px;padding:3px 10px}
.duna .pl{position:absolute;right:-18px;top:-18px;opacity:.95}
'''


def pills(slug):
    out = []
    for n, r in rec[slug]:
        cls = RES[r][1]
        first = ' first' if n in FIRSTS else ''
        extra = ''
        if n in FIRSTS:
            extra += f'<span class="st">{icon("star", 20, "#ffcf4a")}</span>'
        if r == 'dead':
            extra += f'<span class="sk">{icon("skull", 16, "#ff4d5e")}</span>'
        out.append(f'<div class="pill {cls}{first}">{n}{extra}</div>')
    return ''.join(out)


cards = ''.join(
    f'<div class="card"><div class="ph"><img src="crafts/{s}.jpg"></div><div class="nm">{CRAFT_NAMES[s]}</div>'
    f'<div class="pills">{pills(s)}</div></div>' for s in career)
sbc = ''.join(
    f'<div class="sb"><div class="ph"><img src="crafts/{s}.jpg"></div><div class="nm">{CRAFT_NAMES[s]}</div></div>' for s in sandbox)

body = f'''
<div class="hdr">
  <div>
    <div class="kicker">{icon('rocket', 26, '#8e98b6')}<span>Crafts</span></div>
    <div class="title">{len(career)} <small>career</small> <span style="color:var(--dim);font-weight:500">+</span> {len(sandbox)} <small>sandbox</small></div>
  </div>
  {legend()}
</div>
<div class="grid">{cards}</div>
<div class="grp">{icon('flask', 22, '#7fa8ff')}<span style="color:#9bb8f2">Sandbox</span><span class="ln"></span>
  <span style="color:#ffb08e">Next</span>{icon('flag', 22, '#ff9d73')}</div>
<div class="grid2">{sbc}<div class="arrow">{icon('arrow', 30)}</div>
  <div class="duna"><div class="ph"><img src="crafts/duna-1.jpg"></div>
  <div class="nm">{planet('duna', 26)} Duna 1</div></div>
</div>
'''

write('02-crafts.html', page('Craft catalog', css, body, 2, seed=11))
