# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Múi giờ và thư viện cần cho psycopg
RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY app/requirements.txt app/requirements-dev.txt ./
ARG INSTALL_DEV=0
RUN pip install -r requirements.txt \
    && if [ "$INSTALL_DEV" = "1" ]; then pip install -r requirements-dev.txt; fi

COPY app/ /app/
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Không chạy bằng quyền quản trị
RUN useradd --create-home --uid 1000 knjsc && chown -R knjsc /app
USER knjsc

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "knjsc.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
