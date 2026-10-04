"""Fixture dùng chung của bài kiểm báo cáo."""
import pytest


@pytest.fixture
def du_cot_dinh_danh(monkeypatch):
    """Hiện đủ cột định danh (Lần nộp, Loại tiền) cho mọi loại nguồn. Bài dùng fixture này kiểm cơ chế hai cột đó
    bằng dữ liệu mẫu MKT; báo cáo thật ẩn theo `layout.HIDDEN_IDENTITY`: MKT ẩn cả hai (AC-47.6), Sale ẩn Lần nộp,
    giữ Loại tiền (AC-47.7)."""
    from reports import layout
    monkeypatch.setattr(layout, "HIDDEN_IDENTITY", {})
