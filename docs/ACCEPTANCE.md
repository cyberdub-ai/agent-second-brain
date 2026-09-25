---
approved: 2026-09-25T19:06:40+03:00
source: docs/PRODUCT-VERDICT.md «До продажи», утверждено владельцем 2026-09-25 18:41 («да»); owner-words.md — 0 реплик (транскриптов проекта нет), пункты собраны руками
---
## Из слов владельца
- [ ] A-01: Вопрос бота доходит до мозга и получает ответ: промпт вставляется режимом bracketed paste (`tmux paste-buffer -p`), Enter отправляет его, а не остаётся в поле ввода — проверка: `grep -c 'paste-buffer.*"-p"' src/d_brain/services/claude_session.py` ≥ 1 (сейчас 0); `uv run pytest tests/test_claude_session.py` — 0 failed; после перезапуска панели мозга локальный прогон doctor печатает `✅ canary` (сейчас `❌ canary: no reply in 120.0s`) — источник: PRODUCT-VERDICT.md, «До продажи» п.1, утверждено владельцем 2026-09-25 «да»
- [ ] A-02: Бот не сдаётся после серии падений: `StartLimitIntervalSec=0` в `deploy/dbrain-bot.service` и в установленном unit, systemd перезапускает бота бесконечно с паузой — проверка: `grep -c '^StartLimitIntervalSec=0' deploy/dbrain-bot.service` = 1 (сейчас 0); `systemctl --user show dbrain-bot -p StartLimitIntervalUSec` → `StartLimitIntervalUSec=0` (сейчас 5min) — источник: PRODUCT-VERDICT.md, «До продажи» п.2, утверждено владельцем 2026-09-25 «да»
- [ ] A-03: Watchdog распознаёт «промпт висит в поле ввода» (текст в строке ввода, модель не работает дольше порога) и очищает строку — проверка: `grep -c 'def test_.*stuck_input' tests/test_watchdog.py` ≥ 1 (сейчас 0); `uv run pytest tests/test_watchdog.py` — 0 failed — источник: PRODUCT-VERDICT.md, «До продажи» п.3, утверждено владельцем 2026-09-25 «да»
- [ ] A-04: Ветка `main` сведена с `origin/main` — проверка: `git rev-list --count HEAD..origin/main` → 0 (сейчас 1) и `git rev-list --count origin/main..HEAD` → 0 после push — источник: PRODUCT-VERDICT.md, «До продажи» п.4, утверждено владельцем 2026-09-25 «да»
- [ ] A-05: Утренний осмотр снова зелёный — проверка: после прогона `dbrain-doctor` (08:00 или ручной `systemctl --user start dbrain-doctor`) `systemctl --user show dbrain-doctor -p Result` → `Result=success` (сейчас `exit-code`) — источник: PRODUCT-VERDICT.md, путь покупателя шаг 6, утверждено владельцем 2026-09-25 «да»

## Не в эту ночь
- Push в `main` с переписыванием истории (force-push) — за владельцем; A-04 делается только rebase + обычным push.

## Не проверено
- Причина падения бота 22.09 04:06 — журнал ротирован; гипотеза «`uv cache prune`» опровергнута (он по воскресеньям 05:15).
- Транскрипция голоса через local Whisper — вживую не проверялась.
