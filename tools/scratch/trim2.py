import krpc, math, warnings, time, itertools
warnings.filterwarnings('ignore')
c=krpc.connect(name='trim'); sc=c.space_center; v=sc.active_vessel
for n in v.control.nodes: n.remove()
n=v.control.add_node(sc.ut+900,0,0,0)
def ev(p,nm,r):
    n.prograde,n.normal,n.radial=p,nm,r; time.sleep(0.04)
    nx=n.orbit.next_orbit
    if nx is None or nx.body.name!='Moho': return None
    return nx.periapsis_altitude/1e3, math.degrees(nx.inclination)
# sensitivities
for k,(a,b,cc) in {}.items():
    print(k, ev(a,b,cc), ev(-a,-b,-cc))
res=[]
g=[x*0.5 for x in range(-16,17)]
for p,nm in itertools.product(g,g):
    e=ev(p,nm,0)
    if e: res.append((math.sqrt(p*p+nm*nm),e[0],e[1],p,nm,0.0))
for r,nm in itertools.product(g,g):
    e=ev(0,nm,r)
    if e: res.append((math.sqrt(r*r+nm*nm),e[0],e[1],0.0,nm,r))
ok=[x for x in res if 18<x[1]<35]
print(len(res),'enc',len(ok),'ok')
for lim in (90,40,25,15):
    s=[x for x in ok if x[2]<lim]
    if s: print('inc<%d: best'%lim, min(s))
n.remove()
