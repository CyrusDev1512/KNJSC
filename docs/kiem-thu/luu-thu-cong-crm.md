# Kiểm chứng lưu thủ công Vận đơn mới — 10.09.2026

Phạm vi: menu …, nút X và buffer ô trong RAM của `van_don_moi` theo cập nhật
[ADR-021](../quyet-dinh/021-luoi-master-va-thong-ke-crm.md). Không đổi endpoint,
schema/dependency; giữ CAS, biên nhận, quyền và nút gửi các form riêng.

## Kết quả

- `node scripts/kiem-thu-master-working-copy.cjs`: đạt các tình huống buffer,
  Undo/Redo, 2.000 ô, replay và chuẩn hóa giá trị sau lưu.
- Chrome `scripts/kiem-thu-master-manual-ui.cjs`: đạt Enter không gọi lưu,
  X cho Cột/Bộ lọc/lọc cột/Phân công/Chi tiết; refresh tìm giá trị giữ X;
  buffer còn khi đổi chức năng/lọc; lưu cả ô ngoài kết quả hiện tại;
  tải lại bỏ nháp không hỏi; không ghi nội dung khách vào localStorage;
  mất phản hồi gửi lại UUID cũ rồi lưu phần sửa tiếp. Menu trong viewport390px,
  X của hộp Cột vẫn thấy khi cuộn cuối. Ảnh kiểm bằng dữ liệu tổng hợp.
- Chrome `scripts/kiem-thu-master-ui.cjs` (gồm row-height): đạt bấm đúp120ms,
  sửa/copy/dán/Delete/Undo/Redo, xung đột hiện hành và lỗi mạng, phân công/
  mất quyền, cuộn/cache, lọc, resize cột/hàng, wrap và giữ chiều cao local;
  viewport1440/1280/390 và zoom125%. Cache tối đa10 khối trong lượt cuộn.
- `docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 -e POSTGRES_DB=knjsc_manual_checks web pytest crm/tests/test_master_grid.py crm/tests/test_waybill_new.py crm/tests/test_waybill_feedback.py core/tests/test_giao_dien.py tests/test_truy_vet.py --tb=short`:
  **690 passed**, 27,71 giây.
- Cùng lệnh Compose, chạy `pytest tests/test_luong_ba_bo_phan.py --tb=short`:
  **2 passed**, 4,33 giây. Bài xuyên Marketing → Sale → Vận đơn đã dùng
  endpoint JSON/CAS và audit gộp hiện hành; vẫn kiểm endpoint HTML cũ bị409.

Chrome chạy fixture `crm/tests/test_master_browser_server.py` ở cổng8031,
biến `KN_MASTER_BROWSER=1`, database test riêng, 1.302 dòng tổng hợp. Không
ghi lên20 khách mẫu hoặc dữ liệu đang làm việc. Sử dụng Chrome/Playwright
có sẵn trên máy; không cài dependency.

Đọc kiểm tại `http://localhost:8021/bang-tinh/van_don_moi/` bằng `quantri`:
menu Lưu dữ liệu và X Cột đã được phục vụ. Chỉ mở/đóng chức năng, không sửa ô.

## Hồi quy bắt được và giới hạn

- Trước sửa, Enter gửi POST ngay (kiểm manual đỏ). Sau sửa chỉ Ctrl+S/Lưu ghi.
- Undo rồi lưu giá trị đã được server cắt khoảng trắng làm Redo từ chối sai:
  đã thêm hồi quy và cập nhật lịch sử theo giá trị chuẩn hóa.
- Menu mobile tràn trái: đã giới hạn vị trí theo viewport.
- Lần chạy CSS đầu báo biến template `master_grid` là tên lớp: đổi điều kiện
  ra ngoài thuộc tính class, không nới whitelist của bộ kiểm tra.
- Bài xuyên bộ phận cũ gửi payload HTML và đòi audit từng ô nên đỏ; cập nhật
  đúng hợp đồng JSON/nhật ký gộp đã duyệt, không đổi backend để chiều bài cũ.
- Bài tìm giá trị có lần timeout lúc fragment chưa settle; runner chờ HTMX
  settle trước nhập. Giữ kiểm phản hồi thực tế và nút X sau khi thay nội dung.

Chưa chạy lại ma trận tải100k/300k hoặc nhiều người của phiên trước; không
lấy số đo renderer cũ làm số đo buffer mới. Chưa kiểm endurance/sản xuất.
Các câu hỏi quy trình xung đột để bàn sau ở [USER_INQUIRY](../USER_INQUIRY.md).
Theo lựa chọn đã duyệt, tải lại/rời bảng bỏ nháp không hỏi; xuất/lọc/thống kê
chỉ dùng dữ liệu đã lưu. Giới hạn2.000 ô khác nhau chưa lưu, Undo/Redo100 lượt.
