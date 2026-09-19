# Backlog

## 19.09.2026 (chiều) — Hai lỗi chủ dự án báo: tên khách đơn thứ hai, hộp lọc cột trông hỏng

**Lỗi tên khách.** `create_order` dùng `get_or_create` theo số điện thoại nên `defaults` bị bỏ qua khi
số đã có; ô Tên khách lấy từ `order.customer.name`, tức tên của lần lên đơn đầu. Chủ dự án chọn: đơn ghi
tên vừa gõ, danh bạ đổi theo, có nhật ký; đơn cũ giữ nguyên; Facebook/Email chỉ điền thêm khi trống.
Bài AC-6.9 (ba bài) ở `orders/tests/test_len_don.py`.

**TL-46 hộp lọc cột.** `crm-frame.css` dòng 184 mở chú thích tiêu đề mục mà thiếu `*/`, nuốt 24 luật
`.loc-cot-*` từ commit `9bac840` (14.09). Hộp lọc hiện ra không nền, không khung, không cuộn, chữ đè
lên lưới. Sửa bằng cách đóng chú thích; 24 luật sống lại đều thuộc nhóm đó, không đụng chỗ khác.
`core/tests/test_giao_dien.py` từng bỏ sót vì quét cả phần trong chú thích — đã sửa, thêm AC-11.40.

Kiểm: 2.428 đạt / 0 đỏ; [biên bản](kiem-chung-hai-loi-20260919.md).
**Còn nợ:** phát hành VPS (cả hai lỗi còn trên domain thật). Hộp lọc cột trên bảng 100.522 dòng mở mất
~5 giây và chỉ hiện 200 giá trị đầu (`GRID_FILTER_OPTIONS_MAX`) — với cột nhiều giá trị như Tên khách thì
danh sách gần như vô dụng, chờ chủ dự án chốt có đổi cách lọc không.

## 19.09.2026 — Ô danh tính Báo cáo tổng hợp: mỗi người một dòng (AC-22.14, TL-45)

## 19.09.2026 — Báo cáo tổng hợp nhóm theo ngày × nhân sự: mỗi người một HÀNG (AC-22.14, TL-45)

Chủ dự án gửi ảnh một hệ thống khác và yêu cầu màn hình giống ảnh: trong một ngày mỗi
marketer là một hàng riêng. Bản đầu (`98d5c1e`) chỉ cho các mã xuống dòng trong một ô, chủ
dự án bác. Đã **đảo quyết định 1 của ADR-035** (ghi thành Bổ sung 19.09 trong chính ADR):
`aggregations.summarize()` nhận `extra_groups` và `derived_key`; cách xem Tổng hợp nhóm theo
ngày × nhân sự, ngày lặp lại, mỗi hàng số của riêng người đó; `marketing_revenue` khoá theo
cặp (ngày, marketer) nên không dồn tiền cả ngày cho từng người; Vận đơn nhóm cùng cách; bỏ
`StringAgg` gộp tên, bỏ `split_labels`/`JOIN`/`.report-name` của bản đầu. Bài AC-22.10,
AC-22.14 và `test_mkt_derived_revenue` viết lại theo cặp (ngày, mã). Kiểm: `pytest -m "not
cham"` 2.508 đạt, 0 đỏ; Chromium 1440 sáng/tối và 390 — ngày 17.09 tách thành hai hàng
ANHPM 2.320 Mess và NAMVH 50 Mess, dòng Tổng vẫn 15.056, không ô nào tràn chữ
([biên bản](kiem-chung-o-danh-tinh-20260919.md), ảnh `docs/kiem-thu/o-danh-tinh-2026-09-19/`).
Đợt hai cùng ngày (chủ dự án "tiếp tục"): **khối theo ngày** như ảnh mẫu — `aggregations.subtotals()`
cộng theo ngày (cộng cả `derived`, tính lại cột tính từ tổng), `activity_views.day_blocks()` chèn dòng
Tổng ngày và gắn STT đếm lại từ 1, CSS `.report-subtotal` + `--w-stt`, Excel cùng khối. Bài mới
AC-22.15; docs/04 và bộ đếm docs/06 lên 234. Chromium: 17.09 Tổng ngày 2.370 = 2.320 + 50, cuộn ngang
cột định danh trôi 0px.
**Còn nợ:** chưa phát hành VPS; tô màu ô theo ngưỡng như ảnh mẫu còn chờ chủ dự án chốt ngưỡng và chỗ
lưu (`marketing.Metric` chưa có trường ngưỡng, luật màu `main.css` khoá sau `.bang-luoi`).

## 19.09.2026 — Ẩn cột với cả công ty (ADR-039), tắt nhóm cột sản phẩm

Chủ dự án muốn tắt nhóm cột số lượng theo sản phẩm `sl_*` trên bảng Vận đơn mới (thêm sản phẩm ở
Lên đơn là hiện thêm một cột). Nút "Cột" cũ chỉ nhớ trong trình duyệt từng người nên không tắt cho
cả công ty được. Chốt qua hai câu hỏi: **quản lý bảng ẩn được mọi cột cho cả công ty ngay trong hộp
"Cột"**, áp dụng **cả ba màn hình** (lưới KN CRM, tệp Excel xuất ra, Bảng dữ liệu ERP). Đã làm:
`ColumnDef.is_hidden` (migration `forms_builder/0015`, đảo được), `table_service.visible_columns` là
chỗ lọc duy nhất cho ba màn hình, `set_columns_hidden` có nhật ký và chặn ẩn cột khoá / cột bắt buộc /
ẩn hết cột; `POST /bang-tinh/<mã>/an-cot/` theo quyền quản lý cột; hộp "Cột" thêm nút từng dòng, nút
gộp cho nhóm cột sản phẩm và mục "Đang ẩn với cả công ty"; cột sản phẩm sinh sau khi nhóm đã ẩn thì
vào ở trạng thái ẩn. Lên đơn và nhập tệp vẫn ghi vào cột ẩn để bật lại là có đủ dữ liệu. Bài mới
`crm/tests/test_an_cot.py` (AC-39.1 → 39.7). Kiểm: [biên bản](kiem-chung-an-cot-20260919.md).
**Còn nợ:** phát hành VPS; sau phát hành **Admin phải bấm ẩn một lần** thì cột sản phẩm mới tắt, vì
ẩn là trạng thái trong cơ sở dữ liệu. Cân nhắc sau: số cột `sl_*` vẫn tăng theo danh mục sản phẩm dù
đang ẩn — bỏ hẳn nhóm cột này thì phải chốt riêng vì mất số liệu 221 dòng nhập từ tệp thật.

## 18.09.2026 (đêm, CLI) — Báo cáo tổng hợp: ô Nhân sự chỉ mã, bảng không tràn ở Toàn màn hình

Chủ dự án so ảnh local với VPS, chọn bố cục local và yêu cầu: ô Nhân sự chỉ hiện mã nhân sự (không họ tên),
bảng ở Toàn màn hình phải có thanh kéo ngang thay vì tràn. Chốt trong phiên: **chỉ bảng + Excel** (cột Nhân sự,
Leader, dòng Theo nhân viên); ô chọn Nhân sự và chip giữ `MÃ · Họ tên`; chưa có mã thì tên đăng nhập (VPS
sau `gan_ma_nhan_su_cu` sẽ ra mã). Sửa: `activity_service` đổi `label_expression` → `code_expression` ở
`person_expressions`, `group_expression` và khoá `person` của `marketing_revenue` (phải cùng biểu thức để
`attach_derived` nối được doanh thu suy ra); CSS `--w-nhan-su` 130px, `--w-leader` 120px, và
`.sp-report-focus .report-workspace{grid-template-rows:minmax(0,1fr)}` — nguyên nhân tràn là hàng grid ngầm
`auto` khiến khung cuộn cao bằng cả bảng, thanh kéo ngang rơi ra ngoài viewport và bị `.noi-dung{overflow:hidden}`
cắt. ADR-037 thêm mục "Bổ sung 18.09 (tối)", docs/04 AC-22.10/22.13/mục 37. Kiểm: `reports/tests` + `tests/test_truy_vet.py` + `core/tests/test_giao_dien.py` trong container: 751 đạt, 1 bỏ qua (Chromium),
0 đỏ sau khi sửa một khẳng định trùng tên; trang thật 8020 và Chromium host (script mới
`scripts/kiem-thu-bao-cao-chi-ma.mjs`, CDP thuần): ô chỉ mã, ô chọn vẫn `MÃ · Họ tên`, Toàn màn hình 960px có thanh kéo
ngang, cửa sổ 300px cao vẫn thấy phân trang. **Còn nợ:** phát hành VPS (chỉ `collectstatic`, không migration); bài e2e
Chromium trong container vẫn bị bỏ qua vì image thiếu thư viện hệ thống.
[Biên bản](kiem-chung-bao-cao-chi-ma-20260918.md).

## 18.09.2026 (tối, CLI) — Bố cục Báo cáo tổng hợp theo bản vẽ (Việc A); Việc B bỏ vì Codex đã làm theo THUANLT

Theo bàn giao 18.09 và bản vẽ `docs/tham-khao/ban-ve-bao-cao-tong-hop-20260918.html`: bộ lọc ba trạng
thái `data-filters` (mở 260px, thanh dọc 48px có huy hiệu, dưới 900px ngăn kéo mặc định đóng), nhớ phiên
`{filters, focus}` đọc được khoá cũ, Toàn màn hình → thanh dọc, Escape đóng ngăn kéo trước; hàng chip bộ
lọc (kể cả Tệp) với × bỏ đúng tham số; bảng ghim tiêu đề + dòng Tổng + cột định danh trái theo lớp
`.report-identity` tổng quát (vị trí 1–4, `left` bằng biến CSS), bỏ rule cắt tên; thay trọn khối CSS
`.report-*`, giữ Chọn nhanh kỳ và ô Tệp khách hàng của Codex — AC-22.13. Việc B (mã nhân sự) CLI đã làm
xong local theo quy tắc `NTLH01` đúng bàn giao sáng, nhưng Codex đã đẩy ADR-037 theo sheet Quy ước
(`THUANLT`) cùng tên trường và migration; bản CLI bỏ, giữ nhánh cục bộ `backup/a-b-local-20260918`.
Kiểm: `reports/tests` (kèm hai bài Chromium mới) + `core/tests/test_giao_dien.py` + `tests/test_truy_vet.py` trên đầu nhánh `3748ea9` của Codex: 0 đỏ sau khi sửa hai khẳng định (`test_activity` so header cột định danh, chip Nhân sự theo nhãn mã của ADR-037); bộ đếm docs/06 225 tiêu chí, 212 tự động, 188 có bài kiểm; Chromium 8020 sau gộp (`storage/bo-cuc-bao-cao/sau-gop-*.png`): 1440 mở, 390 đóng, chip đủ, 5 nút Chọn nhanh, nhãn `mã · họ tên` của Codex, không tràn ngang, không lỗi JS. [Biên bản](kiem-chung-bo-cuc-bao-cao-tong-hop-20260918.md).

## 18.09.2026 (tối) — Bảy PTTT theo sheet Vận đơn (đóng TL-44, bổ sung ADR-031)

Chủ dự án chốt: PTTT căn cứ sheet "Vận đơn" của tệp Quản trị nội bộ — Zelle, PayPal, Visa/Website,
Cheque, Western Union, RIA, Money Gram. `ACTIVE_PAYMENT_METHODS` lên 7 (mã mới `visa_web`, `cheque`,
`western`, `ria`, `moneygram`, đều ≤ 12 ký tự nên không đổi cột), migration `orders/0010` chỉ đổi choices;
form Lên đơn, lưới (`pttt`, `pttt_thuc_te`), nhập tệp và `upgrade_schema` (bổ sung lựa chọn cho bảng có
sẵn) dùng chung hằng số nên không sửa thêm. Tệp thật `vandon-mau.xlsx` vào đủ 221/221 (AC-11.9 viết lại).
**Đã phát hành VPS** (xác nhận 19.09: ô PTTT trên domain thật đủ bảy loại).
Chưa làm theo sheet: trạng thái thanh toán thứ tư "Thanh toán lỗi", 7 trạng thái vận chuyển, khối Đối soát
kế toán — vẫn chờ chốt như mục dưới. Kiểm: xem test-log 18.09 (tối).

## 18.09.2026 (tối) — Hoàn thành trang MKT: mã nhân sự, bảy thị trường, nộp tự do, Kế toán sửa, Tệp khách hàng, Doanh thu suy ra, Chọn nhanh

Theo kế hoạch đã duyệt từ sheet MKT của `Quản trị nội bộ.xlsx` (ADR-037, ADR-038, ADR-031 bổ sung):

- **Mã nhân sự** `UserProfile.staff_code` (quy tắc THUANLT, cố định, tự gán khi rỗng; tài khoản
  mới đăng nhập bằng mã, hoa/thường đều được — `core/auth_backends.py`); một nguồn danh tính
  `core/identity.py` (`employee_code`, `identity_label`, `code_expression`, `label_expression`),
  bộ lọc `|ma`, `|ma_ten`; mọi chỗ định danh hiện **mã trước, tên sau**; lệnh một lần
  `gan_ma_nhan_su_cu` (xem trước / `--xac-nhan`). Migration `org/0005`.
- **Bảy thị trường / tám loại tiền** (EU/EUR, KR/KRW, JP/JPY, AU/AUD thêm), tỉ giá mặc định
  theo sheet, **KRW để trống** chờ kế toán; `configure_erp_reports` bổ sung giá trị cho cột
  Thị trường/Loại tiền có sẵn. Migration `orders/0009` (no-op SQL).
- **Nộp báo cáo không giới hạn số lần/ngày** (bỏ `report_unique_per_person_per_day`, migration
  `reports/0004` — chiều ngược thất bại nếu đã có trùng); **Kế toán xem và sửa mọi báo cáo**
  (`reports/managers.py`, `forms_builder/managers.py`, `activity_service.records`, `can_amend`),
  không bỏ báo cáo người khác. `ACCOUNTING_DEPARTMENT_CODE` và `org_service.is_accountant` một chỗ.
- **Tệp khách hàng** = cột Chọn một `tep_khach_hang` (danh sách mặc định theo sheet, Leader/Manager
  MKT thêm ngay ô chọn), ánh xạ `segment`, bộ lọc `tep` (`__missing__`, giá trị lạ → 400).
- **Doanh thu Marketing suy ra từ vận đơn** (`activity_service.marketing_revenue`, một truy vấn
  trên `WaybillItem.paid_amount`, đơn có Phụ trách Marketing = marketer, theo ngày lên đơn, cùng
  sản phẩm/quốc gia khi lọc); `SummaryResult.derived`; **Hóa đơn/Doanh thu = Hóa đơn ÷ Doanh thu**
  theo nhãn (thay K/J 09.09); `configure_marketing` không tạo cột nhập Doanh thu, gỡ trường khỏi
  biểu mẫu, bỏ cột tính từng dòng. Lọc Tệp khách hàng thì Doanh thu trống.
- **Chọn nhanh kỳ** (`summary_service.date_presets`, nút trong bộ lọc, JS áp ngay).
- Kiểm chứng: `pytest -m "not cham"` toàn bộ xanh; diễn tập máy sạch (migrate → du_lieu_mau →
  configure → gan_ma) và xuôi/ngược ba migration; Chrome — xem
  [biên bản](kiem-chung-trang-mkt-20260918.md). AC mới: AC-4.7, 4.8, 37.1–37.6, 38.1–38.5
  (`docs/04`), bộ đếm `docs/06` cập nhật. **Còn nợ:** Báo cáo Nội dung (D8, đợt sau); hạn nộp
  (N1/H8); tỉ giá KRW; Việc A (bố cục) của bàn giao CLI cần thêm chip `tep` và giữ nút Chọn nhanh.
  Phát hành VPS theo mục mới trong `daily-tasks.md`; prompt dán vào Claude Code CLI ở máy chủ dự án:
  [prompt-cli-phat-hanh-adr036-mkt-20260918.md](prompt-cli-phat-hanh-adr036-mkt-20260918.md).
## 18.09.2026 (chiều) — Một bảng vận đơn duy nhất "Vận đơn mới" (ADR-036)

Chủ dự án chốt: cả hệ thống chỉ dùng một bảng vận đơn `van_don`; **xoá cứng** crmThuận
(`van_don_moi`) và Vận đơn DB (`van_don_db`); **bỏ hẳn** Bảng nhận đơn; **cho phép dòng
không có Chi tiết sản phẩm**. Đã làm: `ACTIVE_WAYBILL_TABLE_CODE = "van_don"`; `WAYBILL_COLUMNS`
= 25 cột chuẩn + 9 cột giữ lại; `ensure_waybill_table` tạo mới hoặc nâng cấp tại chỗ
(`waybill_service.upgrade_schema`, gắn `workflow=waybill`, không ép cột bắt buộc vì tệp thật
thiếu Mã đơn); `push` ghi thẳng; hook lưới gộp Trùng với profile (`crm/services/waybill_grid.py`,
TL-35/36 đóng); `prepare_values` chấp nhận không chi tiết và quốc gia trống; xoá
`destination_service`, `waybill_db_service`, `chuan_bi_bang_nhan_don`, trang/route/nav, cột
`receives_orders` (migration 0014); lệnh `xoa_bang_van_don_cu --dong-y-xoa-cung --backup-da-lam`;
`nap_du_lieu_van_don_moi` → `nap_du_lieu_van_don`, `nap_khach_mau` và `seed_perf` (ghi thô) vào
`van_don`; ma trận phân quyền: Sale vào lưới vận đơn = "Chuyển Lên đơn". Bài mới
`crm/tests/test_mot_bang_van_don.py` (AC-36.1 → 36.7); xoá 8 tệp test và 3 script Bảng nhận đơn;
gạch AC-11.39, AC-18.9; ~40 script/perf đổi URL. Tài liệu: ADR-036, đánh dấu ADR-018/029/034,
docs/02/04/05, CLAUDE.md, `deploy/production/README.md`, `docs/daily-tasks.md` (runbook phát hành
có bước xoá cứng sau backup). Kiểm: xem test-log 18.09 (chiều) và
[biên bản](kiem-chung-mot-bang-van-don-20260918.md).
Kiểm local: pytest 2.384 đạt / 0 đỏ (không `cham`), `cham` 13 đạt 2 xfail; DB dev `xoa_bang_van_don_cu` xoá 385.000 dòng giả trong 56 s; Chromium 8 điểm đạt (xem biên bản). Sửa thêm nhờ kiểm: `_payment_label` nhận "Đã Thanh Toán" của tệp thật; câu chú thích Lên đơn; teardown `test_hieu_nang` (TL-42).
**Đã phát hành VPS** — xác nhận 19.09 bằng ba phép thử trên domain thật (Bảng nhận đơn 404, hai bảng cũ
biến mất, PTTT đủ bảy loại); lần phát hành đó không để lại biên bản, xem
[ghi nhận bổ sung](kiem-chung-phat-hanh-vps-20260919-xac-nhan.md). **Còn nợ:** TL-43 lệnh xoá 50.000 dòng treo một lần chưa tái hiện; script Codex chỉ `node --check`, chưa chạy lại; các bảng đặc tả
"Quản trị nội bộ" (Đối soát kế toán 3 lần, Đối soát với kho, trạng thái vận chuyển 7 giá trị,
PTTT 7 loại, báo cáo giữa ca) vẫn chờ chủ dự án chốt.

## 18.09.2026 (chiều) — Phát hành TL-41 lên VPS: image `knjsc-app:5b68dce-tl41`

Chủ dự án chọn "sửa toàn bộ": sửa tay hai cột `loai_tien` trên VPS trước (VND → VND/USD/CAD/PHP, 101 dòng cũ
giữ VND) rồi phát hành `5b68dce` theo khuôn: backup restore thật khớp, không migration, `check --deploy` sạch,
`configure_erp_reports` chạy lại không đổi, 5 service cùng image, hai domain 200, log sạch. Bản sửa song song tại
máy này (AC-22.13) đã bỏ để không trùng `5b68dce`. [Biên bản](kiem-chung-phat-hanh-vps-20260918-tl41.md).
**Còn nợ:** chủ dự án nộp lại báo cáo Canada trên domain thật để xác nhận; kiểm Sale/CSKH trên domain thật.

## 18.09.2026 (chiều) — TL-41: cột Đơn vị tiền của báo cáo nhận đủ USD/CAD/PHP

Vẫn "Chưa nộp được — CAD không có trong danh sách của cột Đơn vị tiền. Chọn: VND"
sau khi phát hành `5b7922f`, vì việc này chờ chủ dự án chọn cách. Chủ dự án giục,
làm theo cách khuyên: `configure_erp_reports` gặp cột `loai_tien` có sẵn thì bổ
sung ba mã tiền theo quốc gia (`MARKET_CURRENCIES`), giữ VND và tên cột, chạy lại
không đổi, cột không phải Chọn một thì báo lỗi. Bài `reports/tests/test_configure_currency_options.py`
(AC-22.12). **Trên VPS hết lỗi sau khi phát hành commit này và chạy `configure_erp_reports`**
(đã nằm trong dãy lệnh phát hành). Không đụng dữ liệu cũ.

## 18.09.2026 (chiều) — Phát hành lưới như Excel lên VPS: image `knjsc-app:5b7922f-excel`

Theo khuôn 17.09: backup restore thật vào DB tạm khớp số dòng; build tại VPS, `check --deploy` sạch, không
migration, metadata + `collectstatic`, 5 service cùng image mới, hai domain 200, log sạch (ERP chỉ có
`DisallowedHost` do bot gọi thẳng IP). Chromium domain thật với tài khoản Vận đơn Staff tạm `kiem.vd`
trên `van_don`: bấm ô chỉ chọn, gõ phím mở ô nhập với ký tự vừa gõ, Ctrl+A chọn `A1:AK11 · 407 ô`; trên
dòng kiểm `KIEM-VD-1809` (tạo bằng service vì Vận đơn không tạo dòng trên lưới, `protect_table`) chọn
Thành phố→Quốc gia rồi Delete: hỏi xác nhận một lần, chấp nhận → Đã lưu, Quốc gia và Loại tiền trống, tiền
giữ 12, lịch sử ô ghi đủ, 0 lỗi JS. Dòng kiểm đã đánh dấu xoá, `kiem.vd` đã khoá.
[Biên bản](kiem-chung-phat-hanh-vps-20260918-excel.md). **Còn nợ:** TL-41 (cột Đơn vị tiền chỉ VND) chờ chủ
dự án chọn cách; chưa kiểm Sale/CSKH và chưa lên đơn thật trên domain thật.

## 18.09.2026 — Lưới như Excel (bấm chọn, gõ là nhập); xoá Quốc gia thì Loại tiền trống

Video chủ dự án trên VPS: Ctrl+A không chọn cả bảng, xoá cả bảng bị "Chọn quốc gia
hợp lệ để xác định loại tiền" rồi dữ liệu về như cũ. Nguyên nhân (1): sau ADR-033
bấm ô là mở ô nhập nên Ctrl+A rơi vào ô nhập; (2): xoá trống Quốc gia thì
`currency_service.for_label('')` ném lỗi, lượt ghi nguyên tử nên bỏ cả lượt. Chốt:
thao tác **như Excel** (bấm chỉ chọn, gõ phím là nhập với ký tự vừa gõ, Enter/F2/bấm
đúp mở ô, Tab/Enter chỉ chuyển ô) và **Quốc gia trống thì tiền trống**, dòng có tiền
hỏi xác nhận, nhập tệp/lên đơn vẫn bắt buộc. Sửa `master-grid.js`, `currency_service`,
`record_service`, hai script Codex, bài AC-33.8, ADR-033/031 bổ sung, docs 02/04/05/06,
CLAUDE.md. [Biên bản](kiem-chung-luoi-excel-quoc-gia-trong-20260918.md).
**Còn nợ:** ~~phát hành VPS~~ (đã phát hành chiều 18.09, mục trên); **cột Đơn vị tiền của Báo cáo Marketing/Sale chỉ có VND**
(kịch bản 15.09 tạo) trong khi báo cáo tự điền USD/CAD/PHP theo quốc gia → "Chưa nộp
được"; đề xuất `configure_erp_reports` bổ sung ba mã tiền vào cột có sẵn, chờ chủ dự án gật.
## 18.09.2026 — Phát hành bốn góp ý lên VPS: image `knjsc-app:0d970f8-gopy`; Vận đơn mới là bảng nhận đơn duy nhất

Theo khuôn 17.09: backup restore thật vào DB tạm khớp số dòng; **diễn tập bước chuẩn bị `van_don` trên bản sao
dữ liệu thật** (33 → 36 cột, chọn được) rồi mới làm thật; build image tại VPS, `check --deploy` sạch, không
migration, metadata + `collectstatic`, 5 service cùng image mới, hai domain 200, log sạch. Chrome domain thật:
Vận đơn DB hết ô trống/che cột, Báo cáo tổng hợp có Nhân sự/Leader mỗi ngày một dòng. Chủ dự án xác nhận bảng
**"Vận đơn mới" (mã `van_don`, có cột Trùng rồi Ngày)** là bảng nhận đơn duy nhất: đã chuẩn bị (36 cột, 11 dòng
nguyên) và chọn trên production; trang Bảng nhận đơn hiện "Hiện tại: Vận đơn mới", ba bảng đều chọn được.
[Biên bản](kiem-chung-phat-hanh-vps-20260918.md). **Còn nợ:** chưa lên đơn thử trên production; chưa kiểm vai
Vận đơn/Sale/CSKH trên domain thật.

## 18.09.2026 — Bốn góp ý sau phát hành ADR-033 (local, chưa VPS): 1.000 dòng trống, bảng nhận đơn, cột ghim, báo cáo ngày × nhân sự

