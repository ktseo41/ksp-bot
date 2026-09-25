"""Flight routines. Each public function is one mission phase and returns when that phase is done.

Conventions: altitudes in meters above sea level, speeds in m/s, the active vessel is flown.
"""
import math
import re
import time

from .core import say, sc

G0 = 9.80665


# ---------------------------------------------------------------- small helpers

def vessel():
    return sc().active_vessel


def ut():
    return sc().ut


def _norm(v):
    m = math.sqrt(sum(x * x for x in v))
    return tuple(x / m for x in v) if m > 0 else v


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def warp_to(t, lead=0.0):
    """Time-warp until UT t - lead (no-op if already there)."""
    if t - lead > ut() + 1:
        sc().warp_to(t - lead)


def _stage_parts(v, stage):
    try:
        return v.parts.in_stage(stage)
    except Exception:
        return []


def auto_stage(v):
    """Stage when needed: no thrust at all (next engine stage), or dry engines that the next stage drops
    (spent boosters). Never while landed, never into a parachute-only stage, never dropping the last engine.
    Returns True if it staged."""
    cur = v.control.current_stage
    if cur <= 0 or v.situation.name in ("landed", "splashed", "pre_launch"):
        return False
    nxt = _stage_parts(v, cur - 1)
    if nxt and all(p.parachute is not None for p in nxt):
        return False
    all_engines = v.parts.engines
    if not any(e.part.decouple_stage < cur - 1 for e in all_engines):
        return False  # would drop the last engine (e.g. lander stage below a return pod)
    engines = [e for e in all_engines if e.active]
    if v.available_thrust > 0:
        dry = [e for e in engines if not e.has_fuel]
        if not dry or not all(e.part.decouple_stage == cur - 1 for e in dry):
            return False
    v.control.activate_next_stage()
    time.sleep(0.3)
    return True


def burn_time(v, dv):
    thrust = v.available_thrust
    isp = v.specific_impulse * G0
    if thrust <= 0 or isp <= 0:
        return 0.0
    m0 = v.mass
    m1 = m0 / math.exp(dv / isp)
    return (m0 - m1) / (thrust / isp)


def _can_plan():
    try:
        import json
        from .core import bot
        return json.loads(bot().facilities())["limits"]["maneuverNodes"]
    except Exception:
        return True


# ---------------------------------------------------------------- burns

def execute_node(node=None, tol=0.2):
    """Execute a maneuver node (default: the first one). Handles pointing, warp, staging and fine throttle."""
    v = vessel()
    node = node or v.control.nodes[0]
    dv = node.delta_v
    if v.available_thrust <= 0:  # a spent stage still attached (Mun Tanker 1: burn time read 0 s, burn started late)
        auto_stage(v)
    bt = burn_time(v, dv)
    ap = v.auto_pilot
    ap.reference_frame = node.reference_frame
    ap.target_direction = (0, 1, 0)
    ap.engaged = True
    say(f"burn {dv:.0f} m/s, ~{bt:.0f}s, in {node.ut - ut():.0f}s")
    warp_to(node.ut - bt / 2, lead=60)
    _wait_pointing(ap)
    warp_to(node.ut - bt / 2, lead=5)
    while ut() < node.ut - bt / 2:
        time.sleep(0.05)
    v.control.throttle = 1.0
    no_thrust = None
    t_end = time.time() + 3 * bt + 60
    while True:
        if time.time() > t_end:
            say("burn is taking far too long: stopping")
            break
        if _tumbling(v):  # Mun Tanker 1 spun up to 60 deg/s at a burn start and the loop never ended
            v.control.throttle = 0.0
            _damp(v, ap)
            _wait_pointing(ap, timeout=30)
            t_end += 60
            v.control.throttle = 0.1
        auto_stage(v)
        if v.available_thrust <= 0:  # out of fuel with nothing left to stage: stop instead of waiting forever
            no_thrust = no_thrust or time.time()
            if time.time() - no_thrust > 3:
                say("out of thrust")
                break
        else:
            no_thrust = None
        rem = node.remaining_burn_vector(node.reference_frame)
        left = node.remaining_delta_v
        if rem[1] < 0 or left < tol:
            break
        if left > 5:  # steer at what is still missing (long burns drift off the initial direction)
            ap.target_direction = _norm(rem)
        acc = max(v.available_thrust / v.mass, 1e-3)
        v.control.throttle = max(0.02, min(1.0, left / (acc * 1.5)))
        time.sleep(0.02)
    v.control.throttle = 0.0
    left = node.remaining_delta_v
    node.remove()
    ap.engaged = False
    say(f"burn done, residual {left:.1f} m/s")
    return left


def _tumbling(v, limit_deg=11.0):
    w = v.angular_velocity(v.orbit.body.non_rotating_reference_frame)
    return math.degrees(math.sqrt(_dot(w, w))) > limit_deg


def _damp(v, ap, timeout=30):
    """Stop a spin with SAS (the autopilot alone didn't), then hand back to the autopilot. Without SAS (a
    scientist or engineer in a Mk1 pod: Bob's return spun on in a loop) hold the current attitude, roll included."""
    ap.engaged = False
    v.control.sas = True
    time.sleep(0.3)
    held = None
    if v.control.sas:
        say("tumbling: damping with SAS")
    else:
        say("tumbling: no SAS, holding the attitude with the autopilot")
        frame = v.orbit.body.non_rotating_reference_frame
        held = (ap.reference_frame, ap.target_direction)
        ap.reference_frame = frame
        ap.target_direction = v.direction(frame)
        ap.target_roll = v.flight(frame).roll
        ap.engaged = True
    t0 = time.time()
    while time.time() - t0 < timeout:
        w = v.angular_velocity(v.orbit.body.non_rotating_reference_frame)
        if math.sqrt(_dot(w, w)) < 0.01:
            break
        time.sleep(0.2)
    v.control.sas = False
    if held:
        ap.target_roll = float("nan")
        ap.reference_frame, ap.target_direction = held
    ap.engaged = True


def _wait_pointing(ap, timeout=90):
    try:
        ap.wait(timeout)
    except Exception as e:  # keep going: a slightly off burn is better than a missed one
        say(f"pointing not settled ({e.__class__.__name__}), error {ap.error:.1f} deg")


def burn_at(t, prograde=0.0, normal=0.0, radial=0.0):
    """Burn a delta-v (orbital frame at UT t): via a maneuver node, or manually if nodes are locked
    (Tracking Station / Mission Control level 1)."""
    try:
        node = vessel().control.add_node(t, prograde, normal, radial)
    except RuntimeError as e:
        if "Maneuver node" not in str(e):
            raise
        return manual_burn(t, prograde, normal, radial)
    return execute_node(node)


def manual_burn(t, prograde=0.0, normal=0.0, radial=0.0, tol=0.3):
    """Node-less burn: fixed inertial direction from the orbital frame at t, delivered dv integrated
    from thrust/mass."""
    v = vessel()
    body = v.orbit.body
    frame = body.non_rotating_reference_frame
    r = v.orbit.position_at(t, frame)
    vel = tuple((b - a) for a, b in zip(v.orbit.position_at(t - 0.5, frame), v.orbit.position_at(t + 0.5, frame)))
    pro = _norm(vel)
    nrm = _norm(_cross(r, vel))
    rad = _cross(pro, nrm)
    vec = tuple(prograde * a + normal * b + radial * c for a, b, c in zip(pro, nrm, rad))
    dv = math.sqrt(_dot(vec, vec))
    if dv < 0.05:
        return 0.0
    bt = burn_time(v, dv)
    ap = v.auto_pilot
    ap.reference_frame = frame
    ap.target_direction = _norm(vec)
    ap.engaged = True
    say(f"manual burn {dv:.0f} m/s, ~{bt:.0f}s, in {t - ut():.0f}s")
    warp_to(t - bt / 2, lead=60)
    _wait_pointing(ap)
    warp_to(t - bt / 2, lead=5)
    while ut() < t - bt / 2:
        time.sleep(0.05)
    done, last = 0.0, ut()
    v.control.throttle = 1.0
    while done < dv - tol:
        auto_stage(v)
        now = ut()
        done += v.thrust / v.mass * (now - last)
        last = now
        acc = max(v.available_thrust / v.mass, 1e-3)
        v.control.throttle = max(0.02, min(1.0, (dv - done) / (acc * 1.5)))
        if v.available_thrust <= 0:
            break
        time.sleep(0.02)
    v.control.throttle = 0.0
    ap.engaged = False
    say(f"manual burn done ({done:.0f}/{dv:.0f} m/s)")
    return dv - done


