"""Sao lưu, phục hồi và các tác vụ định kỳ — docs/03 mục 8 và 9.

Phần lớn bài chạy với `pg_dump` giả (một hàm thay `subprocess.run`) để kiểm
đúng logic: xoay vòng, kiểm tệp, thất bại không im lặng, mật khẩu không lộ.
Một bài `cham` chạy pg_dump thật nếu máy có.
"""
import shutil
import subprocess
from datetime import timedelta
from pathlib import Path
from unittest import mock

import pytest
from django.core import mail
from django.core.management import CommandError, call_command
from django.utils import timezone

from core.constants import BACKUP_KEEP, AuditAction, JobKind, JobStatus
from core.models import AuditLog, BackgroundJob
from core.services import backup_service

pytestmark = pytest.mark.django_db

MAT_KHAU_GIA = "mat-khau-rat-bi-mat-2026"


@pytest.fixture
def thu_muc_sao_luu(settings, tmp_path):
    settings.BACKUP_DIR = tmp_path / "backups"
    return settings.BACKUP_DIR


@pytest.fixture
def db_gia(monkeypatch):
    """Thông số kết nối giả để kiểm mật khẩu không lộ — không đụng CSDL thật."""
    monkeypatch.setattr(backup_service, "_db", lambda: {
        "NAME": "knjsc_kiem", "USER": "knjsc", "PASSWORD": MAT_KHAU_GIA,
        "HOST": "db", "PORT": "5432",
    })


def _pg_dump_gia(noi_dung=b"PGDMP" + b"\0" * 4096, returncode=0, stderr=""):
    """Một `subprocess.run` giả: ghi tệp ở tham số `--file` rồi trả mã thoát."""
    def _chay(cmd, **kw):
        if returncode == 0 and "--file" in cmd:
            Path(cmd[cmd.index("--file") + 1]).write_bytes(noi_dung)
        return subprocess.CompletedProcess(cmd, returncode, stdout="", stderr=stderr)
    return _chay


def _tao_ban(thu_muc, n, bat_dau=1):
    thu_muc.mkdir(parents=True, exist_ok=True)
    for i in range(bat_dau, bat_dau + n):
        (thu_muc / f"knjsc-202608{i:02d}-020000.dump").write_bytes(b"PGDMP" + b"\0" * 2000)


# ══ Xoay vòng ═══════════════════════════════════════════════════════

def test_chi_giu_30_ban_gan_nhat(thu_muc_sao_luu):
    """AC-10.6 — Bản sao lưu tự động chỉ giữ tối đa 30 bản gần nhất, bản cũ nhất bị xoá trước"""
    _tao_ban(thu_muc_sao_luu, 35, bat_dau=1)          # 01 → 35, "35" mới nhất
    (thu_muc_sao_luu / "knjsc-20260800-000000.dump.part").write_bytes(b"do dang")
    (thu_muc_sao_luu / "ghi-chu.txt").write_text("không phải bản sao lưu")

    da_xoa = backup_service.rotate()

    con = [t.name for t in backup_service.list_backups()]
    assert len(con) == BACKUP_KEEP == 30
    assert sorted(da_xoa) == [f"knjsc-202608{i:02d}-020000.dump" for i in range(1, 6)]
    assert con[0] == "knjsc-20260835-020000.dump" and con[-1] == "knjsc-20260806-020000.dump"
    # Không đụng vào thứ không phải bản sao lưu
    assert (thu_muc_sao_luu / "ghi-chu.txt").exists()
    assert (thu_muc_sao_luu / "knjsc-20260800-000000.dump.part").exists()


def test_sao_luu_xong_thi_xoay_vong_luon(thu_muc_sao_luu, db_gia):
    """AC-10.6 — Chạy sao lưu khi đã đủ 30 bản thì bản mới vào, bản cũ nhất ra"""
    _tao_ban(thu_muc_sao_luu, 30)
    job = backup_service.run_backup(runner=_pg_dump_gia())
    assert job.status == JobStatus.DONE
    assert job.summary["rotated"] == ["knjsc-20260801-020000.dump"]
    assert job.summary["kept"] == 30
    assert len(backup_service.list_backups()) == 30


# ══ Thành công ═════════════════════════════════════════════════════

