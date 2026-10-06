# Biên bản săn lỗi — Fuzz nhẹ (06.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Đợt săn lỗi, bước 10 (chủ dự án duyệt, làm trên nhánh `claude/san-loi-tiep`) |
| Tiêu chí | AC-10.16 (NUL, chuỗi quá dài, số tràn ở mọi đầu vào), AC-21.16 (ô chữ của lưới, nhập tệp, form) |
| Cách làm | Script Python dùng `requests` (không thêm thư viện): đăng nhập theo vai, quét trang (tối đa 60 mỗi vai), rồi bắn 12 dữ liệu lạ vào **mọi tham số GET** thấy trên trang (cộng `tu`, `den`, `q`, `trang`, `sp`, `offset`, `limit`) và **mọi form POST** (bỏ qua form xoá, khoá, đổi mật khẩu, đăng xuất). Riêng JSON ghi lưới bắn tay 14 dạng hỏng |
| Dữ liệu lạ | chuỗi rỗng, 5.000 ký tự, `-1`, số 23 chữ số, `1e309`, `NaN`, ngày `2026-13-45`, ký tự NUL, `'"<script>`, `[]`, `%`, chữ số Ả Rập `١٢٣` |
| Môi trường | Bản sao DB hệ thống thật (`knjsc_fuzz`, chép từ lượt 04.10) để không làm bẩn bài chạy dài; ERP 8040, CRM 8041 chạy mã của nhánh |

## Lượt 1 — mã trước khi sửa

| Vai | Trang | Yêu cầu | Lỗi 500 |
|---|---|---|---|
| `sale.staff` + `quantri` @ ERP | 55 + 55 | 15.505 | **139** (58 nhóm đường dẫn) |
| `vd.manager`, `sale.staff` @ CRM | — | — | không đăng nhập được: lượt `quantri` đã fuzz luôn form sửa tài khoản trên bản sao DB. Lượt sau chép DB mới và chạy CRM trước |

Gom theo gốc:

| Gốc | Chỗ gặp | Số lần |
|---|---|---|
| **Ký tự NUL lọt vào câu truy vấn** (`PostgreSQL text fields cannot contain NUL`) | ô tìm Biểu mẫu, Tài nguyên, Nhân sự, Nhật ký, Tác vụ, danh sách Bảng, Bảng dữ liệu; bộ lọc Sản phẩm, Thị trường, Cách xem của Báo cáo tổng hợp; Lịch sử báo cáo; đăng bài, bình luận Bảng tin; thêm mục Tài nguyên | 108 |
| **Bộ lọc cột sai kiểu trên URL** (`?f_ngay=-1`, `?f_ngay=2026-13-45`, `?f_gia_tien=aaa` → `ValidationError` khi ép về ngày/tiền của cột tách) | Bảng dữ liệu `van_don` (18), `bao_cao_van_don_ngay` (11) | 29 |
| **Ký tự NUL trong JSON ghi lưới** (`unsupported Unicode escape sequence`) | `luu-json` | 1 trong 14 dạng hỏng |
| **Chuỗi dài hơn cột** (`value too long for type character varying(120)`) | thêm mục Tài nguyên với tên 5.000 ký tự | 2 |
| Ô ghi chú lưới nhận 200.000 ký tự (không lỗi, nhưng một ô Excel chỉ giữ 32.767 ký tự: tệp xuất sẽ bị Excel báo hỏng) | `luu-json` | — |

Đạt, không lỗi: 13/14 dạng JSON hỏng của lưới (JSON sai cú pháp, mảng, mã thao tác lạ, `cells` là chuỗi, id chữ, id quá
lớn, cột không có, giá trị là object, tiền `NaN`, thuộc tính lạ, `row_changes` lạ, id rỗng) đều trả 400/403 có lời
tiếng Việt. Form có khai báo (Django forms) đều chặn NUL sẵn — lỗi chỉ ở chỗ view đọc thẳng `request.GET/POST`.

## Lượt 2 — sau ba chặn chung đầu tiên, `vd.manager` @ CRM (dừng giữa chừng)