# ---------------------------------------------------------------- launch

def ascent(target_alt=80000, heading=90.0, turn_start=250, turn_end=45000, shape=0.5, max_aoa=15.0):
    """Launch from Kerbin (or any atmospheric body) to an apoapsis of target_alt, coast out of the
    atmosphere keeping the apoapsis up. Then call circularize()."""
    v = vessel()
    body = v.orbit.body
    atmo = body.atmosphere_depth if body.has_atmosphere else 0
    fl = v.flight(body.reference_frame)
    ap = v.auto_pilot
    ap.reference_frame = v.surface_reference_frame
    ap.target_pitch_and_heading(90, heading)
    # softer gains: with AV-R8 fins at q ~40 kPa the default tuning made heading/AoA oscillate ±3° (Mun Lander 3)
    ap.time_to_peak = (5.0, 5.0, 5.0)
    ap.engaged = True
    v.control.sas = False
    v.control.throttle = 1.0
    if v.situation.name == "pre_launch":
        say("liftoff")
        v.control.activate_next_stage()
    state = {"t": time.time()}
    while True:
        auto_stage(v)
        alt = fl.mean_altitude
        frac = min(1.0, max(0.0, (alt - turn_start) / (turn_end - turn_start)))
        pitch = 90.0 * (1 - frac ** shape)
        spd = fl.speed
        if spd > 80 and alt > turn_start:
            vel_pitch = math.degrees(math.atan2(fl.vertical_speed, max(fl.horizontal_speed, 1e-3)))
            pitch = min(max(pitch, vel_pitch - max_aoa), vel_pitch + max_aoa)
        ap.target_pitch_and_heading(max(pitch, 0), heading)
        apo = v.orbit.apoapsis_altitude
        if apo >= target_alt:
            break
        if not _thrust_ok(v, state):
            return False
        time.sleep(0.05)
    # Phase 2 (low-TWR / flat ascents only): if the apoapsis is less than ~35 s ahead we would fall back
    # before leaving the atmosphere, so keep burning at a shallow positive pitch to hold it ahead.
    # Otherwise just coast (steep or high-TWR ascents).
    while v.orbit.periapsis_altitude < min(atmo, target_alt - 5000):
        auto_stage(v)
        t_apo = v.orbit.time_to_apoapsis if fl.vertical_speed > 0 else 0.0
        if t_apo > 35 or v.orbit.apoapsis_altitude > target_alt + 10000:
            break
        ap.target_pitch_and_heading(max(0.0, min(30.0, 0.8 * (35 - t_apo))), heading)
        v.control.throttle = 1.0
        if not _thrust_ok(v, state):
            return False
        time.sleep(0.05)
    v.control.throttle = 0.0
    say(f"apoapsis {v.orbit.apoapsis_altitude:.0f} m, coasting")
    # coast to the edge of the atmosphere holding prograde, topping up the apoapsis
    ap.reference_frame = v.orbital_reference_frame
    ap.target_direction = (0, 1, 0)
    while fl.mean_altitude < atmo and v.orbit.time_to_apoapsis > 10:
        if v.orbit.apoapsis_altitude < target_alt - 500:
            v.control.throttle = 0.3
            auto_stage(v)
        else:
            v.control.throttle = 0.0
        time.sleep(0.1)
    v.control.throttle = 0.0
    ap.engaged = False
    return True


def _thrust_ok(v, state):
    """False (and engines off) after 3 s without thrust and nothing left to stage."""
    if v.available_thrust > 0:
        state["t"] = time.time()
        return True
    if time.time() - state["t"] < 3:
        return True
    v.control.throttle = 0.0
    v.auto_pilot.engaged = False
    say(f"out of thrust during ascent! orbit {v.orbit.periapsis_altitude:.0f} x {v.orbit.apoapsis_altitude:.0f}")
    return False


def circularize(at="apoapsis"):
    """Circularize at the next apoapsis (or periapsis)."""
    v = vessel()
    o = v.orbit
    mu = o.body.gravitational_parameter
    if at == "apoapsis":
        r, t = o.apoapsis, ut() + o.time_to_apoapsis
    else:
        r, t = o.periapsis, ut() + o.time_to_periapsis
    v_now = math.sqrt(mu * (2 / r - 1 / o.semi_major_axis))
    v_circ = math.sqrt(mu / r)
    burn_at(t, prograde=v_circ - v_now)
    o = v.orbit
    body = o.body
    if body.has_atmosphere and o.periapsis_altitude < body.atmosphere_depth + 2000:
        _raise_pe_now(v, body.atmosphere_depth + 8000)
        o = v.orbit
    say(f"orbit {o.periapsis_altitude:.0f} x {o.apoapsis_altitude:.0f} m")


def _raise_pe_now(v, pe_alt):
    """Burn prograde right now until the periapsis is above pe_alt (a circularization that left it in the air)."""
    say(f"periapsis {v.orbit.periapsis_altitude:.0f} m is in the atmosphere: burning prograde now")
    ap = v.auto_pilot
    ap.reference_frame = v.orbital_reference_frame
    ap.target_direction = (0, 1, 0)
    ap.engaged = True
    _wait_pointing(ap, timeout=30)
    v.control.throttle = 1.0
    t0 = time.time()
    while v.orbit.periapsis_altitude < pe_alt and time.time() - t0 < 120:
        auto_stage(v)
        if v.available_thrust <= 0:
            break
        time.sleep(0.05)
    v.control.throttle = 0.0
    ap.engaged = False


def change_periapsis(new_pe_alt):
    """Burn at apoapsis to move the periapsis (e.g. deorbit to 30 km)."""
    v = vessel()
    o = v.orbit
    mu = o.body.gravitational_parameter
    ra = o.apoapsis
    rp = o.body.equatorial_radius + new_pe_alt
    v_now = math.sqrt(mu * (2 / ra - 1 / o.semi_major_axis))
    v_new = math.sqrt(mu * (2 / ra - 2 / (ra + rp)))
    burn_at(ut() + o.time_to_apoapsis, prograde=v_new - v_now)


# ---------------------------------------------------------------- transfers

def _phase_angle(v, target, t=None):
    """Angle (rad, 0..2pi) the target leads the vessel around the common parent, in the vessel's plane."""
    frame = v.orbit.body.non_rotating_reference_frame
    t = t or ut()
    pv = v.orbit.position_at(t, frame)
    pt = target.orbit.position_at(t, frame)
    vv = v.orbit.position_at(t + 1, frame)
    h = _norm(_cross(pv, tuple(b - a for a, b in zip(pv, vv))))
    ang = math.atan2(_dot(h, _cross(pv, pt)), _dot(pv, pt))
    return ang % (2 * math.pi)


def _ancestors(body):
    """Names of the bodies body orbits (parent, grandparent, ...)."""
    out = []
    while True:
        o = body.orbit
        if o is None:
            return out
        body = o.body
        out.append(body.name)


