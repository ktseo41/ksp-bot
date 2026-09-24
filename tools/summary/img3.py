from common import *

BODY = {'kerbin': 'Kerbin', 'mun': 'Mun', 'minmus': 'Minmus'}
TINT = {'ok': '53,214,124', 'rev': '255,154,46', 'dead': '255,77,94'}
ALPHA = {'ok': .09, 'rev': .09, 'dead': .17}


def kb(name, faded=False):
    return f'<span class="kb{" fd" if faded else ""}">{icon("kerbal", 22, "#9ccc3c")}{name}</span>'


def sk(n=1, faded=False, name=''):
    s = ''.join(icon('skull', 22, '#ff4d5e') for _ in range(n))
    return f'<span class="kb{" fd" if faded else ""}">{s}{name}</span>'


def mono(t, ic=None, col=None):
    i = icon(ic, 20, col or '#8e98b6') if ic else ''
    return f'<span class="mn">{i}{t}</span>'


# per-launch stat/crew content is data (straight from career.json via LAUNCHES); only the layout
# (which combination of mono/kb/sk, icon overrides) is a presentation choice kept here.
STAT = {n: stat for n, _, _, _, stat, _ in LAUNCHES}
CREW = {n: crew for n, _, _, _, _, crew in LAUNCHES}
REVERT_DEATH_COUNT = {l['n']: l['revert_death_count'] for l in RECORD['career_launches'] if 'revert_death_count' in l}
DIVERTED_TO = {l['n']: l['diverted_to'] for l in RECORD['career_launches'] if 'diverted_to' in l}

DETAIL = {
    1: [mono(STAT[1])],
    2: [mono(STAT[2])],
    3: [mono(STAT[3])],
    4: [mono(STAT[4], 'orbit')],
    5: [kb(CREW[5])],
    6: [sk(1, name=CREW[6])],
    7: [mono(STAT[7]), kb(CREW[7])],
    8: [mono(STAT[8]), sk(1, True, CREW[8])],
    9: [mono(STAT[9], 'boom', '#ff9a2e')],
    10: [kb(CREW[10])],
    11: [sk(1, name=CREW[11])],
    12: [mono(STAT[12]), sk(1, name=CREW[12])],
    13: [mono(STAT[13], 'boom', '#ff9a2e'), sk(REVERT_DEATH_COUNT[13], True)],
    14: [mono(STAT[14], 'pad')],
    15: [mono(STAT[15])],
    16: [kb(CREW[16])],
    17: [f'<span class="kb">{icon("arrow", 20, "#8e98b6")}{planet(DIVERTED_TO[17], 24)}{DIVERTED_TO[17].capitalize()}</span>'],
    18: [mono(STAT[18]), kb(CREW[18])],
    19: [mono(STAT[19]), kb(CREW[19])],
    20: [mono(STAT[20]), kb(CREW[20])],
}

css = '''
.hdr{display:flex;justify-content:space-between;align-items:flex-end}
.title{font-size:70px}
.title small{font-size:34px;color:var(--muted);font-weight:500;margin-left:10px}
.tl{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:26px}
.lc{height:206px;border-radius:16px;display:flex;overflow:hidden;position:relative;border:1.5px solid}
.lc .th{width:66px;flex:none;position:relative}
.lc .th img{width:100%;height:100%;object-fit:cover;display:block}
.lc .bd{flex:1;padding:11px 12px 10px 13px;display:flex;flex-direction:column;gap:7px;min-width:0}
.lc .top{display:flex;align-items:center;justify-content:space-between}
.lc .num{font-size:40px;font-weight:700;letter-spacing:-.03em;line-height:1}
.lc .num span{font-size:22px;color:var(--muted);font-weight:500;margin-right:1px}
.lc .res{width:38px;height:38px;border-radius:11px;display:flex;align-items:center;justify-content:center}
.lc .dst{display:flex;align-items:center;gap:7px;font-size:19px;font-weight:600}
.lc .dst .ar{color:var(--muted)}
.lc .det{display:flex;flex-direction:column;gap:5px;margin-top:auto}
.mn{font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700;color:#c9d1e8;display:flex;align-items:center;gap:6px;white-space:nowrap}
.kb{display:flex;align-items:center;gap:5px;font-size:18px;font-weight:600;color:#dfe6f7}
.kb.fd{opacity:.42}
.lc.first{box-shadow:0 0 0 3px var(--gold),0 0 28px rgba(255,207,74,.35)}
.lc .fb{align-self:flex-start;display:inline-flex;align-items:center;gap:6px;background:var(--gold);color:#2b2000;border-radius:999px;padding:4px 11px 4px 8px;font-size:15px;font-weight:700;letter-spacing:.1em}
'''

cards = []
for n, slug, r, dst, fun, crew in LAUNCHES:
    ic, cls = RES[r]
    first = n in FIRSTS
    style = f'background:rgba({TINT[r]},{ALPHA[r]});border-color:rgba({TINT[r]},.55)'
    dhtml = f'{planet(dst, 28)}{BODY[dst]}'
    fb = ''
    det = (f'<span class="fb">{icon("star", 18, "#2b2000")}FIRST</span>' if first else '') + ''.join(DETAIL.get(n) or [mono(STAT[n]), kb(CREW[n])])
    cards.append(f'''<div class="lc{" first" if first else ""}" style="{style}">
<div class="th"><img src="crafts/{slug}.jpg"></div>
<div class="bd"><div class="top"><div class="num"><span>#</span>{n}</div><div class="res {cls}">{icon(ic, 26)}</div></div>
<div class="dst">{dhtml}</div><div class="det">{det}</div></div>{fb}</div>''')

body = f'''
<div class="hdr">
  <div>
    <div class="kicker">{icon('rocket', 26, '#8e98b6')}<span>Career launches</span></div>
    <div class="title">#{LAUNCHES[0][0]} <span style="color:var(--dim);font-weight:500">→</span> #{LAUNCHES[-1][0]}</div>
  </div>
  {legend()}
</div>
<div class="tl">{''.join(cards)}</div>
'''

write('03-timeline.html', page('Launch timeline', css, body, 3, seed=23))
