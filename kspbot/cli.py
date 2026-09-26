"""`uv run ksp <command>` — one command per game action or mission phase."""
import argparse
import json
import math
import sys
import time

from . import flight
from .core import SaveFailed, bot, check_save, save, sc, say, screenshot, status, wait_ready


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
        # KSP has not computed delta-v yet: right after scene load, or for hours after `fly` (Moho 1)
        flight._recalc_delta_v(v)
        try:
            stages = [st for st in v.stages if st.delta_v > 0.5]
        except Exception as e:
            stages = []
            print(f"  stages: {e}")
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
    if ok:
        try:
            save()  # see cmd_launch
        except SaveFailed as e:
            # 2026-09-26: the save threw an NRE (FlightState ctor) right after a flight; the accept had worked, the
            # error made me retry "accept 4", the list had shifted and a second contract (Ike station) got accepted
            raise SystemExit(f"accepted, but {e}; don't retry the accept")


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
    if status().get("scene") == "FLIGHT":  # vessel positions are flight-scene only
        _clear_pad()
    # kRPC's LaunchVessel goes to the flight scene without saving: contracts accepted at the space center since
    # the last save came back as merely offered in flight (the three accepted 2026-09-25 were lost, advances kept).
    if status().get("scene") != "FLIGHT":
        save()
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
    for _ in range(20):  # the recovery rewards land a few seconds after the space center loads
        time.sleep(1)
        after = status()
        if after.get("scene") == "SPACECENTER" and (after.get("funds") != before.get("funds")
                                                    or after.get("science") != before.get("science")):
            break
    print(f"recovered; funds {before.get('funds', 0):.0f} -> {after.get('funds', 0):.0f}, "
          f"science {before.get('science', 0):.1f} -> {after.get('science', 0):.1f}")


SCENE_OF = {"space_center": "SPACECENTER", "tracking_station": "TRACKSTATION", "editor_vab": "EDITOR",
            "editor_sph": "EDITOR", "flight": "FLIGHT"}  # other kRPC scenes are space-center facilities


def cmd_scene(a):
    """Every switch saves first (KSP's buildings do; a switch without a save drops everything since the last one)
    and nothing switches if that save fails. The space center and the tracking station are loaded by the mod from
    the Update phase: kRPC switches from FixedUpdate, which once left FlightGlobals broken at the space center
    and every save throwing (2026-09-26)."""
    want = SCENE_OF.get(a.name, "SPACECENTER")
    if a.name in ("space_center", "tracking_station") and status()["scene"] != want:
        check_save(_j(bot().switch_scene(a.name))["save"])
    else:  # also closes an open space-center facility
        save()
        conn = __import__("kspbot.core", fromlist=["conn"]).conn()
        conn.krpc.game_scene = {s.name: s for s in conn.krpc.GameScene}[a.name]
    end = time.time() + 180
    while True:
        time.sleep(2)
        try:
            s = status()  # the mod's Status() also clears a stale FlightGlobals.ready
        except Exception:
            s = {}
        if s.get("scene") == want and s.get("loaded") == want:
            break
        if time.time() > end:
            raise SystemExit(f"scene {want} did not load within 180 s: {s}")
    print(json.dumps(s))
    if want != "FLIGHT":  # right after a flight loads, FlightGlobals may not be ready: the save would lose the focus
        r = save()
        print(f"test save ok (ready={r['ready']}, cleared stale flag={r['fixedReady']})")


def cmd_warp_any(a):
    """Warp to UT (or +seconds) from the space center / tracking station, where warp is unlimited."""
    t = float(a.ut[1:]) + status()["ut"] if a.ut.startswith("+") else float(a.ut)
    bot().warp_to(t)
    while status()["ut"] < t - 60:
        time.sleep(2)
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
    new = v.control.activate_next_stage()
    print("stage now", v.control.current_stage)
    if not new:
        return
    time.sleep(1)
    for x in new:
        try:
            print(f"separated: {x.name} ({x.type.name}, {len(x.parts.all)} parts"
                  f"{', command part' if flight._has_command(x) else ''})")
        except Exception:
            pass  # already destroyed / unloaded
    if not flight._has_command(v):
        # a decoupler leaves the root's side active: the Eve 2 lander (root Terrier) stays on the dropped stage
        print(f"!! the active vessel {v.name} has no command part now: `ksp switch NAME` to the separated one")