Chủ dự án thử trên domain thật và nêu bốn việc; kế hoạch duyệt trong phiên, làm trọn trên local.
(1) **Lưới 1.000 dòng trống sẵn** (`DRAFT_BATCH`, `absorbCreated` nối dòng vừa tạo vào cache thay
vì `invalidate()`, `geometry.resize` giữ chiều cao hàng): tạo dòng không còn tải lại khối JSON,
tới dòng 999 thêm 1.000 — AC-11.37. (2) **Bảng nhận đơn liệt kê mọi bảng vận đơn** (ADR-034,
`_is_waybill_like`): `van_don` cũ hiện ra nhưng chưa chọn được vì thiếu cột Loại tiền chuẩn;
báo cáo ngày cùng bộ phận không còn lọt — AC-11.39. (3) **Cột ghim đứng đầu thứ tự nhìn thấy**:
hết bôi đen sai, hết ô trống và che cột ở Vận đơn DB — AC-11.38. (4) **Báo cáo tổng hợp**
(ADR-035): Tổng hợp giữ mỗi ngày một dòng, thêm cột Nhân sự và Leader (`Team.leader`) gộp tên ngay
sau Ngày, Theo nhân viên thêm Leader, Excel cùng cột, 100 nhóm/trang, bảng 13px ô 5×8 px;
phạm vi Staff/Leader/Manager **đã có sẵn** qua `apply_scope`, chỉ kiểm lại — AC-22.10, 22.11.
Kiểm: `reports/tests` 133 đạt; hai bài Chromium mới chạy trong container (`playwright install
chromium`) đạt; hồi quy `crm/tests orders/tests forms_builder/tests core` 1.261 bài, 0 đỏ (13 bỏ qua do thiếu môi trường). Ảnh `storage/gop-y-adr033/`.
[Biên bản](kiem-chung-gop-y-sau-adr033-20260918.md).
**Chiều 18.09, ba phản hồi tiếp:** (a) giật khi gõ rồi Enter, cả local — tracer theo frame tìm ra hai
nguyên nhân thật: poll `moi-nhat/` 8 giây coi mốc do **chính mình** lưu là người khác sửa → `invalidate()`
hoá 360 ô thành `…` rồi tải lại; và mỗi dòng trống thành bản ghi thì thanh "Đã tạo dòng" ẩn/hiện đẩy lưới
33 px, tổng dòng +1, nháp bị bỏ trước khi dòng thật nối. Sửa: `luu-json` trả `latest`, `refreshSoft()`
giữ ô cũ khi tải lại, `absorbCreated` nối trong một bước, bù nháp theo đợt, bỏ thanh thông báo —
AC-11.40, tracer sau sửa: 0 nhảy, 0 ô `…`, tổng không đổi. (b) Báo cáo tổng hợp **hoàn lại** mỗi ngày
một dòng (tôi đã tự đổi nhóm, chủ dự án không yêu cầu): hai cột Nhân sự/Leader gộp tên bằng `StringAgg`.
(c) Chủ dự án chốt **`van_don` là bảng duy nhất của Lên đơn**: `prepare_existing` thêm `_upgrade_schema`
(42 → 45 cột, giữ 234 dòng), local đã chọn `van_don`, Lên đơn ghi `DH-1809-0001` vào đó; VPS làm lúc phát hành.
**Còn nợ:** phát hành VPS khi chủ dự án bảo (không migration; chạy `chuan_bi_bang_nhan_don --table van_don`
rồi chọn, có backup trước); DB mẫu local đặt leader team Sale 1 là tài khoản khác
`sale.leader` nên ảnh `sale.leader` không có dòng team (dữ liệu mẫu, không phải lỗi); bài
`.cjs` Codex chưa chạy lại trên máy này.

## 17.09.2026 — Phát hành ADR-033 lên VPS: image `knjsc-app:9949062-adr033`

Làm từ máy có SSH, theo bàn giao trong `daily-tasks.md`. Local: `pull --ff-only`
tới `406c544` (hai commit sau `9949062` chỉ là tài liệu), 0013 đã áp sẵn, Chromium
8021 với `vd.staff` (Tôi → `?cua_toi=1`, 10.000 → 3.333 dòng, gõ ô ngay) và `quantri`
(không nút) đạt. VPS lúc 23:26: backup `release-adr033-20260917-232356` **restore thật
vào DB tạm, số dòng khớp** rồi xoá; kho ff tới `406c544`; build image tại VPS với
`INSTALL_DEV=0`; `check --deploy` sạch cả CRM lẫn ERP; `migrate` áp đúng **hai**
migration `forms_builder.0013` và `reports.0003`; ba lệnh metadata và
`collectstatic` đạt; 5 service cùng image mới, giới hạn tài nguyên giữ nguyên,
restart 0, log sạch; hai domain 200. Chrome domain thật bằng admin: lưới
`van_don_moi` 1 dòng và `van_don_db` 6.667 dòng không lỗi JS, Báo cáo tổng hợp bản
mới có "Toàn màn hình", đăng nhập chung còn chạy. Hai dự báo từ diễn tập:
`bao_cao_mkt` **0/51 dòng thiếu `loai_tien`** nên không có dải vàng; `bao_cao_sale`
đã có 50 dòng, chỉ `bao_cao_van_don_ngay` xuất hiện rỗng. 502 thoáng qua 8 giây khi
thay container CRM, đã ghi. DB thật 31 MB, không phải 1,25 GB.
[Biên bản](kiem-chung-phat-hanh-vps-20260917.md).
**Còn nợ:** chưa kiểm trên VPS bằng tài khoản Vận đơn, Sale, CSKH (chủ dự án chưa
đặt tệp tài khoản kiểm); `app/org/management/commands/du_lieu_mau.py` chưa theo dõi
trên máy Windows trùng tên lệnh ở `core`, chưa quyết giữ hay xoá.

## 17.09.2026 — Nút Tôi / Toàn bộ; nhân viên Vận đơn xem và sửa toàn bảng; bỏ Chế độ xem bảng và Chế độ Xem/Chỉnh sửa (ADR-033)

Chủ dự án thử trên VPS, chốt mặc định công ty: nhân viên Vận đơn thấy **và sửa**
cả đơn của người khác; nút "Chế độ: Xem" và trang "Chế độ xem bảng" (ADR-026)
gây nhầm, xoá hẳn. Ba câu hỏi đã trả lời: sửa được mọi dòng; nút hiện cho mọi
người có cột phụ trách (Vận đơn, Sale/CSKH, Marketing; Admin và Kế toán không);
nhớ trên trình duyệt, mặc định Toàn bộ. Đã làm: bỏ hai điều kiện "phải là người
được giao" ở `assignment_service.scope_condition` và
`grant_service.can_edit_visible_record`; thêm `field_for(user)` và tham số
`cua_toi=1` trong `grid_service.build_grid` (đi theo khối JSON, phiên bản, chip,
Thống kê, Excel); nút `#mg-pham-vi` thay `#mg-mode`, lưới luôn ở chế độ chỉnh
sửa, ô không sửa được mở vùng đọc; xoá trang `che-do-xem/`, service, template,
trường `delivery_view_all` (migration 0013, giữ `delivery_view_version`), hai bài
kiểm và script cũ; 8 script Codex bỏ bấm `#mg-mode`; 11 bài kiểm ghim ADR-020/026
đổi diễn viên sang CSKH hoặc Sale có Grant; bài mới AC-33.1 → 33.7. Tài liệu:
ADR-033, đánh dấu ADR-020/021/026/029, chỉ mục ADR đủ tới 033, docs/02/03/04/05/
06/07, KNJSC_PROBLEM 4/5/8, USER_INQUIRY 6, CLAUDE.md. Kiểm: rebase lên 8 commit
Codex cùng ngày (đợt sửa 19 bài đỏ), toàn bộ `crm orders forms_builder tests core`
còn 3 bài đỏ do quyết định mới (`test_market_currency`, `test_luong_ba_bo_phan`,
bộ đếm `test_truy_vet`) — đã sửa, chạy lại 0 đỏ; Chromium 1440/390 với vd.staff,
vd.manager, sale.staff, quantri — [biên bản](kiem-chung-pham-vi-toi-toan-bo-20260917.md).
**Còn nợ:** chưa chạy trên VPS (máy chủ dự án phát hành, `migrate` có 0013);
script Codex đã sửa chưa chạy lại vì máy ảo thiếu Playwright cho Node.
## 17.09.2026 — Diễn tập nâng cấp VPS 0907cdd → 49e2872

Dựng database ở đúng trạng thái VPS (`0907cdd` + dữ liệu), rồi chạy đúng dãy lệnh
của `deploy/production/README.md` bằng mã `49e2872`. **Đường nâng cấp sạch**: một
migration `reports.0003_report_revision`, đảo ngược được, **10.005 dòng trước và
sau không đổi**; `check --deploy` sạch; `docker compose config` hợp lệ 9 dịch vụ;
gunicorn `settings.prod` khởi động được; Báo cáo tổng hợp ra bản mới, lưới CRM
10.000 dòng không lỗi JS. [Biên bản](kiem-chung-dien-tap-vps-20260917.md).

**Hai việc phải xử lý khi phát hành.** (1) Cột tiền của Báo cáo Marketing sẽ
trống: đo được 5/5 dòng `bao_cao_mkt` thiếu `loai_tien`, `currency_safe_result()`
cố ý bỏ trống để không cộng lẫn tiền tệ. Đã kiểm cách chữa — điền `loai_tien` thì
dải vàng mất và số hiện lại. Cần bổ sung Loại tiền cho dòng cũ trên VPS.
(2) Hai bảng rỗng `bao_cao_sale` và `bao_cao_van_don_ngay` sẽ xuất hiện nếu VPS
chưa từng chạy hai lệnh `configure_*`.

**Claude Code không đẩy được lên VPS.** Đã thử: không có `ssh`, `scp`, `rsync`;
`~/.ssh` rỗng; `curl https://erp.thnsolution.io.vn/` trả `CONNECT tunnel failed,
403` — chính sách mạng của môi trường chặn cả đọc. Phát hành vẫn do Codex làm từ
máy chủ dự án.

## 17.09.2026 — Xoá 12 bài E2E viết cho lưới HTMX cũ

Chạy `pytest` đầy đủ (cả `cham` lẫn `trinh_duyet`, máy ảo có Chromium) cho 14
commit hai ngày qua: **2517 đạt, 12 đỏ**. Cả 12 đều là bài kiểm đi tìm giao diện
đã xoá, **không bài nào chỉ ra lỗi sản phẩm** — đã mở lưới bằng Chromium, sửa ô,
F5, dữ liệu còn nguyên.

Vì sao đỏ âm thầm 36 commit: lưới HTMX cũ bỏ ở `9bac840` (14.09, ADR-021/027),
`tests/e2e/test_bang_tinh_ui.py` lần cuối sửa `cf39064` (06.09). Hai tệp e2e mang
**cả `cham` lẫn `trinh_duyet`**, nên lệnh hằng ngày `-m "not cham"` loại ra, mà
máy không có Chromium thì tự bỏ qua. Hai lớp che.

Không viết lại, vì lưới mới **đã có bài trình duyệt riêng**:
`scripts/kiem-thu-master-ui.cjs` (Ctrl+E/A/C/V/S, bàn phím, clipboard, hoàn tác),
`kiem-thu-shared-grid.cjs` (Ctrl+Z/Ctrl+Y), `kiem-thu-master-row-height.cjs`,
`kiem-thu-master-pinned-ui.cjs` (cột ghim). Viết lại 10 bài Playwright là làm
trùng. Đã xoá `tests/e2e/test_bang_tinh_ui.py`, và bỏ hai dòng `bang-tinh` với
`len-don` khỏi `test_dien_thoai.py` (đường dẫn dời theo ADR-012 và ADR-023); bốn
màn hình 390px còn lại vẫn chạy.

Năm mã tiêu chí mất bài kiểm, đã ghi `HOAN` kèm lý do; `docs/06` nay 154 trên 178,
24 hoãn. Tầng 8 của `docs/06` ghi rõ bài lưới nằm ở `scripts/kiem-thu-master-*.cjs`.

**Hai việc chờ chủ dự án chốt.** `grep` trong `master-grid.js` không thấy
`contextmenu` lẫn dòng trống cuối lưới: **AC-11.21 (menu chuột phải) và AC-11.14
(dòng trống cuối lưới gõ thành bản ghi) là tính năng đã mất khi thay lưới**, mà
`docs/04` vẫn ghi là tiêu chí nghiệm thu. Bỏ tiêu chí hay làm lại tính năng là
quyết định nghiệp vụ, không phải của người viết kiểm thử.

Cùng lượt: thêm stub `repaintSelection` cho `kiem-thu-master-queue-unit.cjs`
(`0907cdd` thêm lời gọi vào `saveAll` mà quên stub, bài đó hỏng từ 16.09).

## 17.09.2026 — Vá nốt đường cấu hình nguồn báo cáo: bốn launcher và VPS

Hôm trước mới gắn `configure_erp_reports` vào `entrypoint.sh`, tưởng là đủ. Dựng
một máy sạch chạy thử thì lộ ra **hai lỗ nữa**, cùng một loại lỗi im lặng.

**Lỗ 1 — entrypoint không chạy trên đường phổ biến nhất.** Thư mục `app/` gắn từ
ngoài vào container, nên pull mã mới thì container không khởi động lại và
entrypoint không chạy. Chính `KN JSC.bat` đã biết điều đó và gọi bù `migrate` với
`tao_bang_van_don` ở bước 5 — nhưng thiếu hai lệnh `configure_*`. `cap-nhat-local.bat`
và `.sh` thủng y hệt. Trên VPS thì `RUN_MIGRATIONS=0` nên entrypoint không bao giờ
chạy phần đó, mà quy trình ở `deploy/production/README.md` cũng không gọi tay.

**Lỗ 2 — thứ tự.** `configure_erp_reports` **bỏ qua bảng chưa tồn tại mà không
báo lỗi** (`if table is not None`), và `ensure_sale()` thoát sớm khi chưa có bộ
phận `sale`. Cả `bao_cao_mkt` lẫn bộ phận `sale` đều do `du_lieu_mau` tạo. Bản vá
đầu tiên đặt hai lệnh **trước** `du_lieu_mau` nên chỉ cấu hình được `van_don_moi`
— đo trên máy sạch mới thấy, không thì lại lọt.

Đã vá năm tệp: `KN JSC.bat` (gộp cờ `CAU_HINH_BAO_CAO`, chạy sau cả hai khối),
`scripts/cap-nhat-local.bat`, `scripts/cap-nhat-local.sh`,
`deploy/production/README.md`, và khối lệnh tay trong `CLAUDE.md`. Máy nào mã
không đổi thì vẫn không chạy gì thêm, giữ nguyên lời hứa "vài giây là lên".

Đo trên máy sạch (DB trống, `knjsc.settings.dev`):

| Thứ tự chạy | ReportSource | Template `/bao-cao/tong-hop/` |
|---|---|---|
| Không có `configure_*` | (rỗng) | `bao_cao_tong_hop.html` — **bản cũ** |
| `configure_*` **trước** `du_lieu_mau` | chỉ `van_don_moi` | `bao_cao_tong_hop.html` — **vẫn cũ** |
| `configure_*` **sau** `du_lieu_mau` | đủ ba nguồn | `activity.html` — **bản mới**, có "Toàn màn hình" |

## 17.09.2026 — Báo cáo tổng hợp toàn màn hình: hết khối trắng dưới bảng

Chủ dự án thấy "ô trắng tinh" khi bấm Toàn màn hình ở Báo cáo tổng hợp: khung
bảng (`.report-table-scroll`) được kéo `flex:1` chiếm hết chiều cao, nền trắng,
phân trang bị đẩy xuống đáy, nên bảng ba dòng để lại một khối trắng cao 700 px.
Sửa một chỗ trong `static/css/solarpunk.css`: khung bảng ôm đúng số dòng
(`flex:0 1 auto`, vẫn cuộn trong khung khi bảng dài hơn màn hình), phân trang nằm
ngay dưới bảng, phần còn lại mang nền dịu `--surface-2`. Kiểm trên máy ảo bằng
Chromium 1440/390 và bảng 42 dòng ở khung 420 px (cuộn trong khung, phân trang
vẫn thấy); `reports/tests` 128 bài đạt. Không đổi JS, không đổi nghiệp vụ.

## 17.09.2026 — Sửa 19 bài kiểm đỏ có sẵn trước khi gộp KN CRM vào main

Nhánh `codex/crm-update-solar-ui` có 19 bài đỏ **từ trước**, không do hai sửa
nút lịch và entrypoint gây ra (đã kiểm lại ở `e5dae4e`). Chúng đỏ vì mã đi
trước tài liệu và bài kiểm, chia bảy nhóm:

| Nhóm | Vì sao đỏ | Sửa |
|---|---|---|
| Bộ phận Kế toán (ADR-025) | `org/0004` thêm bộ phận thứ tư, hai bài còn đếm ba | Đếm bốn; bài hợp trang chỉ đòi vắng bảng vận đơn |
| Tiền theo quốc gia (ADR-031) | Bài xếp hạng còn dựng đơn VND, nay VND không hợp lệ với thị trường nào | Đổi sang PHP thị trường PH, thêm tỉ giá PHP |
| Trùng mã đơn | Nhập tệp nay chặn mã đơn đã có; bài xuất–nhập dùng lại một mã | Thêm khẳng định chặn trùng, dòng thứ hai dùng mã mới |
| Giao diện | Bốn lớp CSS dùng trong template mà chưa khai | Khai `.dashboard-*`, `.thong-bao` bằng biến nền, không màu cứng |
| Ma trận phân quyền (ADR-023) | Lên đơn chuyển sang KN CRM, `/bieu-mau/` thành thư viện hai tab | Thêm kết quả *Chuyển KN CRM*, thêm dòng Thư viện tài liệu; ma trận 45 → **50 ô** |
| Luồng ba bộ phận | Đơn nay lên ở KN CRM | Bài đặt đơn qua URLconf 8021; chiều từ chối kiểm 302 về KN CRM |
| Truy vết | `docs/04` thêm bảng ba cột và hai cột, regex cũ chỉ đọc bốn cột | Đọc cả ba dạng bảng; 191 tiêu chí, 159/178 đã kiểm, 19 hoãn |

19 mã hoãn không phải bài kiểm bị bỏ: AC-24, AC-26, AC-27 là tiêu chí của việc
**đang làm**, chính `docs/04` ghi "đang kiểm chứng". Ghi vào `HOAN` để bài truy
vết đếm đúng, kèm lý do và giai đoạn — quy tắc của `tests/test_truy_vet.py`.

Sau sửa: `pytest -m "not cham"` **2499 xanh, 13 bỏ qua, 0 đỏ**.

## 17.09.2026 — CLAUDE.md theo nhánh đang chạy; cầu nối skill cho Claude Code

Chủ dự án yêu cầu hai việc. (1) Viết lại `CLAUDE.md` cho khớp nhánh
`codex/crm-update-solar-ui`: nhánh chính không phải `main`, VPS và cách phát hành,
lưới `master-grid.js` thay hai tệp HTMX đã xoá, ba bảng vận đơn, cờ `CRM_OPT_*`
tắt, mốc 300.000 dòng / 10 người, lệnh dữ liệu giả, hai điều của AGENTS.md hay bị
quên (duyệt trước, chỉ push khi được yêu cầu), ba lỗi `test_truy_vet` có sẵn, và
ghi rõ TL-01 → TL-34 rà trên lưới cũ. (2) Skill dùng chung: giữ `.agents/skills`
là nguồn duy nhất, thêm 10 cầu nối `.claude/skills/<tên>/SKILL.md` sinh bởi
`scripts/dong-bo-skill.py --tao-cau-noi` (chép `name`/`description`, thân trỏ về
nguồn; không symlink vì Windows, không chép nội dung vì lệch); `--check` và bài
`tests/test_dong_bo_skill.py` bắt lệch. Mâu thuẫn còn để ngỏ: PRODUCT.md (Google
Workspace, 07.09) và ADR-028 (Solarpunk, 14.09) cùng ghi "đã chốt"; chỉ mục ADR
dừng ở 022 và có hai tệp 022 — chưa sửa, chờ chủ dự án.

## 16.09.2026 — Cột Trùng chưa có tác dụng; nạp 300.000 khách mẫu vào Vận đơn DB

Anh/chị xem bảng vận đơn cũ và thấy cột Trùng chỉ hiện con số 2. Rà mã: cột
Trùng chỉ đăng ký cho bảng `van_don` cũ, **Vận đơn DB và `van_don_moi` không
có cột này** (TL-35); đếm theo số điện thoại đúng như gõ nên số ghi khác định
dạng không bắt được, chỉ đếm trong một bảng, không lọc, không bấm, không tô
màu (TL-36). Đề xuất đã gửi anh/chị, **chưa làm gì** cho tới khi chốt.

Lệnh mới `nap_khach_mau` (AC-10.9) nạp 300.000 khách giả theo lô vào Vận đơn
DB: 375.000 dòng, 20 % là khách mua lại, 2 % số dòng mua lại ghi số điện
thoại khác định dạng để đo TL-36; bảng có profile Vận đơn thì có phân công.
Chạy ở máy anh/chị: `docker compose -f deploy/docker-compose.yml exec bangtinh
python manage.py nap_khach_mau --so-khach 300000`, xoá bằng `--xoa-cu --so-khach 0`.
Số đo máy ảo (4 nhân, Postgres 16 mặc định, 16.09): nạp 375.000 dòng hết **220 giây**;
bảng có 301.502 số điện thoại khác nhau (1.502 là số ghi khác định dạng của khách
cũ), **138.694 dòng có số trùng**; bảng DataRecord 896 MB; mở lưới Vận đơn DB lần
đầu bằng Chromium 2,2 giây, chân trang "375.000 dòng khớp bộ lọc", không lỗi JS.

## 16.09.2026 — Kiểm chứng cờ và phát hành tối ưu cuộn (đã phát hành phần đã kiểm)

Bản lưới mới qua 137 hồi quy, E2E lưới chung và hai lượt tải chính 100.000
đơn; 30 Sale + 10 Vận đơn lưu 367/367 đơn đúng. READ/SYNC chưa bật vì
invalidation theo cả bảng làm gián đoạn mở editor khi có đơn ngoài phạm vi;
RENDER chưa có lợi ích bổ sung rõ. Kiểm bền dừng theo yêu cầu sau 14,71 phút đo; chưa đủ 60 phút, đã push/phát hành VPS 0907cdd.
Không đóng nợ 300.000 dòng hoặc hiệu năng VPS. [Bằng chứng](kiem-chung-co-toi-uu-20260916.md).

VPS image `knjsc-app:0907cdd-grid`; Chrome 1440/390 và hash JS đạt, năm service
cùng image, giới hạn tài nguyên/CSS giữ nguyên. Không coi smoke là kiểm tải VPS.

## 16.09.2026 — Mốc thực tế: 300.000 dòng + tối đa 10 người

Chủ dự án xác nhận khoảng 100.000 đơn/năm, kiểm dự phòng 300.000 dòng và tối đa 10 người dùng file Vận đơn. Đã đo trên hai DB giả độc lập: 10 người, đọc toàn bảng p95 local/VPS 1,37/5,04 giây; lọc tháng 8.496 dòng 0,83/3,09 giây. Lưu tương ứng toàn bảng 0,49/2,34 giây, theo tháng 0,31/1,57 giây; không lỗi HTTP hoặc sai giá trị cuối ở 8 lượt chính. SQL phiên bản vẫn quét 300k dòng dù lọc tháng; CPU DB VPS gần hết hai core. Browser VPS nhảy dòng 150k vượt chờ 10 giây; chọn ô vẫn khoảng 36 ms. **Chưa đạt mục tiêu mượt**; cần duyệt tác vụ xử lý server/cache rồi đo lại đúng mốc này, không lấy khảo sát 20 người trước làm yêu cầu. Môi trường đo đã dừng, production giữ nguyên. [Bằng chứng và giới hạn](kiem-chung-300k-10-nguoi-20260916.md).


## 16.09.2026 — Đo đồng thời Vận đơn DB trên VPS và local

Đã đo 1/5/10/20 người trên 10.000 dòng giả, 26 cột, môi trường riêng. VPS 20 người: p95 đọc 965 ms, lưu 848 ms, poll 804 ms; vượt mục tiêu lưu/poll. Local tương ứng 288/272/199 ms. Các lượt hợp lệ không lỗi HTTP, kiểm lại giá trị cuối khớp. Browser 9 Locust + 1 Chrome: local cuộn p95 351 ms, VPS 245 ms; chưa chứng minh tối ưu local giữ lợi ích khi có ghi nền. Ghi nhận 409 đọc gây bỏ cache: cần chốt tác vụ riêng để xử lý, chưa sửa ứng dụng hoặc phát hành. [Phương pháp, số đo và giới hạn](kiem-chung-tai-dong-thoi-20260916.md).

## 16.09.2026 — Sửa riêng bố cục Tổng quan ERP

Đã sửa nhãn–giá trị cùng hàng, bỏ kéo cao thẻ theo Marketing, kiểm responsive và suite báo cáo; push/phát hành VPS commit `da6e2c0`. Không đưa thay đổi báo cáo/lưới chưa phát hành vào bản này. [Kiểm chứng và giới hạn](kiem-chung-tong-quan-20260916.md).

## 16/09/2026 — Chọn ô/nhập trong lúc lưu: đã tối ưu và đo local

