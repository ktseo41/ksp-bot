from common import *

counts = {'ok': 0, 'rev': 0, 'dead': 0}
for l in LAUNCHES:
    counts[l[2]] += 1
assert counts == {'ok': 9, 'rev': 8, 'dead': 3}

css = '''
.hdr{display:flex;justify-content:space-between;align-items:flex-end}
.title .x{color:var(--muted);font-weight:500;margin:0 6px}
.datechip{font-size:18px;color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:7px 14px;letter-spacing:.04em}
.sec{margin-top:26px}
.launch{display:flex;gap:28px;align-items:stretch}
.big{display:flex;flex-direction:column;justify-content:center;width:250px;padding:18px 22px;border-radius:22px;background:var(--panel);border:1px solid var(--line)}
.big .n{font-size:116px;font-weight:700;line-height:.9;letter-spacing:-.04em;display:flex;align-items:center;gap:10px}
.big .l{font-size:22px;color:var(--muted);margin-top:8px;letter-spacing:.08em;text-transform:uppercase}
.right{flex:1;display:flex;flex-direction:column;gap:14px;justify-content:center}
.bar{display:flex;height:100px;border-radius:18px;overflow:hidden;gap:4px}
.bar div{display:flex;align-items:center;justify-content:center;gap:10px;font-size:54px;font-weight:700}
.bar .c-ok{background:linear-gradient(180deg,#46e38b,#23b863)}
.bar .c-rev{background:linear-gradient(180deg,#ffab4d,#f08416)}
.bar .c-dead{background:linear-gradient(180deg,#ff6a78,#e33445);color:#fff}
.strip{display:flex;gap:5px}
.strip i{flex:1;height:36px;border-radius:7px;display:flex;align-items:center;justify-content:center;font-style:normal;font-size:16px;font-weight:700}
.strip i.star{box-shadow:0 0 0 2.5px var(--gold)}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:22px 26px}
.funds .top{display:flex;align-items:center;gap:16px}
.funds .v{font-size:56px;font-weight:700;letter-spacing:-.02em;color:var(--fund)}
.funds .v.s{color:var(--muted);font-size:40px}
.funds .arr{color:var(--dim)}
.funds .now{margin-left:auto;text-align:right}
.funds .now .v{font-size:40px;color:var(--text)}
.funds .now .k{font-size:17px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.tile{background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:20px 20px 20px;min-height:190px;display:flex;flex-direction:column;gap:6px}
.tile .n{font-size:62px;font-weight:700;letter-spacing:-.03em;line-height:1}
.tile .l{font-size:19px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;display:flex;align-items:center;gap:8px}
.tile .sub{font-size:22px;color:var(--muted);display:flex;align-items:center;gap:6px}
.mini{margin-top:auto;padding-top:10px}
.mbar{display:flex;height:16px;border-radius:5px;overflow:hidden;gap:3px}
.mbar i{display:block}
.dots{display:grid;grid-template-columns:repeat(8,1fr);gap:5px}
.dots i{display:block;height:12px;border-radius:3px;background:var(--tech);opacity:.85}
.row{display:flex;gap:3px;align-items:center}
.lv{font-size:26px;color:var(--muted);font-weight:500;margin-left:8px;letter-spacing:.02em}
.bodies{display:flex;justify-content:space-between;align-items:flex-end;position:relative;padding:4px 10px 0}
.body{display:flex;flex-direction:column;align-items:center;gap:8px;position:relative;z-index:1;width:210px}
.body .pl{height:160px;display:flex;align-items:center;justify-content:center}
.body .nm{font-size:27px;font-weight:700}
.body .st{display:flex;align-items:center;gap:8px;font-size:21px;color:var(--muted);height:30px}
.body .st b{color:var(--text)}
.traj{position:absolute;left:100px;right:100px;top:83px;height:2px;z-index:0}
.badge{position:absolute;top:-4px;right:18px;width:46px;height:46px;border-radius:50%;display:flex;align-items:center;justify-content:center;border:3px solid var(--bg)}
.next{font-size:16px;font-weight:700;letter-spacing:.14em;color:#ffb08e;border:1.5px dashed #ff9d73;border-radius:999px;padding:4px 12px}
'''

# funds chart
pts = [('start', 25000), ('#1', 110000), ('#2', 136000), ('#4', 212000), ('B', 13700), ('#5', 121800),
       ('#10', 385300), ('#16', 342800), ('#18', 609000), ('#20', 1299942), ('B', 848942)]
