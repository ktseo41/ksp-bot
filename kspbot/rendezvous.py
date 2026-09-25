"""Rendezvous with another vessel around the same body, close approach, Klaw grab, fuel transfer.

Main engine + reaction wheels only (no RCS yet): every correction turns the ship and burns.
The active vessel is the chaser; the target is passive.
"""
import math
import time

from .core import say, sc
from .flight import _norm, _dot, burn_time, execute_node, tune_node, ut, vessel, warp_to


def find_target(name):
    """The nearest other vessel called `name` around the same body."""
    v = vessel()
    here = v.position(v.orbit.body.non_rotating_reference_frame)
    best = None
    for x in sc().vessels:
        if x.name != name or x == v or x.orbit.body.name != v.orbit.body.name:
            continue
        d = math.dist(here, x.position(v.orbit.body.non_rotating_reference_frame))
        if best is None or d < best[0]:
            best = (d, x)
    if best is None:
        raise RuntimeError(f"no vessel {name!r} around {v.orbit.body.name}")
    return best[1]


def _frame(target):
    """Body-centred, non-rotating frame. Relative vectors are differences in it: the target's own frame breaks
    (NullReference) while it is unloaded, beyond ~2.3 km."""
    return target.orbit.body.non_rotating_reference_frame


def _rel(v, target, frame):
    """(relative position, relative velocity, distance, speed) of v with respect to the target."""
    p = tuple(a - b for a, b in zip(v.position(frame), target.position(frame)))
    u = tuple(a - b for a, b in zip(v.velocity(frame), target.velocity(frame)))
    return p, u, math.sqrt(_dot(p, p)), math.sqrt(_dot(u, u))


def _next_time(o, t):
    while t < ut() + 60:
        t += o.period
    return t


def match_plane(target, tol_deg=0.05):
    """Burn at the nearer of the ascending/descending nodes to match the target's orbital plane."""
    v = vessel()
    o, to = v.orbit, target.orbit
    ri = o.relative_inclination(to)
    if math.degrees(ri) < tol_deg:
        return True
    times = [_next_time(o, o.ut_at_true_anomaly(o.true_anomaly_at_an(to))),
             _next_time(o, o.ut_at_true_anomaly(o.true_anomaly_at_dn(to)))]
    t = min(times)
    spd = o.orbital_speed_at(t)
    dv = 2 * spd * math.sin(ri / 2)
    best = None
    for sign in (1, -1):
        node = v.control.add_node(t, -spd * (1 - math.cos(ri)), sign * dv, 0)
        time.sleep(0.05)
        c = node.orbit.relative_inclination(to)
        node.remove()
        if best is None or c < best[0]:
            best = (c, sign)
    node = v.control.add_node(t, -spd * (1 - math.cos(ri)), best[1] * dv, 0)

    def cost(n):
        time.sleep(0.03)
        return math.degrees(n.orbit.relative_inclination(to))
    tune_node(node, cost, steps=(("normal", 1.0), ("prograde", 0.5)))
    say(f"plane change {math.degrees(ri):.2f} deg: {node.delta_v:.1f} m/s")
    execute_node(node)
    return True


def _closest(orbit, target):
    return orbit.next_closest_approach(target.orbit).distance


