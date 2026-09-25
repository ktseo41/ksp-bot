"""Rendezvous with another vessel around the same body, close approach, Klaw grab, fuel transfer.

Main engine + reaction wheels only (no RCS yet): every correction turns the ship and burns.
The active vessel is the chaser; the target is passive.
"""
import math
import time

from .core import bot, say, sc
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

    sma0 = o.semi_major_axis

    def cost(n):  # keep the orbit's energy: Salvage 2's 90 deg plane change tuned itself onto an escape path
        time.sleep(0.03)
        return math.degrees(n.orbit.relative_inclination(to)) + abs(n.orbit.semi_major_axis - sma0) / 1000
    tune_node(node, cost, steps=(("normal", 1.0), ("prograde", 0.5)))
    say(f"plane change {math.degrees(ri):.2f} deg: {node.delta_v:.1f} m/s")
    execute_node(node)
    return True


def _closest(orbit, target):
    return orbit.next_closest_approach(target.orbit).distance


def intercept(target, max_wait_orbits=12, aim=25.0):
    """Hohmann-type transfer towards the target, timed by phase and tuned for a pass `aim` m from it (not 0: the
    stop at the closest approach should leave room to turn; Rescue 1 stopped at 9 m and hit the target turning)."""
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
        return abs(_closest(n.orbit, target) - aim) + 100 * low
    tune_node(node, cost, steps=(("prograde", 2.0), ("ut", 20.0), ("normal", 1.0), ("radial", 1.0)))
    say(f"intercept burn {node.delta_v:.1f} m/s in {node.ut - ut():.0f}s, closest {_closest(node.orbit, target):.0f} m")
    execute_node(node)
    # fix the closest approach right away (burn errors grow over half an orbit)
    if abs(_closest(v.orbit, target) - aim) > 500:
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
    c = intercept(target, aim=dist)
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


def _face_axis(target, face, frame):
    """Unit vector (in frame) of the face of the target's root part the Klaw should hit: an axis ("-z") or a
    normal "x,y,z" in the part frame. Map a part's faces with sc().raycast_distance first: the Thud's -z
    mounting side is a rounded ridge (only +-0.1 m passes the 43 deg check), its +z side a flat plane 13 deg
    off the axis, normal (0, 0.24, 1)."""
    if "," in face:
        d = tuple(float(x) for x in face.split(","))
    else:
        k = "xyz".index(face[-1])
        d = [0.0, 0.0, 0.0]
        d[k] = -1.0 if face.startswith("-") else 1.0
    return _norm(sc().transform_direction(tuple(d), target.parts.root.reference_frame, frame))


