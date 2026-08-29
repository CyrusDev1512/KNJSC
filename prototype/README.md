# Bản dựng giao diện — Kim Ngân JSC

Mười màn hình HTML và CSS tĩnh, cộng một trang danh mục. Chưa nối cơ sở dữ
liệu, chưa có Django. Mục đích là nhìn thấy và bàn về giao diện trước khi viết
mã thật.

**Năm màn hình đã chuyển sang ứng dụng Django thật** nên không còn ở đây:
đăng nhập, tổng quan, nhân sự, nhật ký hoạt động, và màn hình từ chối. Mở
chúng ở `http://127.0.0.1:8020/`.

---

## Chạy

```
cd prototype
python -m http.server 8010 --bind 127.0.0.1
```

Mở `http://127.0.0.1:8010/`

Cổng 8000 trên máy này đang có một ứng dụng Django khác, nên dùng 8010.

---

## Cách quan sát phân quyền

Ô **Xem theo vai trò** ở thanh trên đổi giữa chín vai trò cộng Admin.
Đổi vai trò thì ba thứ đổi theo:

| Đổi gì | Quan sát ở đâu |
|---|---|
| Mục nào trong điều hướng bị khoá | Thanh bên trái |
| Gọi thẳng đường dẫn có bị chặn không | Gõ thẳng `bang-van-don.html` khi đang là Sale |

Điểm thứ hai là AC-3.7. Bản dựng này hiện thông báo từ chối ngay tại chỗ chứ
không trả danh sách rỗng, đúng như FR-3.5. Bản thật của màn hình 403 nằm ở
ứng dụng Django.

---

## Danh sách màn hình

| Tệp | Màn hình | Giai đoạn |
|---|---|---|
| `index.html` | Danh mục màn hình | — |
| `bao-cao-ngay.html` | Nộp báo cáo ngày | 4 |
| `bao-cao-lich-su.html` | Lịch sử báo cáo | 4 |
| `bao-cao-tong-hop.html` | Báo cáo tổng hợp | 6 |
| `len-don.html` | Lên đơn | 5 |
| `bang-van-don.html` | Bảng vận đơn | 3 · 5 |
| `quan-ly-bieu-mau.html` | Quản lý biểu mẫu và bảng | 3 |
| `tao-bieu-mau.html` | Trình tạo biểu mẫu | 3 |
| `bang-tinh.html` | Danh sách bảng tính | 5 |
| `bang-tinh-chi-tiet.html` | Bảng tính — engine tự viết | 5 |
| `phan-quyen.html` | Ma trận phân quyền | 1 |

---

## Năm tệp trong `static/`

| Tệp | Sau này thành |
|---|---|
| `tokens.css` | `app/static/css/tokens.css` — chuyển thẳng, không sửa |
| `main.css` | `app/static/css/main.css` — chuyển thẳng, không sửa |
| `layout.js` | `app/templates/base.html` cộng `core/permissions.py` |
| `bang-tinh.css` | `app/static/css/bang-tinh.css` — chuyển thẳng |
| `bang-tinh.js` | `app/static/js/bang-tinh.js` — chuyển thẳng |

`layout.js` chèn thanh bên và thanh trên vào mọi trang, giống hệt cách
`base.html` của Django sẽ làm. Hàm `QUYEN` trong tệp đó là bản nháp của
`core/permissions.py` — mỗi màn hình một hàm kiểm, không màn hình nào tự
viết điều kiện lọc riêng.

Khi có Django, phần kiểm quyền chuyển sang máy chủ. Bản dựng tĩnh kiểm ở
trình duyệt chỉ để xem thử, không phải cách làm thật — nguyên tắc P1.

---

## Quy ước đang áp dụng

| Quy tắc | Thấy ở đâu |
|---|---|
| Nhãn tiếng Việt, tên kỹ thuật tiếng Anh | Mọi nhãn trường đều ghi cả hai |
| Phân trang mặc định 25 dòng | Chân mọi bảng danh sách |
| Số tiền canh phải, chữ đều bề ngang | Lớp `.tien` |
| Giờ quốc tế lưu, giờ Việt Nam hiện | Ghi chú ở chân biểu mẫu báo cáo |
| Xoá là đánh dấu | Ma trận phân quyền, bảng thứ hai |
| Nhật ký không có nút sửa và xoá | `nhat-ky.html` |

