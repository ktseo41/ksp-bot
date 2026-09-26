"""Launch grid shared by card 04 (first half) and card 05 (second half). Rendering is rule-based, no per-launch layout."""
from common2 import *

FIRST_N = {f['n'] for f in RECORD['firsts']}
MOONS = {'mun', 'minmus', 'ike'}
KO_DAYS = {1: '첫날', 2: '첫 이틀', 3: '사흘'}

css = '''
.keys{display:flex;flex-direction:column;gap:10px;margin-top:18px}
.keys .legend{gap:18px;font-size:18px;flex-wrap:wrap}
.keys .legend span{gap:7px}
.keys .legend .star{box-shadow:0 0 0 2.5px var(--gold);border-radius:7px;width:22px;height:22px;display:inline-block;background:var(--panel2)}
.tl{display:grid;grid-template-columns:repeat(4,1fr);grid-auto-rows:156px;gap:10px;margin-top:18px}
.lc{border-radius:15px;display:flex;overflow:hidden;position:relative;border:1.5px solid}
.lc .th{width:56px;flex:none;position:relative}
.lc .th img{width:100%;height:100%;object-fit:cover;display:block}
.lc .th.ph0{border:none;border-right:1.5px dashed rgba(255,255,255,.18)}
.lc .bd{flex:1;padding:8px 9px 9px 10px;display:flex;flex-direction:column;gap:3px;min-width:0}
.lc .top{display:flex;align-items:center;gap:6px}
.lc .num{font-size:30px;font-weight:700;letter-spacing:-.03em;line-height:1;margin-right:auto;display:flex;align-items:center;gap:4px}
.lc .num span{font-size:19px;color:var(--muted);font-weight:500}
.lc .res{width:30px;height:30px;border-radius:9px;display:flex;align-items:center;justify-content:center;flex:none}
.lc .cn{font-size:17px;font-weight:600;color:#dfe6f7;white-space:nowrap;overflow:hidden;display:flex;align-items:center;gap:4px;letter-spacing:-.02em}
.pl{display:inline-flex;border-radius:50%;flex:none}
.pl.orb{box-shadow:0 0 0 2px #070b17,0 0 0 3.5px rgba(200,215,255,.7)}
.lc .det{display:flex;flex-direction:column;gap:3px;margin-top:auto}
.mn{font-family:'JetBrains Mono',monospace;font-size:17px;font-weight:700;color:#c9d1e8;display:flex;align-items:center;gap:5px;white-space:nowrap}
.kb{display:flex;align-items:center;gap:5px;font-size:17px;font-weight:600;color:#dfe6f7;white-space:nowrap;overflow:hidden}
.kb.fd{opacity:.45}
.lc.first{box-shadow:0 0 0 3px var(--gold),0 0 24px rgba(255,207,74,.3)}
.lc.live .res{box-shadow:0 0 0 4px rgba(86,200,255,.25)}
.sum{border-radius:15px;border:1.5px dashed var(--line);display:flex;flex-direction:column;justify-content:center;gap:8px;padding:12px 16px}
.sum .r{display:flex;flex-wrap:wrap;gap:8px 14px}
.sum .r span{display:flex;align-items:center;gap:6px;font-size:24px;font-weight:700}
.sum .t{font-size:17px;color:var(--muted)}
'''


def kb(name, faded=False, ic='kerbal', col='#9ccc3c'):
    return f'<span class="kb{" fd" if faded else ""}">{icon(ic, 20, col)}{esc(name)}</span>'


def mono(t, ic=None, col='#8e98b6'):
    i = icon(ic, 18, col) if ic else ''
    return f'<span class="mn">{i}{esc(t)}</span>'


def crew_of(l):
    c = l.get('crew', '')
    return '' if not c or c.startswith('-') else c


