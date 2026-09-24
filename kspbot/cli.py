"""`uv run ksp <command>` — one command per game action or mission phase."""
import argparse
import json
import math
import sys
import time

from . import flight
from .core import bot, sc, say, screenshot, status, wait_ready


def _j(s):
    return json.loads(s)


def cmd_status(a):
    s = status()
    print(json.dumps(s))
    if s["scene"] == "FLIGHT":
        cmd_vessel(a)


def cmd_vessel(a):
    v = sc().active_vessel
    o = v.orbit
    fl = v.flight(o.body.reference_frame)
    print(f"{v.name} [{v.situation.name}] body={o.body.name} alt={fl.mean_altitude:.0f} "
          f"radar={fl.surface_altitude:.0f} speed={fl.speed:.1f} vs={fl.vertical_speed:.1f} "
          f"hs={fl.horizontal_speed:.1f}")
    print(f"orbit: pe={o.periapsis_altitude:.0f} ap={o.apoapsis_altitude:.0f} inc={math.degrees(o.inclination):.2f} "
          f"ecc={o.eccentricity:.3f} t_ap={o.time_to_apoapsis:.0f}s soi_change={o.time_to_soi_change:.0f}s "
          f"next={o.next_orbit.body.name if o.next_orbit else None}")
    print(f"mass={v.mass/1000:.2f}t thrust={v.available_thrust/1000:.1f}kN stage={v.control.current_stage} "
          f"crew={[c.name for c in v.crew]} biome={v.biome}")
    res = v.resources
    print("resources:", {n: round(res.amount(n), 1) for n in res.names})
    try:
        stages = [st for st in v.stages if st.delta_v > 0.5]
    except Exception:
        stages = []  # KSP has not computed delta-v yet (right after scene load)
    for st in stages:
        if True:
            print(f"  stage {st.number}: dv={st.delta_v:.0f} (vac {st.vacuum_delta_v:.0f}) twr={st.twr:.2f} "
                  f"burn={st.burn_time:.0f}s")
    try:
        for n in v.control.nodes:
            print(f"  node in {n.ut - sc().ut:.0f}s dv={n.delta_v:.1f}")
    except Exception:
        pass  # maneuver nodes locked (Mission Control / Tracking Station level)


def cmd_parts(a):
    for p in _j(bot().parts(not a.all)):
        if a.filter and a.filter.lower() not in (p["name"] + p["title"] + p["category"]).lower():
            continue
        extra = ""
        if "engine" in p:
            e = p["engine"]
            extra += f" thrust={e['thrust']} isp={e['ispAsl']:.0f}/{e['ispVac']:.0f} gimbal={e['gimbal']}"
        if "resources" in p:
            extra += " " + ",".join(f"{k}={v:g}" for k, v in p["resources"].items())
        if "experiments" in p:
            extra += " exp=" + ",".join(p["experiments"])
        print(f"{p['name']:<28} {p['title'][:34]:<34} {p['category']:<11} ${p['cost']:<6g} "
              f"{p['wetMass']:.3f}t nodes={','.join(p['stackNodes'])}{' srf' if p['srfAttachable'] else ''}"
              f"{' crew=' + str(p['crew']) if p['crew'] else ''}{extra}"
              f"{'' if p['usable'] else ' [locked:' + p['tech'] + ']'}")


def cmd_tech(a):
    for n in _j(bot().tech_tree()):
        if a.all or n["researchable"]:
            flag = "done" if n["researched"] else ("READY" if n["researchable"] else "")
            print(f"{n['id']:<28} {n['cost']:>5} {flag:<5} {n['title']} <- {','.join(n['parents'])}: "
                  f"{', '.join(n['parts'])}")


def cmd_research(a):
    print(bot().research(a.id))


def cmd_facilities(a):
    f = _j(bot().facilities())
    for x in f["facilities"]:
        print(f"{x['id']:<40} level {x['level']}/{x['maxLevel']}  upgrade ${x.get('upgradeCost', '-')}")
    print(json.dumps(f["limits"]))


def cmd_upgrade(a):
    print(bot().upgrade_facility(a.id))


def _contracts(kind):
    # kRPC's active_contracts list can miss freshly accepted contracts; filter all_contracts by state.
    # all_contracts can also keep a just-completed contract as "active": drop anything in completed_contracts.
    cm = sc().contract_manager
    done = {c._object_id for c in cm.completed_contracts}
    return [c for c in cm.all_contracts if c.state.name == kind and c._object_id not in done]


