"""Connection and small shared helpers."""
import json
import os
import subprocess
import time

import krpc

KSP_DIR = os.environ.get(
    "KSP_DIR", "/mnt/c/Program Files (x86)/Steam/steamapps/common/Kerbal Space Program")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_conn = None


def conn():
    global _conn
    if _conn is None:
        _conn = krpc.connect(name="kspbot")
    return _conn


def sc():
    return conn().space_center


def bot():
    return conn().ksp_bot


def status():
    return json.loads(bot().status())


class SaveFailed(RuntimeError):
    pass


def check_save(r):
    """Raise SaveFailed for a failed KspBot Save() result: a scene change after it would roll the career back
    to the last good save."""
    if not r["ok"]:
        raise SaveFailed(f"save '{r['name']}' failed in {r['scene']}: {r['error']} (FlightGlobals.ready={r['ready']}, "
                         f"activeVessel={r['activeVessel']}); don't change scenes until a save works")
    return r


def save(name="persistent"):
    """Save through the mod, which first clears the stale FlightGlobals state that makes KSP's save throw."""
    return check_save(json.loads(bot().save(name)))


def wait_ready(timeout=300):
    """Wait until KSP is up with a save loaded (after tools/install.sh)."""
    global _conn
    end = time.time() + timeout
    while time.time() < end:
        try:
            s = status()
            if s["scene"] in ("SPACECENTER", "FLIGHT", "TRACKSTATION", "EDITOR"):
                return s
        except Exception:
            _conn = None
        time.sleep(3)
    raise TimeoutError("KSP not ready")


def say(msg, seconds=5.0, screen=True):
    """Print and show the message on the game screen (so a human watching can follow); screen=False for
    diagnostics (a Klaw debug dump covered the whole view). On screen it is cut to one line."""
    print(msg, flush=True)
    from . import recorder
    if recorder.current is not None:  # the decisions of a phase (grab attempts, retries) belong in the flight log
        try:
            recorder.current.event("say", msg, echo=False)
        except Exception:
            pass
    if not screen:
        return
    try:
        bot().message(msg if len(msg) <= 100 else msg[:97] + "...", seconds)
    except Exception:
        pass


def screenshot(name="shot", width=1280):
    """Capture the game view (not the desktop). Returns a local PNG path for viewing."""
    win = f"{KSP_DIR}/Screenshots/kspbot_{name}.png"
    os.makedirs(os.path.dirname(win), exist_ok=True)
    if os.path.exists(win):
        os.remove(win)
    winpath = subprocess.run(["wslpath", "-w", win], capture_output=True, text=True).stdout.strip()
    sc().screenshot(winpath, 1)
    for _ in range(50):
        if os.path.exists(win) and os.path.getsize(win) > 0:
            break
        time.sleep(0.2)
    time.sleep(0.3)
    out = os.path.join(ROOT, "runs", f"{name}.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    from PIL import Image
    im = Image.open(win)
    if im.width > width:
        im = im.resize((width, int(im.height * width / im.width)))
    im.save(out)
    return out
