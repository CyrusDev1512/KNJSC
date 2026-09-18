# ADR-036 — Một bảng vận đơn duy nhất: "Vận đơn mới" (`van_don`)

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã triển khai local, kiểm chứng ở `docs/kiem-chung-mot-bang-van-don-20260918.md`; VPS chờ phát hành |
| Ngày | 18.09.2026 |
| Người quyết định | Chủ dự án (ba câu hỏi trả lời trong phiên Claude Code) |
| Thay thế cho | ADR-018 phần "hai bảng độc lập" (crmThuận song song bảng cũ); toàn bộ ADR-029 và ADR-034 (Bảng nhận đơn); điều "bắt buộc Chi tiết sản phẩm khi tạo dòng" của ADR-018/021 |

## Bối cảnh

Từ ADR-018 (08.09) hệ thống có hai bảng vận đơn: `van_don` (lịch sử, 32 cột theo tệp
thật, không profile) và `van_don_moi` crmThuận (25 cột, profile Vận đơn: chi tiết sản
phẩm, phân công, tiền theo quốc gia). 14.09 thêm Vận đơn DB (`van_don_db`) theo tệp chủ
dự án; 15.09 thêm trang Bảng nhận đơn để Admin chọn đích (ADR-029), 18.09 sáng mở rộng
danh sách và nâng `van_don` thành đích duy nhất của Lên đơn (ADR-034).

Chủ dự án chốt 18.09 chiều: **cả hệ thống sau này chỉ dùng một bảng vận đơn, tên hiển
thị hiện tại "Vận đơn mới"** (`van_don`). Ba câu đã hỏi và trả lời:

| Câu | Trả lời |
|---|---|
| crmThuận (VPS 2 dòng) và Vận đơn DB (VPS 6.667 dòng) xử lý sao? | **Xoá cứng cả hai** |
| Trang Bảng nhận đơn còn cần không? | **Bỏ hẳn** |
| Profile Vận đơn bắt buộc Chi tiết sản phẩm khi tạo dòng; 11 dòng thật và tệp Excel cũ không có | **Cho phép dòng không có chi tiết**; có thì vẫn kiểm tổng khớp |

## Quyết định

1. **`van_don` là bảng vận đơn duy nhất.** `ACTIVE_WAYBILL_TABLE_CODE = WAYBILL_TABLE_CODE =
   "van_don"`. Profile Vận đơn (`waybill_service`) đăng ký theo mã này và `workflow="waybill"`.
   Lên đơn (`dispatch_service.push`) ghi thẳng vào `waybill_table()`, không còn chọn đích.
2. **Cấu trúc bảng** = 25 cột chuẩn `waybill_service.COLUMNS` (thứ tự chuẩn) + 9 cột giữ từ
   tệp thật (`dispatch_service.EXTRA_COLUMNS`: Danh sách đen, Đối soát kế toán, Mua lại lần,
   Nhân viên vận đơn, MKT, Tên người chuyển tiền, Đơn vị phụ, Facebook, Email) + cột số lượng
   theo sản phẩm `sl_*` (AC-11.8). `ensure_waybill_table` (gọi từ `tao_bang_van_don` khi bật
   máy) tạo bảng trên máy sạch và **nâng cấp tại chỗ** bảng đang có: thêm cột thiếu, đổi cột chữ
   thành danh sách chuẩn, gắn nhãn ý nghĩa, đặt bắt buộc cho Mã đơn/Tên khách/SĐT/Ngày/Loại
   tiền, `workflow="waybill"`, dùng chung, tên "Vận đơn mới". Không xoá cột, không đổi tên cột,
   không sửa dữ liệu (`waybill_service.upgrade_schema`, chuyển từ ADR-034).
3. **Hook lưới gộp** (`crm/services/waybill_grid.py`): cột ảo Trùng và màu trạng thái của lưới
   cũ gộp với detail/assignment/protected/bill của profile. TL-35/36 đóng: Trùng có trên bảng
   duy nhất.
