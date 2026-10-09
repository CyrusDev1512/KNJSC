"""Ký tự NUL ở bất kỳ đầu vào nào: trả 400 tiếng Việt, không lỗi 500 — AC-10.16 (săn lỗi 06.10.2026, fuzz).

Fuzz 4.559 yêu cầu vào KN ERP: 26 lỗi 500, đều cùng một gốc — chuỗi có ký tự NUL (`%00`) đi thẳng vào câu truy vấn và
Postgres từ chối ("text fields cannot contain NUL"): ô tìm của Biểu mẫu, Tài nguyên; bộ lọc Sản phẩm, Thị trường của
Báo cáo tổng hợp; đăng bài, bình luận Bảng tin. Không có cách gõ NUL hợp lệ nào, nên chặn một lần ở cửa vào
(`core.middleware.UnicodeNFCMiddleware`) thay vì vá từng view.
"""
import json

import pytest

pytestmark = pytest.mark.django_db


def test_get_co_nul_tra_400(client, nguoi_dung):
    """AC-10.16 — Tham số GET có NUL (ô tìm Tài nguyên, Biểu mẫu, bộ lọc Báo cáo tổng hợp): 400 với lời tiếng Việt"""
    client.force_login(nguoi_dung["manager_mkt"])
    for url in ("/tai-nguyen/?tim=x%00y", "/bieu-mau/?tim=x%00y", "/bao-cao/tong-hop/?sp=x%00y", "/bao-cao/tong-hop/?thi_truong=%00"):
        r = client.get(url)
        assert r.status_code == 400, url
        assert "ký tự điều khiển" in r.content.decode(), url


def test_post_co_nul_tra_400(client, nguoi_dung):
    """AC-10.16 — Form POST có NUL (đăng bài Bảng tin): 400 với lời tiếng Việt, không ghi gì"""
    from feed.models import Post

    client.force_login(nguoi_dung["manager_mkt"])
    truoc = Post.objects.count()
    r = client.post("/bang-tin/dang/", {"noi_dung": "x\x00y", "body": "x\x00y", "content": "x\x00y"})
    assert r.status_code == 400
    assert "ký tự điều khiển" in r.content.decode()
    assert Post.objects.count() == truoc


def test_json_co_nul_tra_400_dang_json(client, nguoi_dung):
    """AC-10.16 — Thân JSON có NUL (lưới): 400 và lời lỗi ở khoá `error` như các lỗi khác của lưới"""
    client.force_login(nguoi_dung["admin"])
    r = client.post("/bang-tinh/van_don/luu-json/", json.dumps({"cells": [{"value": "x\u0000y"}]}),
                    content_type="application/json")
    assert r.status_code == 400
    assert "ký tự điều khiển" in r.json()["error"]


def test_nhap_lieu_binh_thuong_khong_bi_chan(client, nguoi_dung):
    """AC-10.16 — Chữ thường, chữ Việt, ký tự đặc biệt khác (tab, xuống dòng, emoji) vẫn đi qua"""
    client.force_login(nguoi_dung["manager_mkt"])
    assert client.get("/tai-nguyen/?tim=Ngọc%09Ánh%0A😀").status_code == 200


def test_ten_qua_dai_tra_400_khong_500(client, nguoi_dung):
    """AC-10.16 — Tên mục Tài nguyên 5.000 ký tự (cột giữ 120): trả 400 "nội dung quá dài" tiếng Việt, không lỗi 500, không ghi gì — chặn chung cho mọi chỗ ghi chuỗi vượt độ dài cột"""
    from resources.models import ResourceCategory

    client.force_login(nguoi_dung["manager_mkt"])
    truoc = ResourceCategory.objects.count()
    r = client.post("/tai-nguyen/muc-moi/", {"name": "a" * 5000})
    assert r.status_code == 400
    assert "quá dài" in r.content.decode()
    assert ResourceCategory.objects.count() == truoc
