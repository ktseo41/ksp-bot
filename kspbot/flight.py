"""Flight routines. Each public function is one mission phase and returns when that phase is done.

Conventions: altitudes in meters above sea level, speeds in m/s, the active vessel is flown.
"""
import math
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
    (spent boosters). Never while landed, never into a parachute-only stage. Returns True if it staged."""
    cur = v.control.current_stage
    if cur <= 0 or v.situation.name in ("landed", "splashed", "pre_launch"):
        return False
    nxt = _stage_parts(v, cur - 1)
    if nxt and all(p.parachute is not None for p in nxt):
        return False
    engines = [e for e in v.parts.engines if e.active]
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
    while True:
        auto_stage(v)
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
    say(f"orbit {o.periapsis_altitude:.0f} x {o.apoapsis_altitude:.0f} m")


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


def _encounter(orbit, body):
    """(periapsis altitude at body, orbit patch) if the orbit is in / enters body's SOI, else None."""
    if orbit.body.name == body.name:
        return orbit.periapsis_altitude, orbit
    # only the FIRST SOI entered counts: a Minmus "encounter" after a Mun flyby sent Mun Lander 3 into Mun orbit
    o = orbit.next_orbit
    if o is not None and o.body.name == body.name:
        return o.periapsis_altitude, o
    return None


def _node_cost(node, target, pe_alt):
    time.sleep(0.04)  # let KSP recompute patches
    if node.orbit.body.name == target.name:  # already inside the target SOI: just shape the periapsis
        return abs(node.orbit.periapsis_altitude - pe_alt) / 1000.0
    enc = _encounter(node.orbit, target)
    if enc:
        return abs(enc[0] - pe_alt) / 1000.0
    ca = node.orbit.next_closest_approach(target.orbit).distance
    return 1000.0 + ca / 1000.0


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
    target = sc().bodies[target_name]
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


def correct_course(target_name, pe_alt):
    """Mid-course correction toward target periapsis pe_alt (small burn now + 60 s)."""
    v = vessel()
    target = sc().bodies[target_name]
    node = v.control.add_node(ut() + 120, 0, 0, 0)
    tune_node(node, lambda n: _node_cost(n, target, pe_alt),
              steps=(("prograde", 1.0), ("normal", 1.0), ("radial", 1.0)))
    enc = _encounter(node.orbit, target)
    say(f"correction {node.delta_v:.1f} m/s -> pe {enc[0] if enc else None}")
    if enc is None and v.orbit.body.name != target.name:
        node.remove()
        say("no encounter reachable with a small correction; not burning")
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

def land(safety=1.3, final_speed=1.5, max_decel=3.0):
    """Land on an airless body from a low orbit: kill horizontal speed, then a throttled suicide burn."""
    v = vessel()
    body = v.orbit.body
    fl = v.flight(body.reference_frame)
    ap = v.auto_pilot
    ap.reference_frame = v.surface_velocity_reference_frame
    ap.target_direction = (0, -1, 0)
    ap.engaged = True
    _wait_pointing(ap)
    g = body.surface_gravity
    say(f"deorbit: killing horizontal speed ({fl.horizontal_speed:.0f} m/s)")
    v.control.throttle = 1.0
    while fl.horizontal_speed > 5:
        auto_stage(v)
        v.control.throttle = min(1.0, max(0.05, fl.horizontal_speed / 50))
        time.sleep(0.05)
    v.control.throttle = 0.0
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


def liftoff(target_alt=15000, heading=90.0):
    """Take off from an airless body into a low circular orbit."""
    v = vessel()
    fl = v.flight(v.orbit.body.reference_frame)
    v.control.sas = False
    ap = v.auto_pilot
    ap.reference_frame = v.surface_reference_frame
    ap.target_pitch_and_heading(90, heading)
    ap.engaged = True
    v.control.throttle = 1.0
    t0 = time.time()
    while time.time() - t0 < 4 or fl.surface_altitude < 200:
        auto_stage(v)
        if time.time() - t0 > 3 and v.available_thrust <= 0:
            v.control.throttle = 0.0
            say("liftoff aborted: no thrust")
            return False
        time.sleep(0.05)
    ap.target_pitch_and_heading(30, heading)
    while v.orbit.apoapsis_altitude < target_alt:
        auto_stage(v)
        # keep climbing if the terrain is close
        ap.target_pitch_and_heading(45 if fl.surface_altitude < 2000 else 15, heading)
        time.sleep(0.05)
    v.control.throttle = 0.0
    ap.engaged = False
    v.control.legs = False
    circularize()


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
        if not p.deployed:
            p.deploy()
    say("chutes deployed")
    while v.situation.name not in ("landed", "splashed"):
        time.sleep(1)
    say(f"{v.situation.name}! {v.name}")


