import json
from collections import defaultdict
from common import *

SAVE = './docs/record/career-save.json'
d = json.load(open(SAVE))

# group subjects: (body, group) -> sci
groups = defaultdict(float)
for s in d['science']:
    exp, where = s['id'].split('@')
    body = next(b for b in ('Minmus', 'Kerbin', 'Mun') if where.startswith(b))
    rest = where[len(body):]
    if exp == 'recovery':
        g = 'Recovery'
    elif rest.startswith('InSpace'):
        g = 'Space'
    elif rest.startswith('Flying'):
        g = 'Air'
    elif rest.startswith('SrfLanded'):
        g = rest[len('SrfLanded'):]
    else:
        raise ValueError(where)
    groups[(body, g)] += s['sci']
tot = defaultdict(float)
for (b, g), v in groups.items():
    tot[b] += v
assert abs(sum(tot.values()) - 750.5) < 0.01, tot
print(dict(tot), dict(groups))

NICE = {'GreatFlats': 'Great Flats', 'GreaterFlats': 'Greater Flats', 'LesserFlats': 'Lesser Flats', 'LaunchPad': 'Launch Pad'}
GICON = {'Recovery': 'chute', 'Space': 'orbit', 'Air': 'air', 'LaunchPad': 'pad'}
COL = {'Kerbin': '#4fa8ea', 'Mun': '#b9bdc6', 'Minmus': '#a8e8cf'}
MAXV = max(groups.values())

css = '''
.hdr{display:flex;justify-content:space-between;align-items:flex-end}
.title{font-size:76px;color:var(--sci);display:flex;align-items:center;gap:16px}
.stack{display:flex;height:30px;border-radius:9px;overflow:hidden;gap:3px;margin-top:22px}
.stack i{display:block}
.stackl{display:flex;margin-top:8px;font-size:19px;font-weight:600}
.stackl span{display:flex;align-items:center;gap:6px}
.bodyrow{display:flex;gap:24px;margin-top:14px;background:var(--panel);border:1px solid var(--line);border-radius:20px;padding:14px 22px 14px 16px;align-items:center}
.bl{width:250px;flex:none;display:flex;align-items:center;gap:14px}
.bl .tx{display:flex;flex-direction:column;gap:0}
.bl .nm{font-size:26px;font-weight:700}
.bl .v{font-size:40px;line-height:1.05;font-weight:700;letter-spacing:-.02em}
.bars{flex:1;display:flex;flex-direction:column;gap:7px}
.br{display:flex;align-items:center;gap:12px;height:31px}
.br .lab{width:180px;flex:none;display:flex;align-items:center;gap:8px;font-size:19px;font-weight:600;color:#dbe2f3;white-space:nowrap}
.br .lab.g{color:var(--muted);font-weight:500}
.br .tr{flex:1;height:25px;position:relative}
.br .fill{height:100%;border-radius:6px;min-width:6px}
.br .val{font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700;width:70px;text-align:right;flex:none}
.tech{margin-top:30px}
.tech .th{display:flex;align-items:center;gap:12px;font-size:20px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-weight:600}
.tech .th b{font-size:34px;color:var(--tech);letter-spacing:0}
.tech .th .ln{flex:1;height:1px;background:var(--line)}
.tg{display:grid;grid-template-columns:repeat(8,1fr);gap:16px 8px;margin-top:18px;position:relative}
.tn{display:flex;flex-direction:column;align-items:center;gap:6px;position:relative;z-index:1}
.tn .hx{width:74px;height:74px;border-radius:21px;background:linear-gradient(160deg,#3b2c6e,#241a47);border:2px solid #7c62d6;display:flex;align-items:center;justify-content:center;position:relative}
.tn .hx .o{position:absolute;top:-8px;left:-8px;width:24px;height:24px;border-radius:50%;background:var(--bg);border:1.5px solid #7c62d6;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;color:#cbb8ff;font-family:'JetBrains Mono',monospace}
.tn .t{font-size:15px;color:#aeb7d2;text-align:center;line-height:1.15;font-weight:500;height:34px}
.tline{position:absolute;left:5%;right:5%;height:2px;background:linear-gradient(90deg,#4b3d86,#7c62d6);z-index:0}
'''


