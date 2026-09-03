"""Sao lưu và phục hồi cơ sở dữ liệu — docs/03 mục 8, NFR-15, NFR-19, NFR-20.

Cách làm cố ý đơn giản: `pg_dump --format=custom` ra một tệp, giữ tối đa
`BACKUP_KEEP` bản gần nhất trong `BACKUP_DIR`. Ba điều bắt buộc:

- **Mật khẩu đi qua biến môi trường `PGPASSWORD`**, không nằm trên dòng lệnh
  (lộ qua `ps`) và không bao giờ vào nhật ký hay thư cảnh báo (điều cấm 6).
- **Ghi ra tệp `.part` rồi mới đổi tên** — không bao giờ có một tệp trông như
  bản sao lưu mà thật ra mới ghi được nửa chừng. Tệp phải bắt đầu bằng chữ ký
  `PGDMP` và lớn hơn 1 KB mới được tính.
- **Thất bại thì không im lặng**: tác vụ FAILED, một dòng nhật ký hoạt động
  "THẤT BẠI", và thư cho người vận hành.

Mỗi lần chạy — thành công hay không — đều là một `BackgroundJob` loại BACKUP,
nên màn hình Tổng quan của Admin và trang Tác vụ nền đều thấy được.

**Bản sao lưu chưa từng được phục hồi thử thì chưa được tính là bản sao lưu**
(docs/03 mục 8) — vì thế có `run_restore`, và lệnh `phuc_hoi` bắt xác nhận rõ.
"""
import logging
import os
import subprocess
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from ..alerts import bao_nguoi_van_hanh
from ..audit import record
from ..constants import BACKUP_KEEP, AuditAction, JobKind, JobStatus
from ..exceptions import BusinessError
from ..excel import format_size
from ..models import BackgroundJob

logger = logging.getLogger(__name__)

BACKUP_PREFIX = "knjsc-"
BACKUP_SUFFIX = ".dump"
PART_SUFFIX = ".part"
#: Chữ ký đầu tệp của định dạng custom của pg_dump
PGDMP_MAGIC = b"PGDMP"
#: Một bản sao lưu của cơ sở dữ liệu thật không thể nhỏ hơn mức này
BACKUP_MIN_BYTES = 1024
#: pg_dump vài chục nghìn dòng mất vài giây; quá mức này là có chuyện
BACKUP_TIMEOUT_SECONDS = 30 * 60


class BackupError(BusinessError):
    """Sao lưu hoặc phục hồi không thành — thông báo đã lọc mật khẩu."""


def _db():
    return settings.DATABASES["default"]


def backup_dir():
    return Path(settings.BACKUP_DIR)


def _connection_args():
    db = _db()
    return [
        "--host", str(db.get("HOST") or "localhost"),
        "--port", str(db.get("PORT") or "5432"),
        "--username", str(db.get("USER") or ""),
        "--dbname", str(db["NAME"]),
    ]


def command_env():
    """Biến môi trường cho pg_dump/pg_restore. Mật khẩu ở đây, không ở argv."""
    env = os.environ.copy()
    env["PGPASSWORD"] = str(_db().get("PASSWORD") or "")
    return env


def pg_dump_command(target):
    return [
        "pg_dump", "--format=custom", "--no-password",
        *_connection_args(), "--file", str(target),
    ]


def pg_restore_command(source):
    """Phục hồi **đè lên** cơ sở dữ liệu hiện tại — `--clean` xoá bảng cũ trước."""
    return [
        "pg_restore", "--no-password", "--clean", "--if-exists", "--no-owner",
        "--no-privileges", *_connection_args(), str(source),
    ]


def scrub(text):
    """Không để mật khẩu lọt vào thông báo, dù pg_dump có in nó ra."""
    text = str(text or "")
    mat_khau = str(_db().get("PASSWORD") or "")
    if mat_khau:
        text = text.replace(mat_khau, "***")
    return text


def _gon_loi(stderr):
    dong = [d.strip() for d in str(stderr or "").splitlines() if d.strip()]
    return scrub(" | ".join(dong[-3:]) if dong else "không có thông tin lỗi")


def backup_name(luc=None):
    luc = luc or timezone.localtime()
    return f"{BACKUP_PREFIX}{luc:%Y%m%d-%H%M%S}{BACKUP_SUFFIX}"


def list_backups():
    """Các bản sao lưu hợp lệ, **mới nhất trước**. Tên chứa thời điểm nên sắp
    theo tên là sắp theo thời gian; tệp `.part` không được tính."""
    thu_muc = backup_dir()
    if not thu_muc.exists():
        return []
    return sorted(
        (t for t in thu_muc.iterdir()
         if t.is_file() and t.name.startswith(BACKUP_PREFIX) and t.name.endswith(BACKUP_SUFFIX)),
        key=lambda t: t.name, reverse=True,
    )


def rotate(keep=BACKUP_KEEP):
    """Giữ `keep` bản mới nhất, xoá phần còn lại — NFR-15, AC-10.6.
    Trả về tên các bản đã xoá."""
    da_xoa = []
    for tep in list_backups()[keep:]:
        tep.unlink(missing_ok=True)
        da_xoa.append(tep.name)
    return da_xoa


def last_backup():
    """Lần sao lưu gần nhất (thành công hay không) để Tổng quan hiện."""
    return BackgroundJob.objects.filter(kind=JobKind.BACKUP).order_by("-created_at").first()


