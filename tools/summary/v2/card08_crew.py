from collections import Counter
from common2 import *

K = RECORD['kerbals']
n_dead = len(K['deaths_that_stood'])
n_rev = K['deaths_undone_by_revert_count']
n_resc = len(K['rescued'])
headline = f'사망 {n_dead}번, 구조 {n_resc}명'
REACHED = {'success', 'in progress', 'en route', 'failed', 'partial'}  # the craft got there (reverted / crew lost did not)

css = '''
.sum{display:flex;gap:12px;margin-top:18px}
.sum div{display:flex;align-items:center;gap:8px;background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:6px 16px 6px 10px;font-size:30px;font-weight:700}
.sum div span{font-size:17px;color:var(--muted);font-weight:500;margin-left:2px}
.crew{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:18px}
.kc{background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:16px;display:flex;flex-direction:column;gap:10px;position:relative}
.kc .top{display:flex;gap:16px;align-items:center}
.kc .top img{width:104px;height:126px;object-fit:cover;border-radius:15px;border:2px solid rgba(255,255,255,.18);flex:none}
.kc .nm{font-size:32px;font-weight:700;letter-spacing:-.02em;line-height:1.05}
.kc .tr{display:flex;align-items:center;gap:7px;font-size:17px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;margin-top:5px}
.kc .now{display:inline-flex;align-items:center;gap:7px;margin-top:9px;background:rgba(86,200,255,.12);color:#bfe8ff;border-radius:999px;padding:4px 12px 4px 8px;font-size:18px;font-weight:600;white-space:nowrap}
.kc .rs{position:absolute;top:14px;right:16px;display:flex;align-items:center;gap:4px;color:#9ccc3c;font-size:20px;font-weight:700}
.kc .first{position:absolute;top:14px;right:16px;display:flex;align-items:center;gap:5px;background:var(--gold);color:#2b2000;font-weight:700;font-size:17px;border-radius:999px;padding:3px 10px 3px 7px}
.row{display:flex;align-items:center;gap:12px;min-height:44px;border-top:1px solid var(--line);padding-top:9px;flex-wrap:nowrap}
.row .ri{width:22px;display:flex;justify-content:center;color:var(--dim);flex:none}
.vs{display:flex;align-items:center;gap:4px;font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700;color:#dfe6f7}
.vs .x{color:var(--muted);font-weight:500}
.sk{display:flex;align-items:center;gap:2px;font-family:'JetBrains Mono',monospace;font-size:17px;font-weight:700;color:#ff8e98}
.sk.fd{opacity:.4}
.none{color:var(--dim);font-size:18px}
.resc{margin-top:14px;background:var(--panel);border:1px solid var(--line);border-radius:22px;padding:14px 16px 12px}
.resc .t{display:flex;align-items:center;gap:10px}
.resc .g{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin-top:10px}
.rk{display:flex;flex-direction:column;align-items:center;gap:3px}
.rk .nm{font-size:19px;font-weight:700}
.rk .tr{font-size:17px;color:var(--muted);display:flex;align-items:center;gap:5px;min-height:22px}
.rk .n{font-family:'JetBrains Mono',monospace;font-size:17px;color:#9ccc3c}
.photos{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}
.ph{height:196px;border-radius:20px;overflow:hidden;position:relative;border:1px solid var(--line)}
.ph img{width:100%;height:100%;object-fit:cover;display:block}
.ph .tg{position:absolute;left:12px;bottom:12px;}
.ph .tg.up{bottom:auto;top:12px}
.ph .tg{display:flex;align-items:center;gap:8px;background:rgba(7,11,23,.82);border-radius:999px;padding:5px 14px 5px 10px;font-size:19px;font-weight:700}
'''


def skulls(nums, faded):
    out = []
    for n, c in Counter(nums).items():
        more = f'×{c}' if c > 1 else ''
        out.append(f'<span class="sk{" fd" if faded else ""}">{icon("skull", 24, "#ff4d5e")}#{n}{more}</span>')
    return ''.join(out)


cards = []
for r in K['roster']:
    reached = Counter(dest_body(BY_N[n]['dest'])[0] for n in r['flights'] if BY_N[n]['result'] in REACHED)
    vis = ''.join(f'<span class="vs">{planet(b, 34)}<span class="x">×</span>{reached[b]}</span>'
                  for b in BODY_ORDER if reached[b])
    deaths = skulls(r['deaths_stood'], False) + skulls(r['deaths_reverted'], True)
    if r['deaths_stood']:
        corner = f'<div class="rs">{icon("respawn", 24, "#9ccc3c")}×{len(r["deaths_stood"])}</div>'
    elif r.get('first_n'):
        corner = f'<div class="first">{icon("star", 16, "#2b2000")}#{r["first_n"]}</div>'
    else:
        corner = ''
    cards.append(f'''<div class="kc">{corner}
<div class="top"><img src="../crew/{r['name'].lower()}.png"><div><div class="nm">{esc(r['name'])}</div>
<div class="tr">{icon(TRAIT_ICON[r['trait']], 20, '#8e98b6')}{r['trait']}</div>
<div class="now">{icon('live', 16, '#56c8ff')}{esc(r['status_ko'])}</div></div></div>
<div class="row"><span class="ri">{icon('rocket', 20)}</span><span class="none" style="color:var(--muted)">{len(r['flights'])}회</span>{vis}</div>
<div class="row"><span class="ri">{icon('skull', 20)}</span>{deaths or '<span class="none">—</span>'}</div>
</div>''')

FACES = ['bill', 'bob', 'val', 'jeb']
resc = ''.join(
    f'<div class="rk">{kerbal(FACES[i % 4], 62, f"r{i}")}<div class="nm">{esc(k["name"])}</div>'
    f'<div class="tr">{icon(TRAIT_ICON[k["trait"]], 17, "#8e98b6") + k["trait"] if k["trait"] else "&nbsp;"}</div>'
    f'<div class="n">#{k["n"]}</div></div>' for i, k in enumerate(K['rescued']))

boom = [l['n'] for l in LAUNCHES if 't=0' in l.get('stat', '')]
rescue_first = next(f for f in RECORD['firsts'] if f['kind'] == 'rescue')

body = f'''
{header('kerbal', 'Crew', headline)}
<div class="sum">
  <div style="color:var(--dead)">{icon('skull', 30, '#ff4d5e')}{n_dead}<span>확정</span></div>
  <div style="color:rgba(255,77,94,.55)">{icon('skull', 30, 'rgba(255,77,94,.5)')}{n_rev}<span>revert로 되돌림</span></div>
  <div style="color:#9ccc3c">{icon('respawn', 30, '#9ccc3c')}{n_dead}<span>respawn</span></div>
</div>
<div class="crew">{''.join(cards)}</div>
<div class="resc"><div class="t lbl">{icon('kerbal', 22, '#9ccc3c')} 구조된 {n_resc}명</div><div class="g">{resc}</div></div>
<div class="photos">
  <div class="ph"><img src="../crafts/photo-pad-explosion.jpg"><div class="tg">{icon('boom', 22, '#ff9a2e')}t=0 · {' · '.join(f'#{n}' for n in boom)}</div></div>
  <div class="ph"><img src="{photo('rescue-3-grab-wide')}"><div class="tg up">{icon('star', 20, '#ffcf4a')}#{rescue_first['n']} · Klaw · {esc(rescue_first['label_ko'])}</div></div>
</div>
'''

write('08-crew.html', page('Crew', css, body, 8, seed=43))
