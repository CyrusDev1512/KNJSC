"""Tác vụ nền của bảng động: nhập và xuất tệp.

Đặt ở đây chứ không ở core — core không được gọi ngược vào module nghiệp vụ.
Tác vụ chỉ gọi tầng dịch vụ, không viết logic lần hai.
"""
from celery import shared_task

from .services import export_service, import_service


@shared_task(name="forms_builder.chay_tac_vu_nhap")
def chay_tac_vu_nhap(job_id):
    job = import_service.run(job_id)
    return job.status if job else "bo_qua"


@shared_task(name="forms_builder.chay_tac_vu_xuat")
def chay_tac_vu_xuat(job_id):
    job = export_service.run(job_id)
    return job.status if job else "bo_qua"