def _encounter(orbit, body):
    """(periapsis altitude at body, orbit patch) if the orbit is in / enters body's SOI, else None.
    Escapes to a parent body are followed (LKO -> Sun -> Duna); entering any other body first ends the search."""
    # only the FIRST SOI entered counts: a Minmus "encounter" after a Mun flyby sent Mun Lander 3 into Mun orbit
    o = orbit
    for _ in range(4):
        if o.body.name == body.name:
            return o.periapsis_altitude, o
        nxt = o.next_orbit
        if nxt is None or (nxt.body.name != body.name and nxt.body.name not in _ancestors(o.body)):
            return None
        o = nxt
    return None


def _patch_around(orbit, parent_name):
    """The first patch of this trajectory that orbits parent_name, following escapes only."""
    o = orbit
    for _ in range(4):
        if o.body.name == parent_name:
            return o
        nxt = o.next_orbit
        if nxt is None or nxt.body.name not in _ancestors(o.body):
            return None
        o = nxt
    return None


def _inc_short(orbit, min_inc):
    """Degrees by which the orbit's inclination (prograde or retrograde) falls short of min_inc."""
    if not min_inc:
        return 0.0
    i = math.degrees(orbit.inclination)
    return max(0.0, min_inc - min(i, 180 - i))


def _moon_penalty(patch, target):
    """Cost for a path around target that runs into one of target's moons (Duna 1 was headed through Ike;
    avoiding it inside Duna's SOI took 48 m/s)."""
    moon = patch.next_orbit
    if moon is None or moon.body.name == target.name or moon.body.name in _ancestors(target):
        return 0.0
    return 1000.0 + (moon.body.sphere_of_influence - moon.periapsis) / 1000.0


def _node_cost(node, target, pe_alt, min_inc=None):
    time.sleep(0.04)  # let KSP recompute patches
    if node.orbit.body.name == target.name:  # already inside the target SOI: just shape the periapsis
        return abs(node.orbit.periapsis_altitude - pe_alt) / 1000.0 + _inc_short(node.orbit, min_inc) \
            + _moon_penalty(node.orbit, target)
    enc = _encounter(node.orbit, target)
    if enc:
        return abs(enc[0] - pe_alt) / 1000.0 + _inc_short(enc[1], min_inc) + _moon_penalty(enc[1], target)
    o = _patch_around(node.orbit, target.orbit.body.name)
    if o is None:
        return 1e9
    ca = o.next_closest_approach(target.orbit).distance
    miss = 1000.0 + target.sphere_of_influence / 1000.0  # any encounter must beat any miss
    other = o.next_orbit
    if other is not None and other.body.name != o.body.name and other.body.name not in _ancestors(o.body):
        # another body's SOI comes first (a Mun graze on the way to Minmus): push the path out of it
        return 2 * miss + (other.body.sphere_of_influence - other.periapsis) / 1000.0 + ca / 1000.0
    return miss + ca / 1000.0


def tune_node(node, cost, steps=(("prograde", 5.0), ("normal", 5.0), ("radial", 5.0), ("ut", 30.0)),
              iters=80, min_step=0.01):
    """Coordinate-descent on node components to minimise cost(node)."""
    best = cost(node)
    step = {k: s for k, s in steps}
    for _ in range(iters):
        improved = False
        for k, _s in steps:
            for sign in (1, -1):
                old = getattr(node, k)
                setattr(node, k, old + sign * step[k])
                c = cost(node)
                if c < best:
                    best, improved = c, True
                    step[k] *= 1.5
                    break
                setattr(node, k, old)
            else:
                step[k] *= 0.5
        if not improved and all(s < min_step * (30 if k == "ut" else 1) for k, s in step.items()):
            break
    return best


def transfer_to(target_name, pe_alt):
    """From a near-circular parking orbit, plan and burn a Hohmann transfer to a moon of the current body,
    tuned so the moon periapsis is ~pe_alt. Then use capture()."""
    v = vessel()
    o = v.orbit
    if o.body.has_atmosphere and o.periapsis_altitude < o.body.atmosphere_depth:
        say(f"periapsis {o.periapsis_altitude:.0f} m is inside the atmosphere: fix the orbit first")
        return False
    target = sc().bodies[target_name]
    if target.orbit.body.name != v.orbit.body.name:
        return transfer_planet(target_name, pe_alt)
    mu = v.orbit.body.gravitational_parameter
    r1 = v.orbit.semi_major_axis
    r2 = target.orbit.semi_major_axis
    t_trans = math.pi * math.sqrt(((r1 + r2) / 2) ** 3 / mu)
    n1 = math.sqrt(mu / r1 ** 3)
    n2 = math.sqrt(mu / r2 ** 3)
    need = (math.pi - n2 * t_trans) % (2 * math.pi)
    wait = ((_phase_angle(v, target) - need) % (2 * math.pi)) / (n1 - n2)
    if wait < 120:
        wait += 2 * math.pi / (n1 - n2)
    dv = math.sqrt(mu / r1) * (math.sqrt(2 * r2 / (r1 + r2)) - 1)
    node = v.control.add_node(ut() + wait, dv, 0, 0)
    say(f"transfer to {target_name}: {dv:.0f} m/s in {wait:.0f}s, tuning")
    c = tune_node(node, lambda n: _node_cost(n, target, pe_alt),
                  steps=(("prograde", 5.0), ("ut", 60.0), ("normal", 10.0)))
    enc = _encounter(node.orbit, target)
    if not enc:
        say(f"no encounter found (cost {c:.1f}); node left for inspection")
        return False
    say(f"encounter: {target_name} periapsis {enc[0]:.0f} m, dv {node.delta_v:.0f}")
    execute_node(node)
    # long burns drift; fix the encounter right away while corrections are cheap
    enc = _encounter(v.orbit, target)
    if not enc or abs(enc[0] - pe_alt) > 3000:
        return correct_course(target_name, pe_alt)
    return True


def planet_window(target_name, origin=None, lookback_days=40):
    """UT of the Hohmann window from origin (default: the planet we orbit) to another planet: the departure t at
    which the target, at arrival t + T, sits 180 deg from the origin's position at t. Uses the real (eccentric)
    orbits; a linear phase extrapolation 200 days out once missed the Duna window by ~15 days.
    Returns the nearest window from lookback_days ago on (it may be in the past)."""
    target = sc().bodies[target_name]
    if origin is None:
        try:
            origin = vessel().orbit.body
        except Exception:  # space center: no active vessel
            origin = sc().bodies["Kerbin"]
    home = origin
    sun = home.orbit.body
    mu = sun.gravitational_parameter
    frame = sun.non_rotating_reference_frame
    h = _norm(_cross(home.position(frame), home.velocity(frame)))

    def f(t):
        """Angle (rad, -pi..pi) the target leads the home planet by, at arrival, minus 180 deg."""
        ph = home.orbit.position_at(t, frame)
        r1 = math.sqrt(_dot(ph, ph))
        T = math.pi * math.sqrt(((r1 + target.orbit.semi_major_axis) / 2) ** 3 / mu)
        for _ in range(2):
            pt = target.orbit.position_at(t + T, frame)
            r2 = math.sqrt(_dot(pt, pt))
            T = math.pi * math.sqrt(((r1 + r2) / 2) ** 3 / mu)
        ang = math.atan2(_dot(h, _cross(ph, pt)), _dot(ph, pt))
        return (ang - math.pi + math.pi) % (2 * math.pi) - math.pi, T

    now = ut()
    day = 21600.0
    syn = 1 / abs(1 / home.orbit.period - 1 / target.orbit.period)
    t, (prev, _) = now - lookback_days * day, f(now - lookback_days * day)
    while t < now + syn + 2 * day:
        t2 = t + day
        cur, _ = f(t2)
        if prev * cur <= 0 and abs(prev - cur) < 1.0:  # a real zero, not the +-pi wrap
            lo, hi = t, t2
            for _ in range(40):
                mid = (lo + hi) / 2
                if f(mid)[0] * prev <= 0:
                    hi = mid
                else:
                    lo = mid
            t_win, T = lo, f(lo)[1]
            when = f"in {(t_win - now) / day:.1f} days" if t_win >= now else f"{(now - t_win) / day:.1f} days AGO"
            say(f"{home.name}->{target_name}: window {when} (UT {t_win:.0f}), flight {T / day:.0f} days")
            return t_win
        t, prev = t2, cur
    raise RuntimeError("no window found")


