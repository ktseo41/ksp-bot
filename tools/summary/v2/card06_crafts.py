from common2 import *

CR = RECORD['crafts']
FIRSTS = {f['n']: f for f in RECORD['firsts']}
n_designs = len({l['slug'] for l in LAUNCHES})
headline = T('h06')

css = '''
.row{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-top:24px;align-items:end;position:relative}
.ph{border-radius:16px;overflow:hidden;border:1px solid var(--line);position:relative;background:var(--panel)}
.ph img{width:100%;height:100%;object-fit:cover;object-position:center bottom;display:block}
.ph .n{position:absolute;left:8px;top:8px;background:rgba(7,11,23,.82);border-radius:9px;padding:3px 9px;font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700}
.ground{height:3px;border-radius:2px;margin-top:10px;background:linear-gradient(90deg,rgba(255,255,255,.08),rgba(168,217,122,.7))}
.info{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-top:16px;align-items:start}
.col{display:flex;flex-direction:column;gap:8px}
.col .nm{font-size:22px;font-weight:700;line-height:1.15;min-height:52px;letter-spacing:-.01em}
.col .st{display:flex;flex-direction:column;gap:4px;min-height:92px}
.col .st span{font-family:'JetBrains Mono',monospace;font-size:19px;font-weight:700;color:#dfe6f7;display:flex;align-items:center;gap:6px;white-space:nowrap}
.col .st span i{font-style:normal;color:var(--muted);font-weight:500;font-size:17px}
.col .st .none{color:var(--dim);font-weight:500}
.col .rs{font-size:18px;color:#c9d1e8;line-height:1.3;border-top:1px solid var(--line);padding-top:10px;display:flex;gap:6px;align-items:flex-start}
.col .rs .ic{margin-top:2px}
.arrow{display:flex;align-items:center;gap:12px;margin-top:22px;color:var(--muted);font-size:18px;letter-spacing:.12em;text-transform:uppercase}
.arrow .ln{flex:1;height:2px;background:linear-gradient(90deg,rgba(255,255,255,.06),rgba(255,255,255,.3))}
'''

MAXH, MINF = 800, .55
if lang() == 'en':  # English first-labels wrap to 4-5 lines: shorter photos, slightly smaller text
    MAXH = 760
    css += '.col .rs{font-size:17px;line-height:1.25}'
phs, cols = [], []
for i, c in enumerate(CR):
    h = MAXH * (MINF + (1 - MINF) * i / (len(CR) - 1))  # grows left to right (presentation only)
    p = photo(c['slug'])
    img = f'<img src="{p}">' if p else ''
    phs.append(f'<div class="ph" style="height:{h:.0f}px">{img}<span class="n">#{c["first_n"]}</span></div>')
    st = []
    if 'parts' in c:
        st.append(f'<span>{c["parts"]} <i>parts</i></span>')
    if 'mass_t' in c:
        st.append(f'<span>{c["mass_t"]:g} <i>t</i></span>')
    if 'funds' in c:
        st.append(f'<span>{icon("coin", 18, "#f7d75c")}{c["funds"] / 1000:.1f}k</span>')
    st = ''.join(st)
    f = FIRSTS.get(c['first_n'])
    if f:
        rs = f'{icon("star", 18, "#ffcf4a", "ic")}<span>{esc(loc(f, "label"))}</span>'
    else:
        rs = f'{icon("check", 18, "#35d67c", "ic")}<span class="mono">{esc(BY_N[c["first_n"]]["stat"])}</span>'
    cols.append(f'<div class="col"><div class="nm">{esc(c["name"])}</div><div class="st">{st}</div><div class="rs">{rs}</div></div>')

body = f'''
{header('rocket', f'Crafts · {n_designs} designs flown', headline)}
<div class="row">{''.join(phs)}</div>
<div class="ground"></div>
<div class="info">{''.join(cols)}</div>
'''

write('06-crafts.html', page('Craft evolution', css, body, 6, seed=11))
