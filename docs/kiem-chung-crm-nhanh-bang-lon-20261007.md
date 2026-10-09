# Biên bản — KN CRM nhanh khi bảng Vận đơn lớn (07.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 07.10.2026: sửa năm chỗ chậm ngoài phạm vi PR #96 (mục 5 của [biên bản PR #96](kiem-chung-phan-trang-luoi-erp-mo-rong-20261007.md)); không đổi kết quả, không đổi phân quyền |
| Nhánh | `claude/crm-nhanh-bang-lon`, tách từ `claude/phan-trang-luoi-erp-mo-rong` (PR #96, chung tệp lưới), PR nháp về `Staging` |
| Tiêu chí | AC-10.23 → AC-10.26 |
| Môi trường | Máy ảo; Postgres 16; Redis; DB thử **385.034 dòng Vận đơn**; Django test client (đo máy chủ) và hệ thống thật `runserver` 8020/8021 + Playwright Chromium (đi tay) |

## 1. Đã sửa gì

| # | Chỗ | Gốc | Cách sửa (kết quả y nguyên) |
|---|---|---|---|
| 1 | Trang chủ KN CRM `/` | `COUNT(DISTINCT)` + `MAX` qua `records__pk__in=<phạm vi>` trên mọi dòng; hoạt động `target_id__in` 385.000 id; `created_at__date` không dùng chỉ mục | Mỗi bảng vận đơn một phép đếm `in_scope(user, table=…)` dùng chung cho số liệu và "Bảng gần đây"; hôm nay/tháng này so khoảng giờ VN; hoạt động đọc nhật ký theo lô 200, kiểm thuộc bảng vận đơn theo lô |
| 2 | Menu khung (mọi trang CRM) | `TableDef.in_scope` luôn chạy `EXISTS` trên dòng với OR qua JOIN đơn/phân công | `EXISTS` chỉ thêm cho người phòng Sale/CSKH (phòng khác điều kiện đó luôn rỗng); tách thành ba `EXISTS` theo chỉ mục |
| 3 | Thư mục `/thu-muc/` | Đếm theo phạm vi chung (không theo bảng) | `UNION ALL` mỗi bảng một phép đếm `in_scope(user, table=…)` |
| 4 | Khối lưới `du-lieu/` | Mỗi khối 100 dòng quét phạm vi hai lần (mốc COUNT+MAX, tổng COUNT) | Đệm mốc và tổng trong `caches['crm']`; khoá = phạm vi người xem + `GridRevision` (trigger) + `MAX(updated_at)` cả bảng + ngày VN (`optimization.khoa_bang`) |
| 5 | Panel Bộ lọc | Đếm theo phạm vi chung; đếm lại mỗi lần mở | Đếm theo phạm vi bảng; đệm cùng khoá với #4 |
| — | Phạm vi dòng Sale/CSKH (`scope_condition`) | OR qua LEFT JOIN đơn/phân công | Ba truy vấn con `pk__in` theo chỉ mục — cùng tập dòng |

Không bật cờ `CRM_OPT_*` nào. Không thêm 409: khoá đệm lệch chỉ làm tính lại.

## 2. Đo phía máy chủ — trước (`e515101`, worktree riêng) và sau (p50; ms)

| Thao tác | vd.manager | vd.staff | sale.staff |
|---|---|---|---|
| Trang chủ CRM `/` | 150.000–258.000 (đo ở PR #96) → **143** | → **142** | → **266** |
| Phạm vi bảng (`TableDef.in_scope`, menu) | 380 → **6** | 373 → **4** | 588 → **18** |
| Một trang CRM nhẹ (`/bang-da-xoa/`, gần như chỉ menu) | 371 → **22** | 395 → **15** | 601 → **31** |
| Thư mục `/thu-muc/` | 1.321 → **113** | 929 → **110** | 1.451 → **319** |
| Khối lưới lần đầu (bộ đệm trống) | 228 → 248 | 269 → 242 | 863 → **564** |
| Khối lưới đọc lại / cuộn tới dòng 1.000 | 243 / 278 → **111 / 92** | 222 / 265 → **94 / 100** | 905 / 948 → **182 / 159** |
| Mở panel Bộ lọc lần đầu | 2.714 → **843** | 950 → 891 | 1.236 → **969** |
| Mở panel Bộ lọc lần sau (bảng không đổi) | 2.714 → **33** | 950 → **25** | 1.236 → **34** |

Khối lưới lần đầu của Vận đơn không nhanh hơn: thêm một truy vấn khoá (≈1 ms) và một lần ghi Redis; chênh nằm trong
dao động. Phần còn lại của khối khi đã đệm: vd ≈ 24 ms SQL, còn lại là dựng JSON 100 dòng; sale.staff ≈ 56 ms cho chính
truy vấn lấy 100 mã dòng trong phạm vi. Panel lần đầu vẫn ~0,9 s vì phải đếm theo nhóm trên mọi dòng thấy được (ba cột:
0,42 + 0,27 + 0,06 s).

## 3. Kết quả y nguyên — bài so tương đương

| Bài | So gì |
|---|---|
| `forms_builder/tests/test_pham_vi_bang_nhanh.py` | Tập bảng `TableDef.in_scope` và tập dòng `scope_condition` cách cũ (viết lại trong bài) = cách mới cho mọi vai trong `nguoi_dung`, CSKH, CEO, Leader Vận đơn; dữ liệu có hai bảng vận đơn, đơn Sale bán, đơn do Admin tạo gán Sale, CSKH phụ trách, grant |
| `crm/tests/test_trang_chu_bang_lon.py` | Số liệu, "Bảng gần đây", hoạt động trang chủ; thống kê thư mục; số đếm panel — cách cũ = cách mới mọi vai; trang chủ không còn `COUNT(DISTINCT` hay `IN (` dài |
| `crm/tests/test_khoi_luoi_dem.py` | Lặp khối không quét lại (bớt đúng 2 truy vấn); sửa trong phạm vi vẫn 409, ngoài phạm vi không; giao CSKH (không đổi `updated_at`), xoá mềm theo lô, xoá cứng đều ra tổng mới; Redis lỗi vẫn đúng; panel không trả số cũ sau khi sửa ô |

## 4. Đi thử trên hệ thống thật (385.034 dòng, Playwright)

| Bước | vd.manager | sale.staff |
|---|---|---|
| Đăng nhập CRM → trang chủ (gồm đăng nhập, tải tài nguyên) | Đạt, 3,5 s | Đạt, 2,4 s |
| Thư mục | Đạt, 1,0 s | Đạt, 1,1 s |
| Lưới mở rồi cuộn qua nhiều khối | Đạt (`…0001` → `…0848`) | Đạt (`…0005` → `…5087`) |
| Mở panel Bộ lọc | Đạt, 1,4 s | Đạt, 1,4 s |
| Áp dụng lọc Thị trường | Đạt | Đạt, chip "Quốc gia thuộc Canada" |

Trước sửa, máy chủ mất 150–258 giây cho trang chủ CRM (trang ngay sau đăng nhập) — đo ở PR #96, chưa đi tay được.

## 5. Kiểm toàn phần

| Lượt | Kết quả |
|---|---|
| `pytest -m "not trinh_duyet"` | 3.100 đạt, 7 bỏ qua, 0 đỏ |
| Bài trình duyệt lượt 1 (`tests/e2e`) | 53 đạt, 9 đỏ — đúng 9 bài `test_pha_luoi_ghi_chu` lỗi chứng chỉ Google Fonts của máy ảo (`ERR_CERT_AUTHORITY_INVALID`), như `Staging` |
| Bài trình duyệt lượt 2 | 16 đạt, 9 bỏ qua |
| `pytest -m "not trinh_duyet"` khi **tắt Redis** (như CI) | 3.100 đạt, 7 bỏ qua, 0 đỏ — sau khi sửa lỗi CI dưới đây |

CI lần đầu đỏ ở `test_kiem_tai::test_luoi_100_dong_ngan_sach_truy_van`. CI không có Redis, nên khối lưới chạy ngoài snapshot (trong giao dịch của bài kiểm) tốn 16 truy vấn, vượt trần 14: mỗi lần kiểm mốc đều thêm một truy vấn khoá. Đã sửa: lần kiểm mốc thứ hai đọc thẳng `stamp` như trước, trần nới lên 15 cho đúng một truy vấn khoá.

## Rủi ro và chưa kiểm

- Bộ đệm #4/#5 dựa vào trigger `GridRevision` (`crm/migrations/0004`) bắt mọi thay đổi có thể đổi phạm vi hay số đếm.
  Nguồn mới ngoài danh sách trigger (bảng mới quyết định phạm vi) phải thêm vào trigger, không thì có thể trả số cũ tới
  300 giây. Đã ghi ở docstring `optimization.khoa_bang`.
- Mốc phiên bản khối (`stamp`) vẫn không đổi khi xoá mềm theo lô không chạm `updated_at` — như trước, không do lần sửa
  này; tổng số dòng thì đúng.
- Chưa đo trên VPS thật (2 nhân, 4 GB) và chưa chạy locust nhiều người với cách mới.
