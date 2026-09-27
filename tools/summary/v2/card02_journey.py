import math
from common2 import *
from common2 import _width_em

LIVE = RECORD['live_missions']
LB = {k: v for k, v in RECORD['landings_by_body'].items() if not k.startswith('_')}
MOONS, PLANETS = {'mun', 'minmus', 'ike', 'gilly'}, {'duna', 'eve', 'jool', 'moho', 'dres', 'eeloo'}
n_moons = sum(1 for b in LB if b in MOONS)
n_planets = sum(1 for b in LB if b in PLANETS)
headline = T('h02', moons=n_moons, planets=n_planets)


def mission(slug):
    return next(m for m in LIVE if m['slug'] == slug)


def by_body(body, types):
    return [m for m in LIVE if m['body'] == body and m['type'] in types]


def eta(ut):
    d = days_from_now(ut)
    if d < 0:  # the event already happened (e.g. a contract completed): how long ago
        return T('ago', t=f'~{fmt_ydays(-d) if -d >= YEAR_D else num(-d) + "d"}')
    return f'~d+{num(d)}' if d < YEAR_D else f'~{fmt_ydays(d)}'  # from the current UT: approximate


# rows under the map: up to 5 at 78 px; with more, the map loses 60 px of empty sky and the rows shrink to fit
N_ROWS = sum(1 for m in LIVE if m['type'] in ('probe', 'crewed', 'station'))
MAP_H = 600 if N_ROWS <= 5 else 540
ROW_H = 78 if N_ROWS <= 5 else min(78, int((5 * 78 + 4 * 8 + 600 - MAP_H + 30 - (N_ROWS - 1) * 6) / N_ROWS))
ROW_GAP = 8 if N_ROWS <= 5 else 6

css = '''
.map{position:relative;width:968px;height:''' + str(MAP_H) + '''px;margin-top:4px}
.map svg.bg{position:absolute;left:0;top:0}
.pb{position:absolute;transform:translate(-50%,-50%);display:flex}
.lab{position:absolute;display:flex;flex-direction:column;gap:3px;white-space:nowrap}
.lab .nm{font-size:27px;font-weight:700;letter-spacing:-.01em;display:flex;align-items:center;gap:8px}
.lab .s{font-size:19px;color:#c9d1e8;display:flex;align-items:center;gap:6px}
.lab .s b{font-family:'JetBrains Mono',monospace;color:var(--text)}
.lab .s .m{color:var(--muted)}
.rows{margin-top:6px;display:flex;flex-direction:column;gap:''' + str(ROW_GAP) + '''px}
.rows .t{display:flex;align-items:center;gap:12px;margin-bottom:2px}
.rw{display:grid;grid-template-columns:96px 250px 1fr 180px;gap:16px;align-items:center;background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:7px 18px 7px 7px;height:''' + str(ROW_H) + '''px}
.rw .th{width:96px;height:''' + str(ROW_H - 16) + '''px;border-radius:10px;overflow:hidden}
.rw .th img{width:100%;height:100%;object-fit:cover;display:block}
.rw .nm{font-size:23px;font-weight:700;display:flex;flex-direction:column;gap:2px;white-space:nowrap}
.rw .nm span{font-size:17px;color:var(--muted);font-weight:500;display:flex;align-items:center;gap:6px}
.rw .wh{font-size:20px;color:#c9d1e8;display:flex;align-items:center;gap:8px;white-space:nowrap}
.rw .nx{text-align:right;display:flex;flex-direction:column;gap:2px;white-space:nowrap}
.rw .nx b{font-family:'JetBrains Mono',monospace;font-size:24px;color:var(--live)}
.rw .nx span{font-size:17px;color:var(--muted)}
'''

# ---- schematic solar system: Kerbol off the left edge, orbits as arcs (scale ignored)
SX, SY = -150, 300 - (600 - MAP_H) * 3 // 4
ORB = {'moho': (205, 36), 'eve': (260, -38), 'kerbin': (420, 14), 'duna': (600, -14), 'dres': (760, -4),
       'jool': (930, 10), 'eeloo': (1000, -12)}  # radius, angle (deg)
SIZE = {'moho': 50, 'eve': 76, 'kerbin': 84, 'duna': 72, 'dres': 44, 'jool': 124, 'eeloo': 42}


def pos(b):
    r, a = ORB[b]
    return SX + r * math.cos(math.radians(a)), SY + r * math.sin(math.radians(a))


svg = [f'<svg class="bg" width="968" height="{MAP_H}" viewBox="0 0 968 {MAP_H}">']
for b, (r, a) in ORB.items():
    far = b in ('jool', 'dres', 'eeloo')  # not reached yet: dashed, green
    svg.append(orbit_ring(SX, SY, r, dashed=far, color='rgba(168,217,122,.35)' if far else 'rgba(255,255,255,.13)'))