def verify_file(duong_dan):
    """Tệp phải có thật, đủ lớn và đúng chữ ký `PGDMP`."""
    duong_dan = Path(duong_dan)
    if not duong_dan.exists():
        raise BackupError("pg_dump không tạo ra tệp nào.")
    co = duong_dan.stat().st_size
    if co < BACKUP_MIN_BYTES:
        raise BackupError(f"Tệp sao lưu chỉ {format_size(co)} — quá nhỏ, không thể là bản đầy đủ.")
    with open(duong_dan, "rb") as f:
        dau = f.read(len(PGDMP_MAGIC))
    if dau != PGDMP_MAGIC:
        raise BackupError("Tệp sao lưu không đúng định dạng pg_dump (thiếu chữ ký PGDMP).")
    return co


def run_backup(*, actor=None, runner=None, title="Sao lưu hằng đêm"):
    """Sao lưu một lần. Luôn trả về `BackgroundJob`, không ném ra ngoài.

    `runner` thay được để kiểm thử không cần pg_dump thật; tra lúc gọi chứ
    không lúc khai báo, để vá `subprocess.run` cũng có tác dụng.
    """
    runner = runner or subprocess.run
    job = BackgroundJob.objects.create(
        kind=JobKind.BACKUP, status=JobStatus.PENDING, created_by=actor,
        title=title, target_type="database", target_id=str(_db()["NAME"])[:80],
    )
    job.mark_running()
    thu_muc = backup_dir()
    ten = backup_name()
    tam = thu_muc / (ten + PART_SUFFIX)
    try:
        thu_muc.mkdir(parents=True, exist_ok=True)
        try:
            kq = runner(
                pg_dump_command(tam), env=command_env(),
                capture_output=True, text=True, timeout=BACKUP_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as loi:
            raise BackupError(
                "Không tìm thấy lệnh pg_dump trong container — image phải cài postgresql-client."
            ) from loi
        except subprocess.TimeoutExpired as loi:
            raise BackupError(f"pg_dump chạy quá {BACKUP_TIMEOUT_SECONDS // 60} phút, đã dừng.") from loi
        if kq.returncode != 0:
            raise BackupError(f"pg_dump trả mã lỗi {kq.returncode}: {_gon_loi(kq.stderr)}")
        co = verify_file(tam)
        tam.rename(thu_muc / ten)
        da_xoa = rotate()
        con_lai = len(list_backups())
        job.mark_done(summary={
            "file_name": ten, "bytes": co, "size": format_size(co),
            "kept": con_lai, "rotated": da_xoa,
        })
        record(
            AuditAction.BACKUP, actor=actor, target=("backup", ten),
            detail=f"Sao lưu thành công: {ten} ({format_size(co)}), đang giữ {con_lai} bản"
                   + (f", xoá {len(da_xoa)} bản cũ" if da_xoa else ""),
        )
        logger.info("Sao lưu xong: %s (%s)", ten, format_size(co))
    except (BackupError, OSError) as loi:
        tam.unlink(missing_ok=True)
        thong_bao = scrub(loi)
        job.mark_failed(thong_bao)
        # Nhật ký hoạt động chỉ ghi sự kiện; lý do (có thể chứa chữ "password"
        # từ pg_dump) nằm ở tác vụ và thư — bộ lọc nhật ký sẽ lược nó đi
        record(
            AuditAction.BACKUP, actor=actor, target=("backup", "that-bai"),
            detail=f"Sao lưu THẤT BẠI — xem lý do ở tác vụ #{job.pk}",
        )
        logger.error("Sao lưu thất bại: %s", thong_bao)
        bao_nguoi_van_hanh(
            "[KN JSC] Sao lưu THẤT BẠI",
            "Sao lưu cơ sở dữ liệu không thành công.\n\n"
            f"Lý do: {thong_bao}\n\n"
            f"Tác vụ #{job.pk}. Bản gần nhất còn dùng được: "
            + (list_backups()[0].name if list_backups() else "KHÔNG CÓ BẢN NÀO")
            + "\n\nChạy lại bằng tay: scripts/backup.sh",
        )
    return job


def resolve_backup(ten=None):
    """Tệp sao lưu theo tên (hoặc đường dẫn); không ghi tên thì lấy bản mới nhất."""
    if not ten:
        cac_ban = list_backups()
        if not cac_ban:
            raise BackupError("Chưa có bản sao lưu nào trong " + str(backup_dir()))
        return cac_ban[0]
    duong_dan = Path(ten)
    if not duong_dan.is_absolute():
        duong_dan = backup_dir() / ten
    if not duong_dan.exists():
        raise BackupError(f"Không thấy tệp {duong_dan}")
    return duong_dan


def run_restore(duong_dan, *, actor=None, runner=None):
    """Phục hồi **đè** cơ sở dữ liệu từ một bản sao lưu — NFR-10.

    Chỉ gọi từ lệnh `phuc_hoi` sau khi người vận hành xác nhận. Kiểm tệp trước
    khi đụng vào cơ sở dữ liệu; ghi nhật ký cả khi thành công lẫn thất bại.
    """
    runner = runner or subprocess.run
    duong_dan = Path(duong_dan)
    verify_file(duong_dan)
    try:
        kq = runner(
            pg_restore_command(duong_dan), env=command_env(),
            capture_output=True, text=True, timeout=BACKUP_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as loi:
        raise BackupError("Không tìm thấy lệnh pg_restore — image phải cài postgresql-client.") from loi
    if kq.returncode != 0:
        thong_bao = f"pg_restore trả mã lỗi {kq.returncode}: {_gon_loi(kq.stderr)}"
        record(AuditAction.BACKUP, actor=actor, target=("restore", duong_dan.name),
               detail=f"Phục hồi THẤT BẠI từ {duong_dan.name}")
        raise BackupError(thong_bao)
    record(AuditAction.BACKUP, actor=actor, target=("restore", duong_dan.name),
           detail=f"Phục hồi thành công từ {duong_dan.name}")
    return duong_dan
