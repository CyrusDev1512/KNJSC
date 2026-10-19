"""Khoá lệnh đo hiệu năng `do_hieu_nang` — TL-98 · P0-16.

Lệnh này gọi GET nặng, EXPLAIN ANALYZE, xuất 50.000 dòng và **ghi** vào bảng vận đơn
(lưu ô, định dạng). Trước đây nó không có khoá DEBUG như các lệnh dữ liệu giả khác, và
chọn dòng để ghi là "5.000 dòng mới nhất trong phạm vi" — trên máy có dữ liệu thật thì đó
là dòng khách thật. Nay: DEBUG tắt thì từ chối trừ khi ghi rõ `--dong-y-chay-that`; lệnh
ghi chỉ đụng dòng `PERF-*` do `seed_perf` sinh, thiếu thì dừng trước khi đo.

Các bài chọn phạm vi dùng hàm giả (`bo_do_that`); bài JSON gọi endpoint thật để
kiểm hợp đồng CAS hiện hành. Không dùng thời gian của nhóm này làm kết quả kiểm tải.
"""
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from core.management.commands import do_hieu_nang
from core.management.commands.seed_perf import PERF_PREFIX
from forms_builder.models import DataRecord
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db

THAM_SO = ("--lan", "1", "--bo-tinh-lai-lon", "--nguoi", "staff_vd",
           "--nguoi-sale", "manager_sale", "--quan-ly-sale", "manager_sale")


@pytest.fixture
def bang_do(nguoi_dung, settings, tmp_path):
    settings.GRID_ONLY_TABLES = set()
    settings.STORAGE_DIR = tmp_path
    return dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])


def _tao_dong(bang, nguoi, tien_to, so, ghi_chu=""):
    DataRecord.objects.bulk_create([
        DataRecord(table=bang, department=bang.department, created_by=nguoi,
                   data={"ma_don": f"{tien_to}{i:05d}", "ghi_chu": ghi_chu})
        for i in range(so)])
    return set(DataRecord.objects.filter(table=bang, data__ma_don__startswith=tien_to).values_list("pk", flat=True))


@pytest.fixture
def bo_do_that(monkeypatch):
    """Thay hai hàm gọi HTTP của lệnh: GET không làm gì, POST chỉ dựng payload và ghi lại.
    `_get`/`_post` trả một hàm để `_do` bấm giờ (do_hieu_nang.py), nên hàm giả cũng phải trả hàm."""
    payload = []

    def _post(self, client, duong_dan, du_lieu, ma=200):
        return lambda: payload.append((duong_dan, du_lieu() if callable(du_lieu) else du_lieu))

    monkeypatch.setattr(do_hieu_nang.Command, "_get", lambda self, *a, **k: (lambda: None))
    monkeypatch.setattr(do_hieu_nang.Command, "_post", _post)
    return payload


def _pk_da_ghi(payload):
    return {cell['id'] for _, du_lieu in payload for cell in du_lieu.get('cells', [])}


def test_do_hieu_nang_goi_duong_json_thuc(bang_do, nguoi_dung, settings, tmp_path, monkeypatch):
    """AC-10.8 — Lệnh đo thực sự ghi JSON, không còn gọi các endpoint 409 cũ (TL-27)."""
    settings.DEBUG=True
    _tao_dong(bang_do,nguoi_dung['admin'],PERF_PREFIX,1000)
    monkeypatch.setattr(do_hieu_nang.Command,'_get',lambda *a,**k:lambda:None)
    # Xuất lớn không thuộc bài hồi quy đường ghi này.
    from forms_builder.services import export_service
    monkeypatch.setattr(export_service,'build_workbook',lambda *a,**k:type('Book',(),{'save':lambda *a:None})())
    call_command('do_hieu_nang',*THAM_SO)
    assert DataRecord.objects.filter(table=bang_do,data__ghi_chu__startswith='đo tải').exists()


def _anh_chup(pks):
    return list(DataRecord.all_objects.filter(pk__in=pks).order_by("pk").values_list("pk", "data", "style"))


