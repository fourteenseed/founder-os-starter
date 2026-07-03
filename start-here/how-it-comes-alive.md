# How it comes alive

The pages are deliberately dumb: plain HTML that reads small data files. All the life comes from three loops running underneath, and from a handful of tools each doing the one job it's best at. This file is the practical wiring for a stack like Claude + Codex + a local runtime, because that's the reader this is for: someone whose work is already spread across several tools and who wants it connected instead of carried.

## The cast, and what each one actually does

- **Claude (or your main chat tool)** is where most agents live. Its scheduled tasks are your colleagues: each one fires on a trigger, does its job, and writes a dated markdown file into a folder. That folder of files is the OS's raw truth.
- **Codex (or your second tool)** is another building with a different faculty, often the coding work, and often a second lane entirely: the original routes its personal email into Codex and its work email into Claude, so life and work stay separate at the surface level.
- **A local always-on runtime** (Hermes if you run it, otherwise plain cron on Mac and Linux or Task Scheduler on Windows) is the engine block: the thing that runs scripts on a clock even when no chat window is open. This is what makes the OS alive rather than something you have to visit and wind up.
- **A task board** (Linear on the free tier, or whatever your agent has a connector for) holds the work moving between you and the agents, with receipts.
- **A memory store** (Open Brain in the original; use whichever system works for you) holds what the campus remembers.
- **Git** holds the procedures (skills) and the websites.
- **The calendar** holds the human week.
- **The tiny local server** hands all of it to your browser at a bookmark.

Connectors (MCP servers, in current tooling) are the keycards: they're how an agent in Claude reads your calendar, updates the task board, or captures to the memory store. Each connector is a door an agent can open; the OS just makes the doors visible.

## Loop 1: the heartbeat

This is the loop that keeps the pages true, and if you wire only one thing, wire this.

1. Scheduled agents run through the morning (say 06:00 to 08:30) and each writes a dated output file into its folder.
2. A small compile script reads those folders, checks each agent's newest file against its expected rhythm, and writes one small JSON file: who ran, when, what's stale.
3. The runtime (Hermes, cron, whatever you have) runs that compile on a fixed schedule. The original runs it at 08:00, 12:00, 17:00, and 22:00, matching when its human actually checks in.
4. The pages read the JSON. The floor's dots, the freshness line in the footer, the rota's reads: all of it is just this one file, recomputed against the clock each time you look.

No step in that loop needs a chat window open. That's the point: by the time you sit down with your coffee, the floor already knows who showed up.

## Loop 2: the work loop

This is how a job moves between tools without you carrying it.

1. Work enters as a card on the task board, written as a proper record: what's wanted, what sources, what boundaries, what proof.
2. An agent (in whichever tool suits the job) claims the card, does the scoped work, and leaves a receipt: what changed, where the output is, what still needs a human.
3. The card that needs a human shows up in the engine room's "waiting on you" lane, as a link. You click through to the board itself; the OS never keeps its own copy.
4. Outputs land as files (the record office), so the next agent, or the next tool, or tomorrow's you, can pick up from the file rather than from a memory of a chat.

The handoff between Claude and Codex is exactly this: not an integration, just a card and a file both can see. One tool's result becomes the next tool's task because both read the same board and the same folders.

## Loop 3: the human loop

This is the loop you're in, and it closes the circle.

1. Morning: the floor tells you who showed up; the green tells you what your day holds; the engine tells you what waits on you.
2. You sit down in the work room, copy the pickup prompt into whichever tool you're using today, and it hands you back your own context from yesterday's closeout file.
3. Evening: the closeout prompt writes today's note to the project folder.
4. That note is data. Tomorrow's pickup reads it; the compile can see the project moved; over weeks, those notes become the honest activity trail the rest of the OS runs on.

The loop's quiet trick: using the OS is what feeds the OS. There's no separate diligence, no journalling habit to maintain. Close out your day and the machine has what it needs.

## The minimal wiring, if you have two tools and an afternoon

1. Point your scheduled agents' outputs at one folder (or find where they already write).
2. Have your agent write the compile script and schedule it with cron or Task Scheduler: read folders, write one JSON.
3. Build the floor page against that JSON, serve it locally, bookmark it.
4. Create one card on a free task board and run one claim-work-receipt loop with any agent.
5. Add the closeout prompt to your evenings.

That's a living OS: a heartbeat, one work loop, one human loop. Everything else in the rooms is addition, not foundation.

## What stays manual, on purpose

Sending, publishing, deploying, spending, and anything leaving the building: these never automate, whatever your stack. The loops bring the work to your signature; they don't forge it.
