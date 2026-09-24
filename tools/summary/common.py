import json
import random

OUT = './docs/media/summary/'
RECORD_PATH = './docs/record/career.json'

with open(RECORD_PATH) as _f:
    RECORD = json.load(_f)

ICONS = '''
<svg width="0" height="0" style="position:absolute">
<defs>
<symbol id="i-check" viewBox="0 0 24 24"><path d="M5 12.8l4.3 4.2L19 7.2" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-revert" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 4.5l-4 4 4 4"/><path d="M4.8 8.5H14a5.5 5.5 0 0 1 0 11H8.5"/></g></symbol>
<symbol id="i-skull" viewBox="0 0 24 24"><path fill="currentColor" fill-rule="evenodd" d="M12 2.2c-4.6 0-8.3 3.5-8.3 8 0 2.7 1.3 4.6 3 5.8v3.3c0 .9.7 1.5 1.5 1.5h7.6c.8 0 1.5-.6 1.5-1.5V16c1.7-1.2 3-3.1 3-5.8 0-4.5-3.7-8-8.3-8zM6.6 10.8a2.3 2.3 0 1 0 4.6 0a2.3 2.3 0 1 0-4.6 0zM12.8 10.8a2.3 2.3 0 1 0 4.6 0a2.3 2.3 0 1 0-4.6 0zM12 13.4l-1.3 2.3h2.6zM9.6 17.6h1.1v2.6H9.6zM11.45 17.6h1.1v2.6h-1.1zM13.3 17.6h1.1v2.6h-1.1z"/></symbol>
<symbol id="i-rocket" viewBox="0 0 24 24"><path fill="currentColor" fill-rule="evenodd" d="M12 1.5c3.1 2.6 4.6 6.2 4.6 10.3v4.4H7.4v-4.4c0-4.1 1.5-7.7 4.6-10.3zM10.3 9a1.7 1.7 0 1 0 3.4 0a1.7 1.7 0 1 0-3.4 0z"/><path fill="currentColor" d="M7.4 12.6L4 15.8v3.7l3.4-1.9zM16.6 12.6l3.4 3.2v3.7l-3.4-1.9z"/><path fill="#ffb347" d="M9.6 17.4h4.8L12 22.5z"/></symbol>
<symbol id="i-flask" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 2.8h7"/><path d="M10 2.8v6.4L4.6 18.6A1.8 1.8 0 0 0 6.2 21.4h11.6a1.8 1.8 0 0 0 1.6-2.8L14 9.2V2.8"/></g><path fill="currentColor" d="M7.2 15.2h9.6l2 3.6a1 1 0 0 1-.9 1.5H6.1a1 1 0 0 1-.9-1.5z"/></symbol>
<symbol id="i-coin" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9.6" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="M6.8 12.6l2.2 4.2 4.6-10h3.6" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-building" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"><path d="M2.5 21h19"/><path d="M4.5 21V9.5L12 4l7.5 5.5V21"/><path d="M9.5 21v-6h5v6"/></g></symbol>
<symbol id="i-star" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2.2l2.9 6.3 6.9.7-5.2 4.6 1.5 6.8L12 17.1l-6.1 3.5 1.5-6.8-5.2-4.6 6.9-.7z"/></symbol>
<symbol id="i-flag" viewBox="0 0 24 24"><path d="M6 21.5V3" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path fill="currentColor" d="M6.5 3.5h12l-2.6 4.5 2.6 4.5h-12z"/></symbol>
<symbol id="i-boom" viewBox="0 0 24 24"><path fill="currentColor" d="M12 1.5l2 5.6 5.2-3-1.9 5.6 5.2 1.3-4.9 2.4 3.4 4.6-5.6-.9-.4 5.9-3-4.9-3 4.9-.4-5.9-5.6.9 3.4-4.6L1.5 11l5.2-1.3-1.9-5.6 5.2 3z"/></symbol>
<symbol id="i-respawn" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3"/><path d="M19.8 3.8v4.6h-4.6"/></g><circle cx="12" cy="12" r="2.6" fill="currentColor"/></symbol>
<symbol id="i-orbit" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4.2" fill="currentColor"/><ellipse cx="12" cy="12" rx="10" ry="4.6" transform="rotate(-25 12 12)" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
<symbol id="i-chute" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2.5 10.5a9.5 8 0 0 1 19 0"/><path d="M2.5 10.5L12 19.5l9.5-9M12 10.5v9M7.5 10.5 12 19.5l4.5-9"/></g><rect x="9.8" y="18.6" width="4.4" height="3.6" rx="1" fill="currentColor"/></symbol>
<symbol id="i-pad" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"/><path d="M6 21V5M6 8h4M6 12h4M6 16h4"/></g><path fill="currentColor" d="M15 4c1.6 1.4 2.3 3.2 2.3 5.3V17h-4.6V9.3C12.7 7.2 13.4 5.4 15 4z"/></symbol>
<symbol id="i-air" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M3 8.5h11a3 3 0 1 0-3-3"/><path d="M3 13h16a3 3 0 1 1-3 3"/><path d="M3 17.5h7"/></g></symbol>
<symbol id="i-wrench" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" d="M14.5 6.5a4 4 0 0 0 5.3 4.9l-9.4 9.4a2.1 2.1 0 0 1-3-3l9.4-9.4a4 4 0 0 0-4.9-5.3l2.9 2.9z"/></symbol>
<symbol id="i-shield" viewBox="0 0 24 24"><path fill="none" stroke="currentColor" stroke-width="2.3" stroke-linejoin="round" d="M12 2.8l7.5 3v5.5c0 4.8-3.2 8.3-7.5 9.9-4.3-1.6-7.5-5.1-7.5-9.9V5.8z"/><path fill="currentColor" d="M12 6.5l4.5 1.8v3c0 3-1.9 5.3-4.5 6.4z"/></symbol>
<symbol id="i-fin" viewBox="0 0 24 24"><path fill="currentColor" d="M9 2.5h3.5v19H9zM12.5 9l7 9v3.5h-7z"/><path fill="currentColor" opacity=".55" d="M9 9l-4.5 7v5.5H9z"/></symbol>
<symbol id="i-tank" viewBox="0 0 24 24"><rect x="6" y="3" width="12" height="18" rx="3" fill="none" stroke="currentColor" stroke-width="2.3"/><path fill="currentColor" d="M8.3 12h7.4v5.2a1.6 1.6 0 0 1-1.6 1.6H9.9a1.6 1.6 0 0 1-1.6-1.6z"/></symbol>
<symbol id="i-leg" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3h8v7H8z"/><path d="M8 8.5L3.5 19M16 8.5l4.5 10.5"/><path d="M1.5 20.5h4M18.5 20.5h4"/></g></symbol>
<symbol id="i-bolt" viewBox="0 0 24 24"><path fill="currentColor" d="M13.8 1.8L4.5 13.6h6.3l-1.3 8.6 9.3-11.8h-6.3z"/></symbol>
<symbol id="i-planet" viewBox="0 0 24 24"><circle cx="12" cy="12" r="6.4" fill="currentColor"/><ellipse cx="12" cy="12" rx="10.5" ry="3.3" transform="rotate(-20 12 12)" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
<symbol id="i-dot" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5" fill="currentColor"/><circle cx="12" cy="12" r="9.5" fill="none" stroke="currentColor" stroke-width="1.8"/></symbol>
<symbol id="i-gyro" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2.2"/><circle cx="12" cy="12" r="3.3" fill="currentColor"/><path d="M12 3v4.5M12 16.5V21M3 12h4.5M16.5 12H21" stroke="currentColor" stroke-width="2.2"/></symbol>
<symbol id="i-lock" viewBox="0 0 24 24"><rect x="5" y="10.5" width="14" height="10.5" rx="2.2" fill="currentColor"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" fill="none" stroke="currentColor" stroke-width="2.3"/></symbol>
<symbol id="i-arrow" viewBox="0 0 24 24"><path d="M4 12h15M13 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-kerbal" viewBox="0 0 24 24"><ellipse cx="12" cy="12.5" rx="9.5" ry="8.2" fill="currentColor"/><circle cx="8.3" cy="10.8" r="2.7" fill="#fff"/><circle cx="15.7" cy="10.8" r="2.7" fill="#fff"/><circle cx="8.8" cy="11" r="1.2" fill="#111"/><circle cx="15.2" cy="11" r="1.2" fill="#111"/><path d="M8 16c2.3 1.8 5.7 1.8 8 0" fill="none" stroke="#111" stroke-width="1.3" stroke-linecap="round"/></symbol>
</defs></svg>'''


