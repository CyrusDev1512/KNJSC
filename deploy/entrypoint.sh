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

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  python manage.py migrate --noinput
fi

exec "$@"
