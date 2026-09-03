"""Nhập tệp Excel/CSV vào bảng động — FR-7.5, luồng bốn bước (docs/05 A4).

    1. `prepare`  — tải tệp lên: kiểm cỡ, loại thật, số dòng; dò hàng tiêu đề;
                    ánh xạ cột; lưu tệp và tạo tác vụ ở trạng thái *Chờ xác nhận*
    2. xem trước  — người dùng thấy cột nào khớp cột nào, cột nào bị bỏ qua
    3. `confirm`  — chuyển sang *Chờ xử lý* và đẩy vào hàng đợi
    4. `run`      — worker đọc lại tệp, ghi theo lô, báo tiến độ, liệt kê dòng lỗi

Luôn chạy nền, kể cả tệp nhỏ — một đường duy nhất, và trang tiến độ xử lý
luôn trường hợp worker chết (kien-truc.md: "Đang xử lý, sẽ thông báo khi xong").

Chưa có gì được ghi vào bảng trước bước 3. Dòng lỗi không chặn dòng hợp lệ
(AC-7.6); số dòng báo lỗi là **số hàng thật trong tệp Excel** để người dùng
mở tệp ra tìm được ngay.
"""
import logging
import uuid
from pathlib import Path

from django.conf import settings
from django.db import transaction

from core import excel
from core.constants import (
    IMPORT_ERROR_LIST_MAX, IMPORT_FILE_KINDS, IMPORT_MAX_ROWS, JobKind, JobStatus,
)
from core.exceptions import BusinessError
from core.models import BackgroundJob

from ..models import DataRecord, TableDef
from . import record_service

logger = logging.getLogger(__name__)

#: Thư mục tệp chờ nhập, tương đối so với STORAGE_DIR
IMPORT_SUBDIR = "uploads/imports"

#: Bí danh tiêu đề: tệp thật của công ty đặt tên cột bằng tiếng Anh hoặc
#: tên khác với bảng trong hệ thống. Khoá đã chuẩn hoá → tên kỹ thuật cột.
#: Chỉ áp khi bảng có cột mang tên kỹ thuật đó. Khai một chỗ (quy tắc 7).
HEADER_ALIASES = {
    "name": "ten_khach",
    "tên khách hàng": "ten_khach",
    "khách hàng": "ten_khach",
    "phone": "so_dien_thoai",
    "sđt": "so_dien_thoai",
    "điện thoại": "so_dien_thoai",
    "add": "dia_chi",
    "address": "dia_chi",
    "địa chỉ": "dia_chi",
    "city": "thanh_pho",
    "state": "bang",
    "zipcode": "zipcode",
    "zip": "zipcode",
    "mã bưu điện": "zipcode",
    "dấu thời gian": "ngay",
    "ngày lên đơn": "ngay",
    "giá tiền(cad)": "gia_tien",
    "giá tiền (cad)": "gia_tien",
    "giá tiền(usd)": "gia_tien",
    "giá tiền": "gia_tien",
    "hình thức thanh toán": "pttt",
    "cskh": "nguoi_ban",
    "sale/cskh": "nguoi_ban",
    "mkt": "mkt",
    "mua lại lần ?": "mua_lai",
    "mua lại lần": "mua_lai",
    "trạng thái vận đơn mita": "trang_thai_vc",
    "trạng thái vận đơn": "trang_thai_vc",
    "nhân viên vận đơn được giao": "nv_van_don",
    "nhân viên vận đơn": "nv_van_don",
    "trạng thái thanh toán": "trang_thai_tt",
    "ngày thanh toán": "ngay_tt",
    "tên người chuyển tiền": "nguoi_chuyen_tien",
    "nội dung - mã chuyển khoản": "bill",
    "đối soát kế toán": "doi_soat",
    "ghi chú": "ghi_chu",
    # Tệp thật gõ sai tên một sản phẩm; giữ bí danh để nhập không cần sửa tệp
    "kem chống nắnng": "sl_kem_chong_nang",
}

#: Tiêu đề cột số lượng trong tệp thật là "SL <tên sản phẩm>" hoặc chỉ tên
#: sản phẩm; cột trong bảng mang đúng tên sản phẩm. Bỏ tiền tố rồi khớp lại.
QUANTITY_PREFIXES = ("sl ", "số lượng ")


class Mapping:
    """Kết quả ánh xạ cột tệp → cột bảng."""

    def __init__(self):
        self.matched = {}      # chỉ số cột trong tệp → ColumnDef
        self.ignored = []      # (tên cột trong tệp, lý do)
        self.missing_required = []

    def as_summary(self):
        return {
            "mapping": [
                {"chi_so": j, "cot_tep": nhan, "cot_bang": cot.name, "code": cot.code}
                for j, (nhan, cot) in sorted(self.matched.items())
            ],
            "ignored": [{"cot_tep": nhan, "ly_do": ly_do} for nhan, ly_do in self.ignored],
        }


