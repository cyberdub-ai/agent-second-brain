# Подготовленный переход Dbrain на Codex

Статус: изолированный патч для review. Production, units, сеть, secrets, jobs, vault, история и рабочий checkout не изменены. Прямой источник владельца – codex-harness ownrollout01a134bf:295: подготовить патч и проверки, live отдельно.

## Что изменено

Явный BRAIN_BACKEND=codex выбирает новый CodexSession; default остаётся прежним и установка кода сама backend не переключает. Основной и cron имеют разные runtime/thread. Запуск использует установленный CLI wrapper, `codex exec --json`, stdin и точный `exec resume <UUID>`, без --last, tmux-инъекции, API-key auth или новых зависимостей. Persona остаётся существующим brain-system.md.

Codex backend записывает owner-only thread и inflight до запуска. Только agent_message + turn.completed + exit0 подтверждают ответ. В malformed stream, timeout, ошибке CLI или после смерти родителя исход остаётся unknown. Повторная ask, clear и watchdog не очищают marker и не запускают модель заново. Для ручной сверки сохраняется наблюдавшийся thread ID. Необходимая очистка uncertain marker в этот патч не включена: её можно делать только после доказанного внешнего результата, по отдельной точной операции.

Chat показывает неизвестный исход без автоматического retry. Обычный concurrent ввод exec backend ожидает ask-lock вместо неподдерживаемого mid-turn steering. /stop завершает только собственный child; /clear сохраняет vault/историю и работает только без pending outcome. /model не заявляется отправленным в exec. Cron при unknown отключает точное задание, сохраняет статус и не вызывает recovery/retry. Если работа завершилась, а доставка результата не подтверждена, Codex cron также требует review вместо повторного исполнения.

Новый subprocess имеет собственную process group. При timeout завершается и reaped только принадлежащий объекту child/group; чужие процессы и tmux не затрагиваются. Watchdog не создаёт CLI и не заменяет работающую панель.

## Проверки и их пределы

Offline fixtures и реальный локальный sleeping subprocess проверяют lifecycle без inference, Telegram или production. Установленный CLI отдельно принят через initialize/config/read с forced_login_method=chatgpt, approval_policy=never и default_permissions=:workspace; inference turns0. Первоначальное неверное имя profile :workspace-write выявлено этим smoke и исправлено. Официальные docs также требуют не смешивать profiles и старый sandbox_mode.

Полный ruff имеет пять уже существующих замечаний исходного checkout; новые замечания патча устраняются. Сравнение baseline/patch не утверждает полный lint PASS. Финальная полная suite: 306 passed in 4.97s, exit0. Ruff baseline5/patch5, новых замечаний0. git diff --check exit0. Native config/read PASS, inference0.

Подписочная авторизация и реальный ответ Codex не проверены: config/read проверяет конфигурацию, не entitlement/login или модель. Совместимость persona/старых .claude skills и Claude MCP-конфига требует отдельной приёмки. Claude MCP не импортируется автоматически; будущий Codex использует установленную Codex-конфигурацию. UI attach старого Claude не становится новым интерфейсом этого backend.

Очередь concurrent chat остаётся существующей in-process async-сериализацией, не новым durable Telegram inbox. Перезапуск bot с ещё ожидающими chat-coroutines требует проверки входящих update/ACK; по локальным тестам нельзя объявлять их доставленными. Принятие terminal event доказывает завершение Codex-хода, не получение ответа человеком. Pending legacy inflight блокирует переход до сверки, не стирается.

## Конкретный отдельный live-план

1. Владелец принимает точный commit/PR и отдельно разрешает переключение только dbrain-bot.service/dbrain-watchdog.service; сети, других units, аккаунтов и существующих данных это не касается. До live подтвердить владение исходниками и отсутствие параллельного writer.
2. Read-only проверить exact service PID/starttime, vault/runtime paths, main/cron inflight, текущий Claude request и очереди bot/cron. Unknown outcomes сначала выяснить, не replay. Проверить saved CLI auth типа ChatGPT без вывода значений и действующую модель/пермишены.
3. Под own dbrain lock сделать backup точных code/config references, runtime thread/inflight/jobs и unit definition. Старые данные и историю оставить на месте. Остановить только эти два exact units штатно после подтверждённого idle; старый Claude закрыть только по проверенной identity и отдельно принятой live-операции. Чужие tmux/session/processes не трогать.
4. Применить только accepted code c37608b и дизайн a2c4d37 в исходный checkout после проверки ownership; чужой .gitignore сохранить вне коммита. Для выбора backend использовать точные новые drop-in `/home/alexey-zhuykov/.config/systemd/user/dbrain-bot.service.d/codex.conf` и `/home/alexey-zhuykov/.config/systemd/user/dbrain-watchdog.service.d/codex.conf`: только BRAIN_BACKEND=codex и CODEX_BIN=/home/alexey-zhuykov/bin/codex. Existing WorkingDirectory/ExecStart не менять, так сохраняется существующее чтение .env и установленной .venv. CODEX_HOME/доступ выбрать по согласованному service scope, без новых ключей/расходов. Запустить exact units; проверить unit health, отсутствие нового Claude/двойного Codex, protected marker permissions, main/cron separation. Не отправлять Telegram canary без явного включения в live-разрешение.
5. Отдельный согласованный bounded real canary принимает JSONL terminal/thread и совместимость persona/tools в fixture vault; ответы Telegram и любые данные production проверять отдельно без дубликатов. Только после этого разрешать рабочую очередь.
6. При неуспехе остановить только свои новые units/child, сохранить receipt и unknown marker. Вернуть точные backup code/config, не удалять данные и не повторять старые prompts. Возврат старого кода не доказывает работоспособность заблокированного Claude; известное ограничение сохраняется. Освободить lease и документировать фактический итог.

Источники: [Codex non-interactive](https://developers.openai.com/codex/noninteractive), [Permissions](https://learn.chatgpt.com/docs/permissions#migrate-from-older-sandbox-settings). Дизайн: docs/plans/2026-10-13-codex-backend-design.md.
