"""Jool fleet plan: every offline check in one run (no kRPC). The parts are separate scripts next to this one:
transfer (window, Lambert, mid-course, arrival geometry), window (its width, the Mun on the escape path), arrival (the
moon's phase inside Jool's SOI), meet (best meeting points, links), stages (the pad check, dv budgets), capture (finite
burns), land (flight.land simulated), entry (Laythe). docs/jool-fleet-plan.md quotes their output.
Run: uv run python tools/scratch/jool_fleet_plan.py [part ...]"""
import os
import runpy
import sys

PARTS = ["transfer", "window", "arrival", "meet", "stages", "capture", "land", "entry"]

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    for p in sys.argv[1:] or PARTS:
        print(f"\n{'=' * 30} {p} {'=' * 30}", flush=True)
        runpy.run_path(os.path.join(here, f"jool_fleet_{p}.py"), run_name="__main__")
