from common2 import *

UA = RECORD['ut_anchors']
RD = RECORD['real_days']
now_d = ut_to_days(CN['ut'])
headline = T('h10', days=CN['real_days'], years=round(now_d / YEAR_D))
end_d = max(ut_to_days(a['ut']) for a in UA['future'])
jool = max(UA['future'], key=lambda a: a['ut'])  # the farthest future event (was Jool; now Dres 1's arrival)
far_body = dest_body(BY_N[jool['n']]['dest'])[0]

css = '''
.stats{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-top:22px}
.st{background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:14px 18px;display:flex;flex-direction:column;gap:4px}
.st .l{font-size:17px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;display:flex;align-items:center;gap:8px}
.st .v{font-family:'JetBrains Mono',monospace;font-size:44px;font-weight:700;line-height:1.05;white-space:nowrap}
.st .s{font-size:18px;color:var(--muted)}
.tl{position:relative;margin-top:18px;height:880px}
.tl svg{position:absolute;left:0;top:0;overflow:visible}
.lb{position:absolute;display:flex;align-items:center;gap:10px;white-space:nowrap;transform:translateY(-50%);height:30px}
.lb .n{font-family:'JetBrains Mono',monospace;font-size:17px;font-weight:700;border-radius:8px;padding:2px 8px;background:rgba(255,255,255,.07);color:#c9d1e8}
.lb .t{font-size:21px;font-weight:600}
.lb .d{font-family:'JetBrains Mono',monospace;font-size:17px;color:var(--muted)}
.lb.fu .t{color:#c8f0a0}
.lb.fu .n{background:rgba(168,217,122,.12);color:#c8f0a0}
.dl{position:absolute;right:calc(968px - 118px);transform:translateY(-50%);text-align:right;white-space:nowrap}
.dl b{display:block;font-size:20px}
.dl span{font-family:'JetBrains Mono',monospace;font-size:17px;color:var(--muted)}
'''

TOP, H = 16, 850
AX = 205
DAY_COL = ['#7d8cff', '#56c8ff', '#35d67c', '#b28cff']


def Y(d):
    return TOP + H * d / end_d


svg = [f'<svg width="968" height="{TOP + H + 20}" viewBox="0 0 968 {TOP + H + 20}">']
# year ticks
for y in range(0, int(end_d // YEAR_D) + 1):
    yy = Y(y * YEAR_D)
    if abs(yy - Y(now_d)) < 18:
        continue
    svg.append(f'<line x1="{AX - 10}" x2="{AX}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="#5c6684" stroke-width="2"/>'
               f'<text x="{AX - 16}" y="{yy + 6:.1f}" text-anchor="end" font-size="17" fill="#8e98b6" font-family="JetBrains Mono">{y}y</text>')
# axis: past solid, future dashed
svg.append(f'<line x1="{AX}" x2="{AX}" y1="{Y(0):.1f}" y2="{Y(now_d):.1f}" stroke="#eef2ff" stroke-opacity=".7" stroke-width="3"/>')
svg.append(f'<line x1="{AX}" x2="{AX}" y1="{Y(now_d):.1f}" y2="{Y(end_d):.1f}" stroke="#a8d97a" stroke-width="3" stroke-dasharray="6 8"/>')
# real-day stripes
dls = []
prev = 0.0
for i, r in enumerate(RD):
    d1 = ut_to_days(r['ut_end'])
    col = DAY_COL[i % len(DAY_COL)]
    svg.append(f'<rect x="124" y="{Y(prev):.1f}" width="22" height="{max(Y(d1) - Y(prev), 4):.1f}" rx="6" fill="{col}" opacity=".85"/>')
    mid = max((Y(prev) + Y(d1)) / 2, TOP + 22)
    if i == len(RD) - 1:  # keep the last day's label clear of the NOW marker
        mid = min(mid, Y(now_d) - 44)
    rng = f'#{r["n_first"]}' if r['n_first'] == r['n_last'] else f'#{r["n_first"]}–#{r["n_last"]}'
    dls.append(f'<div class="dl" style="top:{mid:.0f}px"><b style="color:{col}">day {i + 1}</b><span>{rng}</span></div>')
    prev = d1

# markers + labels spread so they don't overlap (min gap), leader lines back to the true position
marks = [(ut_to_days(a['ut']), a, False) for a in UA['past']] + [(ut_to_days(a['ut']), a, True) for a in UA['future']]
marks.sort(key=lambda m: m[0])
GAP = 34
ys = [Y(d) for d, _, _ in marks]
pos = ys[:]
for _ in range(200):  # relax: push apart, pull toward the true y
    for i in range(1, len(pos)):
        if pos[i] - pos[i - 1] < GAP:
            push = (GAP - (pos[i] - pos[i - 1])) / 2
            pos[i - 1] -= push
            pos[i] += push
    pos = [max(TOP, min(TOP + H, p)) for p in pos]
    pos = [p + (t - p) * .02 for p, t in zip(pos, ys)]
labels = []
LX = 262
for (d, a, fut), y, py in zip(marks, ys, pos):
    col = '#a8d97a' if fut else '#eef2ff'
    svg.append(f'<path d="M{AX},{y:.1f} C{AX + 28},{y:.1f} {LX - 34},{py:.1f} {LX - 8},{py:.1f}" fill="none" stroke="{col}" stroke-opacity=".35" stroke-width="1.5"/>')
    svg.append(f'<circle cx="{AX}" cy="{y:.1f}" r="6" fill="{col if not fut else "#070b17"}" stroke="{col}" stroke-width="2.5"/>')
    n = f'<span class="n">#{a["n"]}</span>' if a.get('n') else ''
    ap = '~' if a.get('approx') else ''
    labels.append(f'<div class="lb{" fu" if fut else ""}" style="left:{LX}px;top:{py:.0f}px">{n}<span class="t">{esc(loc(a, "label"))}</span>'
                  f'<span class="d">{ap}{fmt_ydays(d)}</span></div>')
# now marker
yn = Y(now_d)
svg.append(f'<line x1="118" x2="{AX + 14}" y1="{yn:.1f}" y2="{yn:.1f}" stroke="#ffcf4a" stroke-width="3"/>'
           f'<circle cx="{AX}" cy="{yn:.1f}" r="10" fill="#ffcf4a"/>'
           f'<text x="112" y="{yn + 7:.1f}" text-anchor="end" font-size="20" font-weight="700" fill="#ffcf4a" font-family="Space Grotesk">NOW</text>')
svg.append('</svg>')

body = f'''
{header('clock', 'Game time', headline)}
<div class="stats">
  <div class="st"><div class="l">{icon('clock', 20, '#8e98b6')} Real</div><div class="v">{CN['real_days']} days</div><div class="s">{RD[0]['date']} → {CN['date']}</div></div>
  <div class="st"><div class="l">{icon('planet', 20, '#8e98b6')} Game</div><div class="v" style="color:var(--gold)">~{fmt_ydays(now_d)}</div><div class="s">Kerbin day ~{num(now_d)} · 1y = {YEAR_D}d</div></div>
  <div class="st"><div class="l">{icon('sat', 20, '#a8d97a')} {esc(loc(jool, 'label'))}</div><div class="v" style="color:var(--jool)">{T('in', t='~' + fmt_ydays(days_from_now(jool['ut'])))}</div><div class="s">{BODY_NAME[far_body]} · #{jool['n']}</div></div>
</div>
<div class="tl">{''.join(svg)}{''.join(dls)}{''.join(labels)}</div>
'''

write('10-time.html', page('Game time', css, body, 10, seed=61))