def test_sao_luu_thanh_cong_ghi_tep_va_nhat_ky(thu_muc_sao_luu, db_gia):
    """NFR-19 — Sao lưu thành công: có tệp đúng chữ ký, không còn tệp .part, tác vụ DONE, nhật ký BACKUP"""
    job = backup_service.run_backup(runner=_pg_dump_gia())
    assert job.status == JobStatus.DONE and job.kind == JobKind.BACKUP
    ten = job.summary["file_name"]
    assert ten.startswith("knjsc-") and ten.endswith(".dump")
    assert (thu_muc_sao_luu / ten).read_bytes()[:5] == b"PGDMP"
    assert not list(thu_muc_sao_luu.glob("*.part"))
    nk = AuditLog.objects.filter(action=AuditAction.BACKUP).latest("created_at")
    assert "thành công" in nk.detail and ten in nk.detail
    assert len(mail.outbox) == 0, "thành công thì không làm phiền người vận hành"


def test_mat_khau_qua_bien_moi_truong_khong_qua_dong_lenh(thu_muc_sao_luu, db_gia):
    """Điều cấm 6 — Mật khẩu chỉ nằm trong PGPASSWORD, không trên dòng lệnh pg_dump/pg_restore"""
    lenh = backup_service.pg_dump_command(thu_muc_sao_luu / "x.dump.part")
    assert MAT_KHAU_GIA not in " ".join(lenh)
    assert "--no-password" in lenh and "--format=custom" in lenh
    assert backup_service.command_env()["PGPASSWORD"] == MAT_KHAU_GIA
    lenh_phuc_hoi = backup_service.pg_restore_command(thu_muc_sao_luu / "x.dump")
    assert MAT_KHAU_GIA not in " ".join(lenh_phuc_hoi)
    assert "--clean" in lenh_phuc_hoi and "--if-exists" in lenh_phuc_hoi


# ══ Thất bại — không được im lặng ══════════════════════════════════

def test_pg_dump_hong_thi_bao_nguoi_van_hanh_khong_lo_mat_khau(thu_muc_sao_luu, db_gia):
    """NFR-19 — pg_dump thất bại: tác vụ FAILED, nhật ký THẤT BẠI, thư cảnh báo; mật khẩu không lọt vào đâu"""
    _tao_ban(thu_muc_sao_luu, 2)
    stderr = f"pg_dump: error: connection failed\npassword {MAT_KHAU_GIA} rejected"
    job = backup_service.run_backup(runner=_pg_dump_gia(returncode=1, stderr=stderr))

    assert job.status == JobStatus.FAILED
    assert "mã lỗi 1" in job.error and "connection failed" in job.error
    assert MAT_KHAU_GIA not in job.error
    nk = AuditLog.objects.filter(action=AuditAction.BACKUP).latest("created_at")
    assert "THẤT BẠI" in nk.detail and MAT_KHAU_GIA not in nk.detail
    assert len(mail.outbox) == 1
    thu = mail.outbox[0]
    assert "THẤT BẠI" in thu.subject
    assert "knjsc-20260802-020000.dump" in thu.body, "thư phải nói bản gần nhất còn dùng được"
    assert MAT_KHAU_GIA not in thu.body
    assert not list(thu_muc_sao_luu.glob("*.part"))
    assert len(backup_service.list_backups()) == 2, "thất bại thì không xoay vòng, không mất bản cũ"


def test_tep_qua_nho_hoac_sai_chu_ky_khong_duoc_tinh(thu_muc_sao_luu, db_gia):
    """NFR-19 — pg_dump "thành công" nhưng tệp rỗng hoặc sai định dạng thì vẫn là thất bại"""
    job = backup_service.run_backup(runner=_pg_dump_gia(noi_dung=b"PGDMP"))
    assert job.status == JobStatus.FAILED and "quá nhỏ" in job.error
    job = backup_service.run_backup(runner=_pg_dump_gia(noi_dung=b"KHONG" + b"\0" * 4096))
    assert job.status == JobStatus.FAILED and "PGDMP" in job.error
    assert backup_service.list_backups() == []
    assert not list(thu_muc_sao_luu.glob("*.part"))
    assert len(mail.outbox) == 2


def test_thieu_pg_dump_trong_container_bao_ro(thu_muc_sao_luu, db_gia):
    """NFR-19 — Image thiếu postgresql-client thì thông báo nói thẳng, không trả lỗi hệ thống mù mờ"""
    def _khong_co(cmd, **kw):
        raise FileNotFoundError("pg_dump")
    job = backup_service.run_backup(runner=_khong_co)
    assert job.status == JobStatus.FAILED and "postgresql-client" in job.error
    assert len(mail.outbox) == 1