def cmd_switch(a):
    flight.switch_to(a.name)
    cmd_vessel(a)


def _reentry(a):
    v = flight.vessel()
    packed = flight.packed_shields(v)
    if packed and not a.packed_ok:
        raise flight.Refused(f"{len(packed)} inflatable heat shield(s) not inflated: `ksp inflate` first "
                             "(or --packed-ok)")
    return flight.reentry(a.main_alt, a.main_speed, a.keep_until, a.science)


def _land(a):
    if flight.vessel().orbit.body.has_atmosphere:
        return flight.land_atmo(a.pe, ignore_link=a.ignore_link, science=a.science)
    if a.science:
        print("--science is for atmospheric landings (flying high/low sets); here run `science --transmit` after")
    return flight.land(biomes=a.biome, max_slope=a.slope, orbits=a.orbits, at=a.at)


def cmd_science(a):
    flight.do_science(transmit=a.transmit or a.all, min_single=a.min_single, all_=a.all)


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
        # the kerbal's spawn kicks the vessel (MPL: ~0.08 m/s, ~6 deg/s): let its SAS damp that
        ship = flight.vessel()
        ship.control.sas = True
        print(b.eva_spawn())
        time.sleep(6)
        o = ship.orbit
        print(f"{ship.name} after the EVA: pe {o.periapsis_altitude / 1000:.1f} km, ap {o.apoapsis_altitude / 1000:.1f} km")
    elif a.action == "state":
        print(b.eva_state())
    elif a.action == "check":
        print(b.eva_check(1.0))
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
        v = flight.vessel()
        if v.type.name != "eva":
            # MS2: after a failed `eva out` this ran every experiment of the ship (5 Science Jrs, 6 goo) in space
            raise SystemExit(f"active vessel {v.name} is not an EVA kerbal: not running anything")
        for e in v.parts.experiments:
            if e.available and not e.has_data:
                e.run()
        time.sleep(1.5)
        for e in flight.vessel().parts.experiments:
            if e.has_data:
                print(e.title, e.science_subject.title, sum(d.science_value for d in e.data))


def cmd_lab(a):
    """Mobile Processing Lab on the active vessel (docs/lab/README.md)."""
    b = bot()
    if a.action in ("process", "dry"):
        r = json.loads(b.lab_process(a.action == "dry"))
        for it in r["items"]:
            print(f"{it['labValue']:6.0f}  {it['result']:18s} {it['subject']}  ({it['part']})")
        print("data stored", r["dataStored"])
        return
    if a.action == "transmit":
        # a transmit with too little EC does nothing and reports nothing (2,056 and 2,102 EC failed, 2,425 worked)
        ec = sc().active_vessel.resources.amount("ElectricCharge")
        if ec < 3000:
            raise SystemExit(f"EC {ec:.0f} < 3000: charge in sunlight first (a transmit with ~2,100 EC fails silently)")
        before = sc().science
    r = json.loads(b.lab_status() if a.action == "status" else b.lab_action(a.action))
    r["processed"] = len(r["processed"])
    print(json.dumps(r))
    if a.action == "transmit":
        # science arrives when the transmission ends (~6 EC per science at the antenna's rate)
        t0 = time.time()
        while time.time() - t0 < 300:
            time.sleep(5)
            gained = sc().science - before
            if gained > 0.5:
                time.sleep(10)
                print(f"science +{sc().science - before:.1f} (now {sc().science:.1f})")
                return
        raise SystemExit(f"no science arrived within 300 s (EC now "
                         f"{sc().active_vessel.resources.amount('ElectricCharge'):.0f}): transmit failed")


def cmd_wait(a):
    print(wait_ready())


