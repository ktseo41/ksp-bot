"""Flight routines. Each public function is one mission phase and returns when that phase is done.

Conventions: altitudes in meters above sea level, speeds in m/s, the active vessel is flown.
"""
import functools
import math
import re
import time

from . import kepler
from .core import say, sc

G0 = 9.80665
PLAN_ONLY = False  # cli --plan: planners stop at their first tuned node (left in place) instead of burning it


class Refused(Exception):
    """A planned burn failed its sanity check; the node is left for inspection."""


class Planned(Exception):
    """--plan: the node is planned and left; burn it with `ksp node` after checking the numbers."""


# ---------------------------------------------------------------- small helpers

def vessel():
    return sc().active_vessel


def ut():
    return sc().ut


def _norm(v):
    m = math.sqrt(sum(x * x for x in v))
    return tuple(x / m for x in v) if m > 0 else v


def speed_at(o, t):
    """Orbital speed at UT t by vis-viva. kRPC's Orbit.orbital_speed_at(t) is wrong for future times (asked for
    +600 s it gave another point's speed): Rescue 3's phasing return burned +172 instead of -66 m/s."""
    return math.sqrt(o.body.gravitational_parameter * (2 / o.radius_at(t) - 1 / o.semi_major_axis))


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def warp_to(t, lead=0.0):
    """Time-warp until UT t - lead (no-op if already there). Inside an atmosphere only physics warp works (x4):
    a 17-minute wait for a periapsis burn there went unnoticed, so say what it costs in real time."""
    dt = t - lead - ut()
    if dt <= 1:
        return
    try:
        v = vessel()
        b = v.orbit.body
        if dt > 120 and b.has_atmosphere and v.flight().mean_altitude < b.atmosphere_depth \
                and v.situation.name not in ("landed", "splashed", "pre_launch"):
            say(f"waiting {dt:.0f} s inside the atmosphere: no rails warp, ~{dt / 4 / 60:.0f}-{dt / 60:.0f} real min")
        elif dt > 3600:
            # the rails cap depends on the altitude: 60 km over Duna ran ~4x effective (Duna 1 waited 25 real min
            # for 5,800 s); from a low orbit say it, far waits belong at the space center (`warp-sc`, then `fly`)
            rate = (1, 5, 10, 50, 100, 1000, 10000, 100000)[min(7, sc().maximum_rails_warp_factor)]
            if dt / rate > 300:
                say(f"waiting {dt:.0f} s at most {rate}x here: >= {dt / rate / 60:.0f} real min "
                    "(a far wait is faster from the space center: `scene space_center`, `warp-sc`, `fly`)")
    except Exception:
        pass
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
    """Seconds to burn dv, through the stages KSP's delta-v readout lists (Jool 1: the Skipper had 480 m/s of a
    1954 m/s ejection, the estimate used its thrust alone (54 s), and the guard stopped the Nerv 601 m/s short).
    Without the readout the stages come from the parts (_burns_from_parts)."""
    burns = _burns(v)
    left, t = dv, 0.0
    for sdv, st, ve in burns:
        if sdv >= left:
            # time goes with the propellant burned, not with dv (Moho 1: 2040 of the Poodle's 2961 m/s is 196 s,
            # not the linear 174 s)
            return t + st * (1 - math.exp(-left / ve)) / (1 - math.exp(-sdv / ve))
        left -= sdv
        t += st
    if not burns:
        now = _burn_time_now(v, dv)
        say(f"WARNING: stage dv unavailable: estimate covers the current stage only ({now:.0f} s), "
            f"real burn may be longer")
        return now
    say(f"WARNING: {dv:.0f} m/s is more than the {dv - left:.0f} m/s the stages hold: burn time {t:.0f} s "
        f"covers all the propellant")
    return t


def _burns(v):
    """[(vacuum dv, burn time, exhaust velocity)] per stage from the current one down, from KSP's delta-v readout.
    After `scene space_center` + `fly` that readout was "not calculated" for hours (Moho 1, 2026-09-27: a 2987 m/s
    capture on Poodle + Terrier read 131 s from the Poodle alone instead of ~278 s, lead 80 s instead of 144 s):
    ask the mod to force KSP's calculation, else model the stages from the parts. burn_time and burn_lead ask back
    to back: the answer is kept while the vessel's stage and mass stay the same."""
    key = (v._object_id, v.control.current_stage)
    mass = v.mass
    hit = _BURNS.get(key)
    if hit and time.monotonic() - hit[0] < 30 and abs(hit[1] - mass) < 1:
        return hit[2]
    burns = _burns_uncached(v)
    _BURNS.clear()
    _BURNS[key] = (time.monotonic(), mass, burns)
    return burns


_BURNS = {}


def _burns_uncached(v):
    for attempt in range(3):
        try:
            burns = []
            for st in sorted((st for st in v.stages if st.vacuum_delta_v > 0.5), key=lambda st: -st.number):
                ve = st.vacuum_delta_v / math.log(st.start_mass / st.end_mass)
                burns.append((st.vacuum_delta_v, st.burn_time, ve))
            return burns
        except Exception as e:
            if "not been calculated" not in str(e) or attempt == 2:
                break
            _recalc_delta_v(v)
    try:
        burns = _burns_from_parts(v)
    except Exception as e:
        say(f"WARNING: stage model from parts failed ({e})")
        return []
    if burns:
        say(f"KSP stage dv unavailable: modelled from parts: "
            + ", ".join(f"{dv:.0f} m/s in {t:.0f} s" for dv, t, _ in burns))
    return burns


def _recalc_delta_v(v):
    """KspBot.RecalcDeltaV: stop KSP's stuck delta-v run and redo it at once (see the mod); a short wait for the
    readout either way. An older mod build has no such call: just wait."""
    try:
        import json
        from .core import bot
        r = json.loads(bot().recalc_delta_v())
        say(f"KSP delta-v readout not ready: forced a recalculation (before {r.get('before')}, "
            f"after {r.get('after')})", screen=False)
    except Exception as e:
        say(f"KSP delta-v readout not ready, recalculation unavailable ({e}): waiting", screen=False)
    time.sleep(1.0)


_DENSITY = {"LiquidFuel": 5.0, "Oxidizer": 5.0, "MonoPropellant": 4.0, "SolidFuel": 7.5, "XenonGas": 0.1}  # kg/unit
_NOT_PROPELLANT = {"ElectricCharge", "IntakeAir"}


def _density(name):
    if name not in _DENSITY:
        try:
            _DENSITY[name] = sc().Resources.density(name)
        except Exception:
            _DENSITY[name] = 5.0
    return _DENSITY[name]


def _burns_from_parts(v):
    """[(vacuum dv, burn time, exhaust velocity)] per stage from the current one down, from the parts: a part
    decoupled in stage d is gone from stage d on; the engines of stage s are the active ones plus those activated
    by then, and they burn (to empty, as auto_stage stages) their propellants in the tanks decoupled with them or
    earlier. Right for a plain stack (decoupler + next engine); a stage whose engines drop at different stages
    (boosters around a core) gets a warning: it counts all their propellant as one burn."""
    cur = v.control.current_stage
    engines = []
    for e in v.parts.engines:
        p = e.part
        f = e.max_vacuum_thrust * e.thrust_limit
        isp = e.vacuum_specific_impulse
        if f > 0 and isp > 0:
            d = p.decouple_stage
            engines.append(dict(stage=p.stage, d=d if d < cur else -1, active=e.active, f=f, isp=isp,
                                props=set(e.propellant_names) - _NOT_PROPELLANT))
    names = set().union(*(e["props"] for e in engines)) if engines else set()
    parts = []
    for p in v.parts.all:
        d = p.decouple_stage
        if d >= cur:
            d = -1  # its decoupler's stage has passed: it stays on
        res = p.resources
        fuel = {n: res.amount(n) * _density(n) for n in names}
        parts.append(dict(d=d, mass=p.mass, fuel={n: m for n, m in fuel.items() if m > 0}))
    burns = []
    for s in range(cur, -1, -1):
        present = [q for q in parts if q["d"] < s]
        eng = [e for e in engines if e["d"] < s and (e["active"] if e["stage"] >= cur else e["stage"] >= s)]
        if not eng:
            continue
        dmin = min(e["d"] for e in eng)
        if max(e["d"] for e in eng) != dmin:
            say(f"WARNING: stage {s} engines drop at different stages: its burn time is a rough guess")
        props = set().union(*(e["props"] for e in eng))
        m0 = sum(q["mass"] for q in present)
        fuel = 0.0
        for q in present:
            if q["d"] >= dmin:
                for n in props & set(q["fuel"]):
                    fuel += q["fuel"][n]
                    q["mass"] -= q["fuel"].pop(n)
        if fuel <= 0 or fuel >= m0:
            continue
        f = sum(e["f"] for e in eng)
        ve = f / sum(e["f"] / e["isp"] for e in eng) * G0
        burns.append((ve * math.log(m0 / (m0 - fuel)), fuel * ve / f, ve))
    return burns


def burn_lead(v, dv):
    """Seconds from ignition until half the dv is burned: the start that centres the dv on the node. Later than
    half the burn time, since the craft gets lighter (Moho 1's 196 s ejection started bt/2 = 87 s early instead of
    113 s: the ejection landed ~5 deg late on the 80 km orbit and missed Moho by 420,000 km)."""
    return burn_time(v, dv / 2)


def _burn_time_now(v, dv):
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

def _controllable(v):
    return v.control.state.name == "full" or (v.control.state.name == "partial" and v.control.source.name == "kerbal")


def _await_link(v, deadline):
    """Right before ignition (and during a burn): an uncrewed craft can lose its CommNet link while it waits (Ike
    Station 1's capture: Kerbin went behind Ike near the periapsis, the burn ran at thrust 0 into the timeout, the
    link came back a minute later). Wait for the link in short warp steps until UT deadline; True if it is back."""
    if _controllable(v):
        return True
    v.control.throttle = 0.0
    say(f"no control ({v.control.state.name}, signal {v.comms.signal_strength:.2f}): waiting for the link "
        f"up to {deadline - ut():.0f} s")
    while ut() < deadline:
        sc().warp_to(min(deadline, ut() + 10))
        if _controllable(v):
            say("link back: burning")
            return True
    return False


def _ensure_control(v):
    """With Require Signal for Control a probe-controlled craft has no throttle without a CommNet link. Minmus Lab 1:
    the stowed HG-55 left only the OKTO's own antenna (~16 Mm with DSN 2), and the capture burn at Minmus sat at
    throttle 1 / thrust 0 until the burn-time guard gave up. Extend antennas in vacuum, else refuse."""
    if v.control.state.name == "full" or (v.control.state.name == "partial" and v.control.source.name == "kerbal"):
        return  # crew without a Pilot and no link is KSP's "No Pilot" state: only map node editing is locked
        # (Vessel.CheckControllable PARTIAL_MANNED); Rescue 6 refused two burns behind Minmus for nothing
    if v.flight().static_pressure < 1:
        _antennas(v, True)
        time.sleep(2)
    if v.control.state.name != "full":
        raise Refused(f"no control ({v.control.state.name}): no CommNet link (signal {v.comms.signal_strength:.2f}); "
                      "a pilot aboard, an antenna or a relay is needed")
    say("antennas extended: control restored")


def _link_by(start, capture_pe, lead, default):
    """UT until which a burn may wait for the link before ignition. A capture waits at most until a start that still
    centres the burn on the periapsis: waiting longer drifts into a flyby (Moho, e = 21)."""
    return default if capture_pe is None else max(start, capture_pe - lead)


def execute_node(node=None, tol=0.2, capture_pe=None, thrust_limit=None):
    """Execute a maneuver node (default: the first one). Handles pointing, warp, staging and fine throttle.
    capture_pe: UT of the periapsis of a capture burn: the pre-ignition link wait ends in time for it, and a link
    lost mid-burn never pauses the burn (see below). thrust_limit: 0..1 on the active engines for this burn only."""
    v = vessel()
    # kRPC's default time_to_peak of 1 s set Moho 1's flexible stack (8 t lander on a 9 t Poodle stage) swinging
    # +-20 deg during a 0.3 m/s trim: the tumble guard fired again and again and the burn went every which way.
    # 8 s settled the same 110 deg turn in 30 s to 0.5 deg. Restored after the burn (other phases tune their own).
    ttp = v.auto_pilot.time_to_peak
    v.auto_pilot.time_to_peak = (8.0, 8.0, 8.0)
    engines = [e for e in v.parts.engines if e.active] if thrust_limit is not None else []
    for e in engines:
        e.thrust_limit = thrust_limit
    try:
        return _execute_node(node, tol, capture_pe)
    finally:
        for e in engines:
            e.thrust_limit = 1.0
        if engines:
            v.control.throttle = 0.0
        v.auto_pilot.time_to_peak = ttp


def _execute_node(node, tol, capture_pe):
    v = vessel()
    _ensure_control(v)
    node = node or v.control.nodes[0]
    dv = node.delta_v
    if v.available_thrust <= 0:  # a spent stage still attached (Mun Tanker 1: burn time read 0 s, burn started late)
        auto_stage(v)
    bt, lead = burn_time(v, dv), burn_lead(v, dv)
    ap = v.auto_pilot
    # steer in an inertial frame: the node's own frame turns with the orbit being changed, and near the end of a
    # burn its small remainder swings about: Moho 1's trims spun up to 11 deg/s in the last 5 m/s every time
    frame = v.orbit.body.non_rotating_reference_frame
    ap.reference_frame = frame
    ap.target_direction = _norm(node.burn_vector(frame))
    ap.engaged = True
    say(f"burn {dv:.0f} m/s, ~{bt:.0f}s (start {lead:.0f}s before the node), in {node.ut - ut():.0f}s")
    warp_to(node.ut - lead, lead=60)
    _wait_pointing(ap)
    warp_to(node.ut - lead, lead=5)
    while ut() < node.ut - lead:
        time.sleep(0.05)
    if not _await_link(v, _link_by(node.ut - lead, capture_pe, lead, node.ut + bt - lead)):
        if capture_pe is not None:
            node.remove()
            raise Refused(f"no CommNet link by {capture_pe - lead - ut():+.0f} s from the periapsis burn start "
                          f"(control {v.control.state.name}): capture not started, node removed; `capture` again "
                          "burns now once the link is back")
        raise Refused(f"no CommNet link at the burn time (control {v.control.state.name}): node left in place")
    v.control.throttle = 1.0
    no_thrust = None
    blind = None  # UT the link was lost at, during a capture burn
    t_end = time.time() + 3 * bt + 60
    t_check = time.time() + 1
    while True:
        if time.time() > t_end:
            say("burn is taking far too long: stopping")
            break
        if time.time() > t_check:  # the link can also drop mid-burn: pause and resume when it returns
            t_check = time.time() + 1
            if not _controllable(v) and capture_pe is not None:
                # a capture never pauses: a warp/pause at e = 21 loses the Oberth window; the loop runs on at
                # throttle 1 without warping and the thrust comes back with the link
                if blind is None:
                    blind = ut()
                    say(f"link lost mid-capture, {node.remaining_delta_v:.0f} m/s left: burning on, no warp")
                if ut() - blind > max(600, 3 * bt):
                    raise Refused(f"CommNet link lost for {ut() - blind:.0f} s mid-capture, "
                                  f"{node.remaining_delta_v:.1f} m/s left: node left")
                t_end = time.time() + 3 * bt + 60
            elif not _controllable(v):
                if not _await_link(v, ut() + max(120, bt)):
                    raise Refused(f"CommNet link lost mid-burn, {node.remaining_delta_v:.1f} m/s left: node left")
                _wait_pointing(ap, timeout=60)
                t_end = time.time() + 3 * bt + 60
            elif blind is not None:
                say(f"link back after {ut() - blind:.0f} s: {node.remaining_delta_v:.0f} m/s left")
                blind = None
        if blind is None and _tumbling(v):  # Mun Tanker 1 spun up to 60 deg/s at a burn start and the loop never ended
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
        rem = node.remaining_burn_vector(frame)
        left = node.remaining_delta_v
        if _dot(rem, ap.target_direction) < 0 or left < tol:
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


def _describe(node):
    """What the node leads to: the orbit after it and the next patches (body, pe, inc, v_inf)."""
    o = node.orbit
    out = [f"{node.delta_v:.1f} m/s in {node.ut - ut():.0f}s ->"]
    for _ in range(3):
        inc = math.degrees(o.inclination)
        s = f"{o.body.name} pe {o.periapsis_altitude / 1000:.1f} km"
        if o.eccentricity < 1:
            s += f" ap {o.apoapsis_altitude / 1000:.1f} km"
        else:
            s += f" v_inf {math.sqrt(o.body.gravitational_parameter / abs(o.semi_major_axis)):.0f}"
        s += f" inc {inc:.1f}" + (" RETROGRADE" if inc > 90 else "")
        out.append(s)
        o = o.next_orbit
        if o is None:
            break
    return out[0] + " " + " / ".join(out[1:])


def _approve(node, expect, pe_alt=None, allow_flip=False):
    """Sanity gate for a planner's tuned node, before execute_node: the Δv must be near the analytic estimate
    (Keo Relay 2's tuner chose 1602 m/s for a 523 m/s job), the orbit must not reverse (that same burn flipped it
    retrograde), and the periapsis must not drop into the air unless pe_alt asks for it. --plan stops here."""
    v = vessel()
    o0, o = v.orbit, node.orbit
    say(f"plan: {_describe(node)} (expected ~{abs(expect):.0f} m/s)", screen=False)
    why = None
    if node.delta_v > 1.5 * abs(expect) + 20:
        why = f"{node.delta_v:.0f} m/s is far above the expected {abs(expect):.0f}"
    elif o.body.name == o0.body.name:
        b = o.body
        rel = math.degrees(_rel_inc(o0.inclination, o0.longitude_of_ascending_node,
                                    o.inclination, o.longitude_of_ascending_node))
        if rel > 90 and not allow_flip:
            why = f"the orbit would reverse direction (relative inclination {rel:.0f} deg)"
        elif b.has_atmosphere and o0.periapsis_altitude >= b.atmosphere_depth > o.periapsis_altitude \
                and not (pe_alt is not None and pe_alt < b.atmosphere_depth):
            why = f"the periapsis would drop into the atmosphere ({o.periapsis_altitude / 1000:.1f} km)"
    if why:
        say(f"REFUSED: {why}; node left for inspection")
        raise Refused(why)
    if PLAN_ONLY:
        raise Planned(_describe(node))


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


def burn_at(t, prograde=0.0, normal=0.0, radial=0.0, capture_pe=None):
    """Burn a delta-v (orbital frame at UT t): via a maneuver node, or manually if nodes are locked
    (Tracking Station / Mission Control level 1)."""
    try:
        node = vessel().control.add_node(t, prograde, normal, radial)
    except RuntimeError as e:
        if "Maneuver node" not in str(e):
            raise
        return manual_burn(t, prograde, normal, radial, capture_pe=capture_pe)
    return execute_node(node, capture_pe=capture_pe)