def transfer_planet(target_name, pe_alt, samples=48):
    """From a circular parking orbit, at the Hohmann window, burn to another planet of the same star:
    sample the ejection point around one parking orbit, keep the closest pass, tune for periapsis pe_alt."""
    v = vessel()
    target = sc().bodies[target_name]
    home = v.orbit.body
    t_win = planet_window(target_name)
    P = v.orbit.period
    if t_win - ut() > P:
        warp_to(t_win - P / 2)
    mu_s = home.orbit.body.gravitational_parameter
    r1, r2 = home.orbit.semi_major_axis, target.orbit.semi_major_axis
    v_inf = abs(math.sqrt(mu_s / r1) * (math.sqrt(2 * r2 / (r1 + r2)) - 1))
    mu, r0 = home.gravitational_parameter, v.orbit.semi_major_axis
    dv = math.sqrt(v_inf ** 2 + 2 * mu / r0) - math.sqrt(mu / r0)
    t0 = ut() + 300
    node = v.control.add_node(t0, dv, 0, 0)
    cost = lambda n: _node_cost(n, target, pe_alt)
    best = None
    for i in range(samples):
        node.ut = t0 + i * P / samples
        c = cost(node)
        if best is None or c < best[0]:
            best = (c, node.ut)
    node.ut = best[1]
    say(f"ejection {dv:.0f} m/s (v_inf {v_inf:.0f}), best seed cost {best[0]:.0f} at +{best[1] - ut():.0f}s; tuning")
    c = tune_node(node, cost, steps=(("prograde", 10.0), ("ut", 30.0), ("normal", 10.0), ("radial", 5.0)))
    enc = _encounter(node.orbit, target)
    say(f"cost {c:.1f}, encounter {enc[0] if enc else None}, dv {node.delta_v:.0f}")
    if not enc and c > 1000.0 + target.sphere_of_influence / 1000.0 + 5e5:  # >500,000 km off: don't burn
        say("no usable ejection found; node left for inspection")
        return False
    execute_node(node)
    enc = _encounter(v.orbit, target)  # a 1 m/s error in the ejection moved the Duna pass by ~12,000 km
    if not enc or abs(enc[0] - pe_alt) > 3000:
        return correct_course(target_name, pe_alt)
    return True


def correct_course(target_name, pe_alt, min_inc=None):
    """Mid-course correction toward target periapsis pe_alt (small burn now + 120 s); min_inc: also tilt the
    arrival orbit to at least this inclination (cheap far out, e.g. for survey sites at high latitude)."""
    v = vessel()
    target = sc().bodies[target_name]
    node = v.control.add_node(ut() + 120, 0, 0, 0)
    cost = lambda n: _node_cost(n, target, pe_alt, min_inc)
    tune_node(node, cost, steps=(("prograde", 1.0), ("normal", 1.0), ("radial", 1.0)))
    if _encounter(node.orbit, target) is None and v.orbit.body.name != target.name:
        # far off course (e.g. deflected by a Mun flyby): seed from a coarse prograde x radial grid, then tune
        say("no encounter nearby; coarse search")
        best = None
        for pg in range(-150, 151, 5):
            for rd in (-40, -20, 0, 20, 40):
                node.prograde, node.normal, node.radial = pg, 0.0, rd
                c = cost(node)
                if best is None or c < best[0]:
                    best = (c, pg, rd)
        node.prograde, node.normal, node.radial = best[1], 0.0, best[2]
        tune_node(node, cost, steps=(("prograde", 2.0), ("normal", 2.0), ("radial", 2.0)))
    enc = _encounter(node.orbit, target)
    inc = math.degrees(enc[1].inclination) if enc else None
    say(f"correction {node.delta_v:.1f} m/s -> pe {enc[0] if enc else None}, inc {inc}")
    if enc is None and v.orbit.body.name != target.name:
        node.remove()
        say("no encounter reachable; not burning")
        return False
    if node.delta_v < 0.3:
        node.remove()
        return enc is not None
    execute_node(node, tol=0.05)
    return enc is not None


def warp_to_soi():
    v = vessel()
    t = v.orbit.time_to_soi_change
    if math.isnan(t) or t <= 0:
        say("no SOI change ahead")
        return False
    body = v.orbit.body.name
    warp_to(ut() + t + 5)
    while v.orbit.body.name == body:
        time.sleep(0.5)
    say(f"now in {v.orbit.body.name} SOI, pe {v.orbit.periapsis_altitude:.0f} m")
    return True


def capture(target_apo=None):
    """At the periapsis of a hyperbolic/elliptic orbit, burn retrograde into a circular orbit
    (or an orbit with apoapsis target_apo)."""
    v = vessel()
    o = v.orbit
    mu = o.body.gravitational_parameter
    rp = o.periapsis
    v_now = math.sqrt(mu * (2 / rp - 1 / o.semi_major_axis))
    ra = rp if target_apo is None else o.body.equatorial_radius + target_apo
    v_new = math.sqrt(mu * (2 / rp - 2 / (rp + ra)))
    burn_at(ut() + o.time_to_periapsis, prograde=v_new - v_now)
    o = v.orbit
    say(f"captured: {o.periapsis_altitude:.0f} x {o.apoapsis_altitude:.0f} m around {o.body.name}")


def return_to_parent(pe_alt=30000):
    """From orbit around a moon, burn so the orbit after leaving the SOI has periapsis pe_alt at the parent."""
    v = vessel()
    moon = v.orbit.body
    parent = moon.orbit.body
    mu = moon.gravitational_parameter
    r = v.orbit.semi_major_axis
    v_circ = math.sqrt(mu / r)
    v_esc = math.sqrt(2 * mu / r)
    # rough: a bit more than escape; the tuner fixes timing and magnitude
    period = v.orbit.period
    best = None
    for i in range(24):
        t = ut() + 120 + period * i / 24
        node = v.control.add_node(t, (v_esc - v_circ) * 1.15, 0, 0)
        time.sleep(0.05)
        enc = _encounter(node.orbit, parent)
        pe = enc[0] if enc else float("inf")
        node.remove()
        if best is None or pe < best[0]:
            best = (pe, t)
    node = v.control.add_node(best[1], (v_esc - v_circ) * 1.15, 0, 0)

    def cost(n):
        time.sleep(0.04)
        enc = _encounter(n.orbit, parent)
        return abs(enc[0] - pe_alt) / 1000.0 if enc else 1e6
    tune_node(node, cost, steps=(("prograde", 5.0), ("ut", 30.0)))
    enc = _encounter(node.orbit, parent)
    say(f"return burn {node.delta_v:.0f} m/s -> {parent.name} pe {enc[0] if enc else None}")
    execute_node(node)


# ---------------------------------------------------------------- landing / takeoff (airless bodies)

def _slope(body, lat, lon, d=150.0):
    """Steepest terrain slope (deg) from (lat, lon) to points d metres N/S/E/W."""
    dl = math.degrees(d / body.equatorial_radius)
    dlo = dl / max(0.2, math.cos(math.radians(lat)))
    h = body.surface_height(lat, lon)
    around = [body.surface_height(lat + dl, lon), body.surface_height(lat - dl, lon),
              body.surface_height(lat, lon + dlo), body.surface_height(lat, lon - dlo)]
    return max(math.degrees(math.atan(abs(x - h) / d)) for x in around)


def _biome(body, lat, lon):
    """Biome at lat/lon (deg). kRPC 0.6's CelestialBody.biome_at passes its arguments straight to KSP's
    BiomeMap.GetAtt, which takes RADIANS, so give it radians (verified against Vessel.biome)."""
    return body.biome_at(math.radians(lat), math.radians(lon))


