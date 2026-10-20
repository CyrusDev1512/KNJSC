# syntax=docker/dockerfile:1
FROM python:3.12-slim-trixie

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Giữ client cùng major với server PostgreSQL 16 trong Compose.
# Client 17 có thể dump server 16 nhưng dump chứa SET transaction_timeout,
# khiến phục hồi lại server 16 thất bại. Dùng kho PGDG có chữ ký, không lấy
# gói postgresql-client mặc định thay đổi theo phiên bản Debian.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates tzdata libpq5 \
    && python -c "import urllib.request; urllib.request.urlretrieve('https://www.postgresql.org/media/keys/ACCC4CF8.asc', '/usr/share/keyrings/postgresql.asc')" \
    && echo 'deb [signed-by=/usr/share/keyrings/postgresql.asc] https://apt.postgresql.org/pub/repos/apt trixie-pgdg main' > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client-16 \
    && rm -rf /var/lib/apt/lists/*

# Gọi đúng binary ngay cả khi image về sau có thêm client major khác.
ENV PATH="/usr/lib/postgresql/16/bin:${PATH}"
RUN pg_dump --version | grep -E '^pg_dump \(PostgreSQL\) 16\.' \
    && pg_restore --version | grep -E '^pg_restore \(PostgreSQL\) 16\.'

WORKDIR /app

COPY app/requirements.txt app/requirements-dev.txt ./
ARG INSTALL_DEV=0
RUN pip install -r requirements.txt \
    && if [ "$INSTALL_DEV" = "1" ]; then pip install -r requirements-dev.txt; fi

COPY app/ /app/
COPY deploy/entrypoint.sh /entrypoint.sh
# Bỏ dấu CR nếu tệp bị checkout kiểu Windows (CRLF): "#!/bin/sh\r" làm Linux
# báo "exec /entrypoint.sh: no such file or directory" — không phụ thuộc vào
# cấu hình git của máy dựng image
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

# Không chạy bằng quyền quản trị. /storage là bind mount từ máy chủ; tạo sẵn
# các thư mục con với đúng chủ sở hữu để lần chạy đầu không hỏng vì quyền ghi
RUN useradd --create-home --uid 1000 knjsc && chown -R knjsc /app \
    && mkdir -p /storage/uploads /storage/exports /storage/backups \
    && chown -R knjsc /storage
USER knjsc

ENTRYPOINT ["/entrypoint.sh"]
# 3 tiến trình × 4 luồng (gthread): yêu cầu ngắn (moi-nhat, lưu ô) không xếp hàng sau
# một lượt xuất Excel hay dán 500 ô đang chiếm tiến trình — ADR-016, K27
CMD ["gunicorn", "knjsc.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "4", "--worker-class", "gthread", "--keep-alive", "5"]
