# Founder OS Starter

Founder OS Starter is a local-first cockpit for founders using multiple AI tools. It helps connect business context, decisions, tasks, reusable skills, AI usage and proof of progress, so AI becomes part of an operating rhythm rather than a collection of disconnected chats.

This repository is a public-safe starter pattern. It uses invented sample data and plain dashboard views so you can see how the system fits together before connecting your own notes, tools or automations.

## Start here

Run the local dashboard:

```bash
./scripts/serve-local.sh
```

Then open:

```text
http://127.0.0.1:8766/dashboard/
```

You can also open `dashboard/index.html` directly in a browser.

## Dashboard views

- **Company map**: the whole business as a living system.
- **Daily brief**: what changed, what matters and what needs a decision.
- **Open Engine**: the visible work layer for human tasks, AI tasks, handoffs and receipts.
- **Open Skills**: reusable runbooks, prompts and methods.
- **Token usage**: where AI effort is going, what it costs and what value comes back.
- **Proof log**: what actually changed, shipped, sold, followed up or improved.
- **System health**: what is stale, missing or ready for attention.

## Core loop

```text
Signal -> judgement -> commitment -> execution -> proof -> learning -> revenue
```

## Public-safe boundary

This starter deliberately uses generic sample data. Do not put private client detail, family material, raw transcripts, mailbox content, passwords, financial information or unfinished judgement about real people into a public fork.
