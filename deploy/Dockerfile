# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Múi giờ, thư viện cho psycopg, và postgresql-client để có pg_dump/pg_restore
# cho sao lưu (docs/03 mục 8). Bản client của Debian trixie là 17, đọc và ghi
# được cơ sở dữ liệu PostgreSQL 16.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata libpq5 postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app/requirements.txt app/requirements-dev.txt ./
ARG INSTALL_DEV=0
RUN pip install -r requirements.txt \
    && if [ "$INSTALL_DEV" = "1" ]; then pip install -r requirements-dev.txt; fi

COPY app/ /app/
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Không chạy bằng quyền quản trị. /storage là bind mount từ máy chủ; tạo sẵn
# các thư mục con với đúng chủ sở hữu để lần chạy đầu không hỏng vì quyền ghi
RUN useradd --create-home --uid 1000 knjsc && chown -R knjsc /app \
    && mkdir -p /storage/uploads /storage/exports /storage/backups \
    && chown -R knjsc /storage
USER knjsc

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "knjsc.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
