# Cấu trúc thư mục — Kim Ngân JSC

Khung ứng dụng: **Django 5.2 + PostgreSQL 16 + Docker Compose**.

Lý do chọn: ba thứ tốn nhiều giờ nhất trong nền móng — xác thực, phân quyền theo đối tượng, trang quản trị — Django cho sẵn. Bảng động dùng `JSONField` với chỉ mục GIN, thứ PostgreSQL hỗ trợ tốt hơn hầu hết cơ sở dữ liệu khác. Giao diện dùng HTMX thay vì framework riêng, vì hệ thống nội bộ 50 người không cần một ứng dụng một trang.

---

## Toàn bộ cây thư mục

```
kim-ngan-jsc/
│
├── app/                                   mã nguồn ứng dụng
│   ├── manage.py
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   │
│   ├── knjsc/                             cấu hình dự án
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                    cấu hình dùng chung
│   │   │   ├── dev.py                     máy cá nhân
│   │   │   └── prod.py                    máy chủ
│   │   ├── urls.py                        gốc điều hướng
│   │   ├── wsgi.py
│   │   └── celery.py                      cấu hình tác vụ nền
│   │
│   ├── core/                              nền móng, mọi module gọi vào
│   │   ├── models.py                      TimestampedModel, SoftDeleteModel
│   │   ├── scope.py                       hàm phạm vi duy nhất
│   │   ├── permissions.py                 kiểm quyền cấp bậc và bộ phận
│   │   ├── middleware.py                  hết phiên, buộc đổi mật khẩu, chặn cache
│   │   ├── audit.py                       ghi nhật ký hoạt động
│   │   ├── mixins.py                      lớp dùng chung cho view
│   │   ├── exceptions.py                  lỗi nghiệp vụ có mã
│   │   ├── validators.py                  kiểm tra dữ liệu dùng chung
│   │   ├── pagination.py                  phân trang mặc định 25 dòng
│   │   ├── excel.py                       đọc và ghi tệp Excel
│   │   ├── services/
│   │   │   ├── audit_service.py
│   │   │   └── backup_service.py
│   │   ├── tasks.py                       dọn dẹp, sao lưu tự động
│   │   ├── migrations/
│   │   └── tests/
│   │       ├── test_scope.py
│   │       ├── test_permissions.py
│   │       └── test_audit.py
│   │
│   ├── org/                               tổ chức và tài khoản
│   │   ├── models.py                      Department, Team, Position, UserProfile
│   │   ├── services/
│   │   │   ├── account_service.py         tạo, khoá, đặt lại mật khẩu
│   │   │   └── org_service.py             bộ phận, team, gán người
│   │   ├── forms.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── migrations/
│   │   └── tests/
│   │       ├── test_account.py
│   │       └── test_org_scope.py
│   │
│   ├── forms_builder/                     biểu mẫu và bảng do người dùng tạo
│   │   ├── models.py                      FieldDef, FormDef, TableDef, ColumnDef,
│   │   │                                  FormTableLink, DataRecord
│   │   ├── services/
│   │   │   ├── form_service.py            tạo, sửa biểu mẫu
│   │   │   ├── table_service.py           tạo bảng, sinh cột
│   │   │   ├── link_service.py            nối biểu mẫu với bảng, kiểm kiểu
│   │   │   └── record_service.py          ghi, sửa, xoá bản ghi
│   │   ├── meaning.py                     bảy nhãn ý nghĩa và cách dùng
│   │   ├── query.py                       dựng truy vấn động trên bảng
│   │   ├── forms.py
│   │   ├── views/
│   │   │   ├── builder_views.py           trình tạo biểu mẫu và bảng
│   │   │   ├── form_views.py              điền biểu mẫu
│   │   │   └── table_views.py             xem và sửa bảng
│   │   ├── urls.py
│   │   ├── migrations/
│   │   └── tests/
│   │       ├── test_builder.py
│   │       ├── test_link_type_check.py
│   │       └── test_dynamic_query.py
│   │
│   ├── reports/                           báo cáo hằng ngày và tổng hợp
│   │   ├── models.py                      DailyReport, ReportTemplate
│   │   ├── services/
│   │   │   ├── daily_service.py           nộp, khoá sau khi nộp
│   │   │   └── summary_service.py         bốn cách nhóm, bộ lọc
│   │   ├── aggregations.py                phép tính dựa trên nhãn ý nghĩa
│   │   ├── forms.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── tasks.py                       xuất báo cáo lớn chạy nền
│   │   ├── migrations/
│   │   └── tests/
│   │       ├── test_daily_lock.py
│   │       └── test_summary_scope.py
│   │
│   ├── orders/                            đơn hàng và luồng sang vận đơn
│   │   ├── models.py                      Order, OrderLine, Product, ProductGroup,
│   │   │                                  Customer, OrderTableLink
│   │   ├── services/
│   │   │   ├── order_service.py           tạo đơn, khoá sau khi lưu
│   │   │   ├── dispatch_service.py        ghi một chiều sang bảng vận đơn
│   │   │   └── customer_service.py        nhận diện khách mua lại
│   │   ├── forms.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── migrations/
│   │   └── tests/
│   │       ├── test_order_lock.py
│   │       ├── test_dispatch_atomic.py
│   │       └── test_repeat_customer.py
│   │
│   ├── dashboard/                         tổng quan
│   │   ├── services/
│   │   │   └── dashboard_service.py       gom số liệu theo phạm vi người xem
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── tests/
│   │
│   ├── templates/
│   │   ├── base.html                      khung chung, thanh điều hướng
│   │   ├── components/                    thành phần dùng lại
│   │   │   ├── table.html
│   │   │   ├── pagination.html
│   │   │   ├── filter_bar.html
│   │   │   ├── form_field.html
│   │   │   └── empty_state.html
│   │   ├── core/
│   │   ├── org/
│   │   ├── forms_builder/
│   │   ├── reports/
│   │   ├── orders/
│   │   └── dashboard/
│   │
│   ├── static/
│   │   ├── css/
│   │   │   ├── tokens.css                 màu, cỡ chữ, khoảng cách
│   │   │   └── main.css
│   │   ├── js/
│   │   │   ├── htmx.min.js
│   │   │   └── table.js                   lọc, sắp xếp, sửa ô
│   │   └── img/
│   │
│   └── conftest.py                        cấu hình chung cho kiểm thử
│
├── config/                                KHÔNG đưa lên kho mã nguồn
│   ├── .env.example                       mẫu, có đưa lên
│   └── .env                               thật, không đưa lên
│
├── deploy/
│   ├── Dockerfile
│   ├── docker-compose.yml                 máy cá nhân
│   ├── docker-compose.prod.yml            máy chủ
│   ├── entrypoint.sh
│   ├── nginx/
│   │   └── knjsc.conf
│   └── systemd/
│       └── knjsc-backup.timer
│
├── scripts/
│   ├── setup.sh                           cài lần đầu
│   ├── deploy.sh                          cập nhật lên máy chủ
│   ├── backup.sh                          sao lưu thủ công
│   ├── restore.sh                         phục hồi
│   ├── seed_demo.py                       dữ liệu mẫu để xem
│   └── seed_perf.py                       sinh 50.000 bản ghi để đo hiệu năng
│
├── storage/                               KHÔNG đưa lên kho mã nguồn
│   ├── uploads/                           tệp người dùng tải lên
│   ├── exports/                           tệp xuất ra, dọn sau 24 giờ
│   └── backups/                           bản sao lưu, giữ 30 bản
│
├── tests/                                 kiểm thử xuyên module
│   ├── test_permission_matrix.py          ma trận chín vai trò
│   ├── test_order_to_table_flow.py        trọn luồng lên đơn
│   └── test_excel_roundtrip.py            xuất rồi nhập lại
│
├── docs/
│   ├── 01-tong-quan-san-pham.md
│   ├── 02-yeu-cau-san-pham.md
│   ├── 03-thiet-ke-ky-thuat.md
│   ├── 04-tieu-chi-nghiem-thu.md
│   ├── 05-huong-dan-va-van-hanh.md
│   ├── kien-truc.md
│   ├── backlog.md
│   ├── quyet-dinh/
│   │   ├── README.md
│   │   ├── 001-chon-django-va-htmx.md
│   │   ├── 002-khong-dung-thu-vien-bang-tinh.md
│   │   ├── 003-tach-cap-bac-va-bo-phan.md
│   │   └── 004-bang-dong-dung-jsonfield.md
│   └── tham-khao/
│       ├── CRM_Tan.xlsx
│       ├── vandon-mau.xlsx
│       └── kn-demo/                       ảnh chụp giao diện đã duyệt
│
├── .gitignore
├── .dockerignore
├── CLAUDE.md
└── README.md
```

