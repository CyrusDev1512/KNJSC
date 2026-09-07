"""Chuỗi truy vấn của bộ lọc nối vào phân trang — rà soát 07.09.2026.

`f"&tim={tim}"` ghép tay làm "Sale & Marketing" mất nửa sau và "#" cắt cả
chuỗi; `filter_query` mã hoá URL một chỗ cho mọi màn hình danh sách.
"""
import pytest

from core.pagination import filter_query

pytestmark = pytest.mark.django_db


def test_filter_query_ma_hoa_va_bo_gia_tri_trong():
    """AC-10.2 — Bộ lọc nối vào phân trang được mã hoá URL, giá trị trống bị bỏ, không có gì thì rỗng"""
    assert filter_query(tim="Sale & Marketing #1", muc="", nguoi=None) == "&tim=Sale+%26+Marketing+%231"
    assert filter_query(muc=7, tab="cua_toi") == "&muc=7&tab=cua_toi"
    assert filter_query(tim="") == ""


def test_tim_co_dau_va_van_giu_qua_phan_trang(client, nguoi_dung, departments):
    """AC-12.3 — Tìm tài liệu với chữ "&" trong từ khoá: chuyển trang vẫn giữ nguyên từ khoá"""
    from documents.services import document_service

    muc = document_service.create_category(name="Chung", department=None, actor=nguoi_dung["admin"])
    for i in range(27):
        document_service.upload_document(
            title=f"Sale & Marketing {i:02d}", category=muc, link="https://vi.du/x", actor=nguoi_dung["admin"])
    client.force_login(nguoi_dung["staff_vd"])
    kq = client.get("/tai-lieu/", {"tim": "Sale & Marketing"})
    assert kq.context["page_obj"].paginator.count == 27
    assert kq.context["qs_loc"] == "&tim=Sale+%26+Marketing"
    assert "&amp;tim=Sale+%26+Marketing" in kq.content.decode()
    kq2 = client.get("/tai-lieu/", {"tim": "Sale & Marketing", "trang": 2})
    assert len(kq2.context["trang"]) == 2 and kq2.context["page_obj"].paginator.count == 27
