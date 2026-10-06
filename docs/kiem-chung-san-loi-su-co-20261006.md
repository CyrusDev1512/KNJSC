# Biên bản săn lỗi — Sự cố và chạy dài (06.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Đợt săn lỗi, bước 6 (chủ dự án duyệt, làm trên nhánh `claude/san-loi-tiep`) |
| Tiêu chí | AC-10.13 (hàng đợi chết), AC-10.14 (trang lỗi tiếng Việt, đĩa đầy), AC-10.15 (Postgres khởi động lại) |
| Môi trường | Máy ảo; hệ thống thật (ERP 8020, CRM 8021 bằng `runserver`, Celery worker) trên dữ liệu lượt 04.10 (10.032 vận đơn); thêm **gunicorn đúng tham số VPS** (`gthread`, 2 worker × 4 luồng) ở cổng 8030 cho phần Postgres và chạy dài. Redis của hệ thống thật để riêng cổng 6380 để tắt được mà không đụng pytest |

## A. Tắt Redis (hàng đợi tác vụ nền và bộ đệm CRM)

| Thao tác | Kết quả trước khi sửa |
|---|---|
| Đăng nhập, trang chủ ERP/CRM, lưới, Thống kê CRM, Báo cáo tổng hợp, xuất Báo cáo tổng hợp, nộp báo cáo, Lên đơn | **Đạt**: đều 200, thời gian như lúc Redis chạy (bộ đệm CRM có hạn 0,2 giây, phiên đăng nhập ở DB) |
| Xuất Excel lưới Vận đơn (10.032 dòng, chạy nền) | **LỖI VỪA: treo 19,2 giây rồi trang lỗi 500.** Tác vụ nằm lại "Chờ xử lý" mãi (tác vụ #3 trên hệ thống thử). Gốc: bộ lưu kết quả Celery (cũng là Redis) thử nối lại 20 lần, log ghi "Celery application must be restarted"; lỗi gửi không được bắt |
| Bật Redis lại | Worker tự nối lại, nhận tác vụ mới, xuất xong 10.032 dòng |

Đã sửa:
- `CELERY_TASK_IGNORE_RESULT = True`: không chỗ nào đọc kết quả Celery (tiến độ ở `BackgroundJob`). Gửi lúc Redis tắt
  báo lỗi sau 0,5 giây thay vì 19 giây; bật Redis lại gửi được ngay trong cùng tiến trình.
- `import_service._gui`: gửi với thử lại ngắn (`HANG_DOI_THU_LAI`, dưới 3 giây). Không gửi được thì tác vụ thành
  Thất bại: "Không gửi được vào hàng đợi tác vụ nền: dịch vụ hàng đợi (Redis) đang không chạy…". Dùng chung cho xuất,
  nhập, tính lại cột.
- Xuất lưới báo lời đó ngay trên lưới, không đưa người dùng sang trang tác vụ đã hỏng.

Đo lại trên hệ thống thật: xuất lưới lúc Redis tắt 0,94 giây, ở lại lưới với lời báo đỏ.

## B. Đầy đĩa `storage` (ổ tmpfs 1 MB đã ghi đầy)

| Thao tác | Kết quả trước khi sửa |
|---|---|
| Tải tài liệu (Nội bộ → Tài liệu) | **LỖI VỪA: trang lỗi 500** (`OSError: [Errno 28] No space left on device`), không ai được báo |
| Nhập tệp vào bảng (bước tải lên) | **Trang lỗi 500**, cùng gốc |
| Xuất lưới chạy nền | Tác vụ Thất bại sau 2 phút với lời chung chung "Xuất thất bại vì lỗi hệ thống" |
| Lưới, Báo cáo tổng hợp, xuất Báo cáo tổng hợp (dựng trong bộ nhớ) | **Đạt** |

Phát hiện kèm: dự án **không có `500.html` và `404.html`**. Trên VPS (DEBUG tắt) mọi lỗi 500 là trang trắng chữ Anh
"Server Error (500)", đường dẫn sai là "Not Found" — trái NFR-6.

Đã sửa:
- `templates/500.html` tự đứng (không kế thừa khung, không `{% static %}`: lúc lỗi có thể chính DB hay tệp tĩnh hỏng),
  có nền tối; `templates/404.html` cùng khuôn với 403.
- `core.middleware.DiskFullMiddleware`: lỗi ENOSPC/EDQUOT ở bất kỳ view nào → 507 "Máy chủ hết chỗ lưu tệp, tệp chưa
  được lưu", và `core.alerts.bao_het_dia` báo người vận hành (mỗi tiến trình tối đa một thư mỗi 10 phút).
- Tác vụ xuất nền gặp đĩa đầy: lời "hết chỗ lưu tệp" và báo người vận hành.

Đo lại: tải tài liệu và nhập tệp đều 507 với lời tiếng Việt; tác vụ xuất Thất bại với lời "hết chỗ lưu tệp".

## C. Khởi động lại Postgres

| Thao tác | Kết quả trước khi sửa |
|---|---|
| `runserver`, yêu cầu liên tục trong lúc khởi động lại | Lỗi 500 trong khoảng 1–2 giây Postgres tắt (đúng, không tránh được), rồi tự hồi phục; phiên đăng nhập còn |
| Worker sau khi Postgres khởi động lại | **Đạt**: nhận và chạy xong tác vụ xuất |
| **gunicorn như VPS**: làm nóng 16 yêu cầu, khởi động lại Postgres, **đợi Postgres chạy lại 3 giây**, bắn 3 lượt × 16 yêu cầu | **LỖI VỪA: lượt đầu 8/16 lỗi 500** — đúng bằng số kết nối gunicorn đang giữ (`CONN_MAX_AGE` 60). Postgres đã khoẻ mà người dùng vẫn gặp lỗi, kể cả lúc đang lưu. Trên VPS (3×4 + 2×2 luồng) tới 16 yêu cầu |

Đã sửa: `CONN_HEALTH_CHECKS = True` — Django kiểm kết nối giữ lại trước yêu cầu đầu tiên dùng nó. Đo lại: **0/48 lỗi**.
Cái giá: một lượt hỏi Postgres rất nhẹ ở đầu mỗi yêu cầu có dùng DB.

## D. Chạy dài

Đang chạy (110 phút, gunicorn như VPS, 5 người đọc mỗi giây + 1 người nộp báo cáo mỗi 30 giây); kết quả ghi bổ sung
vào mục này khi xong.

## Bài kiểm

- `crm/tests/test_hang_doi_chet.py` (AC-10.13, AC-10.14): gửi hỏng thành Thất bại; thử lại ngắn; không lưu kết quả;
  xuất lưới lúc Redis tắt; tác vụ xuất gặp đĩa đầy.
- `core/tests/test_trang_loi.py` (AC-10.14): trang 500, 404 tiếng Việt khi DEBUG tắt; đĩa đầy 507 và báo người vận hành.
- `core/tests/test_ket_noi_db.py` (AC-10.15): kết nối bị cắt thì yêu cầu sau tự mở lại.
- Mọi bài đỏ trên mã cũ, xanh sau khi sửa.

## Chưa kiểm

- Đầy ổ của **chính Postgres** (khác ổ `storage`): cần VPS hoặc máy riêng; nên có cảnh báo dung lượng ở tầng máy chủ.
- Mất điện đột ngột giữa lúc ghi: cần máy thật.
- Xuất Excel lưới 10.032 dòng mất khoảng 2 phút trên máy ảo khi máy đang bận chạy bộ kiểm — chưa đo riêng trên VPS.