def test_tac_vu_hang_dem_goi_dung_dich_vu(thu_muc_sao_luu, db_gia):
    """NFR-19 — Tác vụ Celery hằng đêm chạy qua backup_service, trả trạng thái tác vụ"""
    from core.tasks import sao_luu_hang_dem

    with mock.patch.object(backup_service, "run_backup", wraps=backup_service.run_backup) as goi:
        with mock.patch.object(subprocess, "run", _pg_dump_gia()):
            assert sao_luu_hang_dem.delay().get() == JobStatus.DONE
    assert goi.call_count == 1
    assert BackgroundJob.objects.filter(kind=JobKind.BACKUP, status=JobStatus.DONE).count() == 1


# ══ Phục hồi ═══════════════════════════════════════════════════════

def test_phuc_hoi_bat_xac_nhan(thu_muc_sao_luu, db_gia, capsys):
    """NFR-10 — Lệnh phục hồi không có cờ xác nhận thì chỉ liệt kê, không đụng cơ sở dữ liệu"""
    _tao_ban(thu_muc_sao_luu, 3)
    goi = mock.Mock(side_effect=_pg_dump_gia())
    with mock.patch.object(subprocess, "run", goi):
        call_command("phuc_hoi")
    assert goi.call_count == 0
    ra = capsys.readouterr().out
    assert "knjsc-20260803-020000.dump" in ra and "--toi-chac-chan" in ra


def test_phuc_hoi_co_xac_nhan_chay_pg_restore_va_ghi_nhat_ky(thu_muc_sao_luu, db_gia):
    """NFR-10 — Có cờ xác nhận thì pg_restore chạy đè lên CSDL với bản được chọn và ghi nhật ký"""
    _tao_ban(thu_muc_sao_luu, 3)
    goi = mock.Mock(side_effect=_pg_dump_gia())
    with mock.patch.object(subprocess, "run", goi):
        call_command("phuc_hoi", "knjsc-20260802-020000.dump", "--toi-chac-chan")
    lenh = goi.call_args.args[0]
    assert lenh[0] == "pg_restore" and lenh[-1].endswith("knjsc-20260802-020000.dump")
    assert goi.call_args.kwargs["env"]["PGPASSWORD"] == MAT_KHAU_GIA
    nk = AuditLog.objects.filter(action=AuditAction.BACKUP).latest("created_at")
    assert "Phục hồi thành công" in nk.detail


def test_phuc_hoi_tep_khong_co_thi_bao_loi(thu_muc_sao_luu, db_gia):
    """NFR-10 — Chưa có bản nào, hoặc tên sai, thì lệnh báo lỗi rõ và không chạy gì"""
    with pytest.raises(CommandError, match="Chưa có bản sao lưu"):
        call_command("phuc_hoi", "--toi-chac-chan")
    _tao_ban(thu_muc_sao_luu, 1)
    with pytest.raises(CommandError, match="Không thấy tệp"):
        call_command("phuc_hoi", "khong-co.dump", "--toi-chac-chan")


def test_lenh_sao_luu_bang_tay(thu_muc_sao_luu, db_gia, capsys):
    """NFR-19 — Lệnh `sao_luu` chạy được bằng tay, thất bại thì thoát mã 1"""
    with mock.patch.object(subprocess, "run", _pg_dump_gia()):
        call_command("sao_luu")
    assert "Đã sao lưu" in capsys.readouterr().out
    with mock.patch.object(subprocess, "run", _pg_dump_gia(returncode=2, stderr="hong")):
        with pytest.raises(SystemExit):
            call_command("sao_luu")


# ══ Phục hồi gặp lỗi — TL-97 · P0-15 ═══════════════════════════════

def _nhat_ky_phuc_hoi():
    return AuditLog.objects.filter(action=AuditAction.BACKUP, target_type="restore").order_by("-pk").first()


def test_phuc_hoi_qua_gio_bao_loi_tieng_viet_va_ghi_nhat_ky_that_bai(thu_muc_sao_luu, db_gia):
    """NFR-10 — pg_restore chạy quá giờ thì báo lỗi tiếng Việt (không traceback), có dòng nhật ký "Phục hồi THẤT BẠI",
    không lộ mật khẩu (TL-97)"""
    _tao_ban(thu_muc_sao_luu, 1)
    tep = backup_service.resolve_backup()

    def _qua_gio(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, backup_service.BACKUP_TIMEOUT_SECONDS)

    with pytest.raises(backup_service.BackupError, match="quá 30 phút") as loi:
        backup_service.run_restore(tep, runner=_qua_gio)
    nk = _nhat_ky_phuc_hoi()
    assert nk is not None and "Phục hồi THẤT BẠI" in nk.detail and nk.target_id == tep.name
    assert MAT_KHAU_GIA not in str(loi.value) and MAT_KHAU_GIA not in nk.detail


