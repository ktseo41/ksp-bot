import krpc, math, warnings
warnings.filterwarnings('ignore')
c=krpc.connect(name='occ'); sc=c.space_center; v=sc.active_vessel
sun=sc.bodies['Sun']; moho=sc.bodies['Moho']; ker=sc.bodies['Kerbin']; f=sun.non_rotating_reference_frame
o=v.orbit; tpe=sc.ut+o.time_to_periapsis; R=moho.equatorial_radius+7000
print('t_pe UT %.0f'%tpe)
for dt in range(-600,601,30):
    t=tpe+dt
    mf=moho.non_rotating_reference_frame; s=o.position_at(t,mf); m=(0,0,0); kk=ker.orbit.position_at(t,f); mm=moho.orbit.position_at(t,f); k=[kk[i]-mm[i] for i in range(3)]
    d=[k[i]-s[i] for i in range(3)]; L=math.sqrt(sum(x*x for x in d)); u=[x/L for x in d]
    w=[m[i]-s[i] for i in range(3)]
    tc=sum(u[i]*w[i] for i in range(3))
    closest=math.sqrt(max(0,sum(x*x for x in w)-tc*tc))
    blocked = tc>0 and closest<R
    print('pe%+4d s: alt %5.0f km, ray-to-Kerbin clears Moho by %6.0f km %s'%(dt,(math.sqrt(sum(x*x for x in s))-moho.equatorial_radius)/1e3,(closest-R)/1e3 if tc>0 else 999, 'BLOCKED' if blocked else ''))
