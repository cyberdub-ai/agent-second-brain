## Гейт готовности

| пункт | статус | как проверено |
|---|---|---|
| функционал по ACCEPTANCE | ☐ | |
| тесты | ✓ | `uv run pytest` → 257 passed, 2026-09-25 |
| SEO | ☐ | |
| дизайн | ☐ | |
| скорость | ☐ | |
| безопасность | ☐ | |
| мониторинг | ✓ | doctor `Result=success` + watchdog STATUS healthy, 2026-09-25 |
| бэкапы | ✓ | 2026-09-25: `process.sh` снимает `~/.dbrain/backups/vault-<дата>.tgz` до обработки, 14 дн; doctor `check_backup` ≤26 ч, `dbrain-doctor` Result=success; восстановление `tar -xzf` → `diff -rq` с vault пусто (175 файлов). Потолок: тот же диск |
| юр. страницы | ✓ | 2026-09-25: `PRIVACY.ru.md` (Telegram, Anthropic, локальный Whisper, git-ремоут, снимки, удаление) + ссылка из README.ru.md; `LICENSE` |
| деплой и откат | ✓ | 2026-09-25: `docs/DEPLOY.md`; откат прогнан на живом боте: 958c0f8 → restart → `git revert` 7f41717 → restart → `ActiveState=active`, NRestarts=0, doctor Result=success |
