"""At the apoapsis: one burn to a polar orbit (plane through the body's axis and the position) with periapsis PE."""
import math, sys
from kspbot import flight
from kspbot.core import sc
PE = float(sys.argv[1]); PLAN = len(sys.argv) > 2
s = sc(); v = s.active_vessel; o = v.orbit; b = o.body; mu = b.gravitational_parameter
t_ap = s.ut + o.time_to_apoapsis
if o.time_to_apoapsis > 300:
    flight.warp_to(t_ap - 120)
    o = v.orbit; t_ap = s.ut + o.time_to_apoapsis
nrf = b.non_rotating_reference_frame
r = o.position_at(t_ap, nrf)
def sub(a, c): return [a[i] - c[i] for i in range(3)]
def dot(a, c): return sum(a[i] * c[i] for i in range(3))
def cross(a, c): return [a[1]*c[2]-a[2]*c[1], a[2]*c[0]-a[0]*c[2], a[0]*c[1]-a[1]*c[0]]
def norm(a): n = math.sqrt(dot(a, a)); return [x / n for x in a]
# velocity at apoapsis from the node probe (burn vector of a zero node is zero; use two positions instead)
dt = 1.0
vcur = [x / (2 * dt) for x in sub(o.position_at(t_ap + dt, nrf), o.position_at(t_ap - dt, nrf))]
ra = math.sqrt(dot(r, r)); rp = b.equatorial_radius + PE
speed = math.sqrt(mu * 2 * rp / (ra * (ra + rp)))
axis = [0, 1, 0]  # kRPC body frames: y towards the north pole
n = norm(cross(r, axis))
tdir = norm(cross(n, r))
if dot(tdir, vcur) < 0: tdir = [-x for x in tdir]
vdes = [speed * x for x in tdir]
dv = sub(vdes, vcur)
print(f"apoapsis r {ra/1e3:.0f} km, v now {math.sqrt(dot(vcur,vcur)):.1f} m/s, want {speed:.1f} m/s polar; |dv| {math.sqrt(dot(dv,dv)):.1f} m/s")
ctl = v.control
for nd in ctl.nodes: nd.remove()
axes = {}
for k in ("prograde", "normal", "radial"):
    nd = ctl.add_node(t_ap, **{k: 1.0}); axes[k] = norm(nd.burn_vector(nrf)); nd.remove()
comp = {k: dot(dv, axes[k]) for k in axes}
nd = ctl.add_node(t_ap, **comp)
no = nd.orbit
print("node", {k: round(x, 2) for k, x in comp.items()}, "->", f"pe {no.periapsis_altitude/1e3:.1f} km ap {no.apoapsis_altitude/1e3:.0f} km inc {math.degrees(no.inclination):.1f}")
