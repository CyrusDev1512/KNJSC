"""Hàng đợi tác vụ nền chết thì nói rõ, không treo, không lỗi 500 — AC-10.13 (săn lỗi 06.10.2026).

Đo trên hệ thống thật, tắt Redis: xuất Excel lưới Vận đơn (đủ lớn để chạy nền) treo 19 giây rồi trang lỗi 500, và tác
vụ nằm lại "Chờ xử lý" mãi — worker không bao giờ nhận được nó. Nay gửi vào hàng đợi chỉ thử lại ngắn; không gửi được
thì tác vụ thành "Thất bại" với lời tiếng Việt, người dùng về trang tác vụ thấy ngay vì sao.
"""
import time
from unittest.mock import patch

import pytest
from kombu.exceptions import OperationalError

from core.constants import JobKind, JobStatus
from core.models import BackgroundJob
from forms_builder.services import export_service
from forms_builder.services.import_service import _day_vao_hang_doi
from forms_builder.tasks import chay_tac_vu_xuat

from .test_waybill_new import form_data, setup  # noqa: F401 — fixture `setup` dùng chung

pytestmark = pytest.mark.django_db

REDIS_CHET = OperationalError("Error 111 connecting to 127.0.0.1:6379. Connection refused.")


def test_gui_hang_doi_hong_danh_dau_that_bai(settings, nguoi_dung, django_capture_on_commit_callbacks):
    """AC-10.13 — Không gửi được tác vụ vào hàng đợi (Redis tắt): không ném lỗi ra người gọi, tác vụ thành Thất bại kèm lời tiếng Việt nói hàng đợi không chạy, không kẹt ở Chờ xử lý"""
    settings.CELERY_TASK_ALWAYS_EAGER = False
    job = BackgroundJob.objects.create(kind=JobKind.EXPORT, status=JobStatus.PENDING, created_by=nguoi_dung["admin"])
    with patch.object(chay_tac_vu_xuat, "apply_async", side_effect=REDIS_CHET), \
            django_capture_on_commit_callbacks(execute=True):
        _day_vao_hang_doi(chay_tac_vu_xuat, job.pk)
    job.refresh_from_db()
    assert job.status == JobStatus.FAILED
    assert "hàng đợi" in job.error


def test_gui_hang_doi_thu_lai_ngan(settings, nguoi_dung, django_capture_on_commit_callbacks):
    """AC-10.13 — Gửi vào hàng đợi chỉ thử lại ngắn (dưới 3 giây tổng), không để người dùng chờ hàng chục giây như mặc định của Celery"""
    settings.CELERY_TASK_ALWAYS_EAGER = False
    job = BackgroundJob.objects.create(kind=JobKind.EXPORT, status=JobStatus.PENDING, created_by=nguoi_dung["admin"])
    with patch.object(chay_tac_vu_xuat, "apply_async") as gui, django_capture_on_commit_callbacks(execute=True):
        _day_vao_hang_doi(chay_tac_vu_xuat, job.pk)
    chinh_sach = gui.call_args.kwargs["retry_policy"]
    tong = sum(min(chinh_sach["interval_start"] + i * chinh_sach["interval_step"], chinh_sach["interval_max"])
               for i in range(chinh_sach["max_retries"]))
    assert tong < 3
    assert gui.call_args.args[0] == (job.pk,)


def test_khong_luu_ket_qua_tac_vu():
    """AC-10.13 — Celery không lưu kết quả tác vụ (tiến độ đã ở BackgroundJob): gửi tác vụ lúc Redis tắt không còn chờ bộ lưu kết quả thử lại 20 lần"""
    from knjsc.celery import app

    assert app.conf.task_ignore_result is True


def test_xuat_luoi_luc_redis_tat_khong_500(client, settings, setup, nguoi_dung):  # noqa: F811
    """AC-10.13 — Xuất Excel lưới chạy nền lúc Redis tắt: trả về ngay (dưới 5 giây), không lỗi 500, người dùng ở lại lưới thấy lời báo hàng đợi không chạy; tác vụ ghi Thất bại"""
    settings.CELERY_TASK_ALWAYS_EAGER = False
    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.post("/van-don/len-don/", form_data(setup[2])).status_code == 200
    bang = setup[1]
    bat_dau = time.monotonic()
    # Ngoài giao dịch (như máy chủ thật, không ATOMIC_REQUESTS) on_commit chạy ngay
    with patch.object(export_service, "EXPORT_SYNC_MAX_ROWS", 0), \
            patch.object(chay_tac_vu_xuat, "apply_async", side_effect=REDIS_CHET), \
            patch("forms_builder.services.import_service.transaction.on_commit", side_effect=lambda f: f()):
        r = client.get(f"/bang-tinh/{bang.code}/xuat/", follow=True)
    assert time.monotonic() - bat_dau < 5
    assert r.status_code == 200
    assert r.redirect_chain[-1][0].endswith(f"/bang-tinh/{bang.code}/")
    assert "hàng đợi" in r.content.decode()
    assert BackgroundJob.objects.get(kind=JobKind.EXPORT).status == JobStatus.FAILED


def test_tac_vu_xuat_het_dia_noi_ro(setup, nguoi_dung, client):  # noqa: F811
    """AC-10.14 — Tác vụ xuất nền gặp đĩa đầy lúc ghi tệp: tác vụ Thất bại với lời "hết chỗ lưu tệp" và người vận hành được báo, không phải "lỗi hệ thống" chung chung"""
    import errno

    from django.core.cache import cache
    from django.http import QueryDict

    cache.delete("canh-bao-het-dia")
    client.force_login(nguoi_dung["staff_sale_1"])
    assert client.post("/van-don/len-don/", form_data(setup[2])).status_code == 200
    with patch.object(export_service, "EXPORT_SYNC_MAX_ROWS", 0), \
            patch("forms_builder.services.import_service._day_vao_hang_doi"):
        _, job = export_service.export(nguoi_dung["staff_sale_1"], setup[1], QueryDict(""), builder="grid")
    with patch.object(export_service, "build_workbook", side_effect=OSError(errno.ENOSPC, "No space left on device")), \
            patch("core.alerts.mail_admins") as thu:
        export_service.run(job.pk)
    job.refresh_from_db()
    assert job.status == JobStatus.FAILED
    assert "hết chỗ lưu tệp" in job.error
    assert thu.called