def icon(name, size=24, color=None, cls='', style=''):
    c = f'color:{color};' if color else ''
    return f'<svg class="ic {cls}" width="{size}" height="{size}" style="{c}{style}"><use href="#i-{name}"/></svg>'


def stars(seed=7, n=170, w=1080, h=1350):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.choice([0.5, 0.6, 0.7, 0.8, 1.0, 1.2])
        o = rnd.uniform(0.15, 0.6)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" opacity="{o:.2f}"/>')
    return f'<svg class="stars" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(out)}</svg>'


BASE_CSS = '''
:root{
  --bg:#070b17; --bg2:#0d1428; --panel:rgba(255,255,255,.045); --panel2:rgba(255,255,255,.075);
  --line:rgba(255,255,255,.10); --text:#eef2ff; --muted:#8e98b6; --dim:#5c6684;
  --ok:#35d67c; --rev:#ff9a2e; --dead:#ff4d5e; --pad:#7d879c; --sci:#56c8ff; --fund:#f7d75c; --tech:#b28cff;
  --kerbin:#3f9be0; --mun:#a9adb5; --minmus:#a8e8cf; --duna:#d9663e; --gold:#ffcf4a;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1350px;overflow:hidden}
body{background:radial-gradient(1200px 800px at 85% -10%, #1a2550 0%, rgba(26,37,80,0) 60%),
  radial-gradient(900px 700px at -10% 110%, #1a1440 0%, rgba(26,20,64,0) 60%), var(--bg);
  color:var(--text); font-family:'Space Grotesk',system-ui,sans-serif; position:relative;
  -webkit-font-smoothing:antialiased}
.stars{position:absolute;inset:0;z-index:0;pointer-events:none}
.page{position:absolute;inset:0;padding:52px 56px 0;z-index:1}
.ic{display:inline-block;vertical-align:middle;flex:none}
.mono{font-family:'JetBrains Mono',ui-monospace,monospace}
.kicker{display:flex;align-items:center;gap:10px;font-size:19px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:500}
.kicker b{color:var(--text);font-weight:700}
.title{font-size:76px;font-weight:700;letter-spacing:-.03em;line-height:1;margin-top:10px}
.footer{position:absolute;left:56px;right:56px;bottom:30px;display:flex;justify-content:space-between;align-items:center;
  font-size:17px;color:var(--dim);letter-spacing:.06em;z-index:2}
.footer .dots{display:flex;gap:8px}
.footer .dots i{width:9px;height:9px;border-radius:50%;background:#2a3350;display:block}
.footer .dots i.on{background:var(--muted)}
.legend{display:flex;gap:22px;align-items:center;font-size:19px;color:var(--muted);font-weight:500}
.legend span{display:flex;align-items:center;gap:8px}
.chip{display:inline-flex;align-items:center;justify-content:center;border-radius:9px;color:#fff;font-weight:700}
.c-ok{background:var(--ok);color:#06240f}
.c-rev{background:var(--rev);color:#2b1400}
.c-dead{background:var(--dead);color:#fff}
.c-pad{background:var(--pad)}
'''