Đã tách cập nhật vùng chọn/mở/hủy editor khỏi dựng lại nội dung lưới.
40 lượt/10.000 dòng mô phỏng, trình duyệt Codex 1280×720, giữ request lưu:
p95 chọn/mở/nhập ~33–34 ms; baseline cũng ~34 ms nhưng một lượt chọn 58,1 ms.
Bản cuối max 34,2 ms; DOM tạo mới giảm 51.891 → 466. Đây là phép đo tới hai
rAF của fixture, không phải số đo API/VPS hoặc bảo đảm trên mọi máy.
Giữ nháp mới khi phản hồi cũ về; lỗi lưu và Undo/Redo đã kiểm; 48 test server
và nhóm Node liên quan đạt. Local, chưa push/VPS. Không đánh dấu toàn bộ bảy
hạng mục tối ưu hoàn thành hoặc coi kiểm này là kiểm bộ nhớ dài hạn.
[Chi tiết](kiem-chung-nhap-khi-luu-20260916.md).

## 16.09.2026 — Nhảy xa: gom và ưu tiên request vùng đích (local)

Đã gom 80 ms khi nhảy xa, ngừng tải đón cho tới cuộn ổn định, giữ request
editor/copy dùng chung. Chuỗi 12 vị trí giảm 48→1 request, đổi lại chờ đích
~235–248 ms so với ~139–141 ms trong API mô phỏng trễ 120 ms. Không trì hoãn
cache. Chrome và E2E DB test đạt; chưa đo tải server nhiều người, chưa push/VPS.
[Bằng chứng và giới hạn](kiem-chung-cuon-luoi-20260916.md).

## 16.09.2026 — Cuộn cache và tải trước theo hướng (local)

Đã giảm dựng lại ô khi chỉ cuộn, tải đón tối đa hai khối; cache giữ 10 khối.
Đo Chrome/API mô phỏng trễ 120 ms: p95 cuộn liên tục 140,9→47,7 ms desktop,
136,9→49,4 ms mobile; cached khoảng 32 ms trước/sau. 110 functional và E2E
database test đạt; chưa push/VPS, chưa nghiệm thu tải server nhiều người.
[Kết quả, chi phí request và giới hạn](kiem-chung-cuon-luoi-20260916.md).

## 16.09.2026 — Đổi tên Vận đơn thành crmThuận (local)

Theo yêu cầu chủ dự án, đổi tên hiển thị bảng `van_don_moi` thành `crmThuận`.
Đã cập nhật tên mặc định và chuyển tên cũ khi khởi tạo lại; không ghi đè tên
riêng khác. Local chỉ cập nhật name/updated_at và audit; kiểm trước/sau giữ
ID, code, cờ nhận đơn và số dòng. Chrome mục Bảng nhận đơn hiển thị crmThuận
là lựa chọn hiện tại. 11 test khởi tạo/bảng nhận đơn đạt. Chưa commit/push/VPS.


## 16.09.2026 — Ngày hệ thống và chỉnh sửa báo cáo (local)

Đã triển khai theo ADR-032: nhập ngày DD/MM/YYYY; báo cáo mới khóa ngày Việt
Nam và người nộp; Leader sửa trong team, Manager trong bộ phận, Admin toàn
hệ thống, có lịch sử và chống ghi đè bản cũ. Staff không sửa báo cáo đã nộp,
kể cả qua lưới. Marketing có Doanh thu/Hóa đơn và năm công thức đã chốt;
loại tiền lấy theo thị trường. Tổng tiền khác/thiếu đơn vị để trống có giải thích.
Bổ sung 16/09: đã sửa phần đọc ô ngày và chip lọc lưới còn sót, 34 test đạt.
256 test nhóm cuối đạt; đã kiểm trình duyệt luồng sửa, ngày, lưới và mobile.
Lỗi nhập lại mã đơn trùng tái hiện cả ở HEAD 5ce53f3, không đổi nghiệp vụ nhập.
Phần báo cáo này chưa commit/push/VPS; lỗi thêm sản phẩm 404 trên domain thật
vẫn mở, không coi kết quả local là đã sửa 404.
[Chi tiết và giới hạn](kiem-chung-bao-cao-erp-20260916.md),
[quyết định thay thế](quyet-dinh/032-ngay-he-thong-va-sua-bao-cao.md).

## 16.09.2026 — Đã phát hành tiền/PTTT, bỏ Đơn vị phụ và sửa cột ghim

Đã push mã `5ce53f3`, VPS chạy `knjsc-app:5ce53f3-market-20260916` trên
ERP/CRM và các worker. Hồi quy đúng bản phát hành: 535 đạt, 1 lỗi nền,
17 skip; E2E database test và Chrome VPS 1440/390 đạt. Giữ hotfix sidebar.
Đã xử lý 502 sau thay container bằng nạp lại proxy; không ghi thử dữ liệu VPS.
Mục này thay thế trạng thái chưa push/VPS của các mục cùng phạm vi bên dưới.
[Chi tiết phát hành và giới hạn](phat-hanh-tien-te-20260916.md).

## 16.09.2026 — Màu ba cột ghim trên VPS

Đã sửa CSS kế thừa theme tối gây chữ chìm, kiểm Chrome domain thật sáng/tối
1440/390 đạt. VPS image `7b827a6-pinned-contrast-20260916`, giữ hotfix sidebar.
Chưa commit/push; các thay đổi nghiệp vụ local không được phát hành cùng.
[Bằng chứng và quay lui](kiem-chung-mau-cot-ghim-20260916.md).

## 16.09.2026 — Bỏ Đơn vị phụ trên Lên đơn

Đã bỏ ô nhập và dòng hiển thị ở đơn gốc; giữ dữ liệu lịch sử và đơn vị sản
phẩm. 36 test và Chrome 1440/390 đạt. Local, chưa commit/push/VPS.
Quyết định thay thế tại ADR-023; log `storage/market-currency/subunit-*`.

## 16.09.2026 — Tiền theo quốc gia, PTTT Zelle/PayPal

Đã triển khai/kiểm local: tiền tự theo US/USD, CA/CAD, PH/PHP; đổi quốc gia
có tiền phải xác nhận giữ số tiền. Form/lưới dùng chung hai phương thức.
15 test mới và Chrome 1440/390 đạt. Chưa commit/push/VPS.
[Quyết định](quyet-dinh/031-tien-theo-quoc-gia-va-pttt.md),
[kiểm chứng và ba lỗi test nền](kiem-chung-tien-theo-quoc-gia-20260916.md).
Các lỗi nền: test nhập lại mã trùng và hai test còn kỳ vọng form Lên đơn ở ERP;
cần cập nhật theo quyết định đã chốt trong tác vụ riêng, không nới service.

## 16.09.2026 — Báo cáo ERP, local trước

Đã thêm lọc team/người, bảng tổng hợp kẻ ô, biểu mẫu ngày Vận đơn năm trường,
nút ẩn bộ lọc/toàn màn hình bảng và 36 mẫu đã nộp vào lịch sử.
113 test báo cáo và endpoint sản phẩm đạt;
đã kiểm UI local. **Lỗi 404 thêm sản phẩm trên domain thật còn mở**, chưa
tái hiện; không coi thao tác Sale local thành công là đã sửa VPS.
[Phạm vi, bằng chứng và phần còn lại](kiem-chung-bao-cao-erp-20260916.md).

## 15.09.2026 — Chuẩn bị Vận đơn DB nhận đơn

Đã bổ sung chuyển cấu hình bảng placeholder theo duyệt, giữ dòng/cột và đích
hiện hành; 87 test và Chrome 1440/390 đạt. VPS cf51ad2 đã bật lựa chọn; 6.667 dòng giữ nguyên.
[Kiểm chứng](kiem-chung-chuan-bi-bang-nhan-don-20260915.md).

## 15.09.2026 — Đăng nhập chung ERP/CRM

Đã kiểm local: cookie dùng chung, hai chiều/bốn cấp quyền, 16 kịch bản Chrome
HTTPS đạt. Đã phát hành VPS cdc1a45, Chrome domain thật 4/4 đạt; giữ lỗi CSS nền ở màn hình chọn
bảng nhận đơn (`loi`, `thong-bao`) trong backlog, không đóng cùng tác vụ này.
[Kiểm chứng](kiem-chung-dang-nhap-chung-20260915.md).

## 15.09.2026 — Daily tasks: tối ưu lưới và nhập thiếu Vận đơn DB

Chủ dự án chọn phương án 1 (tải theo vùng nhìn/tải trước có giới hạn), chưa
triển khai. [Daily tasks](daily-tasks.md) lưu đủ 7 hạng mục, dự đoán có điều
kiện và tiêu chí kiểm chứng. Đã xác định job nhập #3 tạo 6.667/10.000 dòng:
3.333 dòng có “Đã về TK” bị từ chối vì danh sách lựa chọn `doi_soat` rỗng;
chưa sửa cấu hình hoặc nhập bù. Đây là vấn đề nhập dữ liệu, tách khỏi tối ưu cuộn.

## 15.09.2026 — Hai bảng báo cáo mẫu đã có trên VPS

Đã tạo Marketing/Sale, mỗi bảng 50 dòng, 5 team và 10 nhân sự “Mẫu” không
đăng nhập được; nguồn/biểu mẫu chuẩn đã có. Kiểm DB và hai lưới domain thật đạt.
Giữ nguyên vận đơn/dịch vụ/phiên SSH khác. [Kiểm chứng](kiem-chung-bao-cao-mau-vps-20260915.md).

## 15.09.2026 — Đã sửa lỗi mẫu nhập trên local

Thay thế trạng thái còn lỗi ghi bên dưới: sửa preview lệch cột, bỏ cột chỉ xuất
khỏi mẫu, căn lại workbook, báo lỗi trước xác nhận và chặn nhập trùng mã đơn.
30 test đạt; trình duyệt kiểm ba mẫu, lỗi/trùng và 10.000 dòng đạt trên DB riêng.
Chưa kiểm trực tiếp Microsoft Excel/chưa VPS. [Chi tiết](kiem-chung-mau-nhap-van-don-20260915.md).

## 15.09.2026 — Kiểm thực tế mẫu nhập: còn lỗi cần xử lý

Nhập qua UI đủ 3 khách/bảng và 10.000 khách DB; còn lỗi preview lệch cột,
mẫu Vận đơn kèm 4 cột chỉ xuất, preview chưa báo lỗi giá trị, rủi ro nhập lại
tạo trùng mã đơn. Chưa sửa nghiệp vụ; chưa đạt nghiệm thu toàn luồng.
[Bằng chứng và phân loại](kiem-chung-mau-nhap-van-don-20260915.md).

## 15.09.2026 — Kiểm lại luồng Bảng nhận đơn

68 test trực tiếp đạt, Chrome 1440/390 đạt và DB xác nhận đơn cũ giữ bảng. Hồi quy rộng: 616 đạt, 1 lỗi, 14 skip. Lỗi tại `crm/tests/test_trang_chu.py:137`: test còn đòi nhãn “Sửa”, trong khi tác vụ Tải mẫu Excel đã bỏ nhãn. Chưa sửa test ngoài phạm vi; không kết luận toàn suite đạt. [Bằng chứng](kiem-chung-bang-nhan-don-20260915.md).


## 15.09.2026 — Tải mẫu Excel vận đơn (local)

Đã thêm tải mẫu theo từng bảng và bỏ nhãn Sửa trên thẻ. Kiểm tải/nhập lại, quyền và trình duyệt local đạt; chưa push/VPS. [Kiểm chứng và giới hạn](kiem-chung-mau-nhap-van-don-20260915.md).

## 15.09.2026 — Chọn bảng nhận đơn tại CRM (local)

Admin chọn đích nhận đơn mới; bảng/đơn cũ giữ nguyên. Đã áp migration 0012 local, chưa đổi đích mặc định, chưa commit/push/VPS. Sau sửa cuối 67 test liên quan đạt; Chrome 1440/390, hai ca 30 Sale đồng thời và migration xuôi/ngược đạt. [Kết quả và giới hạn](kiem-chung-bang-nhan-don-20260915.md) · [ADR-029](quyet-dinh/029-bang-nhan-don-crm.md).


## 15.09.2026 — Sửa sidebar CRM thu gọn

Đã sửa logo/icon nhóm lệch trái khi thu gọn theo ảnh chủ dự án, kiểm Chrome
sáng/tối, thu/mở và reload; triển khai CSS hotfix trên VPS theo yêu cầu.
[Kết quả, cách triển khai và giới hạn](kiem-chung-crm-sidebar-20260915.md).

## 15.09.2026 — Mở rộng giao diện KN ERP trong tab

Đã có bản thử local: cụm Hiển thị trên header dùng icon Mặt trời/Mặt trăng và
Mở rộng. Chế độ mở rộng phủ ERP sát bốn cạnh, bỏ ảnh nền, gutter, bo góc và bóng
ngoài; giữ header/dock để điều hướng, còn Tập trung của bảng vẫn ẩn chúng theo
luồng riêng. Nút này chỉ đổi bố cục trong tab, không gọi Fullscreen API nên không
ẩn thanh địa chỉ hoặc tab Chrome; Esc thu gọn giao diện. Chrome 1440/390 đạt;
lựa chọn được lưu và phục hồi trước khi vẽ khi chuyển trang hoặc mở tab ERP khác.
Đã phát hành commit chức năng `2ea5ab2` trên nhánh riêng. VPS hiện chạy image
`knjsc-app:8dead1b`, là hậu duệ chứa đầy đủ commit này; không merge `main`.

## 14.09.2026 — Toàn màn hình ERP, sắp lại Vận đơn và tạm khóa Chứng từ

Đã triển khai trên `codex/crm-update-solar-ui`: dock ERP thu gọn có nhớ bố cục,
mọi bảng dữ liệu ERP có Tập trung/Fullscreen/Công cụ; ERP vẫn chỉ đọc. `van_don`
giữ mã/ID/222 dòng nhưng đổi nhãn **Vận đơn mới**, thêm Phụ trách CSKH trống và
sắp lại cột; `van_don_moi` giữ nhãn **Vận đơn** và 10.000 dòng. Bill là text/URL
an toàn; kho Chứng từ mặc định tắt và URL trả 404. Không tạo 100 bill/ảnh mẫu.
Full suite cuối: 2.332 đạt, 15 lỗi nền, 31 skip và 2 xfail; không có lỗi mới.
Đã push nhánh và triển khai VPS ngày 15.09 tại image `knjsc-app:97741e4`, sau
backup; HTTPS/tệp tĩnh/check/log đều đạt. Không merge `main`.
[Kiểm chứng](kiem-chung-erp-vandon-bill-20260914.md).

## 14.09.2026 — Hợp nhất CRM-UPDATE và Solar UI

Nhánh `codex/crm-update-solar-ui` giữ CRM-UPDATE làm nguồn chuẩn nghiệp vụ và
phủ giao diện Solar lên bốn khung. Chrome đã đạt các luồng lưới, sửa trạng thái/
ngày, tự lưu, CAS, phân công, báo cáo và focus. Full suite 2.329 đạt, 15 lỗi nền,
31 skip/2 xfail; không có nhóm lỗi mới. Chưa merge `main`, chưa triển khai và
giữ nguyên các nhánh cũ. [Bằng chứng](kiem-chung-crm-update-solar-ui-20260914.md).

## 14.09.2026 — Tích hợp phần local vào CRM-UPDATE

Đã khôi phục ERP từ stash, ghép sửa Thống kê và chế độ xem Vận đơn; Solarpunk giữ riêng. Functional toàn bộ: 2327 đạt, 17 lỗi đều tái hiện trên nền 9bac840, 31 skip/2 xfail. Chrome định danh, bốn cấp quyền, Thống kê và đổi chế độ xem đạt tại 1440/390. Không kích hoạt runtime chính hoặc chạy lại kiểm tải toàn CRM. [Bằng chứng và giới hạn](kiem-chung-tich-hop-local-20260914.md).


**14.09 — CRM-UPDATE đã kiểm chứng trong worktree riêng:** hoàn tất lưới chung,
xóa/khôi phục bảng, tương phản cột ghim và rút gọn truy vấn phạm vi. Chrome
bốn cấu hình, ma trận 100k/300k × 10/20, 2.000 ô, Celery và bài bền 30 phút
đạt; bài bền 31.985 mẫu, oracle 2.859 dòng không lỗi. Giữ bốn lỗi kiểm thử
nền và 11 skip riêng. Local vẫn nhánh fix; chưa commit/push/kích hoạt.
Tạo bảng trắng/duplicate hoãn; chế độ xem toàn bảng của nhánh fix chưa ghép.
[Biên bản bàn giao](kiem-chung-crm-update-20260912.md).

**12.09, 17:20 — Chủ dự án yêu cầu test trước:** đã chuyển checkout chính sang `CRM-UPDATE`, cập nhật local 8020/8021 và worker cùng code; không seed/migrate, chưa commit/push. Marketing/Sale đã xác nhận dùng lưới mới. Functional 1.130 passed, 4 lỗi nền, 11 skipped; Chrome chức năng đạt. Kiểm tải tạm dừng: bản cuối mới đủ 100k/10, chưa nghiệm thu toàn chiến dịch. [Kết quả và phần còn lại](kiem-chung-crm-update-20260912.md).

**12.09 — CRM-UPDATE đang kiểm local:** lưới chung Marketing/Sale/Vận đơn cũ,
xóa mềm/khôi phục bảng; giữ Vận đơn mới, ERP và dữ liệu. Đang chạy ma trận tải,
chưa nghiệm thu toàn chiến dịch; tạo bảng trắng/duplicate cấu trúc hoãn.
[Biên bản](kiem-chung-crm-update-20260912.md) · [ADR-027](quyet-dinh/027-crm-update-luoi-chung-va-vong-doi-bang.md).


> Cập nhật 12.09.2026: theo yêu cầu chủ dự án, đã chuyển nhánh codex/chung-tu-thanh-toan về checkout chính C:/KNJSC/KNJSC và kích hoạt app local 8021. Đã áp dụng orders 0007, org 0004; không chạy seed. Các mô tả chưa kích hoạt bên dưới ghi trạng thái bàn giao trước bước này. Chưa commit/push; bản sao checkout cũ giữ nguyên nội dung, ở detached HEAD.

**12.09.2026 — Trạng thái và chứng từ thanh toán:** đã có bản triển khai trong
checkout riêng `KNJSC-chung-tu-thanh-toan`, nhánh `codex/chung-tu-thanh-toan`.
Trạng thái sửa trực tiếp; kho chứng từ, quyền Kế toán, Ref trong Bill, lưu ảnh riêng tư.
Không mở quyền nhập tiền/đối soát. Chưa áp migration vào database đang chạy ở 8021,
chưa commit/push. [Kết quả và phần chưa kiểm](kiem-chung-chung-tu-thanh-toan-20260912.md).
**14.09 — Solarpunk Office (nhánh UI riêng):** đã triển khai khung xanh, báo cáo hai vùng, chế độ tập trung cả hai lưới; preview ERP 18020 / CRM 18021 và dữ liệu riêng. Đã kiểm Chrome hai lưới, lưu/hoàn tác/lỗi mạng/CAS và bố cục sáng/tối; full suite 2154 pass, 14 fail (1 bài nhận diện khung chạy lại đạt, còn 13 lỗi nền); chưa merge/commit/push, không đổi 8020/8021. [Hồ sơ](kiem-chung-solarpunk-20260914.md), [ADR-028](quyet-dinh/028-solarpunk-office.md).


**14.09 — Vận đơn DB:** đã tạo bảng động riêng `van_don_db`, 26 cột lấy từ định nghĩa hiện có, 0 dòng; sắp thứ tự theo file chủ dự án, không có Đơn vị phụ. Chưa nối Lên đơn; không đổi code ứng dụng hoặc bảng nguồn. Đã kiểm cấu hình lưu, tiêu đề HTML và thứ tự xuất. [Chi tiết](cau-hinh-van-don-db-20260914.md).

**12.09.2026, 17:28 — Đã bật nhánh fix để chủ dự án test nút:** checkout chính `C:/KNJSC/KNJSC` và local 8020/8021 hiện chạy `fix/trung-ma-don-dong-thoi`. Bản CRM-UPDATE được giữ nguyên tại `C:/KNJSC/worktrees/CRM-UPDATE`, chưa ghép. Đã sao lưu database, áp dụng riêng `forms_builder.0011_delivery_view_mode`; không seed hoặc đổi chế độ xem thay người dùng. 10 test chế độ xem đạt trên PostgreSQL test riêng; hai URLconf sạch. Đọc READ ONLY trên local xác nhận trang chế độ xem, liên kết từ lưới và Cột & cấp quyền đều 200; mặc định hiện là theo phân công. Chưa commit/push.

**12.09.2026 — Chế độ xem Vận đơn mới, đã kiểm chứng local:** Admin/Manager
Vận đơn đổi theo phân công/toàn bảng; quyền sửa vẫn theo phân công. Trang
lưới tự reload khi nhận phiên bản mới. 10 test mới, focused cuối 46 passed;
Chrome 1440/390 đạt, migration xuôi/ngược đạt. Hồi quy rộng 500 passed,
4 failed, 10 skipped; 2 lỗi mount fixture chạy lại đạt, còn 2 lỗi markup
nền. Không chạy kiểm tải lớn, không tuyên bố tăng tốc. Đã có diff trên nhánh
fix trong worktree riêng, chưa tích hợp checkout chính/chưa commit/push.
[Bằng chứng](kiem-chung-che-do-xem-van-don-20260912.md), [ADR-026](quyet-dinh/026-che-do-xem-van-don.md).

**11.09.2026 — Sửa trùng mã đơn đồng thời, đạt nghiệm thu local:** nhánh
`fix/trung-ma-don-dong-thoi` từ `a81decd`, worktree riêng. Khóa giao dịch PG
theo DDMM, timeout 5s có kiểm soát, max hậu tố theo số và giữ mã xóa mềm.
TDD/Chrome 1440/390 đạt; lượt 30 Sale + 10 Vận đơn đủ 301,52s đo,
361 đơn đúng, p95 tạo 170,58ms/lưu ô 108,69ms; burst đủ 30/30.
Cờ tắt trong lượt chính, kiểm tương thích bốn cờ đạt. Hai lỗi markup nền và
9 skip giữ riêng; không đóng hiệu năng toàn CRM. Chưa commit/push/merge.
[Bằng chứng và giới hạn](kiem-chung-trung-ma-don-20260911.md).

**11.09.2026 — CRM-Optimization, có bản local; chưa nghiệm thu toàn bộ:** nhánh/checkout riêng,
snapshot đầy đủ đã đóng băng. Đã làm phiên bản/cache quyền, đọc/sync v2,
receipt gọn, tái sử dụng renderer, cache Thống kê 15 giây, xuất write-only
và cấu hình VPS ứng viên. Suite cuối 1.092 passed, 4 lỗi nền, 9 skipped;
E2E/Chrome và tám lượt trước/sau đã kiểm. Bài bền 300k/20 cấu hình 30 phút:
21.828 mẫu, không lỗi mạng/5xx hoặc oracle; 7 CAS dán cùng vùng được tách riêng.
Render chưa cải thiện ổn định, cold Thống kê >1 giây và hàng đợi xuất tăng
là phần còn nợ; cần phân tích thêm RSS app tăng trong bài bền. Cờ mặc định tắt,
chưa commit/push/VPS. Không đánh dấu hoàn thành toàn bộ feedback.
[Biên bản và phần còn nợ](kiem-chung-crm-optimization-20260911.md).

**11.09.2026 — Ba lựa chọn Lên đơn bắt buộc chọn rõ:** Quốc gia/Loại tiền/PTTT mặc định rỗng, chọn hợp lệ mới lưu; đơn kế tiếp trở lại rỗng. 105 test đạt, Chrome 1440/390 đạt, trần 10 truy vấn giữ đạt; không migration/dependency, chưa commit/push. [Bằng chứng bổ sung](kiem-chung-len-don-gio-admin-20260911.md).


**11.09.2026 — Ghim cột Vận đơn mới:** đã thay bù cuộn JavaScript bằng vùng
sticky; đo 100k/300k đạt độ lệch 0 px, cache/request không tăng; hồi quy thao
tác đạt. Render p95 tăng nhẹ; còn nghiệm thu zoom trình duyệt thật/trackpad.
[Biên bản](kiem-chung-ghim-cot-20260911.md). Không đóng lỗi API/kết nối cũ.

**11.09.2026 — Bổ sung giờ lưu và Admin tự đứng đơn (thay quyết định chọn Sale):** Ngày giờ cập nhật HH:mm trên form, thông báo lấy timestamp thực tế đã lưu; bỏ dropdown, Admin/Sale tự đứng bằng mã đăng nhập. Admin thử nghiệm chưa thuộc Sale dùng Sale/team trống, giữ hồ sơ. 117 test đạt; Chrome 1440/390 đạt; kiểm tải đọc 10/20 Admin: 4.782 request đo/0 lỗi, p95 cao nhất 76,38 ms trên fixture nhỏ. Không migration mới, chưa commit/push. [Kiểm chứng và giới hạn](kiem-chung-len-don-gio-admin-20260911.md).


**11.09.2026 — Ngày/đơn vị/mã nhân viên khi lên đơn:** đã kiểm chứng local: Ngày Việt Nam chỉ đọc; chọn hộp/cái/chiếc/túi từng sản phẩm, snapshot trên đơn/vận đơn; mã đăng nhập cho định danh nghiệp vụ và lịch sử. Migration 0006 đã kiểm xuôi/ngược DB test và áp dụng xuôi local. Hồi quy 984 đạt/2 lỗi giao diện thống kê có sẵn; lượt focused cuối 72 đạt; Chrome 1440/390 đạt; Locust đọc 10/20 đạt 4.618 request/0 lỗi. Chống lặp hoãn, không kết luận năng lực toàn CRM. [Bằng chứng và giới hạn](kiem-chung-len-don-20260911.md). Chưa commit/push.


