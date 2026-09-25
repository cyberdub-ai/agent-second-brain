---
approved: 2026-09-25T19:44:03+03:00
source: docs/PRODUCT-VERDICT.md «До продажи», утверждено владельцем 2026-09-25 18:41 («да»); owner-words.md — 0 реплик (транскриптов проекта нет), пункты собраны руками
---
## Из слов владельца
- [x] A-01: Вопрос бота доходит до мозга и получает ответ: промпт вставляется режимом bracketed paste (`tmux paste-buffer -p`), Enter отправляет его, а не остаётся в поле ввода — проверка: `grep -c 'paste-buffer.*"-p"' src/d_brain/services/claude_session.py` ≥ 1 (сейчас 0); `uv run pytest tests/test_claude_session.py` — 0 failed; после перезапуска панели мозга локальный прогон doctor печатает `✅ canary` (сейчас `❌ canary: no reply in 120.0s`) — источник: PRODUCT-VERDICT.md, «До продажи» п.1, утверждено владельцем 2026-09-25 «да»
- [x] A-02: Бот не сдаётся после серии падений: `StartLimitIntervalSec=0` в `deploy/dbrain-bot.service` и в установленном unit, systemd перезапускает бота бесконечно с паузой — проверка: `grep -c '^StartLimitIntervalSec=0' deploy/dbrain-bot.service` = 1 (сейчас 0); `systemctl --user show dbrain-bot -p StartLimitIntervalUSec` → `StartLimitIntervalUSec=0` (сейчас 5min) — источник: PRODUCT-VERDICT.md, «До продажи» п.2, утверждено владельцем 2026-09-25 «да»
- [x] A-03: Watchdog распознаёт «промпт висит в поле ввода» (текст в строке ввода, модель не работает дольше порога) и очищает строку — проверка: `grep -c 'def test_.*stuck_input' tests/test_watchdog.py` ≥ 1 (сейчас 0); `uv run pytest tests/test_watchdog.py` — 0 failed — источник: PRODUCT-VERDICT.md, «До продажи» п.3, утверждено владельцем 2026-09-25 «да»
- [ ] A-04: Ветка `main` сведена с `origin/main` и отправлена в `fork` — проверка: `git rev-list --count HEAD..origin/main` → 0 и `git rev-list --count fork/main..HEAD` → 0 — источник: PRODUCT-VERDICT.md, «До продажи» п.4, утверждено владельцем 2026-09-25 «да»; критерий `fork` — владелец 2026-09-25 «да, fork»
- [x] A-05: Утренний осмотр снова зелёный — проверка: после прогона `dbrain-doctor` (08:00 или ручной `systemctl --user start dbrain-doctor`) `systemctl --user show dbrain-doctor -p Result` → `Result=success` (сейчас `exit-code`) — источник: PRODUCT-VERDICT.md, путь покупателя шаг 6, утверждено владельцем 2026-09-25 «да»
- [x] A-06: Doctor тревожит при серии рестартов бота: читает `NRestarts` unit `dbrain-bot` и валит осмотр, если счётчик вырос с прошлого прогона (замена `OnFailure=`, который после `StartLimitIntervalSec=0` молчит) (идея агента) — проверка: `grep -c 'NRestarts' src/d_brain/services/doctor.py` ≥ 1 (сейчас 0); `uv run pytest tests/test_doctor.py` — 0 failed — источник: штурм 2026-09-25, docs/IDEAS.md
- [x] A-07: Doctor проверяет local Whisper — голос обещан покупателю и вживую не проверен (идея агента) — проверка: `grep -c 'def check_whisper' src/d_brain/services/doctor.py` ≥ 1 (сейчас 0); после `systemctl --user start dbrain-doctor` → `Result=success` — источник: штурм 2026-09-25, docs/IDEAS.md

## Не в эту ночь
- Push в `main` с переписыванием истории (force-push) — за владельцем; A-04 делается только rebase + обычным push.

## Не проверено
- Причина падения бота 22.09 04:06 — журнал ротирован; гипотеза «`uv cache prune`» опровергнута (он по воскресеньям 05:15).

## Черновик (ждёт да)
- [ ] A-08: Ночной `process.sh` коммитит только vault и не пушит в чужой `origin` — `git add -A` по всему репо уже унёс недоделанный код в коммиты «process daily» (идея агента) — проверка: `grep -c 'add -A -- vault' scripts/process.sh` ≥ 2 (сейчас 0); `grep -c 'git push' scripts/process.sh` = 0 — источник: штурм 2026-09-25 цикл 2, docs/IDEAS.md
- [ ] A-09: Заметки пользователя бэкапятся ежедневным снимком vault, doctor валит осмотр, если снимку больше 26 ч (идея агента) — проверка: `grep -c 'def check_backup' src/d_brain/services/doctor.py` ≥ 1 (сейчас 0); после `systemctl --user start dbrain-doctor` → `Result=success` — источник: штурм 2026-09-25 цикл 2, docs/IDEAS.md
- [ ] A-10: README.ru.md честно описывает приватность: голос расшифровывается локальным Whisper, а не Deepgram (идея агента) — проверка: `grep -c 'Whisper' README.ru.md` ≥ 1 (сейчас 0) — источник: штурм 2026-09-25 цикл 2, docs/IDEAS.md
- [ ] A-11: Голосовое не падает на холодной модели Whisper: таймаут транскрибера `WHISPER_TIMEOUT` = 300 с (холодный ответ 112 с при потолке 120) (идея агента) — проверка: `grep -c 'WHISPER_TIMEOUT' src/d_brain/services/transcription.py` ≥ 1 (сейчас 0) — источник: штурм 2026-09-25 цикл 2, docs/IDEAS.md