4. **Dòng không có Chi tiết sản phẩm** vẫn tạo được (nhập tệp, thêm dòng tay, dữ liệu giả):
   giữ số lượng, giá, tiền thu như nhập (chỉ kiểm định dạng tiền); có chi tiết thì tổng phải
   khớp như cũ. Lên đơn luôn sinh chi tiết. Thống kê vẫn đếm "đơn thiếu chi tiết".
5. **Xoá hẳn Bảng nhận đơn**: trang `/cau-hinh/nhan-don/`, mục sidebar, `destination_service`,
   lệnh `chuan_bi_bang_nhan_don`, cột `TableDef.receives_orders` (migration 0014, đảo được).
   Giữ `delivery_view_version` vì lưới còn dùng để ép tải lại.
6. **Xoá cứng crmThuận và Vận đơn DB** bằng lệnh `manage.py xoa_bang_van_don_cu
   --dong-y-xoa-cung --backup-da-lam`: một giao dịch, xoá dòng, chi tiết, phân công, lịch sử ô,
   biên nhận, quyền, nguồn báo cáo, cột rồi bảng; đơn ERP đang trỏ tới dòng bị xoá **giữ đơn, bỏ
   liên kết**; từ chối khi còn biểu mẫu hay báo cáo ngày trỏ tới; từ chối xoá `van_don`; ghi
   nhật ký DELETE. Chạy được khi DEBUG tắt (VPS) nhưng bắt buộc hai cờ. Đây là **ngoại lệ có
   chủ ý của BR-4** ("xoá là đánh dấu") do chủ dự án quyết; trên VPS chỉ chạy sau backup kiểm
   phục hồi. `waybill_db_service` và lệnh tạo Vận đơn DB bỏ.
7. Dữ liệu giả: `nap_du_lieu_van_don_moi` đổi tên `nap_du_lieu_van_don`, `nap_khach_mau` mặc
   định `van_don`, `seed_perf` ghi thô (bảng có profile thì `create_records_bulk` đi từng dòng).

## Lý do

- Một bảng, một profile, một chỗ để phân quyền, thống kê, báo cáo: hết lẫn "bảng nào đang
  nhận đơn", hết ba bộ cột lệch nhau, hết trang cấu hình mà chỉ một lựa chọn đúng.
- Giữ chín cột legacy vì tệp thật và đặc tả Quản trị nội bộ (sheet Vận đơn) còn dùng Đối soát,
  Danh sách đen; bỏ thì mất dữ liệu 11 dòng thật.
- Chi tiết sản phẩm tuỳ chọn vì dữ liệu thật và tệp cũ không có; bắt buộc thì không nhập được
  gì vào bảng duy nhất.

## Hệ quả

**Được gì:** bớt 2 service, 1 trang, 1 lệnh, 8 tệp test, 3 script; mọi thao tác Vận đơn (Tôi /
Toàn bộ, phân công, chi tiết, chứng từ, Thống kê, Excel) trên một bảng.

**Mất gì:** 6.667 dòng Vận đơn DB và 2 dòng crmThuận trên VPS mất vĩnh viễn sau lệnh xoá (chỉ còn
trong backup). Không còn cách tách bảng nhận đơn theo giai đoạn.

**Chỗ cần cẩn thận về sau:**

- `GRID_ONLY_TABLES` mặc định ERP có `van_don` (ADR-014: ERP chỉ đọc) — đúng ý, dịch vụ CRM để rỗng.
- 11 dòng thật trên VPS không có chi tiết: ô Sản phẩm/Số lượng/Giá tiền/Số tiền TT là ô khoá
  (sửa qua hộp Chi tiết sản phẩm). Muốn sửa tổng thì thêm chi tiết.
- Bộ lọc `?trung=1` và Trùng đếm số điện thoại thô (TL-36) vẫn còn.

## Điều kiện xem lại

Khi công ty cần nhiều bảng vận đơn song song (chi nhánh, năm tài chính) — lúc đó dựng lại cơ chế
chọn đích, không tái dùng ADR-029.
