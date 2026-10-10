# Biên bản kiểm chứng: Admin sửa lần nộp ngay trên Báo cáo tổng hợp (ADR-050), 10.10.2026

## Phạm vi

- **Yêu cầu của chủ dự án:** "tôi muốn quản trị có chức năng khi vào báo cáo tổng hợp có thể sửa dữ liệu".
- **Mockup tương tác đã duyệt:** https://claude.ai/artifact/AiyWUW9ycAGuRsdniXRWnN.
- **Chủ dự án đã chốt:**
  - chỉ Admin thấy nút ✎;
  - sửa trong hộp đè lên bảng, lưu xong bảng đổi tại chỗ;
  - dòng Toàn kỳ, TỔNG CỘNG và nguồn Vận đơn giữ nguyên.
- **Nhánh:** `claude/knerp-erp-chinh-sua-hfi7w8`, tách từ `Staging` `348a7da`.

## Môi trường

- **Máy ảo:** Claude Code trên web.
- **Bài kiểm tự động:** pytest chạy ngoài Docker trên Postgres 16 (cổng 5434) và Redis; Python 3.11; Chromium của
  Playwright.
- **Thử tay:** KN ERP `runserver` ở 8020, dữ liệu mẫu:
  - `du_lieu_mau`;
  - `nap_bao_cao_mau --nguoi 6 --lan 2` (Marketing, ngày 01.09 → 10.10);
  - 20 lần nộp Sale (08 → 10.10).

## Đã kiểm

| Mục | Lệnh / cách làm | Kết quả |
|---|---|---|
| Bài kiểm mới chạy đỏ trước khi viết mã | `pytest reports/tests/test_admin_sua_tong_hop.py` | 5 bài kiểm chức năng đỏ, 4 bài kiểm "không có ✎" đạt sẵn; bài thứ 10 (câu báo 409 không đổ cho người sửa từ trước) đỏ với mã cũ |
| Bài kiểm mới (AC-50.1 → 50.8) | như trên, sau khi viết mã | **10/10 đạt** |
| Trình duyệt (AC-50.9, 50.10) | `pytest reports/tests/test_admin_sua_tong_hop_e2e.py` | **2/2 đạt**: sửa, lưu, bảng đổi tại chỗ, 409 trong trình duyệt, Escape, 390 px, 0 lỗi console |
| Phần Báo cáo, không tính bài chậm | `pytest reports forms_builder/tests/test_man_hinh_bang.py -m "not cham"` | đạt hết; sửa một bài đọc tệp mẫu (AC-43.4) cho đọc cả include mới |
| Phần Báo cáo, bài chậm (trình duyệt) | `pytest reports -m cham` | **19/19 đạt**, gồm bố cục Báo cáo tổng hợp và ô nhập số (`report-entry.js` đổi sang gắn theo vùng) |
| Toàn bộ, không tính bài chậm | `pytest -m "not cham"` | xem mục "Toàn bộ" bên dưới |
| Thử tay trên 8020 | script Playwright, đăng nhập `quantri` và `mkt.manager` | **16/16 đạt** (bảng dưới) |

### Thử tay trên 8020

| Bước | Kết quả |
|---|---|
| Marketing 08 → 10.10: số nút ✎ | 36 = số lần nộp; khối Toàn kỳ và TỔNG CỘNG không có |
| Bấm ✎ | Hộp mở, con trỏ ở ô số đầu tiên |
| Sửa CPQC (+500.000) rồi Lưu | TỔNG CỘNG ngày 09.10 từ 130.745.000 thành 131.245.000; không tải lại trang; dòng sáng vàng; báo "Đã lưu chỉnh sửa · đã ghi lịch sử" |
| Hai người cùng sửa | Admin mở hộp, `mkt.manager` lưu Số đơn = 14 trước, Admin bấm Lưu: 409, hộp báo "TRANGDT vừa sửa báo cáo này lúc 10:43 …", ô Số đơn tô vàng và hiện 14; Lưu lại được |
| Gộp | 36 ✎ ở cột Ngày; khối Toàn kỳ không có; Escape đóng hộp, vẫn ở chế độ mở rộng ERP |
| Sale: đổi Thị trường sang Nhật Bản | Loại tiền tự thành JPY; lưu xong dòng sang JPY; TỔNG CỘNG của ngày có thêm dòng JPY (USD, CAD, JPY) |
| `mkt.manager` mở Báo cáo tổng hợp | không có ✎ |
| Admin mở Bảng dữ liệu `bao_cao_mkt` | không có ✎ (ADR-014) |
| 390 × 844 | trang không cuộn ngang; hộp sửa 390 × 844; không lỗi console |

