"""AC-51.1 → AC-51.4 — KN OMS: bản demo dữ liệu giả ở `/oms/` của KN CRM, chỉ Admin (ADR-051, chủ dự án 13.10.2026).

Trang đứng riêng, có khung và tên riêng; mọi số liệu sinh ngay trong trình duyệt (`static/js/oms.js`), máy chủ không
đọc, không ghi dữ liệu nghiệp vụ. Mục "KN OMS" ở thanh bên KN CRM chỉ Admin thấy và mở tab mới; vai khác gọi thẳng
đường dẫn bị 403 có nhật ký từ chối. KN ERP không có trang này.
"""
import re
from pathlib import Path
from urllib.parse import unquote

import pytest
from django.contrib.staticfiles import finders
from django.urls import NoReverseMatch, reverse

from core.constants import AuditAction, Rank
from core.models import AuditLog
from orders.services import dispatch_service

pytestmark = pytest.mark.django_db

MAN = ("baodon", "congno", "ruiro", "kho", "kenh", "lai")
KHONG_PHAI_ADMIN = ("staff_sale_1", "leader_sale_1", "manager_sale", "staff_mkt", "manager_mkt",
                    "staff_vd", "leader_vd", "manager_vd", "staff_kt", "ceo")


@pytest.fixture
def cac_vai(nguoi_dung, make_user, departments):
    """Mười vai không phải Admin, gồm cả Leader/Manager Vận đơn và CEO (xem toàn công ty nhưng không quản trị)."""
    dispatch_service.ensure_waybill_table(actor=nguoi_dung["admin"])
    return {**nguoi_dung,
            "leader_vd": make_user("leader_vd", Rank.LEADER, departments["vd"]),
            "manager_vd": make_user("manager_vd", Rank.MANAGER, departments["vd"]),
            "ceo": make_user("giam_doc", Rank.CEO)}


def _sidebar(html):
    return html.split('id="thanh-ben"')[1].split('<div class="chinh">')[0]


def _tep_tinh(ten):
    duong = finders.find(ten)
    assert duong, f"thiếu tệp tĩnh {ten}"
    return Path(duong).read_text(encoding="utf-8")


def test_admin_mo_kn_oms_khung_rieng(client, nguoi_dung):
    """AC-51.1 — Admin mở /oms/ trên KN CRM: 200, khung riêng "KN OMS" không có thanh bên KN CRM, nhãn Dữ liệu giả,
    đủ sáu màn, nút về KN CRM; nạp oms.css/oms.js có số phiên bản; nền theo khoá knjsc-nen của KN CRM; máy chủ không
    đọc ghi dữ liệu nghiệp vụ, JS không gọi máy chủ"""
    client.force_login(nguoi_dung["admin"])
    truoc = AuditLog.objects.count()
    kq = client.get("/oms/")
    assert kq.status_code == 200
    assert "crm/kn_oms.html" in [t.name for t in kq.templates]
    html = kq.content.decode()
    assert "<title>KN OMS" in html
    assert 'id="thanh-ben"' not in html, "KN OMS có khung riêng, không dùng thanh bên KN CRM"
    assert "Dữ liệu giả" in html
    for man in MAN:
        assert f'data-view="{man}"' in html, man
    assert re.search(r'href="/static/css/oms\.css\?v=\d+"', html)
    assert re.search(r'src="/static/js/oms\.js\?v=\d+"', html)
    assert 'localStorage.getItem("knjsc-nen")' in html
    assert 'href="/"' in html and "Về KN CRM" in html
    assert AuditLog.objects.count() == truoc
    js, css = _tep_tinh("js/oms.js"), _tep_tinh("css/oms.css")
    assert "knjsc-nen" in js and "kn-demo-che-do" not in js
    assert "fetch(" not in js and "XMLHttpRequest" not in js
    assert ':root[data-theme="dark"]' in css


#: Bốn tệp kiểu dáng của crm/base_crm.html, đúng thứ tự KN CRM nạp
CSS_CRM = ("tokens.css", "main.css", "crm-frame.css", "solarpunk.css")
#: Biến của KN CRM mà oms.css không được khai lại: khai lại là KN OMS lệch màu, lệch bo góc với KN CRM
BIEN_CRM = ("--plane", "--surface", "--surface-2", "--surface-3", "--ink", "--ink-2", "--ink-3", "--rule", "--rule-strong",
            "--accent", "--accent-hover", "--accent-soft", "--accent-ink", "--good", "--good-soft", "--warn", "--warn-soft",
            "--critical", "--critical-soft", "--serious", "--serious-soft", "--r-sm", "--r-md", "--r-lg", "--shadow-1",
            "--shadow-2", "--font-van", "--font-ma", "--sp-glass", "--sp-edge", "--sp-selected")


def _tep_css(html):
    return re.findall(r'href="/static/css/([\w-]+\.css)\?v=\d+"', html)