kx, ky = pos('kerbin')
dx, dy = pos('duna')
# moons: rings and positions around their planet (layout)
MOON = {'mun': ('kerbin', 58, 200, 34), 'minmus': ('kerbin', 86, 232, 28), 'ike': ('duna', 56, -150, 24),
        'gilly': ('eve', 54, 130, 20)}
mpos = {}
for mn, (par, r, ang, sz) in MOON.items():
    px, py = pos(par)
    svg.append(orbit_ring(px, py, r, color='rgba(255,255,255,.12)', width=1.2))
    mpos[mn] = (px + r * math.cos(math.radians(ang)), py + r * math.sin(math.radians(ang)))


def where(b):
    return mpos[b] if b in mpos else pos(b)


# craft in transit (live_missions with from/to): a Bézier bowed to the right of the travel direction
PATH_COL = ['#a8d97a', '#56c8ff']
travel = []
for m in LIVE:
    if 'from' not in m:
        continue
    (x0, y0), (x1, y1) = where(m['from']), where(m['to'])
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx_, ny_ = -uy, ux
    bow = min(L * .32, 96)
    r0, r1 = SIZE.get(m['from'], 40) / 2 + 8, SIZE.get(m['to'], 40) / 2 + 12
    P = [(x0 + ux * r0, y0 + uy * r0), (x0 + ux * L / 3 + nx_ * bow, y0 + uy * L / 3 + ny_ * bow),
         (x0 + ux * 2 * L / 3 + nx_ * bow, y0 + uy * 2 * L / 3 + ny_ * bow), (x1 - ux * r1, y1 - uy * r1)]
    col = '#ffb08e' if m['type'] == 'crewed' else PATH_COL[sum(1 for t in travel if t[0]['type'] != 'crewed') % 2]
    mk = f'mk{len(travel)}'
    svg.append(f'<defs><marker id="{mk}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
               f'<path d="M0 0L10 5L0 10z" fill="{col}"/></marker></defs>')
    svg.append(f'<path d="M{P[0][0]:.0f},{P[0][1]:.0f} C{P[1][0]:.0f},{P[1][1]:.0f} {P[2][0]:.0f},{P[2][1]:.0f} {P[3][0]:.0f},{P[3][1]:.0f}" '
               f'fill="none" stroke="{col}" stroke-width="2.4" stroke-dasharray="7 7" marker-end="url(#{mk})"/>')
    mid = tuple(.125 * P[0][k] + .375 * P[1][k] + .375 * P[2][k] + .125 * P[3][k] for k in (0, 1))
    travel.append((m, mid, col, (nx_, ny_)))
svg.append('</svg>')


def pb(x, y, html):
    return f'<div class="pb" style="left:{x:.0f}px;top:{y:.0f}px">{html}</div>'


def lab(x, y, name, lines, color='var(--text)', align='left'):
    ls = ''.join(f'<div class="s">{s}</div>' for s in lines)
    tr = 'transform:translateX(-100%);align-items:flex-end;' if align == 'right' else ''
    return f'<div class="lab" style="left:{x:.0f}px;top:{y:.0f}px;{tr}"><div class="nm" style="color:{color}">{name}</div>{ls}</div>'


def body_lines(b):
    out = []
    if b in LB:
        out.append(f'{icon("flag", 18, "#ffcf4a")}<span class="m">{T("landed")}</span> <b>{len(LB[b])}</b>')
    for t, ic in (('satellite', 'sat'), ('station', 'station')):
        n = len(by_body(b, (t,)))
        if n:
            out.append(f'{icon(ic, 18, "#a8e8cf")}<span class="m">{T(t, n=n)}</span> <b>{n}</b>')
    for m in by_body(b, ('crewed',)):
        out.append(f'{icon("kerbal", 18, "#9ccc3c")}{", ".join(m["crew"])} · <span class="m">{loc(m, "next")}</span> <b>{eta(m["next_ut"])}</b>')
        if m.get('sci_aboard'):
            out.append(f'{icon("flask", 18, "#56c8ff")}<b>~{num(m["sci_aboard"])}</b><span class="m">{T("sci aboard")}</span>')
    return out


# label anchor per body (layout): dx, dy from the body centre, alignment, name colour
LAB = {'moho': (-24, 30, 'left', '#e8b89c'), 'eve': (46, -44, 'left', '#d9b8f2'), 'kerbin': (-44, 48, 'left', '#8fd0ff'), 'mun': (-24, -8, 'right', '#d3d6dc'),
       'minmus': (-24, -90, 'right', '#a8e8cf'), 'duna': (44, -50, 'left', '#ffb08e'), 'dres': (28, -14, 'left', '#d6cfc4'), 'jool': (-2, 76, 'left', '#c8f0a0'),
       'gilly': (16, -14, 'left', '#d8b8a4'), 'eeloo': (-28, -16, 'right', '#e6eaee')}
