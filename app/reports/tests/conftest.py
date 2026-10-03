"""Fixture dùng chung của bài kiểm báo cáo."""
import pytest


@pytest.fixture
def du_cot_dinh_danh(monkeypatch):
    """Hiện đủ cột định danh (Lần nộp, Loại tiền) cho mọi loại nguồn. Bài dùng fixture này kiểm cơ chế hai cột đó —
    vẫn dùng cho báo cáo Sale — bằng dữ liệu mẫu MKT; báo cáo MKT thật ẩn hai cột (AC-47.6, `layout.HIDDEN_IDENTITY`)."""
    from reports import layout
    monkeypatch.setattr(layout, "HIDDEN_IDENTITY", {})