def intercept(target, max_wait_orbits=12):
    """Hohmann-type transfer towards the target, timed by phase and tuned on the closest-approach distance."""
    v = vessel()
    o = v.orbit
    mu = o.body.gravitational_parameter
    r1, r2 = o.semi_major_axis, target.orbit.semi_major_axis
    if abs(r1 - r2) < 2000:
        raise RuntimeError("orbits too similar to phase: change altitude by >= 5 km first")
    t_trans = math.pi * math.sqrt(((r1 + r2) / 2) ** 3 / mu)
    n1, n2 = math.sqrt(mu / r1 ** 3), math.sqrt(mu / r2 ** 3)
    need = (math.pi - n2 * t_trans) % (2 * math.pi)  # target lead angle at departure
    from .flight import _phase_angle
    phase = _phase_angle(v, target)
    if n1 > n2:
        wait = ((phase - need) % (2 * math.pi)) / (n1 - n2)
    else:
        wait = ((need - phase) % (2 * math.pi)) / (n2 - n1)
    synodic = 2 * math.pi / abs(n1 - n2)
    if wait < 120:
        wait += synodic
    if wait > max_wait_orbits * o.period:
        say(f"phasing wait {wait:.0f}s ({wait / o.period:.1f} orbits)")
    dv = math.sqrt(mu / r1) * (math.sqrt(2 * r2 / (r1 + r2)) - 1)
    node = v.control.add_node(ut() + wait, dv, 0, 0)

    # never trade a close pass for a low periapsis (a sandbox tanker tuned itself onto a path 4.8 km under the Mun)
    pe_floor = 0.7 * min(o.periapsis_altitude, target.orbit.periapsis_altitude)

    def cost(n):
        time.sleep(0.03)
        low = max(0.0, pe_floor - n.orbit.periapsis_altitude)
        return _closest(n.orbit, target) + 100 * low
    tune_node(node, cost, steps=(("prograde", 2.0), ("ut", 20.0), ("normal", 1.0), ("radial", 1.0)))
    say(f"intercept burn {node.delta_v:.1f} m/s in {node.ut - ut():.0f}s, closest {_closest(node.orbit, target):.0f} m")
    execute_node(node)
    # fix the closest approach right away (burn errors grow over half an orbit)
    if _closest(v.orbit, target) > 500:
        node = v.control.add_node(ut() + 90, 0, 0, 0)
        tune_node(node, cost, steps=(("prograde", 1.0), ("normal", 1.0), ("radial", 1.0)))
        say(f"intercept correction {node.delta_v:.1f} m/s, closest {_closest(node.orbit, target):.0f} m")
        if node.delta_v > 0.3:
            execute_node(node)
        else:
            node.remove()
    return _closest(v.orbit, target)


def _point(v, frame, d, tol=3.0, timeout=60):
    ap = v.auto_pilot
    ap.reference_frame = frame
    ap.target_direction = _norm(d)
    ap.engaged = True
    t0 = time.time()
    while time.time() - t0 < timeout:
        f = v.direction(frame)
        if math.degrees(math.acos(max(-1, min(1, _dot(f, _norm(d)))))) < tol:
            return True
        time.sleep(0.1)
    return False


def _burn_vector(v, target, frame, want, tol=0.05, max_throttle=1.0):
    """Change the velocity relative to the target by `want` (vector): point, then burn with feedback."""
    u0 = _rel(v, target, frame)[1]
    goal = tuple(a + b for a, b in zip(u0, want))
    if not _point(v, frame, want):
        say("pointing not settled")
    while True:
        u = _rel(v, target, frame)[1]
        err = tuple(g - x for g, x in zip(goal, u))
        left = _dot(err, _norm(want))
        if left < tol:
            break
        acc = max(v.available_thrust / v.mass, 1e-3)
        v.control.throttle = max(0.01, min(max_throttle, left / (acc * 1.2)))
        time.sleep(0.02)
    v.control.throttle = 0.0


def kill_relative(target):
    """At the closest approach: burn off the relative velocity (burn centred on the closest approach)."""
    v = vessel()
    frame = _frame(target)
    tca = v.orbit.next_closest_approach(target.orbit).ut
    _p, u, _d, s = _rel(v, target, frame)
    # relative speed at the closest approach ~ current relative speed at long range is not exact: re-read near it
    bt = burn_time(v, max(s, 1.0))
    warp_to(tca - bt / 2, lead=90)
    _p, u, _d, s = _rel(v, target, frame)
    _point(v, frame, tuple(-x for x in u))
    warp_to(tca - bt / 2, lead=3)
    while ut() < tca - bt / 2:
        time.sleep(0.05)
    _p, u, d, s = _rel(v, target, frame)
    _burn_vector(v, target, frame, tuple(-x for x in u), tol=0.1)
    _p, u, d, s = _rel(v, target, frame)
    say(f"at closest approach: {d:.0f} m, relative {s:.2f} m/s")
    return d


