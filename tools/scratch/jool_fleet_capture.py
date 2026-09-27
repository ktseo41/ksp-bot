"""Jool fleet, part 5 (offline): the capture burn at each moon as `capture` flies it: a node at the periapsis
(retrograde there, direction fixed in space), ignition burn_lead (the time to burn half the dv) before it, staged
thrust. Result orbit, periapsis after the burn, the dv a second burn needs to reach the wanted apoapsis, the burn window
against the link blackout (jool_fleet_meet.py). Also the ejection from LKO the same way (finite-burn loss).
Run: uv run python tools/scratch/jool_fleet_capture.py"""
import math
from jool_fleet_common import *  # noqa: F401,F403
import jool_fleet_stages as st
from jool_fleet_land import Craft

VREL = {"Laythe": 1693.0, "Vall": 1483.0, "Tylo": 1349.0, "Bop": 1403.0, "Pol": 1337.0}  # jool_fleet_meet.py


def burn_time(craft_stages, m_final, dv):
    """Seconds to burn dv through the stages [(thrust N, isp, fuel kg, dry kg)] (mass-correct)."""
    c = Craft(craft_stages, m_final)
    t, left = 0.0, dv
    for _ in range(20):
        if left <= 1e-6:
            return t
        m = c.total_mass()
        f = c.thrust
        if f <= 0:
            return None
        s = c.stages[0]
        ve = s[1] * G0
        cap = ve * math.log(m / (m - s[2]))
        use = min(left, cap)
        m1 = m / math.exp(use / ve)
        t += (m - m1) * ve / f
        s[2] = 0.0 if use >= cap else s[2] - (m - m1)
        left -= use
    return t


def fly(mu, R, vrel, pe_alt, dv, stages, m_final, dt=0.05, early=0.0):
    rp = R + pe_alt
    e = 1 + rp * vrel * vrel / mu
    hyp = Orbit(mu, -mu / vrel ** 2, e, 0.0, 0.0, 0.0, 0.0, 0.0)
    lead = burn_time(stages, m_final, dv / 2)
    total = burn_time(stages, m_final, dv)
    t0 = -lead - early
    pos, vel = hyp.state(t0)
    d = mul(_norm(hyp.state(-early)[1]), -1.0)  # the node's burn direction: retrograde at the node
    c = Craft(stages, m_final)
    t, done = t0, 0.0
    rmin = _mag(pos)
    while done < dv:
        m = c.total_mass()
        if c.thrust <= 0:
            break
        a = c.burn(c.thrust / m, dt)
        r = _mag(pos)
        acc = add(mul(pos, -mu / r ** 3), mul(d, a))
        vel = add(vel, mul(acc, dt))
        pos = add(pos, mul(vel, dt))
        done += a * dt
        t += dt
        rmin = min(rmin, _mag(pos))
    o = Orbit.from_state(mu, pos, vel, t)
    return dict(lead=lead, total=total, start=t0, end=t, orbit=o, rmin=rmin - R, mass=c.total_mass(), craft=c)


def stage_list(rows, names, left):
    """[(thrust, isp, fuel kg, dry kg)] for the stages `names` with `left` m/s in the first one, and the final mass."""
    sel = [r for r in rows if r["name"] in names]
    out = []
    m_above = sel[-1]["m1"] * 1000 - 0.0
    m_final = sel[-1]["m1"] * 1000
    for i, r in enumerate(sel):
        dry = (r["mass"] - r["fuel"]) * 1000
        fuel = r["fuel"] * 1000
        if i == 0 and left is not None:
            m1 = r["m1"] * 1000
            fuel = m1 * (math.exp(left / (r["isp"] * G0)) - 1)
        out.append((r["thrust"] * 1000.0, r["isp"], fuel, dry if i < len(sel) - 1 else 0.0))
    return out, m_final


CASES = [
    # craft, moon, pe km, apo km (None: circular), stages at arrival, dv left in the first of them
    ("jool-vall", "Vall", 100e3, 1000e3, ("Terrier",), 3190.0),
    ("jool-vall", "Vall", 30e3, None, ("Terrier",), 3190.0),
    ("jool-pol", "Pol", 25e3, 100e3, ("Terrier",), 3140.0),
    ("jool-bop", "Bop", 30e3, 100e3, ("Terrier",), 3140.0),
    ("jool-tylo", "Tylo", 50e3, 1000e3, ("Poodle T", "Poodle A", "Terrier B"), 700.0),
    ("jool-tylo", "Tylo", 50e3, None, ("Poodle T", "Poodle A", "Terrier B"), 700.0),
    ("jool-tylo", "Tylo", 50e3, 1000e3, ("Poodle A", "Terrier B"), None),
    ("jool-laythe", "Laythe", 80e3, 2000e3, ("Poodle", "Terrier"), 600.0),
    ("jool-laythe", "Laythe", 80e3, 2000e3, ("Terrier",), None),
    ("jool-laythe", "Laythe", 80e3, None, ("Poodle", "Terrier"), 600.0),
]

