from common2 import *

HOW = RECORD['how']
headline = T('h03')

css = '''
.cols{display:grid;grid-template-columns:370px 1fr;gap:30px;margin-top:34px;align-items:start}
.pipe{display:flex;flex-direction:column;align-items:stretch}
.st{background:var(--panel2);border:1px solid var(--line);border-radius:20px;padding:14px 18px;display:flex;align-items:center;gap:16px;min-height:90px}
.st .ic{width:58px;height:58px;border-radius:16px;display:flex;align-items:center;justify-content:center;flex:none}
.st .tx{font-size:23px;font-weight:700;line-height:1.25}
.st .tx.m{font-family:'JetBrains Mono',monospace;font-size:21px}
.dn{display:flex;justify-content:center;height:36px;align-items:center;color:var(--dim)}
.term{background:#0a0f1f;border:1px solid rgba(255,255,255,.14);border-radius:20px;overflow:hidden;box-shadow:0 18px 50px rgba(0,0,0,.45)}
.term .bar{display:flex;align-items:center;gap:8px;padding:14px 18px;background:rgba(255,255,255,.05);border-bottom:1px solid var(--line)}
.term .bar i{width:13px;height:13px;border-radius:50%;display:block}
.term .bar span{margin-left:10px;font-family:'JetBrains Mono',monospace;font-size:17px;color:var(--muted)}
.term .body{padding:14px 20px 18px;display:flex;flex-direction:column;gap:6px}
.ln{font-family:'JetBrains Mono',monospace;font-size:20px;white-space:nowrap;display:flex;gap:10px;align-items:baseline}
.ln .p{color:#35d67c}
.ln .d{color:#5c6684}
.ln .c{color:#eef2ff;font-weight:700}
.ln .a{color:#56c8ff}
.cur{display:inline-block;width:12px;height:22px;background:#35d67c;vertical-align:middle;opacity:.8}
.rules{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:34px}
.rule{display:flex;align-items:center;gap:14px;background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:15px 20px;font-size:23px;font-weight:700}
.loop{position:relative;margin-top:40px;height:300px}
.loop > svg{position:absolute;left:0;top:0}
.pk{position:absolute;transform:translate(-50%,-50%);display:flex;flex-direction:column;align-items:center;z-index:1}
.pk span{position:absolute;top:100%;margin-top:4px;font-size:20px;font-weight:700;color:var(--muted)}
.rule .ic{width:46px;height:46px;border-radius:13px;display:flex;align-items:center;justify-content:center;flex:none;background:rgba(255,255,255,.06)}
'''

ST_STYLE = [('term', '#b28cff', 'rgba(178,140,255,.16)', False), ('rocket', '#35d67c', 'rgba(53,214,124,.14)', True),
            ('bolt', '#ffcf4a', 'rgba(255,207,74,.14)', True), ('planet', '#56c8ff', 'rgba(86,200,255,.14)', False)]
stack = []
for i, (txt, (ic, col, bg, mono)) in enumerate(zip(HOW['stack'], ST_STYLE)):
    if i:
        stack.append(f'<div class="dn">{icon("arrow", 30, "#5c6684", style="transform:rotate(90deg)")}</div>')
    stack.append(f'<div class="st"><div class="ic" style="background:{bg}">{icon(ic, 34, col)}</div>'
                 f'<div class="tx{" m" if mono else ""}">{esc(txt)}</div></div>')


def cmd(c):
    head, _, rest = esc(c).partition(' ')
    rest = re.sub(r'(--\S+)', r'<span class="d">\1</span>', rest)
    return f'<div class="ln"><span class="p">$</span><span class="d">uv run ksp</span><span class="c">{head}</span><span class="a">{rest}</span></div>'


lines = ''.join(cmd(c) for c in HOW['commands'])
term = (f'<div class="term"><div class="bar"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i>'
        f'<i style="background:#28c840"></i><span>~/ksp-bot</span></div><div class="body">{lines}'
        f'<div class="ln"><span class="p">$</span><span class="cur"></span></div></div></div>')

# one mission as a loop: phases before the first 'land' fly out, 'land' .. before 'liftoff' happen at the target, the rest fly home
names = [c.split()[0] for c in HOW['commands']]
target = next(c.split()[1] for c in HOW['commands'] if c.startswith('transfer '))
i_land, i_lift = names.index('land'), names.index('liftoff')
out, at, back = names[:i_land], names[i_land:i_lift], names[i_lift:]
LW, LH = 968, 300
KX, KY, TX, TY = 100, 150, 780, 150


def qpt(p0, c, p1, t):
    return tuple((1 - t) ** 2 * p0[k] + 2 * (1 - t) * t * c[k] + t * t * p1[k] for k in (0, 1))


top = ((KX + 58, KY - 34), (440, -40), (TX - 44, TY - 26))
bot = ((TX - 44, TY + 26), (440, 330), (KX + 58, KY + 34))
lp = [f'<svg width="{LW}" height="{LH}" viewBox="0 0 {LW} {LH}" style="display:block;overflow:visible">',
      '<defs><marker id="la" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="#5c6684"/></marker></defs>']
for (p0, c, p1) in (top, bot):
    lp.append(f'<path d="M{p0[0]},{p0[1]} Q{c[0]},{c[1]} {p1[0]},{p1[1]}" fill="none" stroke="#3a4566" stroke-width="2.5" stroke-dasharray="6 7" marker-end="url(#la)"/>')
k = 0


def step(x, y, name, where):
    global k
    k += 1
    ty = {'up': y - 22, 'down': y + 38, 'right': y + 7}[where]
    tx, anc = (x + 24, 'start') if where == 'right' else (x, 'middle')
    lp.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="14" fill="#35d67c"/><text x="{x:.1f}" y="{y + 5:.1f}" text-anchor="middle" '
              f'font-size="16" font-weight="700" fill="#06240f" font-family="JetBrains Mono">{k}</text>'
              f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anc}" font-size="19" fill="#eef2ff" font-family="JetBrains Mono">{name}</text>')


for j, n in enumerate(out):
    step(*qpt(*top, (j + .5) / len(out)), n, 'up')
for j, n in enumerate(at):
    step(TX + 68, TY - 24 + 48 * j, n, 'right')
for j, n in enumerate(back):
    step(*qpt(*bot, (j + .5) / len(back)), n, 'down')
lp.append('</svg>')
loop = (f'<div class="loop"><div class="pk" style="left:{KX}px;top:{KY}px">{planet("kerbin", 116)}<span>{BODY_NAME["kerbin"]}</span></div>'
        f'<div class="pk" style="left:{TX}px;top:{TY}px">{planet(target.lower(), 70)}<span>{esc(target)}</span></div>{"".join(lp)}</div>')

R_IC = [('shield', '#ff9a2e'), ('wrench', '#b28cff'), ('coin', '#f7d75c'), ('revert', '#ff9a2e')]
rules = ''.join(f'<div class="rule"><div class="ic">{icon(ic, 28, col)}</div>{t}</div>' for t, (ic, col) in zip(map(esc, loc(HOW, 'rules')), R_IC))

body = f'''
{header('term', 'How it plays', headline)}
<div class="cols"><div class="pipe">{''.join(stack)}</div>{term}</div>
{loop}
<div class="rules">{rules}</div>
'''

write('03-how.html', page('How it plays', css, body, 3, seed=29))
