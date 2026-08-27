# Kim Ngân JSC — Hệ thống vận hành nội bộ

Hệ thống quản lý vận hành cho công ty thương mại điện tử xuyên biên giới.
Ba bộ phận Sale, Marketing và Vận đơn làm việc trên cùng một nơi, mỗi người
chỉ thấy phần thuộc quyền của mình.

---

## Bối cảnh

Công ty bán hàng sang thị trường nước ngoài, hiện có Canada và Philippines.
Ba bộ phận phối hợp trong một chuỗi:

```
Marketing  →  chạy quảng cáo, thu tin nhắn khách
Sale       →  tư vấn, chốt đơn, lên đơn
Vận đơn    →  giao hàng, theo dõi trạng thái, đối soát thanh toán
```

Mỗi bộ phận hiện dùng biểu mẫu và bảng tính riêng trên nền tảng bên ngoài.
Ba vấn đề phát sinh từ đó:

| Vấn đề | Hệ quả |
|---|---|
| Dữ liệu nằm rời ở nhiều nơi | Không đối chiếu được giữa các bộ phận |
| Không phân quyền được | Ai cũng xem được dữ liệu của người khác |
| Báo cáo tổng hợp làm thủ công | Tốn thời gian, dễ sai lệch |

Mỗi thị trường có cấu trúc dữ liệu khác nhau, nên hệ thống cần cho phép
quản lý tự tạo biểu mẫu và bảng cho thị trường mới mà không cần sửa mã nguồn.

---

## Người sử dụng

| Bộ phận | Cấp bậc | Công việc trên hệ thống |
|---|---|---|
| **Sale** | Staff · Leader · Manager | Nộp báo cáo hằng ngày, lên đơn |
| **Marketing** | Staff · Leader · Manager | Nộp báo cáo hằng ngày, dùng bảng tính |
| **Vận đơn** | Staff · Leader · Manager | Nộp báo cáo hằng ngày, dùng bảng tính |

Phạm vi dữ liệu theo cấp bậc:

```
Staff     →  chỉ dữ liệu của bản thân
Leader    →  toàn bộ team mình phụ trách
Manager   →  toàn bộ bộ phận
```

---

## Đọc file nào

| Bạn là ai | Đọc file nào |
|---|---|
| Chủ doanh nghiệp, muốn biết hệ thống làm gì | `docs/01-tong-quan-san-pham.md` |
| Người duyệt phạm vi trước khi triển khai | `docs/02-yeu-cau-san-pham.md` |
| Người phát triển, hoặc AI hỗ trợ viết mã | `docs/03-thiet-ke-ky-thuat.md` và `CLAUDE.md` |
| Người kiểm thử và nghiệm thu | `docs/04-tieu-chi-nghiem-thu.md` |
| Nhân viên sử dụng hằng ngày | `docs/05-huong-dan-va-van-hanh.md` phần A |
| Người vận hành hệ thống | `docs/05-huong-dan-va-van-hanh.md` phần B |
| Muốn biết vì sao chọn cách làm này | `docs/quyet-dinh/` |
| Muốn biết còn việc gì chưa quyết | `docs/backlog.md` |

---

## Trạng thái tài liệu

| Tài liệu | Trạng thái |
|---|---|
| `README.md` | Bản nháp 0.1 |
| `CLAUDE.md` | Bản nháp 0.1 |
| `01-tong-quan-san-pham.md` | Bản nháp 0.1 |
| `02-yeu-cau-san-pham.md` | Bản nháp 0.1 |
| `03-thiet-ke-ky-thuat.md` | Bản nháp 0.1 |
| `04-tieu-chi-nghiem-thu.md` | Bản nháp 0.1 |
| `05-huong-dan-va-van-hanh.md` | Bản nháp 0.1 |
| `kien-truc.md` | Bản nháp 0.1 |
| `cau-truc-thu-muc.md` | Bản nháp 0.1 |
| `so-do-kien-truc.html` | Bản nháp 0.1 |
| `backlog.md` | Bản nháp 0.1 |
| `quyet-dinh/README.md` | Bản nháp 0.1 |

---

