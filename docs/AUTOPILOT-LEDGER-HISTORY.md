# AUTOPILOT-LEDGER — agent-second-brain, цикл 1 с 2026-09-25

## Роль

solo — правила роли: `~/.claude/skills/autopilot/SKILL.md`. Цель: прод-готовность по docs/ACCEPTANCE.md. Резерв 10%.

## Пункты

- [x] B-01 ← A-01: Вопрос бота доходит до мозга и получает ответ: промпт вставляется режимом bracketed paste (`tmux paste-buffer -p`), Enter отправляет его, а не остаётся в поле ввода — проверка: `grep -c 'paste-buffer.*"-p"' src/d_brain/services/claude_session.py` ≥ 1 (сейчас 0); `uv run pytest tests/test_claude_session.py` — 0 failed; после перезапуска панели мозга локальный прогон doctor печатает `✅ canary` (сейчас `❌ canary: no reply in 120.0s`) — источник: PRODUCT-VERDICT.md, «До продажи» п.1, утверждено владельцем 2026-09-25 «да»
- [x] B-02 ← A-02: Бот не сдаётся после серии падений: `StartLimitIntervalSec=0` в `deploy/dbrain-bot.service` и в установленном unit, systemd перезапускает бота бесконечно с паузой — проверка: `grep -c '^StartLimitIntervalSec=0' deploy/dbrain-bot.service` = 1 (сейчас 0); `systemctl --user show dbrain-bot -p StartLimitIntervalUSec` → `StartLimitIntervalUSec=0` (сейчас 5min) — источник: PRODUCT-VERDICT.md, «До продажи» п.2, утверждено владельцем 2026-09-25 «да»
- [x] B-03 ← A-03: Watchdog распознаёт «промпт висит в поле ввода» (текст в строке ввода, модель не работает дольше порога) и очищает строку — проверка: `grep -c 'def test_.*stuck_input' tests/test_watchdog.py` ≥ 1 (сейчас 0); `uv run pytest tests/test_watchdog.py` — 0 failed — источник: PRODUCT-VERDICT.md, «До продажи» п.3, утверждено владельцем 2026-09-25 «да»
- [~] B-04 ← A-04: Ветка `main` сведена с `origin/main` — проверка: `git rev-list --count HEAD..origin/main` → 0 (сейчас 1) и `git rev-list --count origin/main..HEAD` → 0 после push — источник: PRODUCT-VERDICT.md, «До продажи» п.4, утверждено владельцем 2026-09-25 «да»
  - ⏳ ждёт владельца (2026-09-25): upstream `origin/main` (7828ed6) влит merge-коммитом, `HEAD..origin/main` = 0, тесты 257 passed. Rebase отменён: `origin` — чужой upstream smixs, rebase переписал бы 18 опубликованных коммитов форка. Push сторож автопилота отбил. Осталось отправить `main` в ремоут `fork` (fast-forward). Критерий `origin/main..HEAD` = 0 недостижим без push в чужой smixs — предлагаю заменить на `fork/main..HEAD` = 0.
- [x] B-05 ← A-05: Утренний осмотр снова зелёный — проверка: после прогона `dbrain-doctor` (08:00 или ручной `systemctl --user start dbrain-doctor`) `systemctl --user show dbrain-doctor -p Result` → `Result=success` (сейчас `exit-code`) — источник: PRODUCT-VERDICT.md, путь покупателя шаг 6, утверждено владельцем 2026-09-25 «да»

## ⛔ Не в эту ночь
- Push в `main` с переписыванием истории (force-push) — за владельцем; A-04 делается только rebase + обычным push.


---

# AUTOPILOT-LEDGER — agent-second-brain, цикл 2 с 2026-09-25

## Роль

solo — правила роли: `~/.claude/skills/autopilot/SKILL.md`. Цель: прод-готовность по docs/ACCEPTANCE.md. Резерв 10%.

## Пункты

