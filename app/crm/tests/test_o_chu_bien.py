"""Ô chữ ở biên: ký tự NUL và chuỗi quá dài — AC-21.16 (săn lỗi 06.10.2026, fuzz).

Fuzz trên hệ thống thật: gửi vào lưới một ô có ký tự NUL (`\\u0000`) là **lỗi 500** — Postgres không chứa được ký tự
này trong JSONB. Và một ô ghi chú nhận được 200.000 ký tự, trong khi một ô Excel chỉ giữ được 32.767 ký tự: tệp xuất
ra mở bằng Excel sẽ báo hỏng. Nay ô chữ từ chối NUL và chuỗi dài quá trần một ô Excel, báo lỗi tiếng Việt, ở mọi
đường ghi (lưới, nhập tệp, form) vì cùng đi qua `record_service.parse_value`.
"""
import pytest

from core.constants import CELL_TEXT_MAX_CHARS
from core.exceptions import BusinessError
from forms_builder.meaning import FieldType
from forms_builder.models import ColumnDef
from forms_builder.services.record_service import parse_value

from .test_master_grid import write
from .test_waybill_feedback import feedback  # noqa: F401 — fixture dùng chung

pytestmark = pytest.mark.django_db


def test_luoi_o_co_nul_bao_loi_khong_500(client, feedback, nguoi_dung):  # noqa: F811
    """AC-21.16 — Lưới nhận ô có ký tự NUL: trả 400 với lời tiếng Việt, dữ liệu không đổi, không lỗi 500"""
    client.force_login(nguoi_dung["admin"])
    row = feedback[2][0]
    cu = row.data.get("ghi_chu")
    r = write(client, row, old=cu, value="x\u0000y")
    assert r.status_code == 400
    assert "ký tự điều khiển" in r.json()["error"]
    row.refresh_from_db()
    assert row.data.get("ghi_chu") == cu


def test_luoi_o_qua_dai_bao_loi(client, feedback, nguoi_dung):  # noqa: F811
    """AC-21.16 — Ô chữ dài hơn 32.767 ký tự (trần một ô Excel) bị từ chối với lời nói rõ trần; đúng bằng trần thì ghi được"""
    client.force_login(nguoi_dung["admin"])
    row = feedback[2][0]
    cu = row.data.get("ghi_chu")
    r = write(client, row, old=cu, value="a" * (CELL_TEXT_MAX_CHARS + 1))
    assert r.status_code == 400 and "32.767" in r.json()["error"]
    assert write(client, row, old=cu, value="a" * CELL_TEXT_MAX_CHARS).status_code == 200


def test_parse_value_dung_chung_cho_moi_duong_ghi():
    """AC-21.16 — Kiểm ở `parse_value` (đường ghi chung của lưới, nhập tệp, form): cột Chữ, Chữ dài, Chọn một đều từ chối NUL"""
    for kieu in (FieldType.TEXT, FieldType.LONG_TEXT, FieldType.CHOICE):
        cot = ColumnDef(code="c", name="Cột", field_type=kieu)
        with pytest.raises(BusinessError, match="ký tự điều khiển"):
            parse_value(cot, "a\x00b", choices=[])


def test_tao_thu_muc_ma_bo_phan_la_404_khong_500(client, nguoi_dung):
    """AC-10.16 — Tạo thư mục với mã bộ phận không phải số (gửi tay, fuzz): 404, không lỗi 500"""
    client.force_login(nguoi_dung["admin"])
    assert client.post("/bang-tinh/thu-muc/moi/", {"bo_phan": "abc", "name": "X"}).status_code == 404


@pytest.mark.parametrize("tham_so", ["f_ngay__lon_bang=2026-13-45", "f_ngay__nho_bang=NaN", "f_ngay__lon_bang=١٢٣"])
def test_luoi_loc_ngay_sai_kieu_khong_500(client, feedback, nguoi_dung, tham_so):  # noqa: F811
    """AC-10.16 — Lưới Vận đơn mở với bộ lọc ngày sai kiểu trên URL (khung trang và khối dữ liệu): 200, bộ lọc bị bỏ qua"""
    client.force_login(nguoi_dung["admin"])
    assert client.get(f"/bang-tinh/van_don/?{tham_so}").status_code == 200
    assert client.get(f"/bang-tinh/van_don/du-lieu/?offset=0&limit=100&{tham_so}").status_code == 200
