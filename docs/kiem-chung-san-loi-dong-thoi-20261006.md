# Biên bản săn lỗi — Đồng thời và bấm lặp (06.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án hỏi còn khía cạnh nào để tìm lỗi nghiêm trọng ngoài unit/e2e; đã duyệt đợt săn lỗi 7 bước, đây là bước 1 |
| Tiêu chí | AC-4.12 (nộp báo cáo một lần), AC-6.11 (lưu đơn một lần) |
| Nhánh | `claude/san-loi-dong-thoi` từ `Staging` `87ff1a6` |
| Môi trường | Máy ảo Claude Code trên web; hệ thống thật chạy thẳng (ERP 8020, CRM 8021, Celery, Redis, PostgreSQL 16) trên dữ liệu lượt 04.10: 10.000 vận đơn, 2.040 báo cáo |

## Đã thử

| Kịch bản | Cách làm | Kết quả trước khi sửa |
|---|---|---|
| 20 người lên đơn cùng một giây, 10 người cùng một số điện thoại mới | 20 luồng `requests`, chờ chung một hiệu lệnh rồi cùng POST `/van-don/len-don/` | **Đạt**: 20 đơn, 20 mã `DH-0610-0001…0020` không trùng, chỉ 1 khách cho số điện thoại chung (khoá sinh mã đã tuần tự hoá) |
| Bấm đúp, bấm 3 lần nút "Lưu đơn" | Playwright `dblclick`, 3 lần `click` | **Đạt**: 1 đơn (trình duyệt đã chặn) |
| Bấm đúp, Enter 3 lần nút "Nộp báo cáo" | Playwright | **Đạt**: 1 báo cáo |
| Cùng một lần nộp báo cáo gửi 2 lần cùng lúc, rồi gửi lại lần 3 sau 2 giây (mạng gửi lại; Back rồi Nộp) | `requests`, cùng phiên, cùng dữ liệu | **LỖI NGHIÊM TRỌNG**: thành **3 báo cáo**. Doanh số và CPQC trong Báo cáo tổng hợp bị cộng gấp ba |
| Cùng một lần Lưu đơn gửi 2 lần cùng lúc | `requests` | **LỖI NGHIÊM TRỌNG**: thành **2 đơn** `DH-0610-0023`, `0024` |
| Bấm Xác nhận nhập tệp hai lần | Đọc mã `import_service.confirm` | **Đạt**: có khoá bảng, `select_for_update`, kiểm trạng thái; lần hai báo "đã được xác nhận rồi" |
| Lưu Chi tiết sản phẩm hai lần | Đọc mã `update_items` | **Đạt**: lưu là thay toàn bộ chi tiết, gửi lặp ra cùng kết quả |

## Đã sửa

Mỗi lần mở form nộp báo cáo hay Lên đơn có một mã lần nộp `ma_lan_nop` (UUID) trong ô ẩn. Máy chủ ghi biên nhận
`core.SubmissionReceipt`, có ràng buộc duy nhất `(người, mã)`. Cách làm cùng khuôn với `GridMutationReceipt` của lưới.

- Hàm `core/submission.run_once` được gọi ở tầng dịch vụ: `daily_service.submit_current(submission_key=…)` và
  `order_service.create_order_once`.
- Lần gửi đầu tạo biên nhận rồi mới ghi. Gửi lại đúng mã thì trả bản đã ghi, kèm lời báo:
  - báo cáo: "Lần nộp này đã được ghi lúc HH:MM, không tạo thêm báo cáo mới";
  - đơn: "Đơn DH-… đã lưu từ lần bấm trước…, không tạo đơn mới".
- Hai yêu cầu cùng lúc: yêu cầu sau chờ ở chỉ mục duy nhất tới khi yêu cầu trước commit.
- Nộp lỗi thì biên nhận quay lui cùng dữ liệu, nên sửa rồi nộp lại với cùng mã vẫn ghi được.
- Form mở từ trước bản sửa (không có mã) vẫn nộp được như cũ.
- Vẫn nộp được nhiều lần trong ngày (AC-4.7), vì mỗi lần mở form là một mã mới.
- Migration `core/0007_submission_receipt` chạy xuôi, ngược, rồi xuôi lại đều được. `makemigrations --check` không
  sinh gì.

## Bài kiểm

- `reports/tests/test_nop_mot_lan.py`: 4 bài, có một bài **hai luồng thật, hai kết nối DB** cùng gửi.
- `crm/tests/test_len_don_mot_lan.py`: 2 bài, cũng có bài hai luồng.
- Cả 6 bài đỏ trên mã cũ: thiếu ô `ma_lan_nop`; đua hai luồng ra 2 báo cáo và 2 đơn. Sau khi sửa: xanh.

## Chưa kiểm

- Bắn lại trên hệ thống thật với bản sửa: gửi cùng lần nộp 2 lần cùng lúc + 1 lần sau → **1 báo cáo**, hai lần sau
  báo "Lần nộp này đã được ghi lúc 08:42"; Lưu đơn tương tự → **1 đơn `DH-0610-0025`**, hai lần sau báo "đã lưu từ
  lần bấm trước". (Mục này đã kiểm, để đây cho đủ vết.)
- Bảng biên nhận chỉ ghi thêm, chưa có lệnh dọn. Mỗi lần nộp một dòng nhỏ: khoảng 100.000 đơn và vài chục nghìn báo
  cáo mỗi năm là chấp nhận được. Ghi vào backlog để xem lại.