W, H = 968 - 52, 262
x0, x1, ytop, ybot = 40, W - 40, 34, H - 44
ymax = 1300000
ytop = 40


def X(i):
    return x0 + (x1 - x0) * i / (len(pts) - 1)


def Y(v):
    return ybot - (ybot - ytop) * v / ymax


poly = ' '.join(f'{X(i):.1f},{Y(v):.1f}' for i, (_, v) in enumerate(pts))
area = f'M{X(0):.1f},{ybot} L' + ' L'.join(f'{X(i):.1f},{Y(v):.1f}' for i, (_, v) in enumerate(pts)) + f' L{X(len(pts)-1):.1f},{ybot} Z'
labels = {0: '25k', 3: '212k', 4: '13.7k', 6: '385k', 8: '609k', 9: '1.30M', 10: '849k'}
svg = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" style="display:block;margin-top:6px;overflow:visible">',
       '<defs><linearGradient id="fa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f7d75c" stop-opacity=".45"/><stop offset="1" stop-color="#f7d75c" stop-opacity="0"/></linearGradient></defs>']
for v in (500000, 1000000):
    svg.append(f'<line x1="{x0}" x2="{x1}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="rgba(255,255,255,.08)" stroke-dasharray="3 6"/>')
    svg.append(f'<text x="{x0-8}" y="{Y(v)+5:.1f}" text-anchor="end" font-size="15" fill="#5c6684" font-family="JetBrains Mono">{v//1000000 if v>=1000000 else v//1000}{"M" if v>=1000000 else "k"}</text>')
svg.append(f'<line x1="{x0}" x2="{x1}" y1="{ybot}" y2="{ybot}" stroke="rgba(255,255,255,.18)"/>')
svg.append(f'<path d="{area}" fill="url(#fa)"/>')
svg.append(f'<polyline points="{poly}" fill="none" stroke="#f7d75c" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>')
for i, (lab, v) in enumerate(pts):
    fac = lab == 'B'
    col = '#ff9a2e' if fac else '#f7d75c'
    r = 9 if i == 9 else 6.5
    svg.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="{r}" fill="{col}" stroke="#070b17" stroke-width="3"/>')
    if i in labels:
        big = i in (9,)
        dy = -18 if i != 4 else -16
        anchor = 'middle' if 0 < i < 10 else ('start' if i == 0 else 'end')
        xx = X(i) + (8 if i == 10 else 0) if i != 0 else X(i) - 6
        if i == 10:
            anchor = 'middle'
        if i == 8:
            xx, anchor = X(i) - 12, 'end'
            dy = -8
        svg.append(f'<text x="{xx:.1f}" y="{Y(v)+dy:.1f}" text-anchor="{anchor}" font-size="{30 if big else 21}" font-weight="700" '
                   f'fill="{"#f7d75c" if not fac else "#ffb45c"}" font-family="Space Grotesk">{labels[i]}</text>')
    # axis labels
    if not fac:
        svg.append(f'<text x="{X(i):.1f}" y="{ybot+30}" text-anchor="middle" font-size="17" fill="#8e98b6" font-family="JetBrains Mono">{lab if lab!="start" else "▶"}</text>')
# facility upgrades (6): MC2 between #1/#2, TS2+Pad2 at idx4, VAB2 between #10/#16, AC2 between #18/#20, R&D2 at idx10
for fx, n in ((1.5, 1), (4, 2), (6.5, 1), (8.5, 1), (10, 1)):
    xc = x0 + (x1 - x0) * fx / (len(pts) - 1)
    for k in range(n):
        off = (k - (n - 1) / 2) * 24
        svg.append(f'<g transform="translate({xc+off-11:.1f},{ybot+12})" color="#ff9a2e"><use href="#i-building" width="22" height="22"/></g>')
svg.append('</svg>')
chart = ''.join(svg)

strip = ''.join(
    f'<i class="{RES[r][1]}{" star" if n in FIRSTS else ""}">{n}</i>' for n, s, r, *_ in LAUNCHES)