PHASES = {
    "ascent": lambda a: flight.ascent(a.alt, a.heading, twr=a.twr),
    "circularize": lambda a: flight.circularize(a.at),
    "periapsis": lambda a: flight.change_periapsis(a.alt),
    "transfer": lambda a: flight.transfer_to(a.body, a.pe),
    "correct": lambda a: flight.correct_course(a.body, a.pe, a.inc, a.inc_to),
    "soi": lambda a: flight.warp_to_soi(a.force),
    "capture": lambda a: flight.capture(a.apo, a.early),
    "land": _land,
    "liftoff": lambda a: flight.liftoff(a.alt, a.heading),
    "return": lambda a: flight.return_to_parent(a.pe),
    "depart": lambda a: flight.depart_planet(a.body, a.pe, a.at, a.max_arrival, a.horizon),
    "match-orbit": lambda a: flight.match_orbit(a.inc, a.lan, a.argpe, a.sma, a.ecc),
    "wait-plane": lambda a: flight.wait_plane(a.inc, a.lan),
    "reentry": _reentry,
    "deorbit": lambda a: flight.deorbit(a.pe, a.at, a.under, a.sunward, a.ignore_link),
    "inflate": lambda a: flight.inflate(),
    "node": lambda a: flight.execute_node(tol=a.tol, thrust_limit=a.thrust),
    "hop": lambda a: flight.hop(not a.no_science, a.heading, a.pitch),
    "survey": lambda a: flight.survey(a.kind, a.dist),
    "rendezvous": lambda a: _rdv().rendezvous(a.target, a.dist),
    "approach": lambda a: _rdv().approach(_rdv().find_target(a.target), a.dist),
    "grab": lambda a: _rdv().grab(a.target, a.speed, a.face, a.max_contacts),
    "transfer-fuel": lambda a: _rdv().transfer_fuel(a.frac),
    "transfer-crew": lambda a: _rdv().transfer_crew(a.to),
    "release": lambda a: _rdv().release(),
    "balance-fuel": lambda a: _rdv().balance_fuel(),
}


