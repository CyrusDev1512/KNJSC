# Kiến trúc Kim Ngân JSC

Bản phác thảo để bàn. Mọi phần đều có thể đổi.

---

## Tổng quan hệ thống

```
                        ┌──────────────────┐
                        │  Nhân sự đăng    │
                        │  nhập            │
                        └────────┬─────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Phân quyền             │
                    │  bộ phận × cấp bậc      │
                    └────────────┬────────────┘
                                 │
   ┌─────────────────────────────┼─────────────────────────────┐
   │                             │                             │
┌──▼──────────┐          ┌───────▼────────┐          ┌─────────▼────┐
│  SALE       │          │  MARKETING     │          │  VẬN ĐƠN     │
├─────────────┤          ├────────────────┤          ├──────────────┤
│ Báo cáo ngày│          │ Báo cáo ngày   │          │ Báo cáo ngày │
│ Lên đơn     │          │ Bảng dữ liệu   │          │ Bảng vận đơn │
└──────┬──────┘          └────────────────┘          └──────▲───────┘
       │                                                    │
       └────────────── đơn chảy một chiều ──────────────────┘
```

### Bảy module trong mã nguồn

```
┌──────────────────────────────────────────────────────────────┐
│  dashboard        tổng quan, chỉ đọc, không sở hữu dữ liệu   │
└───────────────────────────┬──────────────────────────────────┘
                            │
     ┌──────────────┬───────┴───────┬──────────────┐
     │              │               │              │
┌────▼─────┐  ┌─────▼─────┐  ┌──────▼──────┐       │
│  orders  │  │  crm      │  │  reports    │       │
│  đơn hàng│  │  khách    │  │  báo cáo    │       │
│  sản phẩm│  │  bảng tính│  │  thống kê   │       │
└────┬─────┘  └─────┬─────┘  └──────┬──────┘       │
     │              │               │              │
     └──────────────┴───────┬───────┘              │
                            │                      │
              ┌─────────────▼──────────┐           │
              │  forms_builder         │           │
              │  biểu mẫu và bảng      │           │
              │  do người dùng tạo     │           │
              └─────────────┬──────────┘           │
                            │                      │
              ┌─────────────▼──────────┐           │
              │  org                   │◄──────────┘
              │  bộ phận · team        │
              │  cấp bậc · tài khoản   │
              └─────────────┬──────────┘
                            │
     ┌──────────────────────▼───────────────────────┐
     │  core                                        │
     │  xác thực · phạm vi quyền · nhật ký · sao lưu│
     └──────────────────────────────────────────────┘
```

**Mũi tên chỉ chiều gọi.** Module trên gọi module dưới. Không có vòng ngược.

`orders` và `crm` là hai module riêng. `orders` giữ đơn hàng và sản phẩm;
`crm` giữ khách hàng và màn hình Bảng tính — lưới kiểu Excel cho mọi bảng
(ADR-004, ADR-009, ADR-010).
Tách ra vì `crm` sẽ thành ứng dụng riêng khi đo được điều kiện ở cuối tài
liệu này, còn `orders` thì ở lại.

Giao diện dùng chung không thành module riêng — nó nằm ở `app/templates/`
và `app/static/`, vì không sở hữu dữ liệu nào.

### Tác vụ chạy nền

```
┌──────────────────┐     ┌──────────────────────────────┐
│  Người dùng bấm  │────▶│  Hàng đợi                    │
│  nhập tệp Excel  │     │  ├── nhập tệp lớn            │
└──────────────────┘     │  ├── xuất báo cáo lớn        │
                         │  ├── sao lưu hằng đêm        │
┌──────────────────┐     │  └── dọn dẹp tệp tạm         │
│  Lịch định kỳ    │────▶│                              │
└──────────────────┘     └──────────────────────────────┘
```

Tác vụ nền gọi cùng tầng dịch vụ với giao diện web — không viết logic hai lần.

## Ai sở hữu dữ liệu gì

