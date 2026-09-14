# Vận đơn DB — cấu hình ngày 14.09.2026

Chủ dự án yêu cầu bảng riêng trong CRM, chưa nối với Lên đơn. Tạo bằng service
bảng động hiện có, không sửa mã nguồn ứng dụng, không thêm migration/kiểu trường.
Bảng local: `van_don_db`, ID 5, tên **Vận đơn DB**, bộ phận Vận đơn, bắt đầu trống.
Giữ quyền mặc định của bảng động; không sao chép Grant hoặc bật bảng dùng chung.

Nguồn thứ tự: file `- Cột A ngày lên đơn = Thông tin kh.txt` do chủ dự án gửi.
Dùng lại 25 định nghĩa cột của `van_don_moi`; Đối soát kế toán dùng định nghĩa
`doi_soat` đã có trong `van_don`. Giữ tên, mã, kiểu, danh sách lựa chọn, ý nghĩa
và điều kiện bắt buộc. Không tạo mã trường mới hoặc sửa cấu trúc hai bảng nguồn.
Không có Đơn vị phụ trong bảng mới; không xóa cột hay dữ liệu của bảng nguồn.

| Cột | Nội dung |
|---|---|
| A | Ngày |
| B–F | Chi tiết số nhà, đường → Thành phố → Bang → Quốc gia → Zipcode |
| G | Số điện thoại |
| H–L | Sản phẩm → Số lượng sản phẩm → Giá tiền → Loại tiền → PTTT lên đơn |
| M–P | SALE/CSKH → Phụ trách CSKH → Phụ trách Marketing → Phụ trách Vận đơn |
| Q–R | Mã đơn → Trạng thái vận chuyển |
| S–W | Ngày thanh toán → Tên khách → Số tiền thanh toán → Bill → Ghi chú |
| X–Y | Trạng thái thanh toán → PTTT thực tế |
| Z | Đối soát kế toán |

Các cột hiện có không được nhắc riêng trong file được giữ trong nhóm liên quan.
Tên khách ở nhóm thanh toán theo đúng chữ trong file; không suy thành tên người
chuyển tiền. Bảng độc lập dùng hành vi bảng động hiện có, chưa có luồng nhận đơn
hoặc nghiệp vụ phân công/chi tiết riêng của `van_don_moi`.

Kiểm chứng: giao dịch tạo bảng/cột cùng audit; đọc lại 26 mã/thứ tự và so khớp
toàn bộ thuộc tính với cột nguồn; bảng có 0 DataRecord; view trả 200 và đủ tiêu
đề đúng thứ tự; bộ truy vấn xuất Excel dùng cùng thứ tự. Không chạy kiểm tải
hoặc tuyên bố kiểm E2E ghi dữ liệu cho thay đổi cấu hình này.
Bằng chứng local: `storage/van-don-db-20260914/result.json`.

Đây là cấu hình lưu trong database local, không phải tính năng mới trong Git.
Không commit/push; bảng nguồn và liên kết Lên đơn giữ nguyên.

## Thay thế ngày 15.09.2026 — cấu hình có thể tái tạo

Theo xác nhận của chủ dự án, `van_don_db` phải có trên cả máy mới và VPS thay vì
chỉ tồn tại trong database local. Lệnh `manage.py tao_bang_van_don` nay tạo hoặc
bổ sung bảng này theo đúng 26 cột ở trên, chạy lặp không sinh bảng/cột trùng và
không tạo hay xoá dòng dữ liệu. `deploy/entrypoint.sh` đã gọi lệnh này sau migrate,
vì vậy không cần migration vật lý riêng cho bảng động `TableDef`/`ColumnDef`.
