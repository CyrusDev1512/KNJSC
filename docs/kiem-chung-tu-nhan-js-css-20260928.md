# Kiểm chứng — Máy chạy thử tự nhận CSS/JS mới (AC-10.11) — 28.09.2026

Nhánh `claude/tu-nhan-js-css-moi` tách từ `main` (`a0313be`), máy ảo Claude Code, PostgreSQL 16.

## Vấn đề

Chủ dự án kéo bản sửa chỉ đổi `master-grid.js`/`master-grid.css` (PR #61) nhưng lưới vẫn như cũ cho
tới khi Ctrl+F5. `core/context_processors.py` tính `PHIEN_BAN_TINH` (thời điểm sửa mới nhất của CSS/JS,
gắn sau đường dẫn `?v=`) **một lần lúc khởi động**; runserver chỉ tự khởi động lại khi tệp Python đổi,
nên sửa riêng tệp tĩnh thì `?v=` đứng yên và Chrome dùng bản trong bộ đệm.

## Sửa

`phien_ban_hien_tai()`: DEBUG bật (máy local, `knjsc.settings.dev`; `bangtinh` gốc `dev`) thì quét lại
mỗi lần tải trang; DEBUG tắt (VPS: `settings.prod`, `BANGTINH_GOC=prod`) trả số tính lúc khởi động như
trước — phát hành là khởi động lại nên số vẫn đổi.

## Kiểm

| Kiểm | Kết quả |
|---|---|
| `core/tests/test_phien_ban_tinh.py` (AC-10.11) trước sửa | **đỏ**: `'1790579646' != '1790579646'` — sửa JS mà số không đổi |
| Cùng tệp sau sửa | 2 đạt (DEBUG đổi số; DEBUG tắt giữ số khởi động) |
| `tests/test_truy_vet.py`, `core/tests/`, `reports/tests/test_summary_scope.py` (trên nhánh `claude/toi-va-lich-su-o` gộp cùng AC-21.13: docs/06 → 279 / 266 / 243) | đạt |
| runserver thật, `touch static/js/master-grid.js` rồi tải lại `/dang-nhap/` | `?v=1790579646` → `?v=1790579776`, nhật ký không có dòng khởi động lại |
| Chi phí quét (`timeit`, 200 lần, 32 tệp) | 0,24 ms mỗi lần tải trang |

## Chưa kiểm

- Docker Desktop trên Windows: thời điểm sửa tệp qua bind mount được giữ khi `git pull` (hành vi chuẩn
  của Docker Desktop/WSL2), chưa thử trên máy chủ dự án.
