# The rota

**The question it answers:** When does everything run, and on whose meter?

**The analogy.** The staff rota pinned to the wall: who works which shift, and the day strip showing when the office is busiest.

**What's on the page.** A day strip plotting every scheduled run at its true trigger time (only times confirmed by the scheduler itself — prose in config files lies), with the human's working hours shaded so contention is visible. Then the rota: every agent with role, true frequency, and cost lane — inside which subscription, or free as a local script. "Runs daily" next to "hasn't run since Monday" is a scheduler problem you can see at a glance.

**The rule it carries.** One timestamp, one truth — and trust the registry, not the prose. The original found its task descriptions claiming different times than the scheduler actually fired.

**Inspired by / changed.** Original room; the cost-lane framing answers the question every multi-tool user asks ("is it cheaper to run agents at night?") honestly: no provider prices by time of day — the real economics are subscription windows, batch APIs, and free local scripts.

**Building yours.** Get trigger times from the scheduler's own records. If your agents cluster before your working day, you'll see your capacity is protected; if they don't, you'll see why your quota vanishes by lunch.
