"""Codex CLI backend with durable, fail-closed turn ownership.

No tmux, API key, login, or automatic replay. Only a successful JSONL terminal
event and successful child exit acknowledge a turn. Uncertain execution leaves
an owner-only marker for manual reconciliation, including after process death.
"""

import fcntl
import json
import os
import shutil
import signal
import subprocess
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path

from d_brain.services.claude_session import DEFAULT_TIMEOUT, AskResult
from d_brain.services.tmux_parse import PaneState


class CodexSession:
    supports_steering = False
    supports_safe_replay = False

    def __init__(
        self,
        session_name: str,
        work_dir: Path,
        runtime_dir: Path,
        *,
        system_prompt_file: Path,
        codex_bin: str = "codex",
        model: str | None = None,
        popen=subprocess.Popen,
    ) -> None:
        self.session_name = session_name
        self.work_dir = Path(work_dir).resolve()
        self.runtime_dir = Path(runtime_dir)
        self.system_prompt_file = Path(system_prompt_file)
        self.codex_bin = codex_bin
        self.model = model
        self._popen = popen
        self._process = None
        self._process_lock = threading.Lock()
        self._state_file = self.runtime_dir / "codex-thread.json"
        self._inflight = self.runtime_dir / "codex-inflight.json"

    def _prepare(self) -> None:
        if self.runtime_dir.is_symlink():
            raise ValueError("symlink runtime refused")
        self.runtime_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        for name in ("pane.lock", "codex-thread.json", "codex-inflight.json"):
            if (self.runtime_dir / name).is_symlink():
                raise ValueError("symlink runtime file refused")

    @contextmanager
    def _locked(self, *, blocking: bool = True):
        self._prepare()
        fd = os.open(self.runtime_dir / "pane.lock", os.O_CREAT | os.O_RDWR, 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
            except BlockingIOError:
                yield False
                return
            yield True
        finally:
            os.close(fd)

    def _write(self, path: Path, value: dict) -> None:
        temp = self.runtime_dir / (".codex-" + uuid.uuid4().hex)
        try:
            fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as out:
                json.dump(value, out, ensure_ascii=False)
                out.write("\n")
                out.flush()
                os.fsync(out.fileno())
            os.replace(temp, path)
            # Persist rename/unlink ordering across a machine crash.
            fd = os.open(self.runtime_dir, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        finally:
            temp.unlink(missing_ok=True)

    def _state(self) -> dict:
        if not self._state_file.exists():
            return {"thread_id": None, "cwd": str(self.work_dir)}
        value = json.loads(self._state_file.read_text())
        if not isinstance(value, dict):
            raise ValueError("invalid runtime state")
        if value.get("cwd") != str(self.work_dir):
            raise ValueError("runtime belongs to another workspace")
        if value.get("thread_id") is not None:
            if not isinstance(value["thread_id"], str):
                raise ValueError("invalid thread identity")
            uuid.UUID(value["thread_id"])
        return value

    def _uncertain(self) -> bool:
        # Never reinterpret a legacy in-flight request as safe to replay.
        return self._inflight.exists() or (self.runtime_dir / "inflight").exists()

    def ensure_session(self) -> None:
        with self._locked():
            self._state()
            if self._uncertain():
                raise RuntimeError("pending outcome requires reconciliation")
            if not shutil.which(self.codex_bin):
                raise RuntimeError("Codex CLI is unavailable")
            if "# d-brain session contract" not in self.system_prompt_file.read_text():
                raise RuntimeError("invalid brain persona")

    def is_healthy(self) -> bool:
        try:
            self._prepare()
            self._state()
            return True
        except (OSError, ValueError, TypeError):
            return False

    def current_state(self) -> PaneState:
        return PaneState.UNKNOWN if self._uncertain() else PaneState.READY

    def is_working(self) -> bool:
        with self._process_lock:
            return self._process is not None and self._process.poll() is None

    def has_pending_input(self) -> bool:
        return False

    def is_turn_active(self) -> bool:
        return self.is_working()

    def is_steerable_turn(self) -> bool:
        return False

    def force_recover(self) -> bool:
        # Watchdog cannot clear unknown outcomes, kill clients or spawn a turn.
        with self._locked(blocking=False) as got:
            return bool(got and not self._uncertain() and self.is_healthy())

    def _stop_owned(self) -> None:
        with self._process_lock:
            proc = self._process
            if proc is not None and proc.poll() is None:
                try:
                    if isinstance(proc, subprocess.Popen):
                        # This child was started in its own session above.
                        if os.getpgid(proc.pid) != proc.pid:
                            return
                        os.killpg(proc.pid, signal.SIGTERM)
                    else:
                        proc.terminate()
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    try:
                        if isinstance(proc, subprocess.Popen):
                            os.killpg(proc.pid, signal.SIGKILL)
                        else:
                            proc.kill()
                        proc.wait(timeout=3)
                    except (OSError, subprocess.TimeoutExpired):
                        pass  # Durable unknown marker still blocks another turn.
                except OSError:
                    pass

    def interrupt(self) -> None:
        self._stop_owned()

    def kill(self) -> None:
        self._stop_owned()

    def steer(self, text: str) -> None:
        raise RuntimeError("exec backend queues messages; steering is unavailable")

    def clear(self) -> None:
        with self._locked():
            if self._uncertain():
                raise RuntimeError("cannot clear an uncertain outcome")
            # Keep the Codex rollout, vault, and previous receipt intact.
            previous = self._state()
            self._write(self._state_file, {
                "cwd": str(self.work_dir), "thread_id": None,
                "previous_thread_id": previous.get("thread_id"),
            })

    def send_control(self, text: str) -> None:
        if text not in ("/clear", "/compact"):
            raise ValueError("control unsupported by Codex exec")
        self.clear()

    def _argv(self, thread: str | None) -> list[str]:
        args = [self.codex_bin, "-C", str(self.work_dir),
                "-c", 'forced_login_method="chatgpt"',
                "-c", 'approval_policy="never"',
                "-c", 'default_permissions=":workspace"', "exec"]
        if thread:
            args += ["resume"]
        args += ["--json", "--skip-git-repo-check"]
        if self.model:
            args += ["--model", self.model]
        return args + ([thread] if thread else []) + ["-"]

    def _accept(self, output: str, expected: str | None, returncode: int) -> tuple:
        thread = None
        reply = None
        started = False
        completed = False
        for line in output.splitlines():
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("invalid event")
            kind = event.get("type")
            if kind == "thread.started":
                candidate = event["thread_id"]
                uuid.UUID(candidate)
                if thread is not None or (expected and expected != candidate):
                    raise ValueError("thread correlation mismatch")
                thread = candidate
            elif kind == "turn.started":
                if not thread or started:
                    raise ValueError("unexpected turn")
                started = True
            elif kind == "item.completed":
                if not started or completed:
                    raise ValueError("item outside active turn")
                item = event.get("item", {})
                if item.get("type") == "agent_message":
                    reply = item.get("text")
                    if not isinstance(reply, str):
                        raise ValueError("invalid reply")
            elif kind == "turn.completed":
                if not started or completed:
                    raise ValueError("unexpected terminal event")
                completed = True
            elif kind in ("error", "turn.failed"):
                raise ValueError("turn failure")
        if returncode != 0 or not completed or not reply or not reply.strip():
            raise ValueError("turn completion unconfirmed")
        return thread, reply

    def _observe_thread(self, output, transaction: dict, expected: str | None):
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        for line in (output or "").splitlines():
            try:
                event = json.loads(line)
                if event.get("type") != "thread.started":
                    continue
                thread = event["thread_id"]
                uuid.UUID(thread)
                if expected and thread != expected:
                    return
                transaction["thread_id"] = thread
                self._write(self._inflight, transaction)
                return
            except (OSError, ValueError, TypeError, AttributeError, KeyError):
                continue

    def ask(
        self, prompt: str, *, timeout: float = DEFAULT_TIMEOUT,
        request_id: str | None = None, wrap: bool = True,
    ) -> AskResult:
        with self._locked():
            if self._uncertain():
                return AskResult("unknown", detail="pending outcome; no replay")
            try:
                state = self._state()
                persona = self.system_prompt_file.read_text()
                if "# d-brain session contract" not in persona:
                    raise ValueError("invalid persona")
            except (OSError, ValueError, TypeError):
                return AskResult("error", detail="invalid local session state")
            transaction = {"status": "prepared", "request_id": request_id,
                           "thread_id": state.get("thread_id"), "owner": os.getpid()}
            self._write(self._inflight, transaction)
            env = os.environ.copy()
            for key in ("OPENAI_API_KEY", "CODEX_API_KEY", "CODEX_THREAD_ID",
                        "CX_ROUTE_DIR", "CX_RESTART_RECEIPT", "TMUX_PANE"):
                env.pop(key, None)
            env["CODEX_SKIP_PROXY_CHECKS"] = "1"
            try:
                proc = self._popen(
                    self._argv(state.get("thread_id")), cwd=self.work_dir,
                    env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL, text=True, start_new_session=True,
                )
            except OSError:
                self._inflight.unlink(missing_ok=True)
                return AskResult("error", detail="CLI spawn failed before dispatch")
            with self._process_lock:
                self._process = proc
            transaction.update(status="unknown", child_pid=proc.pid)
            try:
                self._write(self._inflight, transaction)
                # Private persona and user input never appear in argv/logs.
                output, _ = proc.communicate(persona + "\n\n" + prompt, timeout=timeout)
                self._observe_thread(output, transaction, state.get("thread_id"))
                thread, reply = self._accept(
                    output, state.get("thread_id"), proc.returncode
                )
                self._write(self._state_file, {
                    "cwd": str(self.work_dir), "thread_id": thread,
                    "last_request_id": request_id, "status": "completed",
                })
                self._inflight.unlink()
                return AskResult("ok", reply=reply)
            except subprocess.TimeoutExpired as exc:
                self._observe_thread(exc.output, transaction, state.get("thread_id"))
                self._stop_owned()
                return AskResult("unknown", detail="execution unconfirmed; no replay")
            except (OSError, ValueError, TypeError, AttributeError, KeyError):
                self._stop_owned()
                return AskResult("unknown", detail="execution unconfirmed; no replay")
            finally:
                with self._process_lock:
                    self._process = None
