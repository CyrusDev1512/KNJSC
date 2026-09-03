"""Kiểm thử đầu-cuối bằng trình duyệt thật — Playwright + Chromium (backlog Q44).

Chỉ chạy được trên máy có Playwright và Chromium (`pip install -r
requirements-dev.txt && playwright install chromium`); thiếu thì **tự bỏ qua
kèm lý do**, không đỏ. Trong container `web` không có Chromium — chạy trên máy
phát triển hoặc máy kiểm thử.

Mọi bài ở đây mang hai dấu: `trinh_duyet` (cần Chromium) và `cham`.
"""
import os
from pathlib import Path

import pytest

# Playwright đồng bộ chạy vòng lặp sự kiện trong luồng kiểm thử; Django phải
# được phép truy vấn trong luồng đó
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")

try:
    from playwright.sync_api import sync_playwright
except ImportError:                     # pragma: khong do
    sync_playwright = None

LY_DO = ("cần Playwright và Chromium — pip install -r requirements-dev.txt "
         "&& playwright install chromium")
#: Ảnh chụp màn hình để người xem đối chiếu — nằm trong storage/, không vào git
THU_MUC_ANH = Path(__file__).resolve().parents[3] / "storage" / "e2e"
MAT_KHAU = "matkhau-kiem-thu-1"


@pytest.fixture(scope="session")
def trinh_duyet():
    if sync_playwright is None:
        pytest.skip(LY_DO)
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception as loi:        # Chromium chưa cài, hoặc sai phiên bản
            pytest.skip(f"{LY_DO} — {str(loi).splitlines()[0][:160]}")
        yield browser
        browser.close()


@pytest.fixture
def trang(trinh_duyet):
    """Một tab máy tính 1366×800, tiếng Việt."""
    ctx = trinh_duyet.new_context(viewport={"width": 1366, "height": 800}, locale="vi-VN")
    page = ctx.new_page()
    page.set_default_timeout(15_000)
    yield page
    ctx.close()


@pytest.fixture
def trang_dien_thoai(trinh_duyet):
    """Một tab điện thoại 390×844 (cỡ iPhone), có chạm — AC-10.4, AC-11.11."""
    ctx = trinh_duyet.new_context(
        viewport={"width": 390, "height": 844}, device_scale_factor=2,
        is_mobile=True, has_touch=True, locale="vi-VN",
    )
    page = ctx.new_page()
    page.set_default_timeout(15_000)
    yield page
    ctx.close()


@pytest.fixture
def dang_nhap(live_server):
    """Đăng nhập bằng biểu mẫu thật trên một tab cho trước."""
    def _dang_nhap(page, user, mat_khau=MAT_KHAU):
        page.goto(live_server.url + "/dang-nhap/")
        page.fill("input[name=username]", user.username)
        page.fill("input[name=password]", mat_khau)
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")
        assert "/dang-nhap/" not in page.url, "đăng nhập không thành"
        return page
    return _dang_nhap


def chup(page, ten):
    """Lưu ảnh chụp cả trang vào storage/e2e/ để người xem đối chiếu."""
    THU_MUC_ANH.mkdir(parents=True, exist_ok=True)
    duong_dan = THU_MUC_ANH / f"{ten}.png"
    page.screenshot(path=str(duong_dan), full_page=True)
    return duong_dan
