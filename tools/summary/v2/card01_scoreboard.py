from common2 import *

counts = {k: 0 for k in RES}
for l in LAUNCHES:
    counts[code(l)] += 1
N = len(LAUNCHES)
FIRST_N = {f['n'] for f in RECORD['firsts']}

# farthest body flown to (reached or en route)
far = max((dest_body(l['dest'])[0] for l in LAUNCHES), key=BODY_ORDER.index)
headline = f'{CN["real_days"]}일·발사 {N}번·{BODY_NAME[far]}까지'

css = '''
.launch{display:flex;gap:22px;align-items:stretch}
.big{display:flex;flex-direction:column;justify-content:center;width:230px;padding:14px 22px;border-radius:22px;background:var(--panel);border:1px solid var(--line)}
.big .n{font-size:112px;font-weight:700;line-height:.9;letter-spacing:-.04em}
.big .l{font-size:21px;color:var(--muted);margin-top:10px;letter-spacing:.08em;text-transform:uppercase;display:flex;gap:8px;align-items:center}
.right{flex:1;display:flex;flex-direction:column;gap:9px;justify-content:center;min-width:0}
.bar{display:flex;height:84px;border-radius:18px;overflow:hidden;gap:4px}
.bar div{display:flex;align-items:center;justify-content:center;gap:8px;font-size:42px;font-weight:700;min-width:88px}
.bar .c-ok{background:linear-gradient(180deg,#46e38b,#23b863)}
.bar .c-rev{background:linear-gradient(180deg,#ffab4d,#f08416)}
.bar .c-dead{background:linear-gradient(180deg,#ff6a78,#e33445);color:#fff}
.bar .c-fail{background:linear-gradient(180deg,#a6afca,#7c86a3)}
.bar .c-live{background:linear-gradient(180deg,#7ad6ff,#2fa9e6)}
.strip{display:flex;gap:4px}
.strip i{flex:1;height:30px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-style:normal;font-size:16px;font-weight:700;font-family:'JetBrains Mono',monospace;letter-spacing:-.06em}
.strip i.star{box-shadow:0 0 0 2.5px var(--gold)}
.strip i.pad{visibility:hidden}
.funds{padding:18px 24px 10px}
.funds .top{display:flex;align-items:center;gap:14px}
.funds .v{font-size:50px;font-weight:700;letter-spacing:-.02em;color:var(--fund)}
.funds .v.s{color:var(--muted);font-size:36px}
.funds .k{font-size:17px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase}
.funds .now{margin-left:auto;text-align:right}
.funds .now .v{font-size:40px;color:var(--text)}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:16px 18px;min-height:168px;display:flex;flex-direction:column;gap:4px}
.tile .n{font-size:54px;font-weight:700;letter-spacing:-.03em;line-height:1.05;white-space:nowrap}
.tile .n small{font-size:26px;color:var(--muted);font-weight:600;margin-left:6px;letter-spacing:0}
.tile .l{font-size:18px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;display:flex;align-items:center;gap:8px}
.tile .sub{font-size:19px;color:var(--muted);display:flex;align-items:center;gap:6px;margin-top:auto;white-space:nowrap}
.tile .sub b{color:var(--text)}
.tdots{display:grid;grid-template-columns:repeat(12,1fr);gap:4px;margin-top:auto}
.tdots i{display:block;height:10px;border-radius:3px;background:var(--tech);opacity:.85}
.row{display:flex;gap:2px;align-items:center;margin-top:auto;flex-wrap:wrap}
.bodies{display:grid;grid-template-columns:repeat(''' + str(len(BODY_ORDER)) + ''',1fr);position:relative;align-items:end;margin-top:20px}
.body{display:flex;flex-direction:column;align-items:center;gap:6px;position:relative;z-index:1}
.body .pl{height:140px;display:flex;align-items:center;justify-content:center;position:relative}
.body .nm{font-size:23px;font-weight:700}
.body .st{display:flex;align-items:center;gap:6px;font-size:19px;color:var(--muted);height:26px;white-space:nowrap}
.body .st b{color:var(--text)}
.body .who{font-size:18px;color:var(--muted);height:24px}
.traj{position:absolute;left:48px;right:48px;top:70px;height:2px;z-index:0}
.badge{position:absolute;top:8px;right:-6px;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:3px solid var(--bg)}
.enroute{font-size:14px;font-weight:700;letter-spacing:.04em;color:#c8f0a0;border:1.5px dashed var(--jool);border-radius:999px;padding:2px 7px}
'''

# ---- funds chart
TL = CN['funds_timeline']
W, H = 968 - 48, 250
x0, x1, ytop, ybot = 44, W - 30, 36, H - 42
ymax = -(-max(p['funds'] or 0 for p in TL) // 1_000_000) * 1_000_000  # next whole million: points stay under the header


def X(i):
    return x0 + (x1 - x0) * i / (len(TL) - 1)


def Y(v):
    return ybot - (ybot - ytop) * v / ymax


boxes = []
pts = [(i, p) for i, p in enumerate(TL) if p['funds'] is not None]
poly = ' '.join(f'{X(i):.1f},{Y(p["funds"]):.1f}' for i, p in pts)
area = f'M{X(pts[0][0]):.1f},{ybot} L' + ' L'.join(f'{X(i):.1f},{Y(p["funds"]):.1f}' for i, p in pts) + f' L{X(pts[-1][0]):.1f},{ybot} Z'
svg = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" style="display:block;margin-top:4px;overflow:visible">',
       '<defs><linearGradient id="fa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f7d75c" stop-opacity=".42"/>'
       '<stop offset="1" stop-color="#f7d75c" stop-opacity="0"/></linearGradient></defs>']