---

## Sáu module trong `app/`

| Module | Sở hữu dữ liệu gì | Gọi vào ai |
|---|---|---|
| `core` | Không sở hữu dữ liệu nghiệp vụ | Không gọi ai |
| `org` | Bộ phận, team, cấp bậc, tài khoản | `core` |
| `forms_builder` | Định nghĩa biểu mẫu, bảng, bản ghi động | `core`, `org` |
| `reports` | Báo cáo hằng ngày | `core`, `org`, `forms_builder` |
| `orders` | Đơn hàng, sản phẩm, khách hàng | `core`, `org`, `forms_builder` |
| `dashboard` | Không sở hữu, chỉ đọc | Tất cả |

**Quy tắc phụ thuộc:** module chỉ gọi module nằm trên nó trong bảng. Không có vòng.

`orders` cần ghi sang bảng động, nên nó gọi `forms_builder` — không phải ngược lại.

---

## Vì sao mỗi module có thư mục `services/`

Đây là chỗ chứa quy tắc nghiệp vụ, tách khỏi `views.py`.

```
views.py         nhận yêu cầu, kiểm quyền, gọi service, trả kết quả
services/        quy tắc nghiệp vụ — không biết gì về HTTP
tasks.py         tác vụ nền, cũng gọi cùng service đó
```

