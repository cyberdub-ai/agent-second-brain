#!/bin/sh
# откат B-01/B-02 (2026-09-25): вернуть paste без -p и старый StartLimit
set -e
D=$(cd "$(dirname "$0")" && pwd); P=$(cd "$D/../../.." && pwd)
cp "$D/claude_session.py" "$P/src/d_brain/services/claude_session.py"
cp "$D/dbrain-bot.service" "$P/deploy/dbrain-bot.service"
cp "$D/dbrain-bot.service" "$HOME/.config/systemd/user/dbrain-bot.service"
systemctl --user daemon-reload
systemctl --user restart dbrain-bot