def manual_burn(t, prograde=0.0, normal=0.0, radial=0.0, tol=0.3, capture_pe=None):
    """Node-less burn: fixed inertial direction from the orbital frame at t, delivered dv integrated
    from thrust/mass."""
    v = vessel()
    _ensure_control(v)
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
    bt, lead = burn_time(v, dv), burn_lead(v, dv)
    ap = v.auto_pilot
    ap.reference_frame = frame
    ap.target_direction = _norm(vec)
    ap.engaged = True
    say(f"manual burn {dv:.0f} m/s, ~{bt:.0f}s (start {lead:.0f}s before), in {t - ut():.0f}s")
    warp_to(t - lead, lead=60)
    _wait_pointing(ap)
    warp_to(t - lead, lead=5)
    while ut() < t - lead:
        time.sleep(0.05)
    if not _await_link(v, _link_by(t - lead, capture_pe, lead, t + bt - lead)):
        raise Refused(f"no CommNet link at the burn time (control {v.control.state.name})")
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

def _limit_srbs(v, twr):
    """On the pad: thrust-limit the first stage's solid boosters (they can't throttle) for a liftoff TWR of twr.
    The Kickback launcher lifted off at TWR 2.0 and reached 6 g: max Q 51 kPa at 9 km, ~440 m/s of drag to 40 km
    (community guidance: liftoff TWR 1.3-1.7; MechJeb's acceleration limit default 40 m/s^2)."""
    body = v.orbit.body
    engines = [e for e in v.parts.engines if e.part.stage == v.control.current_stage - 1]
    solid = [e for e in engines if "SolidFuel" in e.propellant_names]
    if not solid:
        return
    t_solid = sum(e.max_thrust_at(1.0) for e in solid)
    t_other = sum(e.max_thrust_at(1.0) for e in engines if e not in solid)
    lim = max(0.3, min(1.0, (twr * v.mass * body.surface_gravity - t_other) / t_solid))
    for e in solid:
        e.thrust_limit = lim
    say(f"liftoff TWR {(t_solid + t_other) / (v.mass * body.surface_gravity):.2f} -> {twr:.2f}: "
        f"{len(solid)} SRBs limited to {lim * 100:.0f}%")


def ascent(target_alt=80000, heading=90.0, turn_start=250, turn_end=45000, shape=0.5, max_aoa=15.0, twr=None):
    """Launch from Kerbin (or any atmospheric body) to an apoapsis of target_alt, coast out of the
    atmosphere keeping the apoapsis up. Then call circularize(). twr: liftoff TWR for solid first stages."""
    v = vessel()
    if twr and v.situation.name == "pre_launch":
        _limit_srbs(v, twr)
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
    cmd, t_cmd = 90.0, time.time()
    while True:
        auto_stage(v)
        alt = fl.mean_altitude
        frac = min(1.0, max(0.0, (alt - turn_start) / (turn_end - turn_start)))
        pitch = 90.0 * (1 - frac ** shape)
        spd = fl.speed
        if spd > 80 and alt > turn_start:
            vel_pitch = math.degrees(math.atan2(fl.vertical_speed, max(fl.horizontal_speed, 1e-3)))
            # low-TWR upper stages: the altitude program alone laid Moho 1 flat at 38 km (apoapsis never above it,
            # 2 km/s in the air, the OKTO overheated): above 12 km hold the apoapsis >= 45 s ahead while in the air
            if 12000 < alt < atmo:
                t_apo = v.orbit.time_to_apoapsis if fl.vertical_speed > 0 else 0.0
                if t_apo < 45:
                    pitch += 1.5 * (45 - t_apo)
            pitch = min(max(pitch, vel_pitch - max_aoa), vel_pitch + max_aoa)
        # at most 1.5 deg/s: the sqrt program starts with an infinite slope at turn_start, and that kick set the
        # tall 1.25 m Rescue 3/4 stacks swaying (+-1 deg/s at 0.3 Hz) from 250 m until past max Q
        now = time.time()
        step, t_cmd = 1.5 * (now - t_cmd), now
        cmd = min(max(pitch, cmd - step), cmd + step)
        ap.target_pitch_and_heading(max(cmd, 0), heading)
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
        if any(e.active and not e.has_fuel for e in v.parts.engines):
            # boosters that burned out as the apoapsis reached the target: drop them now (Keo Relay 1 carried
            # its empty Kickbacks from 25 to 70 km, until circularize staged)
            auto_stage(v)
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
        if o.apoapsis_altitude > body.atmosphere_depth and o.time_to_apoapsis < o.time_to_periapsis:
            # the apoapsis comes first: raise the periapsis there (Salvage 3 at 62x84 km burned prograde "now"
            # for 2 minutes: the periapsis rose 9 km, the apoapsis went hyperbolic)
            change_periapsis(body.atmosphere_depth + 8000)
        else:
            _raise_pe_now(v, body.atmosphere_depth + 8000)
        o = v.orbit
    if not body.has_atmosphere or o.periapsis_altitude > body.atmosphere_depth:
        _antennas(v, True)  # in orbit: open antennas and solar panels (retracted again before reentry/liftoff)
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
    ap0 = max(v.orbit.apoapsis_altitude, pe_alt) + 50000
    while v.orbit.periapsis_altitude < pe_alt and time.time() - t0 < 120:
        if v.orbit.apoapsis_altitude > ap0 or v.orbit.eccentricity > 0.2:
            say(f"stopping: apoapsis {v.orbit.apoapsis_altitude:.0f} m running away")
            break
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
    b = patch.body
    if b.has_atmosphere and patch.periapsis_altitude < b.atmosphere_depth \
            and patch.time_to_periapsis < patch.time_to_soi_change:
        return 0.0  # the moon comes after an atmospheric periapsis (Duna 1's return: a Mun pass we never reach)
    return 1000.0 + (moon.body.sphere_of_influence - moon.periapsis) / 1000.0


def _inc_off(orbit, inc_to):
    """Degrees/5 between the arrival inclination and inc_to (0..180: picks prograde vs retrograde too)."""
    return abs(math.degrees(orbit.inclination) - inc_to) / 5.0 if inc_to is not None else 0.0


def _node_cost(node, target, pe_alt, min_inc=None, inc_to=None):
    """Periapsis error (km) + inclination terms, read only off the patch around target (a heliocentric patch's
    inclination means nothing for inc_to); with no encounter, the closest approach behind a fixed miss penalty."""
    time.sleep(0.04)  # let KSP recompute patches
    if node.orbit.body.name == target.name:  # already inside the target SOI: just shape the periapsis
        return abs(node.orbit.periapsis_altitude - pe_alt) / 1000.0 + _inc_short(node.orbit, min_inc) \
            + _inc_off(node.orbit, inc_to) + _moon_penalty(node.orbit, target)
    enc = _encounter(node.orbit, target)
    if enc:
        return abs(enc[0] - pe_alt) / 1000.0 + _inc_short(enc[1], min_inc) + _inc_off(enc[1], inc_to) \
            + _moon_penalty(enc[1], target)
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


FAR_SETTLE = 0.3  # s from a node edit to reading its patches far out: at 0.04 s Eve 2's costs (185 d out) came back
# inconsistent from run to run


def _far_cost(dv, pe, inc, pe_alt, w_pe, min_inc=None, inc_to=None, retro=None):
    """Cost of a far-out correction with an encounter (pure: no kRPC): dv + w_pe per km of periapsis error + 0.3 per
    deg of inclination off inc_to (or short of min_inc) + 1000 for a pass on the wrong side (retro True: it must be
    retrograde, False: prograde, None: either). Eve 2's grid, with no dv term and no side, ended at 30.8 m/s and a
    retrograde pass (inc 156) where 7.7 m/s did."""
    c = dv + w_pe * abs(pe - pe_alt) / 1000.0
    if inc_to is not None:
        c += 0.3 * abs(inc - inc_to)
    if min_inc:
        c += 0.3 * max(0.0, min_inc - min(inc, 180 - inc))
    if retro is not None and (inc > 90) != retro:
        c += 1000.0
    return c


def _pattern_search(f, x0, steps, max_steps, min_steps, iters=60):
    """Compass search (pure): try +-step on each coordinate, keep the first improvement and grow that step x1.3
    (capped at max_steps: the old tuner's x1.5 grew without bound and walked off), halve it on no improvement;
    stop when every step is under min_steps. Returns (f(best), best)."""
    x, fx, st = list(x0), f(list(x0)), list(steps)
    for _ in range(iters):
        improved = False
        for k in range(len(x)):
            for s in (1, -1):
                y = list(x)
                y[k] += s * st[k]
                fy = f(y)
                if fy < fx:
                    x, fx, improved = y, fy, True
                    st[k] = min(st[k] * 1.3, max_steps[k])
                    break
            else:
                st[k] *= 0.5
        if not improved and all(a < b for a, b in zip(st, min_steps)):
            break
    return fx, x


def _far_search(node, target, pe_alt, seeds, steps, cap, w_pe, min_inc=None, inc_to=None, retro=None):
    """Far-out correction (craft around the Sun): a compass search on (prograde, normal, radial) from each seed,
    judged by KSP's own patches read FAR_SETTLE s after every edit; cost _far_cost, a miss ranks behind any
    encounter by its closest approach, dv over cap is never tried. Leaves the best in place (re-read after 1 s) and
    returns (dv, pe, inc) or None with no encounter. Takes minutes (~0.4 s per trial): run it in the background."""
    trials = [0]

    def f(x):
        dv = math.sqrt(sum(a * a for a in x))
        if dv > cap:
            return 1e6 + dv
        node.prograde, node.normal, node.radial = x
        trials[0] += 1
        return cost(FAR_SETTLE)[0]

    def cost(settle):
        time.sleep(settle)
        dv = math.sqrt(node.prograde ** 2 + node.normal ** 2 + node.radial ** 2)
        enc = _encounter(node.orbit, target)
        if enc:
            inc = math.degrees(enc[1].inclination)
            return _far_cost(dv, enc[0], inc, pe_alt, w_pe, min_inc, inc_to, retro) \
                + _moon_penalty(enc[1], target), enc[0], inc
        o = _patch_around(node.orbit, target.orbit.body.name)
        if o is None:
            return 1e9, None, None
        return 1e5 + dv + w_pe * o.next_closest_approach(target.orbit).distance / 1000.0, None, None

    best = None
    for s in seeds:
        c, x = _pattern_search(f, s, steps, [10 * a for a in steps], [max(0.005, a / 100) for a in steps])
        say(f"far search from {[round(a, 2) for a in s]}: cost {c:.2f} at {[round(a, 3) for a in x]}", screen=False)
        if best is None or c < best[0]:
            best = (c, x, s)
    node.prograde, node.normal, node.radial = best[1]
    c, pe, inc = cost(1.0)
    dv = math.sqrt(sum(a * a for a in best[1]))
    if abs(c - best[0]) > 0.5 + 0.05 * abs(best[0]):
        say(f"WARNING: the best node re-read after 1 s costs {c:.2f}, not {best[0]:.2f}: KSP's prediction is unsteady "
            "here; check the node before burning")
    say(f"far search ({trials[0]} trials, {len(seeds)} seeds, cap {cap:.2f} m/s): best {dv:.2f} m/s from seed "
        f"{[round(a, 2) for a in best[2]]} -> " + (f"{target.name} pe {pe / 1000:.1f} km, inc {inc:.1f}"
                                                   + (" RETROGRADE" if inc > 90 else "") if pe is not None
                                                   else "no encounter"))
    return (dv, pe, inc) if pe is not None else None


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
    # an inclined moon (Minmus 6 deg) can sit farther out of our plane at arrival than its SOI: Rescue 6's tuner then
    # found a 1094 m/s escape path instead of 930; say when the moon crosses our plane instead
    frame = v.orbit.body.non_rotating_reference_frame
    h = _norm(_cross(v.position(frame), v.velocity(frame)))
    off = lambda t: abs(_dot(target.orbit.position_at(t, frame), h))
    soi = target.sphere_of_influence
    if off(ut() + wait + t_trans) > 0.8 * soi:
        day = 21600.0
        good = next((k for k in range(1, int(target.orbit.period / day) + 1)
                     if off(ut() + wait + k * day + t_trans) < 0.3 * soi), None)
        raise Refused(f"{target_name} will be {off(ut() + wait + t_trans) / 1e6:.1f} Mm out of our plane at arrival "
                      f"(SOI {soi / 1e6:.1f} Mm)" + (f"; depart ~{good} days later (warp from the space center)"
                                                   if good else ""))
    node = v.control.add_node(ut() + wait, dv, 0, 0)
    say(f"transfer to {target_name}: {dv:.0f} m/s in {wait:.0f}s, tuning")
    c = tune_node(node, lambda n: _node_cost(n, target, pe_alt),
                  steps=(("prograde", 5.0), ("ut", 60.0), ("normal", 10.0)))
    enc = _encounter(node.orbit, target)
    if not enc:
        say(f"no encounter found (cost {c:.1f}); node left for inspection")
        return False
    say(f"encounter: {target_name} periapsis {enc[0]:.0f} m, dv {node.delta_v:.0f}")
    _approve(node, dv)
    execute_node(node)
    # long burns drift; fix the encounter right away while corrections are cheap
    enc = _encounter(v.orbit, target)
    if not enc or abs(enc[0] - pe_alt) > 3000:
        return correct_course(target_name, pe_alt)
    return True


def planet_window(target_name, origin=None, lookback_days=40, flight_time=False):
    """UT of the Hohmann window from origin (default: the planet we orbit) to another planet: the departure t at
    which the target, at arrival t + T, sits 180 deg from the origin's position at t. Uses the real (eccentric)
    orbits; a linear phase extrapolation 200 days out once missed the Duna window by ~15 days.
    Returns the nearest window from lookback_days ago on (it may be in the past); flight_time: (UT, T)."""
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
    # a few days late is fine between planets (synodic ~ years); Mun -> Minmus windows come every 7.4 days, and a
    # 40-day lookback returned one five periods old (Survey 1)
    back = min(lookback_days * day, 0.15 * syn)
    t, (prev, _) = now - back, f(now - back)
    while t < now + 1.5 * syn:  # eccentric targets drift off the mean synodic period (Moho's came 2.5 d past it)
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
            return (t_win, T) if flight_time else t_win
        t, prev = t2, cur
    raise RuntimeError("no window found")


def _stumpff(z):
    """Stumpff functions C(z), S(z)."""
    if z > 1e-8:
        s = math.sqrt(z)
        return (1 - math.cos(s)) / z, (s - math.sin(s)) / s ** 3
    if z < -1e-8:
        s = math.sqrt(-z)
        return (math.cosh(s) - 1) / -z, (math.sinh(s) - s) / s ** 3
    return 0.5, 1 / 6


def _lambert(mu, r1, r2, dt, h):
    """Lambert's problem (universal variables, bisection on z): the velocities (v1, v2) of the conic that goes
    from r1 to r2 in dt seconds the way round that is prograde about the normal h. None near the 180 deg
    singularity (the transfer plane is undefined there) or if no solution."""
    R1, R2 = math.sqrt(_dot(r1, r1)), math.sqrt(_dot(r2, r2))
    c = _cross(r1, r2)
    th = math.acos(max(-1.0, min(1.0, _dot(r1, r2) / (R1 * R2))))
    if _dot(h, c) < 0:
        th = 2 * math.pi - th
    if abs(math.sin(th)) < 1e-3:
        return None
    A = math.sin(th) * math.sqrt(R1 * R2 / (1 - math.cos(th)))

    def y(z):
        C, S = _stumpff(z)
        return R1 + R2 + A * (z * S - 1) / math.sqrt(C)

    def f(z):
        yy = y(z)
        if yy < 0:
            return -1.0
        C, S = _stumpff(z)
        return (yy / C) ** 1.5 * S + A * math.sqrt(yy) - math.sqrt(mu) * dt

    lo, hi = -4 * math.pi ** 2, 4 * math.pi ** 2 - 1e-6
    if f(hi) < 0:
        return None
    for _ in range(120):
        mid = (lo + hi) / 2
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
    yy = y((lo + hi) / 2)
    fl, g, gd = 1 - yy / R1, A * math.sqrt(yy / mu), 1 - yy / R2
    v1 = tuple((b - fl * a) / g for a, b in zip(r1, r2))
    v2 = tuple((gd * b - a) / g for a, b in zip(r1, r2))
    return v1, v2


def _vel_at(o, t, frame):
    """Velocity on orbit o at UT t (central differences of position_at; orbital_speed_at is unreliable)."""
    a, b = o.position_at(t - 1, frame), o.position_at(t + 1, frame)
    return tuple((y - x) / 2 for x, y in zip(a, b))


def _exit_velocity(node, home, frame):
    """Where and how a node's trajectory leaves home's SOI: (velocity relative to home, UT, position in frame),
    read from the patch around home's parent (KSP's own patched-conic hand-over), or None if it does not escape."""
    o = node.orbit
    p = _patch_around(o, home.orbit.body.name)
    if p is None:
        return None
    dt = o.time_to_soi_change
    t = ut() + dt if dt == dt and dt > 0 else None  # NaN check
    soi = home.sphere_of_influence
    if t is None or abs(o.radius_at(t) - soi) > 0.02 * soi:  # not the hand-over time: find the SOI crossing
        lo, hi = node.ut, node.ut + 20 * 86400
        for _ in range(30):
            mid = (lo + hi) / 2
            if o.radius_at(mid) < soi:
                lo = mid
            else:
                hi = mid
        t = hi
    v = tuple(a - b for a, b in zip(_vel_at(p, t, frame), _vel_at(home.orbit, t, frame)))
    return v, t, p.position_at(t, frame)