def test_phuc_hoi_thieu_pg_restore_ghi_nhat_ky_that_bai(thu_muc_sao_luu, db_gia):
    """NFR-10 — Máy thiếu pg_restore thì báo rõ phải cài postgresql-client và vẫn ghi "Phục hồi THẤT BẠI" (TL-97)"""
    _tao_ban(thu_muc_sao_luu, 1)

    def _thieu(cmd, **kw):
        raise FileNotFoundError("pg_restore")

    with pytest.raises(backup_service.BackupError, match="postgresql-client"):
        backup_service.run_restore(backup_service.resolve_backup(), runner=_thieu)
    assert "Phục hồi THẤT BẠI" in _nhat_ky_phuc_hoi().detail


def test_phuc_hoi_tep_hong_khong_dung_vao_csdl_va_ghi_nhat_ky(thu_muc_sao_luu, db_gia):
    """NFR-10 — Tệp sao lưu hỏng (sai chữ ký) bị từ chối trước khi đụng cơ sở dữ liệu, vẫn có dòng nhật ký (TL-97)"""
    thu_muc_sao_luu.mkdir(parents=True, exist_ok=True)
    tep = thu_muc_sao_luu / "knjsc-20260801-020000.dump"
    tep.write_bytes(b"KHONG" + b"\0" * 4096)
    goi = mock.Mock(side_effect=_pg_dump_gia())
    with pytest.raises(backup_service.BackupError, match="PGDMP"):
        backup_service.run_restore(tep, runner=goi)
    assert goi.call_count == 0
    assert "Phục hồi THẤT BẠI" in _nhat_ky_phuc_hoi().detail


def test_lenh_phuc_hoi_qua_gio_bao_command_error_khong_traceback(thu_muc_sao_luu, db_gia):
    """NFR-10 — Lệnh `phuc_hoi` quá giờ thì kết thúc bằng câu tiếng Việt "Phục hồi THẤT BẠI", không traceback (TL-97)"""
    _tao_ban(thu_muc_sao_luu, 2)
    qua_gio = subprocess.TimeoutExpired("pg_restore", backup_service.BACKUP_TIMEOUT_SECONDS)
    with mock.patch.object(subprocess, "run", side_effect=qua_gio):
        with pytest.raises(CommandError, match="Phục hồi THẤT BẠI.*quá 30 phút") as loi:
            call_command("phuc_hoi", "knjsc-20260802-020000.dump", "--toi-chac-chan")
    assert MAT_KHAU_GIA not in str(loi.value)


def test_lenh_phuc_hoi_chay_tron_mot_giao_dich(db_gia):
    """NFR-10 — pg_restore chạy trọn trong một giao dịch: hỏng giữa chừng thì cơ sở dữ liệu giữ nguyên, không để dở
    (`--single-transaction`, đã duyệt cùng kế hoạch P0; TL-97)"""
    lenh = backup_service.pg_restore_command(Path("/tmp/x.dump"))
    assert "--single-transaction" in lenh and lenh[-1] == "/tmp/x.dump" and MAT_KHAU_GIA not in " ".join(lenh)


def test_pg_dump_qua_gio_thi_that_bai_co_nhat_ky(thu_muc_sao_luu, db_gia):
    """NFR-19 — pg_dump quá giờ thì tác vụ THẤT BẠI, có nhật ký và thư, không để tệp dở (bài khoá, TL-97)"""
    def _qua_gio(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, backup_service.BACKUP_TIMEOUT_SECONDS)

    job = backup_service.run_backup(runner=_qua_gio)
    assert job.status == JobStatus.FAILED and "quá 30 phút" in job.error
    assert "THẤT BẠI" in AuditLog.objects.filter(action=AuditAction.BACKUP).latest("pk").detail
    assert len(mail.outbox) == 1 and not list(thu_muc_sao_luu.glob("*.part"))


# ══ Tác vụ định kỳ khác ═══════════════════════════════════════════

