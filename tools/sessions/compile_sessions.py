#!/usr/bin/env python3
"""Compile "The sessions" room: which of my AI sessions needs me right now?

Standard library only. No model calls. Nothing leaves your machine.

Reads, read-only, on macOS:
  ~/.claude/sessions/<pid>.json                                  live Claude processes (status, waiting for what)
  ~/Library/Application Support/Claude/claude-code-sessions/      the Claude desktop app's session files
  ~/.claude/projects/<folder>/<session>.jsonl                     transcript tails, for closed sessions
  ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl                    Codex desktop chats (optional; skipped if absent)
Writes ONE file, sessions.json, shaped for the-sessions.html beside this script.

    python3 compile_sessions.py                 compile to sessions.json beside this script
    python3 compile_sessions.py --out PATH      compile to PATH
    python3 compile_sessions.py --print         compile and print the payload instead

Privacy. The compiler refuses to run without a private list (private.json beside this script; copy
private.example.json to start). A session is private if its folder is under a listed prefix, or its
title, task name, summary or folder contains a listed keyword or name. A private row carries only a
label, the state and the times: no title, no summary, no path. Every free-text field that is published
goes through scrub(): no links, email addresses, home-folder paths, keys or token-like strings.
The private list is the only copy of what you consider private, so keep it out of any public repo.

Payload:
    {schema, generated_at, source, inputs{claude_registry, claude_desktop, codex: {ok, n[, bad]}},
     keeps{finished_hours, ended_asking_days}, open_link, sessions[]}
    row: id, tool (claude|codex), private, label (private rows only), title, project, kind
         (chat|scheduled|spawned|terminal), task, state, live, waiting_for, needs, maybe_stuck,
         since, last_activity, content, content_source (app|message), state_basis (Codex: event|inferred)
    state: needs_approval, needs_answer, waiting_other, needs_reply, ready_to_review,
           stopped_mid_step, unanswered, unreviewed, running, idle_open, finished, unknown

Codex desktop rollouts record no approval prompts, so a Codex approval is inferred from a shell call
that asked for escalated permissions and has no result yet. The page labels it as inferred.

This is the generic version of the compiler behind one founder's own sessions room. It was written
against the Claude desktop app and Codex desktop as they were in autumn 2026. If either changes its
file layout, the page will say which input it could not read rather than show stale rows as live.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HOME = Path.home()
HERE = Path(__file__).resolve().parent
SCHEMA = 3
SOURCE = 'compile_sessions.py'

# "Open on Mac" deep link, as seen in the Claude desktop app's own session listing. Set to None to switch it off.
OPEN_LINK_TEMPLATE: Optional[str] = 'claude://claude.ai/epitaxy/{id}'

CLOSED_WINDOW_DAYS = 7      # how far back closed sessions are read
FINISHED_HOURS = 24         # "Finished" rows stay this long
AGE_OUT_DAYS = 7            # ended asking / ended with work to review / stopped part-way
STUCK_MINUTES = 30          # running with a transcript this quiet gets a "no activity" note
CODEX_SCAN_DAYS = 14        # rollout folders are dated by start day
TITLE_MAX = 120
NEEDS_MAX = 140
CONTENT_MAX = 140           # the "what it says" line, after scrubbing
RAW_CONTENT_MAX = 600       # raw text kept for the privacy check, before it is scrubbed and cut
CODEX_WORKING_MINUTES = 10  # an open Codex turn with an event this recent is Working
CODEX_APPROVAL_HOURS = 12   # an approval prompt older than this is treated as dead
CODEX_TAIL_RECORDS = 400    # records read from the end of a rollout
CODEX_TAIL_BYTES = 300_000

STATE_RANK = {
    'needs_approval': 0, 'needs_answer': 1, 'waiting_other': 2, 'needs_reply': 3,
    'ready_to_review': 4, 'stopped_mid_step': 5, 'unanswered': 6, 'unreviewed': 7,
    'running': 8, 'idle_open': 9, 'finished': 10, 'unknown': 11,
}
CLOSED_NEEDS = ('unanswered', 'unreviewed', 'stopped_mid_step')
LIVE_ATTENTION = ('needs_approval', 'needs_answer', 'waiting_other', 'running')


@dataclass
class Env:
    """Every path the compiler touches, so tests can point it at a fake home."""
    home: Path = HOME
    registry_dir: Path = HOME / '.claude' / 'sessions'
    desktop_dir: Path = HOME / 'Library' / 'Application Support' / 'Claude' / 'claude-code-sessions'
    projects_dir: Path = HOME / '.claude' / 'projects'
    codex_dir: Path = HOME / '.codex' / 'sessions'
    codex_index: Path = HOME / '.codex' / 'session_index.jsonl'
    config_path: Path = HERE / 'private.json'
    out_path: Path = HERE / 'sessions.json'


# --------------------------------------------------------------------------- privacy

class ConfigError(Exception):
    pass


@dataclass
class PrivacyConfig:
    default_label: str
    cwd_prefixes: List[Tuple[str, str]]          # (normalised lowercase absolute path, label)
    keywords: List[Tuple[str, str]]              # (lowercase substring, label)
    name_patterns: List[Any]                     # compiled whole-word patterns
    names: List[str] = field(default_factory=list)


def _expand(path: str, home: Path) -> str:
    p = str(path).strip()
    if p == '~' or p.startswith('~/'):
        p = str(home) + p[1:]
    return os.path.normpath(p).lower()


def load_config(path: Path, home: Path = HOME) -> PrivacyConfig:
    """Fails closed: a missing or broken private list stops the compile rather than writing unredacted rows."""
    try:
        raw = json.loads(Path(path).read_text(encoding='utf-8'))
        default_label = str(raw.get('default_label') or 'Private')
        prefixes = [(_expand(e['path'], home), str(e['label'])) for e in raw.get('private_folders', [])]
        keywords = [(str(e['match']).lower(), str(e.get('label') or default_label))
                    for e in raw.get('keywords', []) if str(e.get('match') or '').strip()]
        names = [str(n).strip() for n in raw.get('names', []) if str(n).strip()]
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ConfigError(f'cannot use the private list at {path}: {exc}') from exc
    if not prefixes and not keywords and not names:
        raise ConfigError(f'the private list at {path} is empty; add at least one folder, keyword or name')
    patterns = [re.compile(r'(?<![A-Za-z])' + re.escape(n) + r'(?![A-Za-z])', re.I) for n in names]
    return PrivacyConfig(default_label, prefixes, keywords, patterns, names)


def _under(path: str, prefix: str) -> bool:
    p = os.path.normpath(path).lower()
    return p == prefix or p.startswith(prefix.rstrip('/') + '/')


_URL_RE = re.compile(r'https?://\S+')
_EMAIL_RE = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}')
_HOMEPATH_RE = re.compile(r'(?:/Users|/home)/[^\s"\'`<>)\]}]*')
_SECRET_RES = (
    re.compile(r'\bsk-[A-Za-z0-9_\-]{8,}'),                                # API keys of the sk- family
    re.compile(r'\bgh[pousr]_[A-Za-z0-9]{16,}'),                           # GitHub tokens
    re.compile(r'\bgithub_pat_[A-Za-z0-9_]{16,}'),                         # GitHub fine-grained tokens
    re.compile(r'\bxox[abposr]-[A-Za-z0-9\-]{8,}'),                        # Slack tokens
    re.compile(r'\b(?:AKIA|ASIA)[0-9A-Z]{12,}\b'),                         # AWS access key ids
    re.compile(r'\beyJ[A-Za-z0-9_\-]{8,}(?:\.[A-Za-z0-9_\-]+){0,2}'),      # JWTs
)
_MIXED_RUN_RE = re.compile(r'[A-Za-z0-9_\-]{24,}')
_LONG_RE = re.compile(r'\S{41,}')
_CTRL_RE = re.compile(r'[\x00-\x1f\x7f]+')


def _mixed_run(m: Any) -> str:
    s = m.group(0)
    return '[removed]' if any(ch.isalpha() for ch in s) and any(ch.isdigit() for ch in s) else s


def scrub(text: Any, limit: int) -> str:
    """Plain, short, and without links, emails, home paths, keys or token-like strings. Never longer than limit."""
    if not text:
        return ''
    t = _CTRL_RE.sub(' ', str(text))
    t = _URL_RE.sub('a link', t)
    t = _EMAIL_RE.sub('an email address', t)
    t = _HOMEPATH_RE.sub('a file path', t)
    for rx in _SECRET_RES:
        t = rx.sub('[removed]', t)
    t = _MIXED_RUN_RE.sub(_mixed_run, t)
    t = _LONG_RE.sub('[long string]', t)
    t = re.sub(r'\s+', ' ', t).strip()
    if len(t) > limit:
        head = t[:max(1, limit - 1)]
        if ' ' in head:
            head = head.rsplit(' ', 1)[0]
        t = head.rstrip(' ,;:.-') + '…'
    return t


_MD_LEAD_RE = re.compile(r'^(?:\s*(?:#{1,6}\s+|>+\s*|[-*+•]\s+|\d{1,2}[.)]\s+))+')
_SENT_END_RE = re.compile(r'[.!?]+(?=["\')\]]*(?:\s|$))')
_ABBREV = {'e.g', 'i.e', 'etc', 'vs', 'approx', 'mr', 'mrs', 'ms', 'dr', 'st', 'inc', 'ltd', 'cf'}
_ASK_PHRASES = ('do you want', 'shall i', 'should i', 'want me to', 'let me know', 'please confirm', 'would you like')
_ISO_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?\s*(Z|[+-]\d{2}:?\d{2})?$')


def _clean_line(raw: str) -> str:
    s = raw[:4000].strip()
    if not s or re.fullmatch(r'[\s\-=*_`|:+~.]+', s):
        return ''
    s = _MD_LEAD_RE.sub('', s)
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)          # [text](link) -> text
    s = re.sub(r'(\*\*|__|`)', '', s)
    return s.strip()


def _cut_sentence(line: str) -> str:
    for m in _SENT_END_RE.finditer(line):
        before = line[:m.start()].rstrip()
        last = before.rsplit(None, 1)[-1].lower() if before else ''
        if m.group(0) == '.' and last in _ABBREV:
            continue
        return line[:m.end()].strip()
    return line.strip()


def first_sentence_raw(text: Any) -> str:
    """First sentence of a message as written (not yet scrubbed). Skips code fences, rules and headings."""
    if not text:
        return ''
    fence = False
    heading = ''
    for raw in str(text).splitlines()[:80]:
        if raw.strip().startswith('```'):
            fence = not fence
            continue
        if fence:
            continue
        line = _clean_line(raw)
        if len(re.sub(r'[^A-Za-z0-9]', '', line)) < 3:
            continue
        if raw.lstrip().startswith('#'):
            heading = heading or line
            continue
        return _cut_sentence(line[:2000])[:RAW_CONTENT_MAX]
    return _cut_sentence(heading[:2000])[:RAW_CONTENT_MAX] if heading else ''


def asks_for_reply(text: Any) -> bool:
    """True when a finished turn's last message hands the next move back to the human."""
    body = str(text or '').strip()
    if not body:
        return False
    if re.sub(r'[\s*_`>)\]"\'”’]+$', '', body[-600:]).endswith('?'):
        return True
    low = body[-500:].lower()
    return any(p in low for p in _ASK_PHRASES)


