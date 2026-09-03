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
