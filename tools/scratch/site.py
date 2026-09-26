import math, sys
from kspbot import flight as F
from kspbot.kepler import _dot, _norm
v=F.vessel(); sc=F.sc(); body=v.orbit.body
ker=sc.bodies['Kerbin']; sun=sc.bodies['Sun']; fs=sun.non_rotating_reference_frame; fm=body.non_rotating_reference_frame
track=F._track(v); t0=F.ut()
def elev(t):
    up=_norm(v.orbit.position_at(t,fm))
    k=[a-b for a,b in zip(ker.orbit.position_at(t,fs), body.orbit.position_at(t,fs))]
    return 90-math.degrees(math.acos(max(-1,min(1,_dot(up,_norm(k))))))
biomes=sys.argv[1].split(',') if len(sys.argv)>1 else ['Central Lowlands','Western Lowlands','Midlands']
seen={}
t=t0+300; n=0
while t<t0+12*v.orbit.period:
    mid=track(t); b=F._biome(body,*mid)
    seen[b]=seen.get(b,0)+1
    if b in biomes and elev(t)>20 and elev(t-150)>10:
        pts=[track(t-10),mid,track(t+10)]
        sl=max(F._slope(body,*p) for p in pts)
        if all(F._biome(body,*p) in biomes for p in pts) and sl<4:
            print('SITE %s lat %.3f lon %.3f in %.0f s slope %.1f elev %.0f/%.0f alt %.0f'%(b,mid[0],mid[1],t-t0,sl,elev(t),elev(t-150),body.surface_height(*mid)))
            n+=1
            if n>=4: break
            t+=600; continue
    t+=5
print('biomes seen (samples):', seen)
