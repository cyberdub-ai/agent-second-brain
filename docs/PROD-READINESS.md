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
| юр. страницы | ☐ | |
| деплой и откат | ☐ | |
