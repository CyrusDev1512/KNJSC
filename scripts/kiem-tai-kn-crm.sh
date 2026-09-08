#!/usr/bin/env bash
# Kiểm tải KN CRM trên máy này — AC-10.8, docs/06 tầng 9. Một lệnh, chạy lại được:
#
#   ./scripts/kiem-tai-kn-crm.sh                 # nạp 100 nghìn dòng, đo đơn lẻ, 100 người 5 phút
#   ./scripts/kiem-tai-kn-crm.sh --giu-du-lieu   # đã nạp rồi thì đo luôn, không nạp lại
#   ./scripts/kiem-tai-kn-crm.sh --nhanh         # 100 người 1 phút, bỏ bước tính lại 100 nghìn dòng
#
# Việc nó làm: bật lại hai container web (KN ERP) và bangtinh (KN CRM) ở chế độ
# **gunicorn 3 worker** (như máy chủ thật, không đo trên runserver) → seed_perf
# 100 nghìn dòng vận đơn + bảng Sale 20 nghìn dòng có cột tính sẵn → do_hieu_nang
# (một người, không tải) → Locust 100 người → in ĐẠT / KHÔNG ĐẠT → trả container
# về runserver. Báo cáo ở storage/perf/<ngày>-*.md. Dữ liệu giả mang mã PERF-*,
# xoá bằng `manage.py seed_perf --xoa-cu`.
set -uo pipefail
cd "$(dirname "$0")/.."
COMPOSE="docker compose -f deploy/docker-compose.yml"
GUNICORN="gunicorn knjsc.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 4 --worker-class gthread --keep-alive 5"
NAP=1; THOI_LUONG=5m; BO_LON=""
for t in "$@"; do
  case "$t" in
    --giu-du-lieu) NAP=0 ;;
    --nhanh) THOI_LUONG=1m; BO_LON="--bo-tinh-lai-lon" ;;
  esac
done

if ! docker info >/dev/null 2>&1; then
  echo "Docker chưa chạy — nháy đúp 'KN JSC.bat' (hoặc ./scripts/cap-nhat-local.sh) trước rồi chạy lại." >&2
  exit 1
fi

echo "== 1/5 Bật KN ERP và KN CRM ở chế độ gunicorn (3 tiến trình × 4 luồng, như Dockerfile) =="
KNJSC_LENH_WEB="$GUNICORN" $COMPOSE up -d --force-recreate web bangtinh
i=0
until curl -s -o /dev/null http://127.0.0.1:8021/dang-nhap/ 2>/dev/null; do
  i=$((i + 1)); [ "$i" -gt 60 ] && { echo "KN CRM không lên sau 2 phút: $COMPOSE logs bangtinh --tail 50" >&2; exit 1; }
  sleep 2
done
$COMPOSE exec -T bangtinh python manage.py migrate --noinput >/dev/null
$COMPOSE exec -T bangtinh python manage.py du_lieu_mau >/dev/null

if [ "$NAP" = 1 ]; then
  echo "== 2/5 Nạp dữ liệu: 100.000 dòng vận đơn (24 tháng, đủ 30 cột) + bảng Sale 20.000 dòng =="
  $COMPOSE exec -T bangtinh python manage.py seed_perf --xoa-cu --so-dong 100000 --so-thang 24 --dien-day --bang-sale
else
  echo "== 2/5 Giữ dữ liệu đã nạp =="
fi

echo "== 3/5 Đo đơn lẻ (một người, không tải) =="
$COMPOSE exec -T bangtinh python manage.py do_hieu_nang --giai-thich $BO_LON

echo "== 4/5 Locust 100 người trong $THOI_LUONG =="
$COMPOSE exec -T -e ERP_HOST=http://web:8000 -e KNJSC_PERF_DIR=/storage/perf bangtinh \
  locust -f tests/perf/locustfile_kn_crm.py --host http://localhost:8000 \
         --users 100 --spawn-rate 10 --run-time "$THOI_LUONG" --headless --only-summary --reset-stats
KQ=$?

echo "== 5/5 Trả container về chế độ runserver =="
$COMPOSE up -d --force-recreate web bangtinh >/dev/null

echo
if [ "$KQ" = 0 ]; then echo "KẾT QUẢ: ĐẠT"; else echo "KẾT QUẢ: KHÔNG ĐẠT (xem từng dòng ở trên)"; fi
echo "Báo cáo: storage/perf/$(date +%Y-%m-%d)-don-le.md và storage/perf/$(date +%Y-%m-%d)-tai-100.md"
exit "$KQ"