HEAD = '''<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=block" rel="stylesheet">
<style>{css}</style></head><body>'''


def page(title, css, body, idx, total=5, seed=7):
    dots = ''.join(f'<i class="{"on" if i == idx else ""}"></i>' for i in range(1, total + 1))
    footer = f'<div class="footer"><span>KSP 1.12 · career · flown by Claude</span><span class="dots">{dots}</span></div>'
    return HEAD.format(title=title, css=BASE_CSS + css) + ICONS + stars(seed) + f'<div class="page">{body}</div>' + footer + '</body></html>'


def legend(items=('ok', 'rev', 'dead'), size=26):
    lab = {'ok': ('check', 'Success'), 'rev': ('revert', 'Revert'), 'dead': ('skull', 'Crew lost')}
    out = []
    for k in items:
        ic, t = lab[k]
        out.append(f'<span><i class="chip c-{k}" style="width:{size}px;height:{size}px;border-radius:7px">{icon(ic, size-8)}</i>{t}</span>')
    return '<div class="legend">' + ''.join(out) + '</div>'


def write(name, html):
    with open(OUT + name, 'w') as f:
        f.write(html)


def fmt_funds(n):
    """25000 -> '25k', 1299942 -> '1.30M' (matches career.json funds_timeline label style)."""
    if n >= 1_000_000:
        return f'{n / 1_000_000:.2f}M'
    return f'{round(n / 1000)}k'


_pid = [0]