def _station(v, target, frame, a, dist, tol=2.0, timeout=900):
    """Move to the point dist m out along the target's axis a and stop there, going around the target
    (via a point off to the side) when starting on the far side."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        p, u, d, s = _rel(v, target, frame)
        along = _dot(p, a)
        lat = tuple(x - along * y for x, y in zip(p, a))
        ll = math.sqrt(_dot(lat, lat))
        if along < 0.3 * dist:  # behind or beside the face: first a point to the side, clear of the target
            side = _norm(lat) if ll > 1 else _norm(_cross_any(a))
            goal = tuple(dist * x + 0.5 * dist * y for x, y in zip(side, a))
        else:
            goal = tuple(dist * x for x in a)
        off = tuple(g - x for g, x in zip(goal, p))
        do = math.sqrt(_dot(off, off))
        if do < tol and s < 0.05:
            return True
        want = tuple(x / max(do, 1e-6) * min(1.0, do / 20.0) for x in off)
        err = tuple(w - x for w, x in zip(want, u))
        if math.sqrt(_dot(err, err)) > max(0.03, 0.15 * math.sqrt(_dot(want, want))):
            _burn_vector(v, target, frame, err, tol=0.01, max_throttle=0.3)
        else:
            time.sleep(0.5)
    return False


def _cross_any(a):
    from .flight import _cross
    c = _cross(a, (0.0, 0.0, 1.0))
    return c if _dot(c, c) > 0.01 else _cross(a, (1.0, 0.0, 0.0))


def _air_below(v, margin=2000.0):
    """Periapsis in (or near) the atmosphere: stop manoeuvring and fix the orbit first."""
    b = v.orbit.body
    pe = v.orbit.periapsis_altitude
    if b.has_atmosphere and pe < b.atmosphere_depth + margin:
        say(f"periapsis {pe / 1000:.1f} km, near {b.name}'s air: stopping (raise it at the apoapsis first)")
        return True
    return False


def grab(name, speed=0.15, face=None, max_contacts=3):
    """Tag our parts, arm the Klaw, point at the target and drift into it at `speed` m/s.
    The Klaw only catches when a 0.1 m ray from its centre hits the target within 43 deg of square
    (ModuleGrappleNode.CheckGrappleContact): on a small part (a Thud) aim at a flat face, e.g. face="-z".
    Stops after max_contacts bounces: repeating the same approach taught nothing new (Salvage 1/2, Rescue 2/3)."""
    v = vessel()
    target = find_target(name)
    sc().target_vessel = target
    for p in v.parts.all:
        p.tag = "chaser"
    n0 = len(v.parts.all)
    frame = _frame(target)
    # Turning swings the Klaw around the centre of mass: only turn freely while the target is outside that
    # circle (+ margin). Rescue 1 (12 m stack) started at 8.6 m, swung at 4-16 deg/s for 90 s and hit the target.
    arm = math.sqrt(_dot(_claw(v).position(v.reference_frame), _claw(v).position(v.reference_frame)))
    safe = arm + 8.0
    d = _rel(v, target, frame)[2]
    if d < safe:
        say(f"too close to turn: {d:.1f} m < {safe:.1f} m (Klaw {arm:.1f} m from the centre of mass); back off first")
        return False
    if face:
        a = _face_axis(target, face, frame)
        say(f"moving onto the target's {face} axis")
        if not _station(v, target, frame, a, max(25.0, safe + 10)):
            say("could not reach the approach point")
            return False
    arm_claw(v)
    if face and any(p.rcs is not None for p in v.parts.all):
        return _rcs_grab(v, target, frame, face, speed, n0, max_contacts=max_contacts)
    t0 = tlog = time.time()
    contacts, bouncing = 0, False
    while time.time() - t0 < 1800:
        if len(vessel().parts.all) > n0:
            say(f"grabbed after {contacts} bounce(s), {time.time() - t0:.0f} s")
            vessel().auto_pilot.engaged = False  # the grab merged us into a new vessel object
            return True
        if _air_below(v):
            return False
        p, u, d, s = _rel(v, target, frame)
        closing = -_dot(p, u) / d
        if d < arm + 3 and closing < -0.05 and not bouncing:  # moving apart right after a touch
            contacts, bouncing = contacts + 1, True
            say(f"contact {contacts}: bounced at {d:.1f} m, {closing:.2f} m/s, {time.time() - t0:.0f} s in")
            if contacts >= max_contacts:
                say(f"{contacts} bounces: stopping to diagnose (ksp log)")
                v.control.throttle = 0.0
                return False
        elif d > arm + 5:
            bouncing = False
        w = target.angular_velocity(frame)
        if math.degrees(math.sqrt(_dot(w, w))) > 3 and d > safe:
            # a spinning target can't be grabbed (Module 761V7 turned at 160 deg/s after our bumps); stock KSP
            # zeroes the spin of vessels going on rails, so a moment of rails warp stops it
            say(f"target spinning {math.degrees(math.sqrt(_dot(w, w))):.0f} deg/s: rails warp to stop it")
            sc().rails_warp_factor = 2
            time.sleep(3)
            sc().rails_warp_factor = 0
            time.sleep(3)
            continue
        if face:  # come in along the face axis, steering the sideways offset back onto it
            a = _face_axis(target, face, frame)
            along = _dot(p, a)
            lat = tuple(x - along * y for x, y in zip(p, a))
            ll = math.sqrt(_dot(lat, lat))
            if along < safe and d > safe:  # not in front of the face (it turned after a bump): go round again
                say(f"not in front of the {face} face (along {along:.1f} m, off {ll:.1f} m): repositioning")
                _station(v, target, frame, a, max(25.0, safe + 10))
                continue
            los = tuple(-x for x in a)
            # inside the turning circle nothing can be corrected: hold outside it until the offset is small
            go = speed if (ll < 0.25 or along > safe + 6) else 0.0
            want = tuple(go * x - 0.05 * y for x, y in zip(los, lat))
        else:
            los = tuple(-x / d for x in p)
            want = tuple(x * speed for x in los)
        err = tuple(a_ - b for a_, b in zip(want, u))
        e = math.sqrt(_dot(err, err))
        if time.time() - tlog > 20:
            say(f"grab: {d:.1f} m, closing {closing:.2f} m/s, velocity error {e:.3f} m/s, {time.time() - t0:.0f} s")
            tlog = time.time()
        # Outside the turning circle the velocity is trimmed to 0.03 m/s (Salvage 1 with 0.08 m/s drifted metres
        # past a Thud for 10 min); inside it only small pushes near the current facing are allowed.
        if d > safe and e > 0.03:
            _burn_vector(v, target, frame, err, tol=0.01, max_throttle=0.05)
        elif e > 0.05 and _dot(_norm(err), los) > 0.95:
            _burn_vector(v, target, frame, err, tol=0.01, max_throttle=0.05)
        _point(v, frame, los, tol=0.5 if d < safe else 2.0, timeout=20)
        time.sleep(0.2)
    say("no grab within 30 min")
    return False


def _rcs_axes(v, target, frame, pulse=0.6):
    """Signs mapping vessel-frame x/y/z to control.right/forward/up, from a short test pulse on each."""
    c = v.control
    signs = []
    for name in ("right", "forward", "up"):
        u0 = sc().transform_direction(_rel(v, target, frame)[1], frame, v.reference_frame)
        setattr(c, name, 1.0)
        time.sleep(pulse)
        setattr(c, name, 0.0)
        time.sleep(0.3)
        u1 = sc().transform_direction(_rel(v, target, frame)[1], frame, v.reference_frame)
        du = [b - a for a, b in zip(u0, u1)]
        k = max(range(3), key=lambda i: abs(du[i]))
        signs.append((k, 1.0 if du[k] > 0 else -1.0))
        say(f"rcs {name}: vessel axis {'xyz'[k]} {'+' if du[k] > 0 else '-'} ({abs(du[k]):.3f} m/s)")
    return signs  # per control: (vessel axis index, sign)


def _rcs_grab(v, target, frame, face, speed, n0, timeout=1800, max_contacts=3):
    """Final approach with RCS: the Klaw stays square to the face (autopilot), RCS alone steers the sideways
    offset to 0 and holds the closing speed, and keeps pushing through the contact."""
    c = v.control
    c.sas = False
    c.rcs = True
    ap = v.auto_pilot
    ap.reference_frame = frame
    ap.engaged = True
    ap.target_direction = tuple(-x for x in _face_axis(target, face, frame))
    ap.wait()
    for p in v.parts.all:  # RCS for translation only: attitude is the reaction wheels' job (Salvage 2 spent
        if p.rcs is not None:  # its monopropellant holding attitude)
            p.rcs.pitch_enabled = p.rcs.yaw_enabled = p.rcs.roll_enabled = False
    signs = _rcs_axes(v, target, frame)
    reach = math.sqrt(_dot(_claw(v).position(v.reference_frame), _claw(v).position(v.reference_frame))) + 1.5
    t0 = tlog = time.time()
    contacts, bouncing = 0, False
    try:
        while time.time() - t0 < timeout:
            if len(vessel().parts.all) > n0:
                say(f"grabbed after {contacts} bounce(s), {time.time() - t0:.0f} s")
                return True
            if _air_below(v):
                return False
            a = _face_axis(target, face, frame)
            ap.target_direction = tuple(-x for x in a)
            p, u, d, s = _rel(v, target, frame)
            w = target.angular_velocity(frame)
            spin = math.degrees(math.sqrt(_dot(w, w)))
            along = _dot(p, a)
            lat = tuple(x - along * y for x, y in zip(p, a))
            ll = math.sqrt(_dot(lat, lat))
            closing = -_dot(p, u) / d
            if d < reach + 1.5 and closing < -0.05 and not bouncing:  # moving apart right after a touch
                contacts, bouncing = contacts + 1, True
                say(f"contact {contacts}: bounced at {d:.1f} m, {closing:.2f} m/s, off-axis {ll:.2f} m, "
                    f"{time.time() - t0:.0f} s in")
                if contacts >= max_contacts:
                    say(f"{contacts} bounces: stopping to diagnose (ksp log)")
                    return False
            elif d > reach + 4:
                bouncing = False
            if spin > 3 and d > 6:
                say(f"target spinning {spin:.0f} deg/s: rails warp to stop it")
                for x in ("right", "forward", "up"):
                    setattr(c, x, 0.0)
                sc().rails_warp_factor = 2
                time.sleep(3)
                sc().rails_warp_factor = 0
                time.sleep(3)
                continue
            if spin > 3 or along < 3.0 or (ll > 3.0 and along < 12.0):
                # spinning up close, or not in front of the face: translate (no turning) to a point in front of
                # it, via a point off to the side when behind (a straight line from behind would cross the target)
                side = _norm(lat) if ll > 1 else _norm(_cross_any(a))
                goal = tuple(20 * x for x in a) if along > 3.0 else tuple(20 * x + 10 * y for x, y in zip(side, a))
                off = tuple(g - x for g, x in zip(goal, p))
                do = math.sqrt(_dot(off, off))
                want = tuple(x / max(do, 1e-6) * min(0.5, do / 20.0) for x in off)
            else:
                closing = speed if ll < 0.5 or along > 8 else 0.0  # line up before the last metres
                want = tuple(-closing * x - min(0.15, 0.1 * ll) * y / max(ll, 1e-6) for x, y in zip(a, lat))
            err = sc().transform_direction(tuple(w_ - x for w_, x in zip(want, u)), frame, v.reference_frame)
            for (k, sign), name in zip(signs, ("right", "forward", "up")):
                cmd = err[k] * sign * 8.0
                setattr(c, name, max(-1.0, min(1.0, cmd if abs(err[k]) > 0.004 else 0.0)))
            if d < reach + 1.5:  # near contact: what does the Klaw's own capture ray see?
                try:
                    say(f"klaw {d:.2f} m: {bot().grapple_debug(target.name)}", screen=False)
                except Exception as ex:
                    say(f"grapple debug failed: {ex}")
            if time.time() - tlog > 15:
                say(f"rcs grab: {d:.1f} m, along {along:.1f}, off-axis {ll:.2f} m, closing {-_dot(p, u) / d:.2f} m/s, "
                    f"target spin {spin:.1f}, mono {v.resources.amount('MonoPropellant'):.1f}")
                tlog = time.time()
            time.sleep(0.1)
    finally:
        for x in ("right", "forward", "up"):
            setattr(c, x, 0.0)
        c.rcs = False
        try:
            vessel().auto_pilot.engaged = False
        except Exception:
            pass
    say(f"no grab within {timeout / 60:.0f} min")
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
    balance_fuel(dst)
    return moved


def transfer_crew():
    """After a grab: move the grabbed vessel's crew into free seats on ours (tag 'chaser'), like the stock
    crew-transfer dialog. A rescue contract's 'Save X' completes on the grab itself (onPartCouple)."""
    v = vessel()
    seats = [p for p in v.parts.all if p.tag == "chaser" and p.crew_capacity > len(p.crew)]
    moved = []
    for p in v.parts.all:
        if p.tag == "chaser":
            continue
        for c in list(p.crew):
            dst = next((s for s in seats if s.crew_capacity > len(s.crew)), None)
            if dst is None:
                say(f"no free seat for {c.name}")
                break
            sc().transfer_crew(c, dst)
            time.sleep(2)  # KSP respawns the crew a frame later
            moved.append(c.name)
    say(f"moved {moved}; aboard: " + ", ".join(f"{p.title}: {[c.name for c in p.crew]}"
                                             for p in vessel().parts.all if p.tag == "chaser" and p.crew_capacity))
    return bool(moved)


def balance_fuel(parts=None):
    """Even out the fill level of the tanks: filling Bob's radial tanks one after another (180/30/3) put the
    centre of mass 0.36 m off the thrust axis, and his return burn spun the lander up."""
    v = vessel()
    RT = sc().ResourceTransfer
    parts = parts or [p for p in v.parts.all if p.resources.has_resource("LiquidFuel")]
    for res in ("LiquidFuel", "Oxidizer"):
        frac = sum(p.resources.amount(res) for p in parts) / max(sum(p.resources.max(res) for p in parts), 1e-9)
        over = [[p, p.resources.amount(res) - frac * p.resources.max(res)] for p in parts]
        src = [x for x in over if x[1] > 0.05]
        for d, need in [(p, -e) for p, e in over if e < -0.05]:
            for x in src:
                amt = min(need, x[1])
                if amt < 0.05:
                    continue
                t = RT.start(x[0], d, res, amt)
                while not t.complete:
                    time.sleep(0.1)
                x[1] -= t.amount
                need -= t.amount
    say("tanks " + ", ".join(f"{p.resources.amount('LiquidFuel'):.0f}/{p.resources.max('LiquidFuel'):.0f}" for p in parts))


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
