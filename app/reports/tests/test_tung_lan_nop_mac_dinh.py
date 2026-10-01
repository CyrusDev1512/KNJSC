"""Báo cáo tổng hợp luôn hiện từng lần nộp; nút Chọn nhanh chỉ sáng một — chủ dự án 01.10.2026.

"Bỏ luôn ô và chức năng cách xem, để mặc định là từng lần nộp luôn; thị trường, sản phẩm, thời gian đều có
các filter bên dưới rồi." và "lỗi hiển thị khi chọn được cả tháng này và hôm nay" (ngày 01 của tháng).
"""
from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from core.identity import employee_code
from reports import screen
from reports.services import summary_service
from reports.tests.test_activity import delivery_source  # noqa: F401
from reports.tests.test_aggregations import bang_mkt  # noqa: F401
from reports.tests.test_che_do_so_lieu import bon_lan_nop  # noqa: F401
from reports.tests.test_mkt_derived_revenue import mkt_source, van_don  # noqa: F401
from reports.tests.test_mkt_excel import marketing_scope  # noqa: F401


def _sang(presets):
    return [p["key"] for p in presets if p["active"]]


def test_chon_nhanh_chi_sang_mot_nut():
    """AC-22.22 — Ngày 01 của tháng "Hôm nay" và "Tháng này" cùng khoảng, thứ Hai "Hôm nay" và "Tuần này"
    cùng khoảng: chỉ một nút sáng — nút vừa bấm (`ky`) nếu khoảng của nó khớp kỳ đang lọc, không thì nút khớp
    đầu tiên; `ky` không khớp kỳ (đã sửa tay ô ngày) thì không theo `ky`"""
    mung_1 = date(2026, 10, 1)                       # thứ Năm, ngày đầu tháng
    assert _sang(summary_service.date_presets(mung_1, start=mung_1, end=mung_1)) == ["hom-nay"]
    assert _sang(summary_service.date_presets(mung_1, start=mung_1, end=mung_1, key="thang-nay")) == ["thang-nay"]
    assert _sang(summary_service.date_presets(mung_1, start=mung_1, end=mung_1, key="hom-nay")) == ["hom-nay"]
    thu_hai = date(2026, 10, 5)
    assert _sang(summary_service.date_presets(thu_hai, start=thu_hai, end=thu_hai, key="tuan-nay")) == ["tuan-nay"]
    # `ky` cũ không khớp kỳ đang lọc (ví dụ đã sửa tay hai ô ngày): theo kỳ, không theo `ky`
    assert _sang(summary_service.date_presets(mung_1, start=mung_1, end=mung_1, key="hom-qua")) == ["hom-nay"]
    assert _sang(summary_service.date_presets(mung_1, start=date(2026, 9, 3), end=mung_1, key="thang-nay")) == []
    assert _sang(summary_service.date_presets(mung_1, start=mung_1, end=mung_1, key="bia")) == ["hom-nay"]


@pytest.mark.django_db
def test_man_hinh_chi_sang_nut_vua_bam(client, bang_mkt, mkt_source, nguoi_dung, monkeypatch):
    """AC-22.22 — Màn Báo cáo tổng hợp ngày 01.10: bấm "Tháng này" (`ky=thang-nay`) thì chỉ nút đó sáng, không
    sáng cả "Hôm nay"; ô ẩn `ky` giữ nút đã bấm; Bảng dữ liệu dạng báo cáo cũng vậy"""
    monkeypatch.setattr("django.utils.timezone.localdate", lambda *a, **k: date(2026, 10, 1))
    client.force_login(nguoi_dung["manager_mkt"])
    ky = {"nguon": bang_mkt.code, "tu": "2026-10-01", "den": "2026-10-01"}
    r = client.get("/bao-cao/tong-hop/", {**ky, "ky": "thang-nay"})
    html = r.content.decode()
    assert html.count("report-preset is-active") == 1 and 'is-active" data-key="thang-nay"' in html
    assert 'name="ky" id="ky" value="thang-nay"' in html
    assert client.get("/bao-cao/tong-hop/", ky).content.decode().count("report-preset is-active") == 1
    r = client.get(f"/bang/{bang_mkt.code}/", {"tu": "2026-10-01", "den": "2026-10-01", "ky": "thang-nay"})
    html = r.content.decode()
    assert html.count("report-preset is-active") == 1 and 'is-active" data-key="thang-nay"' in html