---

## Chỗ còn chờ quyết định

Mọi chỗ chưa chốt đều được đánh dấu ngay trên màn hình, kèm mã câu hỏi:

| Mã | Nội dung | Thấy ở màn hình |
|---|---|---|
| A2 · A3 | Quyền Thêm, Sửa, Xoá | `phan-quyen.html` |
| B1 | Phân quyền theo từng bảng động | `tao-bieu-mau.html` |
| B2 | Sale có xem được đơn mình tạo bên vận đơn không | `phan-quyen.html` |
| B3 | Ai được thêm trường | `tao-bieu-mau.html` |
| B5 | Vai trò CSKH | `bao-cao-ngay.html` |
| C1–C4 | Black list, thanh toán, địa chỉ, trạng thái vận chuyển | `bang-van-don.html` |
| C3 | Thị trường theo Quốc gia hay theo Bang | `bao-cao-tong-hop.html` |
| C5 | Công thức ô M5 lệch nhãn | `bao-cao-ngay.html` |
| C6 | Sáu trường lên đơn không có bên bảng vận đơn | `len-don.html` |
| C8 | Có chặn nộp báo cáo muộn không | `bao-cao-lich-su.html` |
| K2 · K3 | Tự sinh bảng, và danh sách nhãn ý nghĩa | `tao-bieu-mau.html` |

Bảy nhãn ý nghĩa trong trình tạo biểu mẫu là **đề xuất**, chưa chốt:
Ngày, Số lượng, Tiền, Tỉ lệ, Người, Sản phẩm, Thị trường.

Lưu ý: `docs/03-thiet-ke-ky-thuat.md` mục 2.5 ghi một danh sách **khác** —
Ngày, Khách hàng, Số điện thoại, Doanh thu, Người bán, Sản phẩm, Trạng thái.
Hai danh sách chưa thống nhất, đã ghi vào backlog dưới mã **N8**.


---

## Bảng tính

Tham khảo bố cục của bản KN Demo: đầu trang, thanh công cụ, thanh công thức,
lưới, chân trang có tab trang tính. Engine tự viết, **không dùng thư viện
ngoài** — đúng ADR-002, và cũng là cách bản demo của họ làm.

**Hàm đã có:** `SUM` `AVERAGE` `COUNT` `COUNTA` `COUNTIF` `SUMIF` `MIN` `MAX`
`IF` `IFERROR` `ROUND` `ABS` `LEN` `LEFT` `RIGHT` `MID` `CONCAT` `TODAY` `NOW`,
cùng bốn phép tính, luỹ thừa, so sánh, ngoặc, tham chiếu ô và vùng `A1:B8`.

**Có sẵn:** chọn vùng bằng chuột và Shift, phím mũi tên, gõ là sửa như Excel,
hoàn tác và làm lại, đậm nghiêng gạch, màu chữ và màu nền, căn lề, xuống dòng
trong ô, định dạng số theo VND USD phần trăm, nhiều trang tính, thống kê vùng
chọn ở chân trang, tải xuống CSV.

**Chưa có:** kéo thả tay cầm để điền, sao chép dán, chèn và xoá dòng cột, lọc
kiểu Excel, gộp ô. Bản demo của họ có những phần này.

### Ranh giới bắt buộc

Trang `Vận đơn` cắm cờ `nguon: "van_don"` và `cot_khoa: 9`, nên cột A–I là bản
sao chỉ đọc — gõ vào thì bị từ chối kèm lời nhắc. Người dùng tính ở cột J trở đi,
đọc được từ vùng khoá nhưng không ghi ngược về bảng gốc.

Đây là quy tắc trong `kien-truc.md`: *sheet không phải nguồn dữ liệu*. Bỏ ranh
giới này là mất cấu trúc dữ liệu và quay lại đúng vấn đề của cách làm bằng Excel.

### Kiểm chứng bằng số liệu thật

Trang `Báo cáo MKT` dùng nguyên số liệu trong ảnh báo cáo Marketing của bản
KN Demo. Bảy dòng nhân viên và dòng tổng cộng đều do công thức tự tính, và khớp
từng đồng với bản của họ — kể cả `6,56%`, `98.094 ₫`, `1.496.335 ₫`, `30,92%`.

**Đơn vị tiền trong bản demo là VND, không phải USD.**