| Dữ liệu | Nguồn chính | Ai sửa được |
|---|---|---|
| Tài khoản, mật khẩu | Bảng cố định | Quản trị viên |
| Bộ phận, team, cấp bậc | Bảng cố định | Quản trị viên |
| Định nghĩa trường và biểu mẫu | Bảng cố định | Manager |
| Định nghĩa bảng và cột | Bảng cố định | Manager |
| Báo cáo hằng ngày | Bảng cố định | Người nộp, chỉ một lần |
| Đơn hàng và dòng sản phẩm | Bảng cố định | Người tạo, chỉ một lần |
| Danh mục sản phẩm | Bảng cố định | Manager |
| **Bản ghi trong bảng động** | **Bảng động** | Theo phân quyền từng bảng |
| Nhật ký hoạt động | Bảng cố định | Không ai — chỉ ghi thêm |

**Ranh giới quan trọng:** đơn hàng nằm ở bảng cố định. Khi lên đơn, hệ thống ghi thêm một bản sao sang bảng động — đó là bản sao để vận đơn thao tác, không phải nguồn chính.

---

## Database và VPS

### Giai đoạn đầu

```
VPS KNJSC
├── Reverse proxy
├── KNJSC Web
├── KNJSC Worker
├── Redis / Queue
└── PostgreSQL
     └── knjsc_db
```

Một VPS, một database. Không tách vì chưa có gì để tách.

Cấu hình đề xuất: 2 vCPU, 4 GB RAM, 40 GB SSD, Ubuntu Server 24.04, đặt tại Việt Nam.

### Khi dữ liệu lớn dần

```
VPS KNJSC
├── Reverse proxy
├── KNJSC Web
├── KNJSC Worker
├── Redis / Queue
└── PostgreSQL
     ├── knjsc_db
     └── read replica          ← thêm khi báo cáo làm chậm ghi
```

**Chỉ thêm read replica khi đo được:** báo cáo tổng hợp chạy quá 3 giây, hoặc thao tác ghi chậm đi trong giờ cao điểm.

### Khi thật sự cần tách

```
VPS Ứng dụng                VPS Dữ liệu
├── Reverse proxy           └── PostgreSQL
├── KNJSC Web                    ├── knjsc_db
├── KNJSC Worker                 └── read replica
└── Redis / Queue
```

**Điều kiện chuyển:** CPU máy chủ vượt 70% liên tục, hoặc RAM không đủ cho cả ứng dụng và cơ sở dữ liệu.

Ba sơ đồ trên là đường đi, không phải ba lựa chọn. Bắt đầu ở sơ đồ đầu.

---

## Hệ thống phải chịu được khi từng phần lỗi

### Bảng động lỗi

```
Người dùng mở Tổng quan
    ↓
Bảng động không truy vấn được
    ↓
Tổng quan vẫn hiện Báo cáo, Đơn hàng, Nhân sự
    ↓
Khu vực bảng báo "Dữ liệu bảng tạm thời chưa khả dụng"
```

Tổng quan không được phụ thuộc bắt buộc vào bảng động.

### Tác vụ nền chết

```
Người dùng nhập tệp Excel
    ↓
Tác vụ nền không chạy
    ↓
Hệ thống báo "Đang xử lý, sẽ thông báo khi xong"
    ↓
Người dùng làm việc khác, không bị treo màn hình
    ↓
Quản trị viên thấy cảnh báo tác vụ tồn đọng
```

### Đĩa đầy

```
Sao lưu tự động thất bại
    ↓
Ghi cảnh báo vào nhật ký
    ↓
Gửi thông báo cho người vận hành
    ↓
Hệ thống vẫn cho đọc, chặn thao tác ghi tệp mới
```

**Không được im lặng.** Sao lưu hỏng mà không ai biết là rủi ro lớn nhất trong vận hành.

---

## Cấu trúc repo

```
kim-ngan-jsc/
├── app/
│   ├── core/                 ← xác thực, phân quyền, nhật ký, sao lưu
│   ├── org/                  ← bộ phận, team, cấp bậc, tài khoản
│   ├── forms_builder/        ← định nghĩa trường, biểu mẫu, bảng động
│   ├── reports/              ← báo cáo hằng ngày, báo cáo tổng hợp
│   ├── orders/               ← đơn hàng, sản phẩm, luồng ghi sang bảng
│   ├── crm/                  ← khách hàng, và về sau là bảng tính
│   └── dashboard/            ← tổng quan, chỉ đọc
│
├── config/                   ← cấu hình, không đưa lên kho mã nguồn
├── deploy/
│   ├── docker/
│   ├── reverse-proxy/
│   └── backup/
├── scripts/                  ← sinh dữ liệu mẫu, chuyển dữ liệu
├── tests/
├── docs/
├── CLAUDE.md
└── README.md
```

