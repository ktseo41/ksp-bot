"""Shared pieces for the v2 progress cards (docs/summary-cards-plan.md).

Everything shown on a card comes from docs/record/career.json (RECORD). This module only holds layout, colours,
icons and the photo/crop table (which picture belongs to which craft slug).
"""
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from common import ICONS, BASE_CSS, RECORD, icon, stars, planet as planet1, fmt_funds  # noqa: E402,F401

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.join(ROOT, 'docs', 'media', 'summary', 'v2') + '/'
IMG = OUT + 'img/'
MEDIA = os.path.join(ROOT, 'docs', 'media') + '/'
TOTAL = 10

CN = RECORD['career_now']
LAUNCHES = RECORD['career_launches']
BY_N = {l['n']: l for l in LAUNCHES}

# KSP calendar (same constants as kspbot/flight.py)
DAY_S = 21600
YEAR_D = 426


def ut_to_days(ut):
    return ut / DAY_S


def fmt_ydays(days):
    """1262.2 -> '2y 410d' (Kerbin years of 426 days)."""
    d = int(days)
    y, r = divmod(d, YEAR_D)
    return f'{y}y {r}d' if y else f'{r}d'


def days_from_now(ut):
    return (ut - CN['ut']) / DAY_S


def esc(s):
    return html.escape(str(s), quote=False)


def num(n, dec=0):
    """thousands separator: 4246 -> '4,246'."""
    return f'{n:,.{dec}f}'


KO_NUM = {1: '하나', 2: '둘', 3: '셋', 4: '넷', 5: '다섯', 6: '여섯', 7: '일곱', 8: '여덟', 9: '아홉'}
KO_ORD = {1: '첫째', 2: '둘째', 3: '셋째', 4: '넷째', 5: '다섯째'}

# ---------------------------------------------------------------- results
RESULT_CODE = {'success': 'ok', 'reverted': 'rev', 'crew lost': 'dead', 'failed': 'fail', 'partial': 'fail',
               'in progress': 'live', 'en route': 'live'}
RES = {'ok': ('check', 'c-ok'), 'rev': ('revert', 'c-rev'), 'dead': ('skull', 'c-dead'),
       'fail': ('cross', 'c-fail'), 'live': ('live', 'c-live')}
RES_LABEL = {'ok': 'Success', 'rev': 'Revert', 'dead': 'Crew lost', 'fail': 'Failed', 'live': 'In flight'}
RES_TINT = {'ok': '53,214,124', 'rev': '255,154,46', 'dead': '255,77,94', 'fail': '142,152,182', 'live': '86,200,255'}


def code(l):
    return RESULT_CODE[l['result']]


def legend(items=('ok', 'rev', 'dead', 'fail', 'live'), size=24):
    out = []
    for k in items:
        ic, cls = RES[k]
        out.append(f'<span><i class="chip {cls}" style="width:{size}px;height:{size}px;border-radius:7px">{icon(ic, size - 8)}</i>{RES_LABEL[k]}</span>')
    return '<div class="legend">' + ''.join(out) + '</div>'


# ---------------------------------------------------------------- bodies
BODY_NAME = {'kerbin': 'Kerbin', 'mun': 'Mun', 'minmus': 'Minmus', 'duna': 'Duna', 'eve': 'Eve', 'moho': 'Moho',
             'dres': 'Dres', 'jool': 'Jool', 'ike': 'Ike', 'kerbol': 'Kerbol'}
# display order (the order they were reached); Dres/Jool last = farthest (Dres 1, Jool 1 are still on their way)
BODY_ORDER = ['kerbin', 'minmus', 'mun', 'duna', 'eve', 'moho', 'dres', 'jool']


def dest_body(dest):
    """career_launches dest -> (planet kind, in orbit?). 'kerbin-orbit' -> ('kerbin', True)."""
    if dest.endswith('-orbit'):
        return dest[:-6], True
    return dest, False


