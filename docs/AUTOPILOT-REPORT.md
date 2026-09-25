## Цикл 1 — 25.09.2026

### Сделано
- B-01 (A-01): paste-buffer -p (2f4b190); grep=1; test_claude_session 42 passed; панель пересоздана, локальный doctor: ✅ canary: сессия отвечает
- B-02 (A-02): StartLimitIntervalSec=0 (a4b7b8b); grep=1; unit установлен, daemon-reload; StartLimitIntervalUSec=0; бот active
- B-05 (A-05): systemctl --user start dbrain-doctor → Result=success, ExecMainStatus=0, ok=True
- B-03 (A-03): has_pending_input + Watchdog._is_input_stuck → recovered_stuck_input; grep stuck_input=3; test_watchdog 0 failed, весь набор 257 passed; watchdog перезапущен, STATUS healthy

## Цикл 25.09.2026
### Цель
Прод-готовность по docs/ACCEPTANCE.md: главный контур «сообщение → ответ мозга» живой.
### Сделано
- [x] B-01 ← A-01: bracketed paste (`paste-buffer -p`) — 2f4b190
- [x] B-02 ← A-02: `StartLimitIntervalSec=0` — a4b7b8b
- [x] B-03 ← A-03: watchdog `stuck_input` → перезапуск мозга — 5b6248d
- [x] B-05 ← A-05: doctor зелёный
- upstream `origin/main` (7828ed6) влит merge-коммитом — 5fa242a
### Задеплоено и как проверено
- unit бота установлен, `daemon-reload`, бот перезапущен → `StartLimitIntervalUSec=0`, `active`
- панель мозга пересоздана `force_recover` → локальный doctor `✅ canary: сессия отвечает`
- `systemctl --user start dbrain-doctor` → `Result=success`
- watchdog перезапущен → STATUS `healthy`
- тесты: `uv run pytest` → 257 passed
### Откаты
- `docs/rollback/B-01/undo.sh` (B-01+B-02), `docs/rollback/B-03/undo.sh`; не применялись
- rebase на `origin/main` отменён (`git rebase --abort`): переигрывал 18 коммитов форка поверх чужого upstream
### Не сделано
- B-04: отправка `main` в ремоут `fork` — сторож отбил (push в default-ветку), ждёт владельца. Платежей нет.
### Требует решения
- Отправить `main` в ремоут `fork` (рекомендую): fast-forward, 27 коммитов; готовая команда — в docs/OWNER-ACTIONS.md.
- Критерий A-04 → `fork/main..HEAD` = 0 (рекомендую): `origin` — чужой smixs, текущий критерий недостижим без отправки туда. Альтернатива «отправить в smixs» — чужая инфраструктура, не рекомендую.
- Черновик A-06 (тревога по `NRestarts`) и A-07 (проверка Whisper) — утвердить «да» / правки.
- B-03 сделан перезапуском мозга, а не очисткой строки: клавишная очистка рискует выходом из Claude Code (`C-c`) или меню отката (`Esc Esc`). Цена — теряется контекст разговора панели.
### Где мы
ACCEPTANCE 4/5 [x]; остался A-04 (за владельцем). Гейт готовности (docs/PROD-READINESS.md): ✓ тесты, мониторинг; остальное ☐.
push: не удался (fatal: unable to access 'https://github.com/smixs/agent-second-brain.git/': The requested URL returned error: 403)
### Нужно от вас — сейчас
- Отправить `main` в ремоут `fork` — готовая команда в docs/OWNER-ACTIONS.md (B-04).
### Нужно от вас — можно на самый конец
- Критерий A-04 → `fork/main..HEAD` = 0: «да, fork» / правки.
- Черновик A-06, A-07: «да» / правки.
### Что агент ещё сделает до прода
- После «да» на черновик: A-06 (тревога doctor по `NRestarts`), A-07 (`check_whisper`).
- После отправки `main` в `fork`: закрыть B-04 проверкой `fork/main..HEAD` = 0.
### Штурм
6 идей, в черновик 2 (A-06, A-07), остальные в бэклог — docs/IDEAS.md
### Лимит
неделя: 17.0% сейчас (на старте 16.0%).
### Для покупателя изменилось
Бот снова отвечает: вопрос в Telegram доходит до мозга и получает ответ (раньше висел в поле ввода); бот больше не ляжет на дни после серии падений.