def test_tac_vu_cho_qua_15_phut_bi_danh_dau_ket(nguoi_dung):
    """AC-9.2 — Tác vụ chờ quá 15 phút không ai nhận → STALE, một dòng nhật ký, thư cảnh báo"""
    from core.tasks import danh_dau_tac_vu_ket

    ket = BackgroundJob.objects.create(
        kind=JobKind.EXPORT, status=JobStatus.PENDING, created_by=nguoi_dung["manager_sale"],
        title="Xuất bảng lớn",
    )
    BackgroundJob.objects.filter(pk=ket.pk).update(updated_at=timezone.now() - timedelta(minutes=20))
    moi = BackgroundJob.objects.create(kind=JobKind.EXPORT, status=JobStatus.PENDING, title="Vừa tạo")

    assert danh_dau_tac_vu_ket.delay().get() == 1
    ket.refresh_from_db()
    moi.refresh_from_db()
    assert ket.status == JobStatus.STALE and "worker" in ket.error
    assert moi.status == JobStatus.PENDING
    assert AuditLog.objects.filter(target_type="job", target_id=str(ket.pk)).exists()
    assert len(mail.outbox) == 1 and "kẹt" in mail.outbox[0].subject


@pytest.mark.parametrize("kind", [JobKind.RECOMPUTE, JobKind.IMPORT, JobKind.EXPORT, JobKind.BACKUP])
def test_tac_vu_dang_chay_im_lang_qua_nguong_bi_danh_dau_ket(nguoi_dung, kind):
    """AC-9.2 — Tác vụ ĐANG CHẠY mà không có tiến độ quá ngưỡng (worker chết giữa chừng — TL-23) → STALE kèm
    lời báo, giữ tiến độ đã làm, một dòng nhật ký, thư cảnh báo; tác vụ còn nhịp trong ngưỡng không bị đụng"""
    from core.constants import JOB_RUNNING_STALE_MINUTES, JOB_RUNNING_STALE_MINUTES_BACKUP
    from core.tasks import danh_dau_tac_vu_ket

    nguong = JOB_RUNNING_STALE_MINUTES_BACKUP if kind == JobKind.BACKUP else JOB_RUNNING_STALE_MINUTES
    ket, con_song = (BackgroundJob.objects.create(
        kind=kind, status=JobStatus.RUNNING, created_by=nguoi_dung["manager_sale"], title=ten,
        target_type="table", progress=40_000, total=100_000) for ten in ("Chết giữa chừng", "Đang chạy tốt"))
    BackgroundJob.objects.filter(pk=ket.pk).update(updated_at=timezone.now() - timedelta(minutes=nguong + 1))
    BackgroundJob.objects.filter(pk=con_song.pk).update(updated_at=timezone.now() - timedelta(minutes=nguong - 1))

    assert danh_dau_tac_vu_ket.delay().get() == 1
    ket.refresh_from_db()
    con_song.refresh_from_db()
    assert ket.status == JobStatus.STALE and "worker" in ket.error
    assert ket.finished_at is not None and ket.progress == 40_000
    assert con_song.status == JobStatus.RUNNING
    assert AuditLog.objects.filter(target_type="job", target_id=str(ket.pk)).count() == 1
    assert not AuditLog.objects.filter(target_type="job", target_id=str(con_song.pk)).exists()
    assert len(mail.outbox) == 1 and "kẹt" in mail.outbox[0].subject
    assert f"#{ket.pk} " in mail.outbox[0].body and f"#{con_song.pk} " not in mail.outbox[0].body


def test_nguong_ket_dai_hon_khoang_im_lang_that():
    """AC-9.2 — Ngưỡng kẹt của tác vụ đang chạy dài hơn khoảng im lặng thật: sao lưu được phép im tới trần
    pg_dump, tính lại 100.000 dòng đo 19–28 giây (ADR-016) — tác vụ còn sống không bị đánh kẹt (TL-23)"""
    from core.constants import (
        BACKUP_TIMEOUT_SECONDS, JOB_RUNNING_STALE_MINUTES, JOB_RUNNING_STALE_MINUTES_BACKUP,
        PERF_RECOMPUTE_SECONDS,
    )

    assert JOB_RUNNING_STALE_MINUTES_BACKUP * 60 > BACKUP_TIMEOUT_SECONDS
    assert JOB_RUNNING_STALE_MINUTES * 60 > PERF_RECOMPUTE_SECONDS * 10
    assert backup_service.BACKUP_TIMEOUT_SECONDS == BACKUP_TIMEOUT_SECONDS


