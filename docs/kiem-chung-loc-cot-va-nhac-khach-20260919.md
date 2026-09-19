# Kiểm chứng hộp lọc cột và lời nhắc khách — 19.09.2026 (tối)

Nền `6be31e8`, nhánh `codex/crm-update-solar-ui`, máy ảo Claude Code trên web.
Chưa phát hành VPS.

## Việc 1 — Chắn lỗi gõ nhầm số điện thoại

**Vì sao cần.** Bản sửa buổi chiều cho tên khách lấy theo lần gõ mới nhất làm lỗi đổi
dạng chứ chưa hết: gõ nhầm một chữ số trúng khách khác thì trước đây đơn hiện tên người
lạ (thấy ngay), còn sau đó đơn trông đúng nhưng **danh bạ bị đổi tên âm thầm**. Chủ dự án
chọn chắn bằng tự điền cộng cảnh báo, không chặn lưu.

**Đã làm.** Ô Số điện thoại và ô Tên khách cùng gọi lời nhắc khách, mỗi ô gửi kèm ô kia
(`hx-include`) — trước đây chỉ số điện thoại được gửi nên server không biết đang gõ tên
gì. `customer_notice` nhận thêm tên đang gõ, trả `ten_dang_luu`, `ten_dang_go`,
`ten_khac`, `phone`. Mảnh nhắc mang `data-ten-khach`; `order-entry.js` điền tên đó vào ô
Tên khách **chỉ khi ô đang trống**. Khi tên gõ khác tên đang lưu thì hiện khối vàng
(`bao bao-cho`, lớp có sẵn) nêu cả số điện thoại lẫn hai tên.

**Chromium, gõ thật từng phím, tài khoản `sale.staff`:**

| Tình huống | Kết quả |
|---|---|
| Gõ số đã có, ô tên đang trống | Ô Tên khách **tự điền** "Ten Sua Lai"; không cảnh báo |
| Sửa tên thành "Nguoi Hoan Toan Khac" | Hiện "Lưu đơn sẽ đổi tên khách của số 0911000001", nêu cả tên cũ lẫn tên mới |
| Gõ số mới hoàn toàn | Không tự điền, không nhắc gì |
| Lỗi JavaScript | Không có |

## Việc 2 — Hộp lọc cột chọn công cụ theo số giá trị

**Vì sao cần.** Đầu hộp ghi `{{ tuy_chon|length }}`, tức **số mục đã cắt**, nên cột nhiều
giá trị luôn ghi "200 giá trị (hiện 200 đầu)" — sai. Và danh sách ô tích là sai công cụ
cho cột như Tên khách.

**Đo chi phí trước khi chọn cách**, trên 100.533 dòng, mỗi cột ba lượt:

| Cột | Có chỉ mục | Đếm đủ số giá trị khác nhau | Lấy 201 giá trị rồi đếm | Số giá trị thật |
|---|---|---|---|---|
| Trạng thái vận chuyển | có | 0,10 s | 0,10 s | 9 |
| Quốc gia | không | 0,11 s | 0,12 s | 3 |
| Tên khách | có | 0,13 s | 0,17 s | 94.554 |
| Mã đơn | không | 0,13 s | 0,15 s | 100.523 |
| Ghi chú | không | 0,11 s | 0,11 s | 3.620 |

Đếm đủ rẻ ngang lấy danh sách, nên không cần thủ thuật: cứ đếm thật.

**Đã làm.** `grid_service.dem_gia_tri` dùng chung cách chọn nguồn với `filter_options`
(gom vào `_nguon_gia_tri`, bớt trùng mã). Ngưỡng `GRID_FILTER_LIST_MAX = 50` khai cạnh
`GRID_FILTER_OPTIONS_MAX` trong `core/constants.py` — **số tạm**, chọn theo cảm nhận sử
dụng chứ chưa có số đo. Trên ngưỡng thì hộp mở sẵn ô gõ chữ (`f_<cột>__chua`, phép lọc đã
có sẵn) và gập danh sách ô tích vào; dưới ngưỡng giữ nguyên như cũ.

