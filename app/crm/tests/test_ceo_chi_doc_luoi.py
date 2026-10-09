"""CEO đọc toàn công ty nhưng không sửa được ô nào trên lưới — AC-21.17 (săn lỗi 06.10.2026, bước 7 đột biến).

Đột biến M16 (bỏ dòng `is_company_reader → False` trong `grant_service.can_edit_visible_record`) không làm bài nào
đỏ: chưa có bài canh rằng CEO — thấy mọi dòng (ADR-020) — vẫn không ghi được qua lưới.
"""
import pytest

from core.constants import Rank

from .test_master_grid import write
from .test_waybill_feedback import feedback  # noqa: F401 — fixture dùng chung

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("trong_bo_phan", [False, True])
def test_ceo_xem_duoc_nhung_khong_sua_duoc_o_luoi(client, feedback, make_user, trong_bo_phan):  # noqa: F811
    """AC-21.17 — CEO (kể cả hồ sơ gắn vào chính bộ phận Vận đơn, nơi bảng dùng chung cho mọi người trong bộ phận sửa) mở được lưới và thấy dòng, nhưng không ô nào hiện là sửa được và ghi một ô bị từ chối (403), dữ liệu không đổi"""
    row = feedback[2][0]
    ceo = make_user("giam_doc", Rank.CEO, department=row.table.department if trong_bo_phan else None)
    client.force_login(ceo)
    du_lieu = client.get("/bang-tinh/van_don/du-lieu/?offset=0&limit=100")
    assert du_lieu.status_code == 200
    o = [c for r in du_lieu.json()["rows"] for c in r["cells"].values()]
    assert o and not any(c["editable"] for c in o)
    cu = row.data.get("ghi_chu")
    r = write(client, row, old=cu, value="CEO sửa")
    assert r.status_code == 403
    row.refresh_from_db()
    assert row.data.get("ghi_chu") == cu
