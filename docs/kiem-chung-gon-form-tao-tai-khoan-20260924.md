# Kiểm chứng — Gọn form Tạo tài khoản: bỏ Email, ẩn Ngày sinh — 24.09.2026

Nhánh `claude/gon-form-tao-tai-khoan` tách từ `main` (`a120af5`), máy ảo Claude Code.
Chốt của chủ dự án: chỉ đụng form TẠO; màn Sửa hồ sơ giữ ô Ngày sinh (đường nhập cho
thiệp sinh nhật); dữ liệu email cũ giữ nguyên (BR-4). Không migration.

## Kiểm tự động

| Lượt | Kết quả |
|---|---|
| Bài mới AC-1.8 (`org/tests/test_account.py`) | Form tạo không còn `name="email"`/`name="birthday"`; POST không email tạo được (email rỗng, đăng nhập bằng mã, vẫn buộc đổi mật khẩu); màn Sửa còn ô Ngày sinh và lưu được 15.01.1999 |
| `org/` + `feed/` (thiệp sinh nhật AC-13.4/13.5 nguyên trạng) | 0 đỏ |
| `tests/test_truy_vet.py` + docs/06 | 265 tiêu chí, 252 tự động, 229 có bài — khớp |
| 4 test cũ POST kèm `email=` | đã dọn key, vẫn xanh (AC-1.5, AC-37.4) |
| Suite đầy đủ `-m "not trinh_duyet and not cham"` | (điền sau khi chạy) |
| `makemigrations --check` | (điền sau) |

## Chromium (server dev 8020, DB `knjsc_db`, tài khoản `quantri`)

Ảnh ở `docs/kiem-thu/gon-form-tao-tai-khoan-2026-09-24/`, 0 lỗi JavaScript:

| Ảnh | Kết quả |
|---|---|
| `01` | `/nhan-su/moi/` không còn ô Email và Ngày sinh (assert trên HTML thật) |
| `02` | `/nhan-su/<pk>/sua/` vẫn có ô Ngày sinh, không có ô Email |

## Không đổi

Đăng nhập (chỉ tra username/mã — `core/auth_backends.py`), tìm kiếm nhân sự vẫn tra
được email cũ (chỉ đổi chữ placeholder), thiệp sinh nhật Bảng tin, dữ liệu đã có.

## Chưa kiểm

Chưa chạy VPS (không migration nên phát hành chỉ cần image mới).
