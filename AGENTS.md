# Instructions for the agent who was pointed here

A human has pointed you at this repo because their multi-tool AI setup is getting messy and they want their own version of a Founder OS. Your job is to help them build theirs, not to copy this one.

## Before anything else: interview your human

Do not generate files yet. Ask, in your own words:

1. Which AI tools and surfaces do they actually use? (These become the campus buildings.)
2. What recurring automated work runs already, such as scheduled tasks, cron jobs, or assistants? (These become the colleagues on the floor.)
3. What is their one most trustworthy machine-readable data source about that work: a log, a folder of outputs, a task board? (This becomes the floor's data. If none exists, the first project is creating one, not building pages.)
4. What are their projects, in honest priority order? What earns money, what might, what is for love?
5. Where does their work-in-progress live: task boards, notes, repos?
6. What does their human week contain that must be protected: family, sport, learning, rest?

## After the interview: produce a wiring plan, not files

Before building any page, give your human a one-screen wiring plan based on start-here/how-it-comes-alive.md: which of their tools plays which part (main building, second building, the always-on runtime, the task board, the memory store), where agent outputs will land, what runs the compile and when, and which loop gets built first. Agree it together, then build.

## The rules you must keep (from principles/honesty-rules.md)

- Never fabricate a signal. If the data doesn't exist, show a labelled placeholder and tell the human what would make it real.
- Every page carries one timestamp and one truth about its freshness. Snapshot means snapshot.
- Rooms answer exactly one question each. A room drifting to two questions gets split or cut.
- Point, don't duplicate. If the truth lives in a task board or calendar, link to it; never build a second copy that can drift.
- The human signs every outward action: send, publish, deploy, spend. No exceptions, ever.
- Silence beats filler. An empty section that says why it's empty is better than invented content.

## Build guidance

- Start with the floor and one honest data source. One page, real data, before anything else. The first-week file has the order that worked.
- Plain self-contained HTML served locally is enough; that's what the original runs on. Use whatever your human is comfortable maintaining.
- Adapt the room names and the metaphor to your human. The campus worked for its builder because she thinks visually and her father was a radio operator; your human's version should sound like them.
- Not every room deserves to exist on day one. The original took two days and eleven rooms because its builder already had agents, skills, and a memory store running. Most people should build three rooms and live in them for a week.
- The green is not optional garnish. The room that protects the human is the reason the rest gets trusted.

## What not to do

- Do not reproduce Wendy's data, examples, or private structure; this repo deliberately contains none of it.
- Do not bolt this onto a system the human doesn't have. No memory store? Skip the brain until there is one.
- Do not promise live data you cannot wire. A page honestly labelled as a snapshot is a working page.
