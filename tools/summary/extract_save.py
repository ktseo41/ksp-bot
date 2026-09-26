"""Career save -> docs/record/career-save.json (science subjects, researched tech, crew and their career logs).
Run at the space center after a mission: uv run python tools/summary/extract_save.py"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kspbot.core import KSP_DIR, save

save()
t = open(f"{KSP_DIR}/saves/kspbot/persistent.sfs", encoding="utf-8").read()
ros = t[t.index("\n\tROSTER"):]
out = {"kerbals": [], "science": [], "techs": []}
for m in re.finditer(r"\n\t\tKERBAL\n\t\t\{(.*?)\n\t\t\}", ros, re.S):
    b = m.group(1)
    g = lambda k: (re.search(r"\n\t\t\t" + k + r" = (.*)", b) or [None, None])[1]
    log = re.findall(r"\n\t\t\t\t(\d+) = (.*)", b.split("CAREER_LOG")[1]) if "CAREER_LOG" in b else []
    if g("type") != "Applicant":
        out["kerbals"].append(dict(name=g("name"), type=g("type"), trait=g("trait"), state=g("state"),
                                   career_log=[f"{n}:{e}" for n, e in log]))
for m in re.finditer(r"\n\t\tScience\n\t\t\{(.*?)\n\t\t\}", t, re.S):
    d = dict(re.findall(r"\n\t\t\t(\w+) = (.*)", m.group(1)))
    out["science"].append(dict(id=d["id"], title=d["title"], sci=round(float(d["sci"]), 1), cap=round(float(d["cap"]), 1)))
out["techs"] = re.findall(r"\n\t\tTech\n\t\t\{\n\t\t\tid = (\S+)\n\t\t\tstate = Available", t)
dst = Path(__file__).resolve().parents[2] / "docs/record/career-save.json"
json.dump(out, open(dst, "w"), indent=1, ensure_ascii=False)
print(f"{dst}: {len(out['science'])} subjects, {sum(s['sci'] for s in out['science']):.1f} sci, {len(out['techs'])} tech")
