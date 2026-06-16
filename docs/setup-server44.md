# Установка на сервер 44 (RU ISP, Docker/systemd host)

> Это руководство специфично для нашего сервера: 192.168.2.44, РФ-провайдер (DPI/ТСПУ),
> WireGuard VPN → LA, Privoxy :8118, faster-whisper endpoint :8000.
> Для чистого VPS без ограничений читай [upstream docs](../README.md).

## Предварительные условия

- Python 3.12, `uv` установлен (`~/.local/bin/uv`)
- Claude Code CLI в `~/bin/claude` с активной Max-подпиской
- WireGuard (wg0) + Privoxy :8118 работают (`systemctl is-active privoxy` → active)
- SSH SOCKS5 proxy :1080 активен (для tmux-сессии — не нужен, для проверок)
- faster-whisper OpenAI-compatible endpoint на :8000 запущен
- Syncthing синхронизирует `/srv/data/second-brain/vault/` с Obsidian

## Шаг 1. Клонировать форк

```bash
git clone https://github.com/cyberdub-ai/agent-second-brain.git ~/stack/agent-second-brain
cd ~/stack/agent-second-brain
uv sync
```

## Шаг 2. Создать vault и заполнить brain-skills

```bash
mkdir -p /srv/data/second-brain/vault
cp -r vault/.claude/ /srv/data/second-brain/vault/.claude/
```

Структура skills в vault `.claude/`:
- `skills/` — autograph, dbrain-processor, cron
- `agents/` — brain persona
- `rules/` — brain-specific правила

## Шаг 3. Создать .env

```bash
cat > ~/stack/agent-second-brain/.env <<'EOF'
TELEGRAM_BOT_TOKEN=<токен из /srv/secrets/second-brain.env>
WHISPER_URL=http://127.0.0.1:8000
TELEGRAM_PROXY=http://127.0.0.1:8118
VAULT_PATH=/srv/data/second-brain/vault
ALLOWED_USER_IDS=[6515956507]
TZ=Europe/Moscow
CLAUDE_MODEL=sonnet
CRON_ENABLED=true
BRAIN_ROOT=/home/alexey-zhuykov/stack/agent-second-brain
EOF
chmod 600 ~/stack/agent-second-brain/.env
```

**Токен взять из:** `grep TELEGRAM_BOT_TOKEN /srv/secrets/second-brain.env`

## Шаг 4. Изолированный Claude config

```bash
mkdir -p ~/.dbrain-claude

# Скопировать credentials от Max-подписки
cp ~/.claude/.credentials.json ~/.dbrain-claude/

# Флаги онбординга
cat > ~/.dbrain-claude/.claude.json <<'EOF'
{"hasCompletedOnboarding": true, "theme": "dark", "autoUpdates": false, "mcpServers": {}, "projects": {}}
EOF

# Разрешить --dangerously-skip-permissions без интерактивного подтверждения
cat > ~/.dbrain-claude/settings.json <<'EOF'
{"skipDangerousModePermissionPrompt": true}
EOF
```

> **Критично:** `CLAUDE_CONFIG_DIR=~/.dbrain-claude` изолирует мозг от твоих
> operator-hooks и skills. Без изоляции любой hook вроде `validate-idea` заблокирует
> tmux-панель навсегда при слове «идея» → «❌ Ошибка сессии» на каждый запрос.

## Шаг 5. Установить systemd units

Скрипт `deploy/upgrade.sh` вшивает `WorkingDirectory=%h/projects/dbrain`, но мы
держим код в `~/stack/agent-second-brain`. Устанавливаем вручную:

```bash
PROJ="$HOME/stack/agent-second-brain"
for svc in dbrain-bot dbrain-watchdog dbrain-doctor dbrain-process dbrain-notify@; do
    sed "s|%h/projects/dbrain|$PROJ|g; s|%h|$HOME|g" \
        "$PROJ/deploy/${svc%%@*}.service" \
        > "$HOME/.config/systemd/user/${svc}.service" 2>/dev/null || true
done
cp "$PROJ/deploy/dbrain-process.timer" ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now dbrain-bot.service dbrain-watchdog.service dbrain-process.timer dbrain-doctor.timer
```

Или просто:

```bash
cd ~/stack/agent-second-brain
bash deploy/upgrade.sh
```

(`upgrade.sh` подставляет `$PROJECT_DIR` через sed и перезапускает сервисы)

## Шаг 6. Проверить

```bash
# Все сервисы должны быть active
dbrain status

# Claude-сессия должна ответить
tmux attach -t "$(cat ~/.dbrain/brain.name)"
# Видишь prompt Claude Code → Ctrl+B, D (отсоединиться)

# Бот должен ответить в Telegram
# Отправь любое сообщение @cyberdub_second_brain_bot
```

## Обновление кода

```bash
cd ~/stack/agent-second-brain
git pull fork main          # наши изменения
# или
git pull origin main        # upstream smixs
uv sync                     # обновить зависимости

# Перезапустить с полным сбросом сессии (обязательно при изменениях кода!)
tmux kill-session -t "$(cat ~/.dbrain/brain.name)"
systemctl --user restart dbrain-bot.service
```

## Восстановление после сбоя

```bash
# Туннель упал (proxy 8118 не работает)
sudo systemctl restart ssh-proxy-vps.service

# Watchdog завис
systemctl --user restart dbrain-watchdog.service

# Claude-сессия не отвечает дольше 5 минут
tmux kill-session -t "$(cat ~/.dbrain/brain.name)"
systemctl --user restart dbrain-bot.service

# Проверить логи
dbrain logs
journalctl --user -u dbrain-watchdog.service -n 50
```

## Файловая структура runtime

```
~/.dbrain/
  brain.name          ← имя tmux-сессии (генерируется при первом старте)
  brain.lock          ← PID-lock активной сессии
  pane.log            ← вывод tmux-панели (ротируется)
  ready               ← флаг готовности Claude
  cron/               ← cron state: jobs.json + логи

~/.dbrain-claude/
  .credentials.json   ← Claude Max auth (обновлять при ротации!)
  .claude.json        ← hasCompletedOnboarding + тема
  settings.json       ← skipDangerousModePermissionPrompt

/srv/data/second-brain/vault/
  .claude/            ← brain skills/persona (не трогать без необходимости)
  daily/              ← дневники (YYYY-MM-DD.md)
  thoughts/           ← отдельные мысли
  attachments/        ← медиафайлы
```