def _rdv():
    from . import rendezvous
    return rendezvous


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
    p.add_argument("--crew", nargs="*", help='kerbal names; "none" launches uncrewed (no names = default crew)')
    add("recover", cmd_recover)
    p = add("scene", cmd_scene, help="space_center | tracking_station | editor_vab | flight")
    p.add_argument("name")
    p = add("load-save", cmd_load_save, help="switch to another save folder without restarting KSP")
    p.add_argument("name")
    p = add("warp-sc", cmd_warp_any, help="warp from the space center / tracking station to UT or +seconds")
    p.add_argument("ut")
    p = add("fly", cmd_fly, help="from the space center: fly (switch to) the named vessel")
    p.add_argument("name")
    p = add("shot", cmd_shot, help="screenshot of the game -> runs/<name>.png")
    p.add_argument("name", nargs="?", default="shot")
    add("hire", cmd_hire)
    add("stage", cmd_stage)
    p = add("science", cmd_science, help="run all fresh experiments")
    p.add_argument("--transmit", action="store_true")
    p.add_argument("--all", action="store_true",
                   help="transmit everything, goo / materials bay too (one-way probes; implies --transmit)")
    p.add_argument("--min-single", type=float, default=15.0,
                   help="run goo/materials bay only if the subject has this much science left")
    p = add("warp", cmd_warp, help="warp to UT or +seconds")
    p.add_argument("ut")
    p = add("eva", cmd_eva, help="EVA: out | state | report | flag | board")
    p.add_argument("action", choices=["out", "state", "check", "report", "flag", "board"])
    p = add("lab", cmd_lab, help="science lab: status | dry | process | start | stop | transmit | clean")
    p.add_argument("action", choices=["status", "dry", "process", "start", "stop", "transmit", "clean"])
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
    p.add_argument("--twr", type=float, help="liftoff TWR: thrust-limit the first stage's SRBs (e.g. 1.5)")
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
    p.add_argument("--inc-to", type=float, help="aim for this arrival inclination (0..180 deg)")
    p = add("window", lambda a: flight.planet_window(a.body), help="next Hohmann window to another planet")
    p.add_argument("body")
    p = add("soi", PHASES["soi"], help="warp to the next SOI change (refused if the periapsis there is under the terrain)")
    p.add_argument("--force", action="store_true", help="warp even if the predicted periapsis is under the terrain")
    p = add("capture", PHASES["capture"], help="burn at periapsis into orbit (circular or --apo)")
    p.add_argument("--apo", type=float)
    p.add_argument("--early", type=float, default=0.0, metavar="S",
                   help="centre the burn S seconds before the periapsis (uncrewed craft: a forecast blackout inside "
                        "the burn moves it earlier by itself, ending >= 25 s before it)")
    p = add("land", PHASES["land"], help="powered landing (airless), or entry + chutes + powered touchdown (atmosphere)")
    p.add_argument("--biome", nargs="*", help="wait for a gentle site in one of these biomes first")
    p.add_argument("--slope", type=float, default=5.0, help="max terrain slope (deg) for --biome sites")
    p.add_argument("--orbits", type=int, default=8, help="how many orbits ahead to search for a --biome site")
    p.add_argument("--at", type=float, nargs=2, metavar=("LAT", "LON"), help="land near this point (a waypoint)")
    p.add_argument("--pe", type=float, default=5000, help="atmosphere: deorbit burn (now) to this periapsis first")
    p.add_argument("--ignore-link", action="store_true",
                   help="atmosphere, uncrewed: burn even with Kerbin < 20 deg up at the predicted periapsis")
    p.add_argument("--science", action="store_true",
                   help="atmosphere, one-way probe: flying high/low science on the way down (in the background, "
                        "the descent control never waits), then the landed set and leftovers like `science --all`")
    p = add("liftoff", PHASES["liftoff"], help="take off from an airless body into orbit")
    p.add_argument("--alt", type=float, default=15000)
    p.add_argument("--heading", type=float, default=90)
    p = add("match-orbit", PHASES["match-orbit"], help="reach an orbit given by elements (a contract's specific orbit)")
    for k in ("inc", "lan", "argpe", "sma", "ecc"):
        p.add_argument("--" + k, type=float, required=True)
    p = add("wait-plane", PHASES["wait-plane"], help="on the pad: warp until launch into plane --inc/--lan, print heading")
    p.add_argument("--inc", type=float, required=True)
    p.add_argument("--lan", type=float, required=True)
    p = add("return", PHASES["return"], help="leave a moon for the parent with periapsis --pe")
    p.add_argument("--pe", type=float, default=30000)
    p = add("depart", PHASES["depart"], help="from an eccentric orbit around a planet, leave for another planet: "
                                            "run 1 plans/burns the plane tilt at the apoapsis, run 2 (--at UT) the periapsis ejection")
    p.add_argument("body")
    p.add_argument("--pe", type=float, default=30000, help="target periapsis for the later mid-course correction")
    p.add_argument("--at", type=float, help="UT of the departure periapsis pass (printed by run 1)")
    p.add_argument("--max-arrival", type=float, help="cap on the arrival v_inf (m/s) when choosing the departure")
    p.add_argument("--horizon", type=float, default=800.0, help="how many days ahead to consider departures")
    p = add("reentry", PHASES["reentry"], help="coast to atmosphere, drop stages, drogues, main chutes, land")
    p.add_argument("--main-alt", type=float, default=4000)
    p.add_argument("--main-speed", type=float, default=250)
    p.add_argument("--keep-until", type=float, help="uncrewed: keep the service module (probe core) on, drop it under chutes below this height")
    p.add_argument("--science", action="store_true",
                   help="one-way probe: run + queue the transmission of fresh experiments at flying high and flying "
                        "low without waiting (the last single-use copy is kept), then after the landing the landed "
                        "set and leftovers like `science --all`")
    p.add_argument("--packed-ok", action="store_true", help="enter with an inflatable heat shield still packed")
    h = "retrograde burn (now, --at UT, or --under BODY) until the periapsis is at --pe; coasts afterwards"
    p = add("deorbit", PHASES["deorbit"], help=h, description=h)
    p.add_argument("--pe", type=float, required=True, help="periapsis altitude to burn down to (m)")
    p.add_argument("--at", type=float, help="centre the burn on this UT")
    p.add_argument("--under", metavar="BODY",
                   help="burn where the new periapsis (the entry) comes to lie under BODY as seen from here (the "
                        "vessel 180 deg from BODY's direction, in the orbit plane), e.g. Kerbin for the direct link")
    p.add_argument("--sunward", type=float, default=0.0, metavar="DEG",
                   help="with --under: rotate that direction DEG towards the Sun (Eve 2: 30 = daylight, Kerbin up; "
                        "negative: away from it)")
    p.add_argument("--ignore-link", action="store_true",
                   help="uncrewed: burn even with Kerbin < 20 deg up at the predicted periapsis (printed always)")
    h = "inflate the inflatable heat shield (refused while an engine is aboard; KSP blocks it while a part sits on its top node)"
    add("inflate", PHASES["inflate"], help=h, description=h)
    h = ("in flight: make the loaded vessel NAME active. A decoupler leaves the root's side active, and a part dropped "
         "from 'X Probe' is named 'X Probe' again: among equal names the one with a command part wins")
    p = add("switch", cmd_switch, help=h, description=h)
    p.add_argument("name", help="exact name, else a prefix, else a substring (case-insensitive)")
    p = add("node", PHASES["node"], help="execute the next maneuver node")
    p.add_argument("--tol", type=float, default=0.2, help="stop at this residual (m/s); far-out trims: 0.02")
    p.add_argument("--thrust", type=float, default=None,
                   help="thrust limit 0..1 for the burn (restored after): a 0.2 m/s trim on a Poodle is 15 ms at full thrust")
    p = add("survey", PHASES["survey"], help="orbital survey contract: run the experiment over each waypoint")
    p.add_argument("--kind", default="temperature")
    p.add_argument("--dist", type=float, default=8000.0)
    p = add("hop", PHASES["hop"], help="suborbital hop: launch, science at apex, chutes")
    p.add_argument("--no-science", action="store_true")
    p.add_argument("--heading", type=float, default=90)
    p.add_argument("--pitch", type=float, default=90)
    p = add("rendezvous", PHASES["rendezvous"], help="match plane, intercept, stop and hold --dist m from the target vessel")
    p.add_argument("target")
    p.add_argument("--dist", type=float, default=25.0)
    p = add("approach", PHASES["approach"], help="close in on a nearby target vessel and hold --dist m")
    p.add_argument("target")
    p.add_argument("--dist", type=float, default=25.0)
    p = add("grab", PHASES["grab"], help="arm the Klaw and drift into the target vessel")
    p.add_argument("target")
    p.add_argument("--speed", type=float, default=0.15)
    p.add_argument("--face", help='side of the target\'s root part to hit, e.g. "-z" (a flat face)')
    p.add_argument("--max-contacts", type=int, default=3, help="stop after this many bounces")
    p = add("transfer-fuel", PHASES["transfer-fuel"], help="after a grab: move our fuel into the grabbed vessel")
    p.add_argument("--frac", type=float, default=1.0)
    p = add("transfer-crew", PHASES["transfer-crew"], help="after a grab: move the grabbed vessel's crew into our free seats")
    p.add_argument("--to", default="mk1pod.v2", help="internal name of our crew part")
    add("release", PHASES["release"], help="open the Klaw")
    add("balance-fuel", PHASES["balance-fuel"], help="even out the fill level of all fuel tanks")

    sub.choices["deorbit"].add_argument("--plan", action="store_true",
                                        help="print the burn (UT, m/s) and the predicted periapsis ground point, stop")
    for name in ("transfer", "correct", "match-orbit", "return", "depart"):
        sub.choices[name].add_argument("--plan", action="store_true",
                                       help="stop at the first tuned node (left in place); burn it with `ksp node`")

    a = ap.parse_args(argv)
    if a.cmd == "reentry" and a.science and a.keep_until is not None:
        ap.error("--science does not work with --keep-until")
    flight.PLAN_ONLY = getattr(a, "plan", False)
    try:
        if a.cmd in PHASES or a.cmd in ("stage", "science"):
            from .recorder import Recorder
            with Recorder(a.cmd) as rec:
                r = a.fn(a)
                _orbit_check(rec)
        else:
            r = a.fn(a)
    except flight.Planned as e:
        then = "run it again without --plan" if a.cmd == "deorbit" else "`ksp node`"
        print(f"PLANNED (not burned): {e}\ncheck it against the expected numbers, then {then}")
        return
    except flight.Refused as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        sys.exit(3)
    except Exception as e:  # show kRPC server errors compactly
        msg = str(e).split("\nServer stack trace")[0]
        print(f"ERROR: {e.__class__.__name__}: {msg}", file=sys.stderr)
        sys.exit(1)
    if r is False:
        sys.exit(2)


def _orbit_check(rec):
    """After every flight phase: an orbiting craft whose periapsis dips into the air is decaying. Rescue 3's
    Klaw bumps left 64.8 x 80.7 km unnoticed until a pass through the atmosphere."""
    try:
        v = flight.vessel()
        b = v.orbit.body
        pe = v.orbit.periapsis_altitude
        if v.situation.name == "orbiting" and b.has_atmosphere and pe < b.atmosphere_depth:
            rec.event("orbit", f"periapsis {pe / 1000:.1f} km is inside {b.name}'s atmosphere "
                               f"({b.atmosphere_depth / 1000:.0f} km): raise it at the apoapsis")
    except Exception:
        pass


if __name__ == "__main__":
    main()
