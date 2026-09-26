from common2 import *

INC = [i for i in RECORD['incidents'] if not i.get('hidden')]
headline = '실패 목록이 곧 개발 일지'
CAUSE = {'code': ('우리 코드', '#56c8ff'), 'design': ('설계', '#ff9a2e'), 'pilot': ('조종', '#b28cff'), 'game': ('게임', '#a9b3cf')}

css = '''
.causes{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:22px}
.cz{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:12px 16px;display:flex;flex-direction:column;gap:8px}
.cz .h{display:flex;align-items:baseline;justify-content:space-between}
.cz .h span{font-size:20px;font-weight:700}
.cz .h b{font-family:'JetBrains Mono',monospace;font-size:34px;line-height:1}
.cz .bar{height:8px;border-radius:4px;background:rgba(255,255,255,.06);overflow:hidden}
.cz .bar i{display:block;height:100%;border-radius:4px}
.list{margin-top:18px;display:flex;flex-direction:column;gap:9px}
.it{display:grid;grid-template-columns:52px 76px 1fr auto;gap:14px;align-items:center;background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:0 16px 0 12px;height:82px}
.it .ic{width:52px;height:52px;border-radius:14px;display:flex;align-items:center;justify-content:center}
.it .n{font-family:'JetBrains Mono',monospace;font-size:26px;font-weight:700}
.it .n span{color:var(--muted);font-size:19px}
.it .tx{font-size:25px;font-weight:600;line-height:1.25;color:#e6ebf8}
.it .tag{font-size:18px;font-weight:700;border-radius:999px;padding:5px 13px;white-space:nowrap}
'''

counts = {c: sum(1 for i in INC if i['cause'] == c) for c in CAUSE}
mx = max(counts.values())
causes = ''.join(
    f'<div class="cz"><div class="h"><span style="color:{col}">{name}</span><b style="color:{col}">{counts[c]}</b></div>'
    f'<div class="bar"><i style="width:{counts[c] / mx * 100:.0f}%;background:{col}"></i></div></div>'
    for c, (name, col) in CAUSE.items())


def ic_for(i):
    l = BY_N[i['n']]
    if 't=0' in l.get('stat', ''):
        return 'boom', '#ff9a2e'
    if l['result'] == 'crew lost':
        return 'skull', '#ff4d5e'
    if i['cause'] == 'code':
        return 'bug', '#56c8ff'
    return 'wrench', '#a9b3cf'


rows = []
for i in INC:
    assert len(i['text_ko']) <= 28, i  # plan §2: one line, <= 28 characters
    ic, col = ic_for(i)
    name, ccol = CAUSE[i['cause']]
    rows.append(f'<div class="it"><div class="ic" style="background:{col}22">{icon(ic, 30, col)}</div>'
                f'<div class="n"><span>#</span>{i["n"]}</div><div class="tx">{esc(i["text_ko"])}</div>'
                f'<div class="tag" style="color:{ccol};background:{ccol}1f;border:1px solid {ccol}55">{name}</div></div>')

body = f'''
{header('wrench', 'What went wrong', headline)}
<div class="causes">{causes}</div>
<div class="list">{''.join(rows)}</div>
'''

write('09-failures.html', page('What went wrong', css, body, 9, seed=53))
