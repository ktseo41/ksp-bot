"""Pure two-body Kepler math on orbital elements (no kRPC): state at a time, elements from a state, time to a
true anomaly, closest approach of two orbits. KSP's elements (inclination, LAN, argument of periapsis, mean
anomaly at epoch) are read straight into the standard right-handed parametrisation (x = reference direction,
z = reference normal): angles between planes/lines and all times come out right whatever KSP's handedness, as
long as everything goes through this module (flight._plane uses the same trick). Used by the departure
planner in flight.py and by the offline tests under tools/."""
import math


def _norm(v):
    m = math.sqrt(sum(x * x for x in v))
    return tuple(x / m for x in v) if m > 0 else v


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _mag(v):
    return math.sqrt(_dot(v, v))


def rotate(v, axis, ang):
    """Rodrigues rotation of v about the unit vector axis by ang (rad)."""
    c, s = math.cos(ang), math.sin(ang)
    k = _norm(axis)
    kv = _cross(k, v)
    kd = _dot(k, v)
    return tuple(x * c + y * s + z * kd * (1 - c) for x, y, z in zip(v, kv, k))


class Orbit:
    """Keplerian orbit around a body of gravitational parameter mu. a < 0 for a hyperbola (e > 1).
    m0 is the mean anomaly at epoch (hyperbolic mean anomaly for e > 1), KSP style."""

    def __init__(self, mu, a, e, inc, lan, argpe, m0, epoch, name=""):
        self.mu, self.a, self.e = mu, a, e
        self.inc, self.lan, self.argpe = inc, lan, argpe
        self.m0, self.epoch, self.name = m0, epoch, name
        # perifocal basis: P towards the periapsis, Q 90 deg ahead in the direction of motion, W the normal
        cl, sl, ci, si, cw, sw = math.cos(lan), math.sin(lan), math.cos(inc), math.sin(inc), math.cos(argpe), math.sin(argpe)
        self.P = (cl * cw - sl * sw * ci, sl * cw + cl * sw * ci, sw * si)
        self.Q = (-cl * sw - sl * cw * ci, -sl * sw + cl * cw * ci, cw * si)
        self.W = (sl * si, -cl * si, ci)

    # ------------------------------------------------------------ construction
    @classmethod
    def from_state(cls, mu, r, v, t, name=""):
        h = _cross(r, v)
        hm = _mag(h)
        R, V = _mag(r), _mag(v)
        ev = tuple((V * V - mu / R) * x / mu - _dot(r, v) * y / mu for x, y in zip(r, v))
        e = _mag(ev)
        energy = V * V / 2 - mu / R
        a = -mu / (2 * energy) if abs(energy) > 1e-12 else float("inf")
        W = tuple(x / hm for x in h)
        inc = math.acos(max(-1.0, min(1.0, W[2])))
        n = (-W[1], W[0], 0.0)  # node line = z x W
        nm = _mag(n)
        if nm < 1e-12:
            n, nm = (1.0, 0.0, 0.0), 1.0
        lan = math.atan2(n[1], n[0]) % (2 * math.pi)
        if e > 1e-12:
            P = tuple(x / e for x in ev)
        else:
            P = tuple(x / nm for x in n)
        Q = _cross(W, P)
        nh = tuple(x / nm for x in n)
        argpe = math.atan2(_dot(_cross(nh, P), W), _dot(nh, P)) % (2 * math.pi)
        nu = math.atan2(_dot(r, Q), _dot(r, P))
        if e < 1:
            E = 2 * math.atan2(math.sqrt(1 - e) * math.sin(nu / 2), math.sqrt(1 + e) * math.cos(nu / 2))
            M = E - e * math.sin(E)
        else:
            H = 2 * math.atanh(max(-1 + 1e-15, min(1 - 1e-15, math.sqrt((e - 1) / (e + 1)) * math.tan(nu / 2))))
            M = e * math.sinh(H) - H
        return cls(mu, a, e, inc, lan, argpe, M, t, name)

    # ------------------------------------------------------------ scalars
    @property
    def n(self):
        return math.sqrt(self.mu / abs(self.a) ** 3)

    @property
    def period(self):
        return 2 * math.pi / self.n if self.e < 1 else float("inf")

    @property
    def periapsis(self):
        return self.a * (1 - self.e)

    @property
    def apoapsis(self):
        return self.a * (1 + self.e)

    @property
    def h(self):
        return math.sqrt(self.mu * abs(self.a) * abs(1 - self.e * self.e))

    def v_inf(self):
        return math.sqrt(self.mu / -self.a) if self.e > 1 else 0.0

    def mean_anomaly(self, t):
        M = self.m0 + self.n * (t - self.epoch)
        return M % (2 * math.pi) if self.e < 1 else M

    def true_anomaly(self, t):
        M = self.mean_anomaly(t)
        e = self.e
        if e < 1:
            E = M if e < 0.8 else math.pi
            for _ in range(60):
                d = (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
                E -= d
                if abs(d) < 1e-13:
                    break
            return 2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2))
        H = math.asinh(M / e) if abs(M) > 1 else M
        for _ in range(80):
            d = (e * math.sinh(H) - H - M) / (e * math.cosh(H) - 1)
            H -= d
            if abs(d) < 1e-13:
                break
        return 2 * math.atan2(math.sqrt(e + 1) * math.sinh(H / 2), math.sqrt(e - 1) * math.cosh(H / 2))

    def radius_at_nu(self, nu):
        p = abs(self.a) * abs(1 - self.e * self.e)
        return p / (1 + self.e * math.cos(nu))

    def radius_at(self, t):
        return self.radius_at_nu(self.true_anomaly(t))

    def time_of_nu(self, nu, after=None):
        """UT at which the true anomaly is nu: the first one >= after (default: the epoch) for an ellipse."""
        e = self.e
        if e < 1:
            E = 2 * math.atan2(math.sqrt(1 - e) * math.sin(nu / 2), math.sqrt(1 + e) * math.cos(nu / 2))
            M = (E - e * math.sin(E)) % (2 * math.pi)
            t = self.epoch + ((M - self.m0) % (2 * math.pi)) / self.n
            after = self.epoch if after is None else after
            P = self.period
            t += math.ceil((after - t) / P) * P if t < after else 0.0
            return t
        H = 2 * math.atanh(math.sqrt((e - 1) / (e + 1)) * math.tan(nu / 2))
        return self.epoch + (e * math.sinh(H) - H - self.m0) / self.n

    def time_at_radius(self, r, t0, outward=True):
        """First UT after t0 at which the radius is r (bisection along the arc that moves away from the body if
        outward). Hyperbolae only need the outbound leg."""
        lo, hi = t0, t0 + (self.period / 2 if self.e < 1 else 400 * 86400)
        f = (lambda t: self.radius_at(t) - r) if outward else (lambda t: r - self.radius_at(t))
        if f(hi) < 0:
            return None
        for _ in range(80):
            mid = (lo + hi) / 2
            if f(mid) < 0:
                lo = mid
            else:
                hi = mid
        return hi

    # ------------------------------------------------------------ vectors
    def state_at_nu(self, nu):
        r = self.radius_at_nu(nu)
        p = abs(self.a) * abs(1 - self.e * self.e)
        c, s = math.cos(nu), math.sin(nu)
        k = math.sqrt(self.mu / p)
        pos = tuple(r * (c * x + s * y) for x, y in zip(self.P, self.Q))
        vel = tuple(k * (-s * x + (self.e + c) * y) for x, y in zip(self.P, self.Q))
        return pos, vel

    def state(self, t):
        return self.state_at_nu(self.true_anomaly(t))

    def position(self, t):
        return self.state(t)[0]

    def velocity(self, t):
        return self.state(t)[1]

    def normal(self):
        return self.W

    def __repr__(self):
        return (f"Orbit({self.name} a={self.a:.4g} e={self.e:.4f} inc={math.degrees(self.inc):.2f} "
                f"lan={math.degrees(self.lan):.1f} argpe={math.degrees(self.argpe):.1f})")