def cmd_contracts(a):
    for kind in ("active", "offered"):
        for i, c in enumerate(_contracts(kind)):
            print(f"[{kind} {i}] {c.title} | adv ${c.funds_advance:.0f} done ${c.funds_completion:.0f} "
                  f"sci {c.science_completion:.0f} rep {c.reputation_completion:.0f}")
            if kind == "active" or a.verbose:
                for p in c.parameters:
                    kids = [q.title for q in p.children]
                    print(f"      - {'[x]' if p.completed else '[ ]'} {p.title}" + (f" {kids}" if kids else ""))


def _pick(kind, key):
    cs = _contracts(kind)
    if key.isdigit():
        return cs[int(key)]
    hits = [c for c in cs if key.lower() in c.title.lower()]
    if len(hits) != 1:
        raise SystemExit(f"'{key}' matches {len(hits)} {kind} contracts: {[c.title for c in hits]}")
    return hits[0]


def cmd_accept(a):
    c = _pick("offered", a.key)
    c.accept()
    time.sleep(1)
    ok = any(x.title == c.title for x in _contracts("active"))
    print("accepted:" if ok else "ACCEPT FAILED:", c.title)


def cmd_decline(a):
    c = _pick("offered", a.key)
    c.decline()
    print("declined:", c.title)


def cmd_build(a):
    with open(a.spec) as f:
        spec = f.read()
    print(bot().build_craft(spec))


def _clear_pad(radius_deg=0.01):
    """Recover landed vessels/debris near the pad (~1 km): KSP only clears a vessel sitting exactly on it, and
    boosters left beside it made new crafts explode at spawn (Jeb lost twice, 2026-09-24)."""
    s = sc()
    kerbin = s.bodies["Kerbin"]
    pad_lat, pad_lon = -0.0972, -74.5577
    for v in list(s.vessels):
        if v.orbit.body != kerbin or v.situation.name not in ("landed", "splashed", "pre_launch"):
            continue
        pos = v.position(kerbin.reference_frame)
        lat, lon = kerbin.latitude_at_position(pos, kerbin.reference_frame), kerbin.longitude_at_position(pos, kerbin.reference_frame)
        if abs(lat - pad_lat) < radius_deg and abs(lon - pad_lon) < radius_deg:
            try:
                v.recover()
                print("cleared from pad area:", v.name)
            except Exception as e:
                print("could not clear", v.name, e)


def cmd_launch(a):
    try:
        _clear_pad()
    except Exception as e:  # some calls are flight-scene only
        print("pad check skipped:", str(e).splitlines()[0])
    sc().launch_vessel("VAB", a.craft, "LaunchPad", a.crew or [])
    time.sleep(5)
    try:
        bot().dismiss_dialogs()
    except Exception:
        pass  # older mod build
    cmd_vessel(a)


def cmd_recover(a):
    v = sc().active_vessel
    before = status()
    v.recover()
    time.sleep(4)
    after = status()
    print(f"recovered; funds {before.get('funds', 0):.0f} -> {after.get('funds', 0):.0f}, "
          f"science {before.get('science', 0):.1f} -> {after.get('science', 0):.1f}")


def cmd_scene(a):
    sc_mod = __import__("krpc").client  # noqa
    conn = __import__("kspbot.core", fromlist=["conn"]).conn()
    names = {s.name: s for s in conn.krpc.GameScene}
    if status()["scene"] == "FLIGHT":
        sc().save("persistent")  # kRPC's scene switch doesn't save: leaving flight would roll back to the last autosave
        time.sleep(1)
    conn.krpc.game_scene = names[a.name]
    time.sleep(3)
    print(status())


def cmd_fly(a):
    bot().fly_vessel(a.name)
    time.sleep(10)
    for _ in range(60):
        if status()["scene"] == "FLIGHT":
            break
        time.sleep(2)
    bot().dismiss_dialogs()
    print(status())


def cmd_load_save(a):
    before = status()["save"]
    bot().load_save(a.name)
    time.sleep(8)
    for _ in range(90):
        try:
            s = status()
            if s["save"] == a.name and s["scene"] == "SPACECENTER":
                print(s)
                return
        except Exception:
            pass
        time.sleep(2)
    raise SystemExit(f"save {a.name} did not load (was {before})")


def cmd_shot(a):
    print(screenshot(a.name))


def cmd_hire(a):
    print(bot().hire_kerbal())


def cmd_stage(a):
    v = sc().active_vessel
    v.control.activate_next_stage()
    print("stage now", v.control.current_stage)


def cmd_science(a):
    flight.do_science(transmit=a.transmit)


