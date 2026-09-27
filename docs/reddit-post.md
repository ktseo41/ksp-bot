# Reddit post draft (images: docs/media/summary/reddit/1-crafts.png, 2-where.png, 3-numbers.png)

Numbers as of 2026-09-27 (launch #53, UT 50.80M), from docs/record/career.json.

## Title (pick one)
- I let an AI (Claude) play a KSP career from scratch. 53 launches later it has landed on Minmus, the Mun, Duna, Moho, Eve and Gilly
- An AI has been playing my KSP career for 4 days: 53 launches, crew home from Duna, probes on the way to Jool, Dres and Eeloo

## Body
I gave Claude Code one goal: start a new Normal career and get as far as it can. It designs every craft (as a list
of parts), builds it, and flies it through kRPC with flight code it wrote itself. No MechJeb or other autopilot mods,
and I never touched the controls.

After 4 real days (~5.5 Kerbin years in game):

- 53 launches: 29 successes, 13 reverted, 4 failed, 3 crews lost (all on day one), 4 still flying
- Crew landed and came home from Minmus, the Mun and Duna
- Uncrewed landers on Moho, Eve (splashdown) and Gilly
- 5 CommNet relays, a science lab station at Minmus, 6 stranded kerbals rescued with the Klaw
- Probes on the way to Jool, Dres and Eeloo

It pays for everything, reverts only when the game offers it (hence the 13), and quickloads only when its own
tooling broke.

Most failures were its own bugs, fixed in code afterwards: a burn that flipped an orbit retrograde, a landing script
that died at 28 km over Duna, a Klaw that bounced off four times because the craft files it generated were missing
data.

1: milestone crafts on the pad · 2: in-game screenshots · 3: the numbers

## If someone asks how it works (comment)
Claude Code runs in a terminal next to the game. KSP talks to it through kRPC plus a small helper mod it wrote (craft
building from JSON, tech research, contracts, KSP's flight log). Each flight phase is one command it wrote in Python
(ascent, transfer, capture, land, reentry...) and every flight is recorded at 1 Hz; after a failure it reads the
recording, finds the cause and fixes the code or the design before flying again.
