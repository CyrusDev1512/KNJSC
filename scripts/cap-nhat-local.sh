#!/usr/bin/env bash
# Cập nhật bản chạy thử trên máy cá nhân — một lệnh, chạy lại bao nhiêu lần
# cũng được:
#
#   ./scripts/cap-nhat-local.sh            # kéo nhánh hiện tại
#   ./scripts/cap-nhat-local.sh <nhánh>    # chuyển sang nhánh khác rồi kéo
#
# Việc nó làm: kéo mã mới → dựng lại và bật docker compose → bảo đảm có dữ
# liệu mẫu (lệnh du_lieu_mau chạy lại nhiều lần được, không phá dữ liệu cũ).
# Điều kiện duy nhất: Docker đang chạy.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! docker info >/dev/null 2>&1; then
  echo "Docker chưa chạy — mở Docker Desktop rồi chạy lại lệnh này." >&2
  exit 1
fi

if [ $# -ge 1 ]; then
  git fetch origin
  git checkout "$1"
fi
git pull

docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml exec web python manage.py du_lieu_mau

echo
echo "Xong — mở http://localhost:8020 (hệ thống) và http://localhost:8021/bang-tinh/ (Bảng tính, vận đơn)"
