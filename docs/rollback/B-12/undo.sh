#!/bin/sh
# откат B-12 (2026-09-25): учебный прогон трогал только docs/ и рестарт бота —
# вернуть бота в строй рестартом, docs/DEPLOY.md убрать revert своего коммита
set -e
systemctl --user restart dbrain-bot
systemctl --user show dbrain-bot -p ActiveState