def approach(target, dist=25.0, max_speed=6.0):
    """Close in to `dist` m and stop. Bursts: fix the velocity error when it is large, coast otherwise."""
    v = vessel()
    frame = _frame(target)
    while True:
        p, u, d, s = _rel(v, target, frame)
        speed_want = max(0.0, min(max_speed, (d - dist) / 25.0))
        if d - dist < 3 and s < 0.3:
            break
        want = tuple(-x / d * speed_want for x in p)
        err = tuple(a - b for a, b in zip(want, u))
        e = math.sqrt(_dot(err, err))
        if e > max(0.2, 0.15 * max(s, speed_want)):
            _burn_vector(v, target, frame, err, tol=0.05, max_throttle=0.5)
        else:
            time.sleep(0.5)
    v.auto_pilot.engaged = False
    p, u, d, s = _rel(v, target, frame)
    say(f"holding {d:.1f} m from {target.name}, relative {s:.2f} m/s")
    return d


def rendezvous(name, dist=25.0):
    target = find_target(name)
    sc().target_vessel = target
    match_plane(target)
    c = intercept(target)
    if c > 5000:
        say(f"closest approach {c:.0f} m, too far")
        return False
    kill_relative(target)
    approach(target, dist)
    return True


# ---------------------------------------------------------------- Klaw

def _claw(v):
    for p in v.parts.all:
        if p.name in ("GrapplingDevice", "smallClaw"):
            return p
    raise RuntimeError("no Klaw on this vessel")


def _module(part, name):
    for m in part.modules:
        if m.name == name:
            return m
    return None


def claw_state(v=None):
    v = v or vessel()
    c = _claw(v)
    out = {}
    for m in c.modules:
        out[m.name] = {"events": list(m.events), "fields": dict(m.fields)}
    return out


def arm_claw(v):
    c = _claw(v)
    for m in c.modules:
        for e in m.events:
            if e.lower().startswith("arm"):
                m.trigger_event(e)
                time.sleep(2)
                return True
    return False


def grab(name, speed=0.3):
    """Tag our parts, arm the Klaw, point at the target and drift into it at `speed` m/s."""
    v = vessel()
    target = find_target(name)
    sc().target_vessel = target
    for p in v.parts.all:
        p.tag = "chaser"
    n0 = len(v.parts.all)
    arm_claw(v)
    frame = _frame(target)
    t0 = time.time()
    while time.time() - t0 < 600:
        if len(vessel().parts.all) > n0:
            say("grabbed")
            v.auto_pilot.engaged = False
            return True
        p, u, d, s = _rel(v, target, frame)
        los = tuple(-x / d for x in p)
        want = tuple(x * speed for x in los)
        err = tuple(a - b for a, b in zip(want, u))
        e = math.sqrt(_dot(err, err))
        if e > 0.08 and _dot(_norm(err), los) > 0.3:  # a push that still roughly faces the target
            _burn_vector(v, target, frame, err, tol=0.02, max_throttle=0.1)
        elif e > 0.08 and d > 8:  # need braking or a big sideways fix: turn to it, then face the target again
            _burn_vector(v, target, frame, err, tol=0.02, max_throttle=0.1)
        _point(v, frame, los, tol=2.0, timeout=20)
        time.sleep(0.2)
    say("no grab within 10 min")
    return False


def transfer_fuel(amount_frac=1.0):
    """After a grab: move the chaser's (tag 'chaser') liquid fuel and oxidizer into the other vessel's tanks."""
    v = vessel()
    RT = sc().ResourceTransfer
    src = [p for p in v.parts.all if p.tag == "chaser" and p.resources.has_resource("LiquidFuel")]
    dst = [p for p in v.parts.all if p.tag != "chaser" and p.resources.has_resource("LiquidFuel")]
    moved = {}
    for res in ("LiquidFuel", "Oxidizer"):
        for d in dst:
            for s in src:
                room = d.resources.max(res) - d.resources.amount(res)
                have = s.resources.amount(res) * amount_frac
                if room < 0.01 or have < 0.01:
                    continue
                t = RT.start(s, d, res, min(room, have))
                while not t.complete:
                    time.sleep(0.1)
                moved[res] = moved.get(res, 0) + t.amount
    say(f"moved {moved}")
    return moved


def release():
    v = vessel()
    c = _claw(v)
    for m in c.modules:
        for e in m.events:
            if e.lower() in ("release", "decouple"):
                m.trigger_event(e)
                time.sleep(1)
                say("released")
                return True
    return False