nodes = [pb(SX + 90, SY, planet('kerbol', 260))]
nodes += [pb(*pos(b), planet(b, SIZE[b], dashed=any(t[0]['to'] == b and t[0]['type'] == 'probe' for t in travel) and b not in LB))
          for b in ORB]
nodes += [pb(*mpos[mn], planet(mn, MOON[mn][3])) for mn in MOON]
labels = []
for b, (ox, oy, al, col) in LAB.items():
    x, y = where(b)
    labels.append(lab(x + ox, y + oy, BODY_NAME[b], body_lines(b), col, al))
# planets and moons are obstacles for the in-transit labels
placed = [(x - SIZE.get(b, 24) / 2, y - SIZE.get(b, 24) / 2, SIZE.get(b, 24), SIZE.get(b, 24))
          for b in list(ORB) + list(MOON) for x, y in [where(b)]]
for m, (mx_, my_), col, (nx_, ny_) in travel:
    nodes.append(pb(mx_, my_, icon('kerbal' if m['type'] == 'crewed' else 'sat', 30, '#9ccc3c' if m['type'] == 'crewed' else col)))
    if m['type'] == 'probe':
        # on the outer side of the bow: to the right of a path bowing right, under one bowing down
        # on the outer side of the bow (right of a path bowing right, under one bowing down); if that box hits a label
        # already placed, try the other sides of the marker
        name, line = esc(craft_name(m['slug'])), f'{loc(m, "next")} {eta(m["next_ut"])}'
        w, h = max(_width_em(name) * 27, _width_em(line) * 19 + 24), 62
        right, under = (mx_ + 30, my_ - 16, 'left'), (mx_ - 40, my_ + 22, 'left')
        left, above = (mx_ - 26, my_ - 16, 'right'), (mx_ - 40, my_ - 16 - h - 8, 'left')
        cands = [right, under, left, above] if abs(nx_) >= abs(ny_) else [under, right, left, above]
        cands += [(mx_ + 30 + dx, my_ - 16, 'left') for dx in (40, 80)]  # last resort (longer English lines): further right
        def overlap(box):
            return sum(max(0, min(box[0] + box[2], b[0] + b[2]) - max(box[0], b[0]))
                       * max(0, min(box[1] + box[3], b[1] + b[3]) - max(box[1], b[1])) for b in placed)
        boxes_ = [((lx - w if al == 'right' else lx, ly, w, h), (lx, ly, al)) for lx, ly, al in cands]
        box, (lx, ly, al) = next((c for c in boxes_ if not overlap(c[0])), min(boxes_, key=lambda c: overlap(c[0])))
        placed.append(box)
        labels.append(lab(lx, ly, name,
                          [f'{icon("arrow", 18, col)}<span class="m">{loc(m, "next")}</span> <b>{eta(m["next_ut"])}</b>'], col, al))
mapdiv = f'<div class="map">{"".join(svg)}{"".join(nodes)}{"".join(labels)}</div>'

# ---- live missions rows
ROW_PHOTO = {'duna-1': 'img/duna-1-landed.jpg', 'eve-2': 'img/eve-2-gilly.jpg'}
rows = []
for m in LIVE:
    if m['type'] not in ('probe', 'crewed', 'station'):
        continue
    crew = ', '.join(m['crew']) if m['crew'] else T('uncrewed')
    ic = {'probe': 'sat', 'crewed': 'kerbal', 'station': 'station'}[m['type']]
    p = ROW_PHOTO.get(m['slug']) or photo(m['slug'])
    th = f'<div class="th"><img src="{p}"></div>' if p else '<div class="th ph0"></div>'
    if 'next_ut' in m:
        nx = f'<b>{eta(m["next_ut"])}</b><span>{loc(m, "next")}</span>'
    else:
        nx = f'<b>~{m["sci_per_day"]:g}</b><span>{T("sci / day")}</span>'
    rows.append(f'<div class="rw">{th}<div class="nm">{craft_name(m["slug"])}<span>{icon(ic, 18, "#8e98b6")}{crew} · #{m["n"]}</span></div>'
                f'<div class="wh">{planet(m["body"], 26)}{loc(m, "where")}</div><div class="nx">{nx}</div></div>')

body = f'''
{header('planet', 'Where it has been', headline)}
{mapdiv}
<div class="rows"><div class="t lbl">{icon('live', 20, '#56c8ff')} {T('flying now')}</div>{''.join(rows)}</div>
'''

write('02-journey.html', page('Where it has been', css, body, 2, seed=19))
