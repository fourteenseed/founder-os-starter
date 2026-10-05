# The sessions room: setup

This folder is the working version of [the sessions](../../rooms/12-the-sessions.md): a page that answers one question, which of my AI sessions needs me right now. It runs on macOS with the Claude desktop app. Codex is optional. Nothing here calls a model, and nothing leaves your machine.

What is in the folder:

| File | What it is |
|---|---|
| `compile_sessions.py` | Reads the Claude desktop app's local session files (and Codex rollouts if present) and writes `sessions.json`. Standard library only. |
| `the-sessions.html` | The page. Reads `sessions.json` beside it and redraws every minute. |
| `private.example.json` | The shape of the privacy list. Copy it to `private.json` and make it yours. |
| `test_compile_sessions.py` | Tests against a fake home folder, so you can check the compiler without touching your own files. |
| `com.example.founder-os-sessions.plist` | A launchd job that runs the compile every five minutes. |

## First run

1. **Make the privacy list.** Copy `private.example.json` to `private.json` and edit it. List the folders whose sessions should never show detail, the keywords that mark a session private, and the first names of people whose sessions stay private. The compiler refuses to run without this file, and an empty list is refused too, so there is never an unredacted copy by accident. The `.gitignore` already keeps `private.json` and `sessions.json` out of git.

2. **Compile once.**

   ```
   cd tools/sessions
   python3 compile_sessions.py
   ```

   It prints one line, such as `wrote sessions.json: 9 rows (needs_answer 1, running 2, finished 6), 1 private`. Open `sessions.json` and read it before you go further. Every title and summary line should be one you are happy to have on a page on your own screen. If something shows that should not, add a keyword or folder to `private.json` and compile again.

3. **Serve the folder and open the page.** Browsers will not let a page opened as a plain file read another file beside it, so run a small local server from the repo root, as in [start-here/running-it-locally.md](../../start-here/running-it-locally.md):

   ```
   python3 -m http.server 8144
   ```

   Then visit `http://localhost:8144/tools/sessions/the-sessions.html`. The stamp at the top right says when the file was compiled, and turns to "Snapshot" when it is more than fifteen minutes old.

## Run it on a schedule

A page that only updates when you remember to run a script is decoration. The launchd job keeps it honest.

1. Copy `com.example.founder-os-sessions.plist` to `~/Library/LaunchAgents/`.
2. Open the copy and change the `WorkingDirectory` line to the full path of this folder on your Mac.
3. Load it:

   ```
   launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.founder-os-sessions.plist
   ```

4. Check the log a few minutes later: `tail ~/Library/Logs/founder-os/sessions.log`. You should see one `wrote` line per run.

To stop it: `launchctl bootout gui/$(id -u)/com.example.founder-os-sessions`.

Five minutes is a reasonable cadence. The compiler reads only files changed in the last week and reads the tail of each transcript rather than the whole file, so a run is cheap. If you want it quicker, lower `StartInterval`, but do not go below sixty seconds.

## What the states mean

The page groups sessions into four bands, in order of how much they need you.

- **Waiting on you.** A raised hand. Tinted when a live session is stuck right now: a permission prompt, a question, or a reply it asked for. Paler when a session has already ended, but ended asking you something or with work for you to review. Those stay seven days.
- **Working now.** A session that is mid-turn. If its transcript has been quiet for thirty minutes the row says so, because a session that looks busy but has stopped writing is usually stuck at a prompt the app has not surfaced.
- **Open and quiet.** Open, idle, nothing asked.
- **Finished in the last 24 hours.** Folded by default.

A Codex "needs your approval" is inferred, not recorded. Codex desktop rollouts hold no approval events, so the compiler looks for a shell call that asked for escalated permissions and has no result yet. The tooltip says so.

## Proof gate

Before you trust the page, make it show silence. Stop the launchd job, wait twenty minutes, and reload. The stamp must say "Snapshot" and a notice must say the copy is old. If the page still says "Live", fix that before you rely on it. Then start the job again and watch the stamp recover on its own.

## Adapting it

The compiler was written against the Claude desktop app and Codex desktop as they were in autumn 2026. If either changes where it keeps its files, the page will tell you which input it could not read rather than show old rows as live, and the paths to change are all at the top of `compile_sessions.py` in the `Env` class. Run the tests after any change:

```
cd tools/sessions
python3 test_compile_sessions.py
```

If you want a different page, the payload is small and documented in the compiler's docstring. Point anything at `sessions.json`.