**11.09.2026 — Điều hướng ERP/thư viện/Lên đơn CRM:** đã triển khai local theo ADR-023. Giữ Bảng dữ liệu ERP; sửa Biểu mẫu thiếu người tạo, gộp hai tab đúng quyền; chuyển nhập đơn và xem đơn gốc sang CRM. Kiểm thử, số đo và giới hạn tại [báo cáo bàn giao](kiem-chung-erp-hub-20260911.md). Chưa commit/push.

Nơi ghi lại mọi phát hiện, ý tưởng và câu hỏi chưa được quyết định.

> **Quy tắc:** phát hiện gì thì ghi vào đây trước, **không sửa tài liệu ngay**.
> Chỉ cập nhật tài liệu sau khi đã quyết định thực hiện.
>
> Phát hiện được ghi lại không có nghĩa là sẽ làm. Có thứ đáng làm, có thứ để sau,
> có thứ không bao giờ làm.

---

## Cách đọc

| Cột | Nghĩa |
|---|---|
| Mức | Chặn · Cao · Trung bình · Thấp |
| Trạng thái | Chờ quyết định · Đã duyệt · Từ chối · Đã làm |
| Nguồn | Ai hoặc cái gì phát hiện ra |

**Mức Chặn** nghĩa là không làm thì không triển khai được.

---

## 0. Còn nợ những gì — xem ở đây trước

**11.09.2026 — Admin/nhập ô Vận đơn mới:** đã sửa nguồn options bị null,
draft dang dở và click rê nhẹ; nhập trong ô được chủ dự án duyệt, hồi quy
Chrome/E2E đạt. Chạy bền snapshot `7449e73` đã đủ 30 phút/300k/20 người:
22.460 request, 16 lỗi ngắt kết nối đọc; lọc p95 1,35s còn chưa đạt.
Số đo inline ghi riêng. Suite liên quan 1.041 đạt/2 lỗi/7 skip; hai lỗi rà CSS/nhãn
của Thống kê tái hiện cả trên snapshot trước sửa, còn cần xử lý riêng.
Ba lỗi truy vết tài liệu AC-22/số lượng tiêu chí cũng có từ trước. Lượt ngắn
inline 300k còn đọc/lọc p95 1,28/1,85s và 2 lỗi kết nối đọc; chưa chốt nguyên nhân.
Chưa kiểm lại phiên người dùng/IME thật. Xem
[báo cáo 11.09](kiem-chung-master-admin-20260911.md).

**11.09.2026 — Bàn điều hành KN CRM theo ADR-022:** `/thong-ke/` đã được nâng
cấp từ Thống kê Vận đơn riêng thành góc nhìn tổng hợp Marketing–Sale–Vận đơn và
phân tích chuyên sâu từng bảng đang hoạt động trong phạm vi người xem. Hệ thống
tách tiền tệ, so kỳ liền trước, đưa tối đa ba nhận định theo quy tắc và liên kết
về đúng dữ liệu; không tự nhận là AI, tạo việc hoặc hành động. KNERP giữ Báo cáo
tổng hợp/xuất Excel và chỉ thêm liên kết. Hồi quy tập trung 159 bài đạt; kiểm
trình duyệt đủ 1440/1280/390px, sáng/tối, giảm chuyển động và zoom 125%. Phép đo
20 request sau warmup đạt p95 89,07ms ở 20k Sale, 333,72ms ở 100k Vận đơn,
893,26ms ở 300k Vận đơn và 733,64ms ở góc tổng hợp; đỉnh cấp phát Python của
Vận đơn giữ 0,25MiB ở cả 100k và 300k. Xem
[ADR-022](quyet-dinh/022-ban-dieu-hanh-kn-crm.md).

**11.09.2026 — đã hoàn thiện dữ liệu thử Vận đơn mới trên `vandonmoi`:** nhóm
`MAU-20260910-*` có đúng 10.000 vận đơn Canada/CAD, trong đó giữ nguyên danh tính
500 dòng cũ và tạo 9.500 dòng còn thiếu. Mỗi dòng có địa chỉ, 1–3 chi tiết sản
phẩm, tiền thanh toán từng sản phẩm và phân công Sale/CSKH/Vận đơn hợp lệ. Lệnh
`nap_du_lieu_van_don_moi` chạy lại an toàn, có dry-run và không tạo Customer/Order
ERP. Ghi chú lỗi dấu hỏi được thay bằng dữ liệu UTF-8; kiểm tra xác định đây là
dữ liệu hỏng riêng của nhóm mẫu, không phải lỗi font toàn hệ thống. Giao diện
`van_don_moi` có vùng ba cột nhận diện ghim màu slate và thanh công cụ dễ đọc hơn;
không đổi giao diện bảng CRM khác.

**09.09.2026 — feedback KN CRM trên `codex/sua-feedback`:** đã triển khai
phân công Vận đơn/CSKH/Marketing theo tài khoản, phạm vi theo người được giao,
bộ lọc nhanh/chi tiết và xuất Excel theo ngày/bộ lọc có mã nhân viên.
Xem [ADR-020](quyet-dinh/020-phan-cong-loc-xuat-van-don-moi.md) và
[test-log](test-log.md). H7 vẫn chưa chốt, không mở quyền đối soát.

**Thứ tự thực hiện chốt 09.09.2026:** sửa feedback khách hàng trước; “Việc
cần làm của tôi”, nhắc việc chủ động và AI để giai đoạn sau. Không mở rộng
tác vụ feedback sang các tính năng này. Điểm nghiệp vụ chưa rõ tiếp tục
ghi trong USER_INQUIRY.md, không tự quyết khi sửa.

**09.09.2026 — mục tiêu sản phẩm do chủ dự án xác nhận:** tài liệu KNJSC là
ghi chép phản hồi trong buổi họp khách hàng; `KNJSC_PROBLEM.txt` tổng hợp các
vấn đề từ nguồn đó. Đây là nguồn feedback, không mặc nhiên biến mọi ý thành
yêu cầu đã duyệt. Đích cuối là hệ thống chủ động cho từng người dùng biết
công việc của mình còn gì, giảm việc quản lý phải liên tục vào kiểm tra;
dài hạn tích hợp AI xuyên suốt CRM/ERP. Đã ghi vào PRODUCT.md và AGENTS.md.
Chưa chốt quy tắc sinh việc, hạn xử lý, kênh thông báo hoặc quyền hành động
của AI; chưa triển khai các tính năng này.

**09.09.2026 — đã chốt nghiệp vụ phân công và kế toán, chưa triển khai:**
Leader Vận đơn giao/đổi người phụ trách trên từng dòng. Nhân viên Vận đơn và
CSKH chỉ thấy khách/đơn được giao cho chính mình. Kế toán làm trên cùng bảng
Vận đơn mới, ban đầu cần xem toàn bộ đơn chưa thu tiền; đối chiếu riêng tình
trạng giao hàng (đã giao/chưa giao), tình trạng thanh toán (đã trả/chưa trả)
và bằng chứng khi ghi đã trả. Không suy ra rằng đơn đã trả phải bị ẩn khỏi kế
toán hoặc bộ trạng thái hiện có phải thu về hai giá trị. Quyền nhập/sửa số
tiền và bằng chứng **chưa chốt — [H7 trong USER_INQUIRY](USER_INQUIRY.md)**;
chủ dự án sẽ hỏi người có thẩm quyền.
Chỉ ghi nhận yêu cầu, chưa sửa code, quyền hoặc dữ liệu.

**09.09.2026 — ADR-019:** chủ dự án chốt bỏ Lên đơn nhúng trong bảng Vận đơn,
giữ lưới, thống kê và hai trang Lên đơn riêng. Đã gỡ template, context và sự kiện
tải lại bảng sau tạo đơn; cập nhật AC-18.8 và kiểm thử. Phần bố cục ba khu của
Q79/ADR-018 là lịch sử, được ADR-019 thay thế. Yêu cầu Vận đơn chỉ sửa giao hàng
và thu tiền, không sửa giá/số lượng, cần xử lý ở tác vụ riêng; chưa đổi quyền
chi tiết trong lượt này. Không sửa 20 khách mẫu hoặc database local.
Kiểm chứng: 135 bài CRM/đơn hàng đạt; Chrome 1440px và 390px đạt. Script kiểm
form riêng sau HTMX swap, không tải form trong bảng, bảng trống và mô phỏng
tín hiệu lưu chi tiết để kiểm tải lại lưới/thống kê (không POST dữ liệu local).
Đã làm rõ bước tải lại thống kê sau thay `tbody`: node cũ rời DOM nên không
chỉ dựa vào `contains` trong `afterSwap`. Database giữ 20 dòng mới và 13 dòng cũ.

**Đã xong 09.09.2026 — cập nhật đăng nhập mẫu qua launcher:** chủ dự án yêu cầu
đổi mật khẩu chung của 12 tài khoản mẫu và để máy khác nhận khi mở KN JSC.
Đã đồng bộ mặc định seed, tài liệu và script kiểm thử; `KN JSC.bat` gọi
`cap_nhat_mat_khau_mau` sau khởi tạo. Lệnh chỉ chạy khi DEBUG bật, đánh dấu từng
tài khoản trong database để không đặt lại ở lần mở sau, giữ quyền và cờ buộc đổi
mật khẩu, không nạp dữ liệu nghiệp vụ. Sửa ghi chú cũ trong tài liệu: chạy lại
`du_lieu_mau` thực tế có đặt lại mật khẩu tài khoản đã có. Kiểm thử liên quan:
18 bài đạt; database local đã xác thực đủ 12 tài khoản, chạy lại cập nhật 0.
Máy khác cần kéo được nhánh có thay đổi này; chưa kiểm chứng trên máy thứ hai.

**Đã xong 09.09.2026 — Vận đơn theo CRM Tân (ADR-018):** đã bổ sung bảng
`van_don_moi`, luồng tạo ERP/CRM, chi tiết/thanh toán từng sản phẩm và bốn cách
thống kê. 25 bài kiểm mới và toàn bộ hồi quy đã đạt; migration xuôi/ngược đạt;
giao diện 1440px/390px, cuộn ngang và JavaScript đều đạt. Bảng cũ local giữ nguyên
222 dòng; bảng mới vẫn trống, không gieo đơn thử vào dữ liệu thật. Nghiệm thu người
dùng vẫn theo một đợt, không hỏi lại những lựa chọn đã chốt ở Q78–Q80.

Một chỗ duy nhất liệt kê **mọi thứ chưa xong**, cả việc của người dùng lẫn việc
của người viết mã. Chi tiết từng mục nằm ở các phần bên dưới; phần này là bản
tóm để không phải lục.

> Từ 07.09.2026 có thêm hai tệp nhìn theo việc: `backlog-kanban.md` (To do /
> In progress / Finished / Far Plan) và `test-log.md` (từng lỗi `TL-xx` kèm mức
> nghiêm trọng, chỗ sai, blocker, ảnh hưởng, nhánh). Tệp này vẫn là nơi ghi vì
> sao (Q, K, nhật ký).

> Cập nhật ngày 08.09.2026. Giai đoạn 7 phần E (ADR-010) đã vào `main` qua
> PR #4. Phần F (Bảng tính như KN Demo, ADR-011) và phần G (**KN CRM là app
> riêng**, trang chủ cây Bộ phận ▸ Quý ▸ Tháng, ADR-012) **đã vào `main` qua
> PR #5** tối 06.09; đợt chỉnh sửa KNERP đầu tiên — ô chọn có "Thêm mới…",
> danh tính người điền tự ghi, màu cột và viền ô (ADR-013) — vào qua PR #11;
> đợt thứ hai cùng ngày: **Bảng dữ liệu chỉ để xem với mọi bảng**, gỡ hẳn sửa
> ô ở KN ERP (ADR-014, Q62). **KN CRM đợt 2** (7J, ADR-015: khung sidebar theo
> Teeze, trang chủ tổng quan, Leader như Manager trong bộ phận, tạo bảng/nhập
> tệp/cấp quyền ngay trong KN CRM, logo tự vẽ) vào qua PR #19. **Kiểm tải KN CRM
> 100 nghìn khách / 100 người** (7K, ADR-016, K27) đã đo và sửa năm nút thắt,
> còn nợ chạy trên máy anh/chị. **MVP Nội bộ** — Tài liệu, Bảng tin, Công
> việc, Văn hoá, Tài nguyên (ADR-017) — xong ngày 07.09. Rà soát
> lại nhánh ngày 07.09: bốn commit A → D sửa 22 lỗi và điểm yếu, cải tiến giao
> diện, gọn mã dùng chung, thêm bài kiểm và tài liệu; chốt **Q75** (chỉ cấp trên
> ghi nhận cấp dưới), **Q76** (mọi người bán tranh hạng), **Q77** (đồng hạng).
> Nghiệm thu bấm tay theo `docs/07` vẫn chờ anh/chị.
> Mục D chỉ còn `AC-5.1`.

**Đang ở đâu:** xong Giai đoạn 0 tới 7. Nhập tệp Excel/CSV bốn bước có xem
trước và tiến độ, xuất kèm bộ lọc, tệp lớn chạy nền giữ 24 giờ (7A). Sao lưu
`pg_dump` 02:00 mỗi đêm giữ 30 bản, hỏng thì thư cho người vận hành, phục hồi
bằng `scripts/restore.sh` (7B). **Bảng tính vận đơn** theo tệp thật — lọc từng
cột, sửa ô có danh sách chọn, Lọc trùng, tô màu Hủy/Hoàn, mỗi sản phẩm một cột
— chạy ở dịch vụ `bangtinh` `localhost:8021/bang-tinh/`, Bảng dữ liệu chỉ xem
(7C, ADR-009). Kiểm thử chín tầng: thêm Playwright (bàn phím, hộp lọc, cột cố
định, 390px), 50.000 dòng dưới 2 giây, Locust 50 người tự chấm, ma trận 50 ô;
`docs/07` là kịch bản bấm tay (7D). **Bảng tính cho mọi bảng** (7E, ADR-010):
`/bang-tinh/<mã bảng>/` cho bảng nào trong phạm vi; viền ô như Excel, dòng
trống cuối lưới gõ là thành bản ghi; định dạng ô (đậm, nền, cỡ, căn) lưu vào
cơ sở dữ liệu; cột khoá bấm ⌕ là lọc; thanh lọc bên trái (chọn nhanh, khoảng
ngày, sản phẩm); thanh công cụ; thư mục chứa bảng. **Bảng tính như KN Demo**
(7F, ADR-011): khung tối viền vàng, thanh công thức có ô địa chỉ, số dòng,
chữ cột tới Z, chân trang có tab; kéo chọn vùng, dán từ Excel, kéo điền, hoàn
tác, menu chuột phải (xoá/khôi phục dòng, Manager chèn/xoá cột), 40 màu và
định dạng số, hộp lọc theo giá trị, tự cập nhật khi người khác sửa. **KN CRM
là app riêng** (7G, ADR-012): KN ERP không còn lưới, chỉ có mục KN CRM mở tab
mới sang dịch vụ 8021; trang chủ KN CRM là cây Bộ phận ▸ Quý ▸ Tháng ▸ bảng tự
sinh từ cột Ngày, bấm tháng là mở lưới lọc sẵn tháng đó (tháng là góc nhìn,
không tách bảng), quyền theo bảng như cũ. **Chỉnh sửa KNERP 06.09** (ADR-013): mọi cột Chọn một là ô chọn có "＋ Thêm mới…"
cho Manager ở biểu mẫu, báo cáo ngày và Lên đơn; sản phẩm lấy từ
danh mục, Manager thêm tại chỗ; trường Người bán tự ghi tên người điền; Bảng dữ
liệu có viền, tiêu đề xanh lá, màu cột và ngưỡng cảnh báo. **Bảng dữ liệu chỉ để
xem** với mọi bảng (7I, ADR-014): gỡ hẳn đường sửa ô ở KN ERP, sửa số liệu là
việc của KN CRM; luật 13 trong `CLAUDE.md`. **KN CRM đợt 2** (7J, ADR-015): KN CRM
có sidebar theo Teeze (avatar, Trang chủ, Bảng tính gập theo bộ phận, Nhập tệp,
Cấp quyền, Tác vụ nền, KN ERP), trang chủ là tổng quan theo phạm vi, cây tháng
thành mục Bảng tính ở `/thu-muc/`, lưới vẫn toàn màn hình và chỉ lưới có ← (về
thư mục, không về ERP); Leader được như Manager trong bộ phận mình; tạo bảng, sửa
cột kèm cấp quyền, nhập tệp chạy ngay trong KN CRM; logo tự vẽ và favicon.
**Nhóm Nội bộ, bản MVP** (9, ADR-017): Tài liệu chia mục theo bộ phận, Bảng tin có thích, bình
luận, ghim và thiệp sinh nhật tự động, Công việc theo phạm vi cấp bậc, Văn hoá
với ghi nhận một sao, xếp hạng doanh số quy VND và thưởng 5/3/1 sao ngày 1,
Tài nguyên chia mục BM/Via/Page.
**Kiểm tải KN CRM** (7K, ADR-016): 100.000 dòng vận đơn (2,95 triệu ô, 86 nghìn
số điện thoại) + bảng Sale có cột tính sẵn, đo một người rồi 100 người 5 phút trên
gunicorn; sửa theo số đo — ô lưới dựng bằng Python (638 → 154 ms), cột Trùng đếm
theo trang, `moi-nhat/` không đếm dòng, ghi hàng loạt `UPDATE … FROM VALUES`, tính
lại cột chạy nền theo lô (100.000 dòng: 153 s trong request → 19,6 s ở worker, 2 lô song song); gunicorn 3 tiến trình × 4 luồng;
`scripts/kiem-tai-kn-crm.*` chạy lại được trên máy có Docker. Sau khi hợp nhất:
133 tiêu chí, 119 trên 120 tiêu chí tự động có bài kiểm.

**Việc tiếp theo:** **nghiệm thu một đợt theo `docs/07`** — anh/chị bấm tay
từng vai, đánh ☑, gửi danh sách lỗi. Mọi thứ đã ở `main`, các nhánh cũ đã xoá:
máy nhà nháy đúp `KN JSC.bat` (hoặc `scripts\cap-nhat-local.bat main`), rồi bấm
**KN CRM** trên thanh bên (tab mới `localhost:8021/`). Rồi Giai đoạn 8: máy chủ, tên miền con cho KN
CRM, KN ERP dùng tốt trên điện thoại, đo tải trên máy chủ thật (chờ V1).
Với nhóm Nội bộ, bấm thử năm màn hình theo `docs/07` mục 3.1, 3.2, 3.4 và chốt
**N11** (tỉ giá), **N12** (năm giá trị văn hoá).

### A · Nghiệm thu — việc của anh/chị

**Chưa có gì được nghiệm thu.** Giai đoạn 0 tới 5 đều đã giao và toàn bộ bài
kiểm thử tự động đều đạt, nhưng anh/chị **chưa trực tiếp thử màn hình nào**. Phần
trăm trên `dashboard-tien-do.html` là tiến độ *đã làm*, không phải *đã nghiệm thu*.

**Mười tám việc làm được ngay bây giờ — kịch bản từng bước ở `docs/07`:**

| ☐ | Việc | Mã |
|---|---|---|
| ☐ | Thêm team mới, dùng ngay không khởi động lại | `AC-2.4` |
| ☐ | Mở trên điện thoại và máy tính bảng thật | `AC-10.4` |
| ☐ | Cài từ đầu trên máy sạch, chạy tới màn hình đăng nhập | `docs/04` mục 17.1 |
| ☐ | Ba vai trò đăng nhập, chạy trọn quy trình của mình | `docs/04` mục 17.2 |
| ☐ | Thử trên điện thoại và máy tính bảng thật | `docs/04` mục 17.5 |
| ☐ | Ngắt mạng giữa chừng, kiểm thông báo lỗi | `docs/04` mục 17.7 |
| ☐ | Xuất báo cáo tổng hợp, mở bằng Excel, đối chiếu số | `AC-5.6` · `docs/04` mục 17.4 |
| ☐ | Nhập tệp vận đơn thật (`docs/tham-khao/vandon-mau.xlsx`) qua Bảng dữ liệu → Nhập tệp | `docs/04` mục 17.3 |
| ☐ | Sao lưu rồi phục hồi trên máy thử: `scripts/backup.sh`, `scripts/restore.sh --toi-chac-chan` | `AC-10.5` · `docs/04` mục 17.6 |
| ☐ | 50 người đồng thời: `manage.py seed_perf` rồi Locust 1 phút, in ĐẠT | `AC-10.1` |
| ☐ | Bảng tính: cuộn ngang dọc, cột đầu và tiêu đề đứng yên | `AC-11.1` |
| ☐ | Bảng tính trên điện thoại và máy tính bảng thật | `AC-11.11` |
| ☐ | Bảng tính: mọi ô có viền, thanh công cụ đủ mục, ẩn cột nhớ được, thanh bên thu gọn được | `AC-11.18` |
| ☐ | Bảng tính đặt cạnh ảnh `docs/tham-khao/kn-demo/`: khung, thanh công thức, số dòng, chữ cột, cột trống, chân trang, ⛶; kéo chọn vùng, dán từ Excel, chuột phải | `AC-11.27` |
| ☐ | KN CRM: bấm mục trên thanh bên ERP mở tab mới; trang chủ cây Bộ phận ▸ Quý ▸ Tháng; bấm tháng → Mở → lưới lọc tháng → ← về đúng nhánh | `docs/07` mục 3.3 |
| ☐ | KN CRM đợt 2: trang chủ tổng quan có menu trái; Bảng tính → thư mục → Mở → lưới full → ← về thư mục; Leader tạo thư mục, cột, bảng, nhập tệp trong bộ phận mình; Nhập tệp và Cấp quyền trên sidebar | `AC-11.31` → `AC-11.34` · `docs/07` |
| ☐ | Nhóm Nội bộ — Bảng tin, Tài liệu, Công việc, Văn hoá, Tài nguyên — bấm thử theo vai | `docs/07` mục 3.1, 3.2, 3.4 |
| ☐ | Bảng tin trên điện thoại | `AC-13.6` |

**Một việc biết trước là chưa đạt:**

| Việc | Mã | Chờ |
|---|---|---|
| Gặp lỗi hiện thông báo tiếng Việt, không trang trắng | `AC-10.3` | Trang 404 và 500 chưa làm — **K9**, người dùng chốt chưa phải lúc |

### B · Câu hỏi chờ anh/chị quyết

Tám câu này **chặn việc thật**, không phải bàn cho vui:

| # | Câu hỏi | Chặn gì |
|---|---|---|
| **V4** | Mốc nào thì nghiệm thu toàn diện | Cả mục A ở trên |
| **V2** | Ai vận hành hằng ngày sau bàn giao | **K17** — có nên dựng chạy kiểm thử tự động không |
| **V1** | Máy chủ đặt ở đâu | Giai đoạn 8 |
| **N1** | Nộp báo cáo có bắt buộc đúng giờ không | **K16** — cột Trạng thái trên Lịch sử báo cáo |
| **N3** · **N6** | Chăm sóc khách hàng có trong phase 1 không | Biểu mẫu báo cáo CSKH ở Giai đoạn 4 |
| **N7** | Quản trị viên có phải thuộc một bộ phận không | BR-1 đang mâu thuẫn với mã |
| **N11** | Tỉ giá USD, CAD, PHP sang VND cho bảng xếp hạng doanh số — đang tạm 25.400 / 18.500 / 440 | Số trên bảng xếp hạng Văn hoá đúng hay sai; gộp PR #20 |
| **N12** | Năm giá trị văn hoá của công ty — đang tạm Tận tâm, Chính trực, Hợp tác, Sáng tạo, Trách nhiệm | Ghi nhận mang đúng tên giá trị; đổi sau khi có ghi nhận thật thì phải chuyển dữ liệu |

Còn sáu câu **H1 tới H6** cần hỏi trực tiếp người dùng cuối, không phải anh/chị
trả lời thay — xem mục 5. Hai câu **N9** và **N10** anh/chị đã chốt hoãn ngày
03.09.2026 — hỏi lại sau, không chặn gì.

### C · Lỗ hổng kỹ thuật đã biết

Không cái nào chặn triển khai. Xếp theo mức.