def test_kn_oms_mang_dien_mao_kn_crm(client, nguoi_dung):
    """AC-51.9 — KN OMS nạp bốn tệp kiểu dáng của KN CRM đúng thứ tự KN CRM nạp rồi mới tới oms.css; khung theo markup
    KN CRM (body sp-crm, thanh bên kính crm-nav, thanh trên có đường dẫn, mặt đọc noi-dung); oms.css không khai lại biến
    màu, bo góc, đổ bóng của KN CRM và không có viền trái hay phải dày hơn 1 px; trang không còn hộp thoại"""
    client.force_login(nguoi_dung["admin"])
    html = client.get("/oms/").content.decode()
    trang_chu = client.get("/")
    assert trang_chu.status_code == 200
    assert [t for t in _tep_css(trang_chu.content.decode()) if t in CSS_CRM] == list(CSS_CRM)
    assert _tep_css(html) == [*CSS_CRM, "oms.css"]
    assert '<body class="sp-crm sp-oms">' in html
    for moc in ('class="nav crm-nav"', 'class="topbar"', 'class="duong-dan"', 'class="noi-dung"', 'id="nut-nav"'):
        assert moc in html, moc
    assert 'id="hop"' not in html and "<dialog" not in html
    css = re.sub(r"/\*.*?\*/", "", _tep_tinh("css/oms.css"), flags=re.S)
    for bien in BIEN_CRM:
        assert not re.search(rf"{re.escape(bien)}\s*:", css), f"oms.css khai lại {bien} của KN CRM"
    for vien in re.finditer(r"border-(?:left|right|inline-start|inline-end)(?:-width)?\s*:\s*([^;}]*)", css):
        day = re.search(r"(\d*\.?\d+)px", vien.group(1))
        assert not day or float(day.group(1)) <= 1, f"viền một bên dày hơn 1 px: {vien.group(0)}"
    js = _tep_tinh("js/oms.js")
    assert "moHop" not in js and "#hop" not in js


@pytest.mark.parametrize("vai", KHONG_PHAI_ADMIN)
def test_vai_khac_bi_403_co_nhat_ky(client, cac_vai, vai):
    """AC-51.2 — Mọi vai không phải Admin (Staff/Leader/Manager Sale, Staff/Manager MKT, Staff/Leader/Manager Vận đơn,
    Kế toán, CEO) gọi thẳng /oms/ đều bị 403 với đúng một dòng nhật ký từ chối; trang lỗi không lộ nội dung demo"""
    nguoi = cac_vai[vai]
    client.force_login(nguoi)
    kq = client.get("/oms/")
    assert kq.status_code == 403
    noi_dung = kq.content.decode()
    assert "Bạn không có quyền truy cập" in noi_dung and "Dữ liệu giả" not in noi_dung
    assert AuditLog.objects.filter(action=AuditAction.DENIED, actor=nguoi,
                                   target_type="path", target_id="/oms/").count() == 1


def test_chua_dang_nhap_ve_dang_nhap_va_khong_nhan_post(client, nguoi_dung):
    """AC-51.2 — Chưa đăng nhập thì về trang đăng nhập rồi quay lại /oms/; trang chỉ nhận GET (POST 405, không ghi gì)"""
    kq = client.get("/oms/")
    assert kq.status_code == 302 and kq["Location"].startswith("/dang-nhap/")
    assert "/oms/" in unquote(kq["Location"])
    client.force_login(nguoi_dung["admin"])
    assert client.post("/oms/").status_code == 405
    assert not AuditLog.objects.filter(action=AuditAction.DENIED, target_id="/oms/").exists()


def test_muc_kn_oms_chi_admin_mo_tab_moi(client, cac_vai):
    """AC-51.3 — Thanh bên KN CRM của Admin có mục "KN OMS" ở cuối (sau Nhật ký), mở tab mới với rel=noopener; mọi vai
    khác không thấy mục này và trang chủ của họ không có liên kết /oms/"""
    client.force_login(cac_vai["admin"])
    ben = _sidebar(client.get("/").content.decode())
    lien_ket = re.findall(r'<a [^>]*href="/oms/"[^>]*>', ben)
    assert len(lien_ket) == 1
    assert 'target="_blank"' in lien_ket[0] and 'rel="noopener"' in lien_ket[0]
    assert "KN OMS" in ben
    assert ben.index('href="/oms/"') > ben.index('href="/nhat-ky/"')
    for vai in KHONG_PHAI_ADMIN:
        client.force_login(cac_vai[vai])
        kq = client.get("/")
        assert kq.status_code == 200, vai
        html = kq.content.decode()
        assert 'href="/oms/"' not in html and "KN OMS" not in html, vai


def test_erp_khong_co_kn_oms(client, settings, nguoi_dung):
    """AC-51.4 — KN OMS chỉ có ở KN CRM: tên kn_oms chỉ dựng được trong URLconf KN CRM; KN ERP trả 404 cho /oms/ và
    không có liên kết tới đó"""
    assert reverse("kn_oms", urlconf="knjsc.urls_bangtinh") == "/oms/"
    with pytest.raises(NoReverseMatch):
        reverse("kn_oms", urlconf="knjsc.urls")
    settings.ROOT_URLCONF = "knjsc.urls"
    client.force_login(nguoi_dung["admin"])
    assert client.get("/oms/").status_code == 404
    assert 'href="/oms/"' not in client.get("/", follow=True).content.decode()
