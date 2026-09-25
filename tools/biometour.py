"""Low circular orbit EVA biome tour (Survey 1, Mun and Minmus): predict from the ground track the next entry into a
missing biome, warp to the middle of that pass, EVA out, report, board. Usage: biometour.py DONE1,DONE2,... [max_cycles]
Run as a script for now (to become a CLI command: see LOG next steps)."""
import subprocess, sys, time
from kspbot.core import sc
from kspbot import flight
s = sc()
done = set(x for x in sys.argv[1].split(",") if x)
maxc = int(sys.argv[2]) if len(sys.argv) > 2 else 30
ksp = lambda *a: subprocess.run(["uv", "run", "ksp", *a], capture_output=True, text=True)
v = s.active_vessel
body = v.orbit.body
missing = set(body.biomes) - done
print("missing", sorted(missing), flush=True)
for n in range(maxc):
    v = s.active_vessel
    if not missing:
        break
    track = flight._track(v)
    t0 = s.ut
    t, found = t0 + 60, None
    prev = flight._biome(body, *track(t))
    while t < t0 + 40 * v.orbit.period:
        t += 10
        b = flight._biome(body, *track(t))
        # enter the biome and stay 20 s inside
        if b in missing and b != prev and flight._biome(body, *track(t + 20)) == b:
            t_out = t
            while flight._biome(body, *track(t_out + 5)) == b and t_out < t + 600:
                t_out += 5
            found = ((t + t_out) / 2, b)  # the middle of the pass over it
            break
        prev = b
    if not found:
        print("no missing biome within 40 orbits", flush=True)
        break
    flight.warp_to(found[0])
    time.sleep(1)
    b = v.biome
    if b not in missing:
        print(f"  predicted {found[1]} but over {b}; retry", flush=True)
        continue
    r = ksp("eva", "out")
    if r.returncode != 0 or "kerbal" not in r.stdout:
        print("EVA FAILED", r.stdout, r.stderr[-300:], flush=True)
        break
    k = s.active_vessel
    rep = ksp("eva", "report").stdout.strip()
    kb = k.biome
    print(f"  {kb}: {rep}", flush=True)
    bd = ksp("eva", "board")
    time.sleep(2)
    if s.active_vessel.type.name == "eva" or s.active_vessel.crew_count < 1:
        print("BOARDING PROBLEM", bd.stdout, bd.stderr[-300:], flush=True)
        break
    missing.discard(kb)  # only what the kerbal actually reported
    print(f"  left {len(missing)}: {sorted(missing)}", flush=True)