| # | Nội dung | Mức |
|---|---|---|
| **K9** | Chưa có trang lỗi 404 và 500 tiếng Việt — người dùng chốt 03.09.2026: chưa phải lúc | Trung bình |
| **K7** | Khoảng 60 định danh tiếng Việt trong mã Python, trái quy ước `CLAUDE.md` | Trung bình |
| **K13** | Cấp quyền đi hai cơ chế song song, xem lại có gộp được không | Trung bình |
| **K16** | Cột Trạng thái trên Lịch sử báo cáo — chờ **N1** | Trung bình |
| **K17** | Chưa có gì chạy kiểm thử tự động khi đẩy mã — chờ **V2** | Trung bình |
| **K23** | Bài Playwright hộp lọc cột: form gửi lần hai với ô trống ngay sau khi trang tải, chạy tay thì đúng — bài đánh dấu xfail | Trung bình |
| **K24** | Trang Bảng dữ liệu và Bảng tính trên 50.000 dòng tốn 12 lệnh truy vấn, hơn ngân sách 10 (Q2) hai lệnh; thời gian vẫn đạt 0,4 s và 1,1 s — bài hiệu năng đánh dấu xfail | Trung bình |
| **K19** | Bài Playwright và bài 50.000 dòng chỉ chạy trên máy phát triển, không chạy trong container `web` (không có Chromium, `pytest` mặc định không bỏ `cham` nhưng image không có trình duyệt) | Thấp |
| **K21** | Thư mục `storage/` là bind mount, container chạy uid 1000: máy Linux mà chủ thư mục khác thì nhập tệp và sao lưu hỏng — entrypoint chỉ cảnh báo, chưa tự sửa | Thấp |
| **K25** | Bảng tính (`crm`) chưa đọc `choice_registry.for_column`: ô Chọn một của bảng tự tạo ở đó vẫn là ô chữ, máy chủ vẫn chặn giá trị lạ — một dòng trong `grid_service.choice_list`, giao thread KN CRM | Thấp |
| **K26** | `GRID_ONLY_TABLES` và `is_grid_only` chỉ còn KN CRM dùng sau khi KN ERP gỡ hẳn sửa ô (ADR-014); ở dịch vụ `bangtinh` danh sách đã rỗng — thread KN CRM xem xét bỏ luôn | Thấp |
| **K30** | Tệp tài liệu ở `storage/tai-lieu/` không nằm trong `pg_dump` — phục hồi từ bản sao lưu là mất tệp nếu không chép thư mục đi kèm | Trung bình |
| **K31** | `docs/so-do-kien-truc.html` và sơ đồ trong `docs/kien-truc.md` chưa vẽ năm app Nội bộ | Thấp |
| **K29** | Bài Playwright `test_dong_trong_thanh_dong_that_va_loc_theo_o_khoa` (lưới KN CRM) đỏ cả trên `main` 345e1c0: bấm ⌕ ở ô Mã đơn không chuyển sang `?f_ma_don=…`; `test_ban_phim_di_chuyen_sua_va_huy` đỏ khi chạy đủ `cham`, chạy riêng xanh trên cả hai nhánh — thread KN CRM xem | Trung bình |
| **K28** | Ba lỗi giao diện KN CRM anh/chị thấy khi tự thử 07.09: gõ sai kiểu vào dòng trống thì báo "Đã lưu" mà lời báo lỗi bị giấu; hết phiên 60 phút thì trang đăng nhập rơi vào ô; tiêu đề bảng ngoài vận đơn màu vàng thay vì xanh | Sửa trên nhánh tách từ `main`, độc lập PR #21; ưu tiên trước mọi việc tối ưu (Q67) |
| **K8** | `ScopedModel` chưa có cột "người sửa" | Thấp |
| **K10** | Quy tắc Q3 chưa áp ở màn hình nào | Thấp |
| **K14** | Nhánh Staff trong `apply_scope` không đọc phạm vi cấp thêm | Thấp |

### D · Tiêu chí nghiệm thu chưa có bài kiểm

1 tiêu chí đánh dấu *Tự động* nhưng chưa viết được. Danh sách này nằm trong
`app/tests/test_truy_vet.py`, biến `HOAN`, và
**có bài kiểm bắt phải ghi lý do** — không giấu được.

| Tiêu chí | Chờ |
|---|---|
| `AC-5.1` | Bốn cách nhóm mới chạy ba — tab thị trường chờ **N9** |

### E · Màn hình chưa có

**Không còn.** Cả 10 màn hình của bản dựng ở `prototype/` đã có bản Django —
riêng Bảng tính làm theo tệp thật thay vì theo bản dựng (ADR-009). Chi tiết ở
mục 6.

---

## 1. Chờ quyết định

### 1.1. Kỹ thuật

| # | Nội dung | Mức | Nguồn |
|---|---|---|---|
| K7 | Đổi khoảng 60 định danh tiếng Việt trong mã Python sang tiếng Anh theo quy ước CLAUDE.md, gồm cả tên ràng buộc `team_unique_trong_bo_phan` đã vào PostgreSQL | Trung bình | Rà soát GĐ 1–2 |
| K8 | `docs/03` mục 2.1 đòi mọi bảng có cột "người sửa"; `ScopedModel` mới có `created_by`, chưa có `updated_by` | Thấp | Rà soát GĐ 1–2 |
| K9 | Chưa có trang lỗi 404 và 500 bằng tiếng Việt — NFR-6 mới đạt một phần. Người dùng chốt 03.09.2026: chưa phải lúc, để lại chờ xếp giai đoạn | Trung bình | Rà soát GĐ 1–2 |
| K10 | Quy tắc Q3 "chỉ lấy cột cần hiển thị" chưa áp ở màn hình nào | Thấp | Rà soát GĐ 1–2 |
| K13 | `core/scope.py _granted_scope` vẫn trả về rỗng. Cấp quyền theo bảng và biểu mẫu đi đường riêng ở `forms_builder/services/grant_service.py` — hai cơ chế song song, nên xem lại có gộp được không | Trung bình | GĐ 3B |
| K14 | Nhánh Staff trong `apply_scope` không đọc `department_ids` lẫn `team_ids`, nên cấp thêm cả một bộ phận cho Staff không có tác dụng | Thấp | GĐ 3B |
| K16 | Cột **Trạng thái** trên Lịch sử báo cáo (Đã nộp · Nộp muộn · Chưa nộp) chưa làm được vì chưa chốt **N1** — lịch nộp báo cáo có bắt buộc đúng giờ không. Không có hạn nộp thì không tính được thế nào là muộn | Trung bình | Đối chiếu 8010 |
| K17 | Chưa có gì chạy kiểm thử tự động khi đẩy mã lên kho. Người dùng chốt chưa dựng vì **V2** còn để ngỏ ai vận hành sau bàn giao | Trung bình | Kế hoạch kiểm thử |
| K23 | `tests/e2e/test_bang_tinh_ui.py::test_hop_loc_cot_doi_so_dong_va_url`: sau khi gửi form hộp lọc (URL đã có `f_…`), trang lại tải lần nữa với form trống (`?q=&loc_trong_…=`). Thử tay bằng Playwright script trên dịch vụ 8021 thì đúng một lần. Nghi vấn: HTMX xử lý lại `#hop-loc` hoặc `autofocus` của ô tìm; cần bắt `htmx:beforeRequest` để soi. Bài đánh dấu `xfail(strict=False)` ngày 03.09.2026 vì người dùng cần demo gấp | Trung bình | GĐ 7D |
| K24 | Bài `tests/test_hieu_nang.py` trên 50.000 dòng: thời gian đạt (0,4 s Bảng dữ liệu, 1,1 s Bảng tính có lọc) nhưng đếm 12 lệnh truy vấn, hơn ngân sách 10 của Q2 hai lệnh. Chưa soi được lệnh nào thừa (nghi: phiên + hồ sơ + phạm vi + bảng + cột + đếm + trang + quyền cấp + sổ danh sách nhân viên). Bài đánh dấu `xfail(strict=False)` | Trung bình | GĐ 7D |
| K19 | Bài kiểm trình duyệt thật (`tests/e2e/`, Playwright) và bài hiệu năng 50.000 dòng cần Chromium và thời gian, không chạy trong container `web` — tự bỏ qua kèm lý do. Chạy trên máy phát triển: `pip install -r requirements-dev.txt && playwright install chromium && pytest -m trinh_duyet` | Thấp | GĐ 7D |
| K21 | Thư mục `storage/` là bind mount, container chạy uid 1000. Trên máy Linux mà chủ thư mục là người khác thì nhập tệp và sao lưu hỏng vì không ghi được; `entrypoint.sh` mới chỉ cảnh báo, chưa tự sửa quyền | Thấp | GĐ 7B |
| K25 | Bảng tính (`crm`) chưa đọc `choice_registry.for_column` nên ô Chọn một của bảng tự tạo trên lưới vẫn là ô chữ (máy chủ vẫn chặn giá trị lạ qua `parse_value`). Sửa là một dòng trong `grid_service.choice_list` — thuộc thread KN CRM, không sửa ở đây. ~~K22~~ đóng ngày 06.09.2026 bằng `ColumnDef.options` và sổ theo nhãn (ADR-012) | Thấp | KNERP 06.09 |
| K26 | `GRID_ONLY_TABLES` và `grant_service.is_grid_only` chỉ còn KN CRM dùng (lưới báo chỉ xem; bảy tệp `crm/tests` dựa vào nó để kiểm chiều 403) sau khi KN ERP gỡ hẳn sửa ô (ADR-014); ở dịch vụ `bangtinh` danh sách đã rỗng nên thread KN CRM xem xét bỏ luôn — thread KNERP không đụng `app/crm/` | KNERP 06.09 |
| K30 | Tài liệu tải lên nằm ở `storage/tai-lieu/`, ngoài `pg_dump`: `scripts/backup.sh` chưa chép thư mục này, `restore.sh` cũng không; hiện `docs/05` B8 và B10 dặn chép tay cùng bản sao lưu. Tài liệu đã gỡ (xoá mềm) thì tệp vẫn nằm trên đĩa — tệp mồ côi, chưa có lệnh dọn | Trung bình | ADR-017 |
| K31 | Sơ đồ `docs/so-do-kien-truc.html` và hình vẽ trong `docs/kien-truc.md` chưa có năm app Nội bộ; bảng module ở `docs/kien-truc.md` và `docs/cau-truc-thu-muc.md` đã cập nhật chữ | Thấp | ADR-017 |
| K29 | `tests/e2e/test_bang_tinh_ui.py::test_dong_trong_thanh_dong_that_va_loc_theo_o_khoa` đỏ ngày 07.09.2026 khi chạy đủ `cham` — chạy riêng trên `main` 345e1c0 (worktree sạch, cơ sở dữ liệu kiểm thử riêng) cũng đỏ y hệt: sau khi gõ dòng trống thành dòng thật, bấm `.o-khoa-loc` ở ô Mã đơn `DH-1` không chuyển tới `?f_ma_don=DH-1…` trong 15 giây. Không phải do nhánh Nội bộ; cùng họ với K23 (hộp lọc gửi form hai lần). Cùng lần chạy đủ `cham` (28 đạt, 3 xfail), `test_ban_phim_di_chuyen_sua_va_huy` cũng đỏ (chờ ô Trạng thái VC đổi sau khi chọn danh sách quá 15 giây) nhưng chạy riêng thì xanh trên cả `main` lẫn nhánh Nội bộ — nghi do tải Chromium khi chạy nhiều bài liền, cần chờ có điều kiện thay vì đếm giây. Thread KN CRM xem, thread KNERP không đụng `app/crm/` | Trung bình | KNERP 07.09 |
| K27 | **Kiểm tải KN CRM 100 nghìn khách / 100 người** (ADR-016, AC-10.8): số "trước" trên máy ảo — lưới 638 ms (95% vẽ template), `?trung=1` 1,1 s, dán 500 ô 1,7 s, tính lại cột 100.000 dòng 153 s trong request, 100 người p95 11 s. Đã sửa: ô dựng bằng Python, cột Trùng đếm theo trang, `moi-nhat/` không COUNT, `DataRecord.bulk_save` (VALUES), tính lại nền theo lô chỉ ghi dòng đổi, mốc `moi-nhat/` theo cả bảng (Index Only Scan). **Còn nợ**: (1) chạy `scripts/kiem-tai-kn-crm.*` trên máy anh/chị và máy chủ thật rồi ghi số vào docs/06; (2) nếu máy thật vẫn đỏ thì mới đệm hộp lọc / thanh bên bằng Redis và `SESSION_ENGINE = cached_db` (đã cân nhắc, chưa làm); (3) khi có công thức từng ô (S10) đo lại với người dùng gõ công thức; (4) `tests/test_hieu_nang.py` (K24) vẫn xfail vì ngân sách 10 — sau K27 lưới còn 13 truy vấn, cân nhắc nâng ngân sách bài đó lên 13 | Trung | 07.09 |
| K28 | **Ba lỗi giao diện KN CRM đã xác nhận trên `main` (đợt 7F), anh/chị thấy khi tự thử 07.09**: (1) gõ sai kiểu vào dòng trống (chữ vào cột số) → máy chủ trả 400 đúng nhưng thanh trên báo **"✓ Đã lưu"** vì `bang-tinh.js` đặt `isError=false` cho 400, và lời báo `.o-loi-chu` có trong DOM mà bị CSS giấu (tuyệt đối dưới ô, bị cắt; `--critical-soft` không có trong khung lưới) — người dùng thấy "đã lưu" mà không có gì xảy ra; (2) phiên hết hạn sau 60 phút → HTMX dán cả trang đăng nhập vào ô, vì chưa xử lý `HX-Redirect`; (3) tiêu đề bảng không phải vận đơn màu vàng đồng (`#b8952b`) do tôi áp kiểu "sheet nhỏ" của demo cho mọi bảng, trong khi yêu cầu là tiêu đề xanh, ô trắng, chỉ ô cảnh báo mới vàng/đỏ. Sửa trên nhánh tách từ `main`, độc lập PR #21, có ảnh trước/sau và bài kiểm chiều "người dùng nhìn thấy lỗi" | Cao | 07.09 |

### 1.2. Nghiệp vụ

| # | Nội dung | Mức | Nguồn |
|---|---|---|---|
| N1 | Lịch nộp báo cáo có bắt buộc đúng giờ không — chỉ ghi nhận, nhắc nhở, hay chặn nộp muộn | Trung bình | Bàn phạm vi |
| N2 | Nhân viên vận đơn có tự thêm cột vào bảng không | Thấp | Đã hỏi, trả lời là không |
| N3 | Vai trò Chăm sóc khách hàng có thuộc phase 1 không | Trung bình | Tệp vận đơn có cột CSKH, phase 1 chưa có vai trò này |
| N6 | Chăm sóc khách hàng có trong phase 1 không — `README.md` xếp vào phạm vi, `docs/02` mục 17 để ngỏ. Trùng với N3 nhưng nay có thêm chứng cứ vênh giữa hai tài liệu | Cao | Rà soát GĐ 1–2 |
| N7 | BR-1 nói mỗi người thuộc đúng một bộ phận, nhưng Admin hiện không thuộc bộ phận nào. Giữ nguyên hay bắt Admin cũng phải có bộ phận | Trung bình | Rà soát GĐ 1–2 |
| N9 | Cách nhóm theo thị trường của báo cáo tổng hợp lấy số liệu từ đâu — cột Quốc gia bảng vận đơn chưa có nhãn ý nghĩa (ADR-007 để ngỏ); ba đường: thêm nhãn thứ tám kèm tệp chuyển đổi, lấy từ đơn hàng, hay nhóm cột JSON. Người dùng chốt 03.09.2026: **chưa quan trọng, hỏi lại sau**. Tab vẫn hiện kèm ghi chú — Q36 | Trung bình | Kế hoạch GĐ 6 |
| N10 | Có tách loại tiền VND và USD khi cộng doanh thu không — bảng động chưa lưu loại tiền theo dòng có nhãn (Q10 lưu kèm loại tiền chỉ áp cho đơn hàng). GĐ 6 chọn cách đơn giản nhất: cộng thẳng `val_revenue`, không kèm ký hiệu tiền. Hỏi lại cùng lúc với N9 | Thấp | Kế hoạch GĐ 6 |
| N11 | Tỉ giá cố định để quy doanh số về VND trên bảng xếp hạng Văn hoá: đang tạm USD 25.400, CAD 18.500, PHP 440 trong `EXCHANGE_RATES_VND` (`knjsc/settings/base.py`, đè bằng biến môi trường cùng tên, **bắt buộc** dạng `USD=25400,CAD=18500,PHP=440` — số nguyên, không dấu chấm hay phẩy; sai thì hệ thống không lên và nêu tên biến, rà soát 07.09). Anh/chị chốt số, và có cần đổi theo tháng không (S21) | Trung bình | ADR-017 |
| N12 | Danh sách giá trị văn hoá để ghi nhận: đang tạm năm giá trị Tận tâm, Chính trực, Hợp tác, Sáng tạo, Trách nhiệm (`culture/constants.py`). Đổi sau khi có ghi nhận thật thì cần tệp chuyển đổi dữ liệu | Trung bình | ADR-015 |

### 1.3. Vận hành

| # | Nội dung | Mức | Nguồn |
|---|---|---|---|
| V1 | Máy chủ đặt ở đâu — thuê ngoài hay đặt tại văn phòng | Trung bình | Chưa chốt |
| V2 | Ai chịu trách nhiệm vận hành hằng ngày sau khi bàn giao | Cao | Chưa chốt |
| V3 | Kênh gửi thông báo nếu làm tính năng nhắc nộp báo cáo | Thấp | Phụ thuộc N1 |
| V4 | **Mốc nào thì nghiệm thu toàn diện.** Hiện quá ít màn hình để đánh giá được giao diện và trải nghiệm — người dùng không nghiệm thu từng phần nữa, dồn về một đợt. Đề xuất mốc: hết Giai đoạn 5, khi một bộ phận làm trọn được việc hằng ngày. Chờ người dùng chốt | Cao | Người dùng, 29.08.2026 |
| V5 | **Kế hoạch kiểm thử và nghiệm thu chưa lập.** Người dùng chốt để sau, làm cùng lúc với đợt nghiệm thu ở V4. Nội dung cần có: ai kiểm, kiểm trên dữ liệu nào, bao lâu, tiêu chí nào coi là đạt, và xử lý thế nào khi không đạt | Cao | Người dùng, 29.08.2026 |

---

## 2. Đã quyết định

### Feedback KN CRM — phân công, lọc và xuất Vận đơn mới (09.09.2026)

Chủ dự án duyệt triển khai đề xuất 3–6 cho `van_don_moi`. Đã hoàn tất trên
nhánh `codex/sua-feedback`, chưa commit/push trong tác vụ này. Username là mã
nhân viên; Leader/Manager Vận đơn và Admin phân công, không suy người từ tên.
Quyền xem mới không tự cấp quyền sửa CSKH; bảo vệ cột phân công khỏi nhập/dán.
Giữ thống kê và Lên đơn riêng, Excel một đơn một dòng; kiểm lại quyền file nền.
Các test cũ được cập nhật bước phân công rõ ràng trước khi nhân viên xử lý.
Quyết định, giới hạn và cách nghiệm thu ở ADR-020, AC-20.1 đến AC-20.7.
Không làm H7, nhắc việc, AI, chuyển bảng cũ hoặc thay thư viện grid.

