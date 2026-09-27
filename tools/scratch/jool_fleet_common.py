"""Shared constants and helpers for the Jool fleet plan scripts (no kRPC). Body constants and orbital elements were
read from the game on 2026-09-27 (kRPC `space_center.bodies`, read-only); kepler.Orbit on these elements reproduced the
game's Kerbin-moon distances and angles to < 1 m / 0.001 deg at four UTs (heliocentric + Jool-centric in one set of axes)."""
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from kspbot.kepler import Orbit, _cross, _dot, _mag, _norm, rotate  # noqa: E402,F401
from kspbot.flight import _lambert  # noqa: E402,F401

G0 = 9.80665
DAY = 21600.0
MU_SUN = 1.1723327948324905e18
R_SUN = 261.6e6
MU_KERBIN, R_KERBIN, SOI_KERBIN = 3.5316e12, 600e3, 84159286.0
MU_JOOL, R_JOOL, SOI_JOOL, ATM_JOOL = 282528004209995.25, 6000e3, 2455985185.0, 200e3
T_WIN = 54_245_654.0

kerbin = Orbit(MU_SUN, 13_599_840_256.0, 0.0, 0.0, 0.0, 0.0, 3.14000010490417, 0.0, "Kerbin")
jool = Orbit(MU_SUN, 68_773_560_320.0, 0.0500000007450581, 0.02275909379554594, 0.9075712110370514, 0.0,
             0.100000001490116, 0.0, "Jool")
mun = Orbit(MU_KERBIN, 12_000_000.0, 0.0, 0.0, 0.0, 0.0, 1.70000004768372, 0.0, "Mun")


class Moon:
    def __init__(self, name, mu, R, soi, g, rot, atm, space_high, a, e, inc, lan, argpe, m0, terrain):
        self.name, self.mu, self.R, self.soi, self.g, self.rot, self.atm = name, mu, R, soi, g, rot, atm
        self.space_high, self.terrain = space_high, terrain
        self.orbit = Orbit(MU_JOOL, a, e, inc, lan, argpe, m0, 0.0, name)

    def v_circ(self, alt):
        return math.sqrt(self.mu / (self.R + alt))

    def capture_dv(self, vrel, pe_alt, apo_alt=None):
        rp = self.R + pe_alt
        ra = rp if apo_alt is None else self.R + apo_alt
        return math.sqrt(vrel ** 2 + 2 * self.mu / rp) - math.sqrt(self.mu * (2 / rp - 2 / (rp + ra)))


# terrain = flight.TERRAIN (highest terrain, m)
MOONS = {
    "Laythe": Moon("Laythe", 1962000029236.0781, 500e3, 3723645.8, 7.850681, 52980.879, 50e3, 200e3,
                   27_184_000.0, 0.0, 0.0, 0.0, 0.0, 3.14000010490417, 5900),
    "Vall": Moon("Vall", 207481499473.75098, 300e3, 2406401.4, 2.3061375, 105962.089, 0.0, 90e3,
                 43_152_000.0, 0.0, 0.0, 0.0, 0.0, 0.899999976158142, 7990),
    "Tylo": Moon("Tylo", 2825280042099.9526, 600e3, 10856518.4, 7.850681, 211926.358, 0.0, 250e3,
                 68_500_000.0, 0.0, 0.00043633231950044, 0.0, 0.0, 3.14000010490417, 11290),
    "Bop": Moon("Bop", 2486834944.4149065, 65e3, 1221060.9, 0.5888011, 544507.429, 0.0, 25e3,
                128_500_000.0, 0.234999999403954, 0.2617993877991494, 0.17453292519943295, 0.4363323129985824,
                0.899999976158142, 21750),
    "Pol": Moon("Pol", 721702080.0, 44e3, 1042138.9, 0.3729073, 901902.624, 0.0, 22e3,
                179_890_000.0, 0.17085, 0.07417649320975901, 0.03490658503988659, 0.2617993877991494,
                0.899999976158142, 5590),
}


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def mul(a, k):
    return tuple(x * k for x in a)


def ang(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0, _dot(_norm(a), _norm(b))))))


def eject_dv(vinf, mu=MU_KERBIN, r=R_KERBIN + 80e3):
    return math.sqrt(vinf ** 2 + 2 * mu / r) - math.sqrt(mu / r)


def strength(d, power, dsn=250e9):
    rng = math.sqrt(power * dsn)
    s = max(0.0, 1 - d / rng)
    return s * s * (3 - 2 * s)


def incoming_hyperbola(mu, vinf_vec, rp, normal, t_pe=0.0, name=""):
    """kepler.Orbit of the hyperbola that arrives with the velocity-at-infinity vector vinf_vec, periapsis radius rp,
    in the plane through the asymptote whose normal is closest to `normal` (prograde about it); periapsis at t_pe."""
    v = _mag(vinf_vec)
    s = _norm(vinf_vec)
    n = _norm(sub(normal, mul(s, _dot(normal, s))))
    a = -mu / v ** 2
    e = 1 + rp / -a
    th = math.acos(-1 / e)
    P = rotate(mul(s, -1.0), n, th)  # the craft comes from the direction -s at true anomaly -th
    vp = math.sqrt(v * v + 2 * mu / rp)
    Q = _cross(n, P)
    return Orbit.from_state(mu, mul(P, rp), mul(Q, vp), t_pe, name)


__all__ = [k for k in dict(globals()) if not k.startswith("__")]
