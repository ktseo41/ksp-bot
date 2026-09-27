import json
from common import *
from common import _ROOT

SAVE = os.path.join(_ROOT, 'docs', 'record', 'career-save.json')
d = json.load(open(SAVE))
logs = {k['name'].split()[0]: k['career_log'] for k in d['kerbals'] if k['type'] == 'Crew'}
cnt = lambda who, ev: logs[who].count(ev)
assert cnt('Jebediah', 'Die') == 2 and cnt('Bill', 'Die') == 1 and cnt('Bob', 'Die') == 0
assert cnt('Jebediah', 'Land,Minmus') == 2 and cnt('Bill', 'Land,Minmus') == 1 and cnt('Bob', 'Land,Mun') == 1


def kerbal(kind, size=170):
    mouth = {
        'jeb': '<path d="M52 95 Q80 124 108 95 Q80 104 52 95Z" fill="#fff" stroke="#2c3d0c" stroke-width="3" stroke-linejoin="round"/>',
        'bill': '<path d="M62 99 Q80 110 98 99" fill="none" stroke="#2c3d0c" stroke-width="3.5" stroke-linecap="round"/>',
        'bob': '<path d="M68 104 Q80 97 92 104" fill="none" stroke="#2c3d0c" stroke-width="3.5" stroke-linecap="round"/>'
               '<path d="M48 52 L70 58 M112 52 L90 58" stroke="#2c3d0c" stroke-width="4" stroke-linecap="round"/>',
        'val': '<path d="M60 97 Q80 113 100 97" fill="none" stroke="#2c3d0c" stroke-width="3.5" stroke-linecap="round"/>',
    }[kind]
    brows = {'jeb': '<path d="M48 50 Q60 42 72 50 M88 50 Q100 42 112 50" fill="none" stroke="#2c3d0c" stroke-width="4" stroke-linecap="round"/>',
             'bill': '<path d="M50 52 H70 M90 52 H110" stroke="#2c3d0c" stroke-width="4" stroke-linecap="round"/>',
             'bob': '', 'val': ''}[kind]
    hair_back = '<path d="M30 80 C26 40 50 22 80 22 C110 22 134 40 130 80 C126 110 118 120 112 124 L48 124 C42 120 34 110 30 80Z" fill="#e8b93c"/>' if kind == 'val' else ''
    hair_front = ('<ellipse cx="80" cy="22" rx="16" ry="12" fill="#f0c64a"/>'
                  '<path d="M36 64 C40 36 64 30 84 34 C70 40 56 50 50 66Z" fill="#f0c64a"/>'
                  '<path d="M124 64 C120 40 104 32 88 34 C100 42 110 52 112 66Z" fill="#f0c64a"/>') if kind == 'val' else ''
    lash = ('<path d="M50 60 l-6 -6 M110 60 l6 -6" stroke="#2c3d0c" stroke-width="3" stroke-linecap="round"/>') if kind == 'val' else ''
    px = {'jeb': (2, 1), 'bill': (0, 2), 'bob': (-2, -1), 'val': (1, 1)}[kind]
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 160 160">
<defs><radialGradient id="h{kind}" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#c3ef5c"/><stop offset="1" stop-color="#7fb526"/></radialGradient>
<radialGradient id="g{kind}" cx="35%" cy="25%" r="80%"><stop offset="0" stop-color="#2a3d6e"/><stop offset="1" stop-color="#0f1730"/></radialGradient>
<clipPath id="c{kind}"><circle cx="80" cy="80" r="74"/></clipPath></defs>
<circle cx="80" cy="80" r="74" fill="url(#g{kind})"/>
<g clip-path="url(#c{kind})">
{hair_back}
<path d="M24 170 C28 132 52 118 80 118 C108 118 132 132 136 170Z" fill="#f07d2a"/>
<path d="M60 120 h40 v10 h-40z" fill="#c9ced8"/>
<ellipse cx="80" cy="76" rx="48" ry="42" fill="url(#h{kind})"/>
{hair_front}
<circle cx="62" cy="70" r="15" fill="#fff"/><circle cx="98" cy="70" r="15" fill="#fff"/>
<circle cx="{62+px[0]}" cy="{71+px[1]}" r="6.5" fill="#15190e"/><circle cx="{98+px[0]}" cy="{71+px[1]}" r="6.5" fill="#15190e"/>
{brows}{lash}{mouth}
</g>
<circle cx="80" cy="80" r="74" fill="none" stroke="rgba(200,225,255,.55)" stroke-width="3"/>
<path d="M36 44 A52 52 0 0 1 70 22" fill="none" stroke="rgba(255,255,255,.35)" stroke-width="5" stroke-linecap="round"/>
</svg>'''


TRAIT = {'Pilot': 'gyro', 'Engineer': 'wrench', 'Scientist': 'flask'}


def skulls(nums, faded=False):
    out = []
    for n in nums:
        out.append(f'<div class="sk{" fd" if faded else ""}">{icon("skull", 38, "#ff4d5e")}<span>#{n}</span></div>')
    return ''.join(out)


def visit(kind, ic, times=None):
    t = f'<b>×{times}</b>' if times else ''
    return f'<div class="vs">{planet(kind, 52)}<span class="vi">{icon(ic, 20)}</span>{t}</div>'


CREW = [
    ('jeb', 'Jebediah', 'Pilot',
     [visit('kerbin', 'orbit'), visit('minmus', 'flag', 2), visit('mun', 'orbit')],
     [6, 11], [13, 13], 2, None),
    ('bill', 'Bill', 'Engineer',
     [visit('kerbin', 'orbit'), visit('minmus', 'flag', 1)],
     [12], [8], 1, 10),
    ('bob', 'Bob', 'Scientist',
     [visit('kerbin', 'orbit'), visit('mun', 'flag', 1)],
     [], [13], 0, 16),
    ('val', 'Valentina', 'Pilot',
     [],
     [], [13], 0, None),
]

css = '''
.hdr{display:flex;justify-content:space-between;align-items:flex-end}
.title{font-size:76px}
.sum{display:flex;gap:26px;align-items:center;padding-bottom:6px}
.sum div{display:flex;align-items:center;gap:8px;font-size:46px;font-weight:700}
.crew{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:28px}
.kc{background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:20px;display:flex;flex-direction:column;gap:14px;position:relative;min-height:372px}
.kc .top{display:flex;gap:18px;align-items:center}
.kc .nm{font-size:38px;font-weight:700;letter-spacing:-.02em}
.kc .tr{display:inline-flex;align-items:center;gap:8px;font-size:19px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;margin-top:6px}
.kc .first{display:inline-flex;align-items:center;gap:6px;background:var(--gold);color:#2b2000;font-weight:700;font-size:17px;border-radius:999px;padding:4px 12px 4px 8px;margin-top:10px;letter-spacing:.06em}
.kc .rs{position:absolute;top:18px;right:18px;display:flex;align-items:center;gap:4px;color:#9ccc3c;font-size:24px;font-weight:700}
.row{display:flex;align-items:center;gap:14px;min-height:62px;border-top:1px solid var(--line);padding-top:12px}
.row .ri{width:26px;display:flex;justify-content:center;color:var(--dim)}
.vs{display:flex;align-items:center;gap:4px;position:relative;margin-right:10px}
.vs .vi{position:absolute;left:34px;top:-6px;width:28px;height:28px;border-radius:50%;background:#0d1428;border:1.5px solid var(--line);display:flex;align-items:center;justify-content:center;color:#ffcf4a}
.vs b{font-size:22px;margin-left:10px}
.sk{display:flex;flex-direction:column;align-items:center;gap:0;font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700;color:#ff8e98}
.sk.fd{opacity:.35}
.none{color:var(--dim);font-size:24px}
.photos{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:18px}
.ph{height:290px;border-radius:20px;overflow:hidden;position:relative;border:1px solid var(--line)}
.ph img{width:100%;height:100%;object-fit:cover;display:block}
.ph .tg{position:absolute;left:12px;bottom:12px;display:flex;align-items:center;gap:8px;background:rgba(7,11,23,.8);border-radius:999px;padding:6px 14px 6px 10px;font-size:20px;font-weight:700}
'''

cards = []
for kind, name, trait, visits, dead, rev, respawn, first in CREW:
    rs = f'<div class="rs">{icon("respawn", 30, "#9ccc3c")}×{respawn}</div>' if respawn else ''
    fb = f'<div class="first">{icon("star", 18, "#2b2000")}FIRST · #{first}</div>' if first else ''
    vis = ''.join(visits) if visits else f'<span class="none">{planet("kerbin", 52)}</span>'
    death = skulls(dead) + skulls(rev, True)
    cards.append(f'''<div class="kc">{rs}
<div class="top">{kerbal(kind, 150)}<div><div class="nm">{name}</div><div class="tr">{icon(TRAIT[trait], 22, '#8e98b6')}{trait}</div>{fb}</div></div>
<div class="row"><span class="ri">{icon('rocket', 22)}</span>{vis}</div>
<div class="row"><span class="ri">{icon('skull', 22)}</span>{death}</div>
</div>''')

body = f'''
<div class="hdr">
  <div>
    <div class="kicker">{icon('kerbal', 26, '#9ccc3c')}<span>Crew</span></div>
    <div class="title">4 kerbals</div>
  </div>
  <div class="sum">
    <div style="color:var(--dead)">{icon('skull', 44, '#ff4d5e')}3</div>
    <div><span style="color:var(--dead);opacity:.4;display:flex;align-items:center;gap:8px">{icon('skull', 44, '#ff4d5e')}5</span>{icon('revert', 30, '#ff9a2e')}</div>
    <div style="color:#9ccc3c">{icon('respawn', 42, '#9ccc3c')}3</div>
  </div>
</div>
<div class="crew">{''.join(cards)}</div>
<div class="photos">
  <div class="ph"><img src="crafts/photo-pad-explosion.jpg"><div class="tg">{icon('boom', 24, '#ff9a2e')}t=0</div></div>
  <div class="ph"><img src="crafts/photo-mun-landed.jpg"><div class="tg">{icon('star', 22, '#ffcf4a')}#16 · Bob · Mun</div></div>
</div>
'''

write('05-crew.html', page('Kerbal crew', css, body, 5, seed=43))
