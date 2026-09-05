#!/bin/sh
# Chờ cơ sở dữ liệu sẵn sàng rồi mới chạy. Không chạy chuyển đổi cấu trúc
# tự động trên máy chủ — việc đó phải do người vận hành bấm.
set -e

if [ "${WAIT_FOR_DB:-1}" = "1" ]; then
  echo "Cho co so du lieu tai ${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432} ..."
  for i in $(seq 1 60); do
    if python -c "
import socket, sys, os
s = socket.socket()
s.settimeout(1)
try:
    s.connect((os.environ.get('POSTGRES_HOST','db'), int(os.environ.get('POSTGRES_PORT','5432'))))
except Exception:
    sys.exit(1)
" 2>/dev/null; then
      echo "Co so du lieu san sang."
      break
    fi
    sleep 1
  done
fi

# Thư mục tệp (tải lên, xuất, sao lưu) phải ghi được, không thì nhập tệp và
# sao lưu hỏng ngay lần đầu mà không ai biết vì sao. Chỉ cảnh báo, không dừng:
# dịch vụ vẫn lên được để người vận hành sửa quyền — backlog K21.
KHO="${STORAGE_DIR:-/storage}"
for tm in "$KHO" "$KHO/uploads" "$KHO/exports" "$KHO/backups"; do
  mkdir -p "$tm" 2>/dev/null || true
  if [ ! -w "$tm" ]; then
    echo "CANH BAO: khong ghi duoc vao $tm — nhap tep va sao luu se hong. Kiem quyen thu muc storage/ (uid 1000)." >&2
  fi
done

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  python manage.py migrate --noinput
  # Bảng vận đơn là bảng động (quyết định 001) nên migrate không sinh ra nó.
  # Máy sạch mà thiếu bảng này thì màn hình Bảng tính trả 404. Lệnh chạy
  # lại nhiều lần được, đã có thì chỉ bổ sung cột còn thiếu.
  python manage.py tao_bang_van_don
fi

exec "$@"
