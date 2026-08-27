# Hướng dẫn cho AI hỗ trợ viết mã

Đọc file này trước khi sửa bất kỳ mã nguồn nào trong dự án.

---

## Dự án là gì

Hệ thống vận hành nội bộ cho công ty thương mại điện tử xuyên biên giới.
Ba bộ phận Sale, Marketing, Vận đơn làm việc trên cùng một hệ thống, mỗi người
chỉ thấy dữ liệu trong phạm vi quyền của mình.

**Quy mô:** dưới 100 người dùng, tối đa 50 người đồng thời, khoảng 2.000–5.000
bản ghi mới mỗi tháng cho mỗi team.

**Tài liệu đầy đủ nằm ở `docs/`.** Đọc `docs/03-thiet-ke-ky-thuat.md` trước khi
thiết kế bất cứ thứ gì.

---

## Công nghệ

| Thành phần | Lựa chọn |
|---|---|
| Khung ứng dụng | Django 5.2 |
| Cơ sở dữ liệu | PostgreSQL 16 |
| Giao diện | HTMX, không dùng khung giao diện riêng |
| Tác vụ nền | Celery với Redis |
| Đóng gói | Docker Compose |
| Đọc ghi Excel | openpyxl |

Lý do chọn ghi ở `docs/quyet-dinh/005-chon-django.md`.

**Không thêm khung giao diện như React hay Vue.** Bảng dữ liệu là màn hình phức
tạp nhất và HTMX làm được — lọc, sắp xếp, phân trang, sửa từng ô.

---

## Đọc gì trước khi làm

| Việc | Đọc trước |
|---|---|
| Thêm chức năng mới | `docs/02-yeu-cau-san-pham.md` — tìm mã FR tương ứng |
| Sửa cấu trúc dữ liệu | `docs/03-thiet-ke-ky-thuat.md` mục 2 |
| Đụng tới phân quyền | `docs/03-thiet-ke-ky-thuat.md` mục 3 |
| Viết truy vấn | `docs/03-thiet-ke-ky-thuat.md` mục 5 |
| Viết kiểm thử | `docs/04-tieu-chi-nghiem-thu.md` — tìm mã AC tương ứng |

---

## Không được làm

| # | Cấm | Vì sao |
|---|---|---|
| 1 | Viết truy vấn dữ liệu ngoài tầng truy cập | Phạm vi quyền phải áp ở một chỗ duy nhất |
| 2 | Đặt quy tắc nghiệp vụ trong tầng xử lý yêu cầu | Tác vụ nền không dùng lại được |
| 3 | Lọc dữ liệu theo quyền ở tầng giao diện | Gọi thẳng đường dẫn là lộ dữ liệu |
| 4 | Xoá cứng bản ghi | Quy tắc BR-4, xoá là đánh dấu |
| 5 | Sửa tệp chuyển đổi cấu trúc đã chạy | Luôn tạo tệp mới |
| 6 | Ghi dữ liệu nhạy cảm vào nhật ký ứng dụng | Kể cả khi gỡ lỗi |
| 7 | Sửa hoặc xoá bản ghi nhật ký hoạt động | Quy tắc BR-6 |
| 8 | Thêm thư viện mới mà không hỏi trước | Mỗi thư viện là một phụ thuộc phải bảo trì |
| 9 | Dùng số thực dấu phẩy động cho tiền tệ | Quy tắc BR-8, cộng tiền bị sai số |
| 10 | Lấy toàn bộ bảng trong màn hình danh sách | Quy tắc Q4 |
| 11 | Dùng `.objects.filter()` trực tiếp cho dữ liệu có phạm vi quyền | Phải qua Custom Manager |
| 12 | Dùng Django Admin cho nghiệp vụ hằng ngày | Admin bỏ qua tầng dịch vụ, chỉ dùng cho quản trị viên |

---

## Bắt buộc làm