Ảnh chụp các bước ở scratchpad của phiên, không đưa lên kho (CLAUDE.md: không commit ảnh review thiết kế). Bài kiểm
trình duyệt lưu ảnh ở `storage/e2e/admin-sua-*.png` khi chạy.

### Toàn bộ

`pytest -m "not cham"`: 3.154 bài. **3.140 đạt, 10 bỏ qua, 4 đỏ.** Cả bốn bài đỏ đã sửa:

- **Hai bài truy vết** (`tests/test_truy_vet.py`): mục 50 được thêm vào docs/04 khi bộ kiểm đang chạy, mà bài này đọc
  docs/04 lúc nạp tệp. Chạy lại thì lộ thêm một chỗ phải sửa: bộ đếm "đã có bài kiểm" ở docs/06, nay là 346 trên 369.
- **Hai bài quét lớp CSS** (`core/tests/test_giao_dien.py`):
  - `{% if sua_bao_cao %}` và `{% if xung_dot %}` nằm trong `class="…"` nên bị đọc nhầm thành tên lớp;
  - vùng báo lỗi `.report-sua-bao-loi` không có luật CSS.

  Đã đổi sang thuộc tính `data-sua`, `id="report-sua-loi"`, và tách thẻ mở theo điều kiện.

Sau khi sửa:
- bốn tệp liên quan (`tests/test_truy_vet.py`, `core/tests/test_giao_dien.py`, `reports/tests/test_admin_sua_tong_hop.py`,
  `reports/tests/test_form_nhap_bao_cao.py`): **744/744 đạt**;
- `pytest reports -m cham`: **19/19 đạt**.

Chưa chạy lại toàn bộ trên máy ảo sau lần sửa này. CI của PR (`853dc37`) chạy lại toàn bộ, bộ chính
`-m "not trinh_duyet"` và e2e: cả hai xanh.

## Kiểm kỹ trước khi gộp (lượt 2, 10.10.2026)

Chủ dự án: "test kĩ rồi gộp vào staging". Lượt này lấp những chỗ lượt 1 còn hở, sửa những gì tìm ra, rồi mới gộp.

### Rà mã độc lập

`/code-review` mức high trên #107 ra 9 phát hiện. Từng phát hiện đã xác minh trên mã:

| # | Phát hiện | Xử lý |
|---|---|---|
| 1 | Lượt lưu đang chạy không gắn với hộp: bấm Escape hay Huỷ lúc đang lưu thì lỗi 409/400/mất mạng ghi vào hộp đã đóng. Mở hộp khác trước khi có kết quả thì 204 đóng nhầm hộp mới | **Sửa.** Đang lưu thì khoá ✕, Huỷ và chặn `cancel` (Escape). Mỗi lần mở hộp một `phien`, nên kết quả cũ không đụng hộp mới; hộp đã đóng thì báo nổi. Quá 30 giây không trả lời thì thôi chờ |
| 2 | Gặp 409 thì hộp nạp lại mọi ô, bỏ cả số Admin vừa gõ ở ô không xung đột | **Giữ.** Đây là hành vi trong mockup chủ dự án đã duyệt: nạp số mới, tô vàng ô bị đổi, Admin xem lại rồi Lưu |
| 3 | Mọi 403 bị báo là "không còn quyền", kể cả 403 do CSRF khi vừa đăng nhập lại ở tab khác | **Sửa.** 403 báo "phiên đăng nhập hay quyền vừa đổi, tải lại trang"; 404 báo "báo cáo không còn để sửa (có thể vừa bị bỏ)" |
| 4 | "Lần N" ở đầu hộp tính khác bảng (`submission_number` đếm DailyReport, bảng đếm dòng theo cửa sổ) | **Sửa.** Nút ✎ mang `data-lan`, hộp nhận `lan` trên URL; bỏ `submission_number` |
| 5 | Escape bị chặn ở pha capture của cả cửa sổ, nên mọi phím Escape bên trong hộp cũng không tới | **Sửa.** Chặn ở chính hộp, pha nổi bọt. Không sửa `solarpunk-shell.js` dùng chung, để không mở rộng phạm vi |
| 6 | `report_id` thêm LEFT JOIN vào câu số liệu cho mọi người dùng | **Sửa** sau khi đo (bảng dưới): tra mã báo cáo bằng một truy vấn theo đúng các dòng đang hiện (`daily_service.attach_report_ids`), chỉ khi có ✎ |
| 7 | `amend` gắn thuộc tính `da_doi` lên đối tượng trả về | **Giữ.** Chỉ view dùng ngay sau `amend`; đổi chữ ký sẽ đụng các nơi khác gọi `amend` |
| 8 | Nút "Lịch sử sửa (n)" đếm theo danh sách đã cắt 50 dòng | **Sửa.** Nút ghi tổng số lần sửa; danh sách nói rõ chỉ hiện 50 lần gần nhất |
| 9 | Id báo cáo lấy lại bằng regex trên `form.action` | **Sửa.** Đọc từ `data-bao-cao` trên form |

