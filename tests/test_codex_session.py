"""Offline lifecycle contracts: no Codex inference, tmux or Telegram."""

import json
import os
import subprocess
import sys
import threading
import time

import pytest

from d_brain.services.codex_session import CodexSession
from d_brain.services.tmux_parse import PaneState

THREAD = "0199a213-81c0-7800-8aa1-bbab2a035a53"
OTHER = "0199a213-81c0-7800-8aa1-bbab2a035a54"


def stream(*, thread=THREAD, reply="Ответ", terminal=True):
    rows = [
        {"type": "thread.started", "thread_id": thread},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {
            "type": "command_execution", "aggregated_output": "PRIVATE TOOL DATA",
        }},
        {"type": "item.completed", "item": {
            "type": "agent_message", "text": reply,
        }},
    ]
    if terminal:
        rows.append({"type": "turn.completed", "usage": {}})
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"


class FakeProcess:
    pid = 99999999

    def __init__(self, output=None, *, code=0, timeout=False, gate=None):
        self.output = stream() if output is None else output
        self.code = code
        self.returncode = None
        self.timeout = timeout
        self.gate = gate
        self.input = None
        self.stopped = False

    def communicate(self, input, timeout):
        self.input = input
        if self.gate:
            self.gate.wait(3)
        if self.timeout:
            raise subprocess.TimeoutExpired("fixture", timeout, output=self.output)
        self.returncode = self.code
        return self.output, None

    def poll(self):
        return self.returncode

    def terminate(self):
        self.stopped = True
        self.returncode = -15

    def kill(self):
        self.stopped = True
        self.returncode = -9

    def wait(self, timeout):
        return self.returncode


class Factory:
    def __init__(self, processes=None):
        self.processes = list(processes or [FakeProcess()])
        self.calls = []

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        return self.processes.pop(0)


def session(tmp_path, factory=None):
    vault = tmp_path / "vault"
    vault.mkdir(exist_ok=True)
    persona = tmp_path / "persona.md"
    persona.write_text("# d-brain session contract\nPRIVATE PERSONA")
    return CodexSession("fixture", vault, tmp_path / "runtime",
                        system_prompt_file=persona, popen=factory or Factory())