def map_columns(headers, columns):
    """Ghép từng tiêu đề trong tệp với một cột của bảng.

    Ưu tiên tên cột đúng, rồi tới bí danh. Cột tính sẵn không nhận dữ liệu
    (hệ thống tự tính), cột không có trong bảng bị bỏ qua kèm lý do — cả hai
    đều báo cho người dùng ở bước xem trước, không im lặng.
    """
    theo_ten = {excel.normalise_label(c.name): c for c in columns}
    theo_code = {c.code: c for c in columns}
    ket_qua = Mapping()
    da_dung = set()
    for j, nhan in enumerate(headers):
        if nhan in (None, ""):
            continue
        chuan = excel.normalise_label(nhan)
        cot = theo_ten.get(chuan) or theo_code.get(HEADER_ALIASES.get(chuan, ""))
        if cot is None:
            for tien_to in QUANTITY_PREFIXES:
                if chuan.startswith(tien_to):
                    cot = theo_ten.get(chuan[len(tien_to):].strip())
                    break
        if cot is None:
            ket_qua.ignored.append((str(nhan).strip(), "không có cột này trong bảng"))
            continue
        if cot.is_computed:
            ket_qua.ignored.append((str(nhan).strip(), "cột tính sẵn, hệ thống tự tính"))
            continue
        if cot.code in da_dung:
            ket_qua.ignored.append((str(nhan).strip(), f'trùng với cột "{cot.name}" đã khớp'))
            continue
        da_dung.add(cot.code)
        ket_qua.matched[j] = (str(nhan).strip(), cot)
    ket_qua.missing_required = [
        c for c in columns if c.required and not c.is_computed and c.code not in da_dung
    ]
    return ket_qua


def _dong_trong(hang, chi_so_cot):
    """Hàng không có giá trị ở cột nào đã ánh xạ thì coi như trống."""
    return all(hang[j] in (None, "") if j < len(hang) else True for j in chi_so_cot)


def _cac_dong(rows, header_idx, mapping):
    """Các dòng dữ liệu sau hàng tiêu đề: `(số hàng Excel, dict code → giá trị)`.

    Bỏ qua hàng trống. Hàng chỉ có một ô lạc (như hàng công thức đếm ngay
    dưới tiêu đề trong tệp thật) mà không có cột bắt buộc nào → cũng bỏ qua.
    """
    chi_so = list(mapping.matched.keys())
    bat_buoc = [j for j, (_, c) in mapping.matched.items() if c.required]
    ket_qua = []
    for i, hang in enumerate(rows[header_idx + 1:], start=header_idx + 2):
        if _dong_trong(hang, chi_so):
            continue
        co_gia_tri = [j for j in chi_so if j < len(hang) and hang[j] not in (None, "")]
        if len(co_gia_tri) < 2 and not any(j in co_gia_tri for j in bat_buoc):
            continue
        gia_tri = {
            cot.code: excel.coerce_cell(hang[j]) if j < len(hang) else None
            for j, (_, cot) in mapping.matched.items()
        }
        ket_qua.append((i, gia_tri))
    return ket_qua


def _phan_tich(nguon, kind, columns):
    """Đọc tệp, dò tiêu đề, ánh xạ. Dùng ở cả `prepare` lẫn `run`."""
    sheet = excel.read_table(nguon, kind, max_rows=IMPORT_MAX_ROWS)
    if not sheet.rows:
        raise excel.UploadRejected("Tệp không có dòng nào.")
    mong_doi = [c.name for c in columns] + list(HEADER_ALIASES.keys())
    header_idx, diem = excel.find_header_row(sheet.rows, mong_doi)
    if diem == 0:
        raise excel.UploadRejected(
            "Không tìm thấy hàng tiêu đề khớp cột nào của bảng trong 10 hàng đầu. "
            "Tiêu đề cột trong tệp phải trùng tên cột của bảng."
        )
    headers = [v if isinstance(v, str) else None for v in sheet.rows[header_idx]]
    mapping = map_columns(headers, columns)
    if mapping.missing_required:
        raise excel.UploadRejected(
            "Tệp thiếu cột bắt buộc: "
            + ", ".join(c.name for c in mapping.missing_required)
        )
    cac_dong = _cac_dong(sheet.rows, header_idx, mapping)
    if sheet.truncated or len(cac_dong) > IMPORT_MAX_ROWS:
        raise excel.UploadRejected(
            f"Tệp có hơn {IMPORT_MAX_ROWS:,} dòng dữ liệu — vượt giới hạn mỗi lần nhập. "
            "Chia nhỏ tệp rồi nhập nhiều lần.".replace(",", ".")
        )
    return sheet, header_idx, mapping, cac_dong


def _luu_tep(upload, kind):
    """Lưu tệp tải lên vào storage; trả đường dẫn tương đối."""
    thu_muc = Path(settings.STORAGE_DIR) / IMPORT_SUBDIR
    thu_muc.mkdir(parents=True, exist_ok=True)
    ten = f"{uuid.uuid4().hex}.{kind}"
    upload.seek(0)
    with open(thu_muc / ten, "wb") as f:
        for doan in upload.chunks():
            f.write(doan)
    return f"{IMPORT_SUBDIR}/{ten}"


