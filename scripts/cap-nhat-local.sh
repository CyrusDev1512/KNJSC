#!/usr/bin/env bash
# Cập nhật và bật bản chạy thử trên máy cá nhân — một lệnh, chạy lại bao nhiêu
# lần cũng được:
#
#   ./scripts/cap-nhat-local.sh            # kéo nhánh hiện tại
#   ./scripts/cap-nhat-local.sh <nhánh>    # chuyển sang nhánh khác rồi kéo
#
# Việc nó làm: mở Docker nếu chưa chạy → kéo mã mới → dựng lại và bật docker
# compose → đợi web lên → bảo đảm có dữ liệu mẫu (lệnh du_lieu_mau chạy lại
# nhiều lần được, không phá dữ liệu cũ) → mở trình duyệt.
set -euo pipefail
cd "$(dirname "$0")/.."
COMPOSE="docker compose -f deploy/docker-compose.yml"
DIA_CHI="http://127.0.0.1:8020/"

if ! command -v docker >/dev/null 2>&1; then
  echo "Chưa cài Docker. Tải Docker Desktop tại https://www.docker.com/products/docker-desktop/" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker chưa chạy, đang mở ..."
  case "$(uname -s)" in
    Darwin) open -a Docker ;;
    Linux) command -v systemctl >/dev/null 2>&1 && sudo systemctl start docker || true ;;
  esac
  i=0
  until docker info >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -gt 90 ]; then
      echo "Đợi 3 phút mà Docker vẫn chưa lên. Mở Docker Desktop bằng tay rồi chạy lại." >&2
      exit 1
    fi
    sleep 2
  done
fi
echo "Docker đã sẵn sàng."

if [ $# -ge 1 ]; then
  git fetch origin
  git checkout "$1"
fi
git pull

$COMPOSE up -d --build

echo "Đợi web sẵn sàng tại $DIA_CHI ..."
i=0
until curl -s -o /dev/null "$DIA_CHI" 2>/dev/null; do
  i=$((i + 1))
  if [ "$i" -gt 60 ]; then
    echo "Web không lên sau 2 phút. Xem nhật ký bằng: $COMPOSE logs web --tail 50" >&2
    exit 1
  fi
  sleep 2
done

$COMPOSE exec -T web python manage.py du_lieu_mau

case "$(uname -s)" in
  Darwin) open "$DIA_CHI" ;;
  Linux) xdg-open "$DIA_CHI" >/dev/null 2>&1 || true ;;
esac
echo
echo "Xong — mở http://localhost:8020 (hệ thống) và http://localhost:8021/bang-tinh/ (Bảng tính, vận đơn)"
