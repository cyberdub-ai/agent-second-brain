#!/bin/sh
# откат B-03 (2026-09-25): убрать детектор stuck_input (коммит 5b6248d)
set -e
cd "$(dirname "$0")/../../.."
git revert --no-edit 5b6248d
systemctl --user restart dbrain-watchdog
