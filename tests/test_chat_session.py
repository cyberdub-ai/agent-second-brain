"""Tests for ChatSessionManager — chat messages routed to the shared session."""

import asyncio

from d_brain.services.claude_session import AskResult


class FakeSession:
    def __init__(self, result: AskResult) -> None:
        self.result = result
        self.prompts: list[str] = []
        self.cleared = 0

    def ask(self, prompt: str, **kwargs) -> AskResult:
        self.prompts.append(prompt)
        return self.result

    def clear(self) -> None:
        self.cleared += 1


def _manager(tmp_path, result: AskResult):
    from d_brain.services.chat_session import ChatSessionManager

    return ChatSessionManager(tmp_path, session=FakeSession(result))


def test_send_message_returns_reply_on_ok(tmp_path):
    m = _manager(tmp_path, AskResult("ok", reply="привет"))
    reply = asyncio.run(m.send_message(1, "здравствуй"))
    assert reply == "привет"
    assert m._session.prompts == ["здравствуй"]


def test_send_message_maps_rate_limited(tmp_path):
    m = _manager(tmp_path, AskResult("rate_limited"))
    reply = asyncio.run(m.send_message(1, "x"))
    assert "Лимит" in reply


def test_unknown_outcome_is_not_retried(tmp_path):
    m = _manager(tmp_path, AskResult("unknown"))
    reply = asyncio.run(m.send_message(1, "original"))
    assert "Повтор остановлен" in reply
    assert m._session.prompts == ["original"]


def test_exec_chat_messages_wait_in_order(tmp_path):
    import threading

    from d_brain.services.chat_session import ChatSessionManager

    async def scenario():
        from d_brain.services import runtime
        runtime.reset()
        gate, started = threading.Event(), threading.Event()

        class SerialSession(FakeSession):
            supports_steering = False

            def ask(self, prompt, **kwargs):
                self.prompts.append(prompt)
                if prompt == "one":
                    started.set()
                    assert gate.wait(3)
                return AskResult("ok", reply=prompt)

        s = SerialSession(AskResult("ok"))
        m = ChatSessionManager(tmp_path, session=s)
        assert not m.supports_steering
        one = asyncio.create_task(m.send_message(1, "one"))
        assert await asyncio.to_thread(started.wait, 3)
        two = asyncio.create_task(m.send_message(1, "two"))
        await asyncio.sleep(0.02)
        assert s.prompts == ["one"]
        gate.set()
        assert await asyncio.gather(one, two) == ["one", "two"]
        assert s.prompts == ["one", "two"]
        runtime.reset()

    asyncio.run(scenario())


def test_reset_clears_live_session(tmp_path):
    m = _manager(tmp_path, AskResult("ok", reply=""))
    m.reset(1)
    assert m._session.cleared == 1