def transfer_planet(target_name, pe_alt, samples=48):
    """From a circular parking orbit, at (or after) the window, burn to another planet of the same star.
    Lambert (time of flight scanned around the Hohmann value for the cheapest ejection + capture) gives the
    heliocentric departure velocity; the node is tuned so the SOI-exit velocity matches it, with no radial
    component (the burn point stays the periapsis, so it cannot dip into the air), then refined on the target
    periapsis pe_alt once an encounter exists. The target's arrival position is projected onto our orbital
    plane: near a 180 deg transfer the plane change to an inclined planet (Eve, 2.1 deg) cannot be folded into
    the ejection from an equatorial parking orbit (it needs a ~40 deg tilted hyperbola, ~+1100 m/s), so it is
    left to a mid-course correction where the lever arm is long (~a quarter orbit before arrival, <= ~420 m/s).
    Eve 1's old closest-approach tuner instead pumped the energy up and dropped the escape periapsis to 67 km."""
    v = vessel()
    target = sc().bodies[target_name]
    home = v.orbit.body
    sun = home.orbit.body
    t_win, T_h = planet_window(target_name, flight_time=True)
    P = v.orbit.period
    if t_win - ut() > P:
        warp_to(t_win - P / 2)
    mu_s, mu, mu_t = sun.gravitational_parameter, home.gravitational_parameter, target.gravitational_parameter
    r0, r_cap = v.orbit.semi_major_axis, target.equatorial_radius + pe_alt
    frame = sun.non_rotating_reference_frame
    t_dep = ut() + P / 2
    r1 = home.orbit.position_at(t_dep, frame)
    h = _norm(_cross(r1, _vel_at(home.orbit, t_dep, frame)))

    def plan(t1, p1, T):
        """Lambert from p1 at t1 to the target's arrival position projected onto our plane; (v_inf_req vector,
        v_inf magnitudes at departure/arrival, out-of-plane offset of the target at arrival) or None."""
        r2 = target.orbit.position_at(t1 + T, frame)
        z2 = _dot(r2, h)
        sol = _lambert(mu_s, p1, tuple(x - z2 * y for x, y in zip(r2, h)), T, h)
        if sol is None:
            return None
        vi1 = tuple(a - b for a, b in zip(sol[0], _vel_at(home.orbit, t1, frame)))
        vi2 = tuple(a - b for a, b in zip(sol[1], _vel_at(target.orbit, t1 + T, frame)))
        return vi1, math.sqrt(_dot(vi1, vi1)), math.sqrt(_dot(vi2, vi2)), z2

    R1 = math.sqrt(_dot(r1, r1))

    def dv_total(vi1, vi2, z2, T):
        """Ejection + circular capture at pe_alt + the mid-course plane change (tilt z2/R2 at ~arrival speed)."""
        R2 = math.dist(target.orbit.position_at(t_dep + T, frame), (0, 0, 0))
        return math.sqrt(vi1 ** 2 + 2 * mu / r0) - math.sqrt(mu / r0) \
            + math.sqrt(vi2 ** 2 + 2 * mu_t / r_cap) - math.sqrt(mu_t / r_cap) \
            + abs(z2) / R2 * math.sqrt(mu_s * (2 / R2 - 2 / (R1 + R2)))

    # the exact Hohmann time of flight is the 180 deg Lambert singularity: scan the flight time and keep the
    # cheapest total (Duna: 278 d instead of 309, arrival v_inf 780 instead of 870; Eve 1: 184 d + ~410 m/s
    # plane change beats arriving at Eve's node at 238 d, v_inf 1423/2286)
    best = None
    for i in range(41):
        T = T_h * (0.6 + 0.02 * i)
        p = plan(t_dep, r1, T)
        if p and (best is None or dv_total(p[1], p[2], p[3], T) < best[0]):
            best = (dv_total(p[1], p[2], p[3], T), T, p)
    if best is None:
        say("Lambert found no transfer around the window; not planning")
        return False

    def at_T(T):
        p = plan(t_dep, r1, T)
        return (dv_total(p[1], p[2], p[3], T), T, p) if p else (math.inf, T, None)
    # the 2 % grid (2.3 d at Moho) steps over narrow minima: 5,268 at 113.3 d, 5,094 at 114.75 d
    step = 0.02 * T_h
    fine = _golden_min(at_T, max(0.6 * T_h, best[1] - step), min(1.4 * T_h, best[1] + step))
    if fine[0] < best[0]:
        say(f"flight time refined {best[1] / 21600:.2f} -> {fine[1] / 21600:.2f} d: ~{best[0]:.0f} -> ~{fine[0]:.0f} m/s",
            screen=False)
        best = fine
    total, T, (vi_req, vi_dep, vi_arr, z2) = best
    t_arr = t_dep + T
    dv = math.sqrt(vi_dep ** 2 + 2 * mu / r0) - math.sqrt(mu / r0)
    R2 = math.dist(target.orbit.position_at(t_arr, frame), (0, 0, 0))
    dv_pc = abs(z2) / R2 * math.sqrt(mu_s * (2 / R2 - 2 / (R1 + R2)))
    vi_hohmann = abs(math.sqrt(mu_s / R1) * (math.sqrt(2 * R2 / (R1 + R2)) - 1))
    day = 21600.0
    say(f"Lambert: flight {T / day:.0f} d (Hohmann {T_h / day:.0f}), departure v_inf {vi_dep:.0f} (Hohmann "
        f"{vi_hohmann:.0f}) -> ejection ~{dv:.0f} m/s, arrival v_inf {vi_arr:.0f}; {target_name} is "
        f"{z2 / 1e6:+.0f} Mm out of our plane at arrival (SOI {target.sphere_of_influence / 1e6:.0f} Mm), "
        f"plane change ~{dv_pc:.0f} m/s; ejection + capture + plane change ~{total:.0f} m/s")
    if vi_dep > 1.3 * vi_hohmann + 50:
        say(f"departure v_inf {vi_dep:.0f} >> Hohmann {vi_hohmann:.0f}: bad window geometry; not planning")
        return False
    t0 = ut() + 300
    node = v.control.add_node(t0, dv, 0, 0)
    c = _match_exit(node, home, frame, lambda t1, p1, T: (plan(t1, p1, T) or (None,))[0], t_arr,
                    [t0 + i * P / samples for i in range(samples)], req0=vi_req)
    if c > 20:
        say("cannot match the required departure velocity; node left for inspection")
        return False

    def pe_cost(n):
        """Periapsis error (km) + arrival v_inf / 10 (an off-tangent pass costs capture fuel), never into the air."""
        c = _node_cost(n, target, pe_alt)
        if home.has_atmosphere and n.orbit.periapsis_altitude < home.atmosphere_depth:
            c += 1e4
        enc = _encounter(n.orbit, target)
        return c + math.sqrt(mu_t / abs(enc[1].semi_major_axis)) / 10.0 if enc else c
    if _encounter(node.orbit, target) or abs(z2) < target.sphere_of_influence:
        # the in-plane path already passes through the SOI (Duna): shape the pass; else leave it for mid-course
        tune_node(node, pe_cost, steps=(("prograde", 2.0), ("ut", 10.0), ("normal", 2.0), ("radial", 1.0)))
    enc = _encounter(node.orbit, target)
    vi = math.sqrt(mu_t / abs(enc[1].semi_major_axis)) if enc else None
    say(f"encounter {enc[0] if enc else None}, arrival v_inf {vi}, dv {node.delta_v:.0f}")
    if vi and vi > 1.25 * vi_arr + 50:
        say(f"arrival v_inf {vi:.0f} >> planned {vi_arr:.0f}: off-tangent pass; node left for inspection")
        return False
    if not enc:
        # plane change where the lever arm is long: ~90 deg of true anomaly before arrival on the transfer ellipse
        e = abs(R1 - R2) / (R1 + R2)
        E = 2 * math.atan(math.sqrt((1 - e) / (1 + e)))
        t_pc = t_arr - (E - e * math.sin(E)) / math.pi * T
        say(f"no encounter by design ({target_name} {z2 / 1e6:+.0f} Mm out of plane): do `ksp correct "
            f"{target_name} --pe {pe_alt:.0f}` around UT {t_pc:.0f} ({(t_pc - ut()) / day:.0f} days from now), "
            f"expect ~{dv_pc:.0f} m/s")
    _approve(node, dv)
    execute_node(node)
    if not enc:
        return True
    enc = _encounter(v.orbit, target)  # a 1 m/s error in the ejection moved the Duna pass by ~12,000 km
    if not enc or abs(enc[0] - pe_alt) > 3000:
        return correct_course(target_name, pe_alt)
    return True


def _golden_min(f, a, b, n=20):
    """Golden-section search of f over [a, b]; f(x) -> tuple whose [0] is the cost. The best tuple evaluated."""
    g = (math.sqrt(5) - 1) / 2
    c, d = b - g * (b - a), a + g * (b - a)
    fc, fd = f(c), f(d)
    best = min(fc, fd, key=lambda r: r[0])
    for _ in range(n):
        if fc[0] < fd[0]:
            b, d, fd = d, c, fc
            c = b - g * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + g * (b - a)
            fd = f(d)
        best = min(best, fc, fd, key=lambda r: r[0])
    return best


def _match_exit(node, home, frame, plan, t_arr, seed_uts, req0=None,
                coarse=(("prograde", 10.0), ("ut", 30.0), ("normal", 5.0))):
    """Tune node (prograde, ut, normal) until the velocity with which KSP's own patch leaves home's SOI matches the
    Lambert requirement plan(t1, p1, T) -> v_inf vector (None if unsolvable). First pass against the requirement
    from home's centre (req0, or plan at the node time), seeded at the best of seed_uts; second pass from the real
    hand-over point and time: the SOI edge is 84 Mm from Kerbin / 85 Mm from Eve, 1-2 days later, and the speed
    there exceeds v_inf by 2 mu / r_SOI (9 % at Eve) - the second pass absorbs both. Returns the error left (m/s)."""
    def cost(n):
        time.sleep(0.04)  # let KSP recompute patches
        ex = _exit_velocity(n, home, frame)
        return math.dist(ex[0], cost.req) if ex else 1e6
    cost.req = req0 if req0 is not None else plan(node.ut, home.orbit.position_at(node.ut, frame), t_arr - node.ut)
    if cost.req is None:
        return 1e6
    seed = None
    for t in seed_uts:
        node.ut = t
        c = cost(node)
        if seed is None or c < seed[0]:
            seed = (c, t)
    node.ut = seed[1]
    say(f"best seed v_inf error {seed[0]:.0f} m/s at +{seed[1] - ut():.0f}s; tuning")
    c = tune_node(node, cost, steps=coarse)
    ex = _exit_velocity(node, home, frame)
    req = plan(ex[1], ex[2], t_arr - ex[1]) if ex else None
    if req is not None:
        cost.req = req
        c = tune_node(node, cost, steps=(("prograde", 2.0), ("ut", 10.0), ("normal", 2.0)))
    say(f"ejection tuned: v_inf error {c:.1f} m/s, {node.delta_v:.0f} m/s")
    return c


# ---------------------------------------------------------------- departure from an eccentric / inclined orbit

def _hyperbola_through(mu, r, u):
    """Velocity at position r of the escape hyperbola whose v_inf vector is u, the short way round (the body is not
    passed between r and the asymptote): (velocity, eccentricity, periapsis radius, true anomaly at r), or None if
    r and u are (anti)parallel. The plane is (r, u); the energy fixes a = -mu/u^2; e follows from
    r = p / (1 + e cos(nu_inf - theta)) with theta the angle from r to u and nu_inf = acos(-1/e)."""
    R, um = math.sqrt(_dot(r, r)), math.sqrt(_dot(u, u))
    rh, uh = _norm(r), _norm(u)
    th = math.acos(max(-1.0, min(1.0, _dot(rh, uh))))
    if th < 1e-4 or th > math.pi - 1e-4:
        return None
    W = _norm(_cross(rh, uh))
    a = -mu / um ** 2

    def radius(e):
        return -a * (e * e - 1) / (1 + e * math.cos(math.acos(-1 / e) - th))
    lo, hi = 1.0 + 1e-9, 1.0 + 1e-6
    while radius(hi) < R:
        hi = 1 + (hi - 1) * 2
        if hi > 1e6:
            return None
    for _ in range(100):
        mid = (lo + hi) / 2
        if radius(mid) < R:
            lo = mid
        else:
            hi = mid
    e = (lo + hi) / 2
    p = -a * (e * e - 1)
    nu = math.acos(-1 / e) - th
    k = math.sqrt(mu / p)
    Q = _cross(W, rh)
    vr, vt = k * e * math.sin(nu), k * (1 + e * math.cos(nu))
    return tuple(vr * x + vt * y for x, y in zip(rh, Q)), e, p / (1 + e), nu


def _kepler_of(o, mu=None, name=""):
    """kepler.Orbit from a kRPC Orbit (elements only, so the offline tests can build the same thing from numbers)."""
    return kepler.Orbit(mu if mu is not None else o.body.gravitational_parameter, o.semi_major_axis, o.eccentricity,
                 o.inclination, o.longitude_of_ascending_node, o.argument_of_periapsis, o.mean_anomaly_at_epoch,
                 o.epoch, name)


def plan_departure(ship, home, target, mu_sun, soi, t_from, t_to, t_hohmann=None, refine=4, max_dv=2500.0):
    """Pure planner (kepler.Orbit inputs, no kRPC) for leaving a highly eccentric orbit around home for target.
    A prograde burn at the periapsis is the cheap escape (Oberth), but its asymptote is bound to a cone of
    acos(1/e_hyp) (~25 deg) about the apoapsis direction, fixed in space (turning the apsis line costs ~v_pe/2 per
    radian anywhere on the orbit); the orbital plane can be turned about the apsis line for almost nothing at the
    apoapsis (Eve 1: 90 m/s there). So for each periapsis pass in [t_from, t_to] this finds the flight times T at
    which the Lambert departure v_inf lies exactly on that cone (the hyperbola through our periapsis is tangent
    there: root of its true anomaly at the burn), tilts the plane onto the asymptote, and refines the requirement to
    KSP's hand-over at the SOI edge (velocity there, not v_inf; 9 % faster at Eve). Eve 1's Hohmann window had the
    apoapsis 138 deg from Eve's prograde: unreachable; 8 passes later a 297-day 250 deg arc costs ~340 m/s in all.
    Returns candidates sorted by dv_tilt + dv_pe, each a dict (times in UT, angles in rad, m/s):
    t_pe, T, t_arr, tilt (signed, about the periapsis direction), inc/lan of the tilted plane, dv_tilt, tilt_burn
    (prograde, normal) at the apoapsis, dv_pe, pe_burn (prograde, radial, normal) at the periapsis, v_inf, exit
    (t, r, v relative to home at the SOI edge), arrival v_inf, helio (kepler.Orbit of the transfer)."""
    nrm, crs, dt, mag, Orbit = _norm, _cross, _dot, kepler._mag, kepler.Orbit
    mu = ship.mu
    P = ship.period
    r_pe, v_pe_vec = ship.state_at_nu(0)
    v_pe, v_ap = mag(v_pe_vec), mag(ship.state_at_nu(math.pi)[1])
    if t_hohmann is None:
        t_hohmann = math.pi * math.sqrt(((home.a + target.a) / 2) ** 3 / mu_sun)

    def requirement(t_dep, T, delta=(0.0, 0.0, 0.0)):
        """Lambert v_inf vector (plus the SOI hand-over correction delta) and the arrival v_inf, or None."""
        r1, r2 = home.position(t_dep), target.position(t_dep + T)
        v1 = home.velocity(t_dep)
        sol = _lambert(mu_sun, r1, r2, T, nrm(crs(r1, v1)))
        if sol is None:
            return None
        u = tuple(a - b + d for a, b, d in zip(sol[0], v1, delta))
        return u, mag(tuple(a - b for a, b in zip(sol[1], target.velocity(t_dep + T)))), sol

    def geometry(u):
        """Plane through the periapsis direction and the asymptote (motion from the periapsis towards u), the
        signed tilt to it about the periapsis direction, our velocity at the periapsis once tilted, the hyperbola."""
        Wn = crs(ship.P, nrm(u))
        if mag(Wn) < 1e-9:
            return None
        Wn = nrm(Wn)
        if dt(crs(Wn, ship.P), u) < 0:
            Wn = tuple(-x for x in Wn)
        alpha = math.atan2(dt(crs(ship.W, Wn), ship.P), dt(ship.W, Wn))
        hyp = _hyperbola_through(mu, r_pe, u)
        if hyp is None:
            return None
        return alpha, Wn, tuple(v_pe * x for x in crs(Wn, ship.P)), hyp

    def nu_at_burn(t_pe, T, delta=(0.0, 0.0, 0.0)):
        req = requirement(t_pe, T, delta)
        g = geometry(req[0]) if req else None
        return g[3][3] if g else None

    def solve_T(t_pe, lo, hi, delta=(0.0, 0.0, 0.0)):
        """Flight time in [lo, hi] at which the burn is tangential (true anomaly on the hyperbola = 0)."""
        flo, fhi = nu_at_burn(t_pe, lo, delta), nu_at_burn(t_pe, hi, delta)
        if flo is None or fhi is None or flo * fhi > 0:
            return None
        for _ in range(50):
            mid = (lo + hi) / 2
            fm = nu_at_burn(t_pe, mid, delta)
            if fm is None:
                return None
            if fm * flo <= 0:
                hi, fhi = mid, fm
            else:
                lo, flo = mid, fm
        return (lo + hi) / 2

    out = []
    t_pe = ship.time_of_nu(0, t_from)
    grid = [t_hohmann * (0.5 + 0.02 * i) for i in range(101)]
    while t_pe <= t_to:
        vals = [(T, nu_at_burn(t_pe, T)) if abs(T - t_hohmann) > 0.03 * t_hohmann else (T, None) for T in grid]
        for (T1, f1), (T2, f2) in zip(vals, vals[1:]):
            if f1 is None or f2 is None or f1 * f2 > 0 or abs(f1) > 1.0 or abs(f2) > 1.0:
                continue
            T = solve_T(t_pe, T1, T2)
            if T is None:
                continue
            # refine to the SOI hand-over: shift the requirement by (needed - predicted) exit velocity, re-solve T
            delta, res = (0.0, 0.0, 0.0), None
            for _ in range(refine + 1):
                T = solve_T(t_pe, T - 0.04 * t_hohmann, T + 0.04 * t_hohmann, delta) or T
                req = requirement(t_pe, T, delta)
                g = geometry(req[0]) if req else None
                if g is None:
                    break
                alpha, Wn, v0, (vh, e_h, rp_h, nu_h) = g
                hyp = Orbit.from_state(mu, r_pe, vh, t_pe)
                t_x = hyp.time_at_radius(soi, t_pe)
                if t_x is None:
                    break
                rx, vx = hyp.state(t_x)
                Rx = tuple(a + b for a, b in zip(home.position(t_x), rx))
                sol = _lambert(mu_sun, Rx, target.position(t_pe + T), t_pe + T - t_x, nrm(crs(Rx, home.velocity(t_x))))
                if sol is None:
                    break
                need = tuple(a - b for a, b in zip(sol[0], home.velocity(t_x)))
                d = tuple(a - b for a, b in zip(need, vx))
                res = (req, alpha, Wn, v0, vh, e_h, rp_h, nu_h, t_x, rx, vx, Rx, sol)
                if mag(d) < 0.05:
                    break
                delta = tuple(a + b for a, b in zip(delta, d))
            if res is None:
                continue
            req, alpha, Wn, v0, vh, e_h, rp_h, nu_h, t_x, rx, vx, Rx, sol = res
            dv_pe_vec = tuple(a - b for a, b in zip(vh, v0))
            dv_pe = mag(dv_pe_vec)
            dv_tilt = 2 * v_ap * abs(math.sin(alpha / 2))
            if dv_pe + dv_tilt > max_dv:
                continue
            rh = nrm(r_pe)
            helio = Orbit.from_state(mu_sun, Rx, tuple(a + b for a, b in zip(home.velocity(t_x), vx)), t_x, "transfer")
            tilted = Orbit.from_state(mu, r_pe, v0, t_pe)
            out.append(dict(
                t_pe=t_pe, T=T, t_arr=t_pe + T, tilt=alpha, inc=tilted.inc, lan=tilted.lan,
                dv_tilt=dv_tilt, tilt_burn=(v_ap * (math.cos(alpha) - 1), v_ap * math.sin(alpha)),
                dv_pe=dv_pe, pe_burn=(dt(dv_pe_vec, nrm(v0)), dt(dv_pe_vec, rh), dt(dv_pe_vec, Wn)),
                v_inf=mag(req[0]), u=req[0], nu_h=nu_h, pe_h=rp_h, exit=(t_x, rx, vx), exit_speed=mag(vx),
                arrival_v_inf=mag(tuple(a - b for a, b in zip(sol[1], target.velocity(t_pe + T)))),
                helio=helio, dv=dv_pe + dv_tilt))
        t_pe += P
    out.sort(key=lambda c: c["dv"])
    return out