def parse_ts(value: Any) -> float:
    """Epoch seconds from a number (seconds or milliseconds) or an ISO 8601 string; 0.0 when unreadable."""
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        v = float(value)
        return v / 1000.0 if v > 1e11 else (v if v > 0 else 0.0)
    if isinstance(value, str):
        m = _ISO_RE.match(value.strip())
        if not m:
            return 0.0
        y, mo, d, h, mi, s = (int(m.group(i)) for i in range(1, 7))
        frac = float('0.' + m.group(7)) if m.group(7) else 0.0
        tz = m.group(8)
        offset = 0
        if tz and tz != 'Z':
            digits = tz[1:].replace(':', '')
            offset = (1 if tz[0] == '+' else -1) * (int(digits[:2]) * 3600 + int(digits[2:4]) * 60)
        try:
            base = datetime(y, mo, d, h, mi, s, tzinfo=timezone.utc)
        except ValueError:
            return 0.0
        return base.timestamp() + frac - offset
    return 0.0


# --------------------------------------------------------------------------- candidates

@dataclass
class Candidate:
    """A session before redaction. Never serialised; redact() turns it into the published row."""
    id: str
    tool: str
    title: str = ''
    cwd: str = ''
    origin_cwd: str = ''
    extra_text: List[str] = field(default_factory=list)   # used to classify only, never published
    task_id: str = ''
    kind: str = 'chat'
    state: str = 'unknown'
    waiting_for: str = ''
    needs: str = ''
    detail: str = ''
    since_ts: float = 0.0
    last_ts: float = 0.0
    live: bool = False
    maybe_stuck: bool = False
    content: str = ''
    content_source: str = ''      # app | message
    state_basis: str = ''         # event | inferred (Codex approvals only)