def dest_html(dest, size=26, cls='dst'):
    kind, orb = dest_body(dest)
    o = icon('orbit', size - 6, '#8e98b6') if orb else ''
    return f'<span class="{cls}">{planet(kind, size)}{BODY_NAME[kind]}{o}</span>'


_qid = [0]
EXTRA = {
    'eve': (('#c9a2ea', '#7a3fa6', '#2a1238'),
            '<path d="M14 36c10-6 22-2 30-6s18 0 22 6-8 10-20 9-18 5-26 1-12-6-6-10z" fill="#9a5fc8" opacity=".8"/>'
            '<path d="M48 62c8-3 18 0 20 5s-9 8-17 6-8-8-3-11z" fill="#5c2a86" opacity=".9"/>'
            '<path d="M22 70c5-2 11 0 12 3s-6 5-10 4-5-5-2-7z" fill="#6c3596"/>'),
    'jool': (('#b9e48c', '#5f9a44', '#1e3d17'),
             '<path d="M0 30 Q50 22 100 30 L100 38 Q50 30 0 38Z" fill="#4c8a34" opacity=".75"/>'
             '<path d="M0 50 Q50 44 100 50 L100 56 Q50 50 0 56Z" fill="#8cc860" opacity=".55"/>'
             '<path d="M0 68 Q50 62 100 68 L100 76 Q50 70 0 76Z" fill="#3f7a2c" opacity=".7"/>'
             '<ellipse cx="64" cy="60" rx="9" ry="5" fill="#2f5e22" opacity=".8"/>'),
    'moho': (('#d8a88a', '#9a5f45', '#3c2016'),
             '<circle cx="34" cy="38" r="9" fill="#7e4a34"/><circle cx="62" cy="62" r="11" fill="#84503a"/>'
             '<circle cx="66" cy="30" r="5" fill="#7e4a34"/><circle cx="30" cy="68" r="4" fill="#84503a"/>'),
    'dres': (('#d6cfc4', '#8f877b', '#35312b'),
             '<path d="M6 40 Q30 34 52 44 T98 40" fill="none" stroke="#5f584e" stroke-width="5" opacity=".8"/>'
             '<path d="M10 62 Q40 56 60 64 T96 60" fill="none" stroke="#6b6358" stroke-width="3" opacity=".7"/>'
             '<circle cx="36" cy="26" r="6" fill="#7a7266"/><circle cx="66" cy="76" r="8" fill="#7a7266"/>'),
    'ike': (('#b8b6b2', '#77746f', '#35332f'),
            '<circle cx="36" cy="40" r="10" fill="#6a6762"/><circle cx="64" cy="64" r="8" fill="#6d6a65"/>'
            '<circle cx="60" cy="28" r="5" fill="#6d6a65"/>'),
    'kerbol': (('#fff6c8', '#ffd24a', '#f08a16'), ''),
}


def planet(kind, size, dashed=False):
    if kind not in EXTRA:
        return planet1(kind, size, dashed)
    _qid[0] += 1
    p = f'q{_qid[0]}'
    base, feats = EXTRA[kind]
    if kind == 'kerbol':
        return (f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" class="planet"><defs>'
                f'<radialGradient id="{p}g" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{base[0]}"/>'
                f'<stop offset=".6" stop-color="{base[1]}"/><stop offset="1" stop-color="{base[2]}"/></radialGradient>'
                f'<radialGradient id="{p}h" cx="50%" cy="50%" r="50%"><stop offset=".6" stop-color="#ffcf4a" stop-opacity=".35"/>'
                f'<stop offset="1" stop-color="#ffcf4a" stop-opacity="0"/></radialGradient></defs>'
                f'<circle cx="50" cy="50" r="50" fill="url(#{p}h)"/><circle cx="50" cy="50" r="30" fill="url(#{p}g)"/></svg>')
    stroke = ('<circle cx="50" cy="50" r="49" fill="none" stroke="#a8d97a" stroke-width="1.6" stroke-dasharray="4 4"/>'
              if dashed else '')
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" class="planet">'
            f'<defs><radialGradient id="{p}g" cx="38%" cy="34%" r="70%"><stop offset="0" stop-color="{base[0]}"/>'
            f'<stop offset=".55" stop-color="{base[1]}"/><stop offset="1" stop-color="{base[2]}"/></radialGradient>'
            f'<radialGradient id="{p}s" cx="30%" cy="28%" r="85%"><stop offset=".45" stop-color="#000" stop-opacity="0"/>'
            f'<stop offset="1" stop-color="#000" stop-opacity=".65"/></radialGradient>'
            f'<clipPath id="{p}c"><circle cx="50" cy="50" r="46"/></clipPath></defs>'
            f'<circle cx="50" cy="50" r="46" fill="url(#{p}g)"/><g clip-path="url(#{p}c)" opacity=".9">{feats}</g>'
            f'<circle cx="50" cy="50" r="46" fill="url(#{p}s)"/>{stroke}</svg>')