@pytest.mark.django_db(transaction=True)
def test_tac_vu_dang_giu_khoa_khong_bi_danh_ket_nham(nguoi_dung):
    """AC-9.2 — Tác vụ nhập còn sống giữ khoá dòng tác vụ trong giao dịch (nhịp tiến độ chưa commit) thì lượt
    canh bỏ qua, không treo, không đánh kẹt nhầm; thả khoá rồi mới bị đánh kẹt (TL-23)"""
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from django.db import connections, transaction

    from core.constants import JOB_RUNNING_STALE_MINUTES
    from core.tasks import danh_dau_tac_vu_ket

    job = BackgroundJob.objects.create(kind=JobKind.IMPORT, status=JobStatus.RUNNING, title="Nhập dài")
    BackgroundJob.objects.filter(pk=job.pk).update(
        updated_at=timezone.now() - timedelta(minutes=JOB_RUNNING_STALE_MINUTES + 1))
    held, release = threading.Event(), threading.Event()

    def giu_khoa():
        try:
            with transaction.atomic():
                list(BackgroundJob.objects.select_for_update().filter(pk=job.pk))
                held.set()
                assert release.wait(8)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(1) as pool:
        h = pool.submit(giu_khoa)
        assert held.wait(5)
        assert danh_dau_tac_vu_ket() == 0
        job.refresh_from_db()
        assert job.status == JobStatus.RUNNING and not mail.outbox
        release.set()
        h.result(5)

    assert danh_dau_tac_vu_ket() == 1
    job.refresh_from_db()
    assert job.status == JobStatus.STALE


def test_sao_luu_gap_loi_la_van_dong_tac_vu_va_bao(thu_muc_sao_luu, db_gia, caplog):
    """NFR-19 — Sao lưu gặp lỗi lạ (không phải lỗi pg_dump) vẫn đóng tác vụ THẤT BẠI, xoá tệp dở, ghi nhật ký,
    gửi thư, không ném ra ngoài và không lộ mật khẩu — trước đây tác vụ nằm "Đang chạy" mãi (TL-23)"""
    def _hong(cmd, **kw):
        Path(cmd[cmd.index("--file") + 1]).write_bytes(b"PGDMP" + b"\0" * 100)
        raise RuntimeError(f"hỏng {MAT_KHAU_GIA}")

    truoc = backup_service.list_backups()
    job = backup_service.run_backup(runner=_hong)

    job.refresh_from_db()
    assert job.status == JobStatus.FAILED and job.error and MAT_KHAU_GIA not in job.error
    assert not list(thu_muc_sao_luu.glob("*.part"))
    assert "THẤT BẠI" in AuditLog.objects.filter(action=AuditAction.BACKUP).latest("pk").detail
    assert len(mail.outbox) == 1 and "THẤT BẠI" in mail.outbox[0].subject
    assert MAT_KHAU_GIA not in mail.outbox[0].body and MAT_KHAU_GIA not in caplog.text
    assert backup_service.list_backups() == truoc
    assert not BackgroundJob.objects.filter(kind=JobKind.BACKUP, status=JobStatus.RUNNING).exists()


def test_don_tep_qua_24_gio(settings, tmp_path, nguoi_dung):
    """NFR-16 — Tệp xuất và tệp nhập chờ quá 24 giờ bị xoá, tệp mới giữ, tác vụ bỏ dở bị đóng"""
    import os

    from core.tasks import don_tep_xuat_qua_han

    settings.STORAGE_DIR = tmp_path
    settings.EXPORT_DIR = tmp_path / "exports"
    xuat = settings.EXPORT_DIR
    nhap = tmp_path / "uploads" / "imports"
    xuat.mkdir(parents=True)
    nhap.mkdir(parents=True)
    cu = xuat / "cu.xlsx"
    moi = xuat / "moi.xlsx"
    cu_nhap = nhap / "cu.csv"
    for t in (cu, moi, cu_nhap):
        t.write_bytes(b"x")
    luc_cu = (timezone.now() - timedelta(hours=25)).timestamp()
    luc_moi = (timezone.now() - timedelta(hours=23)).timestamp()
    os.utime(cu, (luc_cu, luc_cu))
    os.utime(cu_nhap, (luc_cu, luc_cu))
    os.utime(moi, (luc_moi, luc_moi))

    bo_do = BackgroundJob.objects.create(
        kind=JobKind.IMPORT, status=JobStatus.DRAFT, created_by=nguoi_dung["manager_sale"],
    )
    BackgroundJob.objects.filter(pk=bo_do.pk).update(created_at=timezone.now() - timedelta(hours=25))
    vua_tao = BackgroundJob.objects.create(kind=JobKind.IMPORT, status=JobStatus.DRAFT)

    assert don_tep_xuat_qua_han.delay().get() == 2
    assert not cu.exists() and not cu_nhap.exists() and moi.exists()
    bo_do.refresh_from_db()
    vua_tao.refresh_from_db()
    assert bo_do.status == JobStatus.FAILED and vua_tao.status == JobStatus.DRAFT
    nk = AuditLog.objects.filter(target_type="cleanup").latest("created_at")
    assert "xoá 2 tệp" in nk.detail and "đóng 1 tác vụ" in nk.detail


