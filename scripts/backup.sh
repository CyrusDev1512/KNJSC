#!/usr/bin/env bash
# Sao lưu cơ sở dữ liệu ngay bây giờ. Tệp ra ở storage/backups/ (hoặc BACKUP_DIR).
#
#   ./scripts/backup.sh
#
# Tác vụ hằng đêm (service `beat`) làm đúng việc này lúc 02:00; script này
# để chạy tay trước khi nâng cấp hay khi cần một bản ngay.
set -euo pipefail
cd "$(dirname "$0")/.."

docker compose -f deploy/docker-compose.yml exec web python manage.py sao_luu
