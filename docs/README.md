# Tài liệu — Kim Ngân JSC

Thư mục này chứa toàn bộ tài liệu của dự án.

---

## Đọc file nào

| Bạn muốn biết | Đọc |
|---|---|
| Hệ thống làm gì, dành cho ai | `01-tong-quan-san-pham.md` |
| Hệ thống phải làm được gì | `02-yeu-cau-san-pham.md` |
| Làm thế nào — kiến trúc, mô hình dữ liệu | `03-thiet-ke-ky-thuat.md` |
| Thế nào là xong | `04-tieu-chi-nghiem-thu.md` |
| Cách dùng và cách vận hành | `05-huong-dan-va-van-hanh.md` |
| Kiến trúc tổng thể, lộ trình | `kien-truc.md` |
| Sơ đồ dạng hình | `so-do-kien-truc.html` |
| Cấu trúc thư mục mã nguồn | `cau-truc-thu-muc.md` |
| Vì sao chọn cách làm này | `quyet-dinh/` |
| Còn việc gì chưa quyết | `backlog.md` |

---

## Toàn bộ tệp

```
docs/
├── README.md                        file này
│
├── 01-tong-quan-san-pham.md         cho người quyết định phạm vi
├── 02-yeu-cau-san-pham.md           48 yêu cầu có mã, kiểm chứng được
├── 03-thiet-ke-ky-thuat.md          cho người phát triển và AI viết mã
├── 04-tieu-chi-nghiem-thu.md        64 tiêu chí, tham chiếu ngược tới yêu cầu
├── 05-huong-dan-va-van-hanh.md      phần A cho người dùng, phần B cho người vận hành
│
├── kien-truc.md                     kiến trúc tổng thể, lộ trình tám giai đoạn
├── cau-truc-thu-muc.md              cây thư mục mã nguồn, sáu module
├── so-do-kien-truc.html             năm sơ đồ dạng hình
├── backlog.md                       phát hiện và câu hỏi chưa quyết
│
├── quyet-dinh/                      nhật ký quyết định kiến trúc
│   ├── README.md
│   ├── 001-bang-dong-luu-dang-json.md
│   ├── 002-khong-nhung-thu-vien-bang-tinh.md
│   ├── 003-tach-cap-bac-va-bo-phan.md
│   ├── 004-crm-la-module-tach-sau.md
│   └── 005-chon-django.md
│
└── tham-khao/                       dữ liệu và tệp gốc từ khách hàng
    ├── CRM_Tan.xlsx
    ├── vandon-mau.xlsx
    └── kn-demo/                     ảnh chụp giao diện đã duyệt
```

---

## Cách các tệp nối với nhau

```
02-yeu-cau          FR-3.1  Staff chỉ xem dữ liệu của mình
     ↓
03-thiet-ke         mục 3.2  hàm phạm vi, cách áp
     ↓
04-nghiem-thu       AC-3.1  cách kiểm
     ↓
mã nguồn            docstring ghi "AC-3.1"
```

Truy vết được hai chiều — từ tài liệu ra mã, và từ mã về tài liệu — mà không cần công cụ gì.

---

## Quy tắc cập nhật

**Phát hiện mới thì ghi vào `backlog.md` trước, không sửa tài liệu ngay.** Chỉ cập nhật tài liệu sau khi đã quyết định thực hiện.

Sửa tài liệu mỗi lần nghĩ ra gì đó là cách nhanh nhất biến nó thành mớ hỗn độn.

**Quyết định kỹ thuật quan trọng thì ghi vào `quyet-dinh/`.** Mục đã ghi thì không sửa — đổi ý thì ghi mục mới và đánh dấu mục cũ là đã được thay thế.

**Tài liệu nào lỗi thời thì đánh dấu, đừng xoá.** Người đọc cần biết nó từng đúng ở thời điểm nào.

---

## Trạng thái

| Tệp | Phiên bản | Trạng thái |
|---|---|---|
| `01-tong-quan-san-pham.md` | 0.1 | Bản nháp |
| `02-yeu-cau-san-pham.md` | 0.1 | Bản nháp |
| `03-thiet-ke-ky-thuat.md` | 0.1 | Bản nháp, còn 2 điểm chưa quyết |
| `04-tieu-chi-nghiem-thu.md` | 0.1 | Bản nháp |
| `05-huong-dan-va-van-hanh.md` | 0.1 | Bản nháp |
| `kien-truc.md` | 0.1 | Bản nháp |
| `cau-truc-thu-muc.md` | 0.1 | Bản nháp |
| `quyet-dinh/001` tới `005` | — | Đã áp dụng |
| `backlog.md` | 0.1 | Cập nhật liên tục |

---

## Điểm chưa quyết

| # | Nội dung | Chặn giai đoạn |
|---|---|---|
| 1 | Tạo biểu mẫu tự sinh bảng hay luôn chọn bảng có sẵn | 3 |
| 2 | Danh sách nhãn ý nghĩa cuối cùng | 3 và 6 |
| 3 | Lịch nộp báo cáo có bắt buộc đúng giờ không | 4 |

Chi tiết ở `backlog.md`.
