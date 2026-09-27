"""Three English images for a short Reddit post (1600x2000 CSS, rendered 2160x2700):
1 the milestone crafts on the pad, 2 in-flight screenshots, 3 the numbers + how it works.

    python3 tools/summary/reddit/build.py

Numbers and names come from docs/record/career.json; this script holds layout, the photo/crop table and the English
captions. Pad photos are re-cropped large from runs/craft-<slug>.png (tools/summary/crop.py fractions).
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'v2'))
sys.path.insert(0, os.path.join(HERE, '..'))
from common2 import *  # noqa: E402,F403
from common2 import ICONS2, HEAD2, CSS2  # noqa: E402
import crop as padcrop  # noqa: E402
from PIL import Image  # noqa: E402

OUTR = os.path.join(ROOT, 'docs', 'media', 'summary', 'reddit') + '/'
IMGR = OUTR + 'img/'
W, H = 1600, 2000
SCALE = 1.35

CSS = f'''
html,body{{width:{W}px;height:{H}px}}
.page{{padding:64px 56px 0}}
.kick{{display:flex;align-items:center;gap:12px;font-size:24px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:500}}
.kick b{{color:var(--text)}}
.ttl{{font-size:78px;font-weight:700;letter-spacing:-.03em;line-height:1.05;margin-top:14px}}
.foot{{position:absolute;left:56px;right:56px;bottom:34px;display:flex;justify-content:space-between;font-size:22px;color:var(--dim);letter-spacing:.05em;z-index:2}}
'''


def page_r(title, css, body, n, seed):
    foot = f'<div class="foot"><span>KSP 1.12.5 · Normal career · flown by Claude</span><span>{n} / 3</span></div>'
    return (HEAD2.format(title=title, css=BASE_CSS + CSS2 + CSS + css) + ICONS + ICONS2 + stars(seed, n=260, w=W, h=H)
            + f'<div class="page">{body}</div>' + foot + '</body></html>')


def header_r(kicker, title):
    return f'<div class="kick">{icon("rocket", 28, "#8e98b6")}<span>{kicker}</span></div><div class="ttl">{title}</div>'


def save_jpg(im, name, width):
    im = im.convert('RGB')
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    im.save(IMGR + name + '.jpg', quality=88, optimize=True, progressive=True)
    return f'img/{name}.jpg'


# ------------------------------------------------------------------ 1: crafts on the pad
# slug, first launch number, English caption (the facts are in career.json / LOG.md)
CRAFTS = [('hopper-1', 1, 'first hop · 16 km'), ('orbiter-1', 4, 'first orbit'),
          ('minmus-lander-1', 10, 'first Minmus landing'), ('mun-lander-3', 16, 'first Mun landing'),
          ('duna-1', 30, 'Duna and back'), ('jool-1', 44, 'nuclear probe to Jool'),
          ('eve-2', 49, 'Eve splashdown + Gilly landing'), ('eeloo-1', 52, 'on its way to Eeloo')]
CELL_W, PHOTO_H = 357, 640
DV = {r['slug']: r for r in RECORD['pad_dv']}
DV_MORE = {'eve-2': ' + lander'}  # KSP lists no delta-v for Eve 2's lander stage on the pad (pad_dv_note)


def pad_photo(slug):
    cx, t, b, cw = padcrop.C[slug]
    im = Image.open(os.path.join(ROOT, 'runs', f'craft-{slug}.png')).convert('RGB')
    A = CELL_W / PHOTO_H
    h = (b - t) * padcrop.H * 1.10
    w = max(h * A, cw * padcrop.W * 2.2)
    h = w / A
    y0 = max(0, min((t + b) / 2 * padcrop.H - h / 2, padcrop.H - h))
    x0 = cx * padcrop.W - w / 2
    return save_jpg(im.crop(tuple(round(v) for v in (x0, y0, x0 + w, y0 + h))), 'pad-' + slug, round(CELL_W * SCALE))


def card1():
    cells = []
    for slug, n, cap in CRAFTS:
        l = BY_N[n]
        crew = l.get('crew', '')
        who = f' · {esc(crew)}' if crew and not crew.startswith('-') else ''
        cells.append(f'<div class="cr"><div class="ph"><img src="{pad_photo(slug)}"><span class="n">#{n}</span></div>'
                     f'<div class="nm">{esc(craft_name(slug))}</div>'
                     f'<div class="dv">Δv {num(DV[slug]["vac"])} m/s{DV_MORE.get(slug, "")}</div>'
                     f'<div class="cp">{esc(cap)}{who}</div></div>')
    css = f'''
.note{{font-size:24px;color:var(--muted);margin-top:14px}}
.grid{{display:grid;grid-template-columns:repeat(4,{CELL_W}px);gap:30px 20px;margin-top:30px}}
.cr .ph{{height:{PHOTO_H}px;border-radius:22px;overflow:hidden;position:relative;border:1px solid var(--line)}}
.cr .ph img{{width:100%;height:100%;object-fit:cover;display:block}}
.cr .n{{position:absolute;top:14px;left:14px;font-family:'JetBrains Mono',monospace;font-weight:700;font-size:26px;background:rgba(7,11,23,.78);border-radius:10px;padding:4px 12px}}
.cr .nm{{font-size:32px;font-weight:700;margin-top:14px;letter-spacing:-.01em}}
.cr .dv{{font-family:'JetBrains Mono',monospace;font-size:24px;font-weight:700;color:var(--sci);margin-top:6px}}
.cr .cp{{font-size:23px;color:var(--muted);margin-top:4px;line-height:1.25}}
'''
    body = header_r('An AI plays <b>Kerbal Space Program</b>', f'{len(LAUNCHES)} launches, from a hopper<br>to an Eeloo probe') \
        + '<div class="note">Δv: KSP\'s own stage sum, in vacuum</div>' + f'<div class="grid">{"".join(cells)}</div>'
    return page_r('Crafts', css, body, 1, 11)


# ------------------------------------------------------------------ 2: in flight
# name, source in docs/media (or runs/), crop box on the source, caption. HUD shots are cropped clear of the HUD.
SHOTS = [
    ('duna', 'docs/media/2026-09-25_duna-1_landed.png', (0, 0, 1280, 720), 'Duna · Valentina landed and flew home'),
    ('minmus', 'docs/media/2026-09-25_minmus-science-1_midlands.png', (160, 90, 1120, 630), 'Minmus · six landing missions'),
    ('keo', 'docs/media/2026-09-25_keo-relay-1.png', (0, 0, 1280, 720), 'CommNet relay in keosynchronous orbit'),
    ('lab', 'docs/media/2026-09-26_minmus-lab-1_orbit.png', (0, 0, 1280, 720), 'Science lab station around Minmus'),
    ('rescue', 'docs/media/2026-09-26_rescue-3_grabbed.png', (0, 5, 1280, 725), 'Klaw rescue of a stranded kerbal'),
    ('moho', 'runs/moho-1-clean.png', (280, 80, 2280, 1205), 'Moho · uncrewed lander'),
    ('eve', 'docs/media/2026-09-27_eve-2-splashdown.png', (320, 110, 960, 470), 'Eve · splashdown on an inflatable heat shield'),
    ('gilly', 'docs/media/2026-09-27_eve-2-gilly-landed.png', (340, 122, 940, 460), 'Gilly · the Eve carrier landed too'),
]
SHOT_W, SHOT_H = 734, 400


def card2():
    cells = []
    for name, src, box, cap in SHOTS:
        im = Image.open(os.path.join(ROOT, src)).convert('RGB').crop(box)
        p = save_jpg(im, 'shot-' + name, round(SHOT_W * SCALE))
        cells.append(f'<div class="sh"><img src="{p}"><span class="cp">{esc(cap)}</span></div>')
    css = f'''
.grid{{display:grid;grid-template-columns:repeat(2,{SHOT_W}px);gap:18px 20px;margin-top:36px}}
.sh{{height:{SHOT_H}px;border-radius:20px;overflow:hidden;position:relative;border:1px solid var(--line)}}
.sh img{{width:100%;height:100%;object-fit:cover;display:block}}
.sh .cp{{position:absolute;left:14px;bottom:14px;right:14px;font-size:24px;font-weight:600;background:rgba(7,11,23,.78);border-radius:12px;padding:8px 14px;width:max-content;max-width:calc(100% - 28px)}}
'''
    body = header_r('In-game screenshots', 'Where it went') + f'<div class="grid">{"".join(cells)}</div>'
    return page_r('Where it went', css, body, 2, 23)


# ------------------------------------------------------------------ 3: numbers + how it works
def card3():
    counts = {}
    for l in LAUNCHES:
        counts[code(l)] = counts.get(code(l), 0) + 1
    LB = {k: v for k, v in RECORD['landings_by_body'].items() if not k.startswith('_')}
    crewed = [b for b in LB if any(crew_ok(BY_N[n]) for n in LB[b])]
    uncrewed = [b for b in LB if b not in crewed]
    en_route = [m['to'] for m in RECORD['live_missions'] if m.get('to') and m['to'] not in LB]
    days = ut_to_days(CN['ut'])
    kb = RECORD['kerbals']
    relays = [m for m in RECORD['live_missions'] if m['type'] == 'satellite']
    label = {'ok': 'successes', 'rev': 'reverted', 'dead': 'crews lost', 'fail': 'failed', 'live': 'still flying'}
    bar = ''.join(f'<div class="{RES[k][1]}" style="flex:{counts[k]}">{icon(RES[k][0], 34)}{counts[k]}</div>' for k in RES if counts.get(k))
    leg = ''.join(f'<span><i class="dot {RES[k][1]}"></i>{counts[k]} {label[k]}</span>' for k in RES if counts.get(k))

    def row(title, bodies, badge):
        ps = ''.join(f'<div class="b">{planet(b, 112, dashed=badge == "en")}<span>{BODY_NAME[b]}</span></div>' for b in bodies)
        return f'<div class="row"><div class="rt">{title}</div><div class="bs">{ps}</div></div>'

    steps = [('term', 'Claude Code', 'designs crafts as part lists, writes and runs the flight code'),
             ('rocket', 'Python flight phases', 'ascent · transfer · capture · land · reentry, its own guidance'),
             ('bolt', 'kRPC + a small helper mod', 'builds crafts from JSON, research, contracts, flight log'),
             ('planet', 'KSP 1.12.5', 'stock parts, Normal career, no MechJeb or other autopilot mods')]
    how = ''.join(f'<div class="st"><div class="si">{icon(ic, 34, "#b28cff")}</div><div><b>{t}</b><span>{d}</span></div></div>'
                  for ic, t, d in steps)
    css = '''
.big{display:flex;align-items:baseline;gap:22px;margin-top:40px}
.big b{font-size:190px;font-weight:700;letter-spacing:-.04em;line-height:.9}
.big span{font-size:34px;color:var(--muted)}
.bar{display:flex;height:96px;border-radius:20px;overflow:hidden;gap:4px;margin-top:28px}
.bar div{display:flex;align-items:center;justify-content:center;gap:8px;font-size:42px;font-weight:700;min-width:84px}
.bar .c-ok{background:linear-gradient(180deg,#46e38b,#23b863)}.bar .c-rev{background:linear-gradient(180deg,#ffab4d,#f08416)}
.bar .c-dead{background:linear-gradient(180deg,#ff6a78,#e33445);color:#fff}.bar .c-fail{background:linear-gradient(180deg,#a6afca,#7c86a3)}
.bar .c-live{background:linear-gradient(180deg,#7ad6ff,#2fa9e6)}
.lg{display:flex;flex-wrap:wrap;gap:10px 26px;margin-top:16px;font-size:24px;color:var(--muted)}
.lg span{display:flex;align-items:center;gap:9px}.lg .dot{width:16px;height:16px;border-radius:5px;display:inline-block}
.facts{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:40px}
.fc{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:22px 26px}
.fc b{display:block;font-size:64px;font-weight:700;letter-spacing:-.02em}
.fc span{font-size:25px;color:var(--muted)}
.row{display:flex;align-items:center;gap:20px;margin-top:20px}
.rt{width:300px;font-size:30px;font-weight:600;color:#c9d1e8;line-height:1.2}
.bs{display:flex;gap:40px}
.b{display:flex;flex-direction:column;align-items:center;gap:8px;font-size:26px;font-weight:600;width:140px}
.sec2{margin-top:50px;font-size:22px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
.how{display:grid;grid-template-columns:1fr;gap:14px;margin-top:16px}
.st{display:flex;gap:16px;align-items:center;background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:18px 22px}
.si{width:60px;height:60px;border-radius:16px;background:rgba(178,140,255,.14);display:flex;align-items:center;justify-content:center;flex:none}
.st b{display:block;font-size:30px}.st span{font-size:24px;color:var(--muted);line-height:1.25;display:block;margin-top:3px}
'''
    body = (header_r('The numbers', f'{CN["real_days"]} real days, ~{days / YEAR_D:.1f} Kerbin years')
            + f'<div class="big"><b>{len(LAUNCHES)}</b><span>launches</span></div><div class="bar">{bar}</div><div class="lg">{leg}</div>'
            + '<div class="facts">'
            + f'<div class="fc"><b>{len(relays)}</b><span>CommNet relay satellites</span></div>'
            + f'<div class="fc"><b>{len(kb["rescued"])}</b><span>stranded kerbals rescued</span></div>'
            + f'<div class="fc"><b>{len(RECORD["research"])}</b><span>technologies researched</span></div></div>'
            + row('Crewed landings,<br>crew home', crewed, 'ok') + row('Uncrewed landers', uncrewed, 'ok')
            + row('Probes on the way', en_route, 'en')
            + f'<div class="sec2">How it plays</div><div class="how">{how}</div>')
    return page_r('The numbers', css, body, 3, 37)


def crew_ok(l):
    c = l.get('crew', '')
    return bool(c) and not c.startswith('-') and l['result'] == 'success'


def main():
    os.makedirs(IMGR, exist_ok=True)
    for name, fn in (('1-crafts', card1), ('2-where', card2), ('3-numbers', card3)):
        html = fn()
        path = OUTR + name + '.html'
        with open(path, 'w') as f:
            f.write(html)
        png = OUTR + name + '.png'
        subprocess.run(['google-chrome', '--headless=new', '--disable-gpu', '--hide-scrollbars',
                        f'--force-device-scale-factor={SCALE}', f'--window-size={W},{H}', '--virtual-time-budget=8000',
                        f'--screenshot={png}', 'file://' + path], check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        print(png, Image.open(png).size)


if __name__ == '__main__':
    main()