Lỗi nào sửa cũng có bài kiểm đỏ trước, xanh sau:
- `test_admin_sua_tong_hop.py`: thêm `test_hop_sua_lich_su_dai`, `test_ma_bao_cao_chi_tra_cho_dong_dang_hien`; sửa
  AC-50.1, 50.2 (thêm Leader), 50.4.
- `test_admin_sua_tong_hop_e2e.py`: thêm `test_hop_sua_bao_loi_khi_luu_hong` (AC-50.11 mới).

### Bảng lớn: nhánh so với `Staging`

**Cách đo:**
- DB `knjsc_bc_lon` nhân từ DB thử, thêm `nap_bao_cao_mau --nguoi 20 --lan 3`: 2.400 lần nộp Marketing, 01.09 → 10.10. Cả kỳ
  vượt `MAX_GROUPS` (2.000).
- Đo trong tiến trình bằng Django test client, 20 lượt mỗi ô, 3 vòng xen kẽ, trên cùng một DB. Cây `Staging` là worktree
  `348a7da`.

**Câu truy vấn số liệu khi còn LEFT JOIN** (`EXPLAIN ANALYZE`, trung vị 8 lượt): 4 câu `ROW_NUMBER` của trang cả kỳ mất
55,1 ms, so với 50,8 ms trên `Staging`.

**Tách phần tốn trên trang Admin** (cùng mã, cùng tiến trình, xen kẽ 40 lượt mỗi cách):

| Kỳ | Phép nối (LEFT JOIN) | Vẽ ✎ (`{% url %}` + SVG mỗi dòng) |
|---|---|---|
| Tháng 9 (1.800 lần nộp) | +4,7 ms | +8,1 ms |
| Cả kỳ (2.400, chạm trần) | +21,8 ms | +6,5 ms |

Phép nối chậm theo cỡ kỳ, và vai không có ✎ cũng phải chịu.

**Đã sửa:**
- tra mã báo cáo một truy vấn theo dòng đang hiện;
- URL ghép ở JS từ mẫu `data-sua-mau`;
- biểu tượng `<use href="#report-but-sua">` khai một lần.

**Sau khi sửa, cùng tiến trình:**

| Kỳ | Có ✎ | Không ✎ | Chênh |
|---|---|---|---|
| Tháng 9 | 129,3 ms | 123,4 ms | **+5,9 ms (+4,8 %)** |
| Cả kỳ | 238,6 ms | 235,2 ms | **+3,4 ms (+1,4 %)** |

**So với `Staging`:**
- Admin thêm đúng 1 truy vấn (7 → 8, 16 → 17). HTML 100 dòng 108 → 137 KB; trước khi gọn là 147 KB.
- Manager và Bảng dữ liệu cùng số truy vấn và cùng cỡ HTML. Thời gian chênh nằm trong nhiễu giữa hai tiến trình (−4,8 % →
  +5,5 %).

**Hộp sửa trên DB lớn** (p50 / p95, 20 lượt):

