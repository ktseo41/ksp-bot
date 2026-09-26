import time, math
from kspbot import flight as F
v=F.vessel(); ap=v.auto_pilot
v.control.sas=False
ap.reference_frame=v.orbital_reference_frame; ap.target_direction=(0,-1,0); ap.time_to_peak=(4,4,4); ap.engaged=True
t0=time.time()
while time.time()-t0<25 and ap.error>12: time.sleep(0.1)
print('pointing err %.1f, t_pe %.0f'%(ap.error, v.orbit.time_to_periapsis), flush=True)
v.control.throttle=1.0
t0=time.time(); last=0
try:
    while time.time()-t0<420:
        F.auto_stage(v)
        o=v.orbit
        if o.eccentricity<1 and o.apoapsis_altitude<1000000: break
        if time.time()-last>10:
            last=time.time(); print('t %.0f ecc %.3f ap %.0f pe %.0f thrust %.0f stage %d err %.1f ctrl %s'%(time.time()-t0,o.eccentricity,o.apoapsis_altitude/1e3 if o.eccentricity<1 else -1,o.periapsis_altitude/1e3,v.thrust,v.control.current_stage,ap.error,v.control.state.name), flush=True)
        time.sleep(0.05)
finally:
    v.control.throttle=0.0
o=v.orbit
print('DONE ecc %.3f pe %.1f km ap %.1f km'%(o.eccentricity,o.periapsis_altitude/1e3,o.apoapsis_altitude/1e3), flush=True)
ap.engaged=False; ap.time_to_peak=(1.0,1.0,1.0)
