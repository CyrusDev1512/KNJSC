"""TL-112/124: kịch bản cũ phải đọc JSON và không đưa dòng thật vào payload."""
import importlib.util
import sys
import types
from pathlib import Path
import pytest


@pytest.fixture
def script(monkeypatch):
    fake = types.ModuleType('locust')
    fake.HttpUser = object
    fake.between = lambda *a: None
    fake.task = lambda *a: a[0] if a and callable(a[0]) else lambda f:f
    listener = types.SimpleNamespace(add_listener=lambda f:f)
    fake.events = types.SimpleNamespace(init=listener, quitting=listener, request=listener, spawning_complete=listener)
    monkeypatch.setitem(sys.modules,'locust',fake)
    monkeypatch.setitem(sys.modules,'gevent',types.SimpleNamespace())
    spec = importlib.util.spec_from_file_location('crm_load_test',Path(__file__).parent/'perf/locustfile_kn_crm.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_locust_doc_json_va_chi_dung_dong_perf(script):
    """AC-10.10 — Kể cả máy chủ trả kèm dòng thật, chỉ PERF-* được vào gói CAS."""
    rows = [{'id':i,'cells':{'ma_don':{'value':code},'ghi_chu':{'value':'cũ','editable':True}}}
            for i,code in [(1,'PERF-T001'),(2,'DH-THAT')]]
    calls=[]
    class Response:
        status_code=200
        text=''
        def json(self):return {'rows':rows}
    class Client:
        def get(self,url,**kwargs): calls.append((url,kwargs));return Response()
    tab=object.__new__(script.TabLuoi)
    tab.client=Client();tab.goc='/bang-tinh/van_don/';tab.rows=[];tab.pks=[]
    tab._luoi('sap=ngay')
    assert '/du-lieu/' in calls[0][0]
    assert 'PERF-' in str(calls[0])
    assert [row['id'] for row in tab.rows] == [1]
    payload=tab._payload(5)
    assert [cell['id'] for cell in payload['cells']] == [1]
    assert payload['cells'][0]['old']=='cũ'


def test_locust_khong_ghi_khi_chi_co_dong_that(script):
    """AC-10.10 — Không có dòng giả thì không dựng lượt ghi rỗng hoặc đổi dòng thật."""
    tab=object.__new__(script.TabLuoi)
    tab.rows=[{'id':2,'cells':{'ma_don':{'value':'DH-THAT'},'ghi_chu':{'value':'cũ','editable':True}}}]
    assert tab._payload(5) is None


def test_locust_chan_host_that_truoc_dang_nhap(script):
    """AC-10.10 — Kịch bản cũ không được chạy thẳng lên domain thật."""
    with pytest.raises(ValueError):
        script.require_local_target('https://crm.example.com')


def test_launcher_giu_du_lieu_khong_seed_hoac_reset_mat_khau():
    """AC-10.10 — Hai launcher dùng một runner: --giu-du-lieu không gọi du_lieu_mau/seed/xoá."""
    path=Path(__file__).resolve().parents[2]/'scripts/kiem-tai-kn-crm.py'
    spec=importlib.util.spec_from_file_location('load_runner',path)
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    commands=runner.preparation(keep=True)
    assert all('knjsc-loadtest' in command for command in commands)
    assert all(not {'du_lieu_mau','seed_perf','--xoa-cu','down'} & set(command) for command in commands)
    seeded=runner.preparation(keep=False)
    guard=next(i for i,c in enumerate(seeded) if 'shell' in c)
    seed=next(i for i,c in enumerate(seeded) if 'du_lieu_mau' in c)
    assert guard < seed
