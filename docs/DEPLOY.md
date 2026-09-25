# Выкатка и откат бота

Бот — user-юнит `dbrain-bot` (systemd), код берётся прямо из рабочего дерева
`~/stack/agent-second-brain`. Выкатка = новый коммит в дереве + рестарт юнита,
откат = `git revert` этого коммита + рестарт юнита.

## Выкатка

```bash
cd ~/stack/agent-second-brain
git pull fork main                      # или слияние upstream: git pull origin main
uv sync                                 # зависимости
uv run pytest -q                        # гейт: 0 failed
git rev-parse --short HEAD              # запомнить, что выкатываем

# юнит менялся (deploy/dbrain-bot.service) — установить его
cp deploy/dbrain-bot.service ~/.config/systemd/user/ && systemctl --user daemon-reload

# код менялся — сбросить Claude-сессию, иначе она живёт со старым контекстом
tmux kill-session -t "$(cat ~/.dbrain/brain.name)"
systemctl --user restart dbrain-bot
```

## Проверка после выкатки и после отката

```bash
systemctl --user show dbrain-bot -p ActiveState -p NRestarts   # ActiveState=active, NRestarts не растёт
journalctl --user -u dbrain-bot -n 30 --no-pager                # без Traceback
systemctl --user start dbrain-doctor && systemctl --user show dbrain-doctor -p Result   # Result=success
```

И живым путём: сообщение боту в Telegram → ответ.

## Откат

Откат — всегда новым коммитом `git revert`, историю не переписывать (`reset --hard` и
force-push запрещены: `main` опубликован в `fork`).

```bash
cd ~/stack/agent-second-brain
git log --oneline -10                   # найти плохой коммит <sha>
git revert --no-edit <sha>              # merge-коммит: git revert -m 1 --no-edit <sha>
uv sync                                 # если откат затронул pyproject.toml / uv.lock
# если откат вернул deploy/dbrain-bot.service — снова cp + daemon-reload, как при выкатке
tmux kill-session -t "$(cat ~/.dbrain/brain.name)"
systemctl --user restart dbrain-bot
```

Затем — «Проверка» выше. Готовые скрипты отката отдельных пунктов лежат в `docs/rollback/<пункт>/undo.sh`.

## Прогон отката на живом боте

2026-09-25, пункт B-12: учебный коммит → рестарт → `git revert` → рестарт → проверка.
Результат — в `docs/AUTOPILOT-REPORT.md`, цикл 4.
