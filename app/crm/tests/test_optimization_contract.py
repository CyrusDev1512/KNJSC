"""Giao thức READ giữ metadata/quyền của lõi lưới chung khi các cờ khác tắt."""
import pytest
from .test_waybill_feedback import feedback

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("sync", [False, True])
@pytest.mark.parametrize("actor", ["admin", "manager_sale", "leader_sale_1", "staff_sale_1", "staff_vd"])
def test_read_metadata_matches_current_grid(client, settings, feedback, nguoi_dung, sync, actor):
    settings.CRM_OPT_RECEIPTS = False
    settings.CRM_OPT_SYNC = sync
    settings.CRM_OPT_READ = False
    client.force_login(nguoi_dung[actor])
    url = f"/bang-tinh/{feedback[0].code}/du-lieu/"
    reference = client.get(url)
    original = reference.json()
    settings.CRM_OPT_READ = True
    response = client.get(url, {"protocol": "2"})
    assert response.status_code == reference.status_code
    if reference.status_code in (403, 404):
        # Bật cờ không được cấp thêm quyền truy cập bảng cho cấp bậc khác.
        assert response.json() == original
        return
    assert response.status_code == 200
    data = response.json()
    for key in ("capabilities", "schema_version", "columns", "total"):
        assert data[key] == original[key]
    assert [r["id"] for r in data["rows"]] == [r["id"] for r in original["rows"]]

    # Response gọn bỏ danh sách cột đã có, nhưng vẫn phải kiểm quyền/schema.
    again = client.get(url, {"protocol": "2", "query_token": data["query_token"],
                           "metadata_version": data["metadata_version"]}).json()
    assert "columns" not in again
    assert again["schema_version"] == data["schema_version"]
    assert again["capabilities"] == data["capabilities"]


def test_read_refreshes_dynamic_choices_without_column_change(client, settings, feedback, nguoi_dung, monkeypatch):
    from forms_builder import choice_registry

    settings.CRM_OPT_READ = True
    client.force_login(nguoi_dung["admin"])
    table = feedback[0]
    values = ["A"]
    monkeypatch.setitem(choice_registry._SO, (table.code, "ghi_chu"),
                        choice_registry.ChoiceList(lambda: list(values)))
    url = f"/bang-tinh/{table.code}/du-lieu/"
    first = client.get(url, {"protocol": "2"}).json()
    values.append("B")
    second = client.get(url, {"protocol": "2", "query_token": first["query_token"],
                             "metadata_version": first["metadata_version"]}).json()
    assert second["metadata_version"] != first["metadata_version"]
    column = next(c for c in second["columns"] if c["code"] == "ghi_chu")
    assert column["options"] == ["A", "B"]
