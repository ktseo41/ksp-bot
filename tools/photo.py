"""Blog photo of the current flight scene: `uv run python tools/photo.py NAME [distance] [pitch] [heading]`
-> runs/NAME.png, UI hidden. Camera angles in degrees, distance in m."""
import sys
import time

from kspbot.core import bot, sc, screenshot

name = sys.argv[1]
cam = sc().camera
if len(sys.argv) > 2:
    cam.distance = max(cam.min_distance, min(cam.max_distance, float(sys.argv[2])))
if len(sys.argv) > 3:
    cam.pitch = float(sys.argv[3])
if len(sys.argv) > 4:
    cam.heading = float(sys.argv[4])
bot().hide_ui(True)
time.sleep(1.5)
try:
    print(screenshot(name))
finally:
    bot().hide_ui(False)
