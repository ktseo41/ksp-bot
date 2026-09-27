from common2 import *

H0 = RECORD['science_hauls']
total = sum(h['gain'] for h in H0)
# repeated lab transmissions share one row (count + sum), so the list keeps its height as visits pile up
H, _lab = [], {}
for h in H0:
    if h['how'] == '실험실 전송':
        if h['n'] not in _lab:
            _lab[h['n']] = {'n': h['n'], 'gain': 0, 'how': h['how'], 'count': 0}
            H.append(_lab[h['n']])
        _lab[h['n']]['gain'] += h['gain']; _lab[h['n']]['count'] += 1
    else:
        H.append(dict(h))
headline = f'큰 수확 {len(H0)}번, +{num(total)}'
NAMES = RECORD['research_names']
TECH = RECORD['research']
rd = CN['facilities']['R&D']

TECH_ICON = {'start': 'dot', 'basicRocketry': 'rocket', 'engineering101': 'wrench', 'generalRocketry': 'rocket',
             'survivability': 'shield', 'stability': 'fin', 'advRocketry': 'rocket', 'basicScience': 'flask',
             'heavyRocketry': 'rocket', 'generalConstruction': 'wrench', 'flightControl': 'gyro', 'fuelSystems': 'tank',
             'landing': 'leg', 'electrics': 'bolt', 'heavierRocketry': 'rocket', 'spaceExploration': 'planet',
             'advConstruction': 'wrench', 'actuators': 'wrench', 'precisionEngineering': 'sat', 'advFuelSystems': 'tank',
             'nuclearPropulsion': 'bolt', 'advFlightControl': 'gyro', 'advExploration': 'planet', 'advElectrics': 'bolt',
             'electronics': 'sat', 'specializedConstruction': 'wrench', 'scienceTech': 'flask', 'advLanding': 'leg',
             'fieldScience': 'flask', 'advScienceTech': 'flask', 'largeVolumeContainment': 'tank',
             'commandModules': 'kerbal', 'largeElectrics': 'bolt', 'aviation': 'air', 'automation': 'sat',
             'heavyLanding': 'leg', 'veryHeavyRocketry': 'rocket', 'advancedMotors': 'rocket', 'specializedElectrics': 'bolt',
             'experimentalElectrics': 'bolt', 'highPerformanceFuelSystems': 'tank', 'propulsionSystems': 'rocket',
             'unmannedTech': 'sat', 'composites': 'wrench', 'advMetalworks': 'wrench', 'ionPropulsion': 'bolt'}
HOW_COL = {'회수': '#56c8ff', '전송': '#b28cff', '실험실 전송': '#a8e8cf'}

css = '''
.hauls{margin-top:22px;display:flex;flex-direction:column;gap:6px}
.hr{display:grid;grid-template-columns:60px 230px 1fr 110px;gap:14px;align-items:center;height:48px}
.hr .th{width:60px;height:46px;border-radius:9px;overflow:hidden;border:1px solid var(--line)}
.hr .th img{width:100%;height:100%;object-fit:cover;display:block}
.hr .nm{font-size:21px;font-weight:700;white-space:nowrap;display:flex;flex-direction:column;line-height:1.1}
.hr .nm span{font-size:17px;color:var(--muted);font-weight:500;margin-top:3px}
.hr .tr{height:30px;position:relative;background:rgba(255,255,255,.04);border-radius:8px}
.hr .fill{height:100%;border-radius:8px}
.hr .how{position:absolute;top:50%;transform:translateY(-50%);font-size:17px;font-weight:700;white-space:nowrap}
.hr .v{font-family:'JetBrains Mono',monospace;font-size:24px;font-weight:700;text-align:right}
.tot{display:flex;justify-content:flex-end;gap:10px;align-items:baseline;margin-top:0;color:var(--muted);font-size:18px}
.tot b{font-family:'JetBrains Mono',monospace;font-size:28px;color:var(--sci)}
.sub{display:flex;align-items:center;gap:12px;margin-top:18px}
.sub .ln{flex:1;height:1px;background:var(--line)}
.sub b{font-size:34px;color:var(--tech);letter-spacing:0}
.aboard{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:14px}
.ab{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:12px 16px;display:flex;align-items:center;gap:12px}
.ab .t{display:flex;flex-direction:column;gap:2px}
.ab .t b{font-family:'JetBrains Mono',monospace;font-size:30px;color:var(--sci);line-height:1.1}
.ab .t span{font-size:17px;color:var(--muted);white-space:nowrap}
.badge{font-size:17px;font-weight:700;letter-spacing:.08em;color:#1a1033;background:var(--tech);border-radius:999px;padding:4px 12px}
.tg{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px 10px;margin-top:12px}
.tn{display:flex;align-items:center;gap:8px;height:48px}
.tn .hx{width:38px;height:38px;border-radius:11px;background:linear-gradient(160deg,#3b2c6e,#241a47);border:1.5px solid #7c62d6;display:flex;align-items:center;justify-content:center;flex:none}
.tn .t{font-size:17px;color:#c3cbe3;line-height:1.12;font-weight:500;letter-spacing:-.01em}
'''
if len(TECH) > 42:  # an 8th row of techs: tighter rows so the grid stays above the footer
    css += '.tg{gap:2px 10px}.tn{height:46px}.hauls{gap:3px}.hr{height:46px}'
