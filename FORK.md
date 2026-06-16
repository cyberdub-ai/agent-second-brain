# Fork: cyberdub-ai customisations

This is a fork of [smixs/agent-second-brain](https://github.com/smixs/agent-second-brain)
running on **server 44** (192.168.2.44, RU ISP) as a personal always-on Telegram agent.

## What changed vs upstream

### 1. Deepgram → local Whisper (`transcription.py`)

Upstream ships a Deepgram cloud transcriber. This fork replaces it with a
local [faster-whisper](https://github.com/SYSTRAN/faster-whisper) server
(OpenAI-compatible endpoint at `WHISPER_URL=http://127.0.0.1:8000`).

- No per-minute Deepgram bill.
- Audio never leaves the host.
- Model: `Systran/faster-whisper-large-v3`, language `ru` hardcoded (change in `transcription.py` if needed).

### 2. `brain_root` config field (`config.py`, `runtime.py`)

Upstream assumes the vault lives inside the project directory.  
On this deployment code is in `~/stack/agent-second-brain` and the vault is in
`/srv/data/second-brain/vault` — they are on different paths.

`BRAIN_ROOT` env var (or `brain_root` in `.env`) points to the directory that
holds `deploy/brain-system.md` and `mcp-config.json`.  
Default is `vault.parent`, so upstream deployments are unaffected.

### 3. Telegram proxy (`config.py`, `bot/main.py`)

`api.telegram.org` is blocked by the Russian ISP via DPI/ТСПУ.  
`TELEGRAM_PROXY=http://127.0.0.1:8118` wires aiogram through Privoxy → WireGuard → US VPS.  
Set to empty string to disable (non-RU deployments).

Requires `aiohttp-socks` (added to `pyproject.toml`) because aiogram's
`AiohttpSession` imports it even for plain HTTP proxies.

### 4. CLAUDE_CONFIG_DIR isolation (`claude_session.py`, systemd units)

`CLAUDE_CONFIG_DIR=~/.dbrain-claude` keeps the brain's Claude session completely
separate from the operator's own `~/.claude`.

**Why this matters:** if the brain inherits the operator's config, any installed
Claude Code skill that auto-fires on keywords (e.g. `validate-idea` on "идея")
will call `AskUserQuestion`, blocking the tmux pane forever and causing every
bot request to time out at 4 minutes with "❌ Ошибка сессии".

`~/.dbrain-claude` contains only:
- `.credentials.json` — Max subscription auth
- `.claude.json` — `hasCompletedOnboarding: true` (skip theme picker)
- `settings.json` — `skipDangerousModePermissionPrompt: true`

The brain's own skills, persona, and rules live in `vault/.claude/`.

Because `tmux new-session` inherits the tmux **server** environment (set when
the server first started, before the systemd units ran), `_start_command` in
`claude_session.py` inlines all critical env vars directly into the shell
command string. `tmux kill-server` would destroy the operator's other sessions.

### 5. Systemd `KillMode=process` (deploy units)

`KillMode=process` ensures that stopping or restarting the bot does **not** kill
the detached tmux brain session living in the same cgroup. The brain outlives
bot restarts; `ensure_session` re-attaches on next start.

To apply a code/config change you **must** kill the brain session first:

```bash
tmux kill-session -t "$(cat ~/.dbrain/brain.name)"
systemctl --user restart dbrain-bot.service
```

## Deployment layout

```
~/stack/agent-second-brain/   ← code (git, this fork)
  .env                         ← local overrides (not committed)
  deploy/                      ← systemd units

/srv/data/second-brain/vault/ ← Obsidian vault (Syncthing-synced)
  .claude/                     ← brain's own skills/persona/rules
  daily/                       ← daily notes
  thoughts/                    ← captured thoughts
  attachments/                 ← voice note transcripts

~/.dbrain-claude/             ← isolated Claude config dir
  .credentials.json
  .claude.json
  settings.json

~/.dbrain/                    ← runtime state (locks, pane.log, flags)
  brain.name                  ← tmux session name

/srv/secrets/second-brain.env ← TELEGRAM_BOT_TOKEN (never in git)
```

## Key env vars

| Variable | Value | Purpose |
|---|---|---|
| `CLAUDE_CONFIG_DIR` | `~/.dbrain-claude` | Isolated Claude config |
| `HTTPS_PROXY` / `HTTP_PROXY` | `http://127.0.0.1:8118` | Privoxy → WireGuard → US for api.anthropic.com |
| `NO_PROXY` | `127.0.0.1,localhost,::1,192.168.2.44` | Keep local Whisper off proxy |
| `NODE_EXTRA_CA_CERTS` | `/opt/mhr-cfw/ca/ca.crt` | mhr-cfw failover TLS trust |
| `TELEGRAM_PROXY` | `http://127.0.0.1:8118` | aiogram proxy for api.telegram.org |
| `WHISPER_URL` | `http://127.0.0.1:8000` | Local faster-whisper endpoint |
| `VAULT_PATH` | `/srv/data/second-brain/vault` | Obsidian vault |
| `BRAIN_ROOT` | `~/stack/agent-second-brain` | Dir with deploy/brain-system.md |
| `ALLOWED_USER_IDS` | `[6515956507]` | Your Telegram user ID |
| `CLAUDE_MODEL` | `sonnet` | Saves Opus budget for heavier work |

## Management

```bash
dbrain status          # systemctl --user status dbrain-*.service dbrain-*.timer
dbrain logs            # journalctl --user -u dbrain-bot.service -f
dbrain attach          # tmux attach -t $(cat ~/.dbrain/brain.name)
dbrain doctor          # run the self-diagnostic manually
```