def find_site(biomes, max_slope=5.0, orbits=8, step=5.0, margin=10.0):
    """Earliest UT when the ground track is over one of `biomes` with gentle terrain for +-margin seconds
    (the touchdown point; land() centres its braking burn on it)."""
    v = vessel()
    body = v.orbit.body
    track = _track(v)
    t0 = ut()
    t = t0 + 120
    while t < t0 + orbits * v.orbit.period:
        mid = track(t)
        if _biome(body, *mid) in biomes:
            pts = [track(t - margin), mid, track(t + margin)]
            if all(_biome(body, *p) in biomes for p in pts) and max(_slope(body, *p) for p in pts) < max_slope:
                say(f"site: {_biome(body, *mid)} at {mid[0]:.2f}, {mid[1]:.2f} in {t - t0:.0f} s")
                return t
        t += step
    return None


def land(safety=1.3, final_speed=1.5, max_decel=3.0, biomes=None, max_slope=5.0, orbits=8):
    """Land on an airless body from a low orbit: kill horizontal speed, then a throttled suicide burn.
    biomes: first wait for a pass over one of these biomes with gentle terrain."""
    if biomes:
        t = find_site(biomes, max_slope, orbits=orbits)
        if t is None:
            say(f"no site under {max_slope} deg in {biomes} within {orbits} orbits")
            return False
    v = vessel()
    body = v.orbit.body
    fl = v.flight(body.reference_frame)
    start = None
    if biomes:
        # the braking burn covers ~hs*burn/2 of ground: start it half a burn before the site
        burn = fl.horizontal_speed / (v.available_thrust / v.mass)
        start = t - burn / 2 - 10  # measured: touchdowns landed 1.4-1.7 km (~10 s) past the site
        warp_to(start, lead=40)
    ap = v.auto_pilot
    ap.reference_frame = v.surface_velocity_reference_frame
    ap.target_direction = (0, -1, 0)
    ap.engaged = True
    _wait_pointing(ap)
    while start and ut() < start:
        time.sleep(0.05)
    g = body.surface_gravity
    say(f"deorbit: killing horizontal speed ({fl.horizontal_speed:.0f} m/s)")
    v.control.throttle = 1.0
    while fl.horizontal_speed > 5:
        auto_stage(v)
        v.control.throttle = min(1.0, max(0.05, fl.horizontal_speed / 50))
        time.sleep(0.05)
    v.control.throttle = 0.0
    # free fall until shortly before the braking curve is reached: warp through it (engines are off)
    a_d = min(max(v.available_thrust / v.mass - g, 0.1) / safety, max_decel)
    h0 = fl.surface_altitude
    t_fall = math.sqrt(2 * a_d * h0 / (g * g + a_d * g))
    if t_fall > 60:
        say(f"free fall from {h0:.0f} m: warping {0.8 * t_fall - 20:.0f} s")
        warp_to(ut() + 0.8 * t_fall - 20)
    _powered_descent(v, fl, ap, safety, final_speed, max_decel)


def _powered_descent(v, fl, ap, safety=1.3, final_speed=1.5, max_decel=3.0):
    """Throttled suicide burn down to touchdown, holding surface retrograde (drag and chutes only help)."""
    body = v.orbit.body
    g = body.surface_gravity
    v.control.legs = True
    time.sleep(1)
    feet = -v.bounding_box(v.reference_frame)[0][1]  # CoM to the lowest point (legs) along the vessel axis
    say(f"descending (feet {feet:.1f} m below CoM)")
    while v.situation.name not in ("landed", "splashed"):
        auto_stage(v)
        h = fl.surface_altitude - feet
        a_max = v.available_thrust / v.mass
        spd = fl.speed
        if spd > 2:
            ap.reference_frame = v.surface_velocity_reference_frame
            ap.target_direction = (0, -1, 0)
        else:
            ap.reference_frame = v.surface_reference_frame
            ap.target_direction = (1, 0, 0)
        # descend along a constant-deceleration curve (capped, so high-TWR landers don't brake at the last moment)
        a_d = min(max(a_max - g, 0.1) / safety, max_decel)
        curve = math.sqrt(max(0.0, 2 * a_d * (h - 2)))
        want = -max(final_speed, curve)
        vs = fl.vertical_speed
        # throttle = hover + curve deceleration (feedforward) + proportional on speed error (+ horizontal kill).
        # Without the feedforward the speed lagged the curve by a_d/Kp: 15 m/s touchdown at Minmus TWR 28.
        ff = a_d if curve > final_speed else 0.0
        acc_cmd = g + ff + 2.0 * (want - vs) + 0.5 * fl.horizontal_speed
        v.control.throttle = max(0.0, min(1.0, acc_cmd / max(a_max, 1e-3)))
        time.sleep(0.03)
    v.control.throttle = 0.0
    ap.engaged = False
    v.control.sas = True
    say(f"landed on {body.name} at {v.flight().latitude:.2f}, {v.flight().longitude:.2f}")


def land_atmo(pe_alt=5000, burn_alt=12000):
    """Land on a body with a thin atmosphere (Duna) from a low orbit: deorbit burn to periapsis pe_alt,
    hold surface retrograde through entry, arm every parachute (they open when safe), and fly the powered
    descent below burn_alt."""
    v = vessel()
    body = v.orbit.body
    fl = v.flight(body.reference_frame)
    ap = v.auto_pilot
    if v.orbit.periapsis_altitude > pe_alt + 5000 and fl.mean_altitude > body.atmosphere_depth:
        _deorbit_now(v, pe_alt)  # a grazing periapsis (Duna 1 captured to 31 km) would skip through the air
    atmo = body.atmosphere_depth
    if fl.mean_altitude > atmo:
        o = v.orbit
        p = o.semi_major_axis * (1 - o.eccentricity ** 2)
        nu = -math.acos(max(-1.0, min(1.0, (p / (body.equatorial_radius + atmo) - 1) / o.eccentricity)))
        warp_to(o.ut_at_true_anomaly(nu), lead=30)
    ap.reference_frame = v.surface_velocity_reference_frame
    ap.target_direction = (0, -1, 0)
    ap.engaged = True
    say(f"entry: holding retrograde, {fl.speed:.0f} m/s at {fl.mean_altitude:.0f} m")
    # only chutes that get dropped later (the lander's): the capsule's own chutes are needed at home
    chutes = [c for c in v.parts.parachutes if c.part.decouple_stage >= 0] or list(v.parts.parachutes)
    armed = False
    while fl.surface_altitude > burn_alt and v.situation.name not in ("landed", "splashed"):
        if not armed and fl.mean_altitude < atmo * 0.6:
            for c in chutes:
                if not c.deployed:
                    c.arm()
            armed = True
            say(f"{len(chutes)} chutes armed at {fl.mean_altitude:.0f} m, {fl.speed:.0f} m/s")
        time.sleep(0.2)
    if not armed:
        for c in chutes:
            if not c.deployed:
                c.arm()
    say(f"powered descent from {fl.surface_altitude:.0f} m AGL at {fl.speed:.0f} m/s")
    _powered_descent(v, fl, ap)


def _deorbit_now(v, pe_alt):
    """Retrograde burn right now until the periapsis is at pe_alt."""
    ap = v.auto_pilot
    ap.reference_frame = v.orbital_reference_frame
    ap.target_direction = (0, -1, 0)
    ap.engaged = True
    _wait_pointing(ap)
    say(f"deorbit to pe {pe_alt:.0f} m")
    while v.orbit.periapsis_altitude > pe_alt:
        err = v.orbit.periapsis_altitude - pe_alt
        v.control.throttle = min(1.0, max(0.05, err / 20000))
        time.sleep(0.05)
    v.control.throttle = 0.0