def test_do_tinh_lai_co_ghi_that_va_kiem_ket_qua(bang_do, nguoi_dung):
    """AC-10.8 — Không chấm phép tính lại no-op: ô fixture bị làm cũ rồi được tính đúng."""
    from forms_builder.models import ColumnDef
    bang_do.workflow = ''
    bang_do.save(update_fields=['workflow'])
    ColumnDef.objects.create(table=bang_do, code='perf_double', name='Gấp đôi',
        field_type='decimal', is_computed=True, compute_op='add', compute_left='so_luong', compute_right='so_luong')
    row = DataRecord.objects.create(table=bang_do, department=bang_do.department,
        created_by=nguoi_dung['admin'], data={'ma_don':'PERF-RECOMPUTE', 'so_luong':2, 'perf_double':'4.00'})
    command = do_hieu_nang.Command()
    command.lan = 1
    command.ket_qua = []
    command._recompute(bang_do)
    row.refresh_from_db()
    assert row.data['perf_double'] == '4.00'
    assert len(command.ket_qua) == 1
    assert command.ket_qua[0].so_truy_van > 0


def test_do_hieu_nang_tu_choi_khi_debug_tat(bang_do, settings, tmp_path, django_assert_num_queries):
    """TL-98 · P0-16 — DEBUG tắt mà không ghi rõ `--dong-y-chay-that` thì `do_hieu_nang` từ chối ngay, trước
    mọi truy vấn, không ghi tệp báo cáo (như seed_perf, nap_khach_mau, du_lieu_mau)"""
    settings.DEBUG = False
    with django_assert_num_queries(0), pytest.raises(CommandError, match="DEBUG"):
        call_command("do_hieu_nang", *THAM_SO)
    assert not list(tmp_path.glob("perf/*.md"))


def test_do_hieu_nang_tu_choi_khi_khong_co_dong_gia(bang_do, nguoi_dung, settings, tmp_path, bo_do_that):
    """TL-98 · P0-16 — Bảng vận đơn chỉ có dòng thật, không có dòng PERF-* thì lệnh dừng trước khi đo, không
    dựng lệnh ghi nào, không đụng dòng thật (trước đây nó lấy 5.000 dòng mới nhất, dù là của khách thật)"""
    settings.DEBUG = True
    that = _tao_dong(bang_do, nguoi_dung["staff_vd"], "DH-", 1000, ghi_chu="Khách dặn giao sáng")
    truoc = _anh_chup(that)

    with pytest.raises(CommandError, match="PERF-"):
        call_command("do_hieu_nang", *THAM_SO)

    assert bo_do_that == []
    assert _anh_chup(that) == truoc
    assert not list(tmp_path.glob("perf/*.md"))


def test_do_hieu_nang_debug_tat_co_dong_y_chi_ghi_vao_dong_perf(bang_do, nguoi_dung, settings, tmp_path,
                                                                bo_do_that):
    """TL-98 · P0-16 — Ghi rõ `--dong-y-chay-that` thì qua được khoá DEBUG; mọi lệnh ghi (lưu ô, định dạng)
    chỉ trỏ vào dòng PERF-*, kể cả khi dòng thật mới hơn; dòng thật nguyên vẹn, có tệp báo cáo"""
    settings.DEBUG = False
    gia = _tao_dong(bang_do, nguoi_dung["admin"], PERF_PREFIX, 600)
    that = _tao_dong(bang_do, nguoi_dung["staff_vd"], "DH-", 500, ghi_chu="Khách dặn giao sáng")
    truoc = _anh_chup(that)

    call_command("do_hieu_nang", *THAM_SO, "--dong-y-chay-that")

    da_ghi = _pk_da_ghi(bo_do_that)
    assert da_ghi and da_ghi <= gia, f"ghi vào dòng không phải PERF-*: {sorted(da_ghi - gia)[:5]}"
    assert _anh_chup(that) == truoc
    assert list(tmp_path.glob("perf/*-don-le.md"))