**Bảy module trong `app/`.** Mỗi module tự chứa mô hình dữ liệu, tầng dịch vụ và giao diện của nó.

Giao diện dùng chung không thành module riêng mà nằm ở `app/templates/` và
`app/static/`, vì nó không sở hữu dữ liệu nào.

`core` là module duy nhất được các module khác gọi vào. Các module còn lại **không gọi trực tiếp nhau** — đi qua tầng dịch vụ.

---

## Lộ trình

### Giai đoạn 1 — Nền móng

```
├── Tạo repo, .gitignore, Docker Compose
├── Chốt cấu trúc dữ liệu lõi
├── Xác thực và quản lý phiên
├── Khung phân quyền: hàm phạm vi duy nhất
├── Nhật ký hoạt động
└── Khung kiểm thử tự động
```

**Ra khỏi giai đoạn khi:** tạo được tài khoản, đăng nhập được, và kiểm thử phân quyền ba cấp đều đạt.

### Giai đoạn 2 — Cơ cấu tổ chức và giao diện chung

```
├── Bộ phận, team, cấp bậc
├── Quản lý tài khoản nhân sự
├── Giao diện và điều hướng chung
├── Điều hướng sau đăng nhập theo bộ phận
└── Màn hình Tổng quan
```

### Giai đoạn 3 — Biểu mẫu và bảng

```
├── Định nghĩa trường: tên, kiểu, nhãn ý nghĩa
├── Trình tạo biểu mẫu
├── Trình tạo bảng
├── Nối biểu mẫu với bảng đích
└── Bảng dữ liệu: hiện, lọc, sắp xếp, phân trang
```

**Đây là giai đoạn rủi ro nhất.** Nếu mô hình bảng động sai thì mọi thứ sau phải làm lại.

### Giai đoạn 4 — Báo cáo hằng ngày

```
├── Biểu mẫu báo cáo riêng từng bộ phận
├── Ghi nhận thời điểm nộp
├── Xem lại báo cáo cũ
└── Leader và Manager xem báo cáo cấp dưới
```

### Giai đoạn 5 — Lên đơn

```
├── Danh mục sản phẩm
├── Biểu mẫu lên đơn, nhiều dòng sản phẩm
├── Ghi một chiều sang bảng vận đơn
├── Lưu mã liên kết đơn và bản ghi
└── Phát hiện khách mua lại theo số điện thoại
```

### Giai đoạn 6 — Báo cáo tổng hợp

```
├── Thống kê theo bốn cách nhóm
├── Lọc theo thời gian và sản phẩm
├── Dòng tổng cộng
└── Xuất Excel
```

### Giai đoạn 7 — Nhập xuất, sao lưu, Bảng tính vận đơn

```
├── Nhập tệp Excel bốn bước, xem trước, tiến độ, dòng lỗi theo hàng Excel
├── Xuất tệp Excel kèm bộ lọc; tệp lớn chạy nền
├── Tác vụ nền có theo dõi (BackgroundJob), đánh dấu kẹt
├── Sao lưu pg_dump hằng đêm, giữ 30 bản, phục hồi có xác nhận; service beat
├── Bảng tính vận đơn theo tệp thật — dịch vụ bangtinh cổng 8021 (ADR-009)
├── Kiểm thử toàn diện: Playwright, Locust, 50.000 dòng, ma trận 45 ô
└── Bảng tính cho mọi bảng: viền ô, dòng trống, cột khoá, thanh lọc trái, định dạng ô, thư mục (ADR-010)
```

### Giai đoạn 8 — Đưa lên máy chủ và hoàn thiện

```
├── Giao diện điện thoại và máy tính bảng
├── Tối ưu: phân trang, chỉ mục, gộp truy vấn
├── Cài đặt máy chủ, kết nối mã hoá, tên miền; subdomain cho Bảng tính
├── Đo tải trên máy chủ thật (kịch bản Locust đã có từ GĐ 7)
├── Thử phục hồi từ bản sao lưu
└── Chuyển dữ liệu thật, đào tạo người dùng
```

---

## CRM — module bây giờ, app riêng về sau

### Giai đoạn đầu: module trong monolith