def liftoff(target_alt=15000, heading=90.0):
    """Take off from an airless body into a low circular orbit (atmosphere: gravity turn above it)."""
    v = vessel()
    body = v.orbit.body
    _antennas(v, False)
    if body.has_atmosphere:
        for c in v.parts.parachutes:  # canopies left from the landing
            if c.deployed:
                c.cut()
        alt = max(target_alt, body.atmosphere_depth + 10000)
        if not ascent(alt, heading, turn_start=100, turn_end=alt * 0.5):
            return False
        v.control.legs = False
        return circularize()
    fl = v.flight(body.reference_frame)
    v.control.sas = False
    ap = v.auto_pilot
    ap.reference_frame = v.surface_reference_frame
    ap.target_pitch_and_heading(90, heading)
    ap.engaged = True
    v.control.throttle = 1.0
    t0 = time.time()
    while time.time() - t0 < 1.5 or fl.surface_altitude < 40:
        auto_stage(v)
        if time.time() - t0 > 3 and v.available_thrust <= 0:
            v.control.throttle = 0.0
            say("liftoff aborted: no thrust")
            return False
        time.sleep(0.05)
    v.control.legs = False
    # Fly low (above the terrain ahead, rising to the target as the speed nears orbital) and build horizontal speed
    # until the periapsis is safe (or the apoapsis is at the target with little left to circularize there). The old
    # profile (45/15 deg pitch) cost ~850 m/s off the Mun instead of ~600; a
    # continuous burn to a circular orbit kept climbing at 80 m/s with pitch clamped at 0 and ended on an escape path.
    R, g, mu = body.equatorial_radius, body.surface_gravity, body.gravitational_parameter
    v_circ = math.sqrt(mu / (R + target_alt))
    hd = math.radians(heading)
    last_check = 0.0
    while True:
        auto_stage(v)
        if v.available_thrust <= 0:
            say("liftoff: out of thrust")
            break
        if v.orbit.periapsis_altitude >= target_alt * 0.85:
            break
        o = v.orbit
        if o.eccentricity >= 1 or o.apoapsis_altitude > 1.5 * target_alt:
            break  # way past the target (Minmus, TWR 18: escaped within seconds); circularize() takes over
        if o.apoapsis_altitude >= target_alt:
            # cut only when little is left for the circularization (a steep climb over a crater rim also lifts
            # the apoapsis, at low speed) and the coast up to the apoapsis clears the terrain (the slow check
            # at most once a second, the cheap one every step)
            v_ap = math.sqrt(mu * (2 / o.apoapsis - 1 / o.semi_major_axis))
            if math.sqrt(mu / o.apoapsis) - v_ap < 0.08 * v_circ and time.time() - last_check > 1.0:
                last_check = time.time()
                if _coast_clear(v, margin=500):
                    break
        lat, lon = math.radians(fl.latitude), math.radians(fl.longitude)
        hs, alt = fl.horizontal_speed, fl.mean_altitude
        ahead = 0.0
        for dt in (3, 6, 10, 15, 20, 30, 45):  # highest terrain on the path over the next 45 s
            d = max(hs, 50.0) * dt / R
            la = math.asin(math.sin(lat) * math.cos(d) + math.cos(lat) * math.sin(d) * math.cos(hd))
            lo = lon + math.atan2(math.sin(hd) * math.sin(d) * math.cos(lat), math.cos(d) - math.sin(lat) * math.sin(la))
            ahead = max(ahead, body.surface_height(math.degrees(la), math.degrees(lo)))
        # climb towards the target as the speed nears orbital, but never faster than a ballistic apex at the target
        # (so the apoapsis stays there and the periapsis rises instead); the terrain ahead overrides both
        # cap the acceleration at 3 g or an orbit in ~30 s: Minmus Science 1 (TWR 18) ran from a 10 km apoapsis
        # to an escape path between two checks
        a_full = max(v.available_thrust / v.mass, 1e-3)
        v.control.throttle = min(1.0, max(3 * g, v_circ / 30) / a_full)
        a = a_full * v.control.throttle
        g_eff = g * (R / (R + alt)) ** 2 - hs ** 2 / (R + alt)
        dz = target_alt - alt
        vs_apex = math.copysign(math.sqrt(2 * g_eff * abs(dz)), dz) if g_eff > 0.05 else dz / 10
        vs_profile = (target_alt * min(1.0, v.orbit.speed / v_circ) - alt) / 8
        clear = 300 + min(500.0, hs)  # less margin while slow: climbing 800 m straight off the pad wasted ~50 m/s
        vs_terrain = (max(ahead, body.surface_height(fl.latitude, fl.longitude)) + clear - alt) / 8
        vs_want = max(-10.0, min(150.0, max(vs_terrain, min(vs_profile, vs_apex))))
        sin_p = max(-0.3, min(0.9, (g_eff + 0.4 * (vs_want - fl.vertical_speed)) / a))
        if o.apoapsis_altitude >= target_alt and vs_terrain < fl.vertical_speed:
            # the coast already reaches the target: thrust no higher than the horizon. vs_apex alone let Bob's
            # apoapsis run to 35 km for a 15 km target (g_eff falls as the horizontal speed grows)
            sin_p = min(sin_p, 0.0)
        ap.target_pitch_and_heading(math.degrees(math.asin(sin_p)), heading)
        time.sleep(0.05)
    v.control.throttle = 0.0
    ap.engaged = False
    if v.orbit.periapsis_altitude < target_alt * 0.85:
        circularize()
    say(f"orbit {v.orbit.periapsis_altitude:.0f} x {v.orbit.apoapsis_altitude:.0f} m")
    return v.orbit.periapsis_altitude > 0


def _coast_clear(v, margin=500.0, steps=24):
    """True if the unpowered path from now to the apoapsis stays `margin` m above the terrain."""
    o, body = v.orbit, v.orbit.body
    t0, tap = ut(), o.time_to_apoapsis
    for i in range(1, steps + 1):
        t = t0 + tap * i / steps
        lat, lon = _latlon_at(v, t)
        if o.radius_at(t) - body.equatorial_radius < body.surface_height(lat, lon) + margin:
            return False
    return True


# ---------------------------------------------------------------- reentry

def reentry(main_alt=4000, main_speed=250):
    """Coast to the atmosphere, drop everything except the parachute stages, hold retrograde, arm drogues
    below 20 km, stage the main chutes once below main_alt and slower than main_speed (or at 2.5 km)."""
    v = vessel()
    body = v.orbit.body
    fl = v.flight(body.reference_frame)
    atmo = body.atmosphere_depth
    o = v.orbit
    if fl.mean_altitude > atmo and o.periapsis_altitude < atmo:
        # true anomaly where r = R + atmo, on the inbound leg
        p = o.semi_major_axis * (1 - o.eccentricity ** 2)
        r = body.equatorial_radius + atmo
        nu = -math.acos(max(-1.0, min(1.0, (p / r - 1) / o.eccentricity)))
        warp_to(o.ut_at_true_anomaly(nu), lead=60)
    _antennas(v, False)
    # jettison stages until only parachutes remain in the next stage
    while v.control.current_stage > 0:
        nxt = _stage_parts(v, v.control.current_stage - 1)
        if nxt and all(p.parachute is not None for p in nxt):
            break
        v.control.activate_next_stage()
        time.sleep(1.0)
    ap = v.auto_pilot
    ap.reference_frame = v.surface_velocity_reference_frame
    ap.target_direction = (0, -1, 0)
    ap.engaged = True
    say("reentry: holding retrograde")

    def next_is(kind):
        nxt = _stage_parts(v, v.control.current_stage - 1) if v.control.current_stage > 0 else []
        chutes = [p for p in nxt if p.parachute is not None]
        if not chutes or len(chutes) != len(nxt):
            return False
        drogue = all("drogue" in p.name.lower() for p in chutes)
        return drogue if kind == "drogue" else not drogue

    while True:
        alt, spd = fl.mean_altitude, fl.speed
        if next_is("drogue") and alt < 20000:
            v.control.activate_next_stage()
            say(f"drogues armed at {alt:.0f} m, {spd:.0f} m/s")
        if next_is("main") and ((alt < main_alt and spd < main_speed) or alt < 2500):
            break
        if v.control.current_stage == 0 or v.situation.name in ("landed", "splashed"):
            break
        time.sleep(0.2)
    ap.engaged = False
    if next_is("main"):
        say(f"main chutes staged at {fl.mean_altitude:.0f} m, {fl.speed:.0f} m/s")
        v.control.activate_next_stage()
    for p in v.parts.parachutes:
        try:
            if not p.deployed:
                p.deploy()
        except Exception as e:  # a chute part already gone (seen once after staging the mains)
            say(f"chute deploy skipped: {e}")
    say("chutes deployed")
    while v.situation.name not in ("landed", "splashed"):
        time.sleep(1)
    say(f"{v.situation.name}! {v.name}")


