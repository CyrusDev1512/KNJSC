"""ADR-038 — nộp báo cáo không giới hạn số lần trong ngày; Kế toán xem và sửa mọi báo cáo."""
from datetime import date

import pytest

from reports.models import DailyReport, ReportRevision
from reports.services import daily_service
from reports.tests.test_bao_cao_ngay import NGAY, _nop, bm_mkt, bm_sale  # noqa: F401

pytestmark = pytest.mark.django_db


def test_nop_nhieu_lan_trong_ngay(client, bm_mkt, nguoi_dung):
    """AC-4.7 — Nộp lại cùng biểu mẫu cùng ngày là thêm một bản mới (không chặn, không đè); cả hai
    bản trong Lịch sử với thời điểm nộp riêng; màn nộp cho biết hôm nay đã nộp bao nhiêu lần"""
    nv = nguoi_dung["staff_mkt"]
    lan_1 = _nop(bm_mkt, nv)
    lan_2 = _nop(bm_mkt, nv, so_mess="7")
    assert lan_1.pk != lan_2.pk and DailyReport.objects.count() == 2
    assert lan_1.record.data["so_mess"] == 1000 and lan_2.record.data["so_mess"] == 7
    assert daily_service.submissions_today(bm_mkt, nv, NGAY) == 2
    client.force_login(nv)
    assert client.get("/bao-cao/lich-su/", {"tu": str(NGAY), "den": str(NGAY)}).context["trang"].paginator.count == 2
    html = client.get("/bao-cao/", {"bieu_mau": bm_mkt.code}).content.decode()
    assert "đã nộp" not in html.lower() or "lần" in html
    # Nộp qua màn hình cho hôm nay hai lần liên tiếp cũng được và thông báo số lần
    for _ in range(2):
        assert client.post("/bao-cao/", {"bieu_mau": bm_mkt.code, "ngay": date.today().isoformat(),
                                         "so_mess": "3", "so_don": "1", "doanh_so": "10"}).status_code == 302
    html = client.get("/bao-cao/", {"bieu_mau": bm_mkt.code}).content.decode()
    assert "2 lần" in html and "đã khoá" not in html


@pytest.mark.parametrize("bieu_mau", ["bm_sale", "bm_mkt"])
def test_ke_toan_xem_va_sua_moi_bao_cao(client, request, nguoi_dung, bieu_mau):
    """AC-4.8 — Kế toán thấy báo cáo của mọi bộ phận trong Lịch sử, mở và sửa được (có ReportRevision,
    giữ người nộp và ngày), nhưng không bỏ được báo cáo của người khác; nhân viên bộ phận khác
    (Vận đơn) vẫn bị 404 ở cả xem lẫn sửa"""
    bm = request.getfixturevalue(bieu_mau)
    nguoi_nop = nguoi_dung["staff_sale_1"] if bieu_mau == "bm_sale" else nguoi_dung["staff_mkt"]
    report = _nop(bm, nguoi_nop)
    kt = nguoi_dung["staff_kt"]
    assert daily_service.can_amend(kt, report)
    assert DailyReport.objects.in_scope(kt).filter(pk=report.pk).exists()
    client.force_login(kt)
    assert client.get("/bao-cao/lich-su/").context["trang"].paginator.count == 1
    assert client.get(f"/bao-cao/{report.pk}/").status_code == 200
    response = client.get(f"/bao-cao/{report.pk}/sua/")
    assert response.status_code == 200
    response = client.post(f"/bao-cao/{report.pk}/sua/", {"version": response.context["version"],
                                                          "so_mess": "250", "so_don": "50", "doanh_so": "5000000"})
    assert response.status_code == 302
    report.refresh_from_db(); report.record.refresh_from_db()
    assert report.record.data["so_mess"] == 250 and report.created_by == nguoi_nop
    assert ReportRevision.objects.filter(report=report, actor=kt).count() == 1
    # Bỏ báo cáo vẫn chỉ người nộp: Kế toán bị từ chối (chuyển hướng kèm thông báo), bản không bị đánh dấu xoá
    assert client.post(f"/bao-cao/{report.pk}/bo/").status_code in (302, 403, 404)
    assert DailyReport.objects.filter(pk=report.pk, deleted_at__isnull=True).exists()
    client.force_login(nguoi_dung["staff_vd"])
    assert client.get(f"/bao-cao/{report.pk}/").status_code == 404
    assert client.get(f"/bao-cao/{report.pk}/sua/").status_code == 404
    assert not DailyReport.objects.in_scope(nguoi_dung["staff_vd"]).exists()
