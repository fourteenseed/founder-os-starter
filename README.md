# Founder OS

A calm command centre for a founder who works with more than one AI tool.

I used to run an office of fourteen people. I could look up from my desk and see who was working on what, and know what I could hand off. When I started building with AI agents, I missed that more than anything: the work was happening, but I couldn't see it. Outputs piled up in chat windows. Schedulers broke silently. I couldn't tell you which agent had shown up that morning, and I was the one carrying every piece of work between the tools.

Founder OS is the office I built to fix that. Eleven rooms, each answering exactly one question, all of it running on data that is allowed to say "I don't know". This repo is the vanilla version: the pattern with my private data removed, so you can build your own.

## Who this is for

Founders and operators who use several AI tools at once (Claude and ChatGPT and a local agent and whatever arrives next month) and can feel it getting messy. If you live happily inside one tool, you don't need this. If you've become the courier between five of them, you might.

You don't need to be a developer. I'm not, in the traditional sense. The intended way to use this repo is the way you're probably already working: read this page yourself, then point your AI agent at the rest and build together.

## How to use this repo

Say this to whichever AI agent you work with:

> Read llms.txt and AGENTS.md in this repo, then help me plan my own Founder OS. Interview me first.

That's it. The agent gets its instructions from [AGENTS.md](AGENTS.md); you get a conversation about your own setup rather than a pile of files to decode.

## The campus, in one paragraph

The whole thing runs on one analogy. Your AI tools are buildings on a campus, each with its own faculty: one is better at reasoning and writing, one at code, one at research. Your agents are colleagues, not buildings; a colleague works in a building but isn't owned by it. A keycard is a connection plus a permission, and some doors (send, publish, spend) open only with your signature at the gatehouse. Your memory is the library and your procedures are the workshop: two pillars every building connects to, so nothing is trapped where it was made. And at the centre of the campus is the green, the open space where you are not in any building at all, because a founder OS that can't see your Wednesday badminton will schedule over it forever.

## What it looks like

Three of the rooms, with demo data for a fictional studio. The pages themselves are in [demo/](demo/) — download the repo and open them in any browser, nothing to install.

**The floor** — did my agents show up today? The next move at the top, one line from the chief of staff, and every agent at a named desk with an honest last-ran read.

![The floor](assets/demo-the-floor.png)

**The green** — the week as a human week. Work blocks, life markers, protected time drawn as first-class blocks, and the charter: the rules the system obeys about its human.

![The green](assets/demo-the-green.png)

**The engine** — what waits on a human, what's in motion, and receipts for what the agents proved. It points at the real task board; it never duplicates it.

![The engine](assets/demo-the-engine.png)

## The rooms at a glance

| Room | The one question it answers |
|---|---|
| [The floor](rooms/01-the-floor.md) | Did my agents show up today? |
| [The green](rooms/02-the-green.md) | What does my week look like as a human, not a machine? |
| [The engine](rooms/03-the-engine.md) | What work is moving, and what waits on me? |
| [The work](rooms/04-the-work.md) | Where do I sit down and do the job? |
| [The rota](rooms/05-the-rota.md) | When does everything run, and on whose meter? |
| [The skills](rooms/06-the-skills.md) | How is work done here, and is it owned or rented? |
| [The brain](rooms/07-the-brain.md) | What does my system remember, and is it healthy? |
| [The flow](rooms/08-the-flow.md) | How does data move through my whole stack? |
| [The broadcast](rooms/09-the-broadcast.md) | What am I saying to the world, and on which frequency? |
| [The estate](rooms/10-the-estate.md) | Are my public websites in good order, for people and for agents? |
| [The connection](rooms/11-the-connection.md) | What does all of this mean, and what's worth writing about? |

Read them in that order and you'll walk my daily loop first (floor, green, engine, work), then the reference rooms, then the outward-facing ones. The connection comes last on purpose: it's the room that joins the dots.

## The rules underneath

Every room obeys the same [honesty rules](principles/honesty-rules.md), and they're the actual product. The short version: never fabricate a signal, label every placeholder, one timestamp one truth, silence beats filler, and busyness is not progress. My first version of this dashboard died because it broke those rules. This one has held because it can't.

## Where it came from

Built in the open in Cornwall, mostly by talking to an agent over a couple of days, standing on the shoulders of people who shared their working generously. The concepts this borrows and what was changed are credited properly in [principles/credits.md](principles/credits.md): Nate B. Jones's Open Brain, Open Skills, and Open Engine; Ankit Patel's architecture thinking; and the Exec Circle community around them. The campus metaphor, the honesty rules, and the green are the parts I'd claim as mine.

If you build your own version, I'd genuinely like to see it. wendy@fourteenseed.com

Wendy Harris, Fourteen Seed
Cornwall >> internet
