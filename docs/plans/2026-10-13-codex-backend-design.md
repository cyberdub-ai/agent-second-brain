# Dbrain – подготовка backend Codex

Прямое разрешение владельца: codex-harness rollout01a134bf:295, подготовить изолированный патч и проверки; live отдельно. Работающий сервис, units, сеть, auth, vault и исходный checkout не меняются.

## Выбор реализации

[РАЗВИЛКА] Рекомендуется штатный `codex exec --json` с продолжением точного thread через `exec resume`. Этот режим документирован для автоматизации; stdin передаёт prompt, JSONL отделяет reply от вывода инструментов, `turn.completed` подтверждает завершение. CLI использует установленную авторизацию; запросов API по ключу и новых зависимостей не добавляем. Перед live отдельно проверить подписочную авторизацию и фактическую версию CLI.

Альтернативы: разбор TUI Codex оставляет хрупкие маркеры и риск чужой tmux-сессии; app-server даёт steering/events, но намного шире по контракту и официальная документация предупреждает об experimental production status. Для ограниченного перехода выбираем exec. Оригинальный backend остаётся доступным для точного rollback; Codex включается только явным BRAIN_BACKEND=codex, production environment не меняется.

## Контракт и сохранность

Новый CodexSession возвращает существующий AskResult и предоставляет методы health/control, которые ожидают bot/cron/watchdog. Два runtime: основной и cron сохраняются раздельно. Межпроцессная блокировка serializes ask; файловый журнал owner-only хранит thread и inflight до запуска, а после запуска – неизвестный исход до принятого terminal event. После timeout, обрыва, malformed stream или смерти родителя unknown сохраняется и исключает автоматический replay. Ни watchdog, ни clear/recover не снимают такой marker. Реальный неизвестный исход требует отдельного recover после проверки истории, не нового prompt.

Запускается и останавливается только собственный subprocess; tmux-команд и смены чужой панели нет. Thread ID берётся из структурированного события, точный ID сохраняется; resume не использует --last. Ответ принимается только из agent_message и при успешном terminal event/exit, вывод command/mcp не становится ответом. Persona читается из имеющегося brain-system.md и передаётся stdin; private prompt/output не записываются в новые публичные логи.

Подписочный login-method фиксируется chatgpt, API-key env исключён из child environment. Сеть и настройки proxy не изменяются; используется установленный wrapper. Права vault для будущего Codex backend – workspace-write без новых путей; live-план должен отдельно подтвердить совместимость с необходимыми файлами и MCP, они не копируются из Claude автоматически.

В exec нет mid-turn steering: новые обычные сообщения ждут текущий async ask-lock; /stop прекращает только свой child и оставляет unknown. /clear сбрасывает только принятый idle Codex thread, vault и историю не удаляет. Неизвестный исход отображается явно вместо совета повторить. Cron unknown отключает точное задание и сохраняет запись до review; повторный запуск работы из неопределённости запрещён.

## Проверки и отдельная live-граница

Fake subprocess fixtures проверяют thread/start/resume, reply/terminal correlation, malformed/error/timeout, отсутствие replay после рестарта, parallel lock, marker permissions, safe watchdog, clear и очередь chat/cron. Полная существующая suite и ruff обязательны; тесты не вызывают Codex inference, Telegram, vault или service. Live Codex качества/авторизации/steering и работа Telegram этим не доказаны.

После проверки – отдельная ветка/PR в fork cyberdub-ai/agent-second-brain, reviewable diff и план только dbrain-bot/dbrain-watchdog: idle/inflight inventory → lock/backup → остановка exact owned units по отдельному согласию → применение accepted commit и явного backend → health без Telegram send → проверка нового thread/absence Claude/queue → rollback при неуспехе. Существующие vault/история/jobs/секреты и network неизменны. Установленные units, scheduler и код production не трогаем на этапе подготовки.

Официальные источники: https://developers.openai.com/codex/noninteractive ; https://developers.openai.com/codex/app-server . Схему и flags сверяем с установленным CLI, а не только документацией.
