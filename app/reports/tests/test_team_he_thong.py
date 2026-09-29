"""Quyết định 25.09: Team báo cáo tự nhận diện như Marketer."""
import pytest
from core.constants import Rank
from forms_builder.models import ColumnDef, FieldDef
from forms_builder.services import form_service
from org.models import Team
from reports.models import DailyReport
from reports.services import daily_service
from reports.tests.test_form_nhap_bao_cao import bang_mkt, mkt_source, _du  # noqa: F401

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('rank', [Rank.STAFF, Rank.LEADER, Rank.MANAGER])
def test_team_tu_ho_so_khong_nhan_gia_mao(client, mkt_source, departments, make_user, rank):
    """AC-44.1 — Team thật được lưu, giá trị giả từ client/service không đổi phạm vi."""
    form = mkt_source.table.forms.get()
    own = Team.objects.create(name='Team của tôi', department=departments['mkt'])
    other = Team.objects.create(name='Team khác', department=departments['mkt'])
    user = make_user('nguoi_nop', rank, departments['mkt'], own)
    col = ColumnDef.objects.create(table=form.table, code='team_mau', name='Team', field_type='text')
    field = FieldDef.objects.create(code='team_mau_input', name='Team', field_type='text', department=departments['mkt'])
    form_service.add_field(form, field, column=col)
    client.force_login(user)
    html = client.get('/bao-cao/', {'bieu_mau':form.code}).content.decode()
    assert 'value="Team của tôi" readonly' in html
    assert '<select class="o-nhap" id="o-team"' not in html
    assert 'id="o-team_mau_input"' not in html
    response = client.post('/bao-cao/', {**_du(form), 'team':other.pk, field.code:'Team giả'})
    assert response.status_code == 302
    report = DailyReport.objects.get()
    assert report.team_id == report.record.team_id == own.pk
    assert report.record.data['team_mau'] == own.name
    # Đường service cũng không cho dùng team khác để vượt kiểm tra view.
    daily_service.submit_current(form, _du(form), actor=user, team=other)
    assert DailyReport.objects.order_by('-pk').first().team_id == own.pk


def test_chua_gan_team_van_nop_duoc(client, mkt_source, nguoi_dung):
    form = mkt_source.table.forms.get()
    client.force_login(nguoi_dung['staff_mkt'])
    assert 'Chưa được gán Team' in client.get('/bao-cao/', {'bieu_mau':form.code}).content.decode()
    assert client.post('/bao-cao/', _du(form)).status_code == 302
    report = DailyReport.objects.get()
    assert report.team_id is None and report.record.team_id is None


def test_sua_bao_cao_giu_team_cu(client, mkt_source, departments, make_user, nguoi_dung):
    form = mkt_source.table.forms.get()
    a = Team.objects.create(name='Team cũ', department=departments['mkt'])
    b = Team.objects.create(name='Team mới', department=departments['mkt'])
    user = make_user('nguoi_nop', Rank.STAFF, departments['mkt'], a)
    col = ColumnDef.objects.create(table=form.table, code='team_mau', name='Team', field_type='text')
    field = FieldDef.objects.create(code='team_input', name='Team', field_type='text', department=departments['mkt'])
    form_service.add_field(form, field, column=col)
    report = daily_service.submit_current(form, _du(form), actor=user)
    user.profile.team = b
    user.profile.save(update_fields=['team'])
    daily_service.amend(report, {field.code:'Team sửa giả'}, version=report.record.updated_at.isoformat(), actor=nguoi_dung['admin'])
    report.refresh_from_db()
    assert report.team_id == report.record.team_id == a.pk
    assert report.record.data['team_mau'] == a.name


@pytest.mark.parametrize('kind', ['sale', 'mkt'])
def test_team_bieu_mau_truc_tiep_cung_chi_doc(client, mkt_source, departments, make_user, kind):
    """AC-44.1 — Đường điền biểu mẫu không để ô Team nhập tay rồi âm thầm bỏ qua."""
    from reports.management.commands.configure_erp_reports import configure_source
    # Dùng cùng bộ cột thử cho cả hai profile báo cáo.
    configure_source(mkt_source.table, kind)
    form = mkt_source.table.forms.get()
    own = Team.objects.create(name='Team hồ sơ', department=departments['mkt'])
    user = make_user('nguoi_dien', Rank.STAFF, departments['mkt'], own)
    col = ColumnDef.objects.create(table=form.table, code='team_mau', name='Team', field_type='text')
    field = FieldDef.objects.create(code='team_input', name='Team', field_type='text', department=departments['mkt'])
    form_service.add_field(form, field, column=col)
    client.force_login(user)
    path = f'/bieu-mau/{form.code}/dien/'
    response = client.get(path)
    assert response.status_code == 200
    assert 'value="Team hồ sơ" readonly' in response.content.decode()
    assert client.post(path, {**_du(form), field.code: 'Team giả'}).status_code == 302
    row = form.table.records.get()
    assert row.team_id == own.pk and row.data['team_mau'] == own.name


def test_ceo_doc_bao_cao_khong_nop_hoac_sua(client, mkt_source, nguoi_dung, make_user, departments):
    """AC-44.6 — Giữ CEO chỉ đọc kể cả báo cáo cùng bộ phận và POST trực tiếp."""
    form = mkt_source.table.forms.get()
    report = daily_service.submit_current(form, _du(form), actor=nguoi_dung['staff_mkt'])
    before = report.record.data.copy()
    ceo = make_user('ceo_cung_bo_phan', Rank.CEO, departments['mkt'])
    client.force_login(ceo)
    assert client.get(f'/bao-cao/{report.pk}/').status_code == 200
    # Màn sửa dùng 404 cho báo cáo ngoài quyền sửa, kể cả vẫn có quyền đọc.
    assert client.get(f'/bao-cao/{report.pk}/sua/').status_code == 404
    assert client.post(f'/bao-cao/{report.pk}/sua/', {
        **_du(form, doanh_so='999'), 'version':report.record.updated_at.isoformat(),
    }).status_code == 404
    assert client.post('/bao-cao/', _du(form)).status_code == 403
    path = f'/bieu-mau/{form.code}/dien/'
    assert client.get(path).status_code == 403
    assert client.post(path, _du(form)).status_code == 403
    report.record.refresh_from_db()
    assert report.record.data == before and DailyReport.objects.count() == 1