`crm` là một module trong `app/`, cùng cấp với `org`, `reports`, `forms_builder`.

Không tách vì chưa có gì để tách. Nhưng **chuẩn bị sẵn để tách được**.

### Ba việc chuẩn bị, làm ngay từ đầu

| Việc | Tốn thêm |
|---|---|
| `crm` không truy vấn trực tiếp bảng của module khác, đi qua service | 0 |
| Mọi truy vấn xuyên module đi qua một lớp trung gian | ~5 giờ |
| Bảng của `crm` không có khoá ngoại cứng sang module khác | 0 |

Ba việc này khiến lần tách sau chỉ là đổi lời gọi hàm thành gọi API.

### Điều kiện tách

Không tách theo lịch. Tách khi **đo được** một trong bốn dấu hiệu:

```
CPU máy chủ vượt 70% liên tục trong giờ làm việc
Thao tác của bộ phận khác chậm đi khi CRM chạy nặng
Tác vụ nền của CRM chiếm hết hàng đợi
CRM cần lịch cập nhật riêng, không cùng nhịp với phần còn lại
```

### Hai điều cần biết trước khi tách

**Cô lập lỗi không đến từ việc tách app.** Tách cô lập được lỗi hạ tầng — CPU, sập, khởi động lại. Không cô lập được lỗi logic: sai phân quyền, sai dữ liệu, rò rỉ thông tin. Những lỗi đó theo mã nguồn, không theo container.

**Chịu tải là chuyện của cơ sở dữ liệu, không phải tầng ứng dụng.** Tách app sang máy chủ khác mà vẫn dùng chung một database thì nút thắt không đổi. Muốn tách tải thật thì phải tách cả database — và lúc đó báo cáo tổng hợp phải gọi API thay vì truy vấn thẳng.

### Bảng tính trong CRM

Khi tách thành app riêng, CRM có thêm màn hình bảng tính tự do:

```
crm/khach-hang     bảng cố định — nguồn dữ liệu chính
crm/don-hang       bảng cố định — nguồn dữ liệu chính
crm/bang-tinh      sheet tự do — nơi người dùng tự tính toán
```

**Ranh giới bắt buộc: sheet không phải nguồn dữ liệu.**

Nó đọc từ bảng cố định, người dùng thao tác trên đó, kết quả không ghi ngược lại.

Nếu để sheet ghi ngược thì mất cấu trúc dữ liệu, và quay lại đúng vấn đề của cách làm bằng Excel hiện tại.

---

## Chốt lại

| Mục | Quyết định |
|---|---|
| Hệ thống | Một ứng dụng, modular monolith |
| Cơ sở dữ liệu | Một PostgreSQL, một database |
| Đăng nhập | Trong ứng dụng, không có SSO riêng |
| Repo | Một repo, bảy module trong `app/` |
| Nguồn nhân sự | Module `org` |
| Nguồn đơn hàng | Module `orders`, bảng cố định |
| Bảng vận đơn | Bảng động, nhận bản sao từ đơn hàng |
| Kanban, đa thị trường | Không phải sản phẩm riêng — là cấu hình của biểu mẫu và bảng |
| CRM | Module trong monolith ở giai đoạn đầu, tách thành app riêng khi đạt điều kiện |
| Bảng tính trong CRM | Màn hình riêng, đọc từ bảng cố định, không ghi ngược |
| Tách VPS | Chưa tách, nhưng chuẩn bị kiến trúc để tách được |
| Tác vụ nền | Có từ giai đoạn 1, dùng cho nhập tệp và sao lưu |

---

## Bốn điểm chưa quyết

| # | Nội dung | Chặn giai đoạn nào |
|---|---|---|
| 1 | Khung ứng dụng cụ thể | Giai đoạn 1 |
| 2 | Bảng dữ liệu: cột tính sẵn, chọn phép tính, hay gõ công thức tự do | Giai đoạn 3 |
| 3 | Tạo biểu mẫu tự sinh bảng, hay luôn chọn bảng có sẵn | Giai đoạn 3 |
| 4 | Danh sách nhãn ý nghĩa cuối cùng | Giai đoạn 3 và 6 |

Điểm 1 chặn ngay. Ba điểm còn lại chặn giai đoạn 3, còn thời gian để hỏi người dùng.