for v in range(1_000_000, ymax + 1, 1_000_000):
    svg.append(f'<line x1="{x0}" x2="{x1}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="rgba(255,255,255,.08)" stroke-dasharray="3 6"/>')
    svg.append(f'<text x="{x0 - 8}" y="{Y(v) + 5:.1f}" text-anchor="end" font-size="16" fill="#5c6684" font-family="JetBrains Mono">{v // 1_000_000}M</text>')
svg.append(f'<line x1="{x0}" x2="{x1}" y1="{ybot}" y2="{ybot}" stroke="rgba(255,255,255,.18)"/>')
svg.append(f'<path d="{area}" fill="url(#fa)"/>')
svg.append(f'<polyline points="{poly}" fill="none" stroke="#f7d75c" stroke-width="3.5" stroke-linejoin="round" stroke-linecap="round"/>')
last_tick_x = -999
for i, p in enumerate(TL):
    fac = p['tick'] == 'facility'
    if fac:
        svg.append(f'<g transform="translate({X(i) - 10:.1f},{ybot + 9})" color="#ff9a2e"><use href="#i-building" width="20" height="20"/></g>')
    if p['funds'] is None:
        continue
    last = i == len(TL) - 1
    col = '#ff9a2e' if fac else '#f7d75c'
    svg.append(f'<circle cx="{X(i):.1f}" cy="{Y(p["funds"]):.1f}" r="{8 if last else 5.5}" fill="{col}" stroke="#070b17" stroke-width="3"/>')
    if p['label']:
        v = p['funds']
        prv = next((q['funds'] for q in reversed(TL[:i]) if q['funds'] is not None), None)
        nxt = next((q['funds'] for q in TL[i + 1:] if q['funds'] is not None), None)
        lo = [q for q in (prv, nxt) if q is not None]
        above_l, above_r = (X(i) - 8, Y(v) - 10, 'end'), (X(i) + 8, Y(v) - 10, 'start')
        if prv is None:                            # first point: above, starting at the point
            cands = [(X(i) - 6, Y(v) - 14, 'start')]
        elif all(q > v for q in lo):               # a dip: below, or above when it sits on the axis
            cands = [(X(i), Y(v) + 30, 'middle')] if Y(v) + 34 < ybot else [(X(i), Y(v) - 22, 'middle'), above_r]
        elif prv < v and (nxt is None or nxt < v):  # a peak (leans left when the next point is labelled too)
            cands = [(X(i), Y(v) - 15, 'middle'), above_l, above_r]
            if i + 1 < len(TL) and TL[i + 1]['label']:
                cands = [above_l] + cands
        elif prv < v:                              # rising: above-left
            cands = [above_l, (X(i), Y(v) - 15, 'middle')]
        else:                                      # falling: above-right
            cands = [above_r, (X(i), Y(v) - 15, 'middle')]
        w = len(p['label']) * 11.5
        for xx, yy, anc in cands:
            bx0 = xx - w / 2 if anc == 'middle' else xx - w if anc == 'end' else xx
            box = (bx0, yy - 17, w, 21)
            if not any(box[0] < c[0] + c[2] and c[0] < box[0] + box[2] and box[1] < c[1] + c[3] and c[1] < box[1] + box[3]
                       for c in boxes):
                break
        boxes.append(box)
        svg.append(f'<text x="{xx:.1f}" y="{yy:.1f}" text-anchor="{anc}" font-size="20" font-weight="700" '
                   f'fill="{"#ffb45c" if fac else "#f7d75c"}" font-family="Space Grotesk">{p["label"]}</text>')
        if not fac and X(i) - last_tick_x > 46:   # skip a tick label that would collide
            last_tick_x = X(i)
            t = '▶' if p['tick'] == 'start' else p['tick']
            svg.append(f'<text x="{X(i):.1f}" y="{ybot + 27}" text-anchor="middle" font-size="16" fill="#8e98b6" font-family="JetBrains Mono">{t}</text>')
svg.append('</svg>')
chart = ''.join(svg)

# ---- launch strip, two rows
half = (N + 1) // 2


def cell(l):
    k = code(l)
    return f'<i class="{RES[k][1]}{" star" if l["n"] in FIRST_N else ""}">{l["n"]}</i>'


rows = [LAUNCHES[:half], LAUNCHES[half:]]
strip = ''.join('<div class="strip">' + ''.join(cell(l) for l in r) + '<i class="pad"></i>' * (half - len(r)) + '</div>' for r in rows)
bar = ''.join(f'<div class="{RES[k][1]}" style="flex:{counts[k]}">{icon(RES[k][0], 34)}{counts[k]}</div>' for k in RES if counts[k])

