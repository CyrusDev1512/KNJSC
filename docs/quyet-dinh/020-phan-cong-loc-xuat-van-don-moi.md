# ADR-020 — Phân công, bộ lọc và xuất Vận đơn mới

> Bổ sung 10.09.2026: [ADR-021](021-luoi-master-va-thong-ke-crm.md) thay phần bố cục/renderer và thống kê nhúng của Vận đơn mới. Quyền, dữ liệu và nghiệp vụ không đổi.


**Ngày:** 09.09.2026. **Trạng thái:** Đã triển khai theo kế hoạch chủ dự án duyệt.
**Phạm vi:** `van_don_moi`, KN CRM và các đường đọc dữ liệu chung với ERP.
Thay ngoại lệ “mọi nhân viên Vận đơn thấy mọi dòng” của ADR-018 trên bảng mới;
giữ ADR-014 (ERP chỉ đọc), ADR-019 (Lên đơn riêng, giữ Thống kê) và bảng cũ.

## Quyền và dữ liệu

- `WaybillAssignment` liên kết một-một với `DataRecord`, ba FK tài khoản:
  `delivery`, `care`, `marketing`, cùng `version`. Không suy đoán từ họ tên.
  Chưa có bản ghi phân công tương đương ba trường trống, phiên bản 0.
- Admin và Leader/Manager Vận đơn xem toàn bảng và phân công trong bộ phận.
  Nhân viên Vận đơn chỉ xem dòng được giao; bảng dùng chung và grant bảng
  không được vượt giới hạn này. Sale Staff xem dòng mình tạo hoặc được giao
  CSKH; CSKH xem dòng được giao chăm sóc. Các vai trò khác giữ quyền hiện có;
  cột Marketing không cấp quyền xem. Leader/Manager Sale giữ phạm vi hiện có.
- Giao CSKH chỉ thêm quyền xem. Mọi đường ghi kiểm lại phạm vi hiện hành rồi
  kiểm quyền sửa riêng. Áp dụng cả ô, dán, định dạng, xoá/khôi phục và chi tiết.
- Người được giao phải đang hoạt động, không bị khoá tạm: Vận đơn thuộc
  `van-don`; CSKH thuộc `sale` hoặc `cskh`; Marketing thuộc `marketing`.
  Không tạo bộ phận hoặc tài khoản nếu danh sách chưa có.
- Username là mã nhân viên; hiển thị `mã — họ tên`, liên kết bằng ID tài khoản.
  Ba cột phân công chỉ đọc ở lưới; sửa qua hộp Phân công riêng. Nhập tệp có
  giá trị tại ba cột này bị từ chối, không cấp quyền từ chuỗi trong Excel.

## Giao dịch phân công

`GET/POST /van-don/phan-cong/` chỉ cho người được quyền phân công. POST nhận
phiên bản từng dòng và các trường cần đổi: không gửi trường = giữ nguyên;
`null` = bỏ phân công. Khoá dòng cha theo PK tăng dần, so phiên bản rồi ghi
trong một transaction; một dòng xung đột làm toàn bộ lượt rollback, trả 409.
Gửi lại request đã thành công với phiên bản cũ cũng bị từ chối. Audit chỉ
ghi ID tài khoản trước/sau, phiên bản và người thực hiện, không dữ liệu khách.
Các đường ghi khác cũng khoá dòng cha trước khi kiểm lại quyền.

## Lọc và cập nhật

- Hai nhóm lọc nhanh vận chuyển/thanh toán độc lập; giữ toàn bộ trạng thái
  hiện hành, kể cả thanh toán một phần. Sản phẩm/thị trường/Marketing trong
  thanh Bộ lọc, giữ lọc tiêu đề cột, ngày, tìm kiếm, URL và sắp xếp hiện có.
- AND giữa nhóm, OR trong nhóm. Sản phẩm tra `WaybillItem.product.code`, chỉ
  chi tiết chưa xoá, dùng subquery để đơn nhiều sản phẩm không nhân dòng.
  `f_san_pham__trong` dùng chung ở tiêu đề/thanh bên; `sp` vẫn nhận để giữ URL.
  Thị trường là Quốc gia; Marketing tra tài khoản được gán, có “Chưa gán”.
- Phạm vi áp trước lựa chọn, số đếm, lưới, tìm kiếm, thống kê và xuất. Số dòng
  ở danh sách bảng/tổng quan/nhập tệp của CRM và ERP cũng theo phạm vi bảng mới.
- Bỏ/thêm lọc đưa về trang đầu, giữ điều kiện khác và sắp xếp. Chip hiện phía
  trên lưới, bỏ từng nhóm được. Polling bảng mới dùng mốc và số dòng **trong
  phạm vi**, để việc mất một dòng do chuyển giao cũng làm lưới cập nhật.
  Đây là ngoại lệ có giới hạn đối với polling không COUNT của ADR-016;
  không thay polling bảng cũ, không bổ sung SSE/WebSocket.

## Xuất và migration

Excel giữ một đơn một dòng, chi tiết sản phẩm JSON và định dạng hiện có;
thêm mã Sale tạo đơn, Vận đơn, CSKH, Marketing. Mã Sale qua `Order.seller`,
dòng nhập không có liên kết để trống. Xuất tất cả kết quả khớp lọc, không
phụ thuộc trang; giữ ngưỡng trực tiếp/nền và trần số dòng hiện hành.

Worker dựng lại truy vấn theo quyền khi chạy, lưu ID dòng vào summary tác vụ.
Trước tải file nền, kiểm lại cả tập ID; có dòng đã chuyển ra ngoài quyền,
đã xoá, tài khoản bị vô hiệu hoá hoặc file cũ thiếu tập ID thì yêu cầu xuất lại.
File đã tải về máy không thể thu hồi bằng cơ chế này.

Migration `orders.0004` tạo model, `0005` thêm ba định nghĩa cột. Không gán
dòng cũ, không chép hoặc chuyển bảng. Đảo migration bỏ cấu trúc phân công mới;
dữ liệu khách/đơn/chi tiết gốc vẫn giữ. Kiểm đảo chỉ trên database test.
Tệp xuất có phân công muốn nhập thành dòng mới phải bỏ/trống ba cột phân công;
định danh người phụ trách luôn được gán lại qua hộp Phân công.

## Giới hạn

Không quyết H7 (ai nhập tiền/bằng chứng), không khóa thêm giá/số lượng, không
làm nhắc việc/AI, không thay grid hoặc công thức. Chưa nghiệm thu năng lực
100 nghìn khách/năm hoặc 10–20 người nhập liệu liên tục từ các test chức năng.
Xem [tiêu chí nghiệm thu](../04-tieu-chi-nghiem-thu.md),
[test-log](../test-log.md) và [câu hỏi còn mở](../USER_INQUIRY.md).