def orbit_ring(cx, cy, r, dashed=False, color='rgba(255,255,255,.14)', width=1.6):
    d = ' stroke-dasharray="5 7"' if dashed else ''
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" stroke="{color}" stroke-width="{width}"{d}/>'


# ---------------------------------------------------------------- photos
# slug -> picture, relative to docs/media/summary/v2/*.html. None = no photo yet (placeholder, README list).
_OLD = ['hopper-1', 'sounding-2', 'orbiter-1', 'minmus-flyby-1', 'minmus-lander-1', 'mun-lander-1', 'sounding-3',
        'pad-lab', 'mun-lander-2', 'mun-lander-3', 'mun-lander-5', 'mun-lander-6', 'mun-lander-7', 'duna-1',
        'jool-1', 'ike-station-1', 'mun-tanker-1', 'rescue-2', 'salvage-1', 'salvage-2', 'moho-1', 'eve-2']
PHOTOS = {s: f'../crafts/{s}.jpg' for s in _OLD}
# crop table (plan §5.3): out name -> (source in docs/media, box x0, y0, x1, y1 on the 1280x720 original)
CROPS = {
    'eve-1': ('2026-09-26_eve-1_eve-pass.png', (400, 0, 880, 690)),
    'minmus-lab-1': ('2026-09-26_minmus-lab-1_orbit.png', (440, 150, 840, 560)),
    'minmus-science-1': ('2026-09-25_minmus-science-1_midlands.png', (420, 120, 840, 600)),
    'polar-relay-1': ('2026-09-25_polar-relay-1.png', (520, 220, 760, 490)),
    'keo-relay-1': ('2026-09-25_keo-relay-1.png', (520, 190, 760, 520)),
    'rescue-1': ('2026-09-25_rescue-1_approach.png', (430, 230, 590, 420)),
    'rescue-3': ('2026-09-26_rescue-3_grabbed.png', (520, 180, 760, 640)),
    'rescue-4': ('2026-09-26_rescue-4_mitbro.png', (360, 250, 860, 520)),
    # wide shots for cards 02 / 08
    'duna-1-landed': ('2026-09-25_duna-1_landed.png', (380, 180, 900, 560)),
    'rescue-3-grab-wide': ('2026-09-26_rescue-3_grabbed.png', (380, 380, 940, 660)),
}
for _s in CROPS:
    PHOTOS[_s] = f'img/{_s}.jpg'
# same design as a photographed sibling
for _s, _same in {'keo-relay-2': 'keo-relay-1', 'keo-relay-3': 'keo-relay-1', 'mun-sat-1': 'keo-relay-1',
                  'rescue-5': 'rescue-3', 'rescue-6': 'rescue-3'}.items():
    PHOTOS[_s] = PHOTOS[_same]


def photo(slug):
    return PHOTOS.get(slug)


def make_crops():
    from PIL import Image
    os.makedirs(IMG, exist_ok=True)
    for name, (src, box) in CROPS.items():
        im = Image.open(MEDIA + src).convert('RGB').crop(box)
        if im.width > 480:
            im = im.resize((480, round(im.height * 480 / im.width)), Image.LANCZOS)
        else:  # small crops: upscale so they stay sharp at @2x in small frames
            k = min(3, 480 / im.width)
            im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        im.save(IMG + name + '.jpg', quality=86, optimize=True, progressive=True)