def _duong_dan_tuyet_doi(rel):
    return Path(settings.STORAGE_DIR) / rel


def _mau(cac_dong, mapping, n=5):
    """Vài dòng đầu để người dùng đối chiếu ở bước xem trước."""
    return [
        [_chuoi(gia_tri.get(cot.code)) for _, cot in sorted(mapping.matched.values(), key=lambda x: x[0])]
        for _, gia_tri in cac_dong[:n]
    ]


def _chuoi(v):
    return "" if v is None else str(v)


# ══ BỐN BƯỚC ══════════════════════════════════════════════════════

def prepare(table, upload, *, actor, request=None):
    """Bước 1 — kiểm tệp, ánh xạ cột, tạo tác vụ *Chờ xác nhận*. Chưa ghi gì."""
    excel.check_size(upload.size)
    kind = excel.sniff_kind(upload, declared_name=upload.name, allowed=IMPORT_FILE_KINDS)
    columns = list(table.columns.order_by("order", "id"))
    sheet, header_idx, mapping, cac_dong = _phan_tich(upload, kind, columns)

    rel = _luu_tep(upload, kind)
    tom_tat = {
        "file_name": upload.name, "kind": kind, "sheet": sheet.sheet_name,
        "header_row": header_idx + 1,
        "sample": _mau(cac_dong, mapping),
        **mapping.as_summary(),
    }
    job = BackgroundJob.objects.create(
        kind=JobKind.IMPORT, status=JobStatus.DRAFT, created_by=actor,
        title=f"Nhập tệp {upload.name} vào bảng {table.name}",
        target_type="table", target_id=table.code,
        input_path=rel, total=len(cac_dong), summary=tom_tat,
    )
    return job


def confirm(job, *, actor, request=None):
    """Bước 3 — người dùng xác nhận: chuyển *Chờ xử lý* và đẩy vào hàng đợi."""
    if job.status != JobStatus.DRAFT:
        raise BusinessError("Tác vụ này đã được xác nhận rồi.")
    job.status = JobStatus.PENDING
    job.save(update_fields=["status", "updated_at"])
    from ..tasks import chay_tac_vu_nhap

    _day_vao_hang_doi(chay_tac_vu_nhap, job.pk)
    return job


def _day_vao_hang_doi(task, job_id):
    """Đẩy tác vụ sau khi giao dịch hiện tại ghi xong — worker đọc trước khi
    commit sẽ thấy trạng thái cũ và bỏ qua. Chạy eager (kiểm thử) thì gọi
    thẳng: cùng luồng, cùng giao dịch, không có gì để chờ."""
    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        task.delay(job_id)
    else:
        transaction.on_commit(lambda: task.delay(job_id))


def run(job_id):
    """Bước 4 — worker chạy. Đọc lại tệp, ghi theo lô, báo tiến độ, tổng kết."""
    job = BackgroundJob.objects.filter(pk=job_id, kind=JobKind.IMPORT).first()
    if job is None or job.status != JobStatus.PENDING:
        return None
    job.mark_running()
    try:
        table = TableDef.objects.get(code=job.target_id)
        columns = list(table.columns.order_by("order", "id"))
        kind = job.summary.get("kind")
        duong_dan = _duong_dan_tuyet_doi(job.input_path)
        with open(duong_dan, "rb") as f:
            _, _, mapping, cac_dong = _phan_tich(f, kind, columns)

        job.set_progress(0, len(cac_dong))
        ket_qua = record_service.create_records_bulk(
            table, [gia_tri for _, gia_tri in cac_dong],
            actor=job.created_by, columns=columns,
            row_numbers=[so for so, _ in cac_dong],
            on_progress=lambda n: job.set_progress(n),
        )
        job.set_progress(len(cac_dong))
        job.mark_done(summary={
            "created": ket_qua.created,
            "error_count": len(ket_qua.errors),
            "errors": [[so, loi] for so, loi in ket_qua.errors[:IMPORT_ERROR_LIST_MAX]],
        })
        duong_dan.unlink(missing_ok=True)
    except BusinessError as loi:
        job.mark_failed(str(loi))
    except Exception:
        logger.exception("Tác vụ nhập #%s thất bại", job.pk)
        job.mark_failed(
            "Nhập thất bại vì lỗi hệ thống. Người vận hành đã được ghi nhận, "
            "hãy thử lại sau."
        )
    return job


def job_for(user, pk, table=None):
    """Tác vụ nhập trong phạm vi người xem, đúng bảng nếu có. Không có → None."""
    ds = BackgroundJob.objects.in_scope(user).filter(pk=pk, kind=JobKind.IMPORT)
    if table is not None:
        ds = ds.filter(target_type="table", target_id=table.code)
    return ds.first()


def record_count(table):
    """Số dòng hiện có, cho màn hình xem trước biết bảng đang lớn cỡ nào."""
    return DataRecord.objects.filter(table=table).count()
