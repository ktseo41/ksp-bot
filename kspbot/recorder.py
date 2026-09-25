"""Flight recorder: background telemetry + anomaly events, one JSONL file per vessel per day.

Started automatically by the CLI around every flight command. Events are also printed (prefix "!!") so the
driving session sees them in the command output.
"""
import datetime
import json
import math
import os
import threading
import time

import krpc

from .core import ROOT

FLIGHT_DIR = os.path.join(ROOT, "runs", "flights")


current = None  # the recorder of the running phase: say() messages go into its log too


class Recorder:
    def __init__(self, label, period=1.0):
        self.label = label
        self.period = period
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self.path = None
        self.events = []

    def __enter__(self):
        global current
        self._thread.start()
        current = self
        return self

    def __exit__(self, *exc):
        global current
        current = None
        self._stop.set()
        self._thread.join(timeout=5)

    def _write(self, rec):
        with open(self.path, "a") as f:
            f.write(json.dumps(rec) + "\n")

    def event(self, kind, msg, echo=True, **extra):
        rec = {"t": round(time.time(), 1), "ut": round(getattr(self, "_ut", 0.0), 1), "event": kind, "msg": msg, **extra}
        self.events.append(rec)
        if self.path:
            self._write(rec)
        if echo:
            print(f"!! [{kind}] {msg}", flush=True)

    def _run(self):
        try:
            conn = krpc.connect(name="kspbot-recorder")
        except Exception as e:  # never break the flight because of the recorder
            print(f"!! recorder could not connect: {e}")
            return
        sc = conn.space_center
        v = sc.active_vessel
        if v is None:
            return
        os.makedirs(FLIGHT_DIR, exist_ok=True)
        day = datetime.date.today().isoformat()
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in v.name)
        self.path = os.path.join(FLIGHT_DIR, f"{day}_{safe}.jsonl")
        self._ut = sc.ut
        self._write({"t": round(time.time(), 1), "ut": round(self._ut, 1), "event": "phase", "msg": self.label})
        try:
            log_start = len(conn.ksp_bot.flight_events(0))
        except Exception:
            log_start = 0
        titles = sorted(p.title for p in v.parts.all)
        n_parts = len(titles)
        stage = v.control.current_stage
        body = v.orbit.body.name
        situation = v.situation.name
        tumbling = spinning = oscillating = False
        hist = []
        while not self._stop.is_set():
            try:
                if sc.active_vessel is None or sc.active_vessel.name != v.name:
                    self.event("vessel", "active vessel changed or lost")
                    return
                self._ut = sc.ut
                o = v.orbit
                fl = v.flight(o.body.reference_frame)
                sfl = v.flight(v.surface_reference_frame)
                # anomalies from KSP's own flight log
                for line in conn.ksp_bot.flight_events(log_start):
                    log_start += 1
                    kind = "ksp"
                    low = line.lower()
                    if any(w in low for w in ("collided", "exploded", "destroyed", "killed", "overheat")):
                        kind = "damage"
                    self.event(kind, line)
                cur_parts = v.parts.all
                if len(cur_parts) != n_parts:
                    new_titles = sorted(p.title for p in cur_parts)
                    lost = list(titles)
                    for t in new_titles:
                        if t in lost:
                            lost.remove(t)
                    self.event("parts", f"part count {n_parts} -> {len(cur_parts)}; gone: {', '.join(lost)}",
                               stage=v.control.current_stage)
                    n_parts, titles = len(cur_parts), new_titles
                if v.control.current_stage != stage:
                    stage = v.control.current_stage
                    self.event("stage", f"stage -> {stage}")
                if o.body.name != body:
                    body = o.body.name
                    self.event("soi", f"entered {body} SOI")
                if v.situation.name != situation:
                    situation = v.situation.name
                    self.event("situation", situation)
                av = v.angular_velocity(o.body.non_rotating_reference_frame)
                rate = math.degrees(math.sqrt(sum(x * x for x in av)))
                q = fl.dynamic_pressure
                aoa = sfl.angle_of_attack if q > 1000 else 0.0
                limit = 30 if q > 1000 else 60  # autopilot slews fast in vacuum
                if (rate > limit or abs(aoa) > 25) and not tumbling:
                    tumbling = True
                    self.event("attitude", f"loss of control? rate={rate:.0f} deg/s aoa={aoa:.0f} q={q:.0f}")
                elif rate < 10 and abs(aoa) < 10:
                    tumbling = False
                # roll rate (spin about the vessel axis) and AoA oscillation in the atmosphere
                axis = v.direction(o.body.non_rotating_reference_frame)
                roll_rate = math.degrees(sum(a * b for a, b in zip(av, axis)))
                if abs(roll_rate) > 10 and not spinning:
                    spinning = True
                    self.event("attitude", f"rolling {roll_rate:.0f} deg/s")
                elif abs(roll_rate) < 3:
                    spinning = False
                hist.append(aoa)
                del hist[:-8]
                flips = sum(1 for a, b in zip(hist, hist[1:]) if a * b < 0 and abs(a - b) > 2)
                if flips >= 3 and not oscillating:
                    oscillating = True
                    self.event("attitude", f"oscillating: AoA {min(hist):.1f}..{max(hist):.1f} deg, rate {rate:.0f} deg/s, q={q:.0f}")
                elif flips == 0:
                    oscillating = False
                self._write({
                    "t": round(time.time(), 1), "ut": round(self._ut, 1), "body": body,
                    "alt": round(fl.mean_altitude), "radar": round(fl.surface_altitude),
                    "spd": round(fl.speed, 1), "vs": round(fl.vertical_speed, 1), "hs": round(fl.horizontal_speed, 1),
                    "pitch": round(sfl.pitch, 1), "hdg": round(sfl.heading, 1), "roll": round(sfl.roll, 1),
                    "roll_rate": round(roll_rate, 1), "aoa": round(aoa, 1),
                    "rate": round(rate, 1), "q": round(q), "thr": round(v.control.throttle, 2),
                    "stage": stage, "parts": n_parts, "mass": round(v.mass), "thrust": round(v.thrust),
                    "ap": round(o.apoapsis_altitude), "pe": round(o.periapsis_altitude),
                })
            except Exception as e:
                if "not found" in str(e).lower() or "no longer exists" in str(e).lower():
                    self.event("vessel", f"vessel gone: {e.__class__.__name__}")
                    return
            self._stop.wait(self.period)


def summary(path, last=20):
    """Events of a flight log (for review after a flight)."""
    out = []
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            if "event" in r:
                out.append(f"ut={r['ut']} [{r['event']}] {r['msg']}")
    return out[-last:]
