#!/usr/bin/env python3
"""Tests for compile_sessions.py against a fake home folder. Run: python3 test_compile_sessions.py"""
import json
import os
import shutil
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path

import compile_sessions as cs

NOW = datetime.now().astimezone()
NOW_TS = NOW.timestamp()


def ms(minutes_ago=0.0):
    return int((NOW_TS - minutes_ago * 60) * 1000)


class FakeHome:
    """Writes the files the compiler reads, in the layout the Claude desktop app and Codex use."""

    def __init__(self, root: Path):
        self.root = root
        self.env = cs.Env(
            home=root,
            registry_dir=root / '.claude' / 'sessions',
            desktop_dir=root / 'Library' / 'Application Support' / 'Claude' / 'claude-code-sessions',
            projects_dir=root / '.claude' / 'projects',
            codex_dir=root / '.codex' / 'sessions',
            codex_index=root / '.codex' / 'session_index.jsonl',
            config_path=root / 'private.json',
            out_path=root / 'sessions.json',
        )
        for d in (self.env.registry_dir, self.env.desktop_dir, self.env.projects_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.env.config_path.write_text(json.dumps({
            'default_label': 'Private',
            'private_folders': [{'path': '~/clients/acme', 'label': 'Client work'}],
            'keywords': [{'match': 'payroll', 'label': 'Finance'}],
            'names': ['Alex'],
        }))

    def registry(self, host, status, wf=None, cwd='~/studio', pid=None):
        d = {'pid': pid or os.getpid(), 'sessionId': 'sid-' + host, 'cwd': self._p(cwd), 'hostSessionId': 'local_' + host,
             'status': status, 'updatedAt': ms(1), 'statusUpdatedAt': ms(1), 'name': ''}
        if wf is not None:
            d['waitingFor'] = wf
        (self.env.registry_dir / f'{d["pid"]}-{host}.json').write_text(json.dumps(d))

    def desktop(self, stem, title='A session', cwd='~/studio', last=1.0, archived=False, task=None,
                category=None, needs='', detail='', mtime_minutes=None):
        d = {'title': title, 'cwd': self._p(cwd), 'originCwd': self._p(cwd), 'isArchived': archived,
             'lastActivityAt': ms(last), 'createdAt': ms(last + 5), 'cliSessionId': 'sid-' + stem,
             'lastAssistantUuid': 'u1'}
        if task:
            d['scheduledTaskId'] = task
        if category:
            d['postTurnSummary'] = {'status_category': category, 'status_detail': detail, 'needs_action': needs,
                                    'summarizes_uuid': 'u1'}
        folder = self.env.desktop_dir / 'org' / 'proj'
        folder.mkdir(parents=True, exist_ok=True)
        p = folder / f'local_{stem}.json'      # the app names its session files local_<id>.json
        p.write_text(json.dumps(d))
        if mtime_minutes is not None:
            t = NOW_TS - mtime_minutes * 60
            os.utime(p, (t, t))

    def transcript(self, stem, text, cwd='~/studio', pending_tool=None):
        slug = ''.join(ch if ch.isalnum() else '-' for ch in self._p(cwd))
        folder = self.env.projects_dir / slug
        folder.mkdir(parents=True, exist_ok=True)
        recs = [{'type': 'assistant', 'message': {'content': [{'type': 'text', 'text': text}]}}]
        if pending_tool:
            recs.append({'type': 'assistant', 'message': {'content': [{'type': 'tool_use', 'id': 't1', 'name': pending_tool}]}})
        (folder / f'sid-{stem}.jsonl').write_text('\n'.join(json.dumps(r) for r in recs) + '\n')

    def codex(self, cid, last_event, source='vscode', title='Codex thing', minutes_ago=5.0):
        day = datetime.fromtimestamp(NOW_TS)
        folder = self.env.codex_dir / day.strftime('%Y') / day.strftime('%m') / day.strftime('%d')
        folder.mkdir(parents=True, exist_ok=True)
        stamp = datetime.fromtimestamp(NOW_TS - minutes_ago * 60).astimezone().isoformat(timespec='seconds')
        recs = [{'type': 'session_meta', 'payload': {'id': cid, 'source': source, 'cwd': self._p('~/studio')}},
                {'type': 'event_msg', 'timestamp': stamp, 'payload': {'type': 'task_started'}},
                {'type': 'response_item', 'timestamp': stamp,
                 'payload': {'type': 'message', 'role': 'assistant', 'content': [{'type': 'output_text', 'text': 'Done. Shall I push?'}]}}]
        if last_event != 'task_started':
            recs.append({'type': 'event_msg', 'timestamp': stamp, 'payload': {'type': last_event, 'last_agent_message': 'Done. Shall I push?'}})
        (folder / f'rollout-{cid}.jsonl').write_text('\n'.join(json.dumps(r) for r in recs) + '\n')
        self.env.codex_index.parent.mkdir(parents=True, exist_ok=True)
        with open(self.env.codex_index, 'a') as f:
            f.write(json.dumps({'id': cid, 'thread_name': title, 'updated_at': stamp}) + '\n')

    def _p(self, cwd):
        return str(self.root / cwd[2:]) if cwd.startswith('~/') else cwd


class CompileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = FakeHome(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def compile(self):
        return cs.compile_sessions(NOW, self.home.env)

    def by_title(self, payload):
        return {r.get('title') or r.get('label'): r for r in payload['sessions']}

    def test_states_from_registry_and_app_summary(self):
        self.home.registry('h1', 'waiting', 'permission prompt')
        self.home.desktop('h1', 'Needs a yes')
        self.home.registry('h2', 'busy')
        self.home.desktop('h2', 'Working away')
        self.home.desktop('h3', 'Asked and closed', category='blocked', needs='Pick a colour')
        self.home.desktop('h4', 'Just finished')
        rows = self.by_title(self.compile())
        self.assertEqual(rows['Needs a yes']['state'], 'needs_approval')
        self.assertTrue(rows['Needs a yes']['live'])
        self.assertEqual(rows['Working away']['state'], 'running')
        self.assertEqual(rows['Asked and closed']['state'], 'unanswered')
        self.assertEqual(rows['Asked and closed']['content'], 'Pick a colour')
        self.assertEqual(rows['Asked and closed']['content_source'], 'app')
        self.assertEqual(rows['Just finished']['state'], 'finished')

    def test_closed_session_with_a_pending_question_and_a_message_line(self):
        self.home.desktop('h5', 'Stopped asking')
        self.home.transcript('h5', 'Which branch should I use?', pending_tool='AskUserQuestion')
        row = self.by_title(self.compile())['Stopped asking']
        self.assertEqual(row['state'], 'unanswered')
        self.assertEqual(row['content'], 'Which branch should I use?')
        self.assertEqual(row['content_source'], 'message')

    def test_private_rows_carry_only_a_label(self):
        self.home.desktop('p1', 'Quarterly numbers', cwd='~/clients/acme/books')
        self.home.desktop('p2', 'Run payroll for March')
        self.home.desktop('p3', 'Call Alex about the roof')
        self.home.desktop('p4', 'Alexandria notes')          # not a whole-word match
        payload = self.compile()
        private = [r for r in payload['sessions'] if r['private']]
        self.assertEqual(sorted(r['label'] for r in private), ['Client work', 'Finance', 'Private'])
        for r in private:
            self.assertEqual(set(r) - {'maybe_stuck'}, {'tool', 'kind', 'state', 'live', 'since', 'last_activity', 'id', 'private', 'label'})
            self.assertTrue(r['id'].startswith('private-'))
        blob = json.dumps(payload)
        for word in ('Quarterly', 'payroll', 'Alex about', 'acme'):
            self.assertNotIn(word, blob)
        self.assertIn('Alexandria notes', blob)

    def test_scrub_removes_links_emails_paths_and_keys(self):
        s = cs.scrub('See https://example.com and mail me@example.com at /Users/someone/x or sk-abcdefghijklmnop', 200)
        self.assertEqual(s, 'See a link and mail an email address at a file path or [removed]')
        self.assertTrue(len(cs.scrub('word ' * 100, 40)) <= 40)

    def test_config_fails_closed(self):
        self.home.env.config_path.write_text('{}')
        with self.assertRaises(cs.ConfigError):
            self.compile()
        self.home.env.config_path.unlink()
        with self.assertRaises(cs.ConfigError):
            self.compile()

    def test_archived_and_old_sessions_are_left_out(self):
        self.home.desktop('a1', 'Archived', archived=True)
        self.home.desktop('a2', 'Two days ago', last=48 * 60, mtime_minutes=48 * 60)
        self.home.desktop('a3', 'Fresh')
        titles = set(self.by_title(self.compile()))
        self.assertEqual(titles, {'Fresh'})

    def test_one_row_per_scheduled_task(self):
        self.home.desktop('t1', 'Digest run 1', task='daily-digest', last=120)
        self.home.desktop('t2', 'Digest run 2', task='daily-digest', last=5)
        rows = self.by_title(self.compile())
        self.assertEqual(list(rows), ['Digest run 2'])
        self.assertEqual(rows['Digest run 2']['task'], 'daily digest')
        self.assertEqual(rows['Digest run 2']['kind'], 'scheduled')

    def test_codex_is_optional_and_reads_desktop_chats_only(self):
        payload = self.compile()
        self.assertFalse(payload['inputs']['codex']['ok'])
        self.home.codex('c1', 'task_complete')
        self.home.codex('c2', 'task_complete', source='exec')
        payload = self.compile()
        self.assertTrue(payload['inputs']['codex']['ok'])
        rows = self.by_title(payload)
        self.assertEqual(list(rows), ['Codex thing'])
        self.assertEqual(rows['Codex thing']['state'], 'needs_reply')
        self.assertEqual(rows['Codex thing']['tool'], 'codex')

    def test_order_puts_what_needs_you_first(self):
        self.home.desktop('o1', 'Finished one')
        self.home.registry('o2', 'busy')
        self.home.desktop('o2', 'Running one')
        self.home.registry('o3', 'waiting', 'input needed')
        self.home.desktop('o3', 'Asking one')
        titles = [r['title'] for r in self.compile()['sessions']]
        self.assertEqual(titles, ['Asking one', 'Running one', 'Finished one'])

    def test_missing_folders_are_reported_not_fatal(self):
        shutil.rmtree(self.home.env.desktop_dir)
        shutil.rmtree(self.home.env.registry_dir)
        payload = self.compile()
        self.assertFalse(payload['inputs']['claude_desktop']['ok'])
        self.assertFalse(payload['inputs']['claude_registry']['ok'])
        self.assertEqual(payload['sessions'], [])

    def test_writes_a_whole_file(self):
        self.home.desktop('w1', 'Written out')
        out = self.tmp / 'out' / 'sessions.json'
        cs.atomic_write_json(out, self.compile())
        self.assertEqual(json.loads(out.read_text())['sessions'][0]['title'], 'Written out')


if __name__ == '__main__':
    unittest.main(verbosity=1)
