# Kiểm chứng — Ba bài đỏ của lưới cho khớp ADR-036 và ADR-040 (TL-68) — 29.09.2026

Nhánh `claude/sua-bai-luoi-dong-trong` tách từ `main` (`206e1b0`). Máy cá nhân của chủ dự án (Windows,
Docker Desktop), PostgreSQL 16, Chromium thật trong một image phụ chỉ để kiểm (`knjsc-web:latest` +
`playwright install --with-deps chromium`) — image phụ không đưa vào kho mã.

## Vì sao đỏ

Rà `main` 206e1b0 trước khi phát hành VPS, nhóm trình duyệt có 3 bài đỏ, cả ba trong
`crm/tests/test_luoi_dong_trong_va_ghim_e2e.py`. **Không phải hồi quy, cũng không phải lỗi ứng dụng** —
bài kiểm tụt lại sau hai quyết định đã chốt:

| Bài | Đỏ vì |
|---|---|
| `test_mot_nghin_dong_trong_san_va_tao_dong_khong_tai_lai` (AC-11.37) | Mở `/bang-tinh/so_tay_kiem/` — bảng thường. [ADR-040](quyet-dinh/040-crm-chi-mot-bang-van-don.md) (24.09) cho KN CRM **404 mọi bảng không phải vận đơn**; log của lượt chạy ghi `Not Found: /bang-tinh/so_tay_kiem/`, gọi thật cũng 404. Trang 404 nên `.mg-cell[data-id]` không bao giờ hiện, Playwright hết 15 s |
| `test_go_lien_tiep_roi_enter_khong_giat` (AC-11.40) | Cùng bảng, cùng 404 |
| `test_cot_ghim_dung_dau_va_boi_den_theo_thu_tu_nhin_thay` (AC-11.38) | Chốt cứng bốn cột ghim; thực tế **năm**. Cột Trùng khai `'frozen': True` trong `crm/services/waybill_grid.py` — cố ý ghim theo [ADR-036](quyet-dinh/036-mot-bang-van-don-duy-nhat.md) (18.09). Ba mệnh đề đầu của khẳng định đúng, chỉ `not dau[4]["pin"]` sai |

**Bằng chứng là có sẵn từ trước, không phải do 14 PR của đợt phát hành:** `.github/workflows/ci.yml` cố ý
`--deselect` đúng tệp này kèm ghi chú "đỏ sẵn từ trước khi có tệp CI này"; và chạy lại tệp đó trên **chính
commit `85227ee` đang chạy trên VPS** cho ra **3 failed, cùng ba bài, cùng thông báo** (122,72 s).

**Không chuyển bài sang `van_don` để giữ AC-11.37 được:** `waybill_service.protect_table = True` (khai cấp
module, đăng ký cho cả mã `van_don` lẫn `workflow="waybill"`) làm `row_mutations.can_create()` trả `False`
với **mọi** tài khoản. Cộng với ADR-040 thì "1.000 dòng trống sẵn" không còn đường nào xảy ra trong KN CRM.
Đo trực tiếp trên lưới thật: bấm đúp ô chỉ đọc ra "Ô này chỉ đọc.", `canCreate: false` trong `#mg-config`.

## Sửa (không đụng mã ứng dụng)

- **AC-11.37 rút** khỏi `docs/04` kèm lý do và điều kiện mở lại; bỏ bài tương ứng và fixture `bang_thuong`
  (không bài nào còn dùng), bỏ luôn `JS_TOTAL` và ba import chỉ phục vụ fixture đó.
- **AC-11.40** bỏ mệnh đề "dòng nháp thành bản ghi nối tại chỗ, dòng trống bù theo đợt". Bài chuyển sang
  bảng vận đơn qua fixture mới `van_don_sau_dong` — sáu dòng thật dựng bằng `order_service.create_order`,
  đúng đường người dùng đi. Gõ liên tiếp 5 dòng cột Tên khách rồi 3 dòng cột Thành phố.
- **`_go_va_enter` sửa cho khớp [ADR-033](quyet-dinh/033-pham-vi-toi-toan-bo-va-quyen-sua-van-don.md) bổ sung
  26.09.2026:** bản cũ bấm ô rồi **chờ ô nhập tự mở** — đúng hành vi trước 26.09. Nay bấm một lần chỉ chọn ô,
  nên bài gõ ký tự đầu để mở ô nhập rồi mới gõ nốt; Enter chỉ chuyển ô, không tự mở ô kế.
- **AC-11.38** thôi chốt cứng bốn cột: lấy nhóm ghim từ chính lưới rồi khẳng định (a) mọi cột ghim đứng
  trước mọi cột thường, (b) bốn cột ghim của bảng vận đơn nằm trong nhóm đó, (c) cột thường đầu tiên nối
  ngay sau, (d) không ô trống giữa các cột. Địa chỉ vùng chọn tính theo số cột ghim thay vì viết cứng
  `A1:E2`. Thêm hay bớt cột ghim sau này không làm bài đỏ lại.
- `docs/06` về **293 tiêu chí — 280 tự động, 257 có bài kiểm** (số do chính `tests/test_truy_vet.py` báo).
- Bỏ dòng `--deselect crm/tests/test_luoi_dong_trong_va_ghim_e2e.py` trong `ci.yml`.

## Kiểm

| Lượt | Trước sửa | Sau sửa |
|---|---|---|
| `crm/tests/test_luoi_dong_trong_va_ghim_e2e.py` (Chromium) | **3 đỏ** (84 s) | **2 đạt** (80 s) |
| Cùng tệp trên `85227ee` — đối chứng bản đang chạy trên VPS | **3 đỏ**, cùng ba bài | — |
| `tests/test_truy_vet.py` + `core/tests/test_giao_dien.py` | 2 đỏ vì bộ đếm docs/06 lệch | **673 đạt** |

Lượt giữa còn một lần `test_cot_ghim_dung_dau...` đỏ vì `Page.goto` quá hạn 15 s ở trang đăng nhập — chập
chờn của máy đang tải nặng, không phải khẳng định; chạy lại cùng mã thì đạt.

## Chưa kiểm / để lại

- **Mã chết:** `row_mutations.create` và phần đệm 1.000 dòng trống vẫn còn trong nguồn nhưng không đường nào
  gọi tới trong KN CRM. Bỏ hay giữ cần quyết định riêng — đã ghi backlog, lượt này không đụng.
- Không đụng mã ứng dụng nên không cần kiểm lại hành vi lưới; các điểm liên quan đã được kiểm tay cùng ngày
  trong đợt rà `main` (xem mục 29.09.2026 thứ nhất của backlog).