# ══ Tổng quan ══════════════════════════════════════════════════════

def test_tong_quan_admin_thay_o_sao_luu_nguoi_khac_khong(client, thu_muc_sao_luu, db_gia, nguoi_dung):
    """NFR-19 — Admin thấy ô "Sao lưu đêm qua" kèm kết quả lần gần nhất; các vai khác không thấy"""
    backup_service.run_backup(runner=_pg_dump_gia(returncode=1, stderr="db chet"))
    client.force_login(nguoi_dung["admin"])
    trang = client.get("/").content.decode()
    assert "Sao lưu đêm qua" in trang and "Lần gần nhất không thành" in trang

    backup_service.run_backup(runner=_pg_dump_gia())
    trang = client.get("/").content.decode()
    assert "Thành công" in trang and "1 bản đang giữ" in trang

    for ma in ("manager_sale", "staff_vd"):
        client.force_login(nguoi_dung[ma])
        assert "Sao lưu đêm qua" not in client.get("/").content.decode()


# ══ pg_dump thật ═══════════════════════════════════════════════════

@pytest.mark.cham
@pytest.mark.skipif(shutil.which("pg_dump") is None, reason="máy này không có pg_dump")
def test_pg_dump_that_ra_tep_hop_le(thu_muc_sao_luu):
    """NFR-19 — pg_dump thật trên cơ sở dữ liệu kiểm thử ra tệp có chữ ký PGDMP và đủ lớn"""
    job = backup_service.run_backup()
    assert job.status == JobStatus.DONE, job.error
    tep = thu_muc_sao_luu / job.summary["file_name"]
    assert tep.read_bytes()[:5] == b"PGDMP" and tep.stat().st_size > 1024


# ══ Sao lưu rồi phục hồi thật vào cơ sở dữ liệu tạm — TL-97 · P0-15 ══

CO_PG = pytest.mark.skipif(shutil.which("pg_dump") is None or shutil.which("pg_restore") is None,
                           reason="máy này không có pg_dump/pg_restore")


@pytest.fixture
def csdl_tam(transactional_db):
    """Một cơ sở dữ liệu rỗng cạnh CSDL kiểm thử để phục hồi vào — không bao giờ đụng CSDL phát triển."""
    import uuid

    from django.db import connection

    goc = connection.settings_dict["NAME"]
    assert goc.startswith("test_"), goc
    ten = f"{goc}_ph_{uuid.uuid4().hex[:8]}"
    with connection.cursor() as c:
        c.execute(f'CREATE DATABASE "{ten}"')
    try:
        yield ten
    finally:
        with connection.cursor() as c:
            c.execute(f'DROP DATABASE IF EXISTS "{ten}" WITH (FORCE)')


def _ket_noi(ten):
    import psycopg
    from django.db import connection

    d = connection.settings_dict
    return psycopg.connect(dbname=ten, host=d.get("HOST") or "localhost", port=d.get("PORT") or 5432,
                           user=d.get("USER"), password=d.get("PASSWORD"), autocommit=True)


def _so_lieu(cur):
    """Số dòng mọi bảng, dấu vân tay dữ liệu bảng động, trigger, chỉ mục, extension."""
    cur.execute("SELECT table_name FROM information_schema.tables "
                "WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY 1")
    bang = [r[0] for r in cur.fetchall()]
    dem = {}
    for b in bang:
        cur.execute(f'SELECT count(*) FROM "{b}"')
        dem[b] = cur.fetchone()[0]
    cur.execute("SELECT md5(coalesce(string_agg(data::text, '|' ORDER BY id), '')) FROM forms_builder_datarecord")
    van_tay = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM pg_trigger WHERE NOT tgisinternal")
    trigger = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM pg_indexes WHERE schemaname='public'")
    chi_muc = cur.fetchone()[0]
    cur.execute("SELECT string_agg(extname, ',' ORDER BY extname) FROM pg_extension")
    return {"dem": dem, "van_tay": van_tay, "trigger": trigger, "chi_muc": chi_muc, "ext": cur.fetchone()[0]}


def _so_lieu_cua(ten):
    with _ket_noi(ten) as k, k.cursor() as c:
        return _so_lieu(c)