def planet(kind, size, dashed=False):
    """Simple SVG planet disc: base gradient + surface features + terminator shade."""
    _pid[0] += 1
    p = f'p{_pid[0]}'
    base = {'kerbin': ('#5bb6f0', '#1f5fae', '#0c2c5c'), 'mun': ('#d3d6dc', '#9a9ea7', '#4b4f58'),
            'minmus': ('#e6fff4', '#a5e6cc', '#4f8f7b'), 'duna': ('#f09a6c', '#c4552c', '#5e2210')}[kind]
    feats = {
        'kerbin': '<path d="M18 30c8-6 18-4 22 3s12 6 14 14-8 12-15 9-10 4-17 1-11-21-4-27z" fill="#4fae4c"/>'
                  '<path d="M60 58c6-3 14 0 16 6s-4 12-11 11-12-4-10-9z" fill="#5cbf55"/>'
                  '<path d="M52 18c5-2 11 0 12 4s-5 6-9 5-6-7-3-9z" fill="#56b851"/>'
                  '<ellipse cx="50" cy="4" rx="22" ry="7" fill="#f4f8ff" opacity=".9"/><ellipse cx="50" cy="97" rx="20" ry="6" fill="#f4f8ff" opacity=".9"/>',
        'mun': '<circle cx="34" cy="36" r="9" fill="#7f838c"/><circle cx="62" cy="58" r="12" fill="#858992"/><circle cx="44" cy="72" r="6" fill="#7b7f88"/>'
               '<circle cx="70" cy="28" r="5" fill="#80848d"/><circle cx="24" cy="60" r="4" fill="#80848d"/>',
        'minmus': '<path d="M14 44c10-8 26-6 34 0s20 4 26 10-6 12-20 10-22 2-32-2-14-12-8-18z" fill="#f2fffa" opacity=".85"/>'
                  '<path d="M40 16c8-2 16 2 16 6s-10 6-16 4-6-8 0-10z" fill="#d6fbee"/>'
                  '<path d="M30 78c8-3 20-2 22 3s-10 7-18 5-9-6-4-8z" fill="#d6fbee"/>',
        'duna': '<path d="M16 40c10-6 20 0 28-4s18 2 20 8-10 10-20 8-16 6-24 2-12-10-4-14z" fill="#a8411f"/>'
                '<path d="M52 66c8-2 16 2 16 7s-10 7-16 5-6-10 0-12z" fill="#b24823"/>'
                '<ellipse cx="50" cy="5" rx="20" ry="7" fill="#fff3ea"/>',
    }[kind]
    stroke = '<circle cx="50" cy="50" r="49" fill="none" stroke="#ff9d73" stroke-width="1.6" stroke-dasharray="4 4"/>' if dashed else ''
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" class="planet">'
            f'<defs><radialGradient id="{p}g" cx="38%" cy="34%" r="70%"><stop offset="0" stop-color="{base[0]}"/>'
            f'<stop offset=".55" stop-color="{base[1]}"/><stop offset="1" stop-color="{base[2]}"/></radialGradient>'
            f'<radialGradient id="{p}s" cx="30%" cy="28%" r="85%"><stop offset=".45" stop-color="#000" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#000" stop-opacity=".65"/></radialGradient>'
            f'<clipPath id="{p}c"><circle cx="50" cy="50" r="46"/></clipPath></defs>'
            f'<circle cx="50" cy="50" r="46" fill="url(#{p}g)"/><g clip-path="url(#{p}c)" opacity=".9">{feats}</g>'
            f'<circle cx="50" cy="50" r="46" fill="url(#{p}s)"/>{stroke}</svg>')


RES = {'ok': ('check', 'c-ok'), 'rev': ('revert', 'c-rev'), 'dead': ('skull', 'c-dead')}

# career.json uses the save's own result wording; the images use these short codes.
RESULT_CODE = {'success': 'ok', 'reverted': 'rev', 'crew lost': 'dead'}

# n, craft slug, result, destination, short stat blurb, crew note -- straight from docs/record/career.json
LAUNCHES = [
    (l['n'], l['slug'], RESULT_CODE[l['result']], l['dest'], l.get('stat', ''), l.get('crew', ''))
    for l in RECORD['career_launches']
]

# launch numbers whose note is flagged as a career first (note text uses "FIRST" in caps), mapped to the body reached
FIRSTS = {l['n']: l['dest'] for l in RECORD['career_launches'] if 'FIRST' in l['note']}

# craft slug -> display name: first career_launches row for that slug, then any photographed sandbox craft
CRAFT_NAMES = {}
for l in RECORD['career_launches']:
    CRAFT_NAMES.setdefault(l['slug'], l['craft'])
for _entry in RECORD.get('sandbox_test_crafts', []):
    for _c in _entry.get('crafts', []):
        CRAFT_NAMES[_c['slug']] = _c['name']