# ---------------------------------------------------------------- science

def do_science(transmit=False):
    """Run every available experiment that has no data yet; optionally transmit results."""
    v = vessel()
    out = []
    for e in v.parts.experiments:
        if e.inoperable or e.has_data or not e.available:
            continue
        try:
            e.run()
        except Exception as ex:
            out.append((e.title, f"error {ex}"))
    time.sleep(1.5)
    for e in v.parts.experiments:
        if e.has_data:
            val = sum(d.science_value for d in e.data)
            out.append((e.title, e.science_subject.title, round(val, 2)))
            if transmit and e.data and any(d.transmit_value > 0 for d in e.data):
                e.transmit()
    for row in out:
        print(row)
    return out


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
    a, b = math.radians(lat1), math.radians(lat2)
    d = math.radians(lon2 - lon1)
    c = math.sin(a) * math.sin(b) + math.cos(a) * math.cos(b) * math.cos(d)
    return body.equatorial_radius * math.acos(max(-1.0, min(1.0, c)))


def survey(keyword="temperature", max_dist=8000.0, horizon_orbits=40, step=20.0):
    """Orbital survey contracts: for each waypoint of a matching contract on this body, warp to the closest
    pass of the ground track and run the matching experiment there (lateral trigger range is up to 15 km)."""
    v = vessel()
    body = v.orbit.body
    wps = [w for w in sc().waypoint_manager.waypoints
           if w.body == body and w.has_contract and keyword in w.contract.title.lower()]
    exp_name = {"temperature": "temperatureScan", "pressure": "barometerScan"}.get(keyword)
    say(f"{len(wps)} {keyword} waypoints on {body.name}: " + ", ".join(f"{w.name} ({w.latitude:.1f}, {w.longitude:.1f})" for w in wps))
    todo = list(wps)
    while todo:
        # scan the predicted ground track for the earliest pass within max_dist of any remaining site
        t0, best = ut(), None
        end = t0 + horizon_orbits * v.orbit.period
        t = t0 + 30
        while t < end and best is None:
            lat, lon = _latlon_at(v, t)
            for w in todo:
                if _ground_dist(body, lat, lon, w.latitude, w.longitude) < max_dist * 1.5:
                    best = (t, w)
                    break
            t += step
        if best is None:
            say(f"no pass within {max_dist:.0f} m of {[w.name for w in todo]} in {horizon_orbits} orbits")
            return False
        t, w = best
        say(f"next: {w.name} around UT {t:.0f} (in {t - ut():.0f} s)")
        warp_to(t, lead=60)
        # fly through the pass at 1x, run the experiment at the closest point (or once inside max_dist)
        last = 1e12
        while True:
            f = v.flight(body.reference_frame)
            d = _ground_dist(body, f.latitude, f.longitude, w.latitude, w.longitude)
            if d > last and last < max_dist:
                break
            if d > last and last >= max_dist and d > max_dist * 3:
                say(f"missed {w.name}: closest {last:.0f} m")
                break
            last = d
            time.sleep(0.5)
        if last < max_dist:
            for e in v.parts.experiments:
                if e.name == exp_name or (exp_name is None and keyword in e.title.lower()):
                    if e.has_data:
                        e.reset()
                        time.sleep(0.5)
                    e.run()
                    say(f"{w.name}: ran {e.title} at {last:.0f} m lateral, alt {f.mean_altitude:.0f} m")
                    break
            todo.remove(w)
        time.sleep(1)
    return True
