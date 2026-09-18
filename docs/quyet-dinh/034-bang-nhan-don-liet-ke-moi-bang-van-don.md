# ADR-034 — Bảng nhận đơn liệt kê mọi bảng vận đơn đang có

> **Đã bị thay thế** bởi [ADR-036](036-mot-bang-van-don-duy-nhat.md) cùng ngày: trang Bảng nhận đơn bỏ hẳn; bước nâng cấp cấu trúc `_upgrade_schema` chuyển thành `waybill_service.upgrade_schema`, chạy tự động trong `tao_bang_van_don`.

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã triển khai local, kiểm chứng ở `docs/kiem-chung-gop-y-sau-adr033-20260918.md` |
| Ngày | 18.09.2026 |
| Người quyết định | Chủ dự án (góp ý sau phát hành ADR-033, trả lời trong phiên Claude Code) |
| Thay thế cho | Điều "Bảng cũ `van_don` không được dùng làm đích mới" và cách chọn ứng viên theo bộ phận của ADR-029 |

## Bối cảnh

Trang Bảng nhận đơn (`/cau-hinh/nhan-don/`, ADR-029) lấy ứng viên bằng
`destination_service.candidates()`: mọi bảng đang hoạt động của bộ phận Vận đơn
**trừ `van_don`**. Trên VPS 17.09 trang hiện ba mục: crmThuận, Vận đơn DB và
"Báo cáo công việc Vận đơn" (mờ, vì cùng bộ phận) — thiếu "Vận đơn mới" (`van_don`),
trong khi bảng báo cáo ngày không phải bảng vận đơn lại lọt vào. Chủ dự án yêu cầu:
**trang phải hiển thị tất cả bảng vận đơn đang có**.

## Quyết định

1. `candidates()` liệt kê mọi bảng đang hoạt động **là bảng vận đơn theo nghĩa nghiệp vụ**
   (`_is_waybill_like`): có `workflow = "waybill"`, hoặc là `van_don_moi`, hoặc là `van_don`
   cũ, hoặc thuộc bộ phận Vận đơn và có cột Mã đơn đúng cấu trúc Vận đơn. Không lọc theo
   bộ phận nữa; bảng báo cáo ngày của bộ phận Vận đơn không hiện vì không có cột Mã đơn.
2. Mỗi bảng vẫn đi kèm `eligibility()`: đủ điều kiện thì chọn được, không thì mờ kèm lý do.
   Bỏ lý do cứng "Bảng Vận đơn cũ chỉ giữ dữ liệu lịch sử" khỏi `_schema_error`; `van_don`
   được xét như mọi bảng khác. Chủ dự án muốn `van_don` chọn được; **thực tế bảng cũ thiếu
   cột Loại tiền đúng cấu trúc** (đo local 18.09: "Cột Loại tiền chưa có hoặc không đúng cấu
   trúc Vận đơn"), nên nó hiện ra nhưng chưa chọn được cho tới khi được chuyển đổi cấu trúc.
   Chọn một bảng thiếu cột chuẩn sẽ làm hỏng Lên đơn, nên không nới điều kiện chọn.
3. `configure()` giữ nguyên: vẫn từ chối bảng chưa đủ điều kiện, vẫn khoá và ghi nhật ký.

## Bổ sung 18.09 (chủ dự án chốt): `van_don` là bảng duy nhất của Lên đơn

Chủ dự án chốt "từ giờ bảng Vận đơn mới (`van_don`, 41 cột) là bảng duy nhất của Lên đơn"
và không cần nút chuẩn bị trên giao diện. Vì bảng thiếu cấu trúc chuẩn, `prepare_existing`
được thêm bước **`_upgrade_schema`** (chạy khi `_schema_error` còn báo): tạo cột còn thiếu
theo `waybill_service.COLUMNS` qua `table_service.add_column` (xếp cuối, có nhật ký và
đồng bộ cột tách), đổi cột chữ tự do thành danh sách khi chuẩn yêu cầu, thêm lựa chọn chuẩn
còn thiếu. Không xoá, không đổi tên, không sửa dữ liệu; giá trị cũ ngoài danh sách hiện
"(giá trị cũ)". Sau đó gắn profile Vận đơn như cũ. Lệnh: `manage.py chuan_bi_bang_nhan_don
--table van_don --actor <admin> --expected-rows <số dòng>` rồi chọn trên trang Bảng nhận đơn
(hoặc `destination_service.configure`). Đo local 18.09: 42 → 45 cột (thêm `pttt_thuc_te`,
`phu_trach_vd`, `phu_trach_mkt`; `loai_tien`, `pttt` thành danh sách), 234 dòng nguyên,
đủ điều kiện, đã chọn; Lên đơn ghi `DH-1809-0001` vào `van_don`; lưới `van_don` mở được, còn
cột Trùng. Trên VPS làm lúc phát hành, có backup trước; `van_don` trên VPS có 32 cột nên
lệnh tự tính phần thiếu. Điều "chọn được cần chuyển đổi riêng" ở trên được thay bằng bước này.

## Hệ quả

- Người dùng nhìn thấy đủ ba bảng vận đơn (Vận đơn mới, crmThuận, Vận đơn DB) trên một
  trang, kèm lý do với bảng chưa chọn được.
- `van_don` được bổ sung cấu trúc bằng bước `_upgrade_schema` (mục Bổ sung 18.09) và là bảng
  nhận đơn duy nhất; crmThuận và Vận đơn DB vẫn hiện trên trang nhưng không còn là đích.
- Bảng ba bảng vận đơn ở CLAUDE.md đã đổi theo.

## Kiểm chứng

`crm/tests/test_order_destination.py::test_candidates_list_every_waybill_table` (AC-11.39):
ba bảng vận đơn có mặt, bảng báo cáo và bảng bộ phận khác không; Staff/Leader/Manager
vẫn bị từ chối vào trang (bài có sẵn). Đo local: `candidates()` trả `van_don` (lý do thiếu
Loại tiền), `van_don_moi` (chọn được), `van_don_db` (lý do PTTT thiếu lựa chọn chuẩn ở local).