Портал: НЕ ПУБЛИКОВАНО — страницы нет, сборка: st(s) -> projects.json
Built 348 project(s) -> /home/alexey-zhuykov/cyberdub-ai-infrastructure/iq-portal/dist
Deployed -> /srv/data/iq-landings/portal (pages: new only; index.html + assets: refreshed)

## Цикл 2 — 25.09.2026

### Сделано
- B-06 (A-06): NRestarts в doctor (check_restarts), pytest 261 passed, dbrain-doctor Result=success; коммит 20e2869
- B-07 (A-07): check_whisper через боевой WhisperTranscriber (тишина WAV), dbrain-doctor Result=success ok=True; коммит 20e2869

### Цель
Прод-готовность по docs/ACCEPTANCE.md: пункты цикла 2 (A-06, A-07).

### Задеплоено и как проверено
- doctor (код подхватывается при каждом прогоне таймера): `systemctl --user start dbrain-doctor` → `Result=success`, `doctor: ok=True`, Whisper ответил через боевой `WhisperTranscriber`; `uv run pytest` → 261 passed; `ruff` чисто.

### Откаты
- Код doctor: `git revert 20e2869`. Файл `~/.dbrain/doctor-nrestarts` — база счётчика, удаление безопасно.

### Не сделано
- B-04 (A-04): отправка `main` в ремоут `fork` отбита сторожем — за владельцем.

### Требует решения
- Отправка `main` в `fork` (команда — в OWNER-ACTIONS).
- Критерий A-04 → `fork/main..HEAD` = 0.
- Утвердить черновик A-08…A-11.

### Где мы
ACCEPTANCE 6/11 [x] (4 новых пункта — черновик), гейт готовности 2/10 ✓.
push: не удался (fatal: unable to access 'https://github.com/smixs/agent-second-brain.git/': The requested URL returned error: 403)

### Нужно от вас — сейчас
- **Отправить `main` в `fork`** — команда в `docs/OWNER-ACTIONS.md` (fast-forward; личных заметок в коммитах нет — проверено по диффу `fork/main..HEAD`).

### Нужно от вас — можно на самый конец
- **Критерий A-04**: заменить на `fork/main..HEAD` = 0 — «да, fork» / правки.
- **Черновик A-08…A-11** — «да» / правки.

### Что агент ещё сделает до прода
- A-08…A-11 после утверждения; гейт: безопасность, бэкапы, юр. страницы, скорость, деплой и откат.

### Штурм
- `process.sh` коммитит только vault и не отправляет в `origin` · безопасность · S · **в черновик** · к проду: гейт «безопасность»
- Ежедневный снимок vault + `check_backup` в doctor · надёжность · M · **в черновик** · к проду: гейт «бэкапы»
- README.ru.md: локальный Whisper вместо Deepgram · юр./доверие · S · **в черновик** · к проду: гейт «юр. страницы»
- `WHISPER_TIMEOUT` = 300 с · скорость · S · **в черновик** · к проду: гейт «скорость»
- SEO и дизайн — «н/п» для Telegram-бота · поддержка · S · в бэклог · решение владельца
- Прогрев Whisper в healthcheck · скорость · S · в бэклог · к проду: нет

### Лимит
неделя: 18.0% сейчас (на старте 17.0%).

### Для покупателя изменилось
Утренний осмотр теперь сообщает, если бот уходит в цикл перезапусков и если перестало работать распознавание голоса.

## Цикл 3 — 25.09.2026

