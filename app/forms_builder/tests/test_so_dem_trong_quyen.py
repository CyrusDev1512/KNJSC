"""TL-11/121: số đếm không được tiết lộ dòng ngoài quyền hay đã xoá."""
import pytest
from django.utils import timezone
from core.models import BackgroundJob
from core.constants import JobKind, JobStatus
from forms_builder.models import DataRecord, TableDef
from crm.tests.test_bang_tinh_luu_o import bang_sale, _dong  # noqa: F401

pytestmark = pytest.mark.django_db


def test_bang_thuong_dem_dung_dong_con_song_trong_quyen(bang_sale, nguoi_dung):
    """AC-3.1 — Staff chỉ đếm dòng mình; Admin cũng không đếm dòng xoá mềm."""
    bang_sale.workflow = ''
    bang_sale.save(update_fields=['workflow'])
    own = nguoi_dung['staff_sale_1']
    _dong(bang_sale, own, khach='Còn sống')
    removed = _dong(bang_sale, own, khach='Đã xoá')
    DataRecord.all_objects.filter(pk=removed.pk).update(deleted_at=timezone.now())
    _dong(bang_sale, nguoi_dung['staff_sale_2'], khach='Người khác')
    assert TableDef.objects.with_visible_record_count(own).get(pk=bang_sale.pk).so_dong == 1
    assert TableDef.objects.with_visible_record_count(nguoi_dung['admin']).get(pk=bang_sale.pk).so_dong == 2


def test_moc_moi_nhat_chi_bao_dang_tinh_khong_lo_so_dong(client, bang_sale, nguoi_dung, settings):
    """AC-10.21 — Poll không đưa tổng/tiến độ cả bảng cho người chỉ thấy một phần."""
    settings.GRID_ONLY_TABLES = set()
    settings.ROOT_URLCONF = 'knjsc.urls_bangtinh'
    user = nguoi_dung['staff_sale_1']
    _dong(bang_sale, user, khach='Của mình')
    job = BackgroundJob.objects.create(kind=JobKind.RECOMPUTE, status=JobStatus.RUNNING,
        created_by=nguoi_dung['admin'], target_type='table', target_id=bang_sale.code,
        total=12345, progress=6789)
    client.force_login(user)
    response = client.get(f'/bang-tinh/{bang_sale.code}/moi-nhat/')
    assert response.status_code == 200
    assert response.json()['tinh_lai'] == {'pk': job.pk}
