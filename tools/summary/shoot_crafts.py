"""Sandbox photo shoot: each craft spec on the pad, daylight, UI hidden, camera framed on the whole rocket."""
import json, math, sys, time, subprocess, os
from kspbot.core import bot, sc, screenshot
from kspbot import flight

def daylight():
    v = sc().active_vessel
    for _ in range(40):
        sun = sc().bodies["Sun"].position(v.surface_reference_frame)
        r = math.sqrt(sum(x * x for x in sun))
        if sun[0] / r > 0.45:
            return
        flight.warp_to(flight.ut() + 900)
        time.sleep(1)

def frame(v):
    (x0, y0, z0), (x1, y1, z1) = v.bounding_box(v.reference_frame)
    h = y1 - y0
    cam = sc().camera
    cam.mode = cam.mode.__class__.free if hasattr(cam.mode.__class__, "free") else cam.mode
    cam.pitch = 4
    cam.heading = 270
    cam.distance = max(cam.min_distance, min(cam.max_distance, h * 1.15 + 4))
    return h

def main():
  for spec in sys.argv[1:]:
    s = json.load(open(spec))
    name = s["name"]
    out = subprocess.run(["uv", "run", "ksp", "build", spec], capture_output=True, text=True)
    if out.returncode:
        print(name, "BUILD FAILED", out.stderr[-200:]); continue
    out = subprocess.run(["timeout", "120", "uv", "run", "ksp", "launch", name], capture_output=True, text=True)
    if "pre_launch" not in out.stdout:
        print(name, "LAUNCH FAILED", out.stdout[-200:], out.stderr[-200:]); continue
    time.sleep(3)
    v = sc().active_vessel
    daylight()
    h = frame(v)
    bot().hide_ui(True)
    time.sleep(2.5)
    slug = os.path.basename(spec)[:-5]
    from kspbot.core import KSP_DIR
    win = f"{KSP_DIR}/Screenshots/craft-{slug}.png"
    if os.path.exists(win): os.remove(win)
    sc().screenshot(subprocess.run(["wslpath", "-w", win], capture_output=True, text=True).stdout.strip(), 2)
    for _ in range(50):
        if os.path.exists(win) and os.path.getsize(win) > 0: break
        time.sleep(0.2)
    time.sleep(0.5)
    p = f"runs/craft-{slug}.png"
    subprocess.run(["cp", win, p])
    bot().hide_ui(False)
    print(name, f"h={h:.1f} m", p)
    v.recover()
    time.sleep(4)


if __name__ == "__main__":
    main()
