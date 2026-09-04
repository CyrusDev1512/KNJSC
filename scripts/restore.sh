#!/usr/bin/env bash
# Phục hồi cơ sở dữ liệu từ bản sao lưu — ĐÈ LÊN dữ liệu hiện tại.
#
#   ./scripts/restore.sh                       # chỉ liệt kê các bản
#   ./scripts/restore.sh --toi-chac-chan       # phục hồi bản mới nhất
#   ./scripts/restore.sh knjsc-20260903-020000.dump --toi-chac-chan
#
# Dừng worker và beat trước để không có tác vụ nào ghi vào giữa chừng, rồi
# bật lại sau khi xong.
set -euo pipefail
cd "$(dirname "$0")/.."
COMPOSE="docker compose -f deploy/docker-compose.yml"

if printf '%s\n' "$@" | grep -qx -- '--toi-chac-chan'; then
  $COMPOSE stop worker beat bangtinh >/dev/null
  trap '$COMPOSE start worker beat bangtinh >/dev/null' EXIT
fi

$COMPOSE exec web python manage.py phuc_hoi "$@"