# ---------------------------------------------------------------- science

def _antennas(v, extend):
    """Extend (before transmitting: a stowed Communotron can't) or retract (before atmosphere/liftoff) antennas."""
    ants = [a for a in v.parts.antennas if a.deployable and a.deployed != extend]
    for a in ants:
        a.deployed = extend
    if ants:
        time.sleep(6)


def do_science(transmit=False, min_single=15.0):
    """Run every available experiment that has no data yet; optionally transmit results.
    Single-use experiments (goo, materials bay) only run when the subject still has >= min_single science left,
    so a low-value situation (LKO, orbit before landing) doesn't spend them."""
    v = vessel()
    out = []
    ran = set()
    for e in v.parts.experiments:
        if e.has_data and not e.inoperable and sum(d.science_value for d in e.data) < 0.01:
            e.reset()  # worthless old data (e.g. a repeated orbit crew report) would block the new situation
            time.sleep(0.3)
        if e.inoperable or e.has_data or not e.available:
            continue
        if e.science_subject.title in ran:
            continue  # a second copy of the same subject is worth almost nothing (two Science Jrs ran in orbit)
        if not e.rerunnable:
            sub = e.science_subject
            left = sub.science_cap - sub.science
            if left < min_single:
                out.append((e.title, sub.title, f"kept (only {left:.1f} left)"))
                continue
        try:
            e.run()
            ran.add(e.science_subject.title)
        except Exception as ex:
            out.append((e.title, f"error {ex}"))
    time.sleep(1.5)
    if transmit:
        _antennas(v, True)
        # no link (Kerbin below the horizon): warp until it rises, up to ~7 h
        for _ in range(40):
            if v.comms.signal_strength > 0.05:
                break
            warp_to(ut() + 600)
            time.sleep(1)
        else:
            say("no signal to KSC; data kept on board")
    for e in v.parts.experiments:
        if e.has_data:
            val = sum(d.science_value for d in e.data)
            out.append((e.title, e.science_subject.title, round(val, 2)))
            # transmit only what can be run again (crew report, thermometer); keep goo etc. for recovery.
            ec = v.resources.amount("ElectricCharge")
            if transmit and e.rerunnable and ec > 120 and e.data and any(d.transmit_value > 0 for d in e.data):
                e.transmit()
    if not transmit:
        _collect(v)
    for row in out:
        print(row)
    return out


def _collect(v):
    """Move all data into an Experiment Storage Unit (ScienceBox on the pod's side): the lander's experiments are
    dropped before reentry, and the rerunnable ones (crew report, thermometer, barometer) are free for the next
    biome without transmitting (transmitting pays only a fraction). The "Collect All" event is inactive in flight;
    its action works. A container refuses a second copy of a subject: that copy stays in its experiment."""
    for p in v.parts.all:
        if p.name != "ScienceBox":
            continue
        for m in p.modules:
            if m.name == "ModuleScienceContainer":
                m.set_action("Collect All", True)
                time.sleep(1.0)
                for e in v.parts.experiments:
                    if e.has_data and e.rerunnable:
                        e.reset()  # a refused duplicate would block this experiment at the next biome
                say(f"data collected into {p.title}")
                return True
    return False


# ---------------------------------------------------------------- early career

def hop(science=True, heading=90.0, pitch=90.0):
    """Suborbital hop: launch at a fixed pitch, run experiments near the apex, land under chutes."""
    v = vessel()
    fl = v.flight(v.orbit.body.reference_frame)
    ap = v.auto_pilot
    ap.reference_frame = v.surface_reference_frame
    ap.target_pitch_and_heading(pitch, heading)
    ap.engaged = True
    v.control.throttle = 1.0
    if v.situation.name == "pre_launch":
        say("liftoff")
        v.control.activate_next_stage()
    top = 0.0
    while True:
        auto_stage(v)
        top = max(top, fl.mean_altitude)
        if fl.vertical_speed < 0 and fl.mean_altitude < top - 20:
            break
        time.sleep(0.1)
    say(f"apex {top:.0f} m")
    if science:
        do_science()
    ap.engaged = False
    v.control.throttle = 0.0
    reentry()
    return top


# ---------------------------------------------------------------- contract surveys

def _latlon_at(v, t):
    """Sub-vessel latitude/longitude at future UT t (accounts for the body's rotation)."""
    body = v.orbit.body
    p = v.orbit.position_at(t, body.non_rotating_reference_frame)
    p = sc().transform_position(p, body.non_rotating_reference_frame, body.reference_frame)
    lat = body.latitude_at_position(p, body.reference_frame)
    lon = body.longitude_at_position(p, body.reference_frame) - math.degrees(body.rotational_speed) * (t - ut())
    return lat, lon


def _ground_dist(body, lat1, lon1, lat2, lon2):
    return _ground_dist_r(body.equatorial_radius, lat1, lon1, lat2, lon2)


def _ground_dist_r(R, lat1, lon1, lat2, lon2):
    a, b = math.radians(lat1), math.radians(lat2)
    d = math.radians(lon2 - lon1)
    c = math.sin(a) * math.sin(b) + math.cos(a) * math.cos(b) * math.cos(d)
    return R * math.acos(max(-1.0, min(1.0, c)))


def _track(v):
    """Fast ground track for the current orbit (no burns): Kepler in Python, calibrated against kRPC.
    Returns f(t) -> (lat, lon). Replaces thousands of kRPC calls (the game ran at 1x meanwhile)."""
    body = v.orbit.body
    frame = body.non_rotating_reference_frame
    o = v.orbit
    a_, e = o.semi_major_axis, o.eccentricity
    n = 2 * math.pi / o.period
    t_pe = ut() + o.time_to_periapsis
    P = _norm(o.position_at(t_pe, frame))
    r2 = o.position_at(t_pe + o.period / 4, frame)
    Q = _norm(tuple(x - _dot(r2, P) * p for x, p in zip(r2, P)))
    w = math.degrees(body.rotational_speed)

    def inertial(t):
        M = n * (t - t_pe)
        E = M if e < 0.8 else math.pi
        for _ in range(30):
            E -= (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
        nu = 2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2))
        r = a_ * (1 - e * math.cos(E))
        x, y, z = (r * (math.cos(nu) * p + math.sin(nu) * q) for p, q in zip(P, Q))
        return math.degrees(math.asin(y / r)), math.degrees(math.atan2(z, x))

    # calibrate the longitude convention (sign, offset) on two points from kRPC's own transform
    t0 = ut() + 60
    refs = [(t, _latlon_at(v, t)) for t in (t0, t0 + o.period / 3, t0 + o.period * 0.71)]
    best = None
    for sgn in (1, -1):
        c = refs[0][1][1] - (sgn * inertial(refs[0][0])[1] - w * (refs[0][0] - t0))
        err = 0.0
        for t, (lat, lon) in refs:
            glon = sgn * inertial(t)[1] - w * (t - t0) + c
            err += abs((glon - lon + 180) % 360 - 180) + abs(inertial(t)[0] - lat)
        if best is None or err < best[0]:
            best = (err, sgn, c)
    err, sgn, c = best
    if err > 1.0:
        say(f"WARNING: fast ground track off by {err:.2f} deg on the calibration points")

    def f(t):
        lat, ilon = inertial(t)
        return lat, (sgn * ilon - w * (t - t0) + c + 180) % 360 - 180
    return f