5.383 yêu cầu, **178 lỗi 500**, bốn gốc:

| Gốc | Chỗ gặp | Số lần |
|---|---|---|
| Bộ lọc ngày sai kiểu (cùng gốc lượt 1, chưa sửa lúc đó) | lưới `/bang-tinh/van_don/` (110), Thống kê CRM `?nguon=van_don&f_ngay__lon_bang=…` (40) | 150 |
| `get_object_or_404(Department, pk="abc")` nổ `ValueError` | tạo thư mục `/bang-tinh/thu-muc/moi/` với `bo_phan` không phải số | 21 |
| Như trên với `ColumnDef` | trang Cột `/bang/van_don/cot/?cot=abc` | 7 |

## Đã sửa

Không vá từng view: ba chặn chung ở cửa vào, cộng một chặn ở đường ghi ô.
1. `core.middleware.UnicodeNFCMiddleware` (đã có từ bước 4) nay từ chối mọi tham số GET, trường form, chuỗi JSON có NUL
   — 400 "Dữ liệu gửi lên có ký tự điều khiển không hợp lệ (NUL)…".
2. `core.middleware.DataLimitMiddleware`: lỗi Postgres SQLSTATE 22001 (chuỗi dài hơn cột) và 22003 (số tràn cột) lọt
   tới cơ sở dữ liệu thành 400 "Nội dung quá dài…" / "Số quá lớn…", giao dịch đã quay lui nên không ghi gì.
3. `core.middleware.tra_loi_400`: lời từ chối đúng kiểu người gọi — JSON cho lưới, chữ thuần cho HTMX (khung trang hiện
   nó), trang tiếng Việt "Dữ liệu chưa hợp lệ" có nút Quay lại cho lần mở trang thường (dùng chung `500.html`).
4. `record_service.parse_value` (đường ghi chung của lưới, nhập tệp, form): ô chữ có NUL hay dài hơn 32.767 ký tự bị từ
   chối có tên cột — chặn được cả ô của tệp nhập, vốn không qua middleware.
5. `forms_builder.query.apply_filters` vốn hứa "tham số do người dùng gõ, sai thì bỏ qua" nhưng chỉ bắt `ValueError`,
   `TypeError`, `FieldError`: thêm `ValidationError`. Một chỗ này sửa cho Bảng dữ liệu, xuất tệp, lưới CRM và Thống kê.
6. Hai view lấy mã từ form/URL đưa thẳng vào `get_object_or_404` (tạo thư mục, trang Cột): mã không phải số là 404, cùng
   khuôn với Tài liệu vốn đã chặn. Rà toàn bộ mã: chỉ còn ba chỗ kiểu này, cả ba đã chặn.

## Lượt 2 — mã sau khi sửa

_điền sau_

## Bài kiểm

- `core/tests/test_ky_tu_nul.py` (AC-10.16): NUL ở GET, POST, JSON → 400; chữ Việt, tab, emoji vẫn qua; tên mục 5.000
  ký tự → 400 không ghi.
- `crm/tests/test_o_chu_bien.py` (AC-21.16, AC-10.16): lưới từ chối NUL, ô quá 32.767 ký tự; `parse_value` từ chối NUL
  cho cột Chữ, Chữ dài, Chọn một; tạo thư mục với mã bộ phận chữ → 404; lưới với bộ lọc ngày sai kiểu → 200.
- `forms_builder/tests/test_loc_sai_kieu.py` (AC-10.16): 7 bộ lọc sai kiểu ở Bảng dữ liệu và Xuất tệp → 200; trang Cột
  `?cot=abc` → 404.
- Đỏ trên mã cũ (lỗi 500 `DataError`), xanh sau khi sửa.

## Chưa kiểm

- Fuzz tệp tải lên (Excel, CSV có cấu trúc lạ): bước 2 đã thử bom nén, đuôi giả; chưa sinh ngẫu nhiên nội dung tệp.
- Fuzz có hướng dẫn theo độ phủ (hypothesis, atheris): cần thêm thư viện.