def thumb(slug, cls='th'):
    p = photo(slug)
    if p:
        return f'<div class="{cls}"><img src="{p}"></div>'
    return f'<div class="{cls} ph0">{icon("rocket", 26, "#5c6684")}</div>'


def craft_name(slug):
    for l in LAUNCHES:
        if l['slug'] == slug:
            return l['craft'] if '(' not in l['craft'] else l['craft'].split(' (')[0]
    return slug


# ---------------------------------------------------------------- kerbal faces (after img5.py)
def kerbal(kind='jeb', size=64, uid='k'):
    mouth = {
        'jeb': '<path d="M52 95 Q80 124 108 95 Q80 104 52 95Z" fill="#fff" stroke="#2c3d0c" stroke-width="3" stroke-linejoin="round"/>',
        'bill': '<path d="M62 99 Q80 110 98 99" fill="none" stroke="#2c3d0c" stroke-width="3.5" stroke-linecap="round"/>',
        'bob': '<path d="M68 104 Q80 97 92 104" fill="none" stroke="#2c3d0c" stroke-width="3.5" stroke-linecap="round"/>',
        'val': '<path d="M60 97 Q80 113 100 97" fill="none" stroke="#2c3d0c" stroke-width="3.5" stroke-linecap="round"/>',
    }[kind]
    px = {'jeb': (2, 1), 'bill': (0, 2), 'bob': (-2, -1), 'val': (1, 1)}[kind]
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 160 160">
<defs><radialGradient id="h{uid}" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#c3ef5c"/><stop offset="1" stop-color="#7fb526"/></radialGradient>
<radialGradient id="g{uid}" cx="35%" cy="25%" r="80%"><stop offset="0" stop-color="#2a3d6e"/><stop offset="1" stop-color="#0f1730"/></radialGradient>
<clipPath id="c{uid}"><circle cx="80" cy="80" r="74"/></clipPath></defs>
<circle cx="80" cy="80" r="74" fill="url(#g{uid})"/>
<g clip-path="url(#c{uid})">
<path d="M24 170 C28 132 52 118 80 118 C108 118 132 132 136 170Z" fill="#f07d2a"/>
<path d="M60 120 h40 v10 h-40z" fill="#c9ced8"/>
<ellipse cx="80" cy="76" rx="48" ry="42" fill="url(#h{uid})"/>
<circle cx="62" cy="70" r="15" fill="#fff"/><circle cx="98" cy="70" r="15" fill="#fff"/>
<circle cx="{62 + px[0]}" cy="{71 + px[1]}" r="6.5" fill="#15190e"/><circle cx="{98 + px[0]}" cy="{71 + px[1]}" r="6.5" fill="#15190e"/>
{mouth}</g>
<circle cx="80" cy="80" r="74" fill="none" stroke="rgba(200,225,255,.55)" stroke-width="3"/></svg>'''


TRAIT_ICON = {'Pilot': 'gyro', 'Engineer': 'wrench', 'Scientist': 'flask', '': 'kerbal'}

# ---------------------------------------------------------------- page chrome
ICONS2 = '''
<svg width="0" height="0" style="position:absolute"><defs>
<symbol id="i-cross" viewBox="0 0 24 24"><path d="M6.5 6.5l11 11M17.5 6.5l-11 11" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"/></symbol>
<symbol id="i-live" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4.6" fill="currentColor"/><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2" opacity=".6"/></symbol>
<symbol id="i-bug" viewBox="0 0 24 24"><g fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M8 7.5l-2-2.5M16 7.5l2-2.5M4 12.5h3.5M16.5 12.5H20M5 18.5l2.8-1.8M19 18.5l-2.8-1.8"/></g><path fill="currentColor" d="M12 6.2c2.6 0 4.6 2.2 4.6 5v3.6c0 2.8-2 5-4.6 5s-4.6-2.2-4.6-5v-3.6c0-2.8 2-5 4.6-5z"/><path d="M12 9.5v9.5" stroke="#070b17" stroke-width="1.6"/></symbol>
<symbol id="i-sat" viewBox="0 0 24 24"><rect x="9" y="9" width="6" height="6" rx="1.2" fill="currentColor"/><path fill="currentColor" opacity=".75" d="M1.5 10h6v4h-6zM16.5 10h6v4h-6z"/><path d="M12 9V4.5M9.5 4.5h5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></symbol>
<symbol id="i-station" viewBox="0 0 24 24"><rect x="8.5" y="4" width="7" height="16" rx="2.5" fill="currentColor"/><path fill="currentColor" opacity=".7" d="M1 8h6.5v8H1zM16.5 8H23v8h-6.5z"/></symbol>
<symbol id="i-term" viewBox="0 0 24 24"><rect x="2.5" y="4" width="19" height="16" rx="2.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M6.5 9.5l3 2.5-3 2.5M11.5 15h6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9.3" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="M12 6.8V12l3.6 2.4" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></symbol>
</defs></svg>'''

HEAD2 = '''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&family=Noto+Sans+KR:wght@500;700&display=block" rel="stylesheet">
<style>{css}</style></head><body>'''

CSS2 = '''
:root{--fail:#8e98b6;--live:#56c8ff;--eve:#b487d6;--jool:#a8d97a}
body{font-family:'Space Grotesk','Noto Sans KR',system-ui,sans-serif;word-break:keep-all}
.mono{font-family:'JetBrains Mono','Noto Sans KR',ui-monospace,monospace}
.c-fail{background:var(--fail);color:#12172a}
.c-live{background:var(--live);color:#04222f}
.hdr{display:flex;justify-content:space-between;align-items:center}
.datechip{font-family:'JetBrains Mono',monospace;font-size:18px;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:7px 14px;letter-spacing:.04em;white-space:nowrap}
.headline{font-weight:700;letter-spacing:-.02em;line-height:1.12;margin-top:14px;white-space:nowrap}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:22px}
.sec{margin-top:24px}
.lbl{font-size:18px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:600}
.ph0{background:rgba(255,255,255,.035);border:1.5px dashed rgba(255,255,255,.16);display:flex;align-items:center;justify-content:center}
'''


def _width_em(s):
    w = 0.0
    for ch in s:
        if '가' <= ch <= '힣':
            w += 1.0
        elif ch == ' ':
            w += 0.28
        elif ch in '·,.:—–-':
            w += 0.4 if ch not in '—–' else 0.9
        elif ch.isupper():
            w += 0.66
        else:
            w += 0.58
    return w


def header(ic, kicker, headline, color='var(--text)', maxpx=66):
    """kicker row + date chip + one Korean headline (<= 18 characters incl. spaces, plan §5.4)."""
    assert len(headline) <= 18, (headline, len(headline))
    size = min(maxpx, int(960 / _width_em(headline)))
    chip = f'{CN["date"]} · day {CN["real_days"]}'
    return (f'<div class="hdr"><div class="kicker">{icon(ic, 26, "#8e98b6")}<span>{kicker}</span></div>'
            f'<div class="datechip">{chip}</div></div>'
            f'<div class="headline" style="font-size:{size}px;color:{color}">{headline}</div>')


def page(title, css, body, idx, seed=7):
    dots = ''.join(f'<i class="{"on" if i == idx else ""}"></i>' for i in range(1, TOTAL + 1))
    footer = f'<div class="footer"><span>KSP 1.12 · career · flown by Claude</span><span class="dots">{dots}</span></div>'
    return (HEAD2.format(title=title, css=BASE_CSS + CSS2 + css) + ICONS + ICONS2 + stars(seed)
            + f'<div class="page">{body}</div>' + footer + '</body></html>')


def write(name, html):
    os.makedirs(OUT, exist_ok=True)
    # guard: no digits may come from the script except layout; this only checks for accidental "None"/"nan"
    assert 'None' not in re.sub(r'<[^>]+>', '', html), name
    with open(OUT + name, 'w') as f:
        f.write(html)