def survey(keyword="temperature", max_dist=8000.0, horizon_orbits=40, step=5.0):
    """Orbital survey contracts: for each waypoint of a matching contract on this body, warp to the closest
    pass of the ground track and run the matching experiment there (lateral trigger range is up to 15 km)."""
    v = vessel()
    body = v.orbit.body
    wps = [w for w in sc().waypoint_manager.waypoints
           if w.body == body and w.has_contract and keyword in w.contract.title.lower()]
    if not wps:
        # contracts accepted mid-flight only register their waypoints on the next scene load
        say(f"no registered {keyword} waypoints on {body.name}: go to the space center and `ksp fly` the vessel")
        return False
    exp_name = {"temperature": "temperatureScan", "pressure": "barometerScan", "observational": "crewReport"}.get(keyword)
    say(f"{len(wps)} {keyword} waypoints on {body.name}: " + ", ".join(f"{w.name} ({w.latitude:.1f}, {w.longitude:.1f})" for w in wps))
    R = body.equatorial_radius
    todo = [(w, w.name, w.latitude, w.longitude) for w in wps]
    caps = {}  # "Take a crew report in spaceflight below 6,000 meters near Sector L-TJ"
    for w in wps:
        for prm in w.contract.parameters:
            m = re.search(r"below ([\d,]+) meters near (.+)$", prm.title)
            if m:
                caps[m.group(2).strip()] = float(m.group(1).replace(",", ""))
    while todo:
        track = _track(v)
        # earliest pass (local minimum of the ground distance) within max_dist of any remaining site
        t0 = ut()
        end = t0 + horizon_orbits * v.orbit.period
        best = None
        prev = {}
        t = t0 + (v.orbit.period / 2 + 90 if caps else 30)  # a dip is planned half an orbit ahead
        while t < end and best is None:
            lat, lon = track(t)
            for site in todo:
                d = _ground_dist_r(R, lat, lon, site[2], site[3])
                if site[1] in prev and prev[site[1]][1] < max_dist and d > prev[site[1]][1]:
                    best = (prev[site[1]][0], site, prev[site[1]][1])
                    break
                prev[site[1]] = (t, d)
            t += step
        if best is None:
            say(f"no pass within {max_dist:.0f} m of {[s_[1] for s_ in todo]} in {horizon_orbits} orbits")
            return False
        t, site, d = best
        say(f"next: {site[1]} at UT {t:.0f} (in {t - ut():.0f} s), predicted {d:.0f} m")
        cap, pe0 = caps.get(site[1]), v.orbit.periapsis_altitude
        dipped = False
        if cap and v.orbit.radius_at(t) - R > cap - 300:
            t_dip = _dip(v, t, cap, site)
            if t_dip is None:
                todo.remove(site)
                continue
            t, dipped = t_dip, True
        warp_to(t, lead=15)
        while ut() < t - 0.3:
            time.sleep(0.1)
        f = v.flight(body.reference_frame)
        d = _ground_dist_r(R, f.latitude, f.longitude, site[2], site[3])
        for e in v.parts.experiments:
            if e.name == exp_name or (exp_name is None and keyword in e.title.lower()):
                if e.has_data:
                    e.reset()
                    time.sleep(0.5)
                e.run()
                say(f"{site[1]}: ran {e.title} at {d:.0f} m lateral, alt {f.mean_altitude:.0f} m")
                break
        todo.remove(site)
        time.sleep(1)
        if dipped:  # back up to the old periapsis at the next apoapsis
            burn_at(ut() + v.orbit.time_to_apoapsis, prograde=_dv_pe(v.orbit, pe0))
            say(f"orbit {v.orbit.periapsis_altitude:.0f} x {v.orbit.apoapsis_altitude:.0f} m")
    return True


def _dv_pe(o, pe_alt):
    """Prograde dv at the apoapsis that moves the periapsis to pe_alt."""
    mu, ra = o.body.gravitational_parameter, o.apoapsis
    rp = o.body.equatorial_radius + pe_alt
    return math.sqrt(mu * (2 / ra - 2 / (ra + rp))) - math.sqrt(mu * (2 / ra - 1 / o.semi_major_axis))


def _orbit_latlon(o, t):
    """Sub-orbit latitude/longitude at UT t on orbit o (any patch, e.g. a node's), body rotation included."""
    body = o.body
    frame = body.non_rotating_reference_frame
    p = sc().transform_position(o.position_at(t, frame), frame, body.reference_frame)
    return (body.latitude_at_position(p, body.reference_frame),
            body.longitude_at_position(p, body.reference_frame) - math.degrees(body.rotational_speed) * (t - ut()))


def _clearance(o, t0, t1, n=120):
    """Lowest height above the terrain on orbit o between UT t0 and t1."""
    body = o.body
    worst = 1e9
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        lat, lon = _orbit_latlon(o, t)
        worst = min(worst, o.radius_at(t) - body.equatorial_radius - body.surface_height(lat, lon))
    return worst


def _dip(v, t_pass, cap, site):
    """Survey sites with an altitude cap ("below 5,100 meters near ..."): half an orbit before the pass, lower
    the periapsis over the site to 1000..300 m under the cap, the lowest that keeps the low arc 800 m above the
    terrain; a quarter orbit before, turn the plane so the periapsis passes right over the site (the trigger
    range for low bands is 7.75 km, and passes 6.5-12 km off didn't count). Returns the new pass time or None."""
    o, body = v.orbit, v.orbit.body
    R = body.equatorial_radius
    site_h = body.surface_height(site[2], site[3])
    n1 = v.control.add_node(t_pass - o.period / 2, 0, 0, 0)
    for pe_alt in (cap - 1000, cap - 800, cap - 600, cap - 450, cap - 300):
        pe_alt = max(pe_alt, site_h + 1200)

        def cost1(n):
            time.sleep(0.03)
            return abs(n.orbit.periapsis_altitude - pe_alt)
        tune_node(n1, cost1, steps=(("prograde", 1.0),))
        n2 = v.control.add_node(t_pass - o.period / 4, 0, 0, 0)

        def cost2(n):
            time.sleep(0.03)
            no = n.orbit
            t_pe = no.ut_at_true_anomaly(0.0)
            while t_pe < n.ut:
                t_pe += no.period
            lat, lon = _orbit_latlon(no, t_pe)
            return _ground_dist_r(R, lat, lon, site[2], site[3]) / 1000 + abs(no.periapsis_altitude - pe_alt) / 200
        tune_node(n2, cost2, steps=(("normal", 2.0), ("prograde", 0.5), ("radial", 0.5)))
        no = n2.orbit
        worst = min(_clearance(n1.orbit, n1.ut, n2.ut, 30), _clearance(no, n2.ut, n2.ut + no.period))
        if worst >= 800:
            break
        n2.remove()
        say(f"{site[1]}: a {pe_alt:.0f} m pass clears the terrain by only {worst:.0f} m")
    else:
        say(f"{site[1]}: skipped")
        n1.remove()
        return None
    t_pe = no.ut_at_true_anomaly(0.0)
    while t_pe < n2.ut:
        t_pe += no.period
    lat, lon = _orbit_latlon(no, t_pe)
    say(f"{site[1]}: dip to pe {no.periapsis_altitude:.0f} m, {_ground_dist_r(R, lat, lon, site[2], site[3]):.0f} m "
        f"off the site ({n1.delta_v:.1f} + {n2.delta_v:.1f} m/s, terrain clearance {worst:.0f} m)")
    execute_node(n1)
    execute_node(n2)
    return ut() + v.orbit.time_to_periapsis