| # | Nội dung | Quyết định | Ngày |
|---|---|---|---|
| Q1 | Đơn hàng chảy sang bảng vận đơn theo chiều nào | Một chiều cho phase 1 | (điền) |
| Q2 | Có làm quản lý tài nguyên và kho thông tin đăng nhập không | Không làm — **sửa bởi Q68** ngày 06.09.2026: có kho tài nguyên bản MVP, vẫn không có kho thông tin đăng nhập | (điền) |
| Q3 | Mảng nhân sự, kế toán, kho | Để giai đoạn sau | (điền) |
| Q4 | Có tích hợp với phần mềm kế toán không | Không, ít nhất trong phase 1 | (điền) |
| Q5 | Ứng dụng di động | Không làm bản cài đặt, chỉ cần giao diện dùng được trên điện thoại | (điền) |
| Q6 | Trợ lý AI | Không làm trong phase 1 | (điền) |
| Q7 | Khung ứng dụng | Django 5.2, PostgreSQL 16, HTMX, Celery với Redis, Docker Compose — ADR-005 | 28.08.2026 |
| Q8 | Danh sách module trong `app/` | Bảy module: core, org, forms_builder, reports, orders, dashboard, crm — **sửa bởi Q74**: mười hai module | 28.08.2026 |
| Q9 | Quản trị viên trong mô hình bộ phận × cấp bậc | Cấp bậc thứ tư tên Admin, phạm vi mọi bộ phận, có tất cả các quyền | 28.08.2026 |
| Q10 | Loại tiền tệ | Phase 1 dùng VND và USD, mỗi số tiền lưu kèm loại tiền, không quy đổi khi lưu | 28.08.2026 |
| Q11 | Mức độ công thức trên bảng — K1, FR-7.8 | Bảng dữ liệu chỉ có cột tính sẵn; gõ công thức tự do tách sang màn hình Bảng tính, không ghi ngược — ADR-006 | 29.08.2026 |
| Q12 | Bảng đích khi tạo biểu mẫu — K2 | Luôn chọn bảng có sẵn, không tự sinh bảng mới — ADR-007 | 29.08.2026 |
| Q13 | Bảy nhãn ý nghĩa — K3 và N8 | Theo `docs/03` mục 2.5: Ngày, Khách hàng, Số điện thoại, Doanh thu, Người bán, Sản phẩm, Trạng thái — ADR-007 | 29.08.2026 |
| Q14 | Chia Giai đoạn 3 làm mấy đợt | Hai đợt có điểm dừng: 3A bảng dữ liệu, 3B biểu mẫu và phân quyền theo bảng | 29.08.2026 |
| Q15 | Màn hình Bảng tính xếp vào giai đoạn nào | Giai đoạn 7, làm chung với nhập xuất Excel | 29.08.2026 |
| Q16 | Có làm màn hình Ma trận phân quyền không | Có, bản chỉ đọc sinh thẳng từ mã nguồn — làm trong 3A | 29.08.2026 |
| Q17 | Ai thấy định nghĩa bảng | Cả bộ phận, mọi cấp bậc. Phạm vi theo cấp bậc chỉ áp cho bản ghi trong bảng | 29.08.2026 |
| Q18 | Cấu trúc trường biểu mẫu | Bốn bảng đúng `docs/03` mục 2.2: FieldDef, FormDef, FormField, FormTableLink | 29.08.2026 |
| Q19 | Mức chi tiết của phân quyền — FR-8.4 | Cấp thêm cho từng người hoặc từng team, cộng vào phạm vi cấp bậc | 29.08.2026 |
| Q20 | K11 và K12 | Đã xong ở 3B: màn hình điền biểu mẫu, và quyền sửa ô tính qua `grant_service.can_edit_record` | 29.08.2026 |
| Q21 | Nội dung báo cáo hằng ngày lưu ở đâu | Trong `DataRecord` do biểu mẫu sinh ra; `DailyReport` chỉ giữ ai nộp, ngày nào, lúc nào — ADR-008 | 29.08.2026 |
| Q22 | Dựng vỏ hết màn hình trước hay làm từng giai đoạn | Làm từng giai đoạn, mỗi màn hình chạy thật rồi mới sang màn tiếp | 29.08.2026 |
| Q23 | Thị trường thật — N5 | Ba nước: Hoa Kỳ, Canada, Philippines. Ô chọn cố định, khai một chỗ trong `orders/constants.py` | 29.08.2026 |
| Q24 | Sáu trường không có trong bảng vận đơn — N4 | Thêm sáu cột vào bảng vận đơn. Vận đơn cần liên lạc được với khách khi giao hỏng | 29.08.2026 |
| Q25 | BLACK LIST — G1 | Cờ đánh dấu trên khách hàng kèm lý do. Lên đơn cho khách trong danh sách đen thì **cảnh báo, không chặn** — chưa có yêu cầu nào cho chặn | 29.08.2026 |
| Q26 | Trạng thái vận chuyển và thanh toán — G2 | Bộ phận Vận đơn sửa thẳng trên bảng, dùng lại chức năng sửa ô của Giai đoạn 3. Không viết màn hình riêng | 29.08.2026 |
| Q27 | Dòng trên bảng động thuộc bộ phận nào | Bộ phận **sở hữu bảng**, không phải bộ phận người ghi. Thêm cờ `is_shared` cho bảng là hàng đợi việc chung | 29.08.2026 |
| Q28 | Ô "Có chỉ mục" trong bản dựng — K15 | Bỏ. Chỉ mục suy ra từ nhãn ý nghĩa, không phải lựa chọn của người dùng — ADR-001 | 29.08.2026 |
| Q29 | Cột "Chỉ mục GIN" trên danh sách bảng | Bỏ. Mọi bảng động đều có chỉ mục GIN trên cột JSON, hiện lên không nói thêm được gì | 29.08.2026 |
| Q30 | Ngưỡng bao phủ kiểm thử — K5 | Đo bằng `pytest-cov` để biết chỗ hổng, **không đặt ngưỡng chặn**. Ngưỡng đẻ ra bài kiểm viết cho đủ số | 29.08.2026 |
| Q31 | Kiểm giao diện tự động tới đâu | Ở mức HTML, không thêm thư viện trình duyệt. Phần cần trình duyệt thật thì bấm tay | 29.08.2026 |
| Q32 | Ai vào được màn hình Lên đơn | Chỉ bộ phận Sale, theo ma trận kiểm chéo `docs/04` mục 3. Thêm bộ lọc bộ phận cho `NavItem` và `assert_departments` | 29.08.2026 |
| Q33 | Ai vào được màn hình Quản lý biểu mẫu | Manager trở lên. Nhân viên điền biểu mẫu qua màn hình Nộp báo cáo ngày | 29.08.2026 |
| Q34 | Điều hướng sau đăng nhập theo bộ phận — K18, FR-1.6, `AC-1.7` | **Bỏ.** Tất cả đăng nhập đều vào trang tổng quan chung, không nhảy thẳng vào chỗ làm việc — phân quyền đã ẩn các tính năng ngoài phận sự nên không cần | 03.09.2026 |
| Q35 | Nguồn số liệu của báo cáo tổng hợp | Chọn đúng **một** bảng trong phạm vi quyền qua ô "Nguồn số liệu" (thay ô "Bộ phận" của bản dựng). Không cộng gộp nhiều bảng — doanh số trên Báo cáo Marketing và Bảng vận đơn ghi cùng một khoản bán, cộng lẫn là đếm trùng | 03.09.2026 |
| Q36 | Cách nhóm theo thị trường | **Hoãn** — người dùng chốt chưa quan trọng, hỏi lại sau (N9). Màn hình giữ tab Theo thị trường kèm ghi chú chờ chốt nguồn, không có bảng số; `AC-5.1` giữ trong danh sách hoãn | 03.09.2026 |
| Q37 | Bảng tính lưu dữ liệu ở đâu | **Dùng chung một cơ sở dữ liệu** — lưới đọc ghi thẳng dòng của bảng vận đơn, không có bảng riêng, không đồng bộ hai chiều — ADR-009 | 03.09.2026 |
| Q38 | Bảng tính chạy ở đâu | **Dịch vụ riêng trong cùng kho mã** — container `bangtinh` cùng image, settings `knjsc.settings.bangtinh`, cổng 8021, tương lai subdomain chia sẻ phiên đăng nhập — ADR-009 | 03.09.2026 |
| Q39 | Số lượng sản phẩm trên bảng vận đơn | **Mỗi sản phẩm một cột** như tệp thật (`sl_<mã sản phẩm>`), tự sinh từ danh mục sản phẩm đang bán, lên đơn điền tự động | 03.09.2026 |
| Q40 | Trạng thái vận đơn và thanh toán | **Đúng danh sách của tệp thật**: tám trạng thái vận đơn, ba trạng thái thanh toán; nhãn cũ đổi bằng tệp chuyển đổi `orders/0002` có chiều ngược | 03.09.2026 |
| Q41 | Tiền tệ | Thêm **CAD** và **PHP** — tệp thật ghi "Giá tiền(CAD)"; ba thị trường ba đồng tiền cộng VND | 03.09.2026 |
| Q42 | Bảng vận đơn sửa ở đâu — sửa Q26 | **Chỉ xem ở Bảng dữ liệu, sửa ở Bảng tính.** `GRID_ONLY_TABLES` trong settings, kiểm ở máy chủ; dịch vụ `bangtinh` để rỗng — AC-11.7 | 03.09.2026 |
| Q43 | Tệp vận đơn thật | **Ẩn danh hoá rồi đưa vào kho** — `scripts/an-danh-vandon.py` → `docs/tham-khao/vandon-mau.xlsx`; bản gốc chỉ ở `storage/`, không vào git. Là thước đo của AC-11.9 | 03.09.2026 |
| Q44 | Công cụ kiểm thử trình duyệt và tải — sửa Q31 | **Thêm Playwright và Locust, chỉ trong `requirements-dev.txt`**, không vào image chạy thật. K6 đóng ngày 03.09.2026 khi `tests/perf/locustfile.py` chạy được và tự chấm | 03.09.2026 |
| Q45 | Ai được nhập tệp Excel vào bảng; sao lưu ở giai đoạn nào | Quản lý trở lên của bộ phận sở hữu bảng hoặc người được cấp quyền **Sửa**; sao lưu thuộc **Giai đoạn 7**; thứ tự làm 7A → 7B → 7C → 7D | 03.09.2026 |
| Q46 | Bảng tính áp cho bảng nào — sửa ADR-009 mục 1 | **Mọi bảng trong phạm vi quyền** ở `/bang-tinh/<mã>/`; `/bang-tinh/` mặc định mở bảng vận đơn; ngoài phạm vi 404 như Bảng dữ liệu; phần riêng của vận đơn bật theo `is_waybill`; luật hai dịch vụ giữ nguyên — ADR-010 | 04.09.2026 |
| Q47 | Ai thêm được dòng thẳng trên lưới (dòng trống cuối lưới) | Cùng bộ phận sở hữu bảng (mọi cấp), hoặc cấp quyền Sửa, hoặc Admin — `can_create_record`; bảng chỉ xem ở dịch vụ này thì không — AC-11.14 | 04.09.2026 |
| Q48 | Cột khoá | `ColumnDef.is_key`, mỗi bảng một cột, Manager đặt trong Sửa cột, bảng vận đơn lấy Mã đơn; ô cột khoá có nút ⌕ lọc theo giá trị — AC-11.16 | 04.09.2026 |
| Q49 | Định dạng ô lưu ở đâu — sửa ADR-002 phần "Mất gì" | **Cơ sở dữ liệu** (`DataRecord.style`), mọi người cùng thấy; sổ giá trị đóng (đậm, sáu màu nền, cỡ 10–18, căn lề), không nhận CSS tự do; quyền bằng quyền sửa ô — AC-11.15, ADR-010 | 04.09.2026 |
| Q50 | "Tạo folder" nghĩa là gì | **Thư mục chứa bảng**, phẳng, thuộc bộ phận, model ở `forms_builder` (không ở `crm` vì ADR-004); Manager bộ phận quản lý; chỉ sắp xếp thanh bên, không ảnh hưởng phạm vi — AC-11.17 | 04.09.2026 |
| Q51 | Bảng tính nhìn và thao tác thế nào | **Y hệt bảng tính KN Demo** về cách nhìn và cách thao tác (ảnh `docs/tham-khao/kn-demo/`), trên nền dữ liệu KNJSC giữ nguyên; làm trên nhánh riêng `claude/bang-tinh-nhu-kn-demo`; bảng "không làm" ghi ở ADR-011 (công thức, tab là trang, chèn hàng giữa, chiều cao dòng, cột trống gõ được) | 04.09.2026 |
| Q52 | Ai xoá được dòng trên lưới | **Đúng bằng quyền sửa dòng** — `grant_service.can_delete_record` gọi `can_edit_record`, đặt tên riêng để sau này tách được mà không phải đổi mô hình quyền; xoá là xoá mềm, Ctrl+Z khôi phục — AC-11.21, ADR-011 | 04.09.2026 |
| Q53 | Bấm một lần vào ô là gì | **Chọn ô**, không mở sửa; bấm đúp, Enter, F2 hoặc gõ chữ mới sửa — như demo và Excel, không thế thì không kéo chọn vùng được; thay cách "bấm ô là sửa" của ADR-009 — AC-11.25, ADR-011 | 04.09.2026 |
| Q54 | Bảng tính đặt ở đâu so với ERP, có làm app không | **KN CRM là app riêng trong hệ sinh thái**: dịch vụ `bangtinh` 8021, tên miền con, mở tab mới từ ERP, **cùng kho mã cùng cơ sở dữ liệu** (cách B trong bảng so sánh A/B/C); KN ERP không còn lưới. **Không** làm app cài đặt (native, PWA) — quá đắt; cái cần trên điện thoại là KN ERP (Giai đoạn 8) — AC-11.30, ADR-012 | 06.09.2026 |
| Q55 | "Thư mục Quý → Tháng → file vận đơn" nghĩa là gì | **Tháng là góc nhìn trên một bảng**, cây tự sinh từ cột Ngày; bấm tháng là mở lưới lọc sẵn. Không tách bảng theo tháng (Lên đơn ghi vào một bảng, Lọc trùng và mua lại lần đếm cả lịch sử) — AC-11.28, AC-11.29, ADR-012 | 06.09.2026 |
| Q56 | Quyền trong KN CRM cấp ở mức nào | **Theo bảng như hiện có** (Manager cấp Xem/Sửa từng bảng ở KN ERP); cây chỉ hiện thứ được xem; không thêm quyền theo thư mục hay theo tháng — ADR-012 | 06.09.2026 |
| Q58 | Danh sách chọn của cột Chọn một lấy từ đâu, ai thêm — K22 | **Ba tầng, một chỗ phân giải** (`choice_registry.for_column`): sổ (bảng, cột) của crm → nhãn ý nghĩa (Sản phẩm = danh mục sản phẩm, chặt; Người bán = nhân sự bộ phận, gợi ý) → `ColumnDef.options` (chặt). **Manager quản lý, Staff chỉ chọn**; cột chưa có danh sách không nhận giá trị nào; bảng vận đơn giữ sổ crm — ADR-013, AC-8.7, AC-8.8 | 06.09.2026 |
| Q59 | Danh tính người điền ghi dạng gì, ép ở đâu | **Họ tên trong hồ sơ, không có thì tên đăng nhập** (`core.identity.display_name`, cùng luật với bảng vận đơn); ép ở tầng dịch vụ `form_service.fill`, không tin POST; chỉ áp cho điền biểu mẫu và nộp báo cáo, nhập tệp và lên đơn giữ nguyên — AC-4.6 | 06.09.2026 |
| Q60 | Tô màu chỉ số quan trọng trên Bảng dữ liệu theo cách nào | **Màu cột** (vàng, đỏ, xanh lá, xanh dương) tô tiêu đề lẫn ô, cộng **ngưỡng cảnh báo** cho cột số (đỏ khi lớn hơn / nhỏ hơn X, còn lại xanh lá); tiêu đề mặc định **xanh lá cố định**; là thuộc tính của cột, khác định dạng từng ô của ADR-010; viền chỉ ở bảng mang lớp `bang-luoi` — ADR-013, AC-8.9, AC-8.10 | 06.09.2026 |
| Q62 | Bảng dữ liệu ở KN ERP có sửa ô không — sửa Q26, Q42 và ADR-010 mục 1 | **Không, với mọi bảng.** Bảng dữ liệu chỉ để xem; sửa số liệu là việc của KN CRM. Gỡ hẳn view `bang_sua_o`, `_o.html`, `choice_service.attach_lists`, khối script sửa ô; nút "Mở trong KN CRM" và dòng báo hiện với mọi bảng; `GRID_ONLY_TABLES` chỉ còn KN CRM dùng (K26) — ADR-014, AC-7.4, AC-11.7, luật 13 `CLAUDE.md` | 06.09.2026 |
| Q61 | Ai thêm sản phẩm, thêm ở đâu | **Manager bất kỳ bộ phận (hoặc Admin) thêm ngay tại ô chọn** — trên biểu mẫu, ô bảng và Lên đơn; mã tự sinh từ tên, đồng bộ cột `sl_` trên bảng vận đơn ngay. Màn hình quản lý sản phẩm đầy đủ để sau (S11) — AC-6.9 | 06.09.2026 |
| Q63 | KN CRM cần trang chủ và menu trái không, lưới có sidebar không | **Có khung riêng như một app**: sidebar theo Teeze (ảnh anh/chị gửi), trang chủ là tổng quan như ERP, cây tháng là mục **Bảng tính** ở `/thu-muc/`; **lưới vẫn full như Excel**, chỉ khi chủ động quay về mới thấy menu trái; chỉ lưới có ← và nó về thư mục, không về ERP — AC-11.31, AC-11.32, ADR-015 | 07.09.2026 |
| Q64 | Leader được làm gì trong KN CRM | **Như Manager trong bộ phận mình**: thư mục, cột, tạo bảng, nhập tệp, xuất, sửa/xoá dòng người khác (một hàm `_quan_ly_bo_phan`); cấp quyền cho người khác vẫn Manager; phạm vi xem không đổi — AC-11.33, ADR-015 | 07.09.2026 |
| Q65 | Nhập tệp, tạo bảng, cấp quyền có phải bật sang ERP không | **Không** — gắn view forms_builder vào 8021, template kế thừa khung KN CRM qua biến `khung`; mục Nhập tệp (Leader+) và Cấp quyền (Manager) trên sidebar — AC-11.34, ADR-015 | 07.09.2026 |
| Q66 | Kiểm thử toàn diện KN CRM ở cỡ hàng triệu ô, 100 nghìn khách, 100 người cùng lúc thì đo cái gì, ngưỡng nào | **Không bấm giao diện** (không Playwright): mô phỏng HTTP như trình duyệt, 100 người di qua di lại và **lập công thức = cột tính sẵn** (S10 chưa có); chạy máy ảo trước, đóng gói `scripts/kiem-tai-kn-crm.*` cho máy anh/chị; ngưỡng **"như Excel trên máy thường"**: p95 mở/lọc/chuyển trang ≤ 1 s, lưu ô ≤ 0,5 s, 0 lỗi, tính lại cột 100.000 dòng ≤ 30 s không chặn người khác — ADR-016 | 07.09.2026 |
| Q67 | Sau kiểm tải, có viết lại lưới theo hướng tối ưu hơn (JSON + JS vẽ ô, SSE, cột tính trong DB) không | **Chưa** — "giờ chưa phải lúc tối ưu". Ghi thành S13, S14, S15 để xét sau; trước mắt sửa lỗi người dùng nhìn thấy (K28) và nghiệm thu bấm tay theo `docs/07` | 07.09.2026 |
| Q68 | Có làm quản lý tài nguyên không — sửa Q2 | **Có, bản MVP**: danh sách chia mục (BM, Via, Page, Tài khoản QC, SIM), Manager trở lên thêm mục và thêm, sửa, gỡ tài nguyên; mọi người xem; **không lưu mật khẩu** (ghi chú bị chặn từ khoá bí mật); chưa có sổ bàn giao (S16) — ADR-017, FR-13.x | 06.09.2026 |
| Q69 | Tài nguyên có phạm vi theo bộ phận không | **Không** — danh mục dùng chung toàn công ty, cột Bộ phận chỉ ghi nhớ ai đang dùng — ADR-017 | 06.09.2026 |
| Q70 | Bảng tin ai đăng, ai ghim, có thiệp sinh nhật không | Mọi người đăng, bình luận, thích; Manager và Admin ghim và gỡ bài bất kỳ, tác giả gỡ bài mình; thiệp sinh nhật tự động 06:00 từ ngày sinh trong hồ sơ (thêm cột `birthday`, org 0003) — ADR-017, FR-10.x | 06.09.2026 |
| Q71 | Bảng xếp hạng doanh số đọc số liệu từ đâu, ai xem | Từ **Đơn hàng** toàn công ty (ngoại lệ phạm vi có chủ ý, ghi trong docstring), tháng này theo người bán, quy về VND bằng `EXCHANGE_RATES_VND` cố định (N11); cả công ty xem hạng, số đơn, tổng — không thấy chi tiết đơn — ADR-017 mục 5 | 06.09.2026 |
| Q72 | Sao tính thế nào | **Một ghi nhận = một sao**; ngày 1 hằng tháng ba người dẫn đầu tháng trước nhận **5, 3, 1** sao, ràng buộc (người, kỳ, nguồn) nên chạy lại không nhân đôi; sổ ghi nhận và sổ sao chỉ ghi thêm, không sửa xoá (S19) — ADR-017 | 06.09.2026 |
| Q73 | Tài liệu chia mục thế nào, ai tải lên | Mục theo bộ phận hoặc toàn công ty; Manager tải lên mục bộ phận mình, Admin cả mục chung; PDF, Word, Excel, CSV, ảnh hoặc chỉ liên kết; tệp ở `storage/tai-lieu/`, tải về qua view kiểm quyền — ADR-017, FR-9.x | 06.09.2026 |
| Q74 | Danh sách module trong `app/` — sửa Q8 | **Mười hai module**: bảy cũ cộng `documents`, `feed`, `taskboard`, `culture`, `resources`; phụ thuộc một chiều `feed → culture → orders`, không ai import `feed` — ADR-017 | 06.09.2026 |
| Q75 | Ai ghi nhận văn hoá được ai — sửa FR-12.1, AC-15.1, ADR-017 mục 5 | **Chỉ cấp trên ghi nhận cấp dưới**: Leader ghi nhận nhân viên team mình, Manager ghi nhận Leader và nhân viên bộ phận, Admin ghi nhận mọi người; nhân viên chỉ xem, không có form; không đặt trần số ghi nhận mỗi ngày (anh/chị chọn cách này thay cho trần). Dịch vụ kiểm bằng `UserProfile.objects.in_scope(giver)` và cấp bậc thấp hơn | 07.09.2026 |
| Q76 | Ai tranh hạng doanh số | **Mọi người bán**, kể cả Leader, Manager, Admin có đơn — không loại quản lý khỏi bảng | 07.09.2026 |
| Q77 | Hoà điểm trên bảng xếp hạng — sửa Q72 | **Đồng hạng, cùng nhận sao** kiểu thi đấu 1, 1, 3: bằng tổng VND và bằng số đơn thì cùng hạng, cùng sao thưởng, người kế tiếp nhảy hạng | 07.09.2026 |
| Q78 | Sheet Vận đơn của CRM Tân là mẫu hiện hành | Tạo **Vận đơn** mới `van_don_moi` trống; đổi `van_don` thành **Vận đơn cũ**, giữ dữ liệu, liên kết, quyền; tất cả đơn mới từ ERP/CRM vào bảng mới; sao quyền riêng đang hiệu lực một lần — ADR-018 | 08.09.2026 |
| Q79 | Bố cục và chi tiết thanh toán | Ba khu cùng trang, giữ thao tác lưới; một đơn một dòng với chi tiết sản phẩm riêng; tiền thu nhập từng sản phẩm, không phân bổ tỷ lệ, không sửa ERP; PTTT tách hai trường, thêm Loại tiền, chưa làm Blacklist/lịch sử nhiều lần thu | 08.09.2026 |
| Q80 | Nguồn và cách thống kê vận đơn mới | Lấy bản sao hiện tại của bảng mới, toàn bộ bộ lọc/quyền, tách loại tiền, nhóm SALE/CSKH/sản phẩm/Quốc gia, distinct đơn; nhập tệp cần chi tiết xác định, không suy đoán từ tổng — ADR-018 | 08.09.2026 |

---

## 3. Ý tưởng cho giai đoạn sau

Những thứ đáng làm nhưng chưa tới lượt.

| # | Ý tưởng | Ghi chú |
|---|---|---|
| S1 | Đồng bộ hai chiều giữa đơn hàng và bảng vận đơn | Cần xử lý xung đột khi hai bên cùng sửa |
| S2 | Cho phép cấp trên chia sẻ quyền xem cho cấp dưới | Khung phạm vi đã thiết kế sẵn chỗ mở rộng |
| S3 | Thông báo chủ động khi có việc cần xử lý | Cần tầng dịch vụ tách khỏi giao diện |
| S4 | Kênh báo sự cố cho nhân viên không có tài khoản | Biểu mẫu công khai, người quản lý xử lý |
| S5 | Bảng tổng hợp dạng xoay chiều | Chưa rõ nhu cầu thật |
| S6 | Nhiều người cùng sửa một bảng theo thời gian thực | Phức tạp, cần đánh giá lại nhu cầu |
| S7 | Thư mục lồng nhau trên Bảng tính | Chưa ai cần; thêm sau chỉ là FK `parent` trên `Folder` — ADR-010 |
| S8 | Xuất Excel mang theo định dạng ô (đậm, màu nền) | `export_service.build_workbook` chưa đọc `DataRecord.style`; làm khi có người hỏi |
| S9 | Kéo đổi chiều cao dòng trên Bảng tính | Dòng đổi chỗ khi sắp xếp và phân trang nên chiều cao theo chỉ số dòng vô nghĩa; nếu cần thì lưu theo bản ghi như `style` — ADR-011 |
| S10 | Công thức gõ ở thanh công thức của Bảng tính | Ô `fx` đã có, gõ `=` đang báo chưa hỗ trợ; chờ "cách thứ ba" người dùng nói tới sau ADR-006; khi có thì cắm vào đúng chỗ này — ADR-011 |
| S11 | Màn hình quản lý sản phẩm đầy đủ: sửa tên, nhóm, ngừng bán | Hiện chỉ thêm nhanh tại ô chọn (Q61); ngừng bán mới làm được qua dòng lệnh. |
| S12 | Xuất Excel Bảng dữ liệu mang theo màu cột và ô cảnh báo | Cùng chỗ với S8 |
| S13 | **Lưới KN CRM trả JSON, trình duyệt tự vẽ ô** (JS thuần, không thêm khung) thay cho máy chủ dựng HTML 3.900 ô mỗi trang (~300 KB): trang chỉ ~20 KB, cuộn ảo không cần phân trang, lọc/sắp xếp/dán chỉ đổi số liệu | Anh/chị chốt 07.09: **giờ chưa phải lúc tối ưu** (Q67). Sau K27 lưới đã 154 ms và 100 người dưới 1 giây; viết lại là ba tới năm ngày không có tính năng mới. Xét lại khi máy thật đo đỏ hoặc khi làm S10 |
| S14 | Máy chủ đẩy sự kiện (SSE) cho lưới thay vì 100 tab hỏi `moi-nhat/` mỗi 8 giây rồi tải lại cả `tbody`; chỉ gửi đúng ô vừa đổi | Cần một kết nối mở cho mỗi tab, chưa có trong hạ tầng; cùng thời điểm với S13 (Q67) |
| S15 | Cột tính sẵn để Postgres tính (cột sinh tự động hoặc một lệnh UPDATE trong DB) thay cho Python đọc rồi ghi lại JSON qua chỉ mục GIN (100.000 dòng 19,6 s) | Đụng cấu trúc dữ liệu nền tảng, phải hỏi trước; chưa cần khi tính lại đã chạy nền dưới 30 giây (Q67) |
| S16 | Sổ bàn giao tài nguyên: ai nhận, ai trả, khi nào | MVP chỉ có cột Người giữ; lịch sử đổi người giữ đang nằm trong Nhật ký — Q68 |
| S17 | Ảnh trong bài Bảng tin và ảnh đại diện | MVP chỉ chữ; avatar là chữ cái đầu — ADR-017 |
| S18 | Bảng kanban kéo thả cho Công việc, việc con, đính kèm | MVP là danh sách với nút đổi trạng thái — ADR-017 |
| S19 | Sửa hoặc thu hồi ghi nhận | Hiện là sổ cái chỉ ghi thêm để sao không lệch (Q72); nếu làm thì thu hồi phải trừ sao kèm nhật ký |
| S20 | Thông báo khi được giao việc, được ghi nhận, được bình luận | Cần chuông trên thanh trên hoặc thư — trùng hướng S3 |
| S21 | Tỉ giá theo ngày lên đơn | Hiện quy đổi bằng bảng cố định tại lúc tính, nên đổi `EXCHANGE_RATES_VND` giữa tháng là hạng đổi ngược thời gian; đã ghi tỉ giá vào nhật ký thưởng (rà soát 07.09). Muốn đúng hẳn thì lưu tỉ giá theo ngày trên từng đơn — N11, ADR-017 |

---

## 4. Rủi ro đã nhận diện

| # | Rủi ro | Mức ảnh hưởng | Cách giảm |
|---|---|---|---|
| R1 | Dữ liệu cũ dần vì phụ thuộc người dùng cập nhật | Cao | Nhắc nhở, và làm sao cho nhập liệu nhanh hơn cách hiện tại |
| R2 | Chỉ một người biết vận hành hệ thống | Cao | Sổ tay vận hành đủ chi tiết để người khác tiếp nhận |
| R3 | Phạm vi phình ra trong quá trình làm | Trung bình | Danh sách ngoài phạm vi trong tài liệu, thay đổi phải được duyệt |
| R4 | Bảng do người dùng tự tạo làm chậm truy vấn | Trung bình | Tách cột có nhãn ý nghĩa ra cột riêng có chỉ mục |
| R5 | Người dùng thấy hệ thống chậm hơn cách làm cũ nên không dùng | Cao | Đo thời gian thao tác thực tế, so với cách làm hiện tại |
| R6 | Bản sao lưu chưa từng được phục hồi thử | Cao | Thử phục hồi trước khi bàn giao |
| R7 | Nghiệm thu dồn về một đợt cuối nên sai về giao diện và trải nghiệm phát hiện muộn, lúc đó sửa đắt hơn | Cao | Bám sát bản dựng ở `prototype/` làm chuẩn giao diện; mỗi giai đoạn vẫn chạy thử tay và báo cáo, chỉ không đòi người dùng nghiệm thu |

---

## 5. Câu hỏi cần hỏi người dùng

Các câu H1–H7 đã chuyển sang [USER_INQUIRY.md](USER_INQUIRY.md) ngày
09.09.2026 theo yêu cầu chủ dự án: chia theo vấn đề, đối tượng trả lời và
danh sách đánh số. Cập nhật câu hỏi/câu trả lời tại file đó để tránh lệch
hai bản. Backlog tiếp tục giữ tiến độ, các vấn đề N/V và lịch sử quyết định.

Tra từng câu: H1 công thức; H2 kéo điền; H3 dán; H4 thời gian nhập/tổng hợp;
H5 tìm kiếm; H6 cơ cấu team; H7 quyền nhập tiền/bằng chứng. H7 vẫn chưa chốt.

---

## 6. Hiện trạng màn hình — chưa nghiệm thu

Người dùng nêu ngày 29.08.2026: **hiện quá thiếu màn hình để đánh giá được
giao diện và trải nghiệm.** Không nghiệm thu từng phần nữa; dồn về một đợt
kiểm thử toàn diện khi đủ màn hình. Mốc cụ thể xem **V4**, kế hoạch kiểm thử
xem **V5** — cả hai đều chưa chốt.

> **Chưa có gì được nghiệm thu.** Giai đoạn 0 tới 5 đều đã giao và đã chạy
> kiểm thử tự động, nhưng **người dùng chưa trực tiếp thử màn hình nào**. Mọi
> phần trăm trong `dashboard-tien-do.html` là tiến độ *đã làm*, không phải
> tiến độ *đã nghiệm thu*. Hai con số đó có thể lệch nhau, và chỉ đóng lại
> được sau đợt kiểm thử ở V4.

| Giai đoạn | Đã giao | Người dùng đã thử |
|---|---|---|
| 0 · Tài liệu và quyết định | ✓ | — |
| 1 · Nền móng | ✓ | Chưa |
| 2 · Cơ cấu tổ chức và giao diện chung | ✓ | Chưa |
| 3 · Biểu mẫu và bảng động | ✓ | Chưa |
| 4 · Báo cáo hằng ngày | ✓ | Chưa |
| 5 · Lên đơn và vận đơn | ✓ | Chưa |
| 6 · Báo cáo tổng hợp | ✓ | Chưa |
| 7 · Nhập xuất, sao lưu, Bảng tính, kiểm thử toàn diện, Bảng tính mọi bảng | ✓ | Chưa — kịch bản ở `docs/07` |
| 8 · Máy chủ, điện thoại, tối ưu | Chưa — chờ V1 | — |
| 9 · Nội bộ, bản MVP — Tài liệu, Bảng tin, Công việc, Văn hoá, Tài nguyên | ✓ trên nhánh riêng, PR #20 nháp | Chưa — kịch bản ở `docs/07` mục 3.1, 3.2, 3.4 |

Bản dựng giao diện tĩnh ở `prototype/` là chuẩn để đối chiếu. Nó có 10 màn
hình mà bản Django chưa có; bảng dưới đây theo dõi việc lấp dần.

