"""TL-08/14/113/114/115: cache không trộn phiên và ACK không nuốt thay đổi ngoài lượt lưu."""
import pytest
from django.test import Client
from playwright.sync_api import expect

from crm.tests.test_bang_tinh_luu_o import bang_sale  # noqa: F401
from crm.tests.test_waybill_feedback import feedback  # noqa: F401
from forms_builder.models import DataRecord
from forms_builder.services import record_service

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.trinh_duyet]


@pytest.fixture
def grid(settings, bang_sale, nguoi_dung):
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    settings.GRID_ONLY_TABLES = set()
    rows = DataRecord.objects.bulk_create([
        DataRecord(table=bang_sale, department=bang_sale.department,
                   created_by=nguoi_dung["staff_sale_1"],
                   data={"khach": f"Khách {i:04d}", "so_luong": 1},
                   val_customer=f"Khách {i:04d}") for i in range(600)
    ])
    return bang_sale, rows


def cell(row, code="khach"):
    return f".mg-cell[data-id='{row.pk}'][data-code='{code}']"


def edit(page, row, text, code="khach"):
    page.dblclick(cell(row, code))
    page.locator("#mg-input input").fill(text)
    with page.expect_response(lambda r: "/luu-json/" in r.url and r.request.method == "POST") as saved:
        page.keyboard.press("Enter")
    assert saved.value.status == 200
    expect(page.locator("#bt-trang-thai")).to_have_text("Đã lưu")


def paste(page, text):
    # Chromium headless không đọc clipboard hệ điều hành; giữ nguyên handler paste thực của lưới.
    page.evaluate("""text => { const dt = new DataTransfer(); dt.setData('text/plain', text);
      document.getElementById('mg-viewport').dispatchEvent(new ClipboardEvent('paste',
        {bubbles:true, clipboardData:dt})); }""", text)


def test_ack_khong_nuot_thay_doi_nguoi_khac(live_server, trang, dang_nhap, grid, nguoi_dung):
    """AC-10.22 — B sửa dòng khác trước A lưu: sau kỳ đồng bộ A vẫn phải nhận nội dung B."""
    table, rows = grid
    dang_nhap(trang, nguoi_dung["admin"])
    with trang.expect_response("**/moi-nhat/"):
        trang.goto(f"{live_server.url}/bang-tinh/{table.code}/?sap=khach")
    expect(trang.locator(cell(rows[1]))).to_have_text("Khách 0001")
    record_service.update_cell(rows[1], "khach", "Khách 0001 đã đổi", actor=nguoi_dung["staff_sale_1"])
    edit(trang, rows[0], "Khách 0000 của A")
    expect(trang.locator(cell(rows[1]))).to_have_text("Khách 0001 đã đổi", timeout=18_000)


