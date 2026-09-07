# ADR-015 — Năm tính năng nội bộ (Bảng tin, Tài liệu, Công việc, Văn hoá, Tài nguyên) là năm app riêng trong KN ERP, làm bản MVP trước

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | 06.09.2026 |
| Người quyết định | Anh/chị chủ dự án, qua bốn câu hỏi và một câu bổ sung ngày 06.09.2026 |
| Thay thế cho | **Backlog Q2** (không làm quản lý tài nguyên) · **Q8** (bảy module) |
| Liên quan | ADR-004 · ADR-012 · FR-9 → FR-13 · AC-12 → AC-16 · backlog Q63 → Q69, K27, K28, N11, N12, S13 → S17 |

---

## Bối cảnh

Anh/chị gửi ảnh một hệ thống nội bộ kiểu Base Inside (bảng tin có thiệp sinh
nhật, thanh bên có sự kiện và xếp hạng) và yêu cầu làm thêm năm tính năng cho
KN ERP, *"tham khảo và làm bản MVP trước"*, trên một nhánh riêng: **tài liệu**
(phải chia mục), **bảng tin**, **quản lý task**, **ghi nhận văn hoá** (có bảng
xếp hạng doanh số và thưởng, từ đó nhận sao), **tài nguyên**.

Bốn câu hỏi đã chốt cùng ngày:

1. *Tài nguyên là gì?* — Kho tài sản dùng chung; rồi rút gọn thêm: ở MVP chỉ
   cần **một danh sách chia mục cơ bản: BM, Via, Page…**, chưa cần sổ bàn giao.
2. *Bảng tin ai đăng, có sinh nhật không?* — **Mọi người đăng**, Manager và
   Admin ghim hoặc gỡ; **có thiệp sinh nhật tự động**, nên thêm ngày sinh vào
   hồ sơ nhân sự.
3. *Bảng xếp hạng doanh số lấy từ đâu, ai xem?* — **Từ Đơn hàng** theo người
   bán, tháng hiện tại, quy về VND bằng tỉ giá cố định trong cấu hình; **toàn
   công ty xem** hạng và số đơn, không thấy chi tiết đơn.
4. *Sao và thưởng?* — **Một ghi nhận = một sao**; cuối tháng **top 3 doanh số
   nhận 5, 3, 1 sao**; tổng sao hiện ở bảng xếp hạng và hồ sơ.

Trước đó backlog Q2 (27.08.2026) chốt *không làm quản lý tài nguyên và kho
thông tin đăng nhập*. Yêu cầu hôm nay là quyết định lại của anh/chị: làm danh
mục tài nguyên, nhưng **vẫn không lưu mật khẩu** trong đó (FR-13.4).

## Các lựa chọn đã cân nhắc

| Lựa chọn | Ưu | Nhược |
|---|---|---|
| Một app `inside` chứa cả năm mô-đun | Ít tệp, một migration | Năm luật quyền khác nhau dồn một chỗ; khó gỡ riêng một tính năng; trái nếp app theo miền của dự án |
| **Năm app nhỏ** (chọn) | Mỗi app một luật phạm vi, một bộ kiểm thử, gỡ hay mở rộng độc lập; đúng nếp `org`, `reports`, `orders` | Nhiều tệp khung hơn |
| Ghi nhận nhân đôi thành bài trên Bảng tin | Bảng tin sôi động hơn | Tạo vòng phụ thuộc `culture ↔ feed`; hai bản ghi cho một việc |
| Xếp hạng doanh số theo nhãn Người bán trên mọi bảng | Gồm cả Marketing | Khớp theo chuỗi tên, không theo tài khoản; anh/chị chọn Đơn hàng |
| Tỉ giá lấy từ dịch vụ ngoài | Đúng theo ngày | Thêm phụ thuộc mạng và thư viện; MVP chỉ cần con số cố định (S17) |

## Quyết định

1. **Năm app riêng, tên Anh, nhãn Việt:** `feed` (Bảng tin), `documents` (Tài
   liệu), `taskboard` (Công việc), `culture` (Văn hoá), `resources` (Tài nguyên).
   Chiều phụ thuộc một chiều: `feed → culture, org`; `culture → orders`; không
   app nào import `feed`. Thanh bên có nhóm **Nội bộ** với năm mục, mọi cấp
   bậc, mọi bộ phận; phạm vi kiểm ở từng view và manager (quy tắc 11).
