"""Lượt hỏi "có gì mới" của lưới Vận đơn không quét cả bảng theo phạm vi — AC-10.21 (07.10.2026).

Mỗi tab hỏi `moi-nhat/` mỗi 8 giây. Bảng Vận đơn từng tính mốc theo phạm vi người xem kèm COUNT (JOIN phân công):
418–595 ms mỗi lần ở 385.000 dòng. Nay mốc lấy trên cả bảng qua chỉ mục `(table, updated_at)` (0,8 ms), như mọi bảng
khác và đúng ghi chú của view; mốc chỉ là thời điểm, không lộ dữ liệu. Sửa ô, xoá, đổi phân công vẫn đổi mốc.
"""
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from crm.tests.test_waybill_feedback import assign_rows, cskh_staff, delivery_leader, feedback  # noqa: F401
from forms_builder.services import record_service

pytestmark = pytest.mark.django_db
URL = "/bang-tinh/van_don/moi-nhat/"


def test_moc_khong_join_pham_vi_va_khong_dem(client, feedback, nguoi_dung):
    """AC-10.21 — `moi-nhat/` của bảng Vận đơn: truy vấn mốc không JOIN phân công, không COUNT; chỉ trả thời điểm"""
    client.force_login(nguoi_dung["staff_vd"])
    client.get(URL)
    with CaptureQueriesContext(connection) as q:
        kq = client.get(URL)
    assert kq.status_code == 200
    moc_sql = [x["sql"] for x in q.captured_queries if 'MAX("forms_builder_datarecord"."updated_at")' in x["sql"]]
    assert len(moc_sql) == 1
    assert "COUNT(" not in moc_sql[0] and "waybillassignment" not in moc_sql[0].lower()
    assert set(kq.json()) == {"delivery_view_version", "moc", "cot", "tinh_lai"}


def test_moc_doi_khi_sua_o_va_doi_phan_cong(client, feedback, nguoi_dung, delivery_leader, cskh_staff):
    """AC-10.21 — Mốc đổi khi sửa một ô và khi đổi phân công (dòng ra hay vào phạm vi một người), nên lưới vẫn biết
    lúc cần tải lại và kiểm quyền; người ngoài phạm vi bảng vẫn 404"""
    _, _, rows = feedback
    client.force_login(nguoi_dung["staff_vd"])
    moc1 = client.get(URL).json()["moc"]
    record_service.update_cell(rows[0], "ghi_chu", "đổi", actor=nguoi_dung["staff_vd"])
    moc2 = client.get(URL).json()["moc"]
    assert moc2 > moc1
    assign_rows(delivery_leader, [rows[1]], care=cskh_staff.pk)
    assert client.get(URL).json()["moc"] > moc2
    client.force_login(nguoi_dung["staff_mkt"])
    assert client.get(URL).status_code in (403, 404)