Nhờ vậy tác vụ nền và giao diện dùng chung một luật. Không có nó thì phải viết logic hai lần, và hai bản sẽ lệch nhau.

**Ví dụ cụ thể:** `dispatch_service.ghi_sang_bang_van_don()` được gọi từ hai chỗ — khi Sale lưu đơn trên web, và khi nhập hàng loạt từ tệp Excel chạy nền.

---

## Ba thư mục không đưa lên kho mã nguồn

```
config/.env          mật khẩu cơ sở dữ liệu, khoá bí mật
storage/             tệp người dùng, bản sao lưu, tệp xuất
app/staticfiles/     sinh ra khi triển khai
```

Nội dung `.gitignore`:

```gitignore
config/.env
!config/.env.example
storage/
staticfiles/
*.pyc
__pycache__/
.venv/
*.sqlite3
*.pgdump
.pytest_cache/
.coverage
```

---

## Vì sao `tests/` nằm ở hai nơi

| Nơi | Kiểm gì |
|---|---|
| `app/<module>/tests/` | Trong một module — service, model, view |
| `tests/` ở gốc | Xuyên module — ma trận phân quyền, trọn luồng lên đơn |

Ba tệp ở gốc là ba thứ dễ hỏng nhất và không thuộc module nào:

**`test_permission_matrix.py`** — chín vai trò nhân bảy đường dẫn. Đây là bài kiểm thử quan trọng nhất trong dự án.

**`test_order_to_table_flow.py`** — Sale lưu đơn, kiểm bảng vận đơn có đúng một dòng, kiểm mã liên kết, kiểm giao dịch quay lui khi lỗi.

**`test_excel_roundtrip.py`** — xuất ra rồi nhập lại chính tệp đó. Đây là lỗi đã gặp ở ZuZu.

---

## Bốn quyết định đã ghi sẵn trong `docs/quyet-dinh/`

| Tệp | Nội dung |
|---|---|
| `001-chon-django-va-htmx.md` | Vì sao Django, vì sao không dùng framework giao diện riêng |
| `002-khong-dung-thu-vien-bang-tinh.md` | Vì sao không nhúng Univer — dữ liệu cần cấu trúc |
| `003-tach-cap-bac-va-bo-phan.md` | Vì sao hai cột riêng, không gộp thành `role` |
| `004-bang-dong-dung-jsonfield.md` | Vì sao JSONField cộng cột tách cho nhãn ý nghĩa |

Bốn tệp này viết ngay khi tạo repo, không đợi.