## Trạng thái dự án

| Mục | Nội dung |
|---|---|
| Giai đoạn hiện tại | Phase 1 — thiết kế |
| Phạm vi phase 1 | Xem bảng bên dưới |
| Bản tham khảo giao diện | KN Demo — chỉ tham khảo, không dùng làm nền mã nguồn |

### Trong phạm vi phase 1

| # | Hạng mục | Nội dung |
|---|---|---|
| 1 | Đăng nhập và phân quyền | Ba bộ phận, ba cấp bậc, điều hướng sau đăng nhập |
| 2 | Báo cáo hằng ngày | Biểu mẫu riêng cho từng bộ phận |
| 3 | Báo cáo tổng hợp | Bốn cách nhóm: tổng hợp, theo nhân viên, theo sản phẩm, theo thị trường |
| 4 | Lên đơn | Biểu mẫu tạo đơn, đơn chảy sang bảng vận đơn |
| 5 | Bảng tính | Bảng dữ liệu có công thức, lọc, sắp xếp, nhập xuất Excel |
| 6 | Quản lý biểu mẫu và bảng | Quản lý tự tạo biểu mẫu và bảng cho từng thị trường |

### Ngoài phạm vi phase 1

Những phần sau thuộc các giai đoạn tiếp theo, không triển khai trong phase 1:

- Mảng nhân sự: đánh giá năng lực, đào tạo, chấm công, nghỉ phép, bảo hiểm
- Mảng kế toán: thống kê và đối chiếu
- Mảng kho: hàng sản xuất, vận chuyển, tồn kho, xuất kho
- Trợ lý AI cho Sale và Chăm sóc khách hàng
- Ứng dụng cài đặt từ cửa hàng ứng dụng

---

## Cấu trúc thư mục

```
kim-ngan-jsc/
├── README.md                        file này
├── CLAUDE.md                        quy tắc cho AI hỗ trợ viết mã
├── docs/
│   ├── 01-tong-quan-san-pham.md
│   ├── 02-yeu-cau-san-pham.md
│   ├── 03-thiet-ke-ky-thuat.md
│   ├── 04-tieu-chi-nghiem-thu.md
│   ├── 05-huong-dan-va-van-hanh.md
│   ├── kien-truc.md
│   ├── cau-truc-thu-muc.md
│   ├── so-do-kien-truc.html
│   ├── backlog.md
│   └── quyet-dinh/
├── app/                             mã nguồn ứng dụng
├── config/                          cấu hình, không đưa lên kho mã nguồn
├── deploy/                          tệp triển khai
├── scripts/                         công cụ hỗ trợ
├── tests/                           kiểm thử xuyên module
└── storage/                         tệp tải lên, tệp xuất, bản sao lưu — không đưa lên kho
```

---

## Chạy dự án

Phần này sẽ được bổ sung khi có mã nguồn.

```
Yêu cầu môi trường:   (bổ sung sau)
Cài đặt lần đầu:      (bổ sung sau)
Chạy hằng ngày:       (bổ sung sau)
```

---

## Quy ước

**Ngôn ngữ.** Toàn bộ tài liệu, giao diện và thông báo bằng tiếng Việt.
Tên biến và hàm trong mã nguồn bằng tiếng Anh.

**Tài liệu.** Mỗi tài liệu phục vụ một nhóm người đọc. Không viết nội dung
kỹ thuật vào tài liệu dành cho người dùng, và ngược lại.

**Quyết định.** Mọi quyết định kỹ thuật quan trọng được ghi vào `docs/quyet-dinh/`
kèm lý do. Quyết định đã ghi thì không sửa; nếu thay đổi thì ghi mục mới và
đánh dấu mục cũ là đã được thay thế.

**Phát hiện mới.** Ghi vào `docs/backlog.md` trước, không sửa tài liệu ngay.
Chỉ cập nhật tài liệu sau khi đã quyết định thực hiện.

---

## Liên hệ

| Vai trò | Người phụ trách |
|---|---|
| Chủ sở hữu sản phẩm | (điền tên) |
| Phát triển | (điền tên) |
| Vận hành | (điền tên) |
