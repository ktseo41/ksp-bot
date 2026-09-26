import krpc, math, warnings, time
warnings.filterwarnings('ignore')
c=krpc.connect(name='opt'); sc=c.space_center; v=sc.active_vessel
pass
n=v.control.add_node(sc.ut+1200,0,0,0)
def cost(x, show=False):
    n.prograde,n.normal,n.radial=x; time.sleep(0.3)
    nx=n.orbit.next_orbit
    dv=math.sqrt(sum(a*a for a in x))
    if nx is None or nx.body.name!='Eve': return 1e6
    pe=nx.periapsis_altitude/1e3; inc=math.degrees(nx.inclination)
    if show: print('dv %.2f pe %.1f inc %.1f  x=%s'%(dv,pe,inc,[round(a,3) for a in x]))
    return dv + 0.02*abs(pe-120) + 0.3*inc + (200 if inc>88 else 0)
best=None
for start in ([0,0,0],[0,-0.48,0.09],[0.1,0,0],[-0.1,0,0]):
    x=list(start); c0=cost(x); st=[0.1,0.1,0.1]
    for it in range(120):
        imp=False
        for k in range(3):
            for s in (1,-1):
                y=list(x); y[k]+=s*st[k]; cy=cost(y)
                if cy<c0: x,c0,imp=y,cy,True; st[k]*=1.3; break
            else: st[k]*=0.5
        if not imp and max(st)<0.001: break
    print('start',start,'->',round(c0,2)); cost(x,True)
    if best is None or c0<best[0]: best=(c0,x)
n.prograde,n.normal,n.radial=best[1]; print('KEPT:'); cost(best[1],True)
print('FINAL node', n.prograde, n.normal, n.radial, 'dv', n.delta_v, 'pe', n.orbit.next_orbit.periapsis_altitude/1e3 if n.orbit.next_orbit else None, 'inc', math.degrees(n.orbit.next_orbit.inclination) if n.orbit.next_orbit else None)
