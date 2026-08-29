"""Cấu hình khi chạy kiểm thử.

Khác dev ở chỗ: bật thêm app chứa model thử phạm vi, chạy tác vụ nền ngay tại
chỗ, băm mật khẩu bằng thuật toán nhanh, và tách mọi thứ ghi ra ngoài khỏi máy
thật — tệp tải lên, thư điện tử.

**Nguyên tắc:** cấu hình kiểm thử được phép chạy nhanh hơn, nhưng **không được
dễ dãi hơn**. Chỗ nào nới lỏng mà làm bài kiểm mất ý nghĩa thì phải ghi rõ, và
bài kiểm liên quan phải tự dựng lại điều kiện thật.
"""
import tempfile

from .dev import *  # noqa: F401,F403
from .dev import INSTALLED_APPS

INSTALLED_APPS = INSTALLED_APPS + ["core.tests.apps.CoreTestsConfig"]

# Tác vụ nền chạy ngay tại chỗ, và lỗi trong đó phải nổ ra.
# Thiếu EAGER_PROPAGATES thì tác vụ hỏng vẫn im lặng và bài kiểm vẫn xanh.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Băm nhanh cho đỡ mất thời gian. Bài kiểm AC-10.7 tự dựng lại thuật toán thật
# — xem core/tests/test_ra_soat.py, vì kiểm mật khẩu dưới MD5 thì không chứng
# minh được gì về hệ thống thật.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Tệp tải lên trong lúc kiểm ghi vào thư mục tạm, không đụng storage/uploads thật
MEDIA_ROOT = tempfile.mkdtemp(prefix="knjsc-kiem-thu-")

# Thư điện tử giữ trong bộ nhớ, không gửi đi đâu cả
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Giữ đúng ngưỡng thật để bài kiểm AC-1.4 có nghĩa
SESSION_IDLE_TIMEOUT_SECONDS = 3600
