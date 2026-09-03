# ADR-009 — Bảng tính là lưới làm việc của bộ phận Vận đơn, chạy thành dịch vụ riêng

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | 03.09.2026 |
| Người quyết định | Anh/chị chủ dự án, qua bốn câu hỏi ngày 03.09.2026 |
| Liên quan | ADR-002 · ADR-004 · **sửa ADR-006** · FR-7.4 · FR-7.8 · backlog Q26, Q38 → Q45 |

---

## Bối cảnh

ADR-006 tách "công thức tự do" sang một màn hình Bảng tính riêng, và bản dựng
`prototype/bang-tinh*.html` đã thử một engine công thức kiểu Excel. Ngày
03.09.2026 anh/chị gửi tệp thật của bộ phận Vận đơn — `MITA Vận đơn CSKH Nội
bộ CANADA.xlsx` — và yêu cầu:

> *Tạo ra một cái bảng tính có y hệt chức năng như file vận đơn (gồm filter
> theo trường lọc). Tương lai bảng tính sẽ là một subdomain, không chịu tải
> cùng cả hệ thống; "Bảng dữ liệu" là nơi để xem, còn "Bảng tính" ở subdomain
> là nơi để tính toán và làm việc của vận đơn.*

Nhìn vào tệp thật thì thấy nó **không phải bảng tính công thức**. Nó là một
lưới làm việc: 28 cột, mỗi sản phẩm một cột số lượng, lọc theo từng cột, ô
chọn từ danh sách (trạng thái, nhân viên), cột "Lọc trùng" đếm số điện thoại
trùng và tô màu, đơn Hủy tô đỏ, cột đầu và hàng tiêu đề cố định, ghi chú
nhiều dòng. Công thức duy nhất là `COUNTA` đếm dòng ở hàng 3.

---

## Quyết định

1. **Bảng tính là lưới làm việc của Vận đơn trên bảng vận đơn** (`van_don`),
   không phải engine công thức. Công thức tự do của bản dựng **bỏ khỏi phạm vi
   phase 1**; ADR-006 sửa theo: cột tính sẵn vẫn ở Bảng dữ liệu, còn phần
   "gõ công thức tự do" không làm.
2. **Dùng chung một cơ sở dữ liệu.** Lưới đọc và ghi thẳng `DataRecord` của
   bảng `van_don` qua tầng dịch vụ; không có bảng riêng, không đồng bộ hai chiều.
3. **Dịch vụ riêng trong cùng kho mã.** Container `bangtinh` chạy cùng image
   với settings `knjsc.settings.bangtinh` (URLconf thu hẹp, `GRID_ONLY_TABLES`
   rỗng), cổng 8021, tương lai đứng sau subdomain và chia sẻ phiên đăng nhập
   bằng `SESSION_COOKIE_DOMAIN`. Đây là bước đầu của ADR-004 (tách `crm`).
4. **Bảng dữ liệu chỉ xem bảng vận đơn** — sửa Q26. `settings.GRID_ONLY_TABLES`
   liệt kê bảng chỉ xem; `grant_service.can_edit_record` trả False cho bảng
   đó, kiểm ở máy chủ. Các bảng khác vẫn sửa ô như cũ.
5. **Mỗi sản phẩm một cột số lượng** (`sl_<mã sản phẩm>`), tự sinh từ danh mục
   sản phẩm đang bán và điền khi lên đơn. Bảng vận đơn có thêm Địa chỉ, Nhân
   viên vận đơn, Mua lại lần, MKT, Tên người chuyển tiền, Đối soát kế toán.
6. **Trạng thái theo đúng tệp.** Vận đơn tám giá trị (Đã lên đơn, Hủy trước
   giao, Hủy sau giao, Đang giao, Đã nhận hàng, Hẹn lại, Khách vắng, Hoàn
   đơn); thanh toán ba (Đã, Chưa, 1 phần); tiền tệ thêm CAD và PHP. Nhãn cũ
   đổi bằng tệp chuyển đổi có chiều ngược (`orders/0002`).
7. **Sổ danh sách chọn** (`forms_builder.choice_registry`) thay cho trường
   `options` trên `ColumnDef` (backlog K22): `crm` đăng ký danh sách của từng
   cột lúc khởi động; tầng dịch vụ kiểm khi sửa ô và khi nhập tệp, giao diện
   vẽ ô chọn từ cùng danh sách. Trạng thái là danh sách **chặt**; nhân viên
   vận đơn là danh sách **gợi ý** — tệp cũ ghi mã người đã nghỉ, không vì thế
   mà bỏ cả dòng.
8. **Trạng thái lưới sống trên URL** (`f_<cột>`, `sap`, `chieu`, `trung`) để
   chép đường dẫn là chia sẻ được đúng bộ lọc; độ rộng cột và cột ẩn do trình
   duyệt nhớ. Không có model "bảng tính".

---

## Hệ quả

| Được | Mất |
|---|---|
| Vận đơn làm việc trên một màn hình giống tệp họ đang dùng, không phải học lại | Không có công thức tự do — ai cần thì xuất Excel ra mà tính |
| Một nơi sửa duy nhất, không còn hai màn hình cùng sửa một dòng | Nhân viên Vận đơn phải mở địa chỉ thứ hai (8021 / subdomain) |
| Lưới chạy riêng, không kéo dịch vụ chính chậm theo | Thêm một container phải vận hành; phiên qua subdomain cần cấu hình ở Giai đoạn 8 |
| Danh sách chọn kiểm ở máy chủ — không còn gõ tay "Đã Thanh Toán" ba kiểu | Bảng tự tạo vẫn chưa có danh sách chọn cho tới khi làm K22 |

Tệp thật ẩn danh hoá thành `docs/tham-khao/vandon-mau.xlsx` (giữ nguyên mọi
"bẫy": tiêu đề ở hàng 2, hàng công thức, điện thoại dạng số, thời gian dạng
chuỗi) và là thước đo của AC-11.9. Bản dựng `prototype/bang-tinh*.html` giữ lại
làm tư liệu, không dùng.