**Chromium, tài khoản `vd.staff`:**

| Cột | Đầu hộp | Bố cục |
|---|---|---|
| Quốc gia (3 giá trị) | "Lọc cột Quốc gia · 3 giá trị" | Danh sách ô tích như cũ, không gập |
| Tên khách (94.554) | "… · 94554 giá trị — quá nhiều để chọn tay" | Ô gõ chữ mở sẵn, danh sách gập sau "Hoặc chọn từ 200 giá trị hay gặp nhất"; chỉ một ô Chứa chữ |

## Việc 3 — Đổi cột thì sót mục của cột trước

**Nguyên nhân gốc.** Ô tìm trong mảnh lọc đặt `hx-target="#hop-loc"`, nên lần gõ tìm đầu
tiên thay toàn bộ ruột hộp và **xoá luôn `<div id="mg-column-filter-body">`**. Lần bấm lọc
cột sau không còn đích, htmx bỏ qua, hộp giữ nguyên nội dung cột trước. Dự án đang bù bằng
một listener `htmx:afterSwap` viết lại `hx-target`, nhưng nó chỉ quét **bên trong** chính
cái div đã mất nên vô tác dụng đúng lúc cần.

Con số 203 mục đếm được hôm nay khớp: 200 mục giá trị của cột trước cộng ba radio Bất kỳ /
Chỉ ô trống / Chỉ ô có giá trị, vốn cũng mang lớp `.loc-cot-muc`.

**Đã làm.** Mảnh lọc trỏ thẳng `hx-target="#mg-column-filter-body"`; bỏ listener bù vì nó
che lỗi; thêm bước xoá ruột và hiện "Đang tải…" trước mỗi lần gọi, che nốt hai đường không
swap khác (HTTP ≥ 400, và khi bảng không còn dùng được).

**Chromium:** mở lọc cột Tên khách, gõ vào ô tìm, rồi mở lọc cột Quốc gia — đầu hộp ghi
"Lọc cột Quốc gia · 3 giá trị", đếm đúng 2 mục giá trị. Trước khi sửa là 203 mục.

## Việc 4 — Mã tiêu chí bị trùng

Ba bài thêm buổi chiều mang mã **AC-6.9**, trùng với AC-6.9 đã có cho "Manager thêm sản
phẩm mới"; và bài CSS mang **AC-11.40**, trùng với "Gõ rồi Enter không giật". Bài truy vết
không bắt được vì `_tieu_chi()` gom vào `dict`, mã trùng lặng lẽ đè nhau.

Đã đổi sang AC-6.10 và AC-11.41, và thêm bài khẳng định **mọi mã trong `docs/04` là duy
nhất**. Bài đó bắt được ngay cả hai chỗ trùng khi vừa viết xong.

## pytest

| Lượt | Kết quả |
|---|---|
| Toàn bộ `-m "not trinh_duyet and not cham"` | 2.527 đạt, 1 bỏ qua, 0 đỏ |
| `tests/test_truy_vet.py` | Đạt; docs/06 lên 237 AC, 224 tự động, 200 đã có bài |
| `node --check` cho `master-grid.js`, `order-entry.js` | Đạt |

Tiêu chí mới: **AC-6.10** (mở rộng: lời nhắc báo trước khi đổi tên, mảnh mang tên để tự
điền), **AC-11.42** (mảnh lọc không trỏ vào cả hộp), **AC-11.43** (hộp lọc chọn công cụ
theo số giá trị).

## Chưa kiểm

- Bài `trinh_duyet` không chạy ở lượt này; chưa thêm bước đổi cột vào
  `scripts/kiem-thu-master-ui.cjs` — bài AC-11.42 ở mức tệp đã khoá đúng nguyên nhân gốc,
  nên để lượt sau.
- Chưa phát hành VPS. Cả bốn việc còn nằm trên nhánh.
- Ngưỡng 50 chưa có số đo chống lưng. Đổi ở `core/constants.py` là đổi mọi chỗ.
- Chưa thu gọn panel "Bộ lọc" — cố ý hoãn, chờ hỏi nhân viên sau khi phát hành.