- [x] B-01 ← A-01: Вопрос бота доходит до мозга и получает ответ: промпт вставляется режимом bracketed paste (`tmux paste-buffer -p`), Enter отправляет его, а не остаётся в поле ввода — проверка: `grep -c 'paste-buffer.*"-p"' src/d_brain/services/claude_session.py` ≥ 1 (сейчас 0); `uv run pytest tests/test_claude_session.py` — 0 failed; после перезапуска панели мозга локальный прогон doctor печатает `✅ canary` (сейчас `❌ canary: no reply in 120.0s`) — источник: PRODUCT-VERDICT.md, «До продажи» п.1, утверждено владельцем 2026-09-25 «да»
- [x] B-02 ← A-02: Бот не сдаётся после серии падений: `StartLimitIntervalSec=0` в `deploy/dbrain-bot.service` и в установленном unit, systemd перезапускает бота бесконечно с паузой — проверка: `grep -c '^StartLimitIntervalSec=0' deploy/dbrain-bot.service` = 1 (сейчас 0); `systemctl --user show dbrain-bot -p StartLimitIntervalUSec` → `StartLimitIntervalUSec=0` (сейчас 5min) — источник: PRODUCT-VERDICT.md, «До продажи» п.2, утверждено владельцем 2026-09-25 «да»
- [x] B-03 ← A-03: Watchdog распознаёт «промпт висит в поле ввода» (текст в строке ввода, модель не работает дольше порога) и очищает строку — проверка: `grep -c 'def test_.*stuck_input' tests/test_watchdog.py` ≥ 1 (сейчас 0); `uv run pytest tests/test_watchdog.py` — 0 failed — источник: PRODUCT-VERDICT.md, «До продажи» п.3, утверждено владельцем 2026-09-25 «да»
- [~] B-04 ← A-04: Ветка `main` сведена с `origin/main` и отправлена в `fork` — проверка: `git rev-list --count HEAD..origin/main` → 0 и `git rev-list --count fork/main..HEAD` → 0 — источник: PRODUCT-VERDICT.md, «До продажи» п.4, утверждено владельцем 2026-09-25 «да»; критерий `fork` — владелец 2026-09-25 «да, fork»
  - ⏳ ждёт владельца (2026-09-25): upstream `origin/main` (7828ed6) влит merge-коммитом, `HEAD..origin/main` = 0, тесты 257 passed. Rebase отменён: `origin` — чужой upstream smixs, rebase переписал бы 18 опубликованных коммитов форка. Push сторож автопилота отбил. Осталось отправить `main` в ремоут `fork` (fast-forward). Критерий `origin/main..HEAD` = 0 недостижим без push в чужой smixs — предлагаю заменить на `fork/main..HEAD` = 0.
- [x] B-05 ← A-05: Утренний осмотр снова зелёный — проверка: после прогона `dbrain-doctor` (08:00 или ручной `systemctl --user start dbrain-doctor`) `systemctl --user show dbrain-doctor -p Result` → `Result=success` (сейчас `exit-code`) — источник: PRODUCT-VERDICT.md, путь покупателя шаг 6, утверждено владельцем 2026-09-25 «да»

## Цикл 2 — принято из ACCEPTANCE

- [x] B-06 ← A-06: Doctor тревожит при серии рестартов бота: читает `NRestarts` unit `dbrain-bot` и валит осмотр, если счётчик вырос с прошлого прогона (замена `OnFailure=`, который после `StartLimitIntervalSec=0` молчит) (идея агента) — проверка: `grep -c 'NRestarts' src/d_brain/services/doctor.py` ≥ 1 (сейчас 0); `uv run pytest tests/test_doctor.py` — 0 failed — источник: штурм 2026-09-25, docs/IDEAS.md
- [x] B-07 ← A-07: Doctor проверяет local Whisper — голос обещан покупателю и вживую не проверен (идея агента) — проверка: `grep -c 'def check_whisper' src/d_brain/services/doctor.py` ≥ 1 (сейчас 0); после `systemctl --user start dbrain-doctor` → `Result=success` — источник: штурм 2026-09-25, docs/IDEAS.md

## ⛔ Не в эту ночь
- Push в `main` с переписыванием истории (force-push) — за владельцем; A-04 делается только rebase + обычным push.