@pytest.mark.django_db
def test_khong_con_cach_xem_va_che_do(client, bang_mkt, mkt_source, bon_lan_nop, nguoi_dung):
    """AC-22.23 — Bộ lọc Báo cáo tổng hợp và Bảng dữ liệu dạng báo cáo không còn ô Cách xem (`nhom`) và ô Chế
    độ (`che_do`), không chip của hai ô đó: luôn mỗi lần nộp một dòng (cột Lần nộp "Lần N · giờ", số đúng như
    nhập); URL cũ mang `nhom=person|team|department|thi-truong` hay `che_do=cong` vẫn mở 200 và vẫn ra từng
    lần nộp; tệp Excel không còn "Chế độ:" ở phụ đề"""
    client.force_login(bon_lan_nop["B"])
    ma_a = employee_code(bon_lan_nop["A"])
    ky = {"nguon": bang_mkt.code, "tu": "2026-08-01", "den": "2026-08-01"}
    for them in ({}, {"nhom": "person"}, {"nhom": "team"}, {"nhom": "department"}, {"nhom": "thi-truong"},
                 {"nhom": "abc"}, {"che_do": "cong"}, {"che_do": "cong", "nhom": "product"}):
        r = client.get("/bao-cao/tong-hop/", {**ky, **them})
        assert r.status_code == 200, them
        assert r.context["params"]["group"] == "day" and r.context["params"]["mode"] == "tung-lan"
        assert r.context["result"].mode == "tung-lan"
        ky_khoi, ngay = r.context["blocks"]
        assert ky_khoi["kind"] == "period" and "lan" in [c["code"] for c in ngay["identity_columns"]]
        assert len([row for row in ngay["rows"] if row["person"] == ma_a]) == 3       # ba lần nộp, không cộng
        html = r.content.decode()
        assert 'name="nhom"' not in html and 'name="che_do"' not in html and 'id="report-che-do"' not in html
        assert not {"Cách xem", "Chế độ"} & {c["label"] for c in r.context["chips"]}
        assert "Lần 3 · 16:40" in html and ">8.000</td>" in html
    r = client.get(f"/bang/{bang_mkt.code}/", {"tu": "2026-08-01", "den": "2026-08-01", "che_do": "cong"})
    html = r.content.decode()
    assert r.context["result"].mode == "tung-lan" and 'name="che_do"' not in html and "Lần 3 · 16:40" in html
    x = client.get("/bao-cao/tong-hop/xuat/", {**ky, "nhom": "person", "che_do": "cong"})
    book = load_workbook(BytesIO(x.content), data_only=True)
    assert "Chế độ" not in book["Toan ky theo nhan su"]["A2"].value
    assert list(book["Theo ngay"].values)[1][4] == "Lần nộp"


@pytest.mark.django_db
def test_nguon_van_don_van_mot_dong_moi_ngay(client, delivery_source, nguoi_dung, rf):
    """AC-22.23 — Nguồn Vận đơn không có lần nộp: màn hình vẫn mở như trước, không ô Cách xem/Chế độ;
    `screen.parameters` luôn trả cách xem Tổng hợp và Từng lần nộp, bỏ qua `nhom`/`che_do` trên URL"""
    client.force_login(nguoi_dung["manager_sale"])
    r = client.get("/bao-cao/tong-hop/", {"nguon": delivery_source.table.code, "nhom": "person"})
    assert r.status_code == 200 and 'name="nhom"' not in r.content.decode()
    tham_so = screen.parameters(rf.get("/", {"nhom": "person", "che_do": "cong", "ky": "hom-nay"}))
    assert (tham_so["group"], tham_so["mode"], tham_so["ky"]) == ("day", "tung-lan", "hom-nay")
