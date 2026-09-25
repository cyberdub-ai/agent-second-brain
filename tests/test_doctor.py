"""Tests for the daily self-diagnostic (Doctor)."""

from d_brain.services.claude_session import AskResult
from d_brain.services.doctor import CheckResult, Doctor


class FakeSession:
    def __init__(self, result: AskResult) -> None:
        self.result = result

    def ask(self, prompt, *, timeout=120, request_id=None) -> AskResult:  # noqa: ANN001
        return self.result


def _ok_check():
    return CheckResult("disk", True, "6 GB free")


def _bad_check():
    return CheckResult("git", False, "push failed")


def test_canary_ok_makes_report_ok():
    sess = FakeSession(AskResult("ok", reply="DBRAIN_OK"))
    rep = Doctor(sess, checks=[_ok_check]).run()
    assert rep.ok
    assert any(c.name == "canary" and c.ok for c in rep.checks)


def test_canary_wrong_reply_fails():
    sess = FakeSession(AskResult("ok", reply="hello?"))
    rep = Doctor(sess, checks=[]).run()
    assert not rep.ok


def test_canary_logged_out_fails_with_reason():
    sess = FakeSession(AskResult("logged_out"))
    rep = Doctor(sess, checks=[]).run()
    canary = next(c for c in rep.checks if c.name == "canary")
    assert not canary.ok
    assert "вход" in canary.detail.lower() or "log" in canary.detail.lower()


def test_failing_local_check_makes_report_not_ok():
    sess = FakeSession(AskResult("ok", reply="DBRAIN_OK"))
    rep = Doctor(sess, checks=[_bad_check]).run()
    assert not rep.ok


def test_report_telegram_green_and_red():
    sess = FakeSession(AskResult("ok", reply="DBRAIN_OK"))
    green = Doctor(sess, checks=[_ok_check]).run().to_telegram()
    assert "🟢" in green
    red = Doctor(sess, checks=[_bad_check]).run().to_telegram()
    assert "🔴" in red
    assert "❌" in red


def test_run_cli_exit_codes_follow_report():
    # upgrade.sh and the systemd OnFailure= hook key off the exit code —
    # a failing canary must be visible as a non-zero exit.
    from d_brain.services.doctor import run_cli

    sent = []
    ok_sess = FakeSession(AskResult("ok", reply="DBRAIN_OK"))
    assert run_cli(ok_sess, checks=[_ok_check], alert=sent.append) == 0

    bad_sess = FakeSession(AskResult("logged_out"))
    assert run_cli(bad_sess, checks=[], alert=sent.append) == 1
    assert len(sent) == 2  # the telegram report goes out either way


def test_canary_is_tagged_as_maintenance():
    # Chat steering keys off the maint- prefix in the inflight id — the
    # canary must never look like a steerable user turn.
    class RecordingSession(FakeSession):
        def __init__(self, result):
            super().__init__(result)
            self.request_ids = []

        def ask(self, prompt, *, timeout=120, request_id=None):
            self.request_ids.append(request_id)
            return self.result

    sess = RecordingSession(AskResult("ok", reply="DBRAIN_OK"))
    Doctor(sess, checks=[]).run()
    assert sess.request_ids and sess.request_ids[0].startswith("maint-")


def test_check_claude_version_resolves_binary_outside_path(monkeypatch, tmp_path):
    # Manual runs (ssh, cron) often lack ~/.local/bin in PATH — the check
    # must resolve the binary like the services do, not false-alarm.
    import d_brain.services.doctor as doc

    fake_bin = tmp_path / ".local" / "bin" / "claude"
    fake_bin.parent.mkdir(parents=True)
    fake_bin.write_text("#!/bin/sh\necho 2.1.0\n")
    fake_bin.chmod(0o755)

    monkeypatch.setenv("PATH", "/usr/bin:/bin")  # no ~/.local/bin
    monkeypatch.setattr(doc.Path, "home", staticmethod(lambda: tmp_path))

    res = doc.check_claude_version()
    assert res.ok
    assert "2.1.0" in res.detail


def test_check_restarts_fails_when_counter_grew(tmp_path):
    # StartLimitIntervalSec=0 silences OnFailure= — a restart loop must
    # surface through the doctor instead.
    from d_brain.services.doctor import check_restarts

    state = tmp_path / "nrestarts"
    first = check_restarts(state, read=lambda: 3)
    assert first.ok  # first run only records the baseline
    same = check_restarts(state, read=lambda: 3)
    assert same.ok
    grew = check_restarts(state, read=lambda: 5)
    assert not grew.ok
    assert "2" in grew.detail
    assert check_restarts(state, read=lambda: 5).ok  # baseline moved


def test_check_restarts_counter_reset_is_ok(tmp_path):
    # systemctl daemon-reload / reboot resets NRestarts to 0 — not an alarm.
    from d_brain.services.doctor import check_restarts

    state = tmp_path / "nrestarts"
    check_restarts(state, read=lambda: 7)
    assert check_restarts(state, read=lambda: 0).ok


def test_check_whisper_ok_on_transcription(monkeypatch):
    # Goes through the production transcriber — the same path a voice
    # message takes — with a generated silent WAV.
    import d_brain.services.doctor as doc

    sent = []

    class FakeTranscriber:
        def __init__(self, url):
            sent.append(url)

        async def transcribe(self, audio):
            sent.append(audio[:4])
            return ""

    monkeypatch.setattr(doc, "WhisperTranscriber", FakeTranscriber)
    assert doc.check_whisper("http://127.0.0.1:8000").ok
    assert sent == ["http://127.0.0.1:8000", b"RIFF"]


def test_check_whisper_fails_when_unreachable(monkeypatch):
    import d_brain.services.doctor as doc

    class DeadTranscriber:
        def __init__(self, url):
            pass

        async def transcribe(self, audio):
            raise doc.httpx.ConnectError("refused")

    monkeypatch.setattr(doc, "WhisperTranscriber", DeadTranscriber)
    res = doc.check_whisper("http://127.0.0.1:8000")
    assert not res.ok
    assert "refused" in res.detail


def test_check_backup_fails_without_snapshot(tmp_path):
    from d_brain.services.doctor import check_backup

    res = check_backup(tmp_path / "backups")
    assert not res.ok
    assert "нет" in res.detail


def test_check_backup_fresh_ok_stale_fails(tmp_path):
    import os
    import time

    from d_brain.services.doctor import check_backup

    snap = tmp_path / "vault-2026-09-25.tgz"
    snap.write_bytes(b"x")
    assert check_backup(tmp_path).ok
    old = time.time() - 27 * 3600
    os.utime(snap, (old, old))
    stale = check_backup(tmp_path)
    assert not stale.ok
    assert "27" in stale.detail
