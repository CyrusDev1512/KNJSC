#!/usr/bin/env bash
# Cập nhật bản chạy thử trên máy cá nhân — một lệnh, chạy lại bao nhiêu lần
# cũng được:
#
#   ./scripts/cap-nhat-local.sh            # kéo nhánh hiện tại
#   ./scripts/cap-nhat-local.sh <nhánh>    # chuyển sang nhánh khác rồi kéo
#
# Việc nó làm: bảo đảm Docker chạy (macOS tự mở Docker Desktop) → kéo mã mới →
# dựng lại sáu container → bảo đảm có dữ liệu mẫu (lệnh du_lieu_mau chạy lại
# nhiều lần được, không phá dữ liệu cũ). Bản Windows: cap-nhat-local.bat.
set -euo pipefail
cd "$(dirname "$0")/.."
COMPOSE="docker compose -f deploy/docker-compose.yml"

echo "[1/5] Kiểm Docker ..."
if ! docker info >/dev/null 2>&1; then
  if [ "$(uname)" = "Darwin" ] && open -a Docker 2>/dev/null; then
    echo "Docker chưa chạy — đang mở Docker Desktop, chờ tối đa 3 phút ..."
  else
    echo "Docker chưa chạy — mở Docker Desktop (hoặc: sudo systemctl start docker) rồi chạy lại." >&2
    exit 1
  fi
  for _ in $(seq 1 36); do
    sleep 5
    docker info >/dev/null 2>&1 && break
    printf .
  done
  echo
  docker info >/dev/null 2>&1 || { echo "Docker vẫn chưa sẵn sàng sau 3 phút." >&2; exit 1; }
fi
echo "Docker sẵn sàng."

echo "[2/5] Kéo mã mới ..."
if [ $# -ge 1 ]; then
  git fetch origin
  git checkout "$1"
fi
git pull --ff-only

echo "[3/5] Dựng lại container (lần đầu tải image, 5–10 phút) ..."
$COMPOSE up -d --build

echo "[4/5] Bảo đảm có dữ liệu mẫu ..."
$COMPOSE exec web python manage.py du_lieu_mau

echo "[5/5] Trạng thái sáu container:"
$COMPOSE ps

echo
echo "Xong — mở http://localhost:8020 (hệ thống) và http://localhost:8021/bang-tinh/ (Bảng tính, vận đơn)"
