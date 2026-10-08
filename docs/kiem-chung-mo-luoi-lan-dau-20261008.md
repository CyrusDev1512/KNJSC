# Biên bản — Vì sao mở bảng tính lần đầu chậm hơn số đã báo (08.10.2026)

| Mục | Nội dung |
|---|---|
| Câu hỏi | Chủ dự án 08.10.2026: "tại sao tôi thấy mở bảng tính lên load lâu hơn thế" — chậm ở **máy local, lần mở đầu** |
| Nhánh | `claude/mo-luoi-lan-dau-nhanh` từ `Staging` `4419643` — chỉ tài liệu, **không đổi mã** |
| Môi trường | Máy ảo; Postgres 16; Redis; `runserver` 8020/8021 như máy local; DB thử 385.034 dòng Vận đơn; Playwright Chromium, mỗi lượt một trình duyệt mới (chưa có cache) |

## 1. Vì sao khác số đã báo

Số báo ở PR #96 và #98 (mở lưới 0,39 s; trang chủ 0,14 s) là **thời gian máy chủ trả lời** cho một yêu cầu, đo khi đã chạy
nóng. Lần mở đầu tiên người dùng thấy còn gồm: bước đăng nhập, trình duyệt tải JS/CSS lần đầu, khối dữ liệu đầu, và dựng
lưới.

## 2. Đo trong trình duyệt — từ lúc bấm Đăng nhập tới khi thấy ô đầu của lưới (385.034 dòng)

| Lượt | Thời gian |
|---|---|
| Ngay sau khi "bật máy" (khởi động lại Postgres, xoá page cache, xoá Redis, chạy migrate/configure như launcher, bật lại dịch vụ) | **1,84 s** |
| Trình duyệt mới, máy chủ đã chạy nóng | **1,24–1,34 s** |
| Mở lại lưới (đã đăng nhập, đã có cache) | **0,34–0,45 s** |

Tách lượt "trình duyệt mới":

| Phần | Thời gian | Ghi chú |
|---|---|---|
| Đăng nhập (POST + chuyển hướng) | 0,66–0,71 s | Riêng **kiểm mật khẩu 0,62 s**: PBKDF2-SHA256 1.000.000 vòng, mặc định của Django 5.2, cố ý chậm để chống dò mật khẩu |
| Trang lưới (HTML) | ~0,04 s | |
| Tải lần đầu 18 tệp JS/CSS (323 KB) | ~0,15–0,25 s | Lần sau trình duyệt dùng cache |
| Khối dữ liệu đầu (`du-lieu/`) | 0,22–0,28 s (sau khi bật máy 0,39 s) | |

## 3. Ba nguyên nhân dự đoán trong kế hoạch — đo từng cái

Đo bằng `do_lan_dau.py`, mỗi kịch bản một trình duyệt mới. Cột giữa tính từ lúc bấm Đăng nhập tới khi thấy lưới.

| Kịch bản | Bấm Đăng nhập → thấy lưới | Mở lại lưới |
|---|---|---|
| Đã nóng | 1,65 s | 0,43 s |
| Chỉ khởi động lại CRM (8021) | 1,76 s | 0,40 s |
| Xoá bộ đệm Redis | 1,62 s | 0,34 s |
| Postgres lạnh (khởi động lại, xoá page cache) | 1,68 s | 0,36 s |
| Cả ba | 1,74 s | 0,42 s |

Lượt này đo chung cả thời gian gõ ô đăng nhập nên cao hơn bảng 2 chừng 0,3 s. So giữa các dòng thì chênh nhau ≤ 0,1 s:
CRM vừa khởi động, Postgres lạnh, Redis trống **không phải** nguyên nhân chính. Vì vậy **không làm** hai sửa đổi đã dự kiến
(launcher gọi thử 8021, lệnh `lam_nong`): không có lợi đo được.

Sáng 08.10, ngay sau khi máy ảo khởi động lại đột ngột, có một lượt đo 5,8 s (khối dữ liệu đầu 5,07 s). Lượt đó không lặp
lại được ở các kịch bản có kiểm soát; nhiều khả năng do Postgres phục hồi sau khi tắt đột ngột và tự chạy vacuum/analyze
cùng lúc.

## 4. Riêng máy local Windows

Chưa đo được ở đây. Hai thứ có thể làm máy local chậm hơn máy ảo:
- Docker Desktop đọc mã, template và JS/CSS qua thư mục gắn từ Windows. `runserver` phục vụ JS/CSS từ đó.
- CPU dành cho Docker ít, nên bước kiểm mật khẩu có thể mất 1–2 s.

Launcher chỉ `git pull` nhánh đang đứng: máy còn ở `main` thì chưa có các bản tăng tốc của #96 và #98.

## 5. Lựa chọn — cần chủ dự án quyết

| # | Cách | Lợi (máy ảo) | Giá |
|---|---|---|---|
| 1 | Giữ nguyên | — | Lần đầu ~1,3 s, sau khi bật máy ~1,8 s |
| 2 | Kiểm mật khẩu bằng Argon2 (Django hỗ trợ sẵn, cần thư viện `argon2-cffi`). Mật khẩu cũ tự đổi sang khi người dùng đăng nhập | Bớt ~0,5 s mỗi lần đăng nhập, vẫn chống dò mật khẩu tốt | Thêm một thư viện — phải được duyệt (quy tắc 8) |
| 3 | Trang chủ và thư mục CRM tải sẵn (prefetch) JS/CSS của lưới | Bớt ~0,2 s lần mở lưới đầu, hơn nữa ở máy Windows | Sửa một template, không thêm thư viện |

Không đề xuất giảm số vòng PBKDF2: nhanh hơn nhưng yếu hơn trước dò mật khẩu.