def details(l):
    out = []
    if l.get('diverted_to'):
        d = l['diverted_to']
        out.append(f'<span class="kb">{icon("arrow", 18, "#8e98b6")}{planet(d, 20)}{BODY_NAME[d]}</span>')
    elif l.get('stat'):
        out.append(mono(l['stat'], 'boom' if 't=0' in l['stat'] else None, '#ff9a2e'))
    crew = crew_of(l)
    if crew:
        if l['result'] == 'crew lost':
            out.append(kb(crew, ic='skull', col='#ff4d5e'))
        else:
            out.append(kb(crew, faded=bool(l.get('revert_death'))))
            if l.get('revert_death'):
                out[-1] = kb(crew, faded=True, ic='skull', col='#ff4d5e')
    n = l.get('revert_death_count', 0)
    if n:
        # up to 3 faded skulls; beyond that one skull + ×n (same notation as the crew card)
        sk = ''.join(icon('skull', 18, '#ff4d5e') for _ in range(min(n, 3) if n <= 3 else 1))
        more = f'×{n}' if n > 3 else ''
        out.append(f'<span class="kb fd">{sk}{more}</span>')
    return ''.join(out)


def card(l):
    k = code(l)
    ic, cls = RES[k]
    kind, orb = dest_body(l['dest'])
    style = f'background:rgba({RES_TINT[k]},{.16 if k == "dead" else .09});border-color:rgba({RES_TINT[k]},.55)'
    first = l['n'] in FIRST_N
    star = icon('star', 20, '#ffcf4a') if first else ''
    pl = f'<span class="pl{" orb" if orb else ""}">{planet(kind, 22)}</span>'
    classes = 'lc' + (' first' if first else '') + (' live' if k == 'live' else '')
    return (f'<div class="{classes}" style="{style}">{thumb(l["slug"])}'
            f'<div class="bd"><div class="top"><div class="num"><span>#</span>{l["n"]}{star}</div>{pl}'
            f'<div class="res {cls}">{icon(ic, 22)}</div></div>'
            f'<div class="cn">{esc(craft_name(l["slug"]))}</div>'
            f'<div class="det">{details(l)}</div></div></div>')


def build(part, idx, seed):
    N = len(LAUNCHES)
    half = (N + 1) // 2
    ls = LAUNCHES[:half] if part == 0 else LAUNCHES[half:]
    a, b = ls[0]['n'], ls[-1]['n']
    dates = sorted({l['date'] for l in ls})
    all_dates = sorted({l['date'] for l in LAUNCHES})
    if part == 0:
        moons = len({dest_body(l['dest'])[0] for l in ls if l['result'] == 'success' and dest_body(l['dest'])[0] in MOONS
                     and any(l['n'] in v for kk, v in RECORD['landings_by_body'].items() if not kk.startswith('_'))})
        dead = sum(1 for l in ls if l['result'] == 'crew lost')
        headline = f'{KO_DAYS[len(dates)]}: 달 {KO_NUM[moons]}, 사망 {dead}'
    else:
        headline = f'{KO_ORD[all_dates.index(dates[0]) + 1]} 날부터: 구조·행성·정거장'
    counts = {}
    for l in ls:
        counts[code(l)] = counts.get(code(l), 0) + 1
    cells = [card(l) for l in ls]
    spare = 24 - len(cells)
    if spare:
        r = ''.join(f'<span style="color:rgba({RES_TINT[k]},1)">{icon(RES[k][0], 22)}{counts[k]}</span>' for k in RES if k in counts)
        cells.append(f'<div class="sum" style="grid-column:span {spare}"><div class="t">#{a}–#{b}</div><div class="r">{r}</div></div>')
    bodies = []
    for l in ls:
        kind, _ = dest_body(l['dest'])
        if kind not in bodies:
            bodies.append(kind)
    bodies.sort(key=BODY_ORDER.index)
    keys = ''.join(f'<span>{planet(b_, 22)}{BODY_NAME[b_]}</span>' for b_ in bodies)
    keys += f'<span><span class="pl orb">{planet("kerbin", 20)}</span>orbit</span><span><i class="star"></i>{icon("star", 18, "#ffcf4a")}first</span>'
    body = f'''
{header('rocket', f'Career launches · #{a} → #{b}', headline)}
<div class="keys">{legend([k for k in RES if k in counts], size=22)}<div class="legend">{keys}</div></div>
<div class="tl">{''.join(cells)}</div>
'''
    write(f'0{idx}-launches-{"ab"[part]}.html', page(f'Launches #{a}-#{b}', css, body, idx, seed=seed))