def classify_private(c: Candidate, cfg: PrivacyConfig) -> Optional[str]:
    for cwd in (c.cwd, c.origin_cwd):
        if cwd:
            for prefix, label in cfg.cwd_prefixes:
                if _under(cwd, prefix):
                    return label
    texts = [c.cwd, c.origin_cwd, c.title, c.task_id, c.needs, c.detail, c.content, c.waiting_for] + list(c.extra_text)
    hay = '\n'.join(t for t in texts if t)
    low = hay.lower()
    for kw, label in cfg.keywords:
        if kw in low:
            return label
    for rx in cfg.name_patterns:
        if rx.search(hay):
            return cfg.default_label
    return None


def project_name(cwd: str, home: Path) -> Optional[str]:
    """The folder the session ran in, shown as its last path segment; '~' for the home folder itself."""
    if not cwd:
        return None
    p = os.path.normpath(cwd)
    if p == str(home):
        return '~'
    return os.path.basename(p) or None


def humanise(task_id: str) -> str:
    return re.sub(r'[-_]+', ' ', task_id).strip()


def _digest(text: str) -> str:
    return hashlib.sha256(('sessions:' + text).encode('utf-8')).hexdigest()


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts).astimezone().isoformat(timespec='seconds')


def redact(c: Candidate, cfg: PrivacyConfig, home: Path) -> Dict[str, Any]:
    label = classify_private(c, cfg)
    row: Dict[str, Any] = {
        'tool': c.tool, 'kind': c.kind, 'state': c.state, 'live': bool(c.live),
        'since': iso(c.since_ts), 'last_activity': iso(c.last_ts),
    }
    if c.maybe_stuck:
        row['maybe_stuck'] = True
    if label is not None:
        row['id'] = 'private-' + _digest(c.id)[:10]
        row['private'] = True
        row['label'] = label
        return row
    row['id'] = c.id
    row['private'] = False
    row['title'] = scrub(c.title, TITLE_MAX) or ('Codex chat' if c.tool == 'codex' else 'Untitled session')
    proj = project_name(c.cwd, home)
    if proj:
        row['project'] = scrub(proj, 60)
    if c.task_id:
        row['task'] = scrub(humanise(c.task_id), 70)
    if c.waiting_for:
        row['waiting_for'] = scrub(c.waiting_for, 60)
    if c.needs:
        row['needs'] = scrub(c.needs, NEEDS_MAX)
    content = scrub(c.content, CONTENT_MAX)
    if content:
        row['content'] = content
        row['content_source'] = c.content_source or 'message'
    if c.state_basis:
        row['state_basis'] = c.state_basis
    return row