2. **Bảng tin toàn công ty.** Bài chỉ có chữ ở MVP. Ai cũng đăng, thích, bình
   luận; gỡ bài là tác giả hoặc Manager trở lên; ghim là Manager trở lên. Thiệp
   sinh nhật do tác vụ nền tạo mỗi sáng từ `UserProfile.birthday`, mỗi người
   mỗi ngày một thiệp (ràng buộc duy nhất). Thanh bên: sinh nhật tháng này, top
   sao, ghi nhận mới, thành viên mới. Bỏ thích là xoá mềm dòng thích.
3. **Tài liệu chia mục theo bộ phận hoặc toàn công ty.** Manager tạo mục cho bộ
   phận mình, Admin tạo mục toàn công ty; Manager trở lên tải lên; mọi người
   trong phạm vi mục xem và tải về qua view có kiểm quyền. Tệp lưu tay dưới
   `STORAGE_DIR/tai-lieu/` (không `FileField`, không route `/media/`, ngoài
   thư mục bị dọn 24 giờ). Thêm PDF và Word vào `FileKind`; Word và Excel cùng
   chữ ký ZIP nên phân biệt bằng đuôi khai báo. Tệp tài liệu **chưa** nằm trong
   bản sao lưu `pg_dump` (K27).
4. **Công việc có phạm vi như dữ liệu khác:** Staff thấy việc mình nhận hoặc
   tạo, Leader thấy team, Manager cả bộ phận, Admin tất cả; giao việc chỉ cho
   người trong `UserProfile.objects.in_scope`; bốn trạng thái, chuyển theo bảng
   cố định; đổi trạng thái bằng HTMX thay đúng một dòng.
5. **Văn hoá:** ghi nhận không tự ghi nhận mình, không xoá được ở MVP (như báo
   cáo đã nộp, để sao không lệch — S16 nếu cần); mỗi ghi nhận sinh một dòng
   sao. Bảng xếp hạng doanh số đọc `orders.Order` toàn công ty — **ngoại lệ
   phạm vi có chủ ý** vì là chỉ số gộp cho văn hoá, không lộ chi tiết đơn;
   quy đổi VND bằng `EXCHANGE_RATES_VND` (Decimal, một chỗ trong settings, đè
   bằng biến môi trường; số mặc định là số tạm — N11). Thưởng tháng chạy ngày
   1 bằng Celery beat và bằng lệnh `thuong_sao_thang --thang` khi cần chạy tay;
   ràng buộc duy nhất (người, kỳ, nguồn) nên chạy lại không nhân đôi.
6. **Tài nguyên là danh mục dùng chung:** mọi người đã đăng nhập xem toàn bộ,
   Manager trở lên thêm mục và thêm, sửa, gỡ; không sổ bàn giao (S13).
7. **Ngày sinh** là cột mới trên hồ sơ nhân sự (org migration 0003), sửa được ở
   màn hình hồ sơ, có trong dữ liệu mẫu để bản demo có thiệp.

## Lý do

Mỗi tính năng có luật quyền riêng và vòng đời riêng, nên tách app giữ được nếp
"một chỗ duy nhất áp phạm vi" của dự án. Bản MVP cố ý bỏ ảnh, ảnh đại diện,
kanban, sổ bàn giao và tỉ giá tự động để mỗi tính năng chạy thật được trước
(Q22), rồi mở rộng khi anh/chị đã dùng thử.

## Hệ quả

| Được gì | Mất gì | Chỗ cần cẩn thận về sau |
|---|---|---|
| Năm màn hình nội bộ chạy thật trên cùng phân quyền, cùng nhật ký, cùng dữ liệu mẫu | Thêm năm app, năm migration, một nhóm thanh bên | Tệp tài liệu ngoài sao lưu (K27); tỉ giá tạm (N11); giá trị văn hoá mẫu (N12) |
| Bảng xếp hạng và sao dùng số thật từ Đơn hàng | Phạm vi có một ngoại lệ gộp, ghi rõ | Đổi luật ngoại lệ này là đổi ADR, không sửa lặng lẽ |
| Ngày sinh trong hồ sơ, thiệp tự động | Cột mới trên bảng nền tảng | Không dùng ngày sinh cho việc khác mà không hỏi lại |

## Điều kiện xem lại

Khi công ty dùng thật ba tháng: cần ảnh trong bài, sổ bàn giao tài nguyên,
kanban, hay tỉ giá theo ngày thì mở các S13 → S17 thành quyết định mới.