if __name__ == "__main__":
    print("capture burns (node at the periapsis, ignition burn_lead before it):")
    for slug, moon, pe, apo, names, left in CASES:
        m = MOONS[moon]
        rows = st.ROWS[slug][0]
        stages, m_final = stage_list(rows, names, left)
        dv = m.capture_dv(VREL[moon], pe, apo)
        r = fly(m.mu, m.R, VREL[moon], pe, dv, [list(s) for s in stages], m_final)
        o = r["orbit"]
        rp_t = m.R + pe
        ra_t = rp_t if apo is None else m.R + apo
        if o.e < 1:
            # second burn at the new periapsis to reach the wanted apoapsis
            v_pe = math.sqrt(m.mu * (2 / o.periapsis - 1 / o.a))
            v_want = math.sqrt(m.mu * (2 / o.periapsis - 2 / (o.periapsis + ra_t)))
            fix = abs(v_pe - v_want)
            res = (f"{(o.periapsis - m.R) / 1e3:.1f} x {(o.apoapsis - m.R) / 1e3:.0f} km, period "
                   f"{o.period / 3600:.2f} h; trim at the pe to the wanted apoapsis {fix:.0f} m/s")
        else:
            res = f"STILL HYPERBOLIC (e {o.e:.2f}, v_inf {o.v_inf():.0f})"
        print(f"  {slug[5:]:7s} at {moon}, pe {pe / 1e3:.0f} km -> " + ("circular" if apo is None else f"x {apo / 1e3:.0f} km")
              + f": {dv:.0f} m/s on {'+'.join(names)} ({r['craft'].total_mass() / 1000:.2f} t after), burn {r['total']:.0f} s from pe"
              f"{r['start']:+.0f} s to pe{r['end']:+.0f} s; lowest point {r['rmin'] / 1e3:.1f} km; result {res}")

    print("\nejection from an 80 km parking orbit (node dv for v_inf 2,710: 1,932 m/s), direction fixed at the node:")
    for slug, names, left in (("jool-vall", ("Poodle", "Terrier"), 1759.0), ("jool-tylo", ("Poodle T",), 3032.0),
                              ("jool-tylo", ("Rhino", "Poodle T"), 150.0), ("jool-laythe", ("Poodle",), 2800.0)):
        rows = st.ROWS[slug][0]
        stages, m_final = stage_list(rows, names, left)
        mu, r0 = MU_KERBIN, R_KERBIN + 80e3
        vc = math.sqrt(mu / r0)
        dv = 1932.0
        circ = Orbit(mu, r0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        lead = burn_time([list(s) for s in stages], m_final, dv / 2)
        total = burn_time([list(s) for s in stages], m_final, dv)
        pos, vel = circ.state(-lead)
        d = _norm(circ.state(0.0)[1])
        c = Craft([list(s) for s in stages], m_final)
        done, t, dt = 0.0, -lead, 0.05
        hmin = 1e9
        while done < dv:
            mm = c.total_mass()
            if c.thrust <= 0:
                break
            a = c.burn(c.thrust / mm, dt)
            r = _mag(pos)
            acc = add(mul(pos, -mu / r ** 3), mul(d, a))
            vel = add(vel, mul(acc, dt))
            pos = add(pos, mul(vel, dt))
            done += a * dt
            t += dt
            hmin = min(hmin, _mag(pos) - R_KERBIN)
        o = Orbit.from_state(mu, pos, vel, t)
        vinf = o.v_inf()
        # what an impulsive burn would have needed for this v_inf
        imp = math.sqrt(vinf ** 2 + 2 * mu / r0) - vc
        want = math.sqrt(2710.0 ** 2 + 2 * mu / r0) - vc
        # direction error of the asymptote against the impulsive one
        ideal = Orbit.from_state(mu, circ.state(0.0)[0], mul(d, vc + dv), 0.0)
        from kspbot.kepler import hyperbola_asymptote
        off = ang(hyperbola_asymptote(o), hyperbola_asymptote(ideal))
        print(f"  {slug[5:]:7s} on {'+'.join(names)}: {total:.0f} s (lead {lead:.0f}), a {stages[0][0] / (c.m_final + sum(s[2] + s[3] for s in stages)):.1f} m/s2 at the start; "
              f"v_inf {vinf:.0f} (wanted 2,710): loss {dv - imp:.0f} m/s, asymptote {off:.1f} deg off, lowest {hmin / 1e3:.1f} km")