# --------------------------------------------------------------------------- Claude readers

def _ms(v: Any) -> float:
    return v / 1000.0 if isinstance(v, (int, float)) and v > 0 else 0.0


def _inp(ok: bool, n: int, bad: int = 0) -> Dict[str, Any]:
    d: Dict[str, Any] = {'ok': bool(ok), 'n': int(n)}
    if bad:
        d['bad'] = int(bad)
    return d


def pid_alive(pid: Any) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def load_registry(env: Env) -> Tuple[List[Dict[str, Any]], bool, int]:
    """Live Claude processes. Only <pid>.json files are opened; the *.key files beside them never are."""
    if not env.registry_dir.is_dir():
        return [], False, 0
    out, bad = [], 0
    for fp in sorted(glob.glob(os.path.join(glob.escape(str(env.registry_dir)), '*.json'))):
        try:
            d = json.loads(Path(fp).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            bad += 1
            continue
        if isinstance(d, dict) and pid_alive(d.get('pid')):
            out.append(d)
    return out, True, bad


def read_tail_records(path: Path, max_bytes: int = 262144, max_total: int = 4 * 1024 * 1024,
                      max_recs: int = 120) -> List[Dict[str, Any]]:
    """Parse the last records of a jsonl file without reading all of it."""
    try:
        size = path.stat().st_size
    except OSError:
        return []
    n = min(size, max_bytes)
    while True:
        try:
            with open(path, 'rb') as f:
                f.seek(size - n)
                chunk = f.read(n)
        except OSError:
            return []
        lines = chunk.split(b'\n')
        if n < size:
            lines = lines[1:]          # the first line is probably cut in half
        recs = []
        for ln in lines[-max_recs:]:
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            if isinstance(r, dict):
                recs.append(r)
        if recs or n >= size or n >= max_total:
            return recs
        n = min(size, n * 4)


def pending_tool_name(recs: List[Dict[str, Any]]) -> Optional[str]:
    """Name of the last tool call in the tail that never got a result, main thread only."""
    uses: Dict[str, str] = {}
    answered = set()
    for r in recs:
        if r.get('isSidechain'):
            continue
        msg = r.get('message')
        content = msg.get('content') if isinstance(msg, dict) else None
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            if r.get('type') == 'assistant' and b.get('type') == 'tool_use' and b.get('id'):
                uses[str(b['id'])] = str(b.get('name') or 'tool')
            elif r.get('type') == 'user' and b.get('type') == 'tool_result' and b.get('tool_use_id'):
                answered.add(str(b['tool_use_id']))
    pending = [name for tid, name in uses.items() if tid not in answered]
    return pending[-1] if pending else None


def find_transcript(env: Env, cwd: str, cli_sid: str) -> Optional[Path]:
    if not cli_sid:
        return None
    slug = re.sub(r'[^A-Za-z0-9]', '-', cwd or '')
    p = env.projects_dir / slug / (cli_sid + '.jsonl')
    if p.is_file():
        return p
    hits = glob.glob(os.path.join(glob.escape(str(env.projects_dir)), '*', glob.escape(cli_sid) + '.jsonl'))
    return Path(hits[0]) if hits else None


def wait_kind(waiting_for: str) -> Optional[str]:
    """'permission prompt' and 'input needed' are the two values seen so far; anything else is shown as written."""
    low = (waiting_for or '').strip().lower()
    if not low:
        return None
    if 'permission' in low:
        return 'approval'
    if 'input' in low or 'question' in low or 'answer' in low:
        return 'answer'
    return None


def claude_state(reg: Optional[Dict[str, Any]], category: Optional[str], pending_tool: Optional[str]) -> Tuple[str, str]:
    """(state, waiting_for text). category is the app's own end-of-turn summary, only when current."""
    if reg is not None:
        status = str(reg.get('status') or '').strip().lower()
        if status == 'waiting':
            wf = str(reg.get('waitingFor') or '').strip()
            kind = wait_kind(wf)
            if kind == 'approval':
                return 'needs_approval', ''
            if kind == 'answer' or pending_tool == 'AskUserQuestion':
                return 'needs_answer', ''
            return 'waiting_other', wf
        if status == 'busy':
            return 'running', ''
        if status in ('idle', ''):
            return {'blocked': 'needs_reply', 'review_ready': 'ready_to_review'}.get(category or '', 'idle_open'), ''
        return 'unknown', status
    if pending_tool:
        return ('unanswered' if pending_tool == 'AskUserQuestion' else 'stopped_mid_step'), ''
    return {'blocked': 'unanswered', 'review_ready': 'unreviewed'}.get(category or '', 'finished'), ''


def _needs_tail(reg: Optional[Dict[str, Any]]) -> bool:
    if reg is None:
        return True
    return str(reg.get('status') or '').lower() == 'waiting' and wait_kind(str(reg.get('waitingFor') or '')) is None


def last_assistant_text(recs: List[Dict[str, Any]]) -> str:
    """Text of the last main-thread assistant message in a transcript tail ('' if there is none)."""
    for r in reversed(recs):
        if r.get('type') != 'assistant' or r.get('isSidechain'):
            continue
        msg = r.get('message')
        content = msg.get('content') if isinstance(msg, dict) else None
        if isinstance(content, str) and content.strip():
            return content
        if isinstance(content, list):
            texts = [str(b.get('text')) for b in content
                     if isinstance(b, dict) and b.get('type') == 'text' and str(b.get('text') or '').strip()]
            if texts:
                return '\n'.join(texts)
    return ''


def build_claude_candidate(d: Dict[str, Any], stem: str, reg: Optional[Dict[str, Any]], mtime: float,
                           env: Env, now_ts: float) -> Candidate:
    pts = d.get('postTurnSummary') if isinstance(d.get('postTurnSummary'), dict) else {}
    current = bool(pts.get('summarizes_uuid')) and pts.get('summarizes_uuid') == d.get('lastAssistantUuid')
    category = pts.get('status_category') if current else None
    app_text = ''
    if current:   # the app's own line, only while its summary is for the latest turn
        app_text = str(pts.get('needs_action') or '').strip() or str(pts.get('status_detail') or '').strip()
    cwd = str(d.get('cwd') or (reg or {}).get('cwd') or '')
    cli_sid = str(d.get('cliSessionId') or (reg or {}).get('sessionId') or '')
    busy = reg is not None and str(reg.get('status') or '').lower() == 'busy'
    transcript = find_transcript(env, cwd, cli_sid) if (busy or _needs_tail(reg) or not app_text) else None
    recs = read_tail_records(transcript) if transcript else []
    pending = pending_tool_name(recs) if (recs and _needs_tail(reg)) else None
    state, waiting_for = claude_state(reg, category, pending)

    last_ts = _ms(d.get('lastActivityAt')) or _ms(d.get('createdAt')) or mtime
    since = last_ts
    if reg is not None:
        since = _ms(reg.get('statusUpdatedAt')) or _ms(reg.get('updatedAt')) or last_ts
        last_ts = max(last_ts, _ms(reg.get('updatedAt')))
    needs = app_text if category in ('blocked', 'review_ready') else ''
    content, source = app_text, ('app' if app_text else '')
    if not content:
        content = first_sentence_raw(last_assistant_text(recs))
        source = 'message' if content else ''
    task = str(d.get('scheduledTaskId') or '')
    spawned = d.get('spawnedFrom') if isinstance(d.get('spawnedFrom'), dict) else {}
    kind = 'scheduled' if task else ('spawned' if spawned else 'chat')
    extra = [str(t) for t in (d.get('previousTitles') or []) if isinstance(t, str)]
    if spawned.get('title'):
        extra.append(str(spawned['title']))
    if reg is not None and reg.get('name'):
        extra.append(str(reg['name']))
    stuck = False
    if busy and transcript is not None:
        try:
            stuck = now_ts - transcript.stat().st_mtime > STUCK_MINUTES * 60
        except OSError:
            pass
    return Candidate(
        id=stem, tool='claude', title=str(d.get('title') or ''), cwd=cwd, origin_cwd=str(d.get('originCwd') or ''),
        extra_text=extra, task_id=task, kind=kind, state=state, waiting_for=waiting_for, needs=needs,
        detail=str(pts.get('status_detail') or '') if current else '', since_ts=since, last_ts=last_ts,
        live=reg is not None, maybe_stuck=stuck, content=content, content_source=source)


def build_registry_only(reg: Dict[str, Any], env: Env, now_ts: float) -> Candidate:
    """A live Claude process with no desktop file, for example a terminal session."""
    cwd = str(reg.get('cwd') or '')
    cli_sid = str(reg.get('sessionId') or '')
    busy = str(reg.get('status') or '').lower() == 'busy'
    transcript = find_transcript(env, cwd, cli_sid)
    recs = read_tail_records(transcript) if transcript else []
    pending = pending_tool_name(recs) if (recs and _needs_tail(reg)) else None
    state, waiting_for = claude_state(reg, None, pending)
    upd = _ms(reg.get('updatedAt')) or now_ts
    since = _ms(reg.get('statusUpdatedAt')) or upd
    stuck = False
    if busy and transcript is not None:
        try:
            stuck = now_ts - transcript.stat().st_mtime > STUCK_MINUTES * 60
        except OSError:
            pass
    content = first_sentence_raw(last_assistant_text(recs))
    return Candidate(id='cli_' + (cli_sid or str(reg.get('pid'))), tool='claude', title=str(reg.get('name') or ''),
                     cwd=cwd, kind='terminal', state=state, waiting_for=waiting_for, since_ts=since, last_ts=upd,
                     live=True, maybe_stuck=stuck, content=content, content_source='message' if content else '')


def collect_claude(env: Env, now_ts: float, inputs: Dict[str, Any]) -> List[Candidate]:
    cands: List[Candidate] = []
    regs, reg_ok, reg_bad = load_registry(env)
    inputs['claude_registry'] = _inp(reg_ok, len(regs), reg_bad)
    by_host = {str(r['hostSessionId']): r for r in regs if r.get('hostSessionId')}
    by_sid = {str(r['sessionId']): r for r in regs if r.get('sessionId')}
    matched, archived = set(), set()
    ok = env.desktop_dir.is_dir()
    files = glob.glob(os.path.join(glob.escape(str(env.desktop_dir)), '*', '*', 'local_*.json')) if ok else []
    horizon = now_ts - CLOSED_WINDOW_DAYS * 86400
    n = bad = 0
    for fp in files:
        p = Path(fp)
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        reg = by_host.get(p.stem)
        if reg is None and mtime < horizon:
            continue                                   # old and not running: never parse a large file for it
        try:
            d = json.loads(p.read_text(encoding='utf-8'))
            if not isinstance(d, dict):
                raise ValueError('not an object')
        except (OSError, ValueError):
            bad += 1
            continue
        if reg is None:
            reg = by_sid.get(str(d.get('cliSessionId') or ''))
        if d.get('isArchived'):
            if reg is not None:
                archived.add(id(reg))
            continue
        if reg is not None:
            matched.add(id(reg))
        cands.append(build_claude_candidate(d, p.stem, reg, mtime, env, now_ts))
        n += 1
    for r in regs:
        if id(r) not in matched and id(r) not in archived:
            cands.append(build_registry_only(r, env, now_ts))
            n += 1
    inputs['claude_desktop'] = _inp(ok, n, bad)
    return cands


# --------------------------------------------------------------------------- Codex reader (optional)

CODEX_APPROVAL_EVENTS = ('exec_approval_request', 'apply_patch_approval_request', 'request_permissions')
CODEX_RESOLVE_EVENTS = ('exec_command_begin', 'exec_command_end', 'patch_apply_begin', 'patch_apply_end')
CODEX_CALL_TYPES = ('function_call', 'local_shell_call', 'custom_tool_call')
CODEX_OUTPUT_TYPES = ('function_call_output', 'local_shell_call_output', 'custom_tool_call_output')


def _codex_text(payload: Dict[str, Any]) -> str:
    content = payload.get('content')
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(str(b.get('text')) for b in content if isinstance(b, dict) and str(b.get('text') or '').strip())
    return ''


def codex_scan(recs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """One pass over the tail of a Codex rollout. Pure: no clock, no files."""
    start = end = -1
    ended: Optional[str] = None
    for i, r in enumerate(recs):
        if r.get('type') != 'event_msg' or not isinstance(r.get('payload'), dict):
            continue
        kind = r['payload'].get('type')
        if kind == 'task_started':
            start = i
        elif kind in ('task_complete', 'turn_aborted'):
            end, ended = i, kind
    is_open = end < 0 or start > end
    last_ts = start_ts = end_ts = 0.0
    policy: Any = None
    last_msg = last_final = task_msg = ''
    msg_idx = -1
    events: Dict[str, float] = {}      # approval events that nothing has resolved yet
    calls: Dict[str, float] = {}       # escalated calls with no result yet
    anon = 0
    for i, r in enumerate(recs):
        ts = parse_ts(r.get('timestamp'))
        if ts:
            last_ts = ts
        p = r.get('payload') if isinstance(r.get('payload'), dict) else {}
        pt = p.get('type')
        rt = r.get('type')
        if rt == 'turn_context':
            policy = p.get('approval_policy', policy)
        elif rt == 'event_msg':
            if i == start:
                start_ts = parse_ts(p.get('started_at')) or ts
            if i == end:
                end_ts = parse_ts(p.get('completed_at')) or ts
                if pt == 'task_complete':
                    task_msg = str(p.get('last_agent_message') or '')
            if pt in CODEX_APPROVAL_EVENTS and i > start:
                anon += 1
                events[str(p.get('call_id') or p.get('id') or '#%d' % anon)] = ts or last_ts
            elif pt in CODEX_RESOLVE_EVENTS and p.get('call_id') is not None:
                events.pop(str(p.get('call_id')), None)
        elif rt == 'response_item':
            if pt == 'message' and p.get('role') == 'assistant':
                text = _codex_text(p)
                if text.strip():
                    last_msg, msg_idx = text, i
                    if p.get('phase') == 'final_answer':
                        last_final = text
            elif pt in CODEX_CALL_TYPES and i > start:
                cid = str(p.get('call_id') or p.get('id') or '')
                blob = str(p.get('arguments') or p.get('action') or p.get('input') or '')
                if cid and 'require_escalated' in blob:
                    calls[cid] = ts or last_ts
            elif pt in CODEX_OUTPUT_TYPES:
                cid = str(p.get('call_id') or '')
                calls.pop(cid, None)
                events.pop(cid, None)
    approval, approval_ts = '', 0.0
    if is_open and str(policy).lower() != 'never':
        if events:
            approval, approval_ts = 'event', min(events.values())
        elif calls:
            approval, approval_ts = 'inferred', min(calls.values())
    return {'open': is_open, 'ended': ended, 'start_idx': start, 'start_ts': start_ts, 'end_ts': end_ts,
            'last_ts': last_ts, 'task_message': task_msg, 'last_message': last_msg, 'last_final': last_final,
            'msg_idx': msg_idx, 'approval': approval, 'approval_ts': approval_ts}


def codex_assess(recs: List[Dict[str, Any]], mtime: float, now_ts: float) -> Dict[str, Any]:
    """State, content line and times for one Codex desktop chat."""
    out: Dict[str, Any] = {'state': 'unknown', 'content': '', 'basis': '', 'since': mtime, 'last': mtime}
    if not recs:
        return out
    s = codex_scan(recs)
    last = s['last_ts'] or mtime
    out['last'] = last
    age = now_ts - last
    this_turn = s['last_message'] if s['msg_idx'] > s['start_idx'] else ''
    if s['open']:
        message = this_turn
        if s['approval'] and age <= CODEX_APPROVAL_HOURS * 3600:
            out.update(state='needs_approval', basis=s['approval'], since=s['approval_ts'] or last)
        elif age < CODEX_WORKING_MINUTES * 60:
            out.update(state='running', since=s['start_ts'] or last)
        else:
            out.update(state='stopped_mid_step', since=last)
    elif s['ended'] == 'turn_aborted':
        message = this_turn
        out.update(state='stopped_mid_step', since=s['end_ts'] or last)
    elif s['ended'] == 'task_complete':
        message = s['task_message'] or s['last_final'] or this_turn
        out.update(state='needs_reply' if asks_for_reply(message) else 'finished', since=s['end_ts'] or last)
    else:
        message = this_turn
    out['content'] = first_sentence_raw(message)
    return out


def collect_codex(env: Env, now_ts: float, inputs: Dict[str, Any]) -> List[Candidate]:
    """Codex desktop chats only (source vscode). Headless runs and sub-agents are left out."""
    out: List[Candidate] = []
    if not env.codex_dir.is_dir():
        inputs['codex'] = _inp(False, 0)
        return out
    titles: Dict[str, Tuple[str, str]] = {}
    try:
        with open(env.codex_index, encoding='utf-8') as f:
            for line in f:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict) and row.get('id'):
                    stamp = str(row.get('updated_at') or '')
                    if str(row['id']) not in titles or stamp >= titles[str(row['id'])][0]:
                        titles[str(row['id'])] = (stamp, str(row.get('thread_name') or ''))
    except OSError:
        pass
    day0 = datetime.fromtimestamp(now_ts)
    files: List[str] = []
    for back in range(CODEX_SCAN_DAYS + 1):
        d = day0 - timedelta(days=back)
        files += glob.glob(os.path.join(glob.escape(str(env.codex_dir)), d.strftime('%Y'), d.strftime('%m'),
                                        d.strftime('%d'), 'rollout-*.jsonl'))
    horizon = now_ts - CLOSED_WINDOW_DAYS * 86400
    bad = 0
    for fp in files:
        try:
            mtime = os.stat(fp).st_mtime
            if mtime < horizon:
                continue
            with open(fp, 'rb') as f:
                first = json.loads(f.readline(4_000_000))
            payload = first.get('payload') if isinstance(first, dict) else None
            if not isinstance(payload, dict) or payload.get('source') != 'vscode':
                continue
            sid = str(payload.get('id') or Path(fp).stem)
            recs = read_tail_records(Path(fp), max_bytes=CODEX_TAIL_BYTES, max_recs=CODEX_TAIL_RECORDS)
            info = codex_assess(recs, mtime, now_ts)
            out.append(Candidate(
                id='codex-' + sid, tool='codex', title=titles.get(sid, ('', ''))[1], cwd=str(payload.get('cwd') or ''),
                state=info['state'], since_ts=info['since'], last_ts=info['last'], live=False,
                content=info['content'], content_source='message' if info['content'] else '',
                state_basis=info['basis']))
        except Exception:                              # one odd rollout must not hide the others
            bad += 1
    inputs['codex'] = _inp(True, len(out), bad)
    return out


# --------------------------------------------------------------------------- rules

def dedupe_tasks(cands: List[Candidate]) -> List[Candidate]:
    """One row per scheduled task: the newest run. A live prompt or running run is never hidden."""
    groups: Dict[str, List[Candidate]] = {}
    for c in cands:
        if c.task_id:
            groups.setdefault(c.task_id, []).append(c)
    drop = set()
    for rows in groups.values():
        rows.sort(key=lambda c: c.last_ts, reverse=True)
        for older in rows[1:]:
            if older.live and older.state in LIVE_ATTENTION:
                continue
            drop.add(id(older))
    return [c for c in cands if id(c) not in drop]


def apply_age_outs(cands: List[Candidate], now_ts: float) -> List[Candidate]:
    keep = []
    for c in cands:
        age = now_ts - c.last_ts
        if c.live or c.state == 'running':
            keep.append(c)
        elif c.state in CLOSED_NEEDS or (c.tool == 'codex' and c.state in ('needs_reply', 'needs_approval')):
            if age <= AGE_OUT_DAYS * 86400:
                keep.append(c)
        elif age <= FINISHED_HOURS * 3600:
            keep.append(c)
    return keep


def compile_sessions(now: Optional[datetime] = None, env: Optional[Env] = None,
                     cfg: Optional[PrivacyConfig] = None) -> Dict[str, Any]:
    env = env or Env()
    now_dt = now or datetime.now().astimezone()
    now_ts = now_dt.timestamp()
    cfg = cfg or load_config(env.config_path, env.home)
    inputs: Dict[str, Any] = {}
    cands: List[Candidate] = []
    for name, fn in (('claude', collect_claude), ('codex', collect_codex)):
        try:
            cands += fn(env, now_ts, inputs)
        except Exception as exc:                       # one broken reader must not take the other down
            inputs['codex' if name == 'codex' else 'claude_desktop'] = _inp(False, 0)
            sys.stderr.write(f'{name} reader failed: {type(exc).__name__}: {exc}\n')
    inputs.setdefault('claude_registry', _inp(False, 0))
    inputs.setdefault('claude_desktop', _inp(False, 0))
    inputs.setdefault('codex', _inp(False, 0))
    cands = apply_age_outs(dedupe_tasks(cands), now_ts)
    cands.sort(key=lambda c: (STATE_RANK.get(c.state, 99), -c.last_ts))
    return {
        'schema': SCHEMA,
        'generated_at': now_dt.astimezone().isoformat(timespec='seconds'),
        'source': SOURCE,
        'inputs': inputs,
        'keeps': {'finished_hours': FINISHED_HOURS, 'ended_asking_days': AGE_OUT_DAYS},
        'open_link': OPEN_LINK_TEMPLATE,
        'sessions': [redact(c, cfg, env.home) for c in cands],
    }


def summarise(payload: Dict[str, Any]) -> str:
    rows = payload.get('sessions', [])
    states: Dict[str, int] = {}
    for r in rows:
        states[r.get('state', '?')] = states.get(r.get('state', '?'), 0) + 1
    redacted = sum(1 for r in rows if r.get('private'))
    parts = ', '.join(f'{k} {v}' for k, v in sorted(states.items(), key=lambda kv: STATE_RANK.get(kv[0], 99)))
    return f'{len(rows)} rows ({parts or "none"}), {redacted} private'


def atomic_write_json(path: Path, payload: Any) -> None:
    """Write the whole file or none of it, so the page never reads a half-written one."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.sessions-', suffix='.tmp', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=1, ensure_ascii=False)
            f.write('\n')
        try:
            os.replace(tmp, path)
        except OSError:
            shutil.move(tmp, str(path))
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


# --------------------------------------------------------------------------- command line

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description='Compile the sessions room: which of my AI sessions needs me right now?')
    ap.add_argument('--out', metavar='PATH', help='write the payload here (default: sessions.json beside this script)')
    ap.add_argument('--print', action='store_true', help='print the payload as JSON instead of writing it')
    args = ap.parse_args(argv)
    env = Env()
    try:
        payload = compile_sessions(env=env)
    except ConfigError as exc:
        sys.stderr.write(f'{exc}\nCopy private.example.json to private.json beside this script and edit it.\n')
        return 2
    if args.print:
        print(json.dumps(payload, indent=1, ensure_ascii=False))
        return 0
    out = Path(args.out) if args.out else env.out_path
    atomic_write_json(out, payload)
    print(f'wrote {out}: {summarise(payload)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
