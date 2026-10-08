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

## 6. So sánh `main` (= mã trước 06.10) và `Staging` — chủ dự án hỏi 08.10.2026

Chủ dự án: "trước khi tối ưu lưới đợt này đâu có load lâu thế… rốt cuộc trước 06.10 và sau thì cái nào nhanh chậm hơn".
`main` (`a73f743`) cùng cây tệp với `Staging` trước 06.10 (`87ff1a6`).

**Cách đo.** Cùng máy ảo, cùng dữ liệu, cùng thao tác. Mỗi mốc mã chạy trên một worktree riêng, DB đi tiến theo migration
của mốc đó.

Trước mỗi mốc:
- `ANALYZE`;
- khởi động lại Postgres, xoá page cache, xoá Redis;
- bật lại ERP và CRM bằng `runserver` như máy local.

Sau đó đăng nhập `vd.manager` rồi đo:
- lần đầu sau khi bật máy;
- đăng nhập tới khi thấy lưới, ba trình duyệt mới, lấy trung vị;
- mở lại lưới sáu lần, lấy trung vị;
- đăng nhập tới trang chủ CRM, chặn ở 30 s.

DB nhỏ gồm `du_lieu_mau` và `nap_du_lieu_van_don` (10.000 dòng). DB lớn là bản sao 385.034 dòng, đưa về cấu trúc
trước 06.10.

Đơn vị trong hai bảng dưới là giây.

**DB 10.000 dòng**

| Mốc | Lần đầu sau bật máy | Đăng nhập → lưới | Mở lại lưới | Khối dữ liệu | Đăng nhập → trang chủ |
|---|---|---|---|---|---|
| **`main`** (trước 06.10) | 1,42 | 1,39 | 0,65 | 0,13 | 1,07 |
| Sau các PR 06.10 (#91–#94) | 1,64 | 1,39 | 0,63 | 0,13 | 1,19 |
| Sau #95 | 1,44 | 1,43 | 0,63 | 0,12 | 1,13 |
| Sau #96 | 1,38 | 1,36 | 0,54 | 0,14 | 1,14 |
| **`Staging`** (sau #98) | **1,29** | **1,19** | **0,43** | **0,10** | **1,01** |
| `Staging`, Redis không với tới (như Docker local) | 1,33 | 1,21 | 0,51 | 0,11 | 1,07 |

**DB 385.034 dòng**

| Mốc | Lần đầu sau bật máy | Đăng nhập → lưới | Mở lại lưới | Khối dữ liệu | Đăng nhập → trang chủ |
|---|---|---|---|---|---|
| **`main`** (trước 06.10) | 5,17 | 3,83 | 2,91 | 0,25 | > 30 |
| Sau các PR 06.10 | 4,58 | 3,88 | 2,99 | 0,24 | > 30 |
| Sau #95 (vừa chạy migration `0017`, xem dưới) | 5,23 | 4,59 | 3,76 | 0,65 | > 30 |
| Sau #96 | 2,26 | 2,08 | 1,21 | 0,23 | > 30 |
| **`Staging`** (sau #98) | **1,88** | **1,34** | **0,47** | **0,10** | **1,11** |
| `Staging`, Redis không với tới | 1,84 | 1,32 | 0,59 | 0,24 | 1,16 |

**Kết luận: `Staging` không chậm hơn `main` ở chỗ nào đo được.**
- Dữ liệu nhỏ: nhanh hơn một chút. Mở lại lưới 0,65 → 0,43 s.
- Dữ liệu lớn: nhanh hơn rõ.
  - Mở lại lưới 2,91 → 0,47 s.
  - Đăng nhập tới lưới 3,83 → 1,34 s.
  - Trang chủ CRM trên 30 s → 1,1 s.
- Đăng nhập khoảng 0,7 s ở mọi mốc, vì kiểm mật khẩu không đổi.

**Ba điều có thể làm máy local thấy chậm dù mã không chậm:**
1. **Ngay sau khi cập nhật lên mã có #95.** Migration `forms_builder/0017` điền khoá mã đơn cho **mọi dòng**, tức ghi lại cả
   bảng một lần.
   - Tới khi Postgres tự dọn dòng chết (autovacuum), đọc lưới chậm hơn. Đo ở dòng "Sau #95": khối dữ liệu 0,24 → 0,65 s,
     mở lại lưới 2,99 → 3,76 s.
   - Trên máy ảo autovacuum chạy sau khoảng 1 phút, máy yếu hơn có thể lâu hơn.
   - Cùng hiện tượng, lượt đo đầu trên DB 10.000 dòng ngay sau khi nạp dữ liệu (chưa có thống kê bảng) cho `main` 4,55 s
     và 2,26 s. Gấp 3 lần, hết ngay khi `ANALYZE`.
2. **Lần cập nhật này dựng lại image** (Django 5.2.6 → 5.2.17). Các yêu cầu đầu sau khi bật lại container chậm hơn.
3. **Docker local chưa trỏ bộ đệm CRM tới Redis.** `deploy/docker-compose.yml` không đặt `CRM_CACHE_URL` (VPS có đặt),
   nên trong container bộ đệm thêm ở #98 trỏ vào `localhost`, không có Redis.
   - Hệ thống vẫn chạy đúng, chỉ không được nhanh thêm.
   - Đo: mở lại lưới 0,47 → 0,59 s ở 385k.

**Đề xuất (chờ duyệt):**
- launcher chạy `ANALYZE` ngay sau `migrate` khi mã đổi;
- `deploy/docker-compose.yml` đặt `CRM_CACHE_URL=redis://redis:6379/2` cho `web` và `bangtinh`.
