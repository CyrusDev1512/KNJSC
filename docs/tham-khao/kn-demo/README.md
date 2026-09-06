# Ảnh tham khảo — bảng tính của KN Demo

Chụp ngày 04.09.2026 từ gói `Kim_Ngan_DEMO.rar` anh/chị gửi, chạy bằng
Playwright trên máy ảo (tài khoản `admin`, cổng 8765). Dùng để đối chiếu giao
diện khi làm Bảng tính của KNJSC (ADR-011).

**Demo là gì.** Một ứng dụng Django riêng ("Kim Ngân DEMO", app `registry`).
Bảng tính của nó là **một bảng tính JSON tự viết** — không dùng thư viện:
model `Spreadsheet(name, data JSON, created_by)`, toàn bộ lưới, công thức
(`=SUM()` và 32 hàm khác), clipboard, hoàn tác, lọc cột nằm trong một tệp
`registry/sheet_detail.html` (1975 dòng), tự lưu cả tài liệu mỗi 1,2 giây.
Đơn hàng lên ở màn hình Lên đơn được ghi thêm thành một dòng vào sheet
"Vận đơn" (mẫu MITA, tiêu đề ở hàng 2). Không phân trang, không phân quyền
theo dòng — khác hẳn nền dữ liệu của KNJSC (ADR-001, ADR-009), nên KNJSC
chỉ lấy **cách nhìn và thao tác**, không lấy cách lưu.

| Ảnh | Nội dung |
|---|---|
| `01-danh-sach-bang-tinh.png` | Trang danh sách bảng tính trong khung hệ thống của demo: mỗi dòng có tên, người tạo, giờ cập nhật, nút Mở / .xlsx / Xóa |
| `02-sheet-van-don.png` | Sheet "Vận đơn" mẫu MITA: khung tối viền vàng, thanh công cụ định dạng, thanh công thức có ô địa chỉ, cột số dòng, chữ cột có nút ▼, hàng tiêu đề xanh ở hàng 2, ô tô màu từng dòng |
| `03-chon-vung-tay-keo-dien.png` | Chọn vùng `C3:F7` bằng kéo chuột: vùng tô vàng nhạt, ô hiện tại viền vàng đậm, tay kéo điền ở góc dưới phải |
| `04-menu-chuot-phai.png` | Menu chuột phải: Cắt · Sao chép · Dán · Chèn/Xóa N hàng · Chèn/Xóa N cột (N = số hàng/cột đang chọn) |
| `05-hop-loc-cot.png` | Bấm ▼ ở cột A: nút chuyển sang trạng thái đang mở, hộp lọc theo giá trị hiện dưới tiêu đề |
| `06-thanh-cong-thuc.png` | Thanh công thức: ô địa chỉ `D4`, chữ `fx`, ô nội dung đang gõ `=SUM(A1:A5)` |
| `07-nhieu-trang-them-dong.png` | Chân trang: nút `+` thêm trang, tab `VẬN ĐƠN` và `Trang 2`, nút `+100 dòng` |
| `08-sheet-chi-phi-ads.png` | Sheet nhỏ "Chi phí Ads theo tuần": tiêu đề vàng ở hàng 1, cột trống tới Z, dòng trống tới 100 — dáng mặc định của một sheet mới |
| `09-che-do-sang.png` | Cùng sheet ở nền sáng: chỉ khung đổi màu, lưới vẫn màu kem |
| `10-bang-mau-nen.png` | Thanh công cụ ở nền sáng khi nút màu nền đang được chọn |

Số đo lấy từ mã demo: hàng cao 25px, cột rộng 100px, cột số dòng 46px, hàng
chữ cột 27px, chữ 13px, viền ô `#e6e0d1`, nền lưới `#fffdf8`, viền chọn
`#b8952b`, bảng 40 màu chữ/nền.