def cmd_warp(a):
    t = float(a.ut[1:]) + sc().ut if a.ut.startswith("+") else float(a.ut)
    flight.warp_to(t)
    print("ut", sc().ut)


def cmd_log(a):
    import glob
    import os
    from .recorder import FLIGHT_DIR, summary
    files = sorted(glob.glob(os.path.join(FLIGHT_DIR, "*.jsonl")), key=os.path.getmtime)
    if not files:
        print("no flight logs")
        return
    path = files[-1] if not a.file else a.file
    print(path)
    for line in summary(path, a.n):
        print(line)


def cmd_sandbox_orbit(a):
    bot().sandbox_set_orbit(a.body, a.alt, a.inc)
    time.sleep(3)
    cmd_vessel(a)


def cmd_eva(a):
    """out | state | report | flag | board (the first crew member; science via kRPC on the EVA kerbal)."""
    b = bot()
    if a.action == "out":
        print(b.eva_spawn())
    elif a.action == "state":
        print(b.eva_state())
    elif a.action == "flag":
        b.eva_plant_flag()
        time.sleep(8)
        b.dismiss_dialogs()  # the flag naming/plaque dialog
        print(b.eva_state())
    elif a.action == "board":
        b.eva_board()
        time.sleep(2)
        cmd_vessel(a)
    elif a.action == "report":
        from . import flight
        for e in flight.vessel().parts.experiments:
            if e.available and not e.has_data:
                e.run()
        time.sleep(1.5)
        for e in flight.vessel().parts.experiments:
            if e.has_data:
                print(e.title, e.science_subject.title, sum(d.science_value for d in e.data))


def cmd_wait(a):
    print(wait_ready())