# ---- tiles
n_tech = len(RECORD['research'])
rd = CN['facilities']['R&D']
kb = RECORD['kerbals']
n_dead = len(kb['deaths_that_stood'])
n_resc = len(kb['rescued'])
game_days = ut_to_days(CN['ut'])

# ---- bodies: first landing, else first orbit, else first anything, per body (firsts[])
live_bodies = {m['body'] for m in RECORD['live_missions'] if m['type'] == 'probe'}


def pick(body):
    fs = [f for f in RECORD['firsts'] if dest_body(f['body'])[0] == body]
    for kind in ('landing', 'orbit'):
        for f in fs:
            if f['kind'] == kind:
                return f
    return fs[0] if fs else None


SIZE = {'kerbin': 94, 'mun': 72, 'minmus': 60, 'duna': 84, 'eve': 90, 'gilly': 40, 'moho': 62, 'dres': 60, 'jool': 104,
        'eeloo': 56}
# a probe on its way to a body with no first yet (Dres 1): EN ROUTE from live_missions
EN_ROUTE = {m['to']: m['n'] for m in RECORD['live_missions'] if m['type'] == 'probe' and 'to' in m}
bodies = []
for b in BODY_ORDER:
    f = pick(b)
    who = f['who'] if f else ''
    reached = f and f['kind'] != 'probe'
    if f and f['kind'] == 'landing':
        badge = f'<div class="badge" style="background:var(--gold)">{icon("flag", 22, "#3b2a00")}</div>'
        st = f'{icon("star", 20, "#ffcf4a")}<b>#{f["n"]}</b>'
    elif reached:
        badge = f'<div class="badge" style="background:#1d3a66">{icon("orbit", 24, "#bfe3ff")}</div>'
        st = f'{icon("orbit", 20, "#8e98b6")}<b>#{f["n"]}</b>'
    else:
        badge = ''
        # badge on the status line, launch number underneath (10 bodies: the two don't fit side by side)
        n_en = f['n'] if f else EN_ROUTE.get(b)
        st = '<span class="enroute">EN ROUTE</span>' if n_en else ''
        who = f'<b style="color:var(--text)">#{n_en}</b>' if n_en else who
    dashed = b in live_bodies and not reached
    col = 'color:#c8f0a0' if dashed else ''
    bodies.append(f'<div class="body"><div class="pl">{planet(b, SIZE[b], dashed=dashed)}{badge}</div>'
                  f'<div class="nm" style="{col}">{BODY_NAME[b]}</div><div class="st">{st}</div><div class="who">{who}</div></div>')

body = f'''
{header('rocket', 'Claude × KSP · <b>Career</b> · Normal', headline)}
<div class="sec launch">
  <div class="big"><div class="n">{N}</div><div class="l">{icon('rocket', 22, '#8e98b6')} Launches</div></div>
  <div class="right"><div class="bar">{bar}</div>{strip}</div>
</div>
<div class="sec panel funds">
  <div class="top">{icon('coin', 44, '#f7d75c')}
    <span class="v s">{fmt_funds(CN['funds_start'])}</span>{icon('arrow', 30, '#5c6684')}<span class="v">{fmt_funds(CN['funds_peak'])}</span>
    <span class="k" style="margin-left:6px">peak</span>
    <div class="now"><div class="k">now</div><div class="v">{fmt_funds(CN['funds'])}</div></div>
  </div>
  {chart}
</div>
<div class="sec tiles">
  <div class="tile"><div class="l">{icon('gyro', 22, '#b28cff')} Tech</div><div class="n" style="color:var(--tech)">{n_tech}<small>R&amp;D Lv.{rd}</small></div>
    <div class="tdots">{'<i></i>' * n_tech}</div></div>
  <div class="tile"><div class="l">{icon('skull', 22, '#ff4d5e')} Kerbals</div>
    <div class="n"><span style="color:var(--dead)">{n_dead}</span><small>사망</small></div>
    <div class="n" style="font-size:40px"><span style="color:#9ccc3c">+{n_resc}</span><small>구조</small></div>
    </div>
  <div class="tile"><div class="l">{icon('star', 22, '#ffcf4a')} Rep</div><div class="n" style="color:var(--gold)">{CN['reputation']:.0f}</div>
    <div class="sub">reputation</div></div>
  <div class="tile"><div class="l">{icon('clock', 22, '#56c8ff')} Game time</div><div class="n" style="color:var(--sci);font-size:44px">~{fmt_ydays(game_days)}</div>
    <div class="sub">{icon('arrow', 18, '#5c6684')} real <b>{CN['real_days']} days</b></div></div>
</div>
<div class="bodies">
  <svg class="traj" viewBox="0 0 828 2" preserveAspectRatio="none"><line x1="0" y1="1" x2="828" y2="1" stroke="#3a4566" stroke-width="2" stroke-dasharray="6 7"/></svg>
  {''.join(bodies)}
</div>
'''

write('01-scoreboard.html', page('Career scoreboard', css, body, 1, seed=7))