| Màn hình trong bản dựng | Giai đoạn | Trạng thái |
|---|---|---|
| Bảng vận đơn — bảng dữ liệu chung | 3A | Đã có, dưới tên `/bang/<mã>/`, chỉ xem như mọi bảng (ADR-014) |
| Ma trận phân quyền | 3A | Đã có, bản chỉ đọc |
| Quản lý biểu mẫu | 3B | Đã có |
| Trình tạo biểu mẫu | 3B | Đã có |
| Nộp báo cáo ngày | 4 | Đã có |
| Lịch sử báo cáo | 4 | Đã có |
| Lên đơn | 5 | Đã có |
| Báo cáo tổng hợp | 6 | Đã có — tab Theo thị trường treo ghi chú chờ N9, Q36 |
| Bảng tính | 7 | Đã có — lưới cho **mọi bảng** ở `/bang-tinh/<mã>/` (ADR-010): viền ô, dòng trống, cột khoá, thanh lọc bên trái, thanh công cụ, định dạng ô, thư mục; bảng vận đơn vẫn sửa ở dịch vụ `bangtinh` (ADR-009); nhìn và thao tác như bảng tính KN Demo — chọn vùng, dán từ Excel, kéo điền, chuột phải, hoàn tác, hộp lọc giá trị, tự cập nhật (ADR-011); là **app riêng KN CRM** ở 8021 với trang chủ cây Bộ phận ▸ Quý ▸ Tháng, ERP chỉ liên kết (ADR-012) — nhánh `claude/bang-tinh-nhu-kn-demo` |
| Bảng tính, màn hình chi tiết | 7 | Không làm engine công thức (ADR-009); phần thanh công cụ định dạng của bản dựng đã có lại dưới dạng sổ đóng (ADR-010); thanh công cụ và thanh công thức theo KN Demo (ADR-011), công thức chờ S10 |

**Thiếu sót đã biết, không phải màn hình riêng nhưng ảnh hưởng trải nghiệm:**

| # | Nội dung | Giai đoạn xử lý |
|---|---|---|
| 1 | ~~Bảng động chưa có chỗ thêm dòng mới~~ — xong ở 3B, màn hình điền biểu mẫu | — |
| 2 | Chưa có trang lỗi 404 và 500 tiếng Việt — K9 | Chưa xếp |
| 3 | Giao diện chưa kiểm trên điện thoại và máy tính bảng — NFR-7, AC-10.4 | 8 |
| 4 | ~~Điều hướng sau đăng nhập theo bộ phận — FR-1.6~~ — bỏ theo Q34, ngày 03.09.2026 | — |
| 5 | Chưa có dữ liệu mẫu đủ lớn để thấy bảng chạy thật thế nào | 8, `seed_perf.py` |

**Khi tới đợt kiểm thử toàn diện, chạy theo `docs/04` mục 3 và mục 10:** ma
trận kiểm chéo chín vai trò, các tiêu chí thủ công `AC-8.1`, `AC-10.3`,
`AC-10.4`, `AC-5.6`, và đối chiếu từng màn hình với bản dựng ở `prototype/`.

---

## Nhật ký cập nhật

| Ngày | Nội dung |
|---|---|
| (điền) | Tạo tài liệu |
| 28.08.2026 | Rà soát Giai đoạn 1 và 2 — 19 phát hiện. Sửa 18, hoãn K7. Thêm K7–K10 và N5–N8 |
| 29.08.2026 | Chốt K1, K2, K3 và N8 — gỡ hết điểm chặn Giai đoạn 3. Ghi ADR-006 và ADR-007 |
| 29.08.2026 | Xong Giai đoạn 3 phần A. Chốt Q14 tới Q17. Thêm AC-3.8, AC-7.10 tới AC-7.12 vào `docs/04`. Mở K11 và K12 |
| 29.08.2026 | Người dùng nêu: quá thiếu màn hình để nghiệm thu. Hoãn nghiệm thu tới một đợt toàn diện — mở V4 và R7, thêm mục 6 theo dõi hiện trạng màn hình |
| 29.08.2026 | Xong Giai đoạn 4 — báo cáo hằng ngày. Chốt Q21 và Q22. Ghi ADR-008 |
| 29.08.2026 | Thêm lệnh `manage.py du_lieu_mau` — máy mới chạy một lệnh là có 12 tài khoản và dữ liệu thật để dùng thử. Trước đó `docker compose up` trên máy sạch cho ra hệ thống không đăng nhập được, và việc số 1 trong danh sách kiểm thủ công **không làm được** dù tôi đã ghi là "chạy được" |
| 29.08.2026 | Cho một tác nhân đóng vai phiên mới đọc kho mã, tìm ra 11 chỗ tài liệu sai hoặc thiếu. Sửa hết: bảng tiến độ báo "mã nguồn chưa bắt đầu" và chỉ hiện tới GĐ 1; số tiêu chí ghi 47 và 58 trong khi thật là 68; `docs/06` ghi 28/40 trong khi thật là 49/61; mục 6 kẹt ở GĐ 4; `docs/05` tả tính năng chưa có như đã chạy; thiếu ADR-008; K1–K4 vẫn ghi là đang chờ. Thêm bốn bài canh con số |
| 29.08.2026 | Lập kế hoạch kiểm thử toàn diện — `docs/06`. Từ 249 lên **779 bài đạt**, bao phủ 83%. Thêm bốn tầng: tệp chuyển đổi, kiểm khói, ma trận 35 ô, truy vết. Tìm ra 4 lỗi phân quyền, 1 lỗi tiền, 3 lỗi giao diện. Chốt Q30 tới Q33, đóng K5 và K15, mở K17 |
| 29.08.2026 | Đối chiếu toàn bộ 8020 với 8010 theo từng trường. Bổ sung: cột Doanh số ở Lịch sử báo cáo, cột Người tạo và Cập nhật ở Quản lý biểu mẫu, Giá trị mặc định cho định nghĩa trường, cột tính sẵn hiện ngay trên biểu mẫu. Làm K15 thành bài kiểm thật. Chốt Q28 Q29, mở K16 |
| 29.08.2026 | Người dùng đối chiếu màn Lên đơn với bản dựng: thiếu cột Thành tiền, khối Tóm tắt, khối Sau khi lưu. Phát hiện thêm `.luoi-2cot` không tồn tại nên bốn màn hình hiện một cột, và ba lớp `.o-tinh` `.o-loi` `.o-trong-bang` chưa có kiểu dáng. Đã bổ sung hết, mở K15 |
| 29.08.2026 | Xong Giai đoạn 5 — lên đơn và vận đơn. Chốt thêm Q27 sau khi chạy thử tay phát hiện Vận đơn không thấy dòng nào |
| 29.08.2026 | Bàn Giai đoạn 5. Chốt Q23 tới Q26 — gỡ N4, N5, G1, G2 |
| 29.08.2026 | Người dùng xác nhận chưa thử màn hình nào, chưa nghiệm thu được. Kế hoạch kiểm thử cũng để sau — mở V5, ghi bảng đã giao / đã thử vào mục 6 |
| 29.08.2026 | Xong Giai đoạn 3 phần B, khép lại Giai đoạn 3. Chốt Q18 tới Q20, đóng K11 và K12, mở K13 và K14. Bỏ model `Position` khỏi tài liệu vì nó không tồn tại |
| 03.09.2026 | Chốt Q34 — bỏ K18: tất cả đăng nhập vào trang tổng quan chung, phân quyền đã ẩn tính năng ngoài phận sự. Gạch FR-1.6 và AC-1.7 khỏi `docs/02` và `docs/04`, còn 67 tiêu chí. K9 (trang lỗi 404 và 500) người dùng chốt chưa phải lúc, giữ trong backlog |
| 03.09.2026 | Xong Giai đoạn 7 phần A — nhập xuất Excel và tác vụ nền: `core/excel.py`, `BackgroundJob`, luồng nhập bốn bước có xem trước và tiến độ, xuất kèm bộ lọc, tệp lớn chạy nền giữ 24 giờ. Gỡ `AC-7.5` tới `AC-7.9` khỏi HOAN. Ẩn danh tệp vận đơn thật (Q43). Sửa Q26 thành Q42 |
| 03.09.2026 | Xong Giai đoạn 7 phần B — sao lưu `pg_dump` hằng đêm giữ 30 bản, thất bại thì thư cho người vận hành; lệnh `sao_luu`, `phuc_hoi --toi-chac-chan`; service `beat` và `bangtinh` trong compose. Gỡ `AC-10.6` khỏi HOAN, mở K21 |
| 03.09.2026 | Xong Giai đoạn 7 phần C — Bảng tính vận đơn theo tệp thật (ADR-009): lưới lọc theo cột, sửa ô tại chỗ có danh sách chọn, Lọc trùng, tô màu Hủy/Hoàn, cột số lượng theo sản phẩm; tám trạng thái mới và tiền tệ CAD/PHP (`orders/0002`); dịch vụ `bangtinh` cổng 8021. Thêm `docs/04` mục 11 (AC-11.1 → 11.11), đánh số lại mục 12–14. Chốt Q37 tới Q45, mở K22 |
| 03.09.2026 | Xong Giai đoạn 7 phần D — kiểm thử toàn diện: Playwright (bàn phím, hộp lọc, cột cố định, 390px không tràn ngang, nhập→xuất→nhập lại qua giao diện), `seed_perf` 50.000 dòng và bài hiệu năng dưới 2 giây, Locust 50 người tự chấm p99, ma trận phân quyền 35 → 45 ô. HOAN chỉ còn `AC-5.1`: 70 trên 70 tiêu chí tự động có bài kiểm. Viết `docs/07-kich-ban-nghiem-thu.md`, cập nhật docs/03, 05, 06; đóng K6, mở K19, K23 (hộp lọc trong Playwright), K24 (12 truy vấn trên 50.000 dòng) — hai bài đó đánh dấu xfail vì người dùng cần demo gấp; bảng tiến độ sang GĐ 8 |
| 03.09.2026 | Người dùng phàn nàn mở `localhost:8020` không lên sau khi đổi phiên làm việc. Nguyên nhân: container không tự bật lại sau khi tắt máy, và mã mới chưa kéo về. Thêm `restart: unless-stopped` cho bốn dịch vụ compose, và `scripts/cap-nhat-local.sh` + `.bat` — một lệnh kéo mã, dựng lại, bảo đảm dữ liệu mẫu |
| 03.09.2026 | Xong Giai đoạn 6 — báo cáo tổng hợp: `reports/aggregations.py` dịch nhãn ý nghĩa sang phép tính, màn hình ba cách nhóm kèm lọc, dòng tổng cộng, bốn ô số và xuất Excel có ghi nhật ký (P5). Chốt Q35 (ô chọn một bảng nguồn) và Q36 (hoãn tab thị trường), mở N9 và N10. Gỡ `AC-5.2` tới `AC-5.5` khỏi HOAN — còn 8 tiêu chí hoãn, 53 trên 61 đã có bài kiểm. Sửa luôn: phân trang giữ tham số lọc (`qs_loc`), đệm phạm vi quyền theo lượt yêu cầu để màn hình đứng dưới trần 10 lệnh truy vấn |
| 04.09.2026 | Người dùng dựng ở máy nhà, gặp lần lượt: Docker chưa mở nên 8020 không lên; gõ `/bangtinh` thiếu gạch nên 404; rồi màn hình Bảng tính 404 vì "Chưa có bảng vận đơn". Người dùng hỏi đúng: *vì sao đã viết mã rồi mà còn phải chạy lệnh tay?* Chốt: bảng vận đơn là bảng động nên `migrate` không sinh ra, nhưng mã đòi nó tồn tại, vậy `entrypoint.sh` phải tự gọi `tao_bang_van_don` sau `migrate`. Lệnh này giờ tự tạo bộ phận Vận đơn trên máy sạch (trước đó chạy trên máy sạch thì đổ lỗi thiếu bộ phận — phát hiện khi thử thật). Gộp vào `scripts/cap-nhat-local.sh` và `.bat` phần tự mở Docker Desktop, đợi web lên và mở trình duyệt — một lệnh là chạy. `du_lieu_mau` vẫn phải chạy tay vì tài khoản mẫu không được tự sinh trên máy chủ thật |
| 04.09.2026 | Người dùng gửi ảnh Lumi OMS, yêu cầu Bảng tính như CRM chuyên biệt. Chốt bốn câu (Q46 → Q50) rồi làm Giai đoạn 7 phần E, ADR-010: lưới cho mọi bảng (A), định dạng ô lưu DB (B), thư mục chứa bảng (C). Thêm `forms_builder/0006` (`is_key`, `style`) và `0007` (`Folder`, `TableDef.folder`); `export_service` có sổ builder để Bảng tính xuất đúng lưới kể cả `trung=` và `sp=` (lỗ hổng cũ: xuất bỏ qua `trung=1`). Phát hiện và sửa lỗi tiềm ẩn: màn hình Sửa cột không lưu thay đổi vì ModelForm đã ghi vào instance trước khi dịch vụ so cũ với mới. AC-11.12 → 11.18; 85 tiêu chí. Ngân sách truy vấn `/bang-tinh/<mã>/` đặt 14 (thanh bên thêm hai lệnh trên K24). Bài Playwright thêm hai: dòng trống + ⌕, chọn vùng + định dạng |
| 04.09.2026 | Người dùng kéo nhánh về máy nhà, mở 8021 gặp `column forms_builder_tabledef.folder_id does not exist`: mã mới vào container qua bind mount nên container không dựng lại, `migrate` trong entrypoint không chạy. Sửa `cap-nhat-local.sh` và `.bat` gọi tường minh `migrate` và `tao_bang_van_don` sau `up` |
| 04.09.2026 | Trên Windows, cả bốn container `Restarting` với `exec /entrypoint.sh: no such file or directory`: git checkout đổi `entrypoint.sh` sang CRLF, `#!/bin/sh\r` không có trình thông dịch. Sửa hai tầng: `.gitattributes` giữ LF cho `.sh .py .html .css .js` (gộp ý từ nhánh `claude/project-status-progress-7ajcqg`), và Dockerfile `sed -i 's/\r$//'` trước `chmod` để image dựng đúng dù git cấu hình thế nào |
| 04.09.2026 | Người dùng cập nhật xong vẫn thấy Bảng tính vỡ bố cục: trình duyệt dùng `bang-tinh.css` cũ trong bộ đệm (cùng tên với tệp đã có trên `main`). Thêm `?v=<mốc sửa tệp tĩnh>` vào mọi đường dẫn CSS và JS (`core/context_processors.PHIEN_BAN_TINH`) — đổi mã là trình duyệt tự tải mới, không phải Ctrl+F5 |
| 04.09.2026 | Người dùng thêm hai yêu cầu: (1) kéo đổi độ rộng từng cột và tự quyết thứ tự cột A B C; (2) Bảng tính phải là một trang toàn màn hình khác hẳn, chức năng chính là lưới. Làm ngay trong 7E: khung riêng `crm/base_bang_tinh.html` (không thanh bên hệ thống, menu ☰), chữ cột A B C, kéo mép tiêu đề đổi rộng, kéo thả tiêu đề đổi thứ tự, nút Đặt lại cột — ba thứ nhớ trên trình duyệt theo mã bảng (ADR-010 mục 8, 9). Sửa AC-11.18 |
| 04.09.2026 | Người dùng gửi gói KN Demo (`Kim_Ngan_DEMO.rar`), chốt *"tạo nhánh riêng và làm cái view y hệt như ảnh"*. Nhánh `claude/bang-tinh-nhu-kn-demo` tách từ đầu nhánh 7E. Đọc trọn mã demo: bảng tính JSON tự viết, công thức tính ở trình duyệt, tự lưu cả tài liệu, không phân trang — KNJSC chỉ lấy cách nhìn và thao tác (ảnh ở `docs/tham-khao/kn-demo/`). Giai đoạn 1 (ADR-011): khung tối viền vàng 48px, thanh công cụ đúng thứ tự demo, thanh công thức có ô địa chỉ `A1`, cột số dòng 46px, hàng chữ cột có nút ▼ và mép kéo, hàng tên cột là hàng 1 (vận đơn xanh, bảng khác vàng), cột trống tới Z, chân trang có tab bảng và `+100 dòng`, trạng thái lưu, nút ⛶ toàn màn hình, bấm một lần là chọn / bấm đúp hoặc gõ chữ là sửa, thanh bên ẩn mặc định. Sổ định dạng mở rộng theo demo: nghiêng, gạch chân, gạch ngang, xuống dòng, viền, bảng 40 màu chữ và nền (`m01…m40`, CSS sinh bằng `scripts/sinh-css-mau.py`), cỡ 10–28, định dạng số. Sửa nhân tiện: `tests/test_hieu_nang.py` để lại bộ phận và bảng giả trong cơ sở dữ liệu kiểm thử (xoá mềm vẫn chiếm tên unique) làm mọi bài chạy sau đỏ khi chạy cả bộ kể cả `cham` — dọn thật ở teardown |
| 04.09.2026 | Giai đoạn 2 của ADR-011 trên nhánh `claude/bang-tinh-nhu-kn-demo`: kéo chuột chọn vùng (ô địa chỉ hiện `C3:F7`, số dòng và chữ cột tô sáng, thống kê Tổng · TB · Số ô), bấm số dòng chọn hàng, chữ cột chọn cột, góc chọn cả trang; Shift+mũi tên, Ctrl+A; cắt/chép/dán qua clipboard hệ thống (TSV — dán từ Excel được, dán nội bộ mang theo định dạng, lặp khối khi vùng là bội số, tràn xuống dòng trống thì tạo bản ghi); tay kéo điền bốn hướng (số cách đều thì tiếp chuỗi, không thì lặp khối); Delete xoá nội dung; hoàn tác/làm lại 100 bước phía trình duyệt (giá trị và định dạng). Máy chủ: `record_service.update_cells` + `POST luu-o/` được cả hoặc không gì, `CellError` chỉ đúng ô, quyền kiểm từng dòng, ngoài phạm vi 403 có nhật ký; AC-11.19, AC-11.20. Ba lỗi ngầm của htmx 2 gặp trên đường: (1) `afterRequest` bắn trước khi thay ô — phải chờ `afterSettle`; (2) phần tử mới trùng id với phần tử cũ thì trong lúc settle mang tạm thuộc tính cũ — trình sửa ô không được mang id; (3) `processNode` chạy sau settle 20ms nên `requestSubmit()` sớm hơn là trình duyệt tự nộp biểu mẫu — `guiSua` chờ hết `htmx-settling`. Và: mảnh HTML có `<td>` đứng trước `<tr>` thì trình duyệt bỏ `<tr>` — phản hồi luu-o trả dòng trước ô |
| 04.09.2026 | Giai đoạn 3 của ADR-011: menu chuột phải đúng nhãn demo (Cắt · Sao chép · Dán · Chèn N hàng trống · Xoá N hàng · Chèn N cột trái/phải · Xoá N cột · Xoá nội dung · Xoá định dạng; mục không có quyền mờ đi); xoá dòng là xoá mềm sau hộp xác nhận, Ctrl+Z khôi phục về chỗ cũ (`xoa-dong/`, `khoi-phuc-dong/`, `record_service.restore_record`, quyền `can_delete_record` = quyền sửa dòng — Q52); Manager của bộ phận sở hữu chèn/bỏ cột ngay trên lưới (`them-cot/`, `xoa-cot/`, `table_service.insert_columns`, `removable_reason`; cột khoá, vế cột tính sẵn, cột hệ thống vận đơn thì giữ; `can_manage_columns`); hộp lọc cột theo demo (tên cột · số giá trị, ô tìm, danh sách giá trị kèm số cho mọi kiểu cột, Điều kiện khác gập, Chọn tất cả · Không chọn · Xóa lọc · Áp dụng); lưới hỏi `moi-nhat/` mỗi `GRID_POLL_SECONDS` giây khi rảnh, có gì mới thì nạp lại thân bảng và toast. AC-11.21 → AC-11.26, 93 tiêu chí, 83 trên 84 tự động có bài kiểm. Nhãn "Bỏ chọn" của demo đổi thành "Không chọn" vì luật nút nguy (test_giao_dien) bắt chữ "Bỏ"; các mục Xoá trong menu mang `nut-nguy` (chữ đỏ) theo cùng luật |
| 04.09.2026 | Giai đoạn 4 của ADR-011 — tài liệu: viết `quyet-dinh/011-bang-tinh-theo-mau-kn-demo.md` (kèm bảng "không làm"), thêm 009/010/011 vào danh sách ADR; `docs/02` FR-7.9 → FR-7.12; `docs/03` §4.6 thêm các dòng lưu nhiều ô, xoá/khôi phục dòng, chèn/bỏ cột, hộp lọc giá trị, tự cập nhật, hoàn tác, cột trống, hai tệp JS; `docs/04` AC-11.27 (thủ công, đối chiếu ảnh) — 94 tiêu chí; `docs/05` A8 viết lại theo giao diện mới; `docs/06` bảng thủ công thêm AC-11.18 (thiếu từ 7E) và AC-11.27; `docs/07` thêm bước dán từ Excel, kéo điền, chuột phải xoá hàng, chèn cột, hộp lọc, tự cập nhật, và sửa các bước cũ theo giao diện mới (bấm đúp mới sửa, Nhập tệp trong ⋯, Tải Excel ở thanh trên, Bộ lọc mở thanh bên); chốt Q51 → Q53, mở S9, S10; dashboard 7F |
| 05.09.2026 | Gộp PR #4 (Giai đoạn 7E, ADR-010) vào `main` bằng merge commit `3facc87`, giữ nguyên SHA và giữ nhánh 7E. PR #5 (7F, ADR-011) đổi base về `main`, vẫn mở trên nhánh riêng theo ý anh/chị — chờ nghiệm thu `docs/07` rồi mới gộp. Nhánh 7F gộp `main` vào để không tụt sau |
| 06.09.2026 | Người dùng muốn một tệp `.bat` nháy đúp là mở ngay `localhost` trên máy đó và tự bật Docker. `cap-nhat-local.bat` làm được nhưng kéo mã, dựng lại image và nạp dữ liệu mẫu nên mất vài phút — quá nặng cho việc mở lại hằng ngày. Thêm `scripts/KN JSC.bat` (tên do người dùng chọn; kèm biểu tượng `KN JSC.ico` vẽ từ `KN JSC.svg` — chữ KN trắng trên nền xanh, vạch cam, chữ JSC; lần đầu chạy tự tạo lối tắt "KN JSC" ngoài Desktop bằng PowerShell, đường dẫn Desktop lấy từ Registry để đúng cả khi OneDrive dời Desktop): mở Docker Desktop nếu chưa chạy (tìm cả trong Registry khi cài ở thư mục khác), `up -d` không `--build`, kiểm web ngay trước khi ngủ nên container đang chạy sẵn là mở trình duyệt tức thì; lần đầu trên máy sạch (chưa có container `web`) thì nạp `du_lieu_mau` trước khi mở, không thì không có tài khoản để đăng nhập. `cap-nhat-local.bat` cũng gọi nó (tham số `loi-tat`) ngay sau `git pull`, vì người dùng kéo mã xong là mong thấy logo ngay chứ không đi tìm tệp `.bat`. Người dùng bực vì vẫn phải tìm thư mục để nháy đúp lần đầu: yêu cầu thật là *mỗi ngày ấn một nút, không gõ gì*. Thêm `scripts/Cai dat KN JSC.bat` gửi thẳng qua chat để nháy đúp một lần ở bất kỳ đâu: tự tìm thư mục KNJSC trên máy (chỗ hay clone, rồi quét `dir /s`), `git pull`, gọi `KN JSC.bat` để tạo logo ngoài Desktop và mở hệ thống. Từ đó chỉ còn logo trên Desktop. Rồi người dùng chốt: **một tệp `.bat` ở thư mục gốc, máy nào clone về cũng nháy đúp là lên** — chuyển `KN JSC.bat` lên gốc, thêm tự `git pull --ff-only`; có mã mới thì migrate, `tao_bang_van_don`, khởi động lại worker/beat, dựng lại image chỉ khi Dockerfile/requirements/entrypoint đổi; gọi lại chính nó sau pull (tham số `da-keo`) vì cmd đọc `.bat` theo byte, tệp tự đổi là đọc lệch dòng. Lối tắt Desktop làm mới mỗi lần chạy để trỏ đúng chỗ khi kho mã chuyển. `cap-nhat-local.bat` giữ làm bản "làm hết cho chắc", và cũng được sửa theo cùng kiểu gọi lại chính nó sau `git pull` (mô phỏng cho thấy bản cũ trên máy người dùng, khi kéo mã đè lên chính nó, đọc tiếp rơi vào giữa dòng `set /a DEM+=1` rồi dừng ngang nếu Docker đang chạy sẵn). Bài học: **tệp `.bat` nào tự `git pull` thì phần sau `pull` phải nằm trong khối `( ... )` và `call` lại chính nó.** Chỉ Windows, chưa làm bản `.sh` vì Mac/Linux chỉ cần `docker compose up -d` |
| 06.09.2026 | Anh/chị hỏi lại câu gốc: vì sao cần Bảng tính, so với Excel, Google Sheets, Lark thì sao; kể lại dây chuyền Google Form → Sheet của Vận đơn lag dần sau vài tháng (6.000 khách một tháng). Chốt: KN ERP xem nhanh, **Bảng tính là app riêng KN CRM** tách tên miền, không làm app cài đặt, cái cần trên điện thoại là ERP. Bốn yêu cầu cho KN CRM (trang mới, thấy thư mục trước, quyền do Manager cấp, cây Bộ phận → Quý → Tháng → file); phản biện được chấp nhận: tháng là góc nhìn trên một bảng, quyền theo bảng. Làm 7G trên cùng nhánh: bỏ `crm.urls` khỏi ERP, một mục KN CRM mở tab mới, `crm/tests/conftest.py` đặt URLconf 8021, `test_khoi` duyệt hai URLconf; `crm/services/tree_service.py` + trang chủ `/` (cây tự sinh từ `val_date`, đếm một truy vấn cho cả bộ phận), nhãn tháng trên lưới, nút ← về đúng nhánh, tạo thư mục từ trang chủ; AC-11.28 → AC-11.30, 97 tiêu chí; ADR-012; Q54 → Q56 |
| 06.09.2026 | Anh/chị xem ảnh trước/sau (main 7E so với nhánh KN CRM) rồi chốt **gộp PR #5 vào `main`**. Gộp `main` (PR #6 → #10, `KN JSC.bat`) vào nhánh trước để hết xung đột ở chính bảng này, rồi gộp PR #5 bằng merge commit, giữ nhánh như lần PR #4. Máy anh/chị đang ở `main` nên nháy đúp `KN JSC.bat` là kéo được KN CRM; mã mount thẳng vào container, không cần dựng lại image. `/bang-tinh/` ở 8020 từ nay trả 404, lưới chỉ có ở KN CRM 8021 |
| 06.09.2026 | Đợt chỉnh sửa KNERP đầu tiên (thread KNERP, chỉ hệ thống chính, không đụng `app/crm/`). Bốn yêu cầu: (1) mọi chỗ chọn lựa là ô chọn có "＋ Thêm mới…", sản phẩm lấy từ danh mục và Manager thêm tại chỗ; (2) trường Người bán tự ghi tên người điền; (3) Bảng dữ liệu tô màu cột và ngưỡng cảnh báo, tiêu đề xanh lá; (4) viền mọi ô. Chốt Q58 → Q61, ghi ADR-013, đóng K22, mở K25, S11, S12. `ColumnDef` thêm `options`, `highlight`, `alert_op`, `alert_value` (migration 0008); `choice_registry` ba tầng; `choice_service`, `product_service`, `core/identity`, `forms_builder/styling`; `components/o_chon.html`, `static/js/chon.js`; hai đường dẫn POST mới. Sửa nhân tiện: chú thích nhiều dòng `{# #}` ở màn nộp báo cáo bị hiện ra màn hình; lỗi sửa ô 400 bị HTMX nuốt nay hiện ngay trong ô. AC-4.6, AC-6.9, AC-8.7 → AC-8.10. PR #5 (KN CRM) vào `main` trước nên đánh số lại ADR-012 → ADR-013, Q54 → Q57 thành Q58 → Q61, nhãn 7G thành 7H; sau khi gộp: 103 tiêu chí, 91 trên 92 tự động có bài kiểm |
| 06.09.2026 | Sau khi gộp PR #5, anh/chị nháy `KN JSC.bat` mà vẫn thấy "Bảng tính" thay vì KN CRM. `git status -sb` trên máy cho thấy kho đứng ở nhánh `claude/bang-tinh-nhu-kn-demo` tại `f11b788` (bản 04.09), `[behind 6]`, và **đang gộp dở**: `UU docs/backlog.md` cùng loạt tệp của main đã stage — dấu vết lần `cap-nhat-local.bat <nhánh>` trước đó `git pull` vướng xung đột ở `docs/backlog.md` rồi dừng, còn `KN JSC.bat` sau đó `git pull --ff-only -q` bị từ chối vì đang merge nhưng `-q` nuốt lỗi, chạy tiếp bằng mã cũ. Gỡ trên máy: `git merge --abort`, `git checkout main`, `git pull --ff-only`. Sửa cho hết lặng lẽ: `KN JSC.bat` thấy `.git/MERGE_HEAD` (hay `rebase-merge`, `rebase-apply`) thì in cách gỡ và không kéo; in nhánh đang đứng, cảnh báo khi không phải `main`; bỏ `-q`, pull lỗi thì in rõ và đợi 8 giây rồi vẫn bật bản đang có; `cap-nhat-local.bat` checkout hay pull lỗi thì dừng có thông báo thay vì dựng tiếp bằng mã cũ và để lại merge dở. Gỡ xong, 8021 báo `ProgrammingError: column forms_builder_columndef.options does not exist` — mã mới đã chạy nhưng **chưa migrate**: `KN JSC.bat` chỉ migrate khi chính nó kéo được mã (`TRUOC` ≠ `SAU`), người dùng kéo tay thì nó thấy "không có mã mới" và bỏ qua. Sửa: nhớ commit của lần chạy trước ở `storage/.kn-jsc-lan-truoc`, khác `HEAD` là migrate và cân nhắc `--build`, dù ai kéo; `cap-nhat-local.bat` migrate xong cũng ghi tệp đó. Bài học: **tệp `.bat` gọi git thì không được `-q`, phải kiểm `errorlevel` sau mỗi lệnh, và "có mã mới" phải so với lần chạy trước chứ không phải với lần kéo của chính nó** |
| 06.09.2026 | Người dùng muốn thêm skill thiết kế như bên Codex: **Impeccable** và **taste-skill** ("teach taste" của Impeccable nay là `/impeccable init`, `teach` là bí danh). Trong phiên web, `impeccable.style` bị chính sách mạng chặn (403) và `npx skills add` bị bộ phân loại chặn, nên chép thẳng từ kho nguồn GitHub: Impeccable skill 4.2.1 (Apache-2.0) vào `.claude/skills/impeccable/` kèm 4 subagent ở `.claude/agents/`, và 4 trên 13 skill của taste-skill (MIT): `design-taste-frontend`, `redesign-existing-projects`, `high-end-visual-design`, `minimalist-ui`; bỏ các skill sinh ảnh và bản riêng cho Codex, Stitch. Không commit hook detector (chạy engine sau mỗi lần sửa tệp), bật tay bằng `/impeccable hooks on`; engine tải về `~/.impeccable/bin/` lần đầu chạy, không nằm trong kho. Ghi nguồn và cách cập nhật ở `.claude/skills/NGUON.md`; CLAUDE.md thêm mục "Skill thiết kế giao diện" nhắc quy tắc 8 đứng trên gợi ý thư viện của skill |
| 06.09.2026 | Chạy `/impeccable init`. Ba câu hỏi, ba câu trả lời: (1) tên chính thức **KNERP** cho hệ thống chính, **KN CRM** cho bảng tính, **Kim Ngân JSC** là công ty; (2) **máy tính là chính, điện thoại phụ** để nộp báo cáo ngày và xem nhanh; (3) **nhiều người dùng máy yếu hoặc mạng yếu**, không có yêu cầu trợ năng nào được nêu (ghi là chưa quyết). Viết `PRODUCT.md` ở thư mục gốc theo lược đồ của Impeccable, phần còn lại lấy từ docs và ADR; không ghi hướng thẩm mỹ. Không có công cụ sinh ảnh trong phiên nên chưa ghi `buildPath`; chế độ live chưa cấu hình vì ứng dụng không chạy trong phiên web. Ngay sau đó chủ dự án nói thêm: *hiện chưa cần quá lo về hiệu năng*, nên PRODUCT.md hạ "máy yếu, mạng yếu" từ ràng buộc xuống điều cần biết, không lấy làm cớ cắt hiệu ứng hay tính năng |
| 06.09.2026 | Anh/chị hỏi vì sao bảng vận đơn không sửa được mà Báo cáo Marketing lại sửa được ngay trên Bảng dữ liệu: vì `GRID_ONLY_TABLES` chỉ có `van_don` (ADR-009 mục 4), bảng khác còn luật sửa ô của Giai đoạn 3 (FR-7.4) và ADR-010 mục 1 giữ nguyên điều đó; đợt KNERP đầu tiên không nêu mâu thuẫn này ra. Anh/chị hỏi tiếp gỡ hết dấu vết sửa ô có nhẹ đi không — trả lời thật: không bớt dữ liệu, tính toán khi ghi chuyển sang KN CRM cùng bộ mã; nhẹ ở mã và ở trang bảng có cột chọn; lý do thật là một cửa ghi duy nhất. Chốt **Bảng dữ liệu chỉ để xem với mọi bảng, sửa số liệu là việc của KN CRM** (Q62, ADR-014, luật 13 `CLAUDE.md`) và gỡ hết phía ERP: view `bang_sua_o` + đường dẫn, `_o.html`, khối script trong `bang_xem.html`, nhánh `editable` của `styling`, `choice_service.attach_lists`, handler 400 trong `chon.js`, CSS `o-loi-ly-do`; nút "Mở trong KN CRM" và dòng báo hiện với mọi bảng. Giữ `can_edit_record`, `record_service`, `GRID_ONLY_TABLES` vì lưới KN CRM dùng (K26). 14 bài kiểm thử sửa ô viết lại thành bài chỉ xem (AC-7.4, AC-11.7, AC-8.7) và bài gọi thẳng `update_cell` (BR-5, ADR-006, AC-7.10); một khẳng định ở `crm/tests/test_bang_tinh.py` đổi 403 → 404 |
| 07.09.2026 | Anh/chị mở KN CRM sau khi gộp PR #5 và nêu bốn điểm: bấm ← mãi rơi về ERP; chưa có trang chủ, chưa có sidebar; thư mục phải là một mục trên sidebar; Leader và Manager được thêm/sửa/xoá/tạo/nhập/xuất. Chốt qua ba câu hỏi và ảnh Teeze: trang chủ tổng quan như ERP, sidebar theo Teeze, Leader như Manager trong bộ phận, lưới vẫn full như Excel và chỉ khi chủ động quay về mới thấy menu trái. Làm **7I** trên nhánh `claude/kn-crm-khung-sidebar` (ADR-015): `grant_service._quan_ly_bo_phan` một chỗ cho mọi phép kiểm quản lý bộ phận, Sửa cột ở ERP kiểm thêm `can_manage_columns` (bịt lỗ Manager bộ phận khác được cấp Xem vẫn sửa cột); `base_crm.html` + `crm/navigation.py` + context processor `khung_crm`; trang chủ `/` = `tong_quan_service`; cây tháng sang `/thu-muc/`; view forms_builder gắn vào 8021 với `{% extends khung %}`, tên `bang`/`bang_xem` chuyển hướng có đăng nhập. Ba lần đụng **tên lớp CSS trùng** giữa sidebar và trang thư mục (`crm-nhan`, `crm-nhom`) làm chữ hoá đơn cách — đặt tiền tố `crm-nav-` cho sidebar. AC-11.31 → AC-11.34, sửa AC-8.8/8.9/11.17/11.19/11.21/11.22/3.6 và ma trận; 107 tiêu chí, 95 trên 96. Số ADR: thread KNERP đã lấy 013 nên đợt này là **014**, sửa dòng trùng "012" trong danh sách ADR |
| 07.09.2026 | Anh/chị muốn thay ▦ trên thanh trên lưới bằng **logo tự thiết kế**, bấm logo về trang chủ; chốt tôi vẽ, đặt ở thanh trên lưới, đầu menu trái KN CRM, đầu menu trái KN ERP và favicon. Vẽ `static/img/kn-crm.svg` cùng họ KN JSC (ô xanh gradient, KN trắng, vạch cam) thêm dấu lưới 3×2 vàng nhạt và chữ CRM; `static/img/kn-jsc.svg` là bản web của `scripts/KN JSC.svg`. Context processor `khung_crm` trả `logo` theo dịch vụ để một dòng favicon dùng chung ở bốn khung; trang đăng nhập cũng mang logo. Trước đó hệ thống chưa có favicon nào |
| 07.09.2026 | **MVP Nội bộ** (ADR-017): năm app `documents`, `feed`, `taskboard`, `culture`, `resources`; nhóm Nội bộ trên thanh bên; ngày sinh hồ sơ (org 0003); `FileKind` PDF, Word; `EXCHANGE_RATES_VND`. 23 tiêu chí mới AC-12.1 → AC-16.3 (một thủ công), 126 tiêu chí, 113 trên 114 tự động có bài kiểm, 1.637 bài đạt (chưa kể `cham`). Chốt Q68 → Q74 (sửa Q2, Q8), mở N11, N12, K30, K31, S16 → S20. Sửa nhân tiện: `|default:a.b.c` với `a` trống trong template ném lỗi — rào `{% if %}` ở bốn template |
| 07.09.2026 | **Rà soát lại MVP Nội bộ**: sửa 22 lỗi và điểm yếu trong bốn commit A → D, cải tiến giao diện, gọn mã dùng chung, thêm bài kiểm và tài liệu. Chốt **Q75** (chỉ cấp trên ghi nhận cấp dưới), **Q76** (mọi người bán tranh hạng), **Q77** (đồng hạng); mở **S21**; sửa K30, N11. 1.677 bài đạt (chưa kể `cham`); K29 vẫn của thread KN CRM |
| 07.09.2026 | Anh/chị yêu cầu **kiểm thử toàn diện KN CRM** ở cỡ hàng triệu ô, 100 nghìn khách, rồi mô phỏng 100 người cùng lúc "di qua di lại" và "lập công thức", không bấm giao diện. Chốt: công thức = cột tính sẵn; chạy máy ảo trước, đóng gói cho máy anh/chị; ngưỡng "như Excel trên máy thường" (Q66). Nhánh `claude/kiem-tai-kn-crm`: `seed_perf` 100.000 dòng 24 tháng đủ 30 cột + bảng `perf_sale` 20.000 dòng có Doanh thu = Đơn giá × Số lượng (45 giây, 209 MB); lệnh mới `do_hieu_nang` đo 25 đường kèm EXPLAIN; `tests/perf/locustfile_kn_crm.py` 100 người bốn vai tự chấm. **Trước**: một người thì lưới 638 ms mà DB chỉ 58 ms (95% là 3.900 `{% include %}` + 7.800 `{% url %}`), `?trung=1` 1,1 s, dán 500 ô 1,7 s / 1.013 lệnh, tính lại cột 100.000 dòng 153 s trong request; 100 người thì 13 RPS, p95 mọi nhóm ~11 s. **Sửa** (ADR-016, K27): ô dựng bằng `grid_service.cell_html`; cột Trùng đếm theo trang + chỉ mục `(table, val_phone)`; `moi-nhat/` chỉ Max(updated_at) trên `all_objects` + chỉ mục `(table, updated_at)`; `DataRecord.bulk_save` bằng `UPDATE … FROM (VALUES …)` vì `bulk_update` của Django ghép CASE WHEN mất 1,2 s/1.000 dòng; tính lại cột chạy nền `BackgroundJob` "Tính lại cột" theo lô có tiến độ trên lưới; compose có `KNJSC_LENH_WEB` để chạy gunicorn. **Sau** một người: lưới 154 ms, trang 500 280 ms, trùng 478 ms, dán 500 ô 207 ms, tính lại 20.000 dòng 4,2 s, 100.000 dòng 19,6 s (2 lô song song ở worker). AC-10.8 (thủ công), AC-11.35, AC-11.36; `scripts/kiem-tai-kn-crm.bat/.sh`; bộ đếm docs/06 110 — 98 tự động, 12 thủ công; 97 trên 98. 100 người 5 phút "sau" (gunicorn 3 tiến trình × 4 luồng, `--reset-stats`): 22,8 yêu cầu/giây, p95 đọc 853 ms, ghi 371 ms, hỏi 143 ms, 0 lỗi, tính lại 100.000 dòng 24,4–24,8 s, p95 người khác lúc đó 900 ms — **ĐẠT** (trước: ~11 s mọi nhóm, 14 lỗi). Trên đường đi còn bắt được một deadlock dán ô ↔ worker (khoá cùng chiều pk + thử lại), mốc `moi-nhat/` phải theo cả bảng mới dùng được chỉ mục, và `bulk_update` của Django chậm gấp 14 lần `UPDATE … FROM VALUES` |
| 07.09.2026 | Anh/chị tự thử KN CRM và gửi video: gõ "ssssd" vào cột Số Mess của dòng trống Báo cáo Marketing, rời ô, thanh trên báo "Đã lưu" mà không có gì xảy ra; hỏi vì sao cả `main` lẫn nhánh mới đều bị. Tái hiện trên máy ảo: máy chủ trả 400 đúng ("không đúng kiểu Số nguyên"), nhưng JS coi 400 là thành công và lời báo bị CSS giấu — lỗi có từ 7F, PR #21 chỉ sửa tốc độ nên không gây và không sửa (K28). Anh/chị chất vấn vì sao không đo và kiểm đường sai từ đầu, và khẳng định cách hiện tại chưa tối ưu; tôi nêu ba hướng tối ưu hơn (lưới JSON + JS vẽ ô, SSE, cột tính trong DB). Anh/chị chốt: **ghi backlog, giờ chưa phải lúc tối ưu** — Q67, S13–S15; việc trước mắt là K28 |
| 08.09.2026 | Theo yêu cầu dọn toàn bộ nhánh: hợp nhất bốn đầu việc còn riêng vào `main` — backlog/test-log, kiểm tải KN CRM, MVP Nội bộ và hợp đồng thiết kế chuẩn ngành. Giải trùng mã do hai nhánh phát triển song song: giữ kiểm tải ở ADR-016, Q66–Q67, K27–K28, S13–S15; chuyển MVP Nội bộ sang ADR-017, Q68–Q77, K30–K31, S16–S21. Ba commit chỉ còn ở local `project-status-progress-7ajcqg` không áp lại vì chức năng đã có bản mới đầy đủ hơn trên `main` (launcher, đặt lại mật khẩu mẫu, `.gitattributes`). Sau khi kiểm tra, xóa các nhánh local và remote cũ, chỉ giữ `main` |