PHASES = {
    "ascent": lambda a: flight.ascent(a.alt, a.heading),
    "circularize": lambda a: flight.circularize(a.at),
    "periapsis": lambda a: flight.change_periapsis(a.alt),
    "transfer": lambda a: flight.transfer_to(a.body, a.pe),
    "correct": lambda a: flight.correct_course(a.body, a.pe, a.inc),
    "soi": lambda a: flight.warp_to_soi(),
    "capture": lambda a: flight.capture(a.apo),
    "land": lambda a: (flight.land_atmo() if flight.vessel().orbit.body.has_atmosphere else flight.land(biomes=a.biome, max_slope=a.slope)),
    "liftoff": lambda a: flight.liftoff(a.alt, a.heading),
    "return": lambda a: flight.return_to_parent(a.pe),
    "reentry": lambda a: flight.reentry(a.main_alt, a.main_speed),
    "node": lambda a: flight.execute_node(),
    "hop": lambda a: flight.hop(not a.no_science, a.heading, a.pitch),
    "survey": lambda a: flight.survey(a.kind, a.dist),
}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ksp")
    sub = ap.add_subparsers(dest="cmd", required=True)
    add = lambda name, fn, **kw: sub.add_parser(name, **kw).set_defaults(fn=fn) or sub.choices[name]

    add("status", cmd_status, help="scene, funds, science; vessel summary in flight")
    add("vessel", cmd_vessel, help="active vessel summary")
    p = add("parts", cmd_parts, help="usable parts (--all: include locked)")
    p.add_argument("filter", nargs="?")
    p.add_argument("--all", action="store_true")
    p = add("tech", cmd_tech, help="researchable tech nodes (--all: whole tree)")
    p.add_argument("--all", action="store_true")
    p = add("research", cmd_research)
    p.add_argument("id")
    add("facilities", cmd_facilities, help="facility levels, upgrade costs, limits")
    p = add("upgrade", cmd_upgrade, help="upgrade facility, e.g. MissionControl")
    p.add_argument("id")
    p = add("contracts", cmd_contracts)
    p.add_argument("-v", "--verbose", action="store_true")
    p = add("accept", cmd_accept, help="accept an offered contract by title substring (or index)")
    p.add_argument("key")
    p = add("decline", cmd_decline)
    p.add_argument("key")
    p = add("build", cmd_build, help="build a .craft from a JSON spec file")
    p.add_argument("spec")
    p = add("launch", cmd_launch, help="roll out a VAB craft to the launch pad (pays its cost)")
    p.add_argument("craft")
    p.add_argument("--crew", nargs="*")
    add("recover", cmd_recover)
    p = add("scene", cmd_scene, help="space_center | tracking_station | editor_vab | flight")
    p.add_argument("name")
    p = add("load-save", cmd_load_save, help="switch to another save folder without restarting KSP")
    p.add_argument("name")
    p = add("fly", cmd_fly, help="from the space center: fly (switch to) the named vessel")
    p.add_argument("name")
    p = add("shot", cmd_shot, help="screenshot of the game -> runs/<name>.png")
    p.add_argument("name", nargs="?", default="shot")
    add("hire", cmd_hire)
    add("stage", cmd_stage)
    p = add("science", cmd_science, help="run all fresh experiments")
    p.add_argument("--transmit", action="store_true")
    p = add("warp", cmd_warp, help="warp to UT or +seconds")
    p.add_argument("ut")
    p = add("eva", cmd_eva, help="EVA: out | state | report | flag | board")
    p.add_argument("action", choices=["out", "state", "report", "flag", "board"])
    add("wait", cmd_wait, help="wait until KSP is up with a save loaded")
    p = add("sandbox-orbit", cmd_sandbox_orbit, help="TEST ONLY: teleport to a circular orbit (sandbox saves)")
    p.add_argument("body")
    p.add_argument("--alt", type=float, default=15000)
    p.add_argument("--inc", type=float, default=0)
    p = add("log", cmd_log, help="events of the latest flight log (runs/flights)")
    p.add_argument("file", nargs="?")
    p.add_argument("-n", type=int, default=30)

    p = add("ascent", PHASES["ascent"], help="launch to apoapsis --alt")
    p.add_argument("--alt", type=float, default=80000)
    p.add_argument("--heading", type=float, default=90)
    p = add("circularize", PHASES["circularize"])
    p.add_argument("--at", default="apoapsis", choices=["apoapsis", "periapsis"])
    p = add("periapsis", PHASES["periapsis"], help="burn at apoapsis to set periapsis --alt")
    p.add_argument("--alt", type=float, required=True)
    p = add("transfer", PHASES["transfer"], help="Hohmann transfer to a moon or (at the window) a planet, tuned for periapsis --pe")
    p.add_argument("body")
    p.add_argument("--pe", type=float, default=20000)
    p = add("correct", PHASES["correct"], help="mid-course correction for periapsis --pe")
    p.add_argument("body")
    p.add_argument("--pe", type=float, default=20000)
    p.add_argument("--inc", type=float, help="minimum arrival inclination (deg)")
    p = add("window", lambda a: flight.planet_window(a.body), help="next Hohmann window to another planet")
    p.add_argument("body")
    add("soi", PHASES["soi"], help="warp to the next SOI change")
    p = add("capture", PHASES["capture"], help="burn at periapsis into orbit (circular or --apo)")
    p.add_argument("--apo", type=float)
    p = add("land", PHASES["land"], help="powered landing (airless), or entry + chutes + powered touchdown (atmosphere)")
    p.add_argument("--biome", nargs="*", help="wait for a gentle site in one of these biomes first")
    p.add_argument("--slope", type=float, default=5.0, help="max terrain slope (deg) for --biome sites")
    p = add("liftoff", PHASES["liftoff"], help="take off from an airless body into orbit")
    p.add_argument("--alt", type=float, default=15000)
    p.add_argument("--heading", type=float, default=90)
    p = add("return", PHASES["return"], help="leave a moon for the parent with periapsis --pe")
    p.add_argument("--pe", type=float, default=30000)
    p = add("reentry", PHASES["reentry"], help="coast to atmosphere, drop stages, drogues, main chutes, land")
    p.add_argument("--main-alt", type=float, default=4000)
    p.add_argument("--main-speed", type=float, default=250)
    add("node", PHASES["node"], help="execute the next maneuver node")
    p = add("survey", PHASES["survey"], help="orbital survey contract: run the experiment over each waypoint")
    p.add_argument("--kind", default="temperature")
    p.add_argument("--dist", type=float, default=8000.0)
    p = add("hop", PHASES["hop"], help="suborbital hop: launch, science at apex, chutes")
    p.add_argument("--no-science", action="store_true")
    p.add_argument("--heading", type=float, default=90)
    p.add_argument("--pitch", type=float, default=90)

    a = ap.parse_args(argv)
    try:
        if a.cmd in PHASES or a.cmd in ("stage", "science"):
            from .recorder import Recorder
            with Recorder(a.cmd):
                r = a.fn(a)
        else:
            r = a.fn(a)
    except Exception as e:  # show kRPC server errors compactly
        msg = str(e).split("\nServer stack trace")[0]
        print(f"ERROR: {e.__class__.__name__}: {msg}", file=sys.stderr)
        sys.exit(1)
    if r is False:
        sys.exit(2)


if __name__ == "__main__":
    main()
