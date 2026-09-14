# Kiểm chứng ERP tập trung, Vận đơn và Bill — 14.09.2026

Phạm vi: nhánh `codex/crm-update-solar-ui`, chưa commit/push/merge `main`.

## Kết quả triển khai

- Dock dưới ERP thu gọn trên mọi trang, chỉ còn nút Menu và nhớ lựa chọn bố cục.
- Bảng dữ liệu ERP tại `/bang/<mã>/` có Tập trung, Công cụ, Fullscreen API và
  Thoát; không thêm trình sửa hay đường ghi ERP.
- `van_don` giữ ID 1 và 222/222 dòng, đổi nhãn thành **Vận đơn mới**, thêm đúng
  một cột Phụ trách CSKH (222 dòng lịch sử đều không có giá trị), giữ cột `ZIP`,
  các cột `sl_*`, và chuyển `don_vi_phu` xuống cuối.
- `van_don_moi` giữ ID 3, nhãn **Vận đơn**, 10.000/10.000 dòng và tiếp tục nhận
  đơn mới. Không seed, không sửa mã `BILL-MAU-*`, không tạo chứng từ/ảnh mẫu.
- Bill sửa như text trong hai lưới CRM. HTTP(S) là liên kết tab mới có
  `noopener noreferrer`; giao thức nguy hiểm chỉ hiển thị chữ.
- `PAYMENT_DOCUMENTS_ENABLED` mặc định tắt. Menu, asset và metadata ảnh không
  được tải; các URL kho trả 404. Test bật cờ vẫn chạy luồng cũ.

## Áp dụng local

Backup trước thay đổi: `storage/backups/knjsc-20260914-213517.dump` (1,6 MB).
Chạy `tao_bang_van_don` hai lần đều trả 42 cột. Hash cặp ID/mã của 41 cột cũ
`van_don` trước/sau cùng là
`38c5b3b30ae57598ae327fdc712f914044c770365ca2404d5754c3703f571207`;
quyền hai bảng không đổi. Bản backup được phục hồi vào database tạm để đối chiếu,
sau đó database tạm đã gỡ. Chỉ restart `web` và `bangtinh`; entrypoint báo không
có migration mới để áp dụng. Hai trang đăng nhập 8020/8021 trả 200.

## Kiểm thử

- Nhóm Django liên quan: `crm/tests/test_waybill_new.py`,
  `crm/tests/test_master_grid.py`, `crm/tests/test_payment_documents.py`,
  `forms_builder/tests/test_man_hinh_bang.py`, `core/tests/test_giao_dien.py` — đạt.
- `scripts/kiem-thu-erp-table-focus.cjs`: 2/2 viewport 1440 và 390 đạt, không có
  lỗi console; có Fullscreen API, Esc theo lớp, trạng thái dock sau reload và ERP
  không có trình sửa ô. Đã xem ảnh sáng desktop và tối mobile.
- `scripts/kiem-thu-bill-text-ui.cjs`: đạt trên database Solarpunk cô lập; giá trị
  thử được khôi phục bằng Undo sau lượt kiểm.
- Full suite cuối: **2.332 passed, 15 failed, 31 skipped, 2 xfailed** trong
  448,37 giây. Cả 15 lỗi đều thuộc baseline nhánh hợp nhất đã ghi trước (cơ cấu
  Kế toán/máy sạch, điều hướng Lên đơn cũ, ma trận quyền cũ và truy vết tài liệu).
  Lượt đầu có thêm sáu lỗi vì test khói còn yêu cầu endpoint Chứng từ tắt chuyển
  đăng nhập; cập nhật test đúng hợp đồng 404 rồi lượt cuối trở về đúng 15 lỗi nền.

## Giới hạn

Không tạo 100 bill placeholder và không dùng hai ảnh tham khảo. Chưa commit/push.
