# The floor

**The question it answers:** Did my agents show up today?

![the floor · demo](../assets/demo-the-floor.png)

*The next move at the top, one line from the chief of staff, and every agent at a named desk with an honest last-ran read.*

**The analogy.** The office floor. You look up from your desk and see your colleagues; except your colleagues are agents, and each is named like a person. The chief of staff sits at the head.

**What's on the page.** One desk per agent: a human name, a plain-language role, and an honest last-ran read: "ran today", "hasn't run since Monday", "no run recorded". A calm green dot when fresh, a quiet amber flag when stale. Above the floor: the single next move (the most important task the data can actually justify), and one line from the chief-of-staff agent; a real handoff, a real decision, or nothing at all.

**The rule it carries.** Never fabricate a signal, and no busyness counts. The floor answers one question: did they show up. Not how much they did: whether they showed up.

**Inspired by / changed.** The genuinely original room. Its trick is emotional: naming agents as people makes staleness feel like a colleague you haven't seen, which makes you actually investigate.

**Building yours.** Start here. One honest data source (agent output files, a scheduler log), one page, recomputed ages at view time. A silent scheduler failure was found on day one of the original because this page existed; expect yours to earn its keep the same way.
