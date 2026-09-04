#!/bin/sh
# Bật hệ thống trên máy cá nhân bằng một lệnh (Mac và Linux).
# Windows dùng scripts/bat.cmd.
#
#   sh scripts/bat.sh
#
# Làm lần lượt: mở Docker nếu chưa chạy, dựng các container, đợi web sẵn
# sàng, nạp dữ liệu mẫu (12 tài khoản, chạy lại không sao), rồi mở trình
# duyệt ở http://127.0.0.1:8020/
set -e
cd "$(dirname "$0")/.."
COMPOSE="docker compose -f deploy/docker-compose.yml"
DIA_CHI="http://127.0.0.1:8020/"

if ! command -v docker >/dev/null 2>&1; then
  echo "Chua cai Docker. Tai Docker Desktop tai https://www.docker.com/products/docker-desktop/"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker chua chay, dang mo ..."
  case "$(uname -s)" in
    Darwin) open -a Docker ;;
    Linux)
      if command -v systemctl >/dev/null 2>&1; then
        sudo systemctl start docker || true
      fi ;;
  esac
  i=0
  until docker info >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -gt 90 ]; then
      echo "Doi 90 giay ma Docker van chua len. Mo Docker Desktop bang tay roi chay lai."
      exit 1
    fi
    sleep 2
  done
fi
echo "Docker da san sang."

echo "Dang dung cac container ..."
$COMPOSE up -d --build

echo "Doi web san sang tai $DIA_CHI ..."
i=0
until curl -s -o /dev/null "$DIA_CHI" 2>/dev/null; do
  i=$((i + 1))
  if [ "$i" -gt 60 ]; then
    echo "Web khong len sau 2 phut. Xem nhat ky bang:"
    echo "  $COMPOSE logs web --tail 50"
    exit 1
  fi
  sleep 2
done

echo "Nap du lieu mau ..."
$COMPOSE exec -T web python manage.py du_lieu_mau

echo "Mo trinh duyet ..."
case "$(uname -s)" in
  Darwin) open "$DIA_CHI" ;;
  Linux) xdg-open "$DIA_CHI" >/dev/null 2>&1 || echo "Mo tay: $DIA_CHI" ;;
esac
echo "Xong. Dang nhap tai $DIA_CHI"
