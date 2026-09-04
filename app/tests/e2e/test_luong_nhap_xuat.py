"""Nhập → xem → xuất → nhập lại, bằng trình duyệt thật — AC-7.7 qua giao diện."""
from datetime import date

import pytest

from core import excel
from forms_builder.meaning import FieldType, Meaning
from forms_builder.models import ColumnDef, DataRecord, TableDef

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet, pytest.mark.cham]


@pytest.fixture
def bang_sale(departments, nguoi_dung):
    bang = TableDef.objects.create(
        name="Đơn hàng Sale", code="don_sale",
        department=departments["sale"], created_by=nguoi_dung["manager_sale"],
    )
    for i, (ten, ma, kieu, nhan) in enumerate([
        ("Ngày", "ngay", FieldType.DATE, Meaning.DATE),
        ("Khách hàng", "khach", FieldType.TEXT, Meaning.CUSTOMER),
        ("Doanh thu", "doanh_thu", FieldType.MONEY, Meaning.REVENUE),
        ("Số lượng", "so_luong", FieldType.INTEGER, ""),
    ]):
        ColumnDef.objects.create(table=bang, name=ten, code=ma, field_type=kieu, meaning=nhan, order=i)
    return bang


def _nhap(page, goc, tep):
    page.goto(goc + "/bang/don_sale/nhap/")
    page.set_input_files("input[name=tep]", str(tep))
    page.click("text=Tải lên và xem trước")
    page.wait_for_url("**/nhap/*/")
    assert "Khách hàng" in page.content()
    page.click("text=Xác nhận nhập")
    page.wait_for_url("**/tac-vu/*/")
    page.wait_for_selector("text=Đã nhập 3 dòng")
    return page.content()


def test_nhap_xem_xuat_roi_nhap_lai_qua_trinh_duyet(live_server, trang, dang_nhap, bang_sale,
                                                     nguoi_dung, tmp_path):
    """AC-7.7 — Qua trình duyệt thật: nhập tệp, xem bảng, xuất tệp, nhập lại tệp vừa xuất — không dòng lỗi"""
    tep = tmp_path / "don.xlsx"
    excel.write_table(
        ["Ngày", "Khách hàng", "Doanh thu", "Số lượng"],
        [[date(2026, 8, 1), "K1", 1000, 1], [date(2026, 8, 2), "K2", 2000, 2],
         [date(2026, 8, 3), "K3", 3000, 3]],
    ).save(tep)
    dang_nhap(trang, nguoi_dung["manager_sale"])
    goc = live_server.url

    _nhap(trang, goc, tep)
    assert DataRecord.objects.filter(table=bang_sale).count() == 3

    trang.goto(goc + "/bang/don_sale/")
    assert "K1" in trang.content() and "K3" in trang.content()
    with trang.expect_download() as tai:
        trang.click("text=Xuất tệp")
    xuat = tmp_path / "xuat.xlsx"
    tai.value.save_as(xuat)
    assert xuat.stat().st_size > 1000

    noi_dung = _nhap(trang, goc, xuat)
    assert "Không có dòng lỗi" in noi_dung
    assert DataRecord.objects.filter(table=bang_sale).count() == 6
