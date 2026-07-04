# The first week

The build order that actually worked, generalised. The original went floor-to-eleven-rooms in two days, but its builder already had scheduled agents, a skills repo, and a memory store running. Adjust to what exists.

Each day ends with a proof gate: a small test the day's work must pass before you move on. A page can look right and still be lying; the gate is how you find out which. Don't skip them. (The gates were Mark Bunce's suggestion, and they're the same idea as swimming lessons: you move up because you swam a width while the teacher watched, not because you attended.)

**Day 1: the floor, on one honest data source.** Find the single most trustworthy machine-readable trace of your automated work (a log, an output folder, a task list). Build one page: who showed up, when, honestly. If an agent has never run, the page says "no run recorded". If the data is stale, the page says snapshot. Resist every other feature.

> **Proof gate:** switch one agent off, or point the page at an empty folder. Does the page *show* the silence? If it stays green while the agent is dead, the page is lying; fix that before building anything else.

**Day 2: make the data feed itself.** Whatever compiles the floor's data should run on a schedule you don't touch (a cron job, a scheduled task). The page's freshness line now tells the truth without you. This is the day the OS becomes alive instead of decorative.

> **Proof gate:** don't touch anything for a full cycle, then check the freshness line updated on its own. If you had to nudge it, it isn't alive yet.

**Day 3: the green.** Read the real calendar. Mark the protected time. Write the charter: the rules the system obeys about its human. Do this before the productivity rooms, not after; it sets the tone for everything.

> **Proof gate:** is your actual protected time on it? Not an example week: your real Wednesday evening, your real family day. If the page shows a week you don't recognise, it protects nothing.

**Day 4: the engine.** One shared task list (any board an agent can read and update). One task, written as a proper record: outcome, sources, boundaries, blocker rule, receipt. Run one loop end to end: agent claims, works, leaves a receipt. One real receipt teaches more than any amount of reading.

> **Proof gate:** the receipt exists, on the board, in the vocabulary, written by the agent. If the loop ended with the agent saying "done" and no evidence, it didn't end.

**Day 5: the work room.** The bench of prompts you actually reuse: pick up where I left off, close out the day, draft the update. Copy buttons, prompts you can read before copying, everything invoking procedures that live in one place.

> **Proof gate:** copy one prompt into a completely fresh session. Does it work without this conversation's context? A prompt that only works where it was written isn't a tool yet.

**Then stop.** Live in five rooms for a week. Rooms six to eleven (skills, brain, flow, broadcast, estate, connection) each earn their existence when you feel their absence; and you will, one at a time, in whichever order your work demands.