| Thao tác | p50 | p95 |
|---|---|---|
| Mở hộp | 24,9 ms | 137,5 ms |
| Lưu không đổi số | 32,0 ms | 46,4 ms |
| Lưu có đổi số | 41,2 ms | 86,4 ms |

Cả ba đều dưới ngưỡng ghi 0,5 s, đều trả 204.

### Thử tay mở rộng trên 8020

Script Playwright (scratchpad `kiem-ky/thu-ky.py`) chạy trên mã cuối cùng: **47/47 đạt**, 0 lỗi console. Các mục:
- **16 bước của lượt 1.** Ở bước 409, Manager phải đổi sang số khác số đang có. Dữ liệu thử còn Số đơn = 14 từ lượt 1, nên
  Manager "lưu" lại số 14 thì không đổi gì: phiên bản không tăng và đúng là không có xung đột.
- **Lịch sử:**
  - "Lịch sử sửa (n)" tăng đúng 1 sau mỗi lần lưu;
  - danh sách trong hộp có lần sửa mới nhất;
  - trang Xem báo cáo ghi lần sửa từ hộp;
  - Bảng dữ liệu và tệp Xuất Excel có số mới.
- **Đường lỗi thật:**
  - để trống ô bắt buộc: 400, hộp báo lỗi;
  - bấm đúp Lưu: đúng một lần sửa;
  - máy chủ không trả lời: sau 30 giây báo trong hộp, giữ số, mở lại nút Lưu.
- **Bàn phím:**
  - Enter mở hộp;
  - Tab đi vòng trong hộp: giữa hai vòng Chromium ra khung trình duyệt, trang phía sau không nhận focus;
  - Escape đóng hộp; focus về đúng ✎.
- **Giữ ngữ cảnh sau khi lưu:**
  - trang 2 vẫn là "101–200";
  - đang lọc một người vẫn giữ lọc và đúng số dòng;
  - Gộp vẫn ở Gộp, nhãn đọc màn hình ghi ngày `dd.mm.yyyy`.
- **Sale:** đổi Thị trường thì Loại tiền đổi theo, TỔNG CỘNG thêm loại tiền mới. Lưu không đổi số thì báo "Không có số nào
  đổi".
- **Vai:**
  - `mkt.manager`, `mkt.leader`, `mkt.staff`, `sale.manager`, `sale.staff` không có ✎;
  - `mkt.staff`, `sale.manager`, `vd.staff` gọi thẳng hộp thì 404;
  - Bảng dữ liệu không có ✎.
- **Cỡ màn hình:** 1366, 1024, 768, 390, cả chế độ mở rộng lẫn thường. Trang không cuộn ngang. ✎ nằm gọn trong ô STT, không đè
  cột Nhân sự đứng yên, kể cả khi kéo bảng sang phải 400 px. Ở 390 px, hộp chiếm cả màn hình.
- **Chế độ tối, độ tương phản:**
  - câu báo 409: 9,87:1;
  - nhãn "vừa đổi": 9:1;
  - tiêu đề hộp: 13,1:1;
  - ghi chú: 6,55:1;
  - báo "Đã lưu": 13,1:1;
  - nút ✎: 8,96:1.

  Chữ cần từ 4,5:1, thành phần giao diện từ 3:1.

Ảnh ở scratchpad `kiem-ky/anh-ky/`, không đưa lên kho.

### Toàn bộ (lượt 2)

- `pytest reports -m cham` (trình duyệt): **20/20 đạt**, gồm ba bài AC-50.9, 50.10, 50.11.
- `pytest -m "not trinh_duyet"` (như bộ chính của CI) trên máy ảo: đang chạy lúc commit này. Kết quả ghi ở commit sau;
  CI của PR chạy cùng bộ.

## Chưa kiểm

- Safari, Firefox và máy Windows thật: máy ảo chỉ có Chromium.
- Một năm dữ liệu (khoảng 22.000 lần nộp Marketing): chưa đo. Câu số liệu nay giữ nguyên như `Staging`, phần thêm cho Admin
  chỉ theo số dòng trên trang (≤ 100), nên không lớn theo cỡ kỳ.
- VPS: chưa phát hành. Thay đổi này không có migration.