def _describe_candidate(c, now, t_win=None):
    day = 21600.0
    when = f"{(c['t_pe'] - now) / day:.0f} d from now" + (f", window {(c['t_pe'] - t_win) / day:+.0f} d" if t_win else "")
    return (f"pe pass UT {c['t_pe']:.0f} ({when}): flight {c['T'] / day:.0f} d, tilt {math.degrees(c['tilt']):+.1f} deg "
            f"({c['dv_tilt']:.0f} m/s at the apoapsis) + ejection {c['dv_pe']:.0f} m/s = {c['dv']:.0f} m/s; "
            f"v_inf {c['v_inf']:.0f}, arrival v_inf {c['arrival_v_inf']:.0f}")


def depart_planet(target_name, pe_alt, at=None, max_arrival=None, horizon_days=800.0):
    """From a highly eccentric and/or inclined orbit around a planet, leave for another planet in two cheap burns:
    a plane tilt at the apoapsis (Eve 1 moves at 90 m/s there) that puts the periapsis direction and the required
    departure asymptote into one plane, then a prograde ejection at the periapsis (Oberth, 4.36 km/s). transfer_planet
    assumes a circular parking orbit and cannot: the asymptote of a periapsis burn is bound to a ~25 deg cone about the
    apoapsis direction, and that direction is fixed in space (turning the apsis line costs ~v_pe/2 per radian); at the
    Hohmann window Eve 1's apoapsis pointed 138 deg from Eve's prograde. plan_departure picks the periapsis pass and
    flight time at which a tangential periapsis burn is exactly what the Lambert transfer needs (Eve 1: 8 passes after
    the window, a 297-day 250 deg arc, ~340 m/s in all against ~1160 for ejecting from the apoapsis at the window).
    Run it twice: the first run plans and (after `ksp node`) burns the tilt at the apoapsis before the chosen pass -
    nodes far ahead are fine, execute_node warps; the second run, with the printed `--at UT`, plans the ejection at
    that periapsis. Then `correct TARGET --pe` far out as after transfer_planet. --plan stops at each tuned node.
    at: UT of the departure periapsis pass to use (nearest candidate); max_arrival: cap on the arrival v_inf (reentry
    heat) when choosing; the default choice is the cheapest within horizon_days."""
    mag, dt = kepler._mag, _dot
    v = vessel()
    target = sc().bodies[target_name]
    home = v.orbit.body
    sun = home.orbit.body
    frame = sun.non_rotating_reference_frame
    o = v.orbit
    now = ut()
    day = 21600.0
    if o.eccentricity < 0.3:
        say(f"eccentricity {o.eccentricity:.2f}: a near-circular orbit; use `transfer` (transfer_planet) instead")
        return False
    ship, home_k, target_k = _kepler_of(o, name=v.name), _kepler_of(home.orbit, name=home.name), \
        _kepler_of(target.orbit, name=target_name)
    # convention checks: the element-based propagation against KSP's own numbers (frame-independent scalars)
    t_pe_k = ship.time_of_nu(0, now + 60)
    t_pe_g = o.ut_at_true_anomaly(0)
    while t_pe_g < now + 60:
        t_pe_g += o.period
    if abs(t_pe_k - t_pe_g) > 60:
        say(f"WARNING: next periapsis by elements {t_pe_k:.0f} vs KSP {t_pe_g:.0f} ({t_pe_k - t_pe_g:+.0f} s): "
            f"shifting the mean anomaly to KSP's timing")
        ship.m0 -= ship.n * (t_pe_k - t_pe_g)
    t_win, T_h = planet_window(target_name, flight_time=True)
    ph, pt = home.orbit.position_at(t_win, frame), target.orbit.position_at(t_win, frame)
    ang_g = math.degrees(math.acos(max(-1.0, min(1.0, dt(ph, pt) / (mag(ph) * mag(pt))))))
    kh, kt = home_k.position(t_win), target_k.position(t_win)
    ang_k = math.degrees(math.acos(max(-1.0, min(1.0, dt(kh, kt) / (mag(kh) * mag(kt))))))
    if abs(ang_g - ang_k) > 1.0:
        say(f"REFUSED: {home.name}-{target_name} angle at the window {ang_k:.1f} (elements) vs {ang_g:.1f} (KSP) deg: "
            f"the element conventions differ; not planning")
        return False
    say(f"planning departures over the next {horizon_days:.0f} days (element check: periapsis {t_pe_k - t_pe_g:+.0f} s, "
        f"window angle {ang_k - ang_g:+.2f} deg)")
    cands = plan_departure(ship, home_k, target_k, sun.gravitational_parameter, home.sphere_of_influence,
                           now + 120, now + horizon_days * day, T_h)
    if max_arrival:
        cands = [c for c in cands if c["arrival_v_inf"] <= max_arrival]
    if not cands:
        say("no departure found (no flight time puts the Lambert asymptote on the periapsis cone); not planning")
        return False
    for c in cands[:5]:
        say("  " + _describe_candidate(c, now, t_win), screen=False)
    cand = min(cands, key=lambda c: abs(c["t_pe"] - at)) if at else cands[0]
    say("chosen: " + _describe_candidate(cand, now, t_win))
    if at and abs(cand["t_pe"] - at) > o.period / 2:
        say(f"REFUSED: no candidate near UT {at:.0f} (nearest {cand['t_pe']:.0f}); not planning")
        return False
    t_pe, t_arr = cand["t_pe"], cand["t_arr"]
    mu_s = sun.gravitational_parameter

    def plan(t1, p1, T1):
        """Lambert requirement in KSP's frame: v_inf vector from p1 at t1 to the target's real position at t_arr."""
        r2 = target.orbit.position_at(t1 + T1, frame)
        h = _norm(_cross(p1, _vel_at(home.orbit, t1, frame)))
        sol = _lambert(mu_s, p1, r2, T1, h)
        return tuple(a - b for a, b in zip(sol[0], _vel_at(home.orbit, t1, frame))) if sol else None

    rel = math.degrees(_rel_inc(o.inclination, o.longitude_of_ascending_node, cand["inc"], cand["lan"]))
    if rel > 0.2:
        # ---- step 1: the tilt at the apoapsis before the departure periapsis (the apsis line is the node line)
        t_ap = t_pe - o.period / 2
        if t_ap < now + 120:
            say(f"REFUSED: the apoapsis before that periapsis is past (UT {t_ap:.0f}); pick a later pass with --at")
            return False
        spd = speed_at(o, t_ap)
        alpha = cand["tilt"]
        pe_floor = o.periapsis_altitude - 2000

        def cost(n):
            time.sleep(0.03)
            low = max(0.0, pe_floor - n.orbit.periapsis_altitude)
            return math.degrees(_rel_inc(n.orbit.inclination, n.orbit.longitude_of_ascending_node, cand["inc"],
                                         cand["lan"])) + low / 100
        best = None
        for sign in (1, -1):  # KSP's normal sign vs our right-handed elements: let its own patch decide
            node = v.control.add_node(t_ap, spd * (math.cos(alpha) - 1), sign * spd * math.sin(alpha), 0)
            c = cost(node)
            node.remove()
            if best is None or c < best[0]:
                best = (c, sign)
        node = v.control.add_node(t_ap, spd * (math.cos(alpha) - 1), best[1] * spd * math.sin(alpha), 0)
        c = tune_node(node, cost, steps=(("normal", 1.0), ("prograde", 0.5), ("radial", 0.5)), min_step=0.002)
        expect = 2 * spd * abs(math.sin(alpha / 2))
        say(f"tilt {math.degrees(alpha):+.1f} deg at the apoapsis in {(t_ap - now) / day:.1f} d: {node.delta_v:.1f} m/s "
            f"(expected {expect:.0f}), plane error left {c:.3f} deg")
        # dry run of the ejection behind it: KSP's chained patch must reach the required exit velocity, else our
        # conventions are off and the tilt would be wasted (about 100 m/s)
        probe = v.control.add_node(t_pe, cand["dv_pe"], 0, 0)
        err = _match_exit(probe, home, frame, plan, t_arr, [t_pe], coarse=(("prograde", 5.0), ("ut", 10.0), ("normal", 2.0)))
        dv_probe = probe.delta_v
        probe.remove()
        say(f"dry run of the ejection after the tilt: v_inf error {err:.1f} m/s with {dv_probe:.0f} m/s "
            f"(planned {cand['dv_pe']:.0f})")
        if err > 50 or dv_probe > 1.5 * cand["dv_pe"] + 20:
            say("REFUSED: the ejection behind this tilt does not reproduce the plan; node left for inspection")
            raise Refused("departure plan not reproduced by KSP's patch")
        say(f"after the burn run: ksp depart {target_name} --pe {pe_alt:.0f} --at {t_pe:.0f} --plan")
        _approve(node, expect)
        execute_node(node)
        say(f"tilt done: inc {math.degrees(v.orbit.inclination):.2f} (want {math.degrees(cand['inc']):.2f}), "
            f"lan {math.degrees(v.orbit.longitude_of_ascending_node):.1f} (want {math.degrees(cand['lan']):.1f}); "
            f"next: ksp depart {target_name} --pe {pe_alt:.0f} --at {t_pe:.0f} --plan")
        return True

    # ---- step 2: the ejection at the periapsis
    if t_pe - now > 1.5 * o.period:
        say(f"the departure periapsis is {(t_pe - now) / day:.1f} d away: warping to the orbit before it")
        warp_to(t_pe - o.period)
    node = v.control.add_node(t_pe, cand["dv_pe"], 0, 0)
    c = _match_exit(node, home, frame, plan, t_arr, [t_pe + d for d in (-120.0, -60.0, 0.0, 60.0, 120.0)],
                    coarse=(("prograde", 5.0), ("ut", 10.0), ("normal", 2.0)))
    if c > 20:
        say("cannot match the required departure velocity; node left for inspection")
        return False
    enc = _encounter(node.orbit, target)
    if enc:
        # KSP already sees the encounter: shape its periapsis a little (an aim-point shift of ~1000 km)
        tune_node(node, lambda n: _node_cost(n, target, pe_alt), steps=(("prograde", 0.5), ("ut", 5.0), ("normal", 0.5), ("radial", 0.3)))
        enc = _encounter(node.orbit, target)
    vi = math.sqrt(target.gravitational_parameter / abs(enc[1].semi_major_axis)) if enc else None
    say(f"ejection {node.delta_v:.0f} m/s (planned {cand['dv_pe']:.0f}) -> encounter pe {enc[0] if enc else None}, "
        f"arrival v_inf {vi if vi else 'n/a'} (planned {cand['arrival_v_inf']:.0f}); mid-course: `ksp correct "
        f"{target_name} --pe {pe_alt:.0f}` a few days after leaving the SOI (expect a few m/s)")
    _approve(node, cand["dv_pe"])
    execute_node(node)
    return True


def correct_course(target_name, pe_alt, min_inc=None, inc_to=None):
    """Mid-course correction toward target periapsis pe_alt (small burn now + 120 s); min_inc: also tilt the
    arrival orbit to at least this inclination (cheap far out, e.g. for survey sites at high latitude);
    inc_to: aim for this arrival inclination (0..180, e.g. 25 to meet a prograde target; flipping from a
    retrograde pass means crossing an impact path, so seed from a grid first).
    Far out (craft around the Sun, no encounter or > 1 day to the SOI): a compass search (_far_search) from the zero
    node, the Lambert seed (no encounter) and a small prograde / retrograde burn, steps scaled to the lever arm (the
    aim point moves ~ dv x time to go), cost dv + periapsis error + inclination (_far_cost; with --inc-to a pass on
    the other side is ruled out, without it the present side is kept), dv capped at 3x the analytic estimate + 0.5.
    It takes minutes. Moho 1's plain tuner planned 390 m/s where 77 did; Eve 2's grid 30.8 m/s retrograde where 7.7
    did. Around a planet (moons) the older grid/tuner paths below still apply."""
    v = vessel()
    target = sc().bodies[target_name]
    node = v.control.add_node(ut() + 120, 0, 0, 0)
    cost = lambda n: _node_cost(n, target, pe_alt, min_inc, inc_to)
    dv_cost = lambda n: cost(n) + n.delta_v  # 1 m/s weighs like 1 km of periapsis or 5 deg of inclination
    expect = None
    far = None  # (step prograde/radial, step normal) of the far-out search
    cap = None
    lam = None
    by_design = False
    day = 21600.0
    inside = v.orbit.body.name == target_name
    enc0 = None if inside else _encounter(v.orbit, target)
    t_in = _t_entry(v.orbit, target) if enc0 else None
    far_out = not inside and v.orbit.body.orbit is None and v.orbit.body.name == target.orbit.body.name \
        and (enc0 is None or (t_in is not None and t_in - node.ut > day))
    if far_out:
        # around the Sun (Moho 1, Eve 2): KSP's patches need >= 0.3 s after a node edit, the old grid + tuner had no
        # dv term and no side (Eve 2: 30.8 m/s and a retrograde pass where 7.7 did): compass search from a few seeds
        seeds = [(0.0, 0.0, 0.0)]
        if enc0 is None:
            lam = _lambert_seed(node, target)
            if lam is None:
                node.remove()
                say("Lambert found no path to the target; not burning")
                return False
            expect, t_arr, vi, z2, flat = lam
            lever = t_arr - node.ut
            by_design = _encounter(node.orbit, target) is None and flat \
                and abs(z2) > 0.5 * target.sphere_of_influence  # the plane change is dear here: in-plane part now
            seeds.append((node.prograde, node.normal, node.radial))
            b_now, inc_now = None, None
        else:
            time.sleep(FAR_SETTLE)
            imp = _impact(node, target)
            vi = imp[2] if imp else math.sqrt(target.gravitational_parameter / abs(enc0[1].semi_major_axis))
            lever = t_in - node.ut
            b_now = math.sqrt(_dot(imp[0], imp[0])) if imp else 0.0
            inc_now = math.degrees(enc0[1].inclination)
        b = _aim_radius(target, pe_alt, vi)
        lev = _levers(v.orbit, target, lever)
        sp, sn = 0.1 * b / lev[0], 0.1 * b / lev[1]  # one step moves the aim point by ~b/10
        if b_now is not None:
            # the pe change in the plane + the turn around the aim ring (chord 2b sin(phi/2)) the inclination asks
            phi = abs(inc_now - inc_to) if inc_to is not None else \
                max(0.0, (min_inc or 0.0) - min(inc_now, 180 - inc_now))
            expect = abs(b_now - b) / lev[0] + 2 * b * math.sin(math.radians(min(phi, 180.0)) / 2) / lev[1]
        cap = 3 * expect + 0.5
        retro = inc_to > 90 if inc_to is not None else (inc_now > 90 if inc_now is not None else None)
        w_pe = max(0.02, 3000.0 / lever)  # a km of pe weighs >= 3x the dv that moves the aim point by a km
        say(f"far out ({lever / day:.1f} d to go): aim radius {b / 1000:.0f} km"
            + (f" (now {b_now / 1000:.0f}, inc {inc_now:.1f})" if b_now is not None else "")
            + f", estimate {expect:.2f} m/s, cap {cap:.2f}; steps {sp:.3f} / {sn:.3f} m/s, pe weight {w_pe:.3f}/km"
            + ("" if retro is None else f", pass must be {'retrograde' if retro else 'prograde'}"))
        if by_design:
            pass  # burn the in-plane Lambert seed as it is
        else:
            seeds += [(2 * sp, 0.0, 0.0), (-2 * sp, 0.0, 0.0)]  # small prograde / retrograde
            _far_search(node, target, pe_alt, seeds, (sp, sn, sp), cap, w_pe, min_inc, inc_to, retro)
    else:
        if not inside and enc0 is None and v.orbit.body.name == target.orbit.body.name:
            # no encounter around the target's parent (Moho 1 after a late ejection: closest approach 331,674 km): the
            # +-6 m/s grid never reaches the SOI and the tuner walks off (390 m/s planned); Lambert from the node instead
            moon = target.orbit.body.orbit is not None
            lam = _lambert_seed(node, target)
            if lam is None and not moon:
                node.remove()
                say("Lambert found no path to the target; not burning")
                return False
        if lam is not None:
            expect, t_arr, vi_arr, z2, flat = lam
            lever = t_arr - node.ut
            b = _aim_radius(target, pe_alt, vi_arr)
            lev = _levers(v.orbit, target, lever)
            if _encounter(node.orbit, target) is None and flat and abs(z2) > 0.5 * target.sphere_of_influence:
                by_design = True  # the plane change is dear here (near the node line): burn the in-plane part now
            elif _encounter(node.orbit, target) is None:
                # the two-body arc and KSP's patches disagree a little: pull the closest approach in (the dv term keeps
                # the tuner from pumping the orbit up)
                s = 0.5 * target.sphere_of_influence / lever
                say(f"Lambert seed has no encounter in KSP's prediction; tuning the closest approach (step {s:.2f} m/s)")
                tune_node(node, dv_cost, steps=(("prograde", s), ("normal", s), ("radial", s)), min_step=s / 50)
            if not by_design and _encounter(node.orbit, target):
                far = (0.1 * b / lev[0], 0.1 * b / lev[1])  # one step moves the aim point by ~b/10
            elif not by_design and moon:
                # around a planet the old coarse grid (a Mun flyby's deflection) is the fallback; around the Sun it
                # was the 390 m/s walk-off
                say("Lambert seed found no encounter; falling back to the coarse search")
                node.prograde, node.normal, node.radial = 0.0, 0.0, 0.0
                lam, expect = None, None
        elif enc0 and t_in and t_in - node.ut > day and (inc_to is not None or min_inc):
            # far out with an encounter: the aim-point seed below (built for turns inside the SOI, Eve 1) lost the
            # encounter on every trial from Duna 1's aphelion and the tuner then walked off to 80 m/s
            imp = _impact(node, target)
            vi = imp[2] if imp else math.sqrt(target.gravitational_parameter / abs(enc0[1].semi_major_axis))
            b = _aim_radius(target, pe_alt, vi)
            lev = _levers(v.orbit, target, t_in - node.ut)
            far = (0.1 * b / lev[0], 0.1 * b / lev[1])
            b_now = math.sqrt(_dot(imp[0], imp[0])) if imp else 0.0
            # the pe change in the plane + at most half a turn around the aim ring (chord 2b), each over its lever arm
            expect = abs(b_now - b) / lev[0] + 2 * b / lev[1]
            cap = 3 * expect + 0.5
            say(f"far out ({(t_in - node.ut) / day:.1f} d to the SOI): aim radius {b / 1000:.0f} km (now "
                f"{b_now / 1000:.0f}), estimate <= {expect:.2f} m/s; grid steps {far[0]:.3f} / {far[1]:.3f} m/s")
        elif inc_to is not None and (v.orbit.eccentricity > 1 if inside else enc0 is not None):
            # on the way in (inside the SOI or with an encounter ahead): a new arrival plane means turning the aim
            # point (impact vector b) around the incoming asymptote; Eve 1 needed ~80 m/s for 10 -> 90 deg inside the
            # SOI, far beyond the +-6 m/s grid below
            expect = _aim_point_seed(node, target, pe_alt, cost)
        elif inc_to is not None:
            # far out (heliocentric, Duna 1) 0.1 m/s moves the pass by ~3,500 km: a 0.5 m/s grid steps over the
            # whole target, so scan a fine grid as well
            best = None
            for g in (0.5, 0.05):
                for nm in [x * g for x in range(-12, 13)]:
                    for rd in [x * g for x in range(-12, 13)]:
                        node.prograde, node.normal, node.radial = 0.0, nm, rd
                        c = cost(node)
                        if best is None or c < best[0]:
                            best = (c, nm, rd)
            node.prograde, node.normal, node.radial = 0.0, best[1], best[2]
        if far:
            _far_grid(node, dv_cost, *far)
            tune_node(node, dv_cost, steps=(("prograde", far[0]), ("normal", far[1]), ("radial", far[0])),
                      min_step=far[0] / 8)
        elif lam is None:
            tune_node(node, cost, steps=(("prograde", 1.0), ("normal", 1.0), ("radial", 1.0)))
        if _encounter(node.orbit, target) is None and not inside and lam is None:
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

    def plane_later():
        """The plane where its lever arm is long: ~90 deg of true anomaly before arrival (transfer_planet's rule)."""
        o = v.orbit
        t90 = o.ut_at_true_anomaly(o.true_anomaly_at_ut(t_arr) - math.pi / 2)
        if not ut() < t90 < t_arr:  # already inside the last 90 deg
            t90 = ut()
        say(f"next: `ksp correct {target_name} --pe {pe_alt:.0f}` around UT {t90:.0f} "
            f"({(t90 - ut()) / day:.0f} days from now) for the plane")
        return True
    if by_design:
        say(f"no encounter by design: {target_name} {z2 / 1000:+.0f} km out of our plane at arrival (SOI "
            f"{target.sphere_of_influence / 1000:.0f} km); this burn fixes the in-plane miss only")
    elif enc is None and not inside:
        node.remove()
        say("no encounter reachable; not burning")
        return False
    if node.delta_v < 0.3:
        node.remove()
        return plane_later() if by_design else enc is not None
    if v.orbit.body.orbit is None and inc_to is None and min_inc is None and node.delta_v < 1.0:
        # around the Sun a few mm/s of burn error move the pass by 100s of km (Duna 1 chased 0.1 m/s trims for
        # 48 days): periapsis trims belong inside the target's SOI
        node.remove()
        if by_design:
            say("far out: an in-plane trim under 1 m/s is below the burn accuracy here; the plane burn takes it")
            return plane_later()
        say("far out: a trim under 1 m/s is below the burn accuracy here; do it inside the SOI")
        return enc is not None
    if v.orbit.body.orbit is None and node.delta_v > 20 and not math.isnan(v.orbit.time_to_soi_change):
        # Duna 1's return from the aphelion: the arrival point lay 180 deg ahead, on the line a normal burn turns
        # the plane about, so pulling Kerbin's 14 Mm out-of-plane pass in cost 80 m/s (~10 m/s 90 deg out)
        o = v.orbit
        frame = o.body.non_rotating_reference_frame
        t_arr = ut() + o.time_to_soi_change
        a, b = o.position_at(ut(), frame), o.position_at(t_arr, frame)
        ang = math.degrees(math.acos(max(-1.0, min(1.0, _dot(_norm(a), _norm(b))))))
        if ang > 135:
            nu = o.true_anomaly_at_ut(t_arr) - math.pi / 2
            t90 = o.ut_at_true_anomaly(nu)
            while t90 < ut():
                t90 += o.period
            dv = node.delta_v
            node.remove()
            raise Refused(f"{dv:.0f} m/s with the arrival {ang:.0f} deg ahead (plane changes are dear on "
                          f"the node line): correct ~90 deg before arrival, UT {t90:.0f}")
    if cap is not None and node.delta_v > cap:
        raise Refused(f"{node.delta_v:.2f} m/s is over 3x the far-out estimate ({expect:.2f}): the requested "
                      "inclination is dear from here (near the node line?); node left for inspection")
    _approve(node, expect or node.delta_v, pe_alt if v.orbit.body.name == target_name else None,
             allow_flip=inc_to is not None)
    execute_node(node, tol=0.05)
    if v.orbit.body.name != target.name:
        # far out a burn error of a few m/s moves the pass by 100s of km (Jool 1: pe -655 km): read it back
        warp_to(ut() + 60)
        time.sleep(0.5)
        enc = _encounter(v.orbit, target)
        floor = _pe_floor(target)
        say(f"60 s after the burn: {target_name} pe " + (f"{enc[0] / 1000:.1f} km" if enc else "none (no encounter)")
            + (f" -- BELOW the terrain + margin ({floor / 1000:.1f} km): trim it before `soi`"
               if enc and enc[0] < floor else ""))
    if by_design and enc is None:
        return plane_later()
    return enc is not None