def closest_approach(oa, ob, t0, t1, n=400):
    """(distance, UT) of the closest approach between orbits oa and ob (same central body) in [t0, t1]:
    coarse scan then golden-section refinement."""
    def d(t):
        return math.dist(oa.position(t), ob.position(t))
    best = min(((d(t0 + (t1 - t0) * i / n), t0 + (t1 - t0) * i / n) for i in range(n + 1)))
    lo, hi = max(t0, best[1] - (t1 - t0) / n), min(t1, best[1] + (t1 - t0) / n)
    g = (math.sqrt(5) - 1) / 2
    a, b = hi - g * (hi - lo), lo + g * (hi - lo)
    fa, fb = d(a), d(b)
    for _ in range(80):
        if fa < fb:
            hi, b, fb = b, a, fa
            a = hi - g * (hi - lo)
            fa = d(a)
        else:
            lo, a, fa = a, b, fb
            b = lo + g * (hi - lo)
            fb = d(b)
    t = (lo + hi) / 2
    return d(t), t


def hyperbola_asymptote(orbit):
    """Unit direction of the outgoing asymptote of a hyperbolic orbit."""
    th = math.acos(-1 / orbit.e)  # true anomaly of the asymptote
    return tuple(math.cos(th) * x + math.sin(th) * y for x, y in zip(orbit.P, orbit.Q))
