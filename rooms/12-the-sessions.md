# The sessions

**The question it answers:** Which of my AI sessions needs me right now?

![the sessions · demo](../assets/demo-the-sessions.png)

*One row per open session, across tools. A raised hand on anything stuck at a permission prompt, a question or a reply. Private sessions show a label and nothing else.*

**The analogy.** The corridor outside the offices. You can't see the work through the doors, and you shouldn't need to; what you can see is which doors have a hand up.

**What's on the page.** Every session with activity in the last day, from the Claude desktop app and from Codex if you use it, in four bands: waiting on you, working now, open and quiet, and finished in the last 24 hours (folded). Each row carries the session's title, one line of what it says (the app's own summary where it wrote one, otherwise the first sentence of its last message), the folder it ran in, the tool, and how long it has been in that state. Tabs switch between all, Claude and Codex. A session whose folder or title matches your privacy list shows only a label such as "Client work". The key at the top counts the rows in each band, and the first count is the one that matters: how many need you.

**The rule it carries.** Show who is waiting, never the work. The page tells you a session is stuck and roughly why; the work stays in the session. Two more, specific to this room: the compiler refuses to run without a privacy list, so there is never an unredacted copy by accident; and the one number it is allowed to show is how many rows need you, because that is the question, not a measure of busyness.

**Inspired by / changed.** The raised hand is the Claude desktop app's own signal for a session that needs you, borrowed as is. The idea of a board for sessions came from one shared in Nate B. Jones's Exec Circle; I borrowed the idea and not the tool. What changed: this one reads the files the app already writes, makes no model calls, and needs nothing new installed; a Python script on a five-minute schedule and a page.

**Building yours.** This is the one room in this repo that ships with working code rather than a pattern, because the hard part is the reading, not the page. [tools/sessions/](../tools/sessions/) holds the compiler, the page, an example privacy list, tests and a launchd job, with a setup note. Make the privacy list first, compile once and read the output file with your own eyes before you serve the page, then put it on the schedule. The proof gate is the same as the floor's: stop the job, wait, and make sure the page says snapshot. The day this room earned its keep in the original, a scheduled run had been sitting at a permission prompt for the best part of a day and a half, and the floor had no way to see it.