def test_accepts_only_agent_reply_and_resumes_exact_thread(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fixture-never-use")
    monkeypatch.setenv("CODEX_API_KEY", "fixture-never-use")
    one, two = FakeProcess(), FakeProcess()
    f = Factory([one, two])
    s = session(tmp_path, f)
    assert s.ask("PRIVATE INPUT", request_id="r1").reply == "Ответ"
    assert "PRIVATE TOOL DATA" not in one.input
    assert "PRIVATE INPUT" in one.input and "PRIVATE PERSONA" in one.input
    assert "PRIVATE INPUT" not in " ".join(f.calls[0][0])
    assert "OPENAI_API_KEY" not in f.calls[0][1]["env"]
    assert "CODEX_API_KEY" not in f.calls[0][1]["env"]
    assert 'forced_login_method="chatgpt"' in f.calls[0][0]
    assert f.calls[0][1]["start_new_session"] is True
    # A different instance/process resumes durable state, never --last.
    assert session(tmp_path, f).ask("next").ok
    assert "resume" in f.calls[1][0] and THREAD in f.calls[1][0]
    assert "--last" not in f.calls[1][0]
    assert not s._inflight.exists()
    assert os.stat(s._state_file).st_mode & 0o777 == 0o600
    assert "PRIVATE" not in s._state_file.read_text()


@pytest.mark.parametrize("output,code", [
    (stream(terminal=False), 0),
    (stream(), 1),
    ("not json", 0),
    (stream() + '{"type":"turn.failed"}\n', 0),
    (stream(reply=""), 0),
    (stream() + '{"type":"turn.completed"}\n', 0),
    ('{"type":"turn.completed"}\n', 0),
    ('{"type":"thread.started","thread_id":"--last"}\n', 0),
    (stream() + '{"type":"item.completed","item":null}\n', 0),
])
def test_uncertain_completion_never_replays_after_restart(tmp_path, output, code):
    f = Factory([FakeProcess(output, code=code)])
    s = session(tmp_path, f)
    assert s.ask("original").status == "unknown"
    assert os.stat(s._inflight).st_mode & 0o777 == 0o600
    restored = session(tmp_path, f)
    assert restored.ask("original").status == "unknown"
    assert len(f.calls) == 1
    assert not restored.force_recover()
    with pytest.raises(RuntimeError):
        restored.clear()
    assert restored._inflight.exists()


def test_timeout_retains_observed_thread_and_stops_only_owned_child(tmp_path):
    proc = FakeProcess(stream(terminal=False), timeout=True)
    f = Factory([proc])
    s = session(tmp_path, f)
    assert s.ask("original", timeout=0.1).status == "unknown"
    assert proc.stopped
    assert json.loads(s._inflight.read_text())["thread_id"] == THREAD
    assert not s.force_recover()


def test_resume_mismatch_cannot_replace_thread(tmp_path):
    f = Factory([FakeProcess(), FakeProcess(stream(thread=OTHER))])
    s = session(tmp_path, f)
    assert s.ask("one").ok
    assert s.ask("two").status == "unknown"
    assert json.loads(s._state_file.read_text())["thread_id"] == THREAD


def test_watchdog_and_clear_do_not_touch_legacy_pending_data(tmp_path):
    f = Factory()
    s = session(tmp_path, f)
    s.runtime_dir.mkdir()
    legacy = s.runtime_dir / "inflight"
    legacy.write_text("legacy pending")
    assert s.ask("new").status == "unknown"
    assert not s.force_recover()
    assert s.current_state() == PaneState.UNKNOWN
    assert legacy.read_text() == "legacy pending"
    assert not f.calls


def test_clear_preserves_vault_and_history_reference(tmp_path):
    f = Factory([FakeProcess(), FakeProcess()])
    s = session(tmp_path, f)
    note = s.work_dir / "note.md"
    note.write_text("keep")
    assert s.ask("one").ok
    s.clear()
    state = json.loads(s._state_file.read_text())
    assert state["previous_thread_id"] == THREAD and state["thread_id"] is None
    assert note.read_text() == "keep"
    assert s.ask("two").ok
    assert "resume" not in f.calls[1][0]


def test_parallel_instances_serialize_and_watchdog_does_not_dispatch(tmp_path):
    gate = threading.Event()
    proc = FakeProcess(gate=gate)
    f = Factory([proc, FakeProcess()])
    one, two = session(tmp_path, f), session(tmp_path, f)
    results = []
    t1 = threading.Thread(target=lambda: results.append(one.ask("one")))
    t1.start()
    deadline = time.monotonic() + 3
    while not f.calls and time.monotonic() < deadline:
        time.sleep(0.001)
    assert not two.force_recover()
    t2 = threading.Thread(target=lambda: results.append(two.ask("two")))
    t2.start()
    time.sleep(0.02)
    assert len(f.calls) == 1
    gate.set()
    t1.join(3)
    t2.join(3)
    assert len(results) == 2 and all(r.ok for r in results)
    assert THREAD in f.calls[1][0]


@pytest.mark.parametrize("broken", ["broken", "[]", '{"thread_id":1}'])
def test_corrupt_state_and_symlink_fail_closed(tmp_path, broken):
    f = Factory()
    s = session(tmp_path, f)
    s.runtime_dir.mkdir()
    s._state_file.write_text(broken)
    assert s.ask("no").status == "error" and not f.calls
    s._state_file.unlink()
    target = tmp_path / "foreign"
    target.write_text("keep")
    s._state_file.symlink_to(target)
    with pytest.raises(ValueError):
        s.ask("no")
    assert target.read_text() == "keep"


def test_spawn_failure_is_known_before_dispatch(tmp_path):
    def unavailable(*args, **kwargs):
        raise FileNotFoundError("fixture")
    s = session(tmp_path, unavailable)
    assert s.ask("not dispatched").status == "error"
    assert not s._inflight.exists()


def test_actual_owned_child_is_reaped_after_timeout(tmp_path):
    processes = []

    def fixture_child(argv, **kwargs):
        proc = subprocess.Popen([sys.executable, "-c",
                                 "import time;time.sleep(30)"], **kwargs)
        processes.append(proc)
        return proc

    s = session(tmp_path, fixture_child)
    assert s.ask("fixture", timeout=0.05).status == "unknown"
    assert processes[0].poll() is not None
    assert s._inflight.exists()


def test_ensure_validates_cli_without_spawning(tmp_path, monkeypatch):
    f = Factory()
    s = session(tmp_path, f)
    monkeypatch.setattr("shutil.which", lambda path: "/fixture/codex")
    s.ensure_session()
    assert not f.calls


def test_completion_storage_failure_is_unknown_and_cannot_replay(tmp_path):
    f = Factory()
    s = session(tmp_path, f)
    write = s._write

    def fail_receipt(path, value):
        if path == s._state_file:
            raise OSError("fixture storage failure after completed turn")
        write(path, value)

    s._write = fail_receipt
    assert s.ask("already executed").status == "unknown"
    assert json.loads(s._inflight.read_text())["thread_id"] == THREAD
    assert session(tmp_path, f).ask("already executed").status == "unknown"
    assert len(f.calls) == 1