def _t_entry(orbit, target):
    """UT at which this trajectory enters target's SOI (now if already inside), else None."""
    o, t = orbit, ut()
    while o.body.name != target.name:
        if o.next_orbit is None:
            return None
        t = ut() + o.time_to_soi_change
        o = o.next_orbit
    return t


def _aim_radius(target, pe_alt, vinf):
    """Impact parameter b (m) of a hyperbola at target with periapsis altitude pe_alt."""
    rp = target.equatorial_radius + pe_alt
    return rp * math.sqrt(1 + 2 * target.gravitational_parameter / (rp * vinf ** 2))


def _levers(orbit, target, t_go):
    """(in-plane, out-of-plane) lever arms (s): a burn dv now moves the arrival point by ~dv x lever. In the plane
    ~ the time to go; a normal burn only tilts the plane, so out of it at most 1/n of our orbit around the target's
    parent (and ~0 on the node line: the cap in correct_course catches that)."""
    p = _patch_around(orbit, target.orbit.body.name)
    out = p.period / (2 * math.pi) if p is not None and p.eccentricity < 1 else t_go
    return t_go, min(t_go, out)


def _far_grid(node, cost, sp, sn):
    """Two-level prograde x normal grid around the node's components (steps 4 sp x 4 sn over +-6, then sp x sn over
    +-4 around the best); leaves the best in place. Moho 1's hand grid (+-0.12 m/s in 0.01 steps) found pe 25-40 km
    on the prograde side where the tuner alone did not."""
    best = (cost(node), node.prograde, node.normal)
    for k, half in ((4.0, 6), (1.0, 4)):
        cp, cn = best[1], best[2]
        for i in range(-half, half + 1):
            for j in range(-half, half + 1):
                node.prograde, node.normal = cp + i * k * sp, cn + j * k * sn
                c = cost(node)
                if c < best[0]:
                    best = (c, node.prograde, node.normal)
    node.prograde, node.normal = best[1], best[2]
    say(f"far grid: cost {best[0]:.1f}, {node.delta_v:.2f} m/s", screen=False)
    return best[0]


def _lambert_seed(node, target):
    """Seed the node (burn at node.ut) for a craft around target's parent with no encounter. The arrival time is
    scanned over +-5 % around the next closest approach and a Hohmann-like flight time; two variants: straight to the
    target's position ("direct"), and to it projected onto our orbital plane ("in-plane", the plane left for a later
    burn, as transfer_planet does: near a 180 deg arc the direct one tilts the whole path). The direct one wins unless
    it costs > 1.2x the in-plane total (in-plane dv + a plane change ~90 deg before arrival) and the arc still to fly
    is > 120 deg. Moho 1: the plain tuner planned 390 m/s; the in-plane Lambert 77 (Moho 92 km out of our plane),
    KSP then showed an encounter (pe -188 km).
    Returns (dv now, arrival UT, arrival v_inf, z2, in_plane) or None."""
    v = vessel()
    o, par = v.orbit, target.orbit.body
    mu = par.gravitational_parameter
    frame = par.non_rotating_reference_frame
    t1 = node.ut
    r1, v1 = o.position_at(t1, frame), _vel_at(o, t1, frame)
    h = _norm(_cross(r1, v1))
    R1 = math.sqrt(_dot(r1, r1))

    def at(t2, flat):
        r2 = target.orbit.position_at(t2, frame)
        z2 = _dot(r2, h)
        zp = z2 if flat else 0.0
        r2p = tuple(x - zp * y for x, y in zip(r2, h))
        th = math.atan2(_dot(h, _cross(r1, r2p)), _dot(r1, r2p)) % (2 * math.pi)  # arc still to fly
        sol = _lambert(mu, r1, r2p, t2 - t1, h)
        if sol is None:
            return math.inf, t2, None, z2, None, th
        dv = tuple(a - b for a, b in zip(sol[0], v1))
        plane = 0.0
        if flat:
            # the later plane change, ~90 deg of arc before arrival (or now on a shorter arc): tilt the path so it
            # rises by z2 at arrival, at the speed there (the arrival speed over-counts inward transfers)
            d = min(th, math.pi / 2)
            tr = kepler.Orbit.from_state(mu, r1, sol[0], t1)
            rb = tr.radius_at_nu(tr.true_anomaly(t2) - d)
            vb = math.sqrt(max(0.0, mu * (2 / rb - 1 / tr.a)))
            tilt = math.atan2(abs(zp), math.sqrt(_dot(r2, r2)) * math.sin(d))
            plane = 2 * vb * math.sin(tilt / 2)
        return math.sqrt(_dot(dv, dv)) + plane, t2, dv, z2, sol[1], th

    centres = []
    try:
        tc = o.next_closest_approach(target.orbit).ut
        if tc > t1 + 600:
            centres.append(tc - t1)
    except Exception:  # no closest approach reported: the flight-time estimate alone
        pass
    centres.append(math.pi * math.sqrt(((R1 + target.orbit.semi_major_axis) / 2) ** 3 / mu))
    best = {}
    for flat in (True, False):
        for T0 in centres:
            rows = [at(t1 + T0 * (0.95 + 0.0025 * i), flat) for i in range(41)]
            b = min(rows, key=lambda r: r[0])
            if b[0] < math.inf:  # the 0.25 % grid can straddle a narrow minimum (transfer_planet's Moho lesson)
                d = 0.0025 * T0
                fine = _golden_min(lambda t, f=flat: at(t, f), max(t1 + 600, b[1] - d), b[1] + d)
                b = min(b, fine, key=lambda r: r[0])
            if flat not in best or b[0] < best[flat][0]:
                best[flat] = b
    if best[True][0] == math.inf and best[False][0] == math.inf:
        return None
    # deferring the plane only makes sense with > ~120 deg to go: else this is the plane burn (no endless deferral)
    flat = best[False][0] > 1.2 * best[True][0] + 5 and (best[True][5] > math.radians(120)
                                                         or best[False][0] == math.inf)
    tot, t2, dv, z2, v2, _th = best[flat]
    dvn = math.sqrt(_dot(dv, dv))
    vt = _vel_at(target.orbit, t2, frame)
    vinf = math.dist(v2, vt)
    day = 21600.0
    say(f"Lambert: direct {best[False][0]:.1f} m/s, in-plane {best[True][0]:.1f} m/s (incl. the plane later) -> "
        f"{'in-plane' if flat else 'direct'}: {dvn:.1f} m/s now, arrival in {(t2 - t1) / day:.1f} d, "
        f"v_inf {vinf:.0f}; {target.name} {z2 / 1000:+.0f} km out of our plane at arrival (SOI "
        f"{target.sphere_of_influence / 1000:.0f} km)" + (f", plane later ~{tot - dvn:.1f} m/s" if flat else ""))
    basis = {}
    for k in ("prograde", "normal", "radial"):  # KSP's node axes, whatever its handedness
        node.prograde, node.normal, node.radial = 0.0, 0.0, 0.0
        setattr(node, k, 1.0)
        basis[k] = node.burn_vector(frame)
    node.prograde, node.normal, node.radial = (_dot(dv, basis[k]) for k in ("prograde", "normal", "radial"))
    time.sleep(FAR_SETTLE)
    enc = _encounter(node.orbit, target)
    say(f"Lambert seed: prograde {node.prograde:.2f} normal {node.normal:.2f} radial {node.radial:.2f} -> "
        + (f"{target.name} pe {enc[0] / 1000:.0f} km" if enc else "no encounter in KSP's prediction"))
    return dvn, t2, vinf, z2, flat


def _impact(node, target):
    """(impact vector b, asymptote direction s, v_inf) of the node's predicted hyperbola at target, in the target's
    non-rotating frame, read off KSP's patch (inside the SOI: the node's own orbit)."""
    o = node.orbit
    t_ref = node.ut
    while o.body.name != target.name:
        if o.next_orbit is None:
            return None
        t_ref = ut() + o.time_to_soi_change + 60
        o = o.next_orbit
    frame = target.non_rotating_reference_frame
    r, vel = o.position_at(t_ref, frame), _vel_at(o, t_ref, frame)
    s = _norm(vel)  # far out the velocity is ~ the asymptote (Eve 1: 84 Mm, v 926 vs v_inf 815)
    return tuple(x - _dot(r, s) * y for x, y in zip(r, s)), s, math.sqrt(target.gravitational_parameter
                                                                         / abs(o.semi_major_axis))


