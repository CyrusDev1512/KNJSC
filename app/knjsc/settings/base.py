"""Cấu hình dùng chung cho mọi môi trường.

Mọi giá trị khác nhau giữa máy cá nhân và máy chủ đều đọc từ biến môi
trường, không viết cứng ở đây. Mẫu biến nằm ở config/.env.example.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPO_DIR = BASE_DIR.parent


def env(ten, mac_dinh=None, bat_buoc=False):
    """Đọc một biến môi trường. Thiếu biến bắt buộc thì dừng ngay khi khởi động."""
    gia_tri = os.environ.get(ten, mac_dinh)
    if bat_buoc and gia_tri in (None, ""):
        raise RuntimeError(f"Thiếu biến môi trường bắt buộc: {ten}")
    return gia_tri


def env_bool(ten, mac_dinh=False):
    return str(os.environ.get(ten, str(mac_dinh))).lower() in ("1", "true", "yes", "on")


def env_list(ten, mac_dinh=""):
    return [x.strip() for x in os.environ.get(ten, mac_dinh).split(",") if x.strip()]


SECRET_KEY = env("DJANGO_SECRET_KEY", "khong-dung-gia-tri-nay-tren-may-chu")
DEBUG = False
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

# ── Ứng dụng ────────────────────────────────────────────────────────
# Bảy module trong app/. core là module duy nhất được các module khác
# gọi vào; các module còn lại không gọi trực tiếp nhau.
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

LOCAL_APPS = [
    "core",
    "org",
    "forms_builder",
    "reports",
    "orders",
    "dashboard",
    "crm",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Ba middleware của core, phải nằm sau AuthenticationMiddleware
    "core.middleware.SessionTimeoutMiddleware",
    "core.middleware.ForcePasswordChangeMiddleware",
    "core.middleware.NoCacheForAuthenticatedMiddleware",
]

ROOT_URLCONF = "knjsc.urls"
WSGI_APPLICATION = "knjsc.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.khung_chung",
            ],
        },
    },
]

# ── Cơ sở dữ liệu ───────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "knjsc_db"),
        "USER": env("POSTGRES_USER", "knjsc"),
        "PASSWORD": env("POSTGRES_PASSWORD", "knjsc"),
        "HOST": env("POSTGRES_HOST", "localhost"),
        "PORT": env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Mật khẩu ────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "/dang-nhap/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/dang-nhap/"

# ── Ngôn ngữ và thời gian ───────────────────────────────────────────
# Mọi thời điểm lưu theo giờ quốc tế, hiển thị theo giờ Việt Nam.
LANGUAGE_CODE = "vi"
TIME_ZONE = "Asia/Ho_Chi_Minh"
USE_I18N = True
USE_TZ = True

# ── Tệp tĩnh và tệp tải lên ─────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = REPO_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
MEDIA_URL = "/media/"
MEDIA_ROOT = REPO_DIR / "storage" / "uploads"

# ── Phiên đăng nhập ─────────────────────────────────────────────────
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
# Hết phiên sau 60 phút không thao tác — FR-1.3, kiểm bằng AC-1.4
SESSION_IDLE_TIMEOUT_SECONDS = int(env("SESSION_IDLE_TIMEOUT_SECONDS", "3600"))

# ── Quy tắc nghiệp vụ khai báo ở một chỗ duy nhất ───────────────────
PAGE_SIZE_DEFAULT = 25          # quy tắc 1
LOGIN_MAX_FAILED = 5            # FR-1.2
LOGIN_LOCK_MINUTES = 15         # FR-1.2
EXPORT_MAX_ROWS = 50_000

# ── Tác vụ nền ──────────────────────────────────────────────────────
CELERY_BROKER_URL = env("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)

# ── Nhật ký ứng dụng ────────────────────────────────────────────────
# Không ghi dữ liệu nhạy cảm vào đây, kể cả khi gỡ lỗi.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "chuan": {"format": "{asctime} {levelname} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "chuan"},
    },
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}