## Thiết lập công cụ Codex — 09.09.2026

Đã bổ sung [bộ 5 skill gọn](bo-skill-knjsc.md) ở `.agents/skills` theo kế hoạch được duyệt; nguồn cố định theo commit, có giấy phép và bản biên tập riêng cho KNJSC. Kiểm tra tĩnh 5/5 đạt. Chờ xác nhận Codex khám phá ở phiên tiếp theo và đánh giá tự chọn qua 5 tác vụ thực tế; chưa kết luận tiết kiệm token hoặc tăng hiệu năng ứng dụng. Các skill để dành chưa cài.

09.09.2026: chuẩn hóa [đồng bộ AI nhiều máy](dong-bo-ai-nhieu-may.md), một nguồn nội dung mỗi skill và 6 cầu nối Codex/Claude; thêm script kiểm tra chỉ đọc, kiểm CRLF và phát hiện sai lệch đạt. Codex đã nhận 5 skill cốt lõi; các cầu nối mới chờ kiểm khám phá. Chưa commit/push, chưa đồng bộ qua GitHub.

09.09.2026: theo yêu cầu gom hoàn chỉnh, chuyển 10 bản nội dung về `ai/skills`; Codex/Claude mỗi bên chỉ còn 10 cầu nối cùng danh mục. `.impeccable` giữ dữ liệu thiết kế. Cập nhật đường dẫn launcher, nguồn và script kiểm hash/danh mục; kiểm CRLF, phát hiện file lệch/file dư đạt. Chưa commit/push; chưa kiểm client trên máy khác.

09.09.2026: thay thế cấu trúc đồng bộ phía trên theo yêu cầu mới: chỉ `.agents/skills` giữ 10 skill, bỏ `ai`, `.claude/skills` và `.impeccable` ở gốc. Hồ sơ thiết kế giữ tại `.agents/design-state`; Impeccable dùng hướng dẫn thủ công, không tự chạy engine tạo lại thư mục gốc. Script chỉ kiểm tra, không tạo cầu nối. Chưa commit/push; chưa kiểm engine ở vị trí mới hoặc tự chọn skill qua 5 tác vụ.

## Đề xuất cho giai đoạn sau — 09.09.2026

**Trạng thái: đề xuất, chưa duyệt triển khai. Ưu tiên hiện tại vẫn là sửa feedback khách hàng.**

**Câu hỏi của chủ dự án (tóm tắt):** Từ feedback trong KNJSC_PROBLEM, KN CRM nên làm tính năng gì, với mục tiêu dài hạn là hệ thống chủ động cho người dùng biết việc còn phải làm và sau này tích hợp AI xuyên suốt CRM/ERP?

**Câu trả lời của trợ lý (tóm tắt):** Dựa trên phân công và trạng thái đơn để phát triển “Việc cần làm của tôi”: tập hợp việc theo người phụ trách, chỉ rõ vì sao cần xử lý, mở đúng đơn và xác định khi nào hoàn tất. Sau đó xem xét danh sách kế toán cần đối chiếu và thông báo có hành động đi kèm; tránh tạo thêm danh sách nhập tay trùng bảng vận đơn. AI về sau có thể tóm tắt việc tồn, giải thích và đề xuất bước tiếp theo, dựa trên dữ liệu, quyền và quy tắc nghiệp vụ đã chốt.

**Phản hồi của chủ dự án:** Đồng ý định hướng, nhưng để giai đoạn sau; bây giờ tập trung sửa feedback của khách hàng trước. Phân công, phân quyền và các lỗi nghiệp vụ được xử lý theo feedback riêng, không gộp thành dự án nhắc việc/AI.

**Còn cần xác nhận khi xem xét đề xuất:** Điều kiện sinh/hoàn thành việc, thời hạn, mức ưu tiên, kênh và tần suất thông báo, quyền hành động của AI. Quyền nhập/sửa tiền và bằng chứng vẫn chờ H7 trong [USER_INQUIRY.md](USER_INQUIRY.md).


## Xác nhận 09.09.2026 — báo cáo và đánh giá nhân sự

- Phạm vi xem báo cáo: Staff xem bản thân; Leader xem team mình; Manager xem
  toàn bộ phòng ban mình; CEO/Admin xem toàn công ty. Đây là phạm vi báo cáo,
  không tự áp lại cho các nội dung nội bộ dùng chung toàn công ty.
- Tên hiển thị “Văn hoá” đổi thành **“Đánh giá nhân sự”**. Giữ module `culture`,
  URL và dữ liệu hiện tại; đổi tên không đồng nghĩa đã có cơ chế chấm điểm mới.
- Báo cáo muộn ảnh hưởng trực tiếp tới Đánh giá nhân sự. Chưa chốt hạn nộp,
  ngoại lệ, mức trừ và cách tác động tới sao/điểm hiện có; chưa triển khai tự trừ.


### 09.09.2026 — BC MKT trên KNERP, triển khai local

Đã hoàn thiện các chỉ tiêu xác định theo Excel, lịch sử lọc biểu mẫu/phòng ban,
khối Marketing trên Tổng quan và đổi tên Đánh giá nhân sự. Chi tiết và giới hạn
ở [BC MKT ERP](bc-mkt-erp.md). `KNJSC_PROBLEM.txt` đánh dấu `-> đã làm` riêng
phần hoàn thành; không đánh dấu cả nhóm 05/06 hoặc các mục hoãn.

Kiểm chứng: 13 test mới đạt (công thức, tổng, zero/missing, 4 cấp quyền trên
lịch sử/thống kê/Tổng quan/xuất, lọc và lỗi khối). Hồi quy reports, culture,
core/tests/test_giao_dien.py, core/tests/test_mau_dung_chung.py và crm/tests đạt.
Phát hiện rồi sửa vượt trần truy vấn do bộ lọc; test lịch sử/tổng hợp <=10 đạt.
Sau tách helper lịch sử và sửa comment lộ trên UI, chạy lại reports đạt.
Trình duyệt 1440px/390px đạt, không có console error được ghi nhận.
Chưa commit/push; chưa áp quy tắc báo cáo muộn hoặc mở mục thị trường.

### 10.09.2026 — Chín hạng mục lưới mới, thay quyết định lưu thủ công

Đã duyệt autosave, chọn hàng/màu xanh, hai chế độ, fs/c/bg, lịch sử và
đối chiếu conflict, Admin chọn Sale, thứ tự tạo tăng dần và số hàng từ 1.
Đã triển khai và kiểm chức năng trên database test: suite rộng 1.049 pass,
6 fixture skip được tách kiểm; 90 test tác động và E2E cuối đạt. Hiệu năng
lọc 300k còn chưa đạt; chạy bền dừng theo yêu cầu chủ dự án, để phiên sau
chạy lại đủ 30 phút. Không đổi H7/lưới cũ.
Xem [quyết định ADR-021](quyet-dinh/021-luoi-master-va-thong-ke-crm.md) và
[báo cáo chín hạng mục](kiem-chung-master-nine.md).

Phát hiện từ ma trận cuối 10.09: lọc Quốc gia trên 300.000 dòng còn p95
1.135ms (10 người)/1.340ms (20 người), vượt mục tiêu 1 giây; đọc khối và
lưu ô đạt mục tiêu ở bốn lượt ngắn. Giữ việc này ở phần hiệu năng chưa
nghiệm thu; không đổi nghiệp vụ lọc hoặc chia bảng để né phép đo.
Các lỗi kết nối lẻ vẫn được tính trong báo cáo, chưa khẳng định nguyên nhân.

### 11.09.2026 — Bàn điều hành Marketing–Sale–Vận đơn

Chủ dự án duyệt nâng trực tiếp `/thong-ke/` thành Bàn điều hành. Đã tách bộ điều
phối, bốn profile, insight và dữ liệu biểu đồ; mọi truy vấn bắt đầu từ manager
scope hiện có. Không thêm dependency, realtime, cache, worker hay bảng Sale.
Giao diện dùng SVG 2.5D tiết chế, bảng số liệu thay thế và tối đa ba nhận định.
Thêm cấu hình owner chỉ đổi cách trình bày cho Admin, không nâng quyền. KN ERP và
Trang chủ CRM chỉ thêm liên kết. Tiêu chí mới là AC-22.1–22.9; trạng thái kiểm
thực tế ghi tại test-log, không lấy nhãn hoàn thành thay cho số đo p95.