def test_dan_qua_khoi_sau_luu_khong_mat_mot_o(live_server, trang, dang_nhap, grid, nguoi_dung):
    """AC-11.19 — Đổi thứ tự giữa hai khối: dán 100 ô phải đủ 100 hoặc từ chối toàn bộ, không 99/100."""
    table, rows = grid
    blocked = {"value": True}
    def read_block(route):
        from urllib.parse import parse_qs, urlparse
        offset = int(parse_qs(urlparse(route.request.url).query).get("offset", [0])[0])
        if blocked["value"] and offset >= 300:
            route.abort()
        else:
            route.continue_()
    trang.route("**/du-lieu/**", read_block)
    # Giữ phản hồi poll ở mốc đầu: tái hiện cửa sổ giữa hai lần đồng bộ, không chờ may rủi 8 giây.
    client = Client(); client.force_login(nguoi_dung["admin"])
    stamp = client.get(f"/bang-tinh/{table.code}/moi-nhat/").json()
    trang.route("**/moi-nhat/", lambda route: route.fulfill(json=stamp))
    dang_nhap(trang, nguoi_dung["admin"])
    trang.goto(f"{live_server.url}/bang-tinh/{table.code}/?sap=khach")
    expect(trang.locator(cell(rows[0]))).to_be_visible()
    trang.locator("#mg-viewport").evaluate("e => e.scrollTop = 245 * 28 + 54")
    expect(trang.locator(cell(rows[250]))).to_be_visible()
    edit(trang, rows[250], "Khách 0250 đã lưu")
    record_service.update_cell(rows[550], "khach", "AAA lên đầu", actor=nguoi_dung["staff_sale_1"])
    blocked["value"] = False
    trang.click(cell(rows[250]))
    sent = []
    trang.on("request", lambda r: sent.append(r.post_data_json) if "/luu-json/" in r.url else None)
    paste(trang, "\n".join(f"TL113-{i:03d}" for i in range(100)))
    trang.wait_for_function("""() => document.getElementById('mg-message').textContent.includes('Dữ liệu đã') ||
       document.getElementById('bt-trang-thai').textContent === 'Đã lưu'""")
    trang.wait_for_timeout(2500)  # vượt giới hạn tự lưu 2 giây, kiểm DB thay vì chỉ lời báo
    count = DataRecord.objects.filter(table=table, data__khach__startswith="TL113-").count()
    assert count in (0, 100), f"Chỉ lưu {count}/100 ô; payload={[(len(p.get('cells', []))) for p in sent]}"
    if count == 0:
        assert not sent, "Lượt đã phát hiện đổi thứ tự không được gửi phần dán dở"
        expect(trang.locator("#mg-message")).to_contain_text("Dữ liệu đã")
        expect(trang.locator(cell(rows[250]))).to_be_visible()
        trang.click(cell(rows[250]))
        with trang.expect_response(lambda r: "/luu-json/" in r.url and r.request.method == "POST") as saved:
            paste(trang, "\n".join(f"TL113-{i:03d}" for i in range(100)))
        assert saved.value.status == 200
        expect(trang.locator("#bt-trang-thai")).to_have_text("Đã lưu")
        assert DataRecord.objects.filter(table=table, data__khach__startswith="TL113-").count() == 100
        assert len(sent[-1]["cells"]) == 100
        assert len({(c["id"], c["column"]) for c in sent[-1]["cells"]}) == 100
    else:
        assert len(sent[0]["cells"]) == 100
        assert len({(c["id"], c["column"]) for c in sent[0]["cells"]}) == 100


def test_poll_ve_muon_khong_ghi_de_trang_thai_sau_luu(live_server, trang, dang_nhap, grid, nguoi_dung):
    """AC-10.22 — Phản hồi hỏi trước khi lưu về muộn không ép tải lại cache của phiên mới."""
    table, rows = grid
    dang_nhap(trang, nguoi_dung["admin"])
    with trang.expect_response("**/moi-nhat/"):
        trang.goto(f"{live_server.url}/bang-tinh/{table.code}/?sap=khach")
    expect(trang.locator(cell(rows[0]))).to_be_visible()
    record_service.update_cell(rows[1], "khach", "Khách 0001 của B", actor=nguoi_dung["staff_sale_1"])
    trang.evaluate("""() => {
      const original=window.fetch; window.__held=false;
      window.fetch=async (...args) => {
        const response=await original(...args);
        if(String(args[0]).endsWith('/moi-nhat/')&&!window.__held){
          window.__held=true; await new Promise(resolve=>window.__release=resolve);
        }
        return response;
      };
    }""")
    trang.wait_for_function("() => window.__held", timeout=12_000)
    edit(trang, rows[0], "Khách 0000 của A")
    reads=[]
    trang.on("request", lambda r: reads.append(r.url) if "/du-lieu/" in r.url else None)
    trang.evaluate("() => window.__release()")
    trang.wait_for_timeout(750)  # khoảng ngắn hơn kỳ poll, đủ phản hồi đang giữ và frame render
    assert not reads, "Phản hồi poll cũ gây tải lại dữ liệu sau lượt lưu mới"
    expect(trang.locator(cell(rows[0]))).to_have_text("Khách 0000 của A")


def test_doi_dien_thoai_cap_nhat_ca_dong_trung(live_server, trang, dang_nhap, settings, feedback, nguoi_dung):
    """AC-11.9 — Cột Trùng cập nhật cả hàng không nằm trong ACK khi đổi số điện thoại."""
    settings.ROOT_URLCONF = "knjsc.urls_bangtinh"
    settings.BANGTINH_URL = ""
    table, _, rows = feedback
    dang_nhap(trang, nguoi_dung["staff_vd"])
    trang.goto(f"{live_server.url}/bang-tinh/{table.code}/")
    expect(trang.locator(cell(rows[1], "__duplicates"))).to_be_visible()
    edit(trang, rows[0], rows[1].data["so_dien_thoai"], "so_dien_thoai")
    for row in rows:
        expect(trang.locator(cell(row, "__duplicates"))).to_have_text("2", timeout=18_000)
