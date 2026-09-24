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


DETAIL = {
    1: [mono('16 km')],
    2: [mono('208 km')],
    3: [mono('2.5 km/s')],
    4: [mono('71×140 km', 'orbit')],
    5: [kb('Jeb')],
    6: [sk(1, name='Jeb')],
    7: [mono('0.4°'), kb('Bill')],
    8: [mono('15 m/s'), sk(1, True, 'Bill')],
    9: [mono('t=0 ×2', 'boom', '#ff9a2e')],
    10: [kb('Bill')],
    11: [sk(1, name='Jeb')],
    12: [mono('960 m/s'), sk(1, name='Bill')],
    13: [mono('t=0 ×4', 'boom', '#ff9a2e'), sk(4, True)],
    14: [mono('Pad', 'pad')],
    15: [mono('1.4 m/s')],
    16: [kb('Bob')],
    17: [f'<span class="kb">{icon("arrow", 20, "#8e98b6")}{planet("mun", 24)}Mun</span>'],
    18: [mono('3 sites'), kb('Jeb')],
    19: [mono('1400 m/s'), kb('Jeb')],
    20: [mono('4 biomes'), kb('Jeb')],
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
    det = (f'<span class="fb">{icon("star", 18, "#2b2000")}FIRST</span>' if first else '') + ''.join(DETAIL[n])
    cards.append(f'''<div class="lc{" first" if first else ""}" style="{style}">
<div class="th"><img src="crafts/{slug}.jpg"></div>
<div class="bd"><div class="top"><div class="num"><span>#</span>{n}</div><div class="res {cls}">{icon(ic, 26)}</div></div>
<div class="dst">{dhtml}</div><div class="det">{det}</div></div>{fb}</div>''')

body = f'''
<div class="hdr">
  <div>
    <div class="kicker">{icon('rocket', 26, '#8e98b6')}<span>Career launches</span></div>
    <div class="title">#1 <span style="color:var(--dim);font-weight:500">→</span> #20</div>
  </div>
  {legend()}
</div>
<div class="tl">{''.join(cards)}</div>
'''

write('03-timeline.html', page('Launch timeline', css, body, 3, seed=23))