if len(TECH) > 48:  # a 9th row: shorter haul rows and tech cells, tighter section gaps
    css += ('.tn{height:44px}.hr{height:40px}.hr .th{height:38px}.hr .nm span{margin-top:1px}.sub{margin-top:12px}'
            '.aboard{margin-top:10px}.ab{padding:8px 16px}.tg{margin-top:8px}.hauls{margin-top:16px}')

mx = max(h['gain'] for h in H)
HAUL_PHOTO = {49: 'img/eve-2-splash.jpg'}  # a milestone shot instead of the pad photo
seen = set()
rows = []
for h in H:
    l = BY_N[h['n']]
    p = (HAUL_PHOTO.get(h['n']) or photo(l['slug'])) if l['slug'] not in seen else None
    seen.add(l['slug'])
    th = f'<div class="th"><img src="{p}"></div>' if p else '<div></div>'
    col = HOW_COL.get(h['how'], '#56c8ff')
    w = max(h['gain'] / mx * 80, 3)  # leave room for the label after the longest bar
    rows.append(f'<div class="hr">{th}<div class="nm">{esc(craft_name(l["slug"]))}<span>#{h["n"]}</span></div>'
                f'<div class="tr"><div class="fill" style="width:{w:.1f}%;background:{col}"></div>'
                f'<span class="how" style="left:calc({w:.1f}% + 12px);color:{col}">{esc(h["how"])}{" ×" + str(h["count"]) if h.get("count", 1) > 1 else ""}</span></div>'
                f'<div class="v" style="color:{col}">+{num(h["gain"])}</div></div>')

ab = []
for a in RECORD['science_aboard']:
    m = next((x for x in RECORD['live_missions'] if x['slug'] == a['slug']), {})
    who = ', '.join(m.get('crew', []))
    if 'sci' in a:
        v, unit = f'{"~" if a.get("approx") else ""}{num(a["sci"])}', 'sci 탑재'
    else:
        v, unit = esc(a['data']), 'lab data'
    ab.append(f'<div class="ab">{planet(m.get("body", "kerbin"), 44)}<div class="t"><span>{esc(craft_name(a["slug"]))} · {who}</span>'
              f'<b>{v}</b><span>{unit}</span></div></div>')

tech = ''.join(f'<div class="tn"><div class="hx">{icon(TECH_ICON.get(t, "gyro"), 22, "#d9ccff")}</div>'
               f'<div class="t">{esc(NAMES.get(t, t))}</div></div>' for t in TECH)

body = f'''
{header('flask', 'Science', headline, color='var(--sci)')}
<div class="hauls">{''.join(rows)}</div>
<div class="tot">합계 <b>+{num(total)}</b></div>
<div class="sub lbl">{icon('flask', 22, '#56c8ff')} 싣고 오는 중<span class="ln"></span></div>
<div class="aboard">{''.join(ab)}</div>
<div class="sub lbl">{icon('gyro', 24, '#b28cff')}<b>{len(TECH)}</b> Tech<span class="ln"></span><span class="badge">R&amp;D Lv.{rd}</span></div>
<div class="tg">{tech}</div>
'''

write('07-science.html', page('Science', css, body, 7, seed=31))