| # | Quy tắc |
|---|---|
| 1 | Mọi màn hình danh sách phải có phân trang, mặc định 25 dòng |
| 2 | Truy vấn có quan hệ phải lấy sẵn dữ liệu liên quan trong cùng một lệnh |
| 3 | Mỗi đường dẫn mới phải có kiểm thử cho cả ba cấp bậc, gồm cả trường hợp bị từ chối |
| 4 | Mỗi thay đổi cấu trúc dữ liệu phải kèm tệp chuyển đổi đảo ngược được |
| 5 | Mọi thời gian lưu theo giờ quốc tế, hiển thị theo giờ Việt Nam |
| 6 | Mọi số tiền lưu dạng số thập phân chính xác |
| 7 | Các giá trị cố định khai báo ở một chỗ duy nhất, không viết rải rác |
| 8 | Truy cập ngoài phạm vi quyền phải trả lỗi từ chối, không trả danh sách rỗng |
| 9 | Cột dùng để lọc hoặc tìm kiếm phải có chỉ mục |
| 10 | Docstring của hàm kiểm thử phải ghi mã tiêu chí nghiệm thu tương ứng |
| 11 | Phạm vi quyền áp bằng Custom Manager, không viết điều kiện lọc ở từng view |
| 12 | Cột JSON dùng để lọc phải có chỉ mục GIN |

---

## Quy ước đặt tên

| Đối tượng | Ngôn ngữ | Ví dụ |
|---|---|---|
| Tên biến, hàm, lớp | Tiếng Anh | `get_user_scope`, `OrderItem` |
| Tên bảng và cột trong cơ sở dữ liệu | Tiếng Anh | `daily_report`, `created_at` |
| Nhãn hiển thị trên giao diện | Tiếng Việt | "Báo cáo hằng ngày" |
| Thông báo lỗi cho người dùng | Tiếng Việt | "Bạn không có quyền truy cập" |
| Chú thích trong mã nguồn | Tiếng Việt | |
| Thông điệp ghi thay đổi mã nguồn | Tiếng Việt không dấu | |

---

## Kiểm thử

**Mỗi tiêu chí nghiệm thu có một hàm kiểm thử, và docstring ghi mã tiêu chí:**

```
def test_staff_chi_xem_duoc_du_lieu_cua_minh():
    """AC-3.1 — Staff chỉ xem được bản ghi do chính mình tạo"""
```

Nhờ vậy truy vết được hai chiều giữa tài liệu và mã nguồn.

**Kiểm thử phân quyền phải kiểm cả hai chiều:** trường hợp được phép và trường
hợp bị từ chối. Chỉ kiểm chiều được phép thì không phát hiện được rò rỉ dữ liệu.

---

## Định nghĩa hoàn thành

Một việc chỉ được coi là xong khi đủ bốn điều:

| # | Điều kiện |
|---|---|
| 1 | Tiêu chí nghiệm thu tương ứng đã có kiểm thử và đạt |
| 2 | Phân quyền đã kiểm cả trường hợp cho phép và từ chối |
| 3 | Tệp chuyển đổi cấu trúc chạy xuôi và ngược đều được |
| 4 | Không có dữ liệu nhạy cảm nào lọt vào nhật ký |

---

## Khi gặp việc chưa rõ

**Không tự quyết những việc sau — hỏi trước:**

- Thêm hoặc đổi cấu trúc dữ liệu nền tảng
- Thêm thư viện bên ngoài
- Thay đổi cách phân quyền
- Bỏ qua một quy tắc trong danh sách trên

**Với việc chưa rõ khác:** chọn cách đơn giản nhất chạy được, ghi lại lựa chọn
đó vào `docs/backlog.md` để xem lại sau.

---

## Trước khi tự viết một thành phần phức tạp

Kiểm tra xem có thư viện mã nguồn mở nào đã giải bài toán đó chưa.
Nếu có, đề xuất trước khi viết — kèm lý do nên dùng hoặc không nên dùng.

Nhưng cũng đừng thêm thư viện cho việc đơn giản. Mỗi phụ thuộc là một thứ
phải bảo trì và cập nhật.

---

## Cấu trúc thư mục

```
kim-ngan-jsc/
├── README.md
├── CLAUDE.md              file này
├── docs/                  tài liệu
├── app/                   mã nguồn ứng dụng
├── config/                cấu hình, không đưa lên kho mã nguồn
├── deploy/                tệp triển khai
└── scripts/               công cụ hỗ trợ
```

**Không đưa lên kho mã nguồn:** tệp cấu hình, tệp cơ sở dữ liệu, bản sao lưu,
tệp người dùng tải lên, khoá bí mật.
