# Running it locally

The whole OS is a folder of HTML files on your own machine. Nothing is hosted anywhere, there is no account, and nothing needs deploying. But there is one wrinkle worth understanding, and one small upgrade worth making.

## The wrinkle: file:// versus a little server

You can double-click any page and it will open in your browser. But browsers stop a page opened as a plain file from reading other files on your machine (a sensible security rule), which means the pages can't load their live data and will show their built-in snapshot instead.

The fix is a tiny local server: a program whose only job is to hand files to your browser when asked. Nothing goes on the internet; "server" here just means "the thing that serves the files", like a waiter. Python ships with one:

```
python3 -m http.server 8144
```

Run that from your OS folder, then visit `http://localhost:8144/` in your browser and bookmark it. "localhost" literally means "this computer"; nobody else can see it. Now the pages can read their data files, and the freshness lines start telling the truth.

## The upgrade: make it start itself

The command above only runs while a terminal window stays open, which is fine for a developer and annoying for a human. The proper version registers the server with your operating system so it starts at login and just quietly exists:

- **macOS:** a LaunchAgent, a small file in `~/Library/LaunchAgents` that tells the system to run the server command at login and restart it if it dies.
- **Windows:** a Task Scheduler entry set to run at log on.
- **Linux:** a systemd user service.

This is a ten-minute job for your agent. Say something like:

> Set up a small background service that serves my Founder OS folder on localhost port 8144, starting automatically when I log in. Then tell me the address to bookmark.

After that, your OS is a bookmark: one click, always fresh, never hosted.

## Keeping the data fresh

The pages read small data files (the original uses JSON compiled from agent outputs, a task board, and a calendar). Something has to rewrite those files on a schedule: a cron job, a scheduled task, or an agent that runs a compile script a few times a day. The original runs its compile at 08:00, 12:00, 17:00, and 22:00, matching when its human actually checks in. Start with once a day; add check-ins when you notice yourself wanting them.
