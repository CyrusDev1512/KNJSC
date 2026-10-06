"""Postgres khởi động lại thì kết nối cũ không làm hỏng yêu cầu nào — AC-10.15 (săn lỗi 06.10.2026).

Đo trên gunicorn như VPS (gthread, `CONN_MAX_AGE` 60): khởi động lại Postgres, đợi nó chạy lại 3 giây, bắn 16 yêu cầu
→ **8 yêu cầu lỗi 500**, đúng bằng số kết nối gunicorn đang giữ. Postgres đã khoẻ mà người dùng vẫn gặp lỗi, kể cả
khi đang lưu. Nay mỗi yêu cầu kiểm kết nối giữ lại trước khi dùng (`CONN_HEALTH_CHECKS`).
"""
import pytest
from django.db import close_old_connections, connection


@pytest.mark.django_db(transaction=True)
def test_ket_noi_cu_hong_tu_mo_lai():
    """AC-10.15 — Kết nối cơ sở dữ liệu giữ lại đã bị Postgres cắt (khởi động lại): yêu cầu tiếp theo tự mở kết nối mới và chạy được, không lỗi"""
    connection.ensure_connection()
    connection.connection.close()   # Postgres cắt kết nối, Django không hay biết
    close_old_connections()          # việc Django làm ở đầu mỗi yêu cầu
    with connection.cursor() as c:
        c.execute("SELECT 1")
        assert c.fetchone() == (1,)
