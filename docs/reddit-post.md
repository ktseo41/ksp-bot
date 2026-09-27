# Reddit post draft (images: docs/media/summary/reddit/1-crafts.png, 2-where.png, 3-numbers.png)

Numbers as of 2026-09-27 (launch #53, UT 50.80M), from docs/record/career.json. The user's own best (saves/science,
Science mode, last saved 2023-03-15): Bob's flight 5 = Duna landing + flag + recovered at Kerbin; no Ike in any save;
saves/20260113 (career, 2026-03) has an uncrewed Eve orbit.

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

For scale: in years of playing on and off, the farthest I ever got myself was Duna (Bob landed, planted a flag and
flew home, in science mode). Claude had Valentina on Duna on its second day and home on the
third.

It pays for everything, reverts only when the game offers it (hence the 13), and quickloads only when its own
tooling broke.

Most failures were its own bugs, fixed in code afterwards: a burn that flipped an orbit retrograde, a landing script
that died at 28 km over Duna, a Klaw that bounced off four times because the craft files it generated were missing
data.

How it felt: at first the fun was just that it worked at all. Then it was watching Claude work its way out, Kerbin to
Minmus to the Mun to Duna, collecting science and finishing contracts along the way. Lately it has gone past anywhere I've
been myself. I woke up one morning to find it had sent a probe to Jool while I was asleep, and it started to feel like
reading someone else's mission reports. What brings the fun back is asking it about each mission: how it put that probe
together, how it worked out the route, why it chose that target. It's clearly a better KSP player than I am. At this
point I at least want to see it visit every planet and finish the tech tree.

1: milestone crafts on the pad, with KSP's vacuum Δv · 2: in-game screenshots · 3: the numbers

Source and the mission-by-mission log: https://github.com/ktseo41/ksp-bot

## If someone asks how it works (comment)
Claude Code runs in a terminal next to the game. KSP talks to it through kRPC plus a small helper mod it wrote (craft
building from JSON, tech research, contracts, KSP's flight log). Each flight phase is one command it wrote in Python
(ascent, transfer, capture, land, reentry...) and every flight is recorded at 1 Hz; after a failure it reads the
recording, finds the cause and fixes the code or the design before flying again.