def _khop(dich, nguon):
    """Đích khớp nguồn: mọi bảng cùng số dòng — riêng tác vụ nền đích có thể thêm tác vụ sao lưu đang chạy lúc chụp."""
    assert {k: v for k, v in dich["dem"].items() if k != "core_backgroundjob"} == \
        {k: v for k, v in nguon["dem"].items() if k != "core_backgroundjob"}
    assert dich["dem"]["core_backgroundjob"] >= nguon["dem"]["core_backgroundjob"]
    assert {k: dich[k] for k in ("van_tay", "trigger", "chi_muc", "ext")} == \
        {k: nguon[k] for k in ("van_tay", "trigger", "chi_muc", "ext")}


@pytest.mark.cham
@CO_PG
def test_sao_luu_roi_phuc_hoi_that_vao_csdl_tam_giu_nguyen_du_lieu(thu_muc_sao_luu, csdl_tam, nguoi_dung, monkeypatch):
    """NFR-10 — Sao lưu thật rồi phục hồi thật bằng lệnh `phuc_hoi` (AC-10.5, phần máy làm được): CSDL đích có đủ
    mọi bảng, đúng từng dòng (chữ Việt, số tiền), trigger, chỉ mục, extension; phục hồi đè lên CSDL đã bị sửa thì
    trả về đúng như bản sao lưu (đường `--clean` thật, TL-97)"""
    from django.db import connection

    from forms_builder.models import DataRecord, TableDef

    bang = TableDef.objects.create(name="Thu chi", code="thu_chi_ph", department=nguoi_dung["staff_sale_1"].profile.department)
    DataRecord.objects.create(table=bang, department=bang.department, created_by=nguoi_dung["staff_sale_1"],
                              data={"ten": "Nguyễn Văn Ân", "loai_tien": "CAD", "tien": "1234.50"})
    with connection.cursor() as c:
        nguon = _so_lieu(c)

    job = backup_service.run_backup()
    assert job.status == JobStatus.DONE, job.error
    monkeypatch.setattr(backup_service, "_db", lambda: {**connection.settings_dict, "NAME": csdl_tam})
    call_command("phuc_hoi", job.summary["file_name"], "--toi-chac-chan")
    _khop(_so_lieu_cua(csdl_tam), nguon)

    with _ket_noi(csdl_tam) as k, k.cursor() as c:
        c.execute("UPDATE forms_builder_datarecord SET data = data || '{\"ten\": \"bị sửa\"}'::jsonb")
        c.execute("DELETE FROM django_session")
    call_command("phuc_hoi", job.summary["file_name"], "--toi-chac-chan")
    _khop(_so_lieu_cua(csdl_tam), nguon)
    assert "Phục hồi thành công" in _nhat_ky_phuc_hoi().detail


@pytest.mark.cham
@CO_PG
def test_phuc_hoi_tep_cut_giua_chung_khong_de_lai_csdl_do_dang(thu_muc_sao_luu, csdl_tam, nguoi_dung, monkeypatch):
    """NFR-10 — Bản sao lưu cụt giữa phần dữ liệu (mục lục còn nguyên): phục hồi báo THẤT BẠI và CSDL đích giữ y như
    trước — đủ dòng, đủ trigger, đủ chỉ mục (trọn một giao dịch, TL-97)"""
    import uuid

    from django.db import connection

    from forms_builder.models import DataRecord, TableDef

    bang = TableDef.objects.create(name="Đầy", code="day_ph", department=nguoi_dung["staff_sale_1"].profile.department)
    DataRecord.objects.bulk_create([DataRecord(table=bang, department=bang.department,
                                               data={"x": uuid.uuid4().hex * 10}) for _ in range(3000)])
    job = backup_service.run_backup()
    assert job.status == JobStatus.DONE, job.error
    tot = thu_muc_sao_luu / job.summary["file_name"]
    monkeypatch.setattr(backup_service, "_db", lambda: {**connection.settings_dict, "NAME": csdl_tam})
    backup_service.run_restore(tot)
    truoc = _so_lieu_cua(csdl_tam)

    cut = thu_muc_sao_luu / "knjsc-20260801-030000.dump"
    noi_dung = tot.read_bytes()
    for ti_le in (0.5, 0.6, 0.7, 0.8, 0.9):
        cut.write_bytes(noi_dung[:int(len(noi_dung) * ti_le)])
        if subprocess.run(["pg_restore", "--list", str(cut)], capture_output=True).returncode == 0:
            break
    else:
        pytest.fail("Không cắt được bản sao lưu ở phần dữ liệu (mục lục luôn hỏng)")

    with pytest.raises(backup_service.BackupError):
        backup_service.run_restore(cut)
    sau = _so_lieu_cua(csdl_tam)
    assert sau == truoc
    assert "Phục hồi THẤT BẠI" in _nhat_ky_phuc_hoi().detail
