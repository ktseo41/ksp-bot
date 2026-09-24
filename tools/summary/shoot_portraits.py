import sys, time, os, subprocess
sys.path.insert(0, "./tools/summary")
from kspbot.core import bot, sc, KSP_DIR
from shoot_crafts import daylight
for name in sys.argv[1:]:
    first = name.split()[0].lower()
    out = subprocess.run(["timeout", "120", "uv", "run", "ksp", "launch", "EVA Test", "--crew", name], capture_output=True, text=True)
    if "pre_launch" not in out.stdout:
        print(name, "launch failed"); continue
    time.sleep(3); daylight(); time.sleep(4)
    win = f"{KSP_DIR}/Screenshots/portrait-{first}.png"
    if os.path.exists(win): os.remove(win)
    sc().screenshot(subprocess.run(["wslpath", "-w", win], capture_output=True, text=True).stdout.strip(), 1)
    time.sleep(2)
    print(name, win)
    sc().active_vessel.recover(); time.sleep(5)