def _solve_dv(node, target, b_want, h=0.5):
    """Least-norm (prograde, normal, radial) that moves the impact vector to b_want, from a numerical Jacobian of
    KSP's own patch prediction around the node's current components (straight-line b/t was far off from Kerbin
    orbit: Survey 1's Mun seed went to inc 167 instead of 90)."""
    base = (node.prograde, node.normal, node.radial)
    time.sleep(0.04)
    b0, sd, _ = _impact(node, target)
    flat = lambda v: tuple(x - _dot(v, sd) * y for x, y in zip(v, sd))  # only the plane across the asymptote
    cols = []
    for k in range(3):
        c = list(base)
        c[k] += h
        node.prograde, node.normal, node.radial = c
        time.sleep(0.04)
        bk = _impact(node, target)
        cols.append(flat(tuple((x - y) / h for x, y in zip(bk[0], b0))) if bk else (0.0, 0.0, 0.0))
    node.prograde, node.normal, node.radial = base
    d = flat(tuple(x - y for x, y in zip(b_want, b0)))
    # x = J^T (J J^T)^-1 d with J = [cols]; J J^T is rank 2 (nothing along the asymptote): regularise
    JJt = [[sum(cols[k][i] * cols[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    eps = 1e-9 * sum(JJt[i][i] for i in range(3))
    for i in range(3):
        JJt[i][i] += eps
    y = _solve3(JJt, d)
    return tuple(base[k] + _dot(cols[k], y) for k in range(3))


def _solve3(A, b):
    """Gaussian elimination for a 3x3 system."""
    M = [list(A[i]) + [b[i]] for i in range(3)]
    for i in range(3):
        p = max(range(i, 3), key=lambda r: abs(M[r][i]))
        M[i], M[p] = M[p], M[i]
        for r in range(3):
            if r != i and M[i][i] != 0:
                f = M[r][i] / M[i][i]
                M[r] = [x - f * y for x, y in zip(M[r], M[i])]
    return [M[i][3] / M[i][i] if M[i][i] else 0.0 for i in range(3)]


def _aim_point_seed(node, target, pe_alt, cost):
    """Seed a node that turns the hyperbola's plane about its incoming asymptote: for each new aim angle (10 deg
    steps) solve for the burn with a numerical Jacobian of the predicted impact vector (twice: re-linearised),
    judged by KSP's own patch (cost); the tuner finishes it. Returns the seed's dv (the estimate)."""
    b_old, s, vinf = _impact(node, target)
    b = _aim_radius(target, pe_alt, vinf)
    u1 = _norm(b_old)
    u2 = _cross(s, u1)
    best = None
    for k in range(36):
        phi = math.radians(10 * k)
        want = tuple(b * (math.cos(phi) * x + math.sin(phi) * y) for x, y in zip(u1, u2))
        node.prograde, node.normal, node.radial = 0.0, 0.0, 0.0
        try:
            for _ in range(2):
                node.prograde, node.normal, node.radial = _solve_dv(node, target, want)
        except (TypeError, ZeroDivisionError):
            continue  # a trial burn lost the encounter
        c = cost(node)
        if best is None or c < best[0]:
            best = (c, node.prograde, node.normal, node.radial, node.delta_v, 10 * k)
    if best is None:  # Duna 1 from the aphelion: every trial lost the encounter (TypeError below)
        node.prograde, node.normal, node.radial = 0.0, 0.0, 0.0
        say("aim-point seed: every trial lost the encounter; tuning from zero")
        return None
    node.prograde, node.normal, node.radial = best[1:4]
    say(f"aim-point seed: {best[4]:.0f} m/s (turn {best[5]} deg), cost {best[0]:.1f}")
    return best[4]


# highest terrain (m) per body: a periapsis below it may hit a peak (Jool 1's far-out trim left pe -655 km)
TERRAIN = {"Kerbin": 6767, "Mun": 7061, "Minmus": 5725, "Moho": 6818, "Eve": 7540, "Gilly": 6400, "Duna": 8264,
           "Ike": 12750, "Dres": 5700, "Laythe": 5900, "Vall": 7990, "Tylo": 11290, "Bop": 21750, "Pol": 5590,
           "Eeloo": 3900}


def _pe_floor(body, margin=1000.0):
    return TERRAIN.get(body.name, 10000) + margin


def _entry_pe(o):
    """(body, periapsis altitude) of the next SOI this orbit enters (not an escape to a parent), else None."""
    nxt = o.next_orbit
    if nxt is None or nxt.body.name in _ancestors(o.body):
        return None
    return nxt.body, nxt.periapsis_altitude


def warp_to_soi(force=False):
    v = vessel()
    t = v.orbit.time_to_soi_change
    if math.isnan(t) or t <= 0:
        say("no SOI change ahead")
        return False
    entry = _entry_pe(v.orbit)
    if entry and entry[1] < _pe_floor(entry[0]):
        why = (f"predicted periapsis at {entry[0].name} {entry[1] / 1000:.1f} km is below its terrain + margin "
               f"({_pe_floor(entry[0]) / 1000:.1f} km): raise it first (`correct {entry[0].name} --pe X`)")
        if not force:
            raise Refused(why + ", or `soi --force`")
        say(f"--force: {why}")
    body = v.orbit.body.name
    warp_to(ut() + t + 5)
    while v.orbit.body.name == body:
        time.sleep(0.5)
    say(f"now in {v.orbit.body.name} SOI, pe {v.orbit.periapsis_altitude:.0f} m")
    return True


def capture(target_apo=None, early=0.0):
    """At the periapsis of a hyperbolic/elliptic orbit, burn retrograde into a circular orbit
    (or an orbit with apoapsis target_apo). early: centre the burn this many seconds before the periapsis (Eve 2:
    the pe lies in Kerbin's shadow, the burn must end before the blackout). An uncrewed craft that has no link by
    the periapsis start is refused instead of drifting into a flyby; a link lost mid-burn does not pause it.
    Uncrewed (no kerbal in a command part), away from Kerbin: the link over the burn is forecast first and the burn
    moved earlier by itself when Kerbin would go behind the body during it (_capture_link)."""
    v = vessel()
    o = v.orbit
    mu = o.body.gravitational_parameter
    t_pe = ut() + o.time_to_periapsis
    t = t_pe - early
    if (o.eccentricity >= 1 or early) and t - ut() < 60:
        # already past the periapsis of a hyperbola (Minmus Lab 1's first capture never fired): burn now
        t = ut() + 60
    elif early:
        say(f"capture burn centred {early:.0f} s before the periapsis")

    def dv_at(tc):
        rp = o.radius_at(tc)
        v_now = math.sqrt(mu * (2 / rp - 1 / o.semi_major_axis))
        ra = rp if target_apo is None else o.body.equatorial_radius + target_apo
        return math.sqrt(mu * (2 / rp - 2 / (rp + ra))) - v_now
    if o.body.orbit is not None and o.body.name != "Kerbin" and not _crewed(v):
        t = _capture_link(v, o, t, t_pe, dv_at)
    burn_at(t, prograde=dv_at(t), capture_pe=t_pe)
    o = v.orbit
    say(f"captured: {o.periapsis_altitude:.0f} x {o.apoapsis_altitude:.0f} m around {o.body.name}")


def _crewed(v):
    """A kerbal in a command part: the throttle works without a CommNet link (without a Pilot only map node editing
    is locked, see _ensure_control)."""
    return any(p.crew for p in v.parts.with_module("ModuleCommand"))


def _ray_clearance(s, k, m, R):
    """Metres by which the segment from s (vessel) to k (Kerbin) passes outside the sphere (centre m, radius R);
    negative: blocked (pure)."""
    d = tuple(b - a for a, b in zip(s, k))
    L = math.sqrt(_dot(d, d))
    u = tuple(x / L for x in d)
    w = tuple(b - a for a, b in zip(s, m))
    tc = _dot(u, w)
    if tc <= 0:
        return math.sqrt(_dot(w, w)) - R
    if tc >= L:
        return math.dist(k, m) - R
    return math.sqrt(max(0.0, _dot(w, w) - tc * tc)) - R


def _sun_chain(body):
    """[(orbit, parent's non-rotating frame)] from body up to the Sun, for _chain_pos."""
    out = []
    while body.orbit is not None:
        out.append((body.orbit, body.orbit.body.non_rotating_reference_frame))
        body = body.orbit.body
    return out


def _chain_pos(chain, t):
    """Position at UT t relative to the Sun: the sum of each orbit's position around its parent (Orbit.position_at
    puts the parent where it is NOW, so a moon's position in the Sun's frame alone would be off; every non-rotating
    frame has the same axes)."""
    p = (0.0, 0.0, 0.0)
    for o, f in chain:
        p = tuple(a + b for a, b in zip(p, o.position_at(t, f)))
    return p


def _link_forecast(o, occluders):
    """f(t) -> (clearance m, body) of the straight line from the vessel (on patch o, in its body's frame) to Kerbin
    past the occluders (radius + highest terrain), the worst one (Moho 1's scratch occl.py, in code). Relays are not
    counted."""
    body = o.body
    frame = body.non_rotating_reference_frame
    cb, ck = _sun_chain(body), _sun_chain(sc().bodies["Kerbin"])
    occ = [(b, None if b.name == body.name else _sun_chain(b), b.equatorial_radius + TERRAIN.get(b.name, 0))
           for b in occluders]

    def f(t):
        pb = _chain_pos(cb, t)
        s = o.position_at(t, frame)
        k = tuple(a - b for a, b in zip(_chain_pos(ck, t), pb))
        worst = None
        for b, ch, R in occ:
            m = (0.0, 0.0, 0.0) if ch is None else tuple(a - c for a, c in zip(_chain_pos(ch, t), pb))
            c = _ray_clearance(s, k, m, R)
            if worst is None or c < worst[0]:
                worst = (c, b.name)
        return worst
    return f


def _blackout(link, t0, t1, step=5.0):
    """(UT the first blackout that meets [t0, t1] begins or None, closest clearance (m, body) sampled over the
    window). A blackout already running at t0 is traced back to its start (up to 6 h)."""
    n = max(1, int(math.ceil((t1 - t0) / step)))
    worst = None
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        c = link(t)
        if worst is None or c[0] < worst[0]:
            worst = c
        if c[0] > 0:
            continue
        hi, lo = t, t - (t1 - t0) / n
        while link(lo)[0] <= 0:
            hi, lo = lo, lo - step
            if t0 - lo > 21600:
                return lo, worst
        for _ in range(12):  # to ~1 ms of a 5 s step
            mid = (lo + hi) / 2
            if link(mid)[0] > 0:
                lo = mid
            else:
                hi = mid
        return hi, worst
    return None, worst


def _link_safe_centre(t, window, blackout, earliest, margin=25.0, tries=6):
    """Latest burn centre <= t whose burn window(t) -> (start, end) ends >= margin s before any blackout
    (blackout(t0, t1) -> UT the first blackout meeting [t0, t1] begins, or None); None if that needs a start before
    earliest (pure: unit-tested). The window is re-read after each shift: off the periapsis the burn grows."""
    for _ in range(tries):
        start, end = window(t)
        if start < earliest:
            return None
        tb = blackout(start, end + margin)
        if tb is None:
            return t
        t -= end + margin - tb + 1.0
    return None


def _capture_link(v, o, t, t_pe, dv_at, margin=25.0):
    """Uncrewed capture: predict the CommNet link over the burn [start, end] (ray to Kerbin vs the body's disc,
    and its parent's for a moon, from the predicted positions). A blackout inside it (Moho 1: Kerbin behind Moho
    from pe-10 s to pe+130 s, the second half of the burn) moves the burn earlier, as --early would, so that it ends
    >= margin s before the blackout; refused if that start is already past (now + 90 s) or the earlier retrograde
    burn drops the periapsis under the terrain / into the atmosphere. Returns the burn centre UT."""
    body = o.body
    par = body.orbit.body
    occl = [body] + ([par] if par.orbit is not None and par.name != "Kerbin" else [])
    link = _link_forecast(o, occl)

    def window(tc):
        dv = abs(dv_at(tc))
        s = tc - burn_lead(v, dv)
        return s, s + burn_time(v, dv)
    start, end = window(t)
    note = " (relays not counted: the direct line to Kerbin only)"
    tb, worst = _blackout(link, start, end + margin)
    if tb is None:
        say(f"link forecast over the burn ({start - t_pe:+.0f} to {end - t_pe:+.0f} s from the pe): clear, closest "
            f"{worst[0] / 1000:.0f} km past {worst[1]}" + note)
        return t
    tc = _link_safe_centre(t, window, lambda a, b: _blackout(link, a, b)[0], ut() + 90, margin)
    what = (f"link forecast: Kerbin blocked from {tb - t_pe:+.0f} s from the pe, inside the burn ({start - t_pe:+.0f} "
            f"to {end - t_pe:+.0f} s)" + note)
    if tc is None:
        raise Refused(what + f"; no burn start after now + 90 s ends {margin:.0f} s before it: raise the periapsis "
                             "(a later, higher pass), or capture with a pilot / relay")
    r, vel = _state(o, tc, body.non_rotating_reference_frame)
    sp = math.sqrt(_dot(vel, vel))
    dv0, dv1 = dv_at(t), dv_at(tc)
    pe = _peri(body.gravitational_parameter, r, tuple(x * (sp + dv1) / sp for x in vel))[0] - body.equatorial_radius
    floor = max(_pe_floor(body), body.atmosphere_depth if body.has_atmosphere else 0.0)
    s1, e1 = window(tc)
    if pe < floor:
        raise Refused(what + f"; burning early enough (centre {t_pe - tc:.0f} s before the pe) leaves the periapsis "
                             f"at ~{pe / 1000:.0f} km, under {floor / 1000:.0f} km: raise the periapsis first")
    say(what + f"; moved the burn earlier: centre {t_pe - tc:.0f} s before the pe (like --early {t_pe - tc:.0f}), "
               f"{s1 - t_pe:+.0f} to {e1 - t_pe:+.0f} s, ends {tb - e1:.0f} s before the blackout; "
               f"{abs(dv0):.0f} -> {abs(dv1):.0f} m/s, periapsis after ~{pe / 1000:.0f} km")
    return tc


def _plane(inc, lan):
    """(normal, ascending-node direction) of an orbital plane in a frame of our own (x = reference direction,
    z = reference normal). KSP's handedness doesn't matter as long as every orbit goes through this."""
    return ((math.sin(inc) * math.sin(lan), -math.sin(inc) * math.cos(lan), math.cos(inc)),
            (math.cos(lan), math.sin(lan), 0.0))


def _rel_inc(i1, l1, i2, l2):
    c = math.cos(i1) * math.cos(i2) + math.sin(i1) * math.sin(i2) * math.cos(l1 - l2)
    return math.acos(max(-1.0, min(1.0, c)))


def _ang(a, b):
    """Smallest difference between two angles (rad), in degrees."""
    return abs(math.degrees((a - b + math.pi) % (2 * math.pi) - math.pi))


def _t_at_arg(o, u):
    """Next UT (at least 60 s ahead) at which the argument of latitude on orbit o is u."""
    t = o.ut_at_true_anomaly(u - o.argument_of_periapsis)
    while t < ut() + 60:
        t += o.period
    return t


def wait_plane(inc, lan, lead=1.0, alt=80000):
    """On the pad: warp until the pad passes under a node of the plane (inc, lan in deg) and return the surface
    heading that launches into it. Northward launches put the pad at the ascending node, southward at the
    descending one; whichever comes first. The node ends up ~lead deg past the pad's longitude at liftoff
    (Polar Relay 1: 203.3 at liftoff -> LAN 204.1)."""
    v = vessel()
    body = v.orbit.body
    lat = math.radians(v.flight().latitude)
    rate = 360.0 / body.rotational_period

    def pad_long():
        o = v.orbit  # the pad's "orbit": lan + argpe + true anomaly = its inertial longitude
        return math.degrees(o.longitude_of_ascending_node + o.argument_of_periapsis + o.true_anomaly) % 360

    az = math.asin(max(-1.0, min(1.0, math.cos(math.radians(inc)) / math.cos(lat))))  # inertial azimuth, north
    opts = [((lan - lead - pad_long()) % 360 / rate, az), (((lan + 180) - lead - pad_long()) % 360 / rate, math.pi - az)]
    wait, az = min(opts)
    v_orb = math.sqrt(body.gravitational_parameter / (body.equatorial_radius + alt))
    v_rot = 2 * math.pi * body.equatorial_radius * math.cos(lat) / body.rotational_period
    heading = math.degrees(math.atan2(v_orb * math.sin(az) - v_rot, v_orb * math.cos(az))) % 360
    say(f"pad at {pad_long():.1f} deg; {'ascending' if az < math.pi / 2 else 'descending'} node in {wait:.0f}s, "
        f"heading {heading:.1f}")
    warp_to(ut() + wait)
    say(f"pad at {pad_long():.1f} deg (target {(lan if az < math.pi / 2 else lan + 180) % 360:.1f} - {lead})")
    return heading


def match_orbit(inc, lan, argpe, sma, ecc):
    """Reach an orbit given by its elements (deg, m) around the current body, e.g. a contract's "specific orbit":
    plane change on the node line, then burn at the future apoapsis for the periapsis height, then at the
    periapsis (placed at argpe) for the apoapsis. Cheap high around a moon (Minmus at 330 km: 67 m/s orbital)."""
    inc, lan, argpe = math.radians(inc), math.radians(lan), math.radians(argpe)
    v = vessel()
    mu = v.orbit.body.gravitational_parameter
    R = v.orbit.body.equatorial_radius
    rp, ra = sma * (1 - ecc), sma * (1 + ecc)

    o = v.orbit
    ri = _rel_inc(o.inclination, o.longitude_of_ascending_node, inc, lan)
    if math.degrees(ri) > 0.2:
        n1, a1 = _plane(o.inclination, o.longitude_of_ascending_node)
        line = _norm(_cross(n1, _plane(inc, lan)[0]))
        u = math.atan2(_dot(line, _cross(n1, a1)), _dot(line, a1))
        t = min((_t_at_arg(o, u + k * math.pi) for k in (0, 1)), key=lambda x: speed_at(o, x))  # the slower crossing
        spd = speed_at(o, t)

        pe_floor = o.periapsis_altitude - 2000  # the tuner's radial freedom once put Polar Relay 1's pe in the air

        def cost(n):
            time.sleep(0.03)
            low = max(0.0, pe_floor - n.orbit.periapsis_altitude)
            return math.degrees(_rel_inc(n.orbit.inclination, n.orbit.longitude_of_ascending_node, inc, lan)) + low / 100
        best = None
        for sign in (1, -1):
            node = v.control.add_node(t, -spd * (1 - math.cos(ri)), sign * 2 * spd * math.sin(ri / 2), 0)
            c = cost(node)
            node.remove()
            if best is None or c < best[0]:
                best = (c, sign)
        node = v.control.add_node(t, -spd * (1 - math.cos(ri)), best[1] * 2 * spd * math.sin(ri / 2), 0)
        tune_node(node, cost, steps=(("normal", 1.0), ("prograde", 0.5), ("radial", 0.5)))
        say(f"plane change {math.degrees(ri):.1f} deg: {node.delta_v:.1f} m/s, left {cost(node):.2f} deg")
        _approve(node, 2 * spd * math.sin(ri / 2))
        execute_node(node)

    # burn 1 at the future apoapsis: the far side (argpe) comes to the periapsis radius
    o = v.orbit
    t = _t_at_arg(o, argpe + math.pi)
    r1 = o.radius_at(t)
    dv = math.sqrt(mu * (2 / r1 - 2 / (r1 + rp))) - speed_at(o, t)

    def cost1(n):
        time.sleep(0.03)
        no = n.orbit
        return abs(no.radius_at_true_anomaly(argpe - no.argument_of_periapsis) - rp) / 1000
    node = v.control.add_node(t, dv, 0, 0)
    tune_node(node, cost1, steps=(("prograde", 1.0), ("radial", 1.0)))
    if node.delta_v > 2.0:  # below that it's burn-residual noise (Keo Relay 3: --plan stopped on 1.2, 0.7, ... trims)
        say(f"periapsis side to {rp - R:.0f} m: {node.delta_v:.1f} m/s")
        _approve(node, dv, rp - R)
        execute_node(node)
    else:
        node.remove()

    # burn 2 at argpe: raise the apoapsis
    o = v.orbit
    t = _t_at_arg(o, argpe)
    r2 = o.radius_at(t)
    dv = math.sqrt(mu * (2 / r2 - 2 / (r2 + ra))) - speed_at(o, t)

    def cost2(n):
        time.sleep(0.03)
        no = n.orbit
        # argPe only counts for eccentric targets (the contract ignores it below e 0.05); without the inclination
        # term the tuner flipped Keo Relay 2 retrograde (1602 m/s) to please the argPe of a near-circle
        return (abs(no.periapsis - rp) + abs(no.apoapsis - ra)) / 1000 \
            + (0.2 * _ang(no.argument_of_periapsis, argpe) if ecc >= 0.05 else 0.0) \
            + 10 * math.degrees(_rel_inc(no.inclination, no.longitude_of_ascending_node, inc, lan))
    node = v.control.add_node(t, dv, 0, 0)
    tune_node(node, cost2, steps=(("prograde", 1.0), ("radial", 1.0), ("ut", 20.0)))
    say(f"apoapsis to {ra - R:.0f} m: {node.delta_v:.1f} m/s")
    _approve(node, dv, rp - R)
    execute_node(node)

    if abs(v.orbit.periapsis - rp) > 0.01 * rp:  # Polar Relay 1 came out 13 % low: fix it at the apoapsis
        change_periapsis(rp - R)
    o = v.orbit
    say(f"orbit pe {o.periapsis_altitude:.0f} (want {rp - R:.0f}) ap {o.apoapsis_altitude:.0f} (want {ra - R:.0f}) "
        f"inc {math.degrees(o.inclination):.2f} (want {math.degrees(inc):.2f}) "
        f"lan {math.degrees(o.longitude_of_ascending_node):.1f} (want {math.degrees(lan):.1f}) "
        f"argpe {math.degrees(o.argument_of_periapsis):.1f} (want {math.degrees(argpe):.1f})")


def return_to_parent(pe_alt=30000):
    """From orbit around a moon, burn so the orbit after leaving the SOI has periapsis pe_alt at the parent."""
    v = vessel()
    moon = v.orbit.body
    parent = moon.orbit.body
    mu = moon.gravitational_parameter
    r = v.orbit.semi_major_axis
    v_circ = math.sqrt(mu / r)
    v_esc = math.sqrt(2 * mu / r)
    # expected: the v_inf that drops the parent periapsis from the moon's orbit to pe_alt (Hohmann), from here;
    # (v_esc - v_circ) alone read 40 m/s for Rescue 4's 224 m/s Minmus return and the gate refused it
    mu_p, r_m, r_p = parent.gravitational_parameter, moon.orbit.semi_major_axis, parent.equatorial_radius + pe_alt
    v_inf = math.sqrt(mu_p / r_m) - math.sqrt(mu_p * 2 * r_p / (r_m * (r_m + r_p)))
    expect = math.sqrt(v_inf ** 2 + v_esc ** 2) - v_circ

    def cost(n):
        """Periapsis error (km); a retrograde arrival is the other, dearer root (MS2: v_inf 313 instead of 229,
        229 m/s instead of 163, and a hotter entry against the atmosphere's rotation)."""
        time.sleep(0.04)
        enc = _encounter(n.orbit, parent)
        if not enc:
            return 1e6
        return abs(enc[0] - pe_alt) / 1000.0 + (1e4 if enc[1].inclination > math.pi / 2 else 0.0)
    # seed with the expected size (a barely-escaping seed picked its burn time almost at random)
    period = v.orbit.period
    node = v.control.add_node(ut() + 120, expect, 0, 0)
    best = None
    for i in range(48):
        node.ut = ut() + 120 + period * i / 48
        c = cost(node)
        if best is None or c < best[0]:
            best = (c, node.ut)
    node.ut = best[1]
    tune_node(node, cost, steps=(("prograde", 5.0), ("ut", 30.0)))
    enc = _encounter(node.orbit, parent)
    say(f"return burn {node.delta_v:.0f} m/s -> {parent.name} pe {enc[0] if enc else None}, "
        f"inc {math.degrees(enc[1].inclination) if enc else None}")
    _approve(node, expect)
    execute_node(node)


# ---------------------------------------------------------------- landing / takeoff (airless bodies)

def _arm_chutes(v):
    for c in v.parts.parachutes:
        try:
            if not _chute_deployed(c):
                c.arm()
        except Exception:
            pass


def _descending(v):
    o = v.orbit
    return v.situation.name not in ("landed", "splashed") and \
        o.periapsis_altitude < (o.body.atmosphere_depth if o.body.has_atmosphere else 0)


def _fallback_descent():
    """Hold retrograde, arm every chute, powered descent to touchdown (what saved Valentina at Duna)."""
    v = vessel()
    fl = v.flight(v.orbit.body.reference_frame)
    ap = v.auto_pilot
    ap.reference_frame = v.surface_velocity_reference_frame
    ap.target_direction = (0, -1, 0)
    ap.engaged = True
    if v.orbit.body.has_atmosphere:
        _arm_chutes(v)
    _powered_descent(v, fl, ap)


def _fallback_chutes():
    """Arm every chute (they open when safe), force them open low down, wait for touchdown."""
    v = vessel()
    fl = v.flight(v.orbit.body.reference_frame)
    _arm_chutes(v)
    while v.situation.name not in ("landed", "splashed"):
        if fl.surface_altitude < 2500:
            for c in v.parts.parachutes:
                try:
                    c.deploy()
                except Exception:
                    pass
        time.sleep(1)
    say(f"{v.situation.name}! {v.name}")


def _contained(fallback):
    """A crewed entry or landing must not die on one RPC error (Duna 1's land_atmo stopped at 28 km on a kRPC
    chute exception; an ad-hoc script saved Valentina). On an exception while coming down: log it and fly the
    fallback, retried a few times. Still in a safe orbit: re-raise."""
    def wrap(fn):
        @functools.wraps(fn)
        def run(*a, **kw):
            try:
                return fn(*a, **kw)
            except Exception as e:
                err = e
            for _ in range(5):
                try:
                    coming_down = _descending(vessel())
                except Exception:
                    coming_down = False
                if not coming_down:
                    raise err
                say(f"{fn.__name__} failed ({err.__class__.__name__}: {str(err)[:60]}): {fallback.__name__}")
                try:
                    return fallback()
                except Exception as e:
                    err = e
                    time.sleep(0.5)
            raise err
        return run
    return wrap


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


def find_point(lat, lon, tol_km=2.0, orbits=20, step=5.0):
    """Earliest UT when the ground track passes within tol_km of (lat, lon) (e.g. a contract waypoint); the
    closest pass if none is that close."""
    v = vessel()
    body = v.orbit.body
    track = _track(v)
    R = body.equatorial_radius

    def dist(p):
        a, b = math.radians(p[0]), math.radians(lat)
        c = math.sin(a) * math.sin(b) + math.cos(a) * math.cos(b) * math.cos(math.radians(p[1] - lon))
        return R * math.acos(max(-1.0, min(1.0, c))) / 1000.0
    t0 = ut()
    best = None
    t = t0 + 120
    while t < t0 + orbits * v.orbit.period:
        d = dist(track(t))
        if best is None or d < best[0]:
            best = (d, t)
        if d < tol_km:
            # refine to the closest point of this pass
            while dist(track(t + 1)) < d:
                t += 1
                d = dist(track(t))
            best = (d, t)
            break
        t += step
    say(f"closest pass {best[0]:.1f} km from ({lat:.2f}, {lon:.2f}) in {best[1] - t0:.0f} s "
        f"(biome {_biome(body, *track(best[1]))}, slope {_slope(body, *track(best[1])):.1f} deg)")
    return best[1]


@_contained(_fallback_descent)
def land(safety=1.3, final_speed=1.5, max_decel=3.0, biomes=None, max_slope=5.0, orbits=8, at=None):
    """Land on an airless body from a low orbit: kill horizontal speed, then a throttled suicide burn.
    biomes: first wait for a pass over one of these biomes with gentle terrain; at: (lat, lon) to land near."""
    t = None
    if at:
        t = find_point(at[0], at[1], orbits=max(orbits, 20))
    elif biomes:
        t = find_site(biomes, max_slope, orbits=orbits)
        if t is None:
            say(f"no site under {max_slope} deg in {biomes} within {orbits} orbits")
            return False
    v = vessel()
    _antennas(v, False, panels_only=True)  # panels break on touchdown; antennas stay (a probe needs its link)
    body = v.orbit.body
    fl = v.flight(body.reference_frame)
    start = None
    if t is not None:
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


@_contained(_fallback_descent)
def land_atmo(pe_alt=5000, burn_alt=12000, ignore_link=False):
    """Land on a body with a thin atmosphere (Duna) from a low orbit: deorbit burn to periapsis pe_alt,
    hold surface retrograde through entry, arm every parachute (they open when safe), and fly the powered
    descent below burn_alt. Its own deorbit burn (from above the atmosphere) is checked like `deorbit`'s: the
    periapsis ground point, refused for an uncrewed craft with Kerbin < 20 deg up there unless ignore_link."""
    v = vessel()
    body = v.orbit.body
    fl = v.flight(body.reference_frame)
    ap = v.auto_pilot
    if v.orbit.periapsis_altitude > pe_alt + 5000 and fl.mean_altitude > body.atmosphere_depth:
        est = _retro_dv(v.orbit, ut(), pe_alt)
        if est and v.orbit.periapsis_altitude >= body.atmosphere_depth:  # else it comes down anyway
            _check_pe_link(v, v.orbit, ut(), est[0], ignore_link)
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
                if not _chute_deployed(c):
                    c.arm()
            armed = True
            say(f"{len(chutes)} chutes armed at {fl.mean_altitude:.0f} m, {fl.speed:.0f} m/s")
        time.sleep(0.2)
    if not armed:
        for c in chutes:
            if not _chute_deployed(c):
                c.arm()
    say(f"powered descent from {fl.surface_altitude:.0f} m AGL at {fl.speed:.0f} m/s")
    _powered_descent(v, fl, ap)


def _chute_deployed(c, default=False):
    """kRPC's Parachute.deployed throws a NullReferenceException for chutes that were staged in vacuum (Duna 1's
    Mk2-Rs shared the lander engine's stage and went active with it at capture): land_atmo died at 28 km."""
    try:
        return c.deployed
    except Exception:
        return default


def _deorbit_now(v, pe_alt, bt=None):
    """Retrograde burn right now until the periapsis is at pe_alt. Refused without thrust: with the engine gone
    (Eve 2's lander drops its Terrier) the old loop sat at throttle 1 forever; also stops when the thrust ends
    mid-burn or the burn runs 3x its estimate (no link = throttle locked)."""
    if v.available_thrust <= 0:
        raise Refused(f"no thrust on {v.name} (stage {v.control.current_stage}): stage the engine first")
    if bt is None:
        est = _retro_dv(v.orbit, ut(), pe_alt)
        bt = burn_time(v, est[0]) if est else 0.0
    ap = v.auto_pilot
    ap.reference_frame = v.orbital_reference_frame
    ap.target_direction = (0, -1, 0)
    ap.engaged = True
    _wait_pointing(ap)
    say(f"deorbit to pe {pe_alt:.0f} m")
    t_end = time.time() + 3 * bt + 60
    no_thrust = None
    while v.orbit.periapsis_altitude > pe_alt:
        pe = v.orbit.periapsis_altitude
        if v.available_thrust <= 0:
            no_thrust = no_thrust or time.time()
            if time.time() - no_thrust > 3:
                v.control.throttle = 0.0
                raise Refused(f"out of thrust at pe {pe:.0f} m (wanted {pe_alt:.0f})")
        else:
            no_thrust = None
        if time.time() > t_end:
            v.control.throttle = 0.0
            raise Refused(f"deorbit burn still running after {3 * bt + 60:.0f} s (control {v.control.state.name}), "
                          f"pe {pe:.0f} m: stopped")
        v.control.throttle = min(1.0, max(0.05, (pe - pe_alt) / 20000))
        time.sleep(0.05)
    v.control.throttle = 0.0


def _peri(mu, r, vel):
    """(periapsis radius, eccentricity vector) of the state r, vel."""
    R, V2, rv = math.sqrt(_dot(r, r)), _dot(vel, vel), _dot(r, vel)
    ev = tuple(((V2 - mu / R) * x - rv * y) / mu for x, y in zip(r, vel))
    e = math.sqrt(_dot(ev, ev))
    h2 = _dot(_cross(r, vel), _cross(r, vel))
    return h2 / mu / (1 + e), ev


def _state(o, t, frame):
    r = o.position_at(t, frame)
    a, b = o.position_at(t - 0.5, frame), o.position_at(t + 0.5, frame)
    return r, tuple(y - x for x, y in zip(a, b))


def _retro_dv(o, t, pe_alt):
    """(Δv, new periapsis direction) of a pure retrograde burn at UT t that puts the periapsis at pe_alt
    (bisection on the speed, body's non-rotating frame); None if the periapsis is already there."""
    mu = o.body.gravitational_parameter
    r, vel = _state(o, t, o.body.non_rotating_reference_frame)
    want = o.body.equatorial_radius + pe_alt
    if _peri(mu, r, vel)[0] <= want:
        return None
    lo, hi = 0.0, 1.0
    for _ in range(50):
        k = (lo + hi) / 2
        if _peri(mu, r, tuple(x * (1 - k) for x in vel))[0] > want:
            lo = k
        else:
            hi = k
    return hi * math.sqrt(_dot(vel, vel)), _peri(mu, r, tuple(x * (1 - hi) for x in vel))[1]


def _in_plane(d, h):
    return _norm(tuple(x - _dot(d, h) * y for x, y in zip(d, h)))


def _plane_angle(a, b, h):
    """Angle (deg, -180..180) from a to b about h, positive in the direction of motion when h = r x v."""
    return math.degrees(math.atan2(_dot(h, _cross(a, b)), _dot(a, b)))


def _toward(k, sd, h, deg):
    """k rotated deg about h towards sd (negative: away from it); pure. release_ut used
    copysign(radians(sunward), side), which dropped the sign of sunward: an anti-sunward offset came out sunward."""
    return kepler.rotate(k, h, math.radians(deg) * math.copysign(1.0, _plane_angle(k, sd, h)))


def _elevation(up, d):
    """Degrees of direction d above the horizon whose zenith is up (pure)."""
    return math.degrees(math.asin(max(-1.0, min(1.0, _dot(_norm(up), _norm(d))))))


def _pe_ground(o, t, dv):
    """Where a retrograde burn of dv (impulsive, at UT t on orbit o) puts the periapsis: (pe UT, lat, lon in the
    body's rotating frame at that UT, terrain height, Kerbin's and the Sun's elevation there in deg; Kerbin None at
    Kerbin). Moho 1's site search (scratch site.py) needed Kerbin > 20 deg up at touchdown for the link."""
    body = o.body
    frame = body.non_rotating_reference_frame
    r, vel = _state(o, t, frame)
    sp = math.sqrt(_dot(vel, vel))
    k = kepler.Orbit.from_state(body.gravitational_parameter, r, tuple(x * (1 - dv / sp) for x in vel), t)
    t_pe = k.time_of_nu(0.0, after=t)
    p = k.position(t_pe)
    q = sc().transform_position(p, frame, body.reference_frame)
    lat = body.latitude_at_position(q, body.reference_frame)
    lon = (body.longitude_at_position(q, body.reference_frame) - math.degrees(body.rotational_speed) * (t_pe - ut())
           + 180) % 360 - 180
    pb = _chain_pos(_sun_chain(body), t_pe)
    sun = _elevation(p, tuple(-a - b for a, b in zip(pb, p)))
    ker = None
    if body.name != "Kerbin":
        pk = _chain_pos(_sun_chain(sc().bodies["Kerbin"]), t_pe)
        ker = _elevation(p, tuple(a - b - c for a, b, c in zip(pk, pb, p)))
    return t_pe, lat, lon, body.surface_height(lat, lon), ker, sun


def _check_pe_link(v, o, t, dv, ignore_link=False, min_elev=20.0):
    """Print the predicted periapsis ground point of a deorbit burn (dv at UT t) with Kerbin's and the Sun's
    elevation there. Refused when Kerbin is under min_elev deg at the pe of an uncrewed craft (the landing and its
    science need the link), unless ignore_link or --plan (which says it would be)."""
    t_pe, lat, lon, h, ker, sun = _pe_ground(o, t, dv)
    body = o.body
    say(f"predicted periapsis: UT {t_pe:.0f} ({(t_pe - t) / 60:.0f} min after the burn) over {lat:.2f}, {lon:.2f} "
        f"(terrain {h:.0f} m, {_biome(body, lat, lon)}); " + (f"Kerbin {ker:.0f} deg up, " if ker is not None else "")
        + f"Sun {sun:.0f} deg up" + (" (drag ends the path before the pe)" if body.has_atmosphere else ""))
    if ker is None or ker >= min_elev or _crewed(v):
        return
    why = f"Kerbin only {ker:.0f} deg up at the periapsis (< {min_elev:.0f}): no link for the landing"
    if ignore_link:
        say(f"--ignore-link: {why}")
    elif PLAN_ONLY:
        say(f"WARNING: {why}; the burn will be refused without --ignore-link")
    else:
        raise Refused(why + " (pick another release point, or --ignore-link)")


def release_ut(v, under, sunward=0.0, pe_alt=0.0, angle=180.0, lead=180.0):
    """Next UT (>= now + lead) at which the vessel is `angle` deg (along its motion) from the direction of body
    `under` seen from our body, rotated `sunward` deg towards the Sun, both projected into our orbit plane
    (non-rotating frame; the directions are taken when the entry comes, half an orbit of pe_alt later). A
    retrograde burn there (angle 180) puts the new periapsis under that direction (within ~e x (1-e') rad:
    < 1 deg from a near-circular orbit). Eve 2's lander: `under` Kerbin, 30 deg sunward (Kerbin up at the
    entry and for hours after the landing, daylight). Returns (UT, deg from the target to the new periapsis)."""
    o, body = v.orbit, v.orbit.body
    s = sc()
    other, sun = s.bodies[under], s.bodies["Sun"]
    frame, sframe = body.non_rotating_reference_frame, sun.non_rotating_reference_frame
    t0 = ut() + lead
    r0, v0 = _state(o, t0, frame)
    h = _norm(_cross(r0, v0))
    # coast from the release to the entry: half an orbit of (r, R + pe_alt)
    coast = math.pi * math.sqrt(((math.sqrt(_dot(r0, r0)) + body.equatorial_radius + pe_alt) / 2) ** 3
                                / body.gravitational_parameter)
    bo, oo = body.orbit, other.orbit

    def target(t):
        pb = bo.position_at(t + coast, sframe)
        d_o = s.transform_direction(tuple(b - a for a, b in zip(pb, oo.position_at(t + coast, sframe))), sframe, frame)
        d_s = s.transform_direction(tuple(-a for a in pb), sframe, frame)
        return _toward(_in_plane(d_o, h), _in_plane(d_s, h), h, sunward)

    def g(t):
        return (_plane_angle(target(t), o.position_at(t, frame), h) - angle + 180) % 360 - 180

    n = 72
    step = o.period / n
    ta, ga = t0, g(t0)
    for i in range(1, n + 2):
        tb = t0 + i * step
        gb = g(tb)
        if ga < 0 <= gb and gb - ga < 90:
            break
        ta, ga = tb, gb
    else:
        raise Refused(f"no point {angle:.0f} deg from {under} found on this orbit")
    for _ in range(40):
        tm = (ta + tb) / 2
        if g(tm) < 0:
            ta = tm
        else:
            tb = tm
    est = _retro_dv(o, tb, pe_alt)
    off = _plane_angle(target(tb), _in_plane(est[1], h), h) if est else float("nan")
    return tb, off


def deorbit(pe_alt, at=None, under=None, sunward=0.0, ignore_link=False):
    """Retrograde burn until the periapsis is at pe_alt: now, at UT `at`, or at release_ut(under, sunward) (the new
    periapsis under that body's direction). Node-less: the burn stops on the periapsis itself. Then coast: nothing
    warps to the atmosphere here (Eve 2: drop the deorbit stage, `inflate`, arm the chutes first; `reentry`).
    Prints the predicted periapsis ground point; an uncrewed craft is refused with Kerbin < 20 deg up there
    (_check_pe_link) unless ignore_link."""
    v = vessel()
    o = v.orbit
    if at is not None and under is not None:
        raise Refused("give --at or --under, not both")
    if under is not None:
        at, off = release_ut(v, under, sunward, pe_alt)
        say(f"release point: 180 deg from {under}" + (f" rotated {sunward:.0f} deg sunward" if sunward else "")
            + f", UT {at:.0f} (in {(at - ut()) / 3600:.2f} h); the new periapsis lies {off:+.1f} deg from that direction")
    t = ut() if at is None else at
    if t < ut() - 10:
        raise Refused(f"UT {t:.0f} is {ut() - t:.0f} s in the past")
    est = _retro_dv(o, max(t, ut()), pe_alt)
    if est is None:
        say(f"periapsis {o.periapsis_altitude:.0f} m is already below {pe_alt:.0f} m: nothing to burn")
        return
    dv = est[0]
    if v.available_thrust <= 0:
        raise Refused(f"no thrust on {v.name} (stage {v.control.current_stage}): stage the engine first "
                      f"({dv:.0f} m/s needed)")
    bt = burn_time(v, dv)
    say(f"deorbit: {dv:.0f} m/s retrograde, ~{bt:.0f} s, in {t - ut():.0f} s -> pe {pe_alt / 1000:.1f} km "
        f"(now {o.periapsis_altitude / 1000:.1f} x {o.apoapsis_altitude / 1000:.1f} km around {o.body.name})")
    _check_pe_link(v, o, max(t, ut()), dv, ignore_link)
    if PLAN_ONLY:
        raise Planned(f"deorbit {dv:.0f} m/s at UT {t:.0f} (in {t - ut():.0f} s) to pe {pe_alt:.0f} m")
    _ensure_control(v)
    if at is not None:
        ap = v.auto_pilot
        ap.reference_frame = v.orbital_reference_frame
        ap.target_direction = (0, -1, 0)
        ap.engaged = True
        warp_to(t - bt / 2, lead=60)
        _wait_pointing(ap)
        warp_to(t - bt / 2, lead=5)
        while ut() < t - bt / 2:
            time.sleep(0.05)
    if not _await_link(v, ut() + 120):
        raise Refused(f"no CommNet link at the burn time (control {v.control.state.name})")
    _deorbit_now(v, pe_alt, bt)
    v.auto_pilot.engaged = False
    o = v.orbit
    say(f"deorbited: {o.periapsis_altitude / 1000:.1f} x {o.apoapsis_altitude / 1000:.1f} km, "
        f"periapsis in {o.time_to_periapsis / 3600:.2f} h")


def liftoff(target_alt=15000, heading=90.0):
    """Take off from an airless body into a low circular orbit (atmosphere: gravity turn above it)."""
    v = vessel()
    body = v.orbit.body
    _antennas(v, False)
    if body.has_atmosphere:
        for c in v.parts.parachutes:  # canopies left from the landing
            if _chute_deployed(c, True):
                try:
                    c.cut()
                except Exception as e:
                    say(f"chute cut skipped: {e}")
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


# ---------------------------------------------------------------- vessel switch, inflatable heat shield

def _has_command(v):
    return bool(v.parts.with_module("ModuleCommand"))


def switch_to(name):
    """Make the loaded vessel `name` active in flight. Exact name first (case-insensitive), then a prefix, then a
    substring: KSP names a separated part "<ship> Probe"/"Lander"/"Debris", and a part dropped from "Eve 2 Probe"
    is again "Eve 2 Probe" (Vessel.AutoRename keeps a name that already says Probe). A decoupler leaves the ROOT's
    side active (Part.decouple makes the far side the new vessel): the Eve 2 lander (root Terrier) stays on the
    spent deorbit stage when that stage drops. Among several matches the one with a command part (probe core,
    pod) wins; the stage left behind has none. Only loaded vessels (~2.5 km): others via `scene` + `fly`."""
    s = sc()
    active = s.active_vessel
    key = name.lower()
    vs = list(s.vessels)
    hits = [x for x in vs if x.name.lower() == key] or [x for x in vs if x.name.lower().startswith(key)] \
        or [x for x in vs if key in x.name.lower()]
    if not hits:
        raise Refused(f"no vessel named like '{name}'")
    if len(hits) == 1 and hits[0] == active:
        say(f"{active.name} is already the active vessel")
        return active
    far = [x for x in hits if x != active and not x.loaded]
    cand = [x for x in hits if x != active and x.loaded]
    if not cand:
        raise Refused(f"'{name}' matches {[x.name for x in far]}: not loaded (out of physics range); "
                      "`scene space_center` + `fly NAME` (never leave a lander unloaded inside an atmosphere)")

    def row(x):
        d = math.dist(x.position(active.reference_frame), (0, 0, 0))
        return (f"{x.name} ({x.type.name}, {len(x.parts.all)} parts, {d:.0f} m"
                + (", command part" if _has_command(x) else ", NO command part") + ")")
    if len(cand) > 1:
        cmd = [x for x in cand if _has_command(x)]
        if len(cmd) != 1:
            raise Refused(f"'{name}' matches {len(cand)} loaded vessels: {'; '.join(row(x) for x in cand)}")
        say(f"'{name}' matches {len(cand)} loaded vessels: taking the one with a command part")
        cand = cmd
    target = cand[0]
    say(f"switching {active.name} -> {row(target)}")
    s.active_vessel = target
    for _ in range(30):
        time.sleep(0.5)
        if s.active_vessel == target:
            break
    else:
        raise Refused(f"KSP did not switch to {target.name}")
    time.sleep(1)
    say(f"active: {target.name}, control {target.control.state.name}, signal {target.comms.signal_strength:.2f}, "
        f"stage {target.control.current_stage}")
    return target


def packed_shields(v):
    """Inflatable heat shields of v that are not inflated yet (ModuleAnimateGeneric animTime < 1)."""
    out = []
    for p in v.parts.with_name("InflatableHeatShield"):
        for m in p.modules:
            if m.name == "ModuleAnimateGeneric":
                f = next((f for f in m.field_list if f.name == "animTime"), None)
                if f is None or f.float_value < 0.99:
                    out.append(p)
    return out


def inflate():
    """Inflate the Heat Shield (10m) of the active vessel. It is not stageable: its ModuleAnimateGeneric event
    ("Toggle", shown as "Inflate Heat Shield") is triggered here. KSP keeps that event inactive while a part sits
    on the shield's top node (restrictedNode = top: the cone would open around it) and ignores it inside a
    fairing/bay; one-shot (disableAfterPlaying, no deflating). Refused while an engine is still aboard (Eve 2:
    drop the deorbit stage first)."""
    v = vessel()
    shields = v.parts.with_name("InflatableHeatShield")
    if not shields:
        raise Refused(f"{v.name} has no inflatable heat shield" + ("" if _has_command(v) else
                      ": it has no command part either (a decoupler leaves the root's side active): `ksp switch NAME`"))
    engines = sorted({e.part.title for e in v.parts.engines})
    if engines:
        raise Refused(f"{v.name} still carries {engines}: drop that stage first (`ksp stage`), the shield inflates "
                      "around what sits on its top node")
    for p in shields:
        m = next((m for m in p.modules if m.name == "ModuleAnimateGeneric"), None)
        if m is None:
            raise Refused(f"{p.title}: no ModuleAnimateGeneric")
        fields = {f.name: f for f in m.field_list}
        anim = lambda: fields["animTime"].float_value if "animTime" in fields else float("nan")
        if anim() > 0.99:
            say(f"{p.title}: already inflated")
            continue
        ev = next((e for e in m.event_list if e.name == "Toggle"), None)
        if ev is None or not ev.active:
            raise Refused(f"{p.title}: the inflate event is not available ({m.events}): a part on its top node, "
                          "or the animation is moving")
        say(f"{p.title}: {ev.gui_name}")
        ev.trigger()
        for _ in range(40):
            time.sleep(0.5)
            if anim() > 0.99:
                break
        if not anim() > 0.99:
            raise Refused(f"{p.title}: triggered, but animTime is {anim():.2f} after 20 s (shielded from the airstream?)")
        say(f"{p.title}: inflated")


# ---------------------------------------------------------------- reentry

@_contained(_fallback_chutes)
def reentry(main_alt=4000, main_speed=250, keep_until=None, science=False):
    """Coast to the atmosphere, drop everything except the parachute stages, hold retrograde, arm drogues
    below 20 km, stage the main chutes once below main_alt and slower than main_speed (or at 2.5 km).
    keep_until=ALT (uncrewed pod whose probe core sits in the service module): keep the service module on,
    engine first, deploy the chutes directly (no staging), decouple it under the chutes below ALT m.
    science (one-way probe, Eve 2's lander): nothing is collected into the root; at each new science situation
    (flying high, flying low) the fresh experiments run and their data is queued for transmission without waiting
    (_entry_science: the loop keeps its cadence); after the landing `do_science(transmit, all_)` sends the landed
    set and whatever is still aboard, with its link and EC waits."""
    if keep_until is not None:
        return _reentry_keep(main_alt, main_speed, keep_until)
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
    if not science:
        collect_science(v)
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

    done, queue = set(), {"mits": 0.0, "ut": ut()}
    high = body.flying_high_altitude_threshold if science else 0.0

    def sci():
        """Once per new flying situation. Not in space: the entry starts ~60 s above the atmosphere."""
        if science and v.situation.name == "flying":
            sit = "flying high" if fl.mean_altitude > high else "flying low"
            if sit not in done:
                done.add(sit)
                try:
                    _entry_science(v, sit, queue)
                except Exception as ex:  # science must never end the entry (-> _fallback_chutes)
                    say(f"{sit} science failed: {ex.__class__.__name__}: {str(ex).splitlines()[0][:80]}")

    while True:
        alt, spd = fl.mean_altitude, fl.speed
        sci()
        if next_is("drogue") and alt < 20000:
            v.control.activate_next_stage()
            say(f"drogues armed at {alt:.0f} m, {spd:.0f} m/s")
        low = (alt < main_alt and spd < main_speed) or alt < 2500
        if next_is("main") and low:
            break
        # nothing left to stage (chutes armed before the entry: Eve 2's lander) used to end the retrograde hold
        # right at the atmosphere's edge, before the heat pulse: hold it until the main-chute point instead
        if (v.control.current_stage == 0 and low) or v.situation.name in ("landed", "splashed"):
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
        sci()
        time.sleep(1)
    say(f"{v.situation.name}! {v.name}")
    if science:
        _await_queue(v, queue)
        do_science(transmit=True, all_=True)


def _reentry_keep(main_alt, main_speed, keep_until):
    v = vessel()
    body = v.orbit.body
    fl = v.flight(body.reference_frame)
    atmo = body.atmosphere_depth
    o = v.orbit
    if fl.mean_altitude > atmo and o.periapsis_altitude < atmo:
        p = o.semi_major_axis * (1 - o.eccentricity ** 2)
        r = body.equatorial_radius + atmo
        nu = -math.acos(max(-1.0, min(1.0, (p / r - 1) / o.eccentricity)))
        warp_to(o.ut_at_true_anomaly(nu), lead=60)
    _antennas(v, False)
    ap = v.auto_pilot
    ap.reference_frame = v.surface_velocity_reference_frame
    ap.target_direction = (0, -1, 0)
    ap.engaged = True
    say("reentry (service module kept): holding retrograde")
    chutes = list(v.parts.parachutes)
    drogues = [c for c in chutes if "drogue" in c.part.name.lower()]
    mains = [c for c in chutes if c not in drogues]
    armed = False
    while True:
        alt, spd = fl.mean_altitude, fl.speed
        if not armed and alt < 20000:
            for c in drogues:
                c.arm()
            armed = True
            say(f"drogues armed at {alt:.0f} m, {spd:.0f} m/s")
        if (alt < main_alt and spd < main_speed) or alt < 2500:
            break
        time.sleep(0.2)
    ap.engaged = False
    for c in mains:
        c.deploy()
    say(f"main chutes deployed at {fl.mean_altitude:.0f} m, {fl.speed:.0f} m/s")
    while fl.surface_altitude > keep_until and v.situation.name not in ("landed", "splashed"):
        time.sleep(0.2)
    for p in v.parts.all:
        if p.decoupler is not None and not p.decoupler.decoupled and "HeatShield" not in p.name:
            p.decoupler.decouple()
            say(f"service module dropped at {fl.surface_altitude:.0f} m, {fl.speed:.1f} m/s")
    v = vessel()
    while v.situation.name not in ("landed", "splashed"):
        time.sleep(1)
    say(f"{v.situation.name}! {v.name}")


# ---------------------------------------------------------------- science

def collect_science(v=None):
    """Move all experiment data into the root part's science container (KspBot StoreScience: the Mk1 pod's own
    "Collect All" is disabled), so data on stages about to be dropped comes home (Duna 1 jettisoned its lander
    with the Duna surface goo and thermometer data: the surface science contract stayed open)."""
    import json
    from .core import bot
    v = v or vessel()
    try:
        r = json.loads(bot().store_science())
    except Exception as ex:
        say(f"science not collected: {str(ex).splitlines()[0]}")
        return 0
    stored = [x for x in r["items"] if x["result"] == "stored"]
    other = [f"{x['subject']} ({x['result']})" for x in r["items"] if x["result"] != "stored"]
    say(f"science into {v.parts.root.title}: {len(stored)} stored, {r['held']} held"
        + (f"; left: {other}" if other else ""))
    return len(stored)


def _antennas(v, extend, panels_only=False):
    """Extend (before transmitting: a stowed Communotron can't) or retract (before atmosphere/liftoff) antennas,
    and the deployable solar panels with them (Ike Station 1's Gigantors: nothing else opens them)."""
    parts = ([] if panels_only else list(v.parts.antennas)) + list(v.parts.solar_panels)
    parts = [a for a in parts if a.deployable and a.deployed != extend]
    for a in parts:
        try:
            a.deployed = extend
        except Exception as ex:  # a non-retractable panel refuses to close
            say(f"{a.part.title}: {ex}")
    if parts:
        time.sleep(6)


def do_science(transmit=False, min_single=15.0, all_=False):
    """Run every available experiment that has no data yet; optionally transmit results.
    Single-use experiments (goo, materials bay) only run when the subject still has >= min_single science left,
    so a low-value situation (LKO, orbit before landing) doesn't spend them. transmit keeps their data for
    recovery; all_ transmits it too (one-way probes: Jool 1 lost its goo and Science Jr data)."""
    v = vessel()
    out = _run_fresh(v, min_single)
    send_ok = transmit
    if transmit:
        if v.situation.name != "flying":  # opening dishes/panels in the airflow tears them off
            _antennas(v, True)
        # no link (Kerbin below the horizon): warp until it rises, up to ~7 h
        for _ in range(40):
            if v.comms.signal_strength > 0.05:
                break
            warp_to(ut() + 600)
            time.sleep(1)
        else:
            say("no signal to KSC; data kept on board")
            send_ok = False
    send = []
    for e in v.parts.experiments:
        if e.has_data:
            val = sum(d.science_value for d in e.data)
            out.append((e.title, e.science_subject.title, round(val, 2)))
            # transmit only what can be run again (crew report, thermometer); keep goo etc. for recovery (all_: send)
            if send_ok and (e.rerunnable or all_) and e.data and any(d.transmit_value > 0 for d in e.data):
                send.append(e)
    for e in send:
        if _transmit(v, e) is None:
            say("a transmission did not arrive: the rest is kept on board")
            break
    if not transmit:
        _collect(v)
    for row in out:
        print(row)
    return out


def _run_fresh(v, min_single=15.0, wait=20.0, keep_last=False):
    """Run every available experiment without data (one per subject; single-use ones only if the subject has
    min_single left) and wait up to `wait` s for their reports. Returns the rows of what was kept/failed.
    keep_last (entry science): never spend the last fresh copy of a single-use experiment (Eve 2's lander: one
    Science Jr, three goo) before the landed set, where it is worth the most."""
    out = []
    ran = set()
    started = []
    exps = list(v.parts.experiments)
    spare = {}
    for e in exps:
        if not e.rerunnable and not e.inoperable and not e.has_data:
            spare[e.part.name] = spare.get(e.part.name, 0) + 1
    for e in exps:
        if e.has_data and e.data and not e.inoperable and sum(d.science_value for d in e.data) < 0.01:
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
            if keep_last and spare.get(e.part.name, 0) <= 1:
                out.append((e.title, sub.title, "kept for the landing (last one)"))
                continue
        try:
            e.run()
            ran.add(e.science_subject.title)
            started.append(e)
            if not e.rerunnable:
                spare[e.part.name] = spare.get(e.part.name, 0) - 1
        except Exception as ex:
            out.append((e.title, f"error {ex}"))
    # the magnetometer boom takes ~7 s to report: collecting after 1.5 s missed it, and the next run reset the
    # half-done experiment as "worthless" (Survey 1 lost the Mun low-orbit magnetometer that way)
    for _ in range(int(wait / 0.5)):
        time.sleep(0.5)
        if all(e.has_data and e.data for e in started):
            break
    return out


def _entry_science(v, label, queue, margin=100.0):
    """reentry --science at a new flying situation: run the fresh experiments (<= 8 s for their reports; the last
    copy of a single-use one is kept for the landing) and hand every result to the transmitter WITHOUT waiting for
    it to arrive. KSP queues transmissions (ModuleDataTransmitter.TransmitData while busy) and sends them in the
    background, and the data leaves the experiment at once, so a rerunnable one is free for the next situation.
    Blocking here (link waits that warp, EC charging, the arrival poll of _transmit: ~40 s a set) would stall the
    chute logic. EC: the queue's cost (Mits x EC/Mit of the dearest antenna, what is still queued
    included, estimated from the antenna's speed) must fit the battery minus margin, or a transmission stalls and
    KSP never resumes it; what does not fit, or finds no link, stays aboard for the landed pass."""
    out = _run_fresh(v, wait=8.0, keep_last=True)
    rate, via = _ec_per_mit(v)
    speed = min((a.packet_size / a.packet_interval for a in v.parts.antennas
                 if a.can_transmit and a.packet_interval > 0), default=1.0)
    backlog = max(0.0, queue["mits"] - (ut() - queue["ut"]) * speed)
    room = v.resources.amount("ElectricCharge") - margin - backlog * (rate or 0)
    sent, kept = [], [f"{r[0]} ({r[-1]})" for r in out]
    link = v.comms.can_transmit_science
    for e in v.parts.experiments:
        if not (e.has_data and e.data and any(d.transmit_value > 0 for d in e.data)):
            continue
        mits = sum(d.data_amount for d in e.data)
        if rate is None or not link or mits * rate > room:
            kept.append(e.title)
            continue
        val = sum(d.transmit_value for d in e.data)
        try:
            e.transmit()
        except Exception as ex:
            kept.append(f"{e.title} ({str(ex).splitlines()[0][:60]})")
            continue
        room -= mits * rate
        backlog += mits
        sent.append(f"{e.title} {val:.1f}")
    queue.update(mits=backlog, ut=ut(), speed=speed)
    say(f"{label} science at {v.flight().mean_altitude / 1000:.1f} km: queued {sent or 'nothing'}"
        + (f"; kept {kept}" if kept else "") + ("" if link else " (no link)")
        + (f" [{backlog:.0f} Mit queued via {via}, {room:.0f} EC spare]" if rate else " [no antenna]"))


def _await_queue(v, queue, timeout=300):
    """After the landing: let the queued transmissions finish (the queue's estimated time has passed and the
    science total, streamed packet by packet, has not moved for 15 s) before do_science measures its own
    arrivals and EC."""
    left = max(0.0, queue["mits"] - (ut() - queue["ut"]) * queue.get("speed", 1.0)) / queue.get("speed", 1.0)
    t_min, t_end = time.time() + 1.2 * left, time.time() + timeout
    last, quiet = sc().science, time.time()
    while time.time() < t_end and (time.time() < t_min or time.time() - quiet < 15):
        time.sleep(2)
        now = sc().science
        if now != last:
            last, quiet = now, time.time()
    say(f"queued transmissions settled (science now {sc().science:.1f}, EC {v.resources.amount('ElectricCharge'):.0f})")


def _ec_per_mit(v):
    """(EC per Mit, antenna title) of the dearest antenna that can transmit: KSP picks the transmitter itself, the
    dearest one bounds the cost (HG-55 6.67, 88-88 10, RA-2 24)."""
    rates = [(a.packet_resource_cost / a.packet_size, a.part.title) for a in v.parts.antennas
             if a.can_transmit and a.packet_size > 0]
    return max(rates) if rates else (None, None)


def _transmit(v, e, margin=100.0, charge_for=6 * 3600):
    """Transmit one experiment once the battery holds its cost (Mits x EC/Mit + margin): a transmission that
    empties the battery stalls and KSP never resumes it (the Jool plan: 900-1,100 EC sets on 1,810 EC). Short of
    charge: wait in sunlight (short rails warps, up to charge_for s), or skip it without solar charge. Then poll the
    career science total until it rises. True: arrived; False: skipped (data kept); None: sent but nothing arrived."""
    mits = sum(d.data_amount for d in e.data)
    rate, via = _ec_per_mit(v)
    if rate is None:
        say(f"{e.title}: no antenna can transmit; data kept")
        return False
    need = mits * rate + margin
    ec, cap = v.resources.amount("ElectricCharge"), v.resources.max("ElectricCharge")
    panels = [p for p in v.parts.solar_panels if p.state.name != "broken"]
    flow = sum(p.energy_flow for p in panels)
    if ec < need:
        if need > cap or not panels:
            say(f"{e.title}: needs {need:.0f} EC ({mits:.0f} Mit x {rate:.2f} via {via} + {margin:.0f}), has {ec:.0f}"
                + (f" of {cap:.0f} max" if need > cap else " and no solar panels") + ": skipped, data kept")
            return False
        say(f"{e.title}: needs {need:.0f} EC, has {ec:.0f}: charging at {flow:.1f} EC/s"
            + (f" (~{(need - ec) / flow:.0f} s)" if flow > 0 else " (in the shade)"))
        deadline = ut() + charge_for
        while ec < need:
            if ut() > deadline:
                say(f"{e.title}: EC {ec:.0f} < {need:.0f} after {charge_for / 3600:.0f} h of charging: skipped, "
                    "data kept")
                return False
            warp_to(ut() + min(600.0, max(30.0, 1.2 * (need - ec) / max(flow, 0.5))))
            time.sleep(1)
            ec, flow = v.resources.amount("ElectricCharge"), sum(p.energy_flow for p in panels)
    before = sc().science
    speed = min((a.packet_size / a.packet_interval for a in v.parts.antennas
                 if a.can_transmit and a.packet_interval > 0), default=1.0)
    wait = 30 + 2 * mits / max(speed, 0.1)
    say(f"transmitting {e.title} ({mits:.0f} Mit, ~{mits * rate:.0f} EC of {ec:.0f})", screen=False)
    e.transmit()
    t0 = time.time()
    while time.time() - t0 < wait:
        time.sleep(2)
        if sc().science - before > 0.001:
            time.sleep(2)
            say(f"{e.title}: science +{sc().science - before:.1f} (now {sc().science:.1f})")
            return True
    say(f"{e.title}: no science arrived within {wait:.0f} s (EC now {v.resources.amount('ElectricCharge'):.0f})")
    return None


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
