"""Read-only helper for the Jool fleet (kRPC, no commands): where is the moon when the craft is at its Jool periapsis?
Reads the named vessel's trajectory (its patch around Jool: the current orbit or the one after the SOI entry), takes the
periapsis (radius, UT, direction) and compares it with the moon's position at that UT. Prints the phase error and the
arrival shifts that would bring the moon to the periapsis point (the mid-course / in-SOI timing target), and the
relative speed if the moon were there.
With --node the trajectory after the vessel's first maneuver node is read instead (the node `--plan` leaves in place;
the vessel must be the active one).
Run: uv run python tools/scratch/jool_phase.py "Tylo 1" Tylo [--node]"""
import math
import sys

import krpc


def main(vessel_name, moon_name, node=False):
    c = krpc.connect(name="jool-phase (read-only)")
    sc = c.space_center
    v = next((x for x in sc.vessels if x.name == vessel_name), None)
    if v is None:
        sys.exit(f"no vessel named {vessel_name!r}")
    jool, moon = sc.bodies["Jool"], sc.bodies[moon_name]
    o = v.orbit
    if node:
        nodes = v.control.nodes
        if not nodes:
            sys.exit("no maneuver node on the vessel")
        o = nodes[0].orbit
        print(f"reading the path after the node at UT {nodes[0].ut:.0f} ({nodes[0].delta_v:.1f} m/s)")
    t_in = sc.ut
    for _ in range(4):
        if o.body.name == "Jool":
            break
        t_in = sc.ut + o.time_to_soi_change
        o = o.next_orbit
        if o is None:
            sys.exit("the trajectory has no patch around Jool (no encounter yet)")
    if o.body.name != "Jool":
        sys.exit("the trajectory has no patch around Jool")
    frame = jool.non_rotating_reference_frame
    mu = jool.gravitational_parameter
    # the periapsis of the patch: true anomaly 0
    t_pe = o.ut_at_true_anomaly(0.0)
    if o.eccentricity < 1:
        while t_pe < t_in:
            t_pe += o.period
    p = o.position_at(t_pe, frame)
    m = moon.orbit.position_at(t_pe, frame)
    rp = math.sqrt(sum(x * x for x in p))
    rm = math.sqrt(sum(x * x for x in m))
    # signed angle from the periapsis direction to the moon, positive along the moon's motion
    m2 = moon.orbit.position_at(t_pe + 60, frame)
    cosang = sum(a * b for a, b in zip(p, m)) / (rp * rm)
    ang = math.degrees(math.acos(max(-1.0, min(1.0, cosang))))
    d0 = math.sqrt(sum((a - b) ** 2 for a, b in zip(p, m)))
    p_hat = tuple(x / rp for x in p)
    ahead = sum(a * (b2 - b1) for a, b1, b2 in zip(p_hat, m, m2)) < 0  # moving away from the pe direction: it is past it
    P = moon.orbit.period
    dt = ang / 360.0 * P * (1 if ahead else -1)  # the moon passed the point dt ago (ahead) / reaches it in -dt
    vinf = math.sqrt(mu / abs(o.semi_major_axis)) if o.eccentricity > 1 else 0.0
    v_pe = math.sqrt(mu * (2 / rp - 1 / o.semi_major_axis))
    v_m = math.sqrt(mu * (2 / rm - 1 / moon.orbit.semi_major_axis))
    day = 21600.0
    print(f"{vessel_name}: Jool patch e {o.eccentricity:.3f}, inc {math.degrees(o.inclination):.2f} deg "
          f"({'PROGRADE' if o.inclination < math.pi / 2 else 'RETROGRADE'}), v_inf {vinf:.0f} m/s")
    print(f"  Jool periapsis: UT {t_pe:.0f} (in {(t_pe - sc.ut) / day:.1f} d), radius {rp / 1e6:.2f} Mm (alt {(rp - 6e6) / 1e3:.0f} km); "
          f"{moon_name} is then at {rm / 1e6:.2f} Mm: periapsis {'inside' if rp < rm else 'outside'} its orbit by "
          f"{abs(rp - rm) / 1e6:.2f} Mm")
    print(f"  {moon_name} at that UT: {ang:.1f} deg {'past' if ahead else 'short of'} the periapsis point "
          f"({d0 / 1e6:.1f} Mm away, SOI {moon.sphere_of_influence / 1e6:.2f} Mm)")
    early, late = (-dt) % P, 0.0
    late = (dt) % P
    print(f"  to meet it there: arrive {late / 3600:.1f} h EARLIER or {early / 3600:.1f} h LATER (period {P / 3600:.1f} h); "
          f"far out ~0.5 m/s per hour (added to the plane burn in quadrature), at Jool's SOI edge ~5 m/s per hour")
    print(f"  speeds at the periapsis: craft {v_pe:.0f}, {moon_name} {v_m:.0f}: relative {abs(v_pe - v_m):.0f} m/s if tangent "
          "and in its plane")


if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if x != "--node"]
    if len(args) != 2:
        sys.exit(__doc__)
    main(args[0], args[1], node="--node" in sys.argv)