### Сделано
- B-09 (A-09): снимок vault в ~/.dbrain/backups из process.sh до обработки, ротация 14 дн; doctor check_backup (26 ч); dbrain-doctor Result=success; 0594f44
- B-10 (A-10): README.ru: 5× Whisper, 0× Deepgram; уточнено, что прочитанное агентом из vault уходит в Anthropic; коммит README
- B-11 (A-11): WHISPER_TIMEOUT=300 в transcription.py, тест; бот перезапущен 20:09:25 active; 870bba7
- B-08 (A-08): git add/commit только -- vault, push удалён; тест test_process_git_scope; e9717d8
### Цель
Прод-готовность по docs/ACCEPTANCE.md: ночной контур не трогает код и чужой upstream, заметки бэкапятся, голос не падает на холодной модели, README не врёт о приватности.
### Задеплоено и как проверено
- тесты: `uv run pytest` → 268 passed; `ruff check` по изменённым файлам → чисто
- B-08: песочница — staged `code.py` вне vault в коммит `-- vault` не попал; повторный пустой коммит ловит `|| true`
- B-09: первый снимок `~/.dbrain/backups/vault-2026-09-25.tgz`; `systemctl --user start dbrain-doctor` → `Result=success`; восстановление `tar -xzf` + `diff -rq` → пусто (175 файлов)
- B-11: бот перезапущен под `deploy-net` → `active` с 20:09:25, polling и cron runner стартовали
### Откаты
- `docs/autopilot/undo-B-11.sh` (`git revert 870bba7` + рестарт бота); не применялся. B-08/B-09/B-10 — `git revert` своего коммита.
### Не сделано
- B-04: отправка `main` в `fork` — по-прежнему за владельцем (сторож отбивает push), теперь 40 коммитов.
### Требует решения
- Отправить `main` в ремоут `fork` (рекомендую): fast-forward, готовая команда — docs/OWNER-ACTIONS.md.
- Черновик A-12 (инструкция выкатки и отката + прогон отката) и A-13 (`PRIVACY.ru.md`) — «да» / правки.
### Где мы
ACCEPTANCE 10/11 [x]; остался A-04 (за владельцем). Гейт готовности 3/10 ✓: тесты, мониторинг, бэкапы.
push: не удался (fatal: unable to access 'https://github.com/smixs/agent-second-brain.git/': The requested URL returned error: 403)
### Нужно от вас — сейчас
- Отправить `main` в ремоут `fork` — команда в docs/OWNER-ACTIONS.md (B-04).
### Нужно от вас — можно на самый конец
- Черновик A-12, A-13: «да» / правки.
### Что агент ещё сделает до прода
- После «да»: A-12 (`docs/DEPLOY.md` + прогон отката на боте), A-13 (`PRIVACY.ru.md`).
- После отправки `main` в `fork`: закрыть B-04 и отметить гейт «функционал по ACCEPTANCE».
### Штурм
5 идей, в черновик 2 (A-12, A-13), остальные в бэклог — docs/IDEAS.md
### Лимит
неделя: 19.0% сейчас (на старте 19.0%).
### Для покупателя изменилось
Заметки теперь каждую ночь сохраняются в архив, и утренний осмотр предупредит, если архив устарел. Голосовые не теряются, пока модель распознавания просыпается. Ночная обработка больше не уносит чужой код в коммиты. README честно пишет, куда уходят данные.

## Цикл 4 — 25.09.2026

### Сделано
- B-13 (A-13): PRIVACY.ru.md (6c862e3): Telegram, Anthropic, локальный Whisper, git-push /process в форк (goals/, about.md), снимки ~/.dbrain/backups 14 дн, удаление; ссылка из README.ru.md. grep Anthropic=3, grep PRIVACY.ru.md в README=1
- B-12 (A-12): DEPLOY.md (9495341); прогон на живом боте: учебный 958c0f8 → restart → git revert (7f41717) → restart → ActiveState=active SubState=running NRestarts=0, Traceback 0, polling @cyberdub_second_brain_bot; doctor Result=success; brain-сессию не убивали — doc-only коммит