def bar_rows(body, order):
    rows = []
    for g in order:
        v = groups[(body, g)]
        ic = GICON.get(g)
        generic = g in ('Recovery', 'Space', 'Air')
        lab = NICE.get(g, g)
        if ic:
            labhtml = f'{icon(ic, 22, "#8e98b6")}{lab}'
        else:
            labhtml = f'{icon("flag", 20, COL[body])}{lab}'
        w = v / MAXV * 100
        op = '.55' if generic else '1'
        rows.append(f'<div class="br"><div class="lab{" g" if generic else ""}">{labhtml}</div>'
                    f'<div class="tr"><div class="fill" style="width:{w:.1f}%;background:{COL[body]};opacity:{op}"></div></div>'
                    f'<div class="val" style="color:{COL[body]}">{v:g}</div></div>')
    return ''.join(rows)


def section(body, kind, psize, order):
    v = round(tot[body], 1)
    return (f'<div class="bodyrow"><div class="bl">{planet(kind, psize)}<div class="tx"><div class="nm">{body}</div>'
            f'<div class="v" style="color:{COL[body]}">{v:g}</div></div></div><div class="bars">{bar_rows(body, order)}</div></div>')


def order_for(body):
    items = [(g, v) for (b, g), v in groups.items() if b == body]
    items.sort(key=lambda x: (-x[1], x[0]))
    return [g for g, _ in items]


TECH = [('start', 'Start', 'dot'), ('basicRocketry', 'Basic Rocketry', 'rocket'), ('engineering101', 'Engineering 101', 'wrench'),
        ('generalRocketry', 'General Rocketry', 'rocket'), ('survivability', 'Survivability', 'shield'), ('stability', 'Stability', 'fin'),
        ('advRocketry', 'Advanced Rocketry', 'rocket'), ('basicScience', 'Basic Science', 'flask'), ('heavyRocketry', 'Heavy Rocketry', 'rocket'),
        ('generalConstruction', 'General Construction', 'wrench'), ('flightControl', 'Flight Control', 'gyro'), ('fuelSystems', 'Fuel Systems', 'tank'),
        ('landing', 'Landing', 'leg'), ('electrics', 'Electrics', 'bolt'), ('heavierRocketry', 'Heavier Rocketry', 'rocket'),
        ('spaceExploration', 'Space Exploration', 'planet')]
assert [t[0] for t in TECH] == d['techs']

tnodes = ''.join(
    f'<div class="tn"><div class="hx"><span class="o">{i+1}</span>{icon(ic, 38, "#d9ccff")}</div><div class="t">{name}</div></div>'
    for i, (_, name, ic) in enumerate(TECH))

K, Mu, Mi = (round(tot[b], 1) for b in ('Kerbin', 'Mun', 'Minmus'))
body = f'''
<div class="hdr">
  <div>
    <div class="kicker">{icon('flask', 26, '#8e98b6')}<span>Science earned</span></div>
    <div class="title">750.5</div>
  </div>
</div>
<div class="stack"><i style="flex:{K};background:{COL['Kerbin']}"></i><i style="flex:{Mi};background:{COL['Minmus']}"></i><i style="flex:{Mu};background:{COL['Mun']}"></i></div>
<div class="stackl"><span style="flex:{K};color:{COL['Kerbin']}">{K:g}</span><span style="flex:{Mi};color:{COL['Minmus']};justify-content:center">{Mi:g}</span><span style="flex:{Mu};color:{COL['Mun']};justify-content:flex-end">{Mu:g}</span></div>
{section('Kerbin', 'kerbin', 96, order_for('Kerbin'))}
{section('Minmus', 'minmus', 90, order_for('Minmus'))}
{section('Mun', 'mun', 84, order_for('Mun'))}
<div class="tech"><div class="th">{icon('gyro', 26, '#b28cff')}<b>16</b>Tech<span class="ln"></span></div>
<div class="tg">{tnodes}</div></div>
'''

write('04-science.html', page('Science map', css, body, 4, seed=31))