body = f'''
<div class="hdr">
  <div>
    <div class="kicker">{icon('rocket', 26, '#8e98b6')}<span>Kerbal Space Program · <b>Career</b> · Normal</span></div>
    <div class="title">Claude <span class="x">×</span> KSP</div>
  </div>
  <div class="datechip mono">2026-09-24</div>
</div>

<div class="sec launch">
  <div class="big"><div class="n">20</div><div class="l">{icon('rocket', 22, '#8e98b6')} Launches</div></div>
  <div class="right">
    <div class="bar">
      <div class="c-ok" style="flex:9">{icon('check', 46)}9</div>
      <div class="c-rev" style="flex:8">{icon('revert', 46)}8</div>
      <div class="c-dead" style="flex:3">{icon('skull', 42)}3</div>
    </div>
    <div class="strip">{strip}</div>
  </div>
</div>

<div class="sec panel funds">
  <div class="top">
    {icon('coin', 50, '#f7d75c')}
    <span class="v s">25k</span>{icon('arrow', 34, '#5c6684', 'arr')}<span class="v">1.30M</span>
  </div>
  {chart}
</div>

<div class="sec tiles">
  <div class="tile"><div class="l">{icon('flask', 24, '#56c8ff')} Science</div><div class="n" style="color:var(--sci)">750.5</div>
     <div class="mini"><div class="mbar"><i style="flex:89.9;background:var(--kerbin)"></i><i style="flex:122;background:var(--mun)"></i><i style="flex:538.6;background:var(--minmus)"></i></div></div></div>
  <div class="tile"><div class="l">{icon('gyro', 24, '#b28cff')} Tech</div><div class="n" style="color:var(--tech)">16</div>
     <div class="mini dots"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div></div>
  <div class="tile"><div class="l">{icon('skull', 24, '#ff4d5e')} Kerbals</div><div class="n" style="color:var(--dead)">3</div>
     <div class="mini row">{icon('skull', 21, '#ff4d5e', style='opacity:1')}{icon('skull', 21, '#ff4d5e', style='opacity:1')}{icon('skull', 21, '#ff4d5e', style='opacity:1')}<span style="width:6px"></span>{icon('skull', 21, '#ff4d5e', style='opacity:0.3')}{icon('skull', 21, '#ff4d5e', style='opacity:0.3')}{icon('skull', 21, '#ff4d5e', style='opacity:0.3')}{icon('skull', 21, '#ff4d5e', style='opacity:0.3')}{icon('skull', 21, '#ff4d5e', style='opacity:0.3')}</div></div>
  <div class="tile"><div class="l">{icon('building', 24, '#ff9a2e')} Facilities</div><div class="n">6<span class="lv">Lv.2</span></div>
     <div class="mini row">{icon('building', 24, '#ff9a2e')}{icon('building', 24, '#ff9a2e')}{icon('building', 24, '#ff9a2e')}{icon('building', 24, '#ff9a2e')}{icon('building', 24, '#ff9a2e')}{icon('building', 24, '#ff9a2e')}</div></div>
</div>

<div class="sec bodies">
  <svg class="traj" viewBox="0 0 768 2" preserveAspectRatio="none"><line x1="0" y1="1" x2="768" y2="1" stroke="#3a4566" stroke-width="2" stroke-dasharray="6 7"/></svg>
  <div class="body"><div class="pl">{planet('kerbin', 156)}</div><div class="badge" style="background:#1d3a66">{icon('orbit', 28, '#bfe3ff')}</div>
     <div class="nm">Kerbin</div><div class="st">{icon('orbit', 22, '#8e98b6')} <b>#4</b></div></div>
  <div class="body"><div class="pl">{planet('minmus', 118)}</div><div class="badge" style="background:var(--gold)">{icon('flag', 26, '#3b2a00')}</div>
     <div class="nm">Minmus</div><div class="st">{icon('star', 22, '#ffcf4a')} <b>#10</b> · Bill</div></div>
  <div class="body"><div class="pl">{planet('mun', 132)}</div><div class="badge" style="background:var(--gold)">{icon('flag', 26, '#3b2a00')}</div>
     <div class="nm">Mun</div><div class="st">{icon('star', 22, '#ffcf4a')} <b>#16</b> · Bob</div></div>
  <div class="body"><div class="pl">{planet('duna', 140, dashed=True)}</div>
     <div class="nm" style="color:#ffb08e">Duna</div><div class="st"><span class="next">NEXT</span></div></div>
</div>
'''

write('01-scoreboard.html', page('Career scoreboard', css, body, 1))
