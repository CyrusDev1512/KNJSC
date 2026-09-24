# Bảng việc — To do / In progress / Finished / Far Plan

## 24.09.2026 — ADR-041: bỏ & khôi phục báo cáo cấp dưới

**Finished local (nhánh `claude/xoa-khoi-phuc-bao-cao`, PR nháp):** Leader team/Manager bộ phận/Admin
bỏ được báo cáo cấp dưới (xoá mềm cả số liệu), Manager/Admin khôi phục ở trang "Đã bỏ"; Kế toán giữ
nguyên chỉ sửa. **To do:** chủ dự án duyệt PR, kéo về local check.

## 24.09.2026 — Ngày lên đầu bảng Vận đơn mới

**Finished local (nhánh `claude/ngay-len-dau-bang-van-don`, PR nháp):** Ngày (lên đơn) là cột
dữ liệu đầu tiên, nhóm ghim 5 cột; Ngày thanh toán giữ nguyên. **To do:** chủ dự án duyệt PR, phát hành VPS.

## 22.09.2026 (đêm) — Lọc theo cột ẩn vẫn chạy, kèm lời nhắc

**Finished local (nhánh `claude/loc-cot-an-co-nhac`, PR nháp):** TL-53 đóng — bộ lọc cột ẩn không còn
bị bỏ lặng lẽ; chip cảnh báo KN CRM, dòng nhắc KN ERP, tệp xuất theo đúng bộ lọc. AC-39.8.
**To do:** chủ dự án duyệt PR; phát hành VPS.

## 22.09.2026 (đêm) — Nợ kỹ thuật đợt 3

**Finished local:** khoá so trùng số điện thoại (TL-36, AC-36.8, migration 0016).
**To do:** chủ dự án xem PR; quyết riêng việc tra khách ở Lên đơn có theo khoá không.
**Far plan:** món 2 — chip nhắc khi lọc theo cột ẩn.

## 22.09.2026 — Bộ gom p95 thật của KN CRM từ log VPS

**Finished local:** `scripts/gom-p95-vps.py` + `app/tests/test_gom_p95.py` (13 bài đạt) — số đo đã nằm sẵn trên
VPS vì `CRM_REQUEST_METRICS` bật từ đầu, nên chỉ cần gom: ba nhóm theo ngưỡng ADR-016, p50/p95/p99, mười tuyến
chậm nhất kèm `db_ms` và số truy vấn, mã thoát 0/1/2. Chỉ đọc log, không chạm dữ liệu.
**To do (người có SSH):** chạy `--since 7d --json` trên VPS rồi điền vào [biên bản](kiem-chung-gom-p95-vps-20260922.md).
Tới giờ **vẫn chưa có con số p95 thật nào** — bộ gom mới là nửa việc.
**Far plan:** cắm vào cron hằng tuần; đặt `logging:` xoay vòng cho `compose.yml` **sau khi** đã gom xong lịch sử.

## 22.09.2026 (chiều) — Nợ kỹ thuật đợt 1

**Finished local:** xoá dữ liệu giả theo lô, có hạn chờ khoá và tiến độ (TL-43, AC-10.10).
**To do:** chủ dự án xem PR. **Far plan:** nguyên nhân gốc lần treo 17 phút.
## 19.09.2026 (đêm) — Bài đầu-cuối hành trình nhân viên

**Finished local:** `tests/e2e/test_hanh_trinh_nhan_vien.py` — một lượt qua lưới, hộp lọc cột, đổi vai, lên đơn,
lời nhắc khách; đã thử đưa lỗi trở lại hai lần đều đỏ.
**To do:** phát hành VPS. **Far plan:** thu gọn panel "Bộ lọc"; xem lại ngưỡng 50; ~~gom p95 từ log VPS~~ (bộ gom xong 22.09, mục trên).
## 19.09.2026 (18:47) — Phát hành gộp ADR-039 + Báo cáo tổng hợp + TL-46/47 + lọc cột lên VPS

**Finished VPS (18:44 19.09):** image `knjsc-app:72af235-gop` trên 5 service; backup kiểm phục hồi; migration `forms_builder 0015`;
hai domain 200, 0 lỗi. Bốn mục 19.09 bên dưới hết "To do: phát hành VPS". [Biên bản](kiem-chung-phat-hanh-vps-20260919-gop.md).
**To do (Admin):** bấm ẩn nhóm cột sản phẩm với cả công ty một lần, kiểm lưới / Excel / Bảng dữ liệu (Việc 5).
**To do (chủ dự án):** kiểm mục 7 hai đợt trên domain thật; tạo hồ sơ cho `admin`/`quantri`.
**To do (CLI):** `pytest` toàn bộ trên `72af235` khi có Docker.

## 19.09.2026 (tối) — Lọc cột và lời nhắc khách

**Finished local:** tự điền tên khách + cảnh báo đổi tên (AC-6.10); hộp lọc cột chọn công cụ theo số giá trị (AC-11.43); sửa gốc lỗi sót mục khi đổi cột (AC-11.42); hết trùng mã AC.
**To do:** phát hành VPS. **Far plan:** thu gọn panel "Bộ lọc"; xem lại ngưỡng 50.

## 19.09.2026 (chiều) — Hai lỗi chủ dự án báo

**Finished local:** tên khách lấy theo lần gõ mới nhất (AC-6.9); hộp lọc cột lấy lại nền, khung và cuộn sau khi đóng chú thích nuốt 24 luật (TL-46, AC-11.40).
**To do:** phát hành VPS. **Far plan:** TL-48 cách lọc cột có quá nhiều giá trị.

## 19.09.2026 — Ô danh tính mỗi người một dòng (AC-22.14, TL-45)

## 19.09.2026 — Tổng hợp nhóm theo ngày × nhân sự, mỗi người một hàng (AC-22.14, TL-45)

**Finished local:** cách xem Tổng hợp mỗi người một hàng trong ngày như ảnh mẫu, Doanh thu suy
ra theo cặp (ngày, marketer), Excel cùng cấu trúc; đảo ADR-035 quyết định 1. Thêm **khối theo ngày**:
dòng Tổng ngày và cột STT (AC-22.15); **tô màu chỉ tiêu** so với dòng Tổng (AC-22.16).
**To do:** phát hành VPS. **Far plan:** ngưỡng tuyệt đối từng chỉ tiêu và màn hình tự sửa ngưỡng.

## 19.09.2026 — Ẩn cột với cả công ty (ADR-039)

**Finished local:** `ColumnDef.is_hidden`, migration `forms_builder/0015`, hộp "Cột" có nút ẩn cho cả công ty + nút gộp cho nhóm cột sản phẩm, ba màn hình cùng lọc. Bài AC-39.1 → 39.7 đạt.
**To do:** phát hành VPS rồi Admin bấm ẩn nhóm cột sản phẩm một lần. **Far plan:** có nên ngừng sinh cột `sl_*` hẳn không.
## 19.09.2026 — Phát hành ADR-036 + bảy PTTT + ADR-037/038 + Báo cáo tổng hợp lên VPS

**Finished VPS (00:19 19.09):** image `knjsc-app:ea8942c-adr036` trên 5 service; backup kiểm phục hồi; 5 migration; xoá cứng
crmThuận + Vận đơn DB; 21 mã nhân sự mẫu; hai domain 200, 0 lỗi. [Biên bản](kiem-chung-phat-hanh-vps-20260919-adr036-mkt.md).
**To do (chủ dự án):** kiểm mục 7 trên domain thật với tài khoản thật; tạo hồ sơ cho `admin`/`quantri`; báo nhân viên (mục 8).
**To do (CLI):** `pytest -m "not cham"` toàn bộ trên `ea8942c` khi máy rảnh bộ nhớ.

## 18.09.2026 (tối, CLI) — Bố cục Báo cáo tổng hợp (A)

**Finished local:** bố cục theo bản vẽ (ba trạng thái bộ lọc, chip, ghim cột định danh, gộp Chọn nhanh và Tệp
của Codex, AC-22.13). Việc B bỏ vì Codex đã làm (ADR-037). Kiểm: `reports/tests` (kèm hai bài Chromium mới) + `core/tests/test_giao_dien.py` + `tests/test_truy_vet.py` trên đầu nhánh `3748ea9` của Codex: 0 đỏ sau khi sửa hai khẳng định (`test_activity` so header cột định danh, chip Nhân sự theo nhãn mã của ADR-037); bộ đếm docs/06 225 tiêu chí, 212 tự động, 188 có bài kiểm; Chromium 8020 sau gộp (`storage/bo-cuc-bao-cao/sau-gop-*.png`): 1440 mở, 390 đóng, chip đủ, 5 nút Chọn nhanh, nhãn `mã · họ tên` của Codex, không tràn ngang, không lỗi JS.
[Biên bản](kiem-chung-bo-cuc-bao-cao-tong-hop-20260918.md). ~~**To do:** đi cùng đợt phát hành tối 18.09 của Codex.~~ Đã phát hành 19.09 (mục trên).

## 18.09.2026 (tối) — Bảy PTTT theo sheet Vận đơn

**Finished local:** `ACTIVE_PAYMENT_METHODS` 7 loại, migration `orders/0010`, AC-11.9 221/221. ~~**To do:** phát hành cùng ADR-036.~~ Đã phát hành 19.09 (mục trên).

## 18.09.2026 (chiều) — Một bảng vận đơn duy nhất (ADR-036)

**Đã phát hành VPS** (xác nhận 19.09, không có biên bản phát hành): `van_don` là bảng duy nhất mang profile Vận đơn + cột Trùng;
Bảng nhận đơn bỏ; lệnh xoá cứng hai bảng cũ; dòng không chi tiết tạo được. Bài AC-36.x đạt.
[Biên bản](kiem-chung-mot-bang-van-don-20260918.md).
~~**To do (CLI máy chủ dự án):** backup → phát hành → `migrate` 0014 → `tao_bang_van_don` →
`xoa_bang_van_don_cu` → kiểm Chrome.~~ Đã phát hành 19.09 (mục trên), kiểm Chrome chờ chủ dự án. **Far plan:** khối Đối soát kế toán, Black list, 7 trạng thái
vận chuyển theo sheet Vận đơn của "Quản trị nội bộ" — chờ chốt.

## 18.09.2026 (chiều) — TL-41 cột Đơn vị tiền

**Finished local:** `configure_erp_reports` bổ sung USD/CAD/PHP vào cột có sẵn; AC-22.12 đạt.
**Finished VPS (chiều 18.09):** sửa tay cột trước, rồi image `knjsc-app:5b68dce-tl41` trên 5 service, backup
kiểm phục hồi, không migration. [Biên bản](kiem-chung-phat-hanh-vps-20260918-tl41.md).
**To do:** chủ dự án nộp thử báo cáo Marketing với Quốc gia Canada trên domain thật.

## 18.09.2026 — Lưới như Excel; Quốc gia trống → tiền trống

**Finished local:** bấm chỉ chọn ô, gõ là nhập, Ctrl+A/Delete tác động lên
lưới; xoá Quốc gia được, dòng có tiền hỏi xác nhận. Bài AC-33.8 và Chromium đạt.
[Biên bản](kiem-chung-luoi-excel-quoc-gia-trong-20260918.md).
**Finished VPS (chiều 18.09):** image `knjsc-app:5b7922f-excel` trên 5 service, backup kiểm phục hồi, không
migration; Chromium domain thật với tài khoản Vận đơn tạm: bấm chọn, gõ nhập, Ctrl+A 407 ô, xoá vùng Quốc gia
hỏi xác nhận rồi lưu, tiền giữ. [Biên bản](kiem-chung-phat-hanh-vps-20260918-excel.md).
**To do:** TL-41 — quyết định cách sửa cột Đơn vị tiền (VND) của bảng báo cáo 15.09; kiểm Sale/CSKH domain thật.
## 18.09.2026 — Phát hành bốn góp ý lên VPS

**Finished VPS:** image `knjsc-app:0d970f8-gopy` trên 5 service; backup + diễn tập trên bản sao DB thật; Vận đơn mới
(`van_don`) được bổ sung cấu trúc và là bảng nhận đơn duy nhất; Chrome domain thật đạt.
[Biên bản](kiem-chung-phat-hanh-vps-20260918.md). **To do:** người dùng lên một đơn thật để xác nhận vào Vận đơn mới;
kiểm vai Vận đơn/Sale/CSKH khi có tài khoản kiểm.

## 18.09.2026 — Bốn góp ý sau ADR-033

**Finished local:** 1.000 dòng trống sẵn và tạo dòng không tải lại (AC-11.37); bảng nhận đơn
hiện đủ ba bảng vận đơn (ADR-034, AC-11.39); cột ghim đứng đầu, bôi đen đúng (AC-11.38); báo
cáo Tổng hợp thêm cột Nhân sự/Leader gộp tên theo ngày, 100 dòng/trang, bảng gọn (ADR-035,
AC-22.10, 22.11). `reports/tests` 133 đạt, hai bài Chromium mới đạt, hồi quy `crm/tests orders/tests forms_builder/tests core` 1.261 bài, 0 đỏ (13 bỏ qua do thiếu môi trường).
[Biên bản](kiem-chung-gop-y-sau-adr033-20260918.md).
Chiều 18.09: sửa giật khi gõ rồi Enter (poll tự lưu + thanh thông báo, AC-11.40); hoàn lại cấu trúc báo cáo
(mỗi ngày một dòng, hai cột gộp tên); `van_don` thành bảng duy nhất của Lên đơn (nâng cấp cấu trúc, local đã chọn).
~~**To do:** phát hành VPS.~~ Đã phát hành 18.09 (mục trên).

## 17.09.2026 — Phát hành ADR-033 lên VPS

**Finished VPS 23:26:** image `knjsc-app:9949062-adr033` (build tại VPS, `INSTALL_DEV=0`)
trên 5 service; backup restore thật vào DB tạm khớp số dòng; `migrate` áp
`forms_builder.0013` + `reports.0003`; `check --deploy` sạch; hai domain 200; Chrome
domain thật bằng admin đạt (lưới, Báo cáo tổng hợp bản mới, đăng nhập chung).
`bao_cao_mkt` không thiếu `loai_tien`; chỉ `bao_cao_van_don_ngay` xuất hiện rỗng.
Cờ `CRM_OPT_*` giữ 0. [Biên bản](kiem-chung-phat-hanh-vps-20260917.md).
**To do:** kiểm trên VPS bằng tài khoản Vận đơn, Sale x2, CSKH khi chủ dự án cấp tệp
tài khoản kiểm; quyết giữ hay xoá `app/org/management/` chưa theo dõi.

## 17.09.2026 — Tôi / Toàn bộ và quyền sửa Vận đơn (ADR-033)

**Finished local, đã lên VPS 23:26 (mục trên):** nhân viên Vận đơn xem và sửa toàn bảng; nút Tôi /
Toàn bộ theo cột phụ trách, nhớ trên trình duyệt; lưới luôn chỉnh sửa; xoá Chế độ
xem bảng (ADR-026) và trường `delivery_view_all` (migration 0013). Sau rebase lên đợt
sửa bài kiểm của Codex: toàn bộ suite Python 0 đỏ. Chromium 1440/390 đạt.
[Biên bản](kiem-chung-pham-vi-toi-toan-bo-20260917.md).
~~**To do:** phát hành VPS (máy chủ dự án, chạy `migrate` 0013).~~ Đã phát hành 17.09 23:26.

## 16.09.2026 — Tối ưu cuộn và cờ: đã phát hành phần đã kiểm

Code/E2E/hồi quy và tải ngắn đã kiểm; đã dừng kiểm bền theo yêu cầu sau 14,71 phút đo; chưa đủ 60 phút. Bảy cờ tắt.
READ/SYNC chưa đạt thao tác dưới tải, RENDER chưa chứng minh lợi ích mới.
Đã push/phát hành VPS 0907cdd; giữ nợ 300k của task khác. [Chi tiết](kiem-chung-co-toi-uu-20260916.md).

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

## 16.09.2026 — Gom nhảy xa

**Finished local:** chỉ tải vùng đích sau 80 ms yên cuộn; tải trước phục hồi
khi cuộn ổn định. Chrome 1440/390, sở hữu request và E2E DB thật đạt.
48→1 request trong chuỗi nhảy mô phỏng; không gọi là tăng tốc lần nhảy đơn.
Chưa push/VPS. [Chi tiết](kiem-chung-cuon-luoi-20260916.md).

## 16.09.2026 — Cuộn cache và tải trước theo hướng

**Finished local trong phép đo kiểm soát:** giữ DOM khi chỉ cuộn, đón hai
khối, giữ trần cache và xử lý lỗi/quyền. Functional 110 đạt; Chrome 1440/390
và tương thích cờ renderer đạt. Chưa push/VPS; còn đo mạng/backend thật khi
phát hành. [Bằng chứng](kiem-chung-cuon-luoi-20260916.md).

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

## 16.09.2026 — Sửa màu cột ghim

**Finished VPS:** CSS vùng giấy thống nhất ở sáng/tối; Chrome thật 1440/390 đạt.
[Kiểm chứng](kiem-chung-mau-cot-ghim-20260916.md). Chưa commit/push.

## 16.09.2026 — Bỏ trường Đơn vị phụ

**Finished local:** bỏ trên Lên đơn/Xem đơn gốc; không xóa dữ liệu cũ.
36 test và Chrome 1440/390 đạt. Chưa commit/push/VPS.

## 16.09.2026 — Tiền theo quốc gia và PTTT

**Finished local:** cố định tiền theo quốc gia, xác nhận giữ số tiền khi đổi,
chọn Zelle/PayPal dùng chung form/lưới. 15 test mới và Chrome 1440/390 đạt;
hồi quy có ba lỗi nền được đối chứng riêng. Chưa commit/push/VPS.
[Kiểm chứng](kiem-chung-tien-theo-quoc-gia-20260916.md).

## 16.09.2026 — Báo cáo ERP

**Local đã có bản xem thử; toàn tác vụ In progress:** lọc nhân sự/team,
kèm nút ẩn/hiện bộ lọc và toàn màn hình bảng (đã kiểm desktop/mobile),
kẻ bảng, báo cáo ngày Vận đơn và 36 mẫu lịch sử đã kiểm. Còn tái hiện/sửa
404 thêm sản phẩm trên domain thật. Chưa commit/push/VPS.
[Bằng chứng](kiem-chung-bao-cao-erp-20260916.md).

## 15.09.2026 — Vận đơn DB bị vô hiệu trong chọn bảng

**Finished VPS cf51ad2:** command/service chuẩn bị bảng đã có placeholder; kiểm
local 87 test + Chrome hai kích thước đạt. [Chi tiết](kiem-chung-chuan-bi-bang-nhan-don-20260915.md).

## 15.09.2026 — Bàn giao tối ưu lưới cho PC nhà

**To do:** đã chọn phương án 1; chưa sửa lưới hoặc tạo “Vận đơn optimize”.
[Daily tasks](daily-tasks.md) là điểm đọc tiếp: 7 hạng mục, phạm vi local,
kiểm chứng, lỗi nhập 3.333 dòng và ranh giới đối soát đang tắt.
Các mục “chưa push” của mẫu Excel bên dưới là nhật ký tại thời điểm kiểm;
code mẫu Excel đã có trên GitHub qua `c41d8f0` và `f971683`.

## 15.09.2026 — Phiên đăng nhập chung

**Finished VPS — cdc1a45; 16 ca Chrome test và 4 ca domain thật đạt.** Không có thay đổi
quyền nghiệp vụ. Hồi quy có một lỗi CSS nền riêng; chưa sửa ở đợt này.
[Kiểm chứng](kiem-chung-dang-nhap-chung-20260915.md).

## 15.09.2026 — Báo cáo Marketing/Sale mẫu trên domain thật

**Finished VPS:** hai bảng mỗi bảng 50 dòng, phân đúng 5 team/10 nhân sự mẫu;
DB và giao diện đã kiểm. Không tạo DailyReport đã nộp, tài khoản mẫu khóa đăng
nhập; không restart dịch vụ. [Chi tiết](kiem-chung-bao-cao-mau-vps-20260915.md).

## 15.09.2026 — Sửa lỗi mẫu nhập đã được duyệt

**Finished local, chờ đối chiếu file của chủ dự án:** preview đúng cột, mẫu bỏ
cột chỉ xuất và căn ô, báo lỗi sớm, chặn nhập trùng. 30 test đạt; UI ba mẫu,
tệp lỗi/trùng và 10.000 dòng đạt. Thay thế trạng thái “Còn việc” ngay bên dưới.
Chưa kiểm Microsoft Excel/chưa VPS. [Chi tiết](kiem-chung-mau-nhap-van-don-20260915.md).

## 15.09.2026 — Kiểm người dùng thật cho mẫu nhập

**Còn việc:** tải/nhập hợp lệ và 10.000 dòng đạt, nhưng preview lệch cột,
mẫu có cột không nhận nhập, báo lỗi muộn và nhập lại tạo trùng. Phát hiện
được ghi nhận, chưa thay đổi nghiệp vụ. [Chi tiết](kiem-chung-mau-nhap-van-don-20260915.md).

## 15.09.2026 — Tải mẫu Excel vận đơn

**Finished local:** nút Tải mẫu Excel đúng từng bảng, bỏ nhãn Sửa; kiểm nhập lại và quyền đạt. Chưa push/VPS. [Kiểm chứng](kiem-chung-mau-nhap-van-don-20260915.md).

## 15.09.2026 — Chọn bảng nhận đơn tại CRM (local)

Admin chọn đích nhận đơn mới; bảng/đơn cũ giữ nguyên. Đã áp migration 0012 local, chưa đổi đích mặc định, chưa commit/push/VPS. Sau sửa cuối 67 test liên quan đạt; Chrome 1440/390, hai ca 30 Sale đồng thời và migration xuôi/ngược đạt. [Kết quả và giới hạn](kiem-chung-bang-nhan-don-20260915.md) · [ADR-029](quyet-dinh/029-bang-nhan-don-crm.md).


## 15.09.2026 — Sửa sidebar CRM thu gọn

**Finished:** căn giữa logo và icon nhóm; Chrome local đạt, VPS đã nhận CSS
hotfix qua HTTPS. [Bằng chứng và giới hạn](kiem-chung-crm-sidebar-20260915.md).

## 15.09.2026 — Mở rộng giao diện KN ERP trong tab

**Finished local, chờ chủ dự án xem:** hai nút Nền/Mở rộng đã đổi thành icon có
nhãn hỗ trợ. ERP tràn sát viewport và không còn ảnh nền khi bật; trình duyệt vẫn
giữ thanh địa chỉ và các tab vì nút không gọi Fullscreen API. Esc, desktop 1440px
và mobile 390px đều đạt. Lựa chọn mở rộng được giữ qua tải lại, chuyển trang và
đồng bộ giữa các tab ERP cùng origin. Đã triển khai VPS; image hiện hành
`knjsc-app:8dead1b` chứa commit chức năng `2ea5ab2`. Không merge `main`.

## 14.09.2026 — Toàn màn hình ERP, sắp lại Vận đơn và tạm khóa Chứng từ

**Đã phát hành nhánh riêng lên VPS, chờ nghiệm thu người dùng:** chức năng, dữ liệu metadata và
Chrome 1440/390 sáng/tối đã áp dụng; database local và VPS được sao lưu trước. Hai bảng giữ
nguyên số dòng/ID/quyền; Chứng từ mặc định tắt nhưng kiểm thử cờ bật vẫn giữ luồng
cũ. VPS đang chạy image `knjsc-app:97741e4`; HTTPS/check/log sau triển khai đạt.
Không merge `main`. [Kiểm chứng](kiem-chung-erp-vandon-bill-20260914.md).
Full suite cuối: **2.332 passed, 15 failed nền, 31 skipped, 2 xfailed**.

## 14.09.2026 — Hợp nhất CRM-UPDATE và Solar UI

**Finished trong phạm vi nhánh:** nghiệp vụ/quyền/lưới master của CRM-UPDATE đã
được hợp nhất với trình bày Solar. Chrome chức năng và bố cục đạt; full suite
2.329 passed, còn 15 lỗi nền đã đối chiếu. Chờ chủ dự án nghiệm thu trước mọi
quyết định với `main` hoặc nhánh cũ. [Bằng chứng](kiem-chung-crm-update-solar-ui-20260914.md).

## 14.09.2026 — Tích hợp phần local vào CRM-UPDATE

Đã khôi phục ERP từ stash, ghép sửa Thống kê và chế độ xem Vận đơn; Solarpunk giữ riêng. Functional toàn bộ: 2327 đạt, 17 lỗi đều tái hiện trên nền 9bac840, 31 skip/2 xfail. Chrome định danh, bốn cấp quyền, Thống kê và đổi chế độ xem đạt tại 1440/390. Không kích hoạt runtime chính hoặc chạy lại kiểm tải toàn CRM. [Bằng chứng và giới hạn](kiem-chung-tich-hop-local-20260914.md).


**Finished trong phạm vi kiểm chứng — 14.09, CRM-UPDATE:** lưới chung,
xóa/khôi phục bảng, tương phản và truy vấn phạm vi đã kiểm functional/Chrome;
ma trận tải và bài bền 30 phút đạt. Bốn lỗi kiểm thử nền/11 skip giữ riêng.
Chờ chủ dự án duyệt diff/kích hoạt; worktree riêng, local vẫn nhánh fix,
chưa commit/push. Tạo bảng trắng/duplicate tiếp tục hoãn.
[Bằng chứng](kiem-chung-crm-update-20260912.md).

**12.09, 17:20 — Chủ dự án yêu cầu test trước:** đã chuyển checkout chính sang `CRM-UPDATE`, cập nhật local 8020/8021 và worker cùng code; không seed/migrate, chưa commit/push. Marketing/Sale đã xác nhận dùng lưới mới. Functional 1.130 passed, 4 lỗi nền, 11 skipped; Chrome chức năng đạt. Kiểm tải tạm dừng: bản cuối mới đủ 100k/10, chưa nghiệm thu toàn chiến dịch. [Kết quả và phần còn lại](kiem-chung-crm-update-20260912.md).

**12.09 — CRM-UPDATE đang kiểm local:** lưới chung Marketing/Sale/Vận đơn cũ,
xóa mềm/khôi phục bảng; giữ Vận đơn mới, ERP và dữ liệu. Đang chạy ma trận tải,
chưa nghiệm thu toàn chiến dịch; tạo bảng trắng/duplicate cấu trúc hoãn.
[Biên bản](kiem-chung-crm-update-20260912.md) · [ADR-027](quyet-dinh/027-crm-update-luoi-chung-va-vong-doi-bang.md).


> Cập nhật 12.09.2026: theo yêu cầu chủ dự án, đã chuyển nhánh codex/chung-tu-thanh-toan về checkout chính C:/KNJSC/KNJSC và kích hoạt app local 8021. Đã áp dụng orders 0007, org 0004; không chạy seed. Các mô tả chưa kích hoạt bên dưới ghi trạng thái bàn giao trước bước này. Chưa commit/push; bản sao checkout cũ giữ nguyên nội dung, ở detached HEAD.

**Chờ kiểm tra trên môi trường sử dụng — Chứng từ thanh toán (12.09):** có mã,
functional/migration và Chrome với fixture 10k; giữ bốn lỗi nền/skip riêng.
Chưa kích hoạt trên app 8021, chưa commit/push. H7 chỉ chốt phần chứng từ,
không đóng quyền nhập tiền và đối soát. [Biên bản](kiem-chung-chung-tu-thanh-toan-20260912.md).
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

**Finished local — Trùng mã đơn khi nhiều Sale lưu (11.09):** nhánh
`fix/trung-ma-don-dong-thoi`/`a81decd`; service khóa PG theo DDMM, chờ tối đa
5s và giữ giao dịch đơn–Vận đơn. Functional/Chrome 1440/390 đạt; hỗn hợp
30 Sale + 10 Vận đơn đủ thời lượng, 361 đơn đúng; đợt dồn 30/30, không
timeout. Kiểm tương thích READ/SYNC/RECEIPTS/RENDER đạt. Chưa commit/push/merge;
các việc truy vấn/render lưới và lỗi nền vẫn giữ trạng thái riêng.
[Biên bản](kiem-chung-trung-ma-don-20260911.md).

**In progress / chờ nghiệm thu — CRM-Optimization (11.09):** mã sau cờ tắt đã có;
đã đo đủ trước/sau 100k/300k × 10/20 và bài bền cấu hình 30 phút. Render/cold
Thống kê, backlog xuất và tăng RSS app còn cần cải thiện/điều tra. Không suy nguyên nhân toàn bộ
16 lỗi lịch sử; chưa kết luận năng lực VPS. [Kiểm chứng](kiem-chung-crm-optimization-20260911.md).

**11.09.2026 — Ba lựa chọn Lên đơn bắt buộc chọn rõ:** Quốc gia/Loại tiền/PTTT mặc định rỗng, chọn hợp lệ mới lưu; đơn kế tiếp trở lại rỗng. 105 test đạt, Chrome 1440/390 đạt, trần 10 truy vấn giữ đạt; không migration/dependency, chưa commit/push. [Bằng chứng bổ sung](kiem-chung-len-don-gio-admin-20260911.md).


**11.09 — Cột ghim Vận đơn mới:** triển khai và hồi quy tự động đã xong;
100k/300k lệch 0 px, cache 10, không tăng request. Còn nghiệm thu thủ công
zoom trình duyệt thật/trackpad; chi phí render tăng nhẹ được ghi rõ tại
[biên bản](kiem-chung-ghim-cot-20260911.md). Không gộp với lỗi API trước đó.

**11.09.2026 — Bổ sung giờ lưu và Admin tự đứng đơn (thay quyết định chọn Sale):** Ngày giờ cập nhật HH:mm trên form, thông báo lấy timestamp thực tế đã lưu; bỏ dropdown, Admin/Sale tự đứng bằng mã đăng nhập. Admin thử nghiệm chưa thuộc Sale dùng Sale/team trống, giữ hồ sơ. 117 test đạt; Chrome 1440/390 đạt; kiểm tải đọc 10/20 Admin: 4.782 request đo/0 lỗi, p95 cao nhất 76,38 ms trên fixture nhỏ. Không migration mới, chưa commit/push. [Kiểm chứng và giới hạn](kiem-chung-len-don-gio-admin-20260911.md).


**11.09.2026 — Ngày/đơn vị/mã nhân viên khi lên đơn:** đã kiểm chứng local: Ngày Việt Nam chỉ đọc; chọn hộp/cái/chiếc/túi từng sản phẩm, snapshot trên đơn/vận đơn; mã đăng nhập cho định danh nghiệp vụ và lịch sử. Migration 0006 đã kiểm xuôi/ngược DB test và áp dụng xuôi local. Hồi quy 984 đạt/2 lỗi giao diện thống kê có sẵn; lượt focused cuối 72 đạt; Chrome 1440/390 đạt; Locust đọc 10/20 đạt 4.618 request/0 lỗi. Chống lặp hoãn, không kết luận năng lực toàn CRM. [Bằng chứng và giới hạn](kiem-chung-len-don-20260911.md). Chưa commit/push.


**11.09.2026 — Điều hướng ERP/thư viện/Lên đơn CRM:** đã triển khai local theo ADR-023. Giữ Bảng dữ liệu ERP; sửa Biểu mẫu thiếu người tạo, gộp hai tab đúng quyền; chuyển nhập đơn và xem đơn gốc sang CRM. Kiểm thử, số đo và giới hạn tại [báo cáo bàn giao](kiem-chung-erp-hub-20260911.md). Chưa commit/push.

**11.09 — Lưới Vận đơn mới:** sửa Admin/nhập trong ô đã kiểm Chrome/E2E;
chạy bền snapshot 7449e73 đã đủ 30 phút; còn 16 lỗi đọc/22.460 request và
lọc Quốc gia p95 1,35s chưa đạt. Hai bài rà giao diện Thống kê
có lỗi từ trước, chưa xử lý trong tác vụ lưới. Chi tiết và giới hạn:
[kiểm chứng 11.09](kiem-chung-master-admin-20260911.md).

Bản nhìn theo cột của `backlog.md`. `backlog.md` vẫn là nơi ghi **vì sao** (quyết
định Q, lỗ hổng K, nhật ký); tệp này chỉ trả lời **đang ở cột nào**. Lỗi cụ thể
kèm mức nghiêm trọng, chỗ sai, blocker và ảnh hưởng nằm ở `test-log.md`; ở đây
chỉ tham chiếu mã `TL-xx`.

Cập nhật: 16.09.2026. Ai làm xong việc nào thì kéo dòng đó sang cột kế tiếp
trong cùng lượt sửa mã, không để dồn.

Mức ưu tiên: **P0** chặn nghiệm thu hoặc mất/lộ dữ liệu · **P1** người dùng
gặp hằng ngày · **P2** khó chịu, có đường vòng · **P3** khi rảnh.

---

## To do

Xếp theo thứ tự nên làm. Mỗi dòng một PR nhỏ, có ảnh trước/sau hoặc bài kiểm.

| Ưu tiên | Việc | Liên quan | Nhánh đích | Ghi chú |
|---|---|---|---|---|
| P0 | Chặn Manager bộ phận khác tự cấp quyền Sửa qua màn Cấp quyền / Thu quyền | TL-01 | `main` | Lộ quyền; bài kiểm phải có chiều bị từ chối |
| P0 | Hết phiên 60 phút: mọi yêu cầu HTMX/fetch phải về màn đăng nhập, không báo "Đã lưu" | TL-02, TL-18 | `main` | Mất dữ liệu âm thầm; cùng gốc với "trang đăng nhập rơi vào ô" |
| P0 | Số ≥ 3 chữ số lẻ bị nhân nghìn khi Enter, dán, kéo điền, hoàn tác | TL-03 | `main` | Sai dữ liệu tiền âm thầm |
| P0 | Lọc khoảng cột tiền/ngày với chuỗi lạ trả 500 | TL-04 | `main` | Trang trắng |
| P0 | Thanh trên báo "Đã lưu" khi máy chủ trả 400; lời báo lỗi bị CSS giấu | TL-19, TL-20 | `main` | K28 — anh/chị gặp trong video 07.09 |
| P0 | PR #21: làm lại giao dịch sau deadlock mất dữ liệu; job tính lại kẹt RUNNING làm lưới ngừng cập nhật | TL-22, TL-23 | `claude/kiem-tai-kn-crm` | **PR #21 không gộp cho tới khi xong hai dòng này** |
| P1 | Cột Trùng có tác dụng: có ở Vận đơn DB, chuẩn hoá số điện thoại, đếm cả lịch sử, bấm để xem, lọc và tô màu | TL-35, TL-36 | `main` | Chờ anh/chị chốt 1 trong các ý ở backlog 16.09 |
| P1 | Tiêu đề bảng ngoài vận đơn màu vàng → xanh; ô trắng; chỉ ô cảnh báo mới vàng/đỏ | TL-21 | `main` | K28; yêu cầu gốc của anh/chị |
| P1 | Khôi phục dòng bỏ qua phạm vi quyền | TL-05 | `main` | Quy tắc 11 |
| P1 | Dòng trống / ô sửa kẹt sau 403/500, tự cập nhật dừng | TL-06 | `main` | |
| P1 | Sau khi chính mình lưu, lưới tự nạp lại và báo "Có dữ liệu mới"; dòng mới không khớp bộ lọc biến mất | TL-08 | `main` | |
| P1 | Sắp xếp không ổn định giữa các trang | TL-09 | `main` | |
| P1 | Cột tiền không mang nhãn Doanh thu sắp xếp và lọc theo chuỗi | TL-10 | `main` | |
| P1 | Màn Sửa cột cho bỏ cột hệ thống của bảng vận đơn | TL-13 | `main` | |
| P1 | Nghiệm thu bấm tay theo `docs/07` một đợt (V4, V5) | — | — | Việc của anh/chị, sau khi các P0 xong |
| P2 | Hoàn tác ghi đè sửa đổi của người khác không cảnh báo | TL-07 | `main` | |
| P2 | Trang chủ và trang chọn bảng đếm cả dòng ngoài phạm vi và dòng đã xoá | TL-11 | `main` | |
| P2 | Xoá 2.000 dòng tốn ~6.000 truy vấn | TL-12 | `main` | |
| P2 | Dán vượt trang tạo dòng mới thay vì ghi tiếp | TL-14 | `main` | |
| P2 | Định dạng ô ngoài phạm vi bị bỏ qua lặng lẽ thay vì 403 | TL-15 | `main` | Quy tắc 8 |
| P2 | Sửa một ô ghi cả dòng; sửa một ô không vẽ lại cột tính sẵn | TL-16, TL-17 | `main` | |
| P2 | Thêm/sửa cột tính sẵn trên bảng lớn chặn request (153 s ở 100.000 dòng) | TL-34 | `main` | PR #21 đã sửa; chỉ còn nếu PR #21 không gộp |
| P2 | PR #21: chỉ luu-o có làm lại khi deadlock; không gộp job tính lại; lỗi một lô không dừng các lô còn lại; `do_hieu_nang` đo tính lại không ghi; docstring lệch mã | TL-24 → TL-28, TL-31, TL-32 | `claude/kiem-tai-kn-crm` | Sau TL-22/23 |
| P2 | Chạy `scripts/kiem-tai-kn-crm.*` trên máy anh/chị và máy chủ thật, ghi số vào `docs/06` | K27 | — | Sau khi PR #21 gộp |
| P3 | Tệp tĩnh không được phục vụ khi chạy gunicorn (không nginx, không whitenoise) | TL-29 | `main` | Giai đoạn 8 sẽ có nginx |
| P3 | Script kiểm tải chạy `du_lieu_mau` nên đặt lại mật khẩu 12 tài khoản mẫu | TL-30 | `claude/kiem-tai-kn-crm` | |
| P3 | `tests/test_hieu_nang.py` vẫn xfail vì ngân sách 10 truy vấn | K24, TL-33 | `main` | Sau K27 lưới còn 13 |

## In progress

| Việc | Ở đâu | Trạng thái | Chặn bởi |
|---|---|---|---|
| Kiểm tải KN CRM 100 nghìn khách / 100 người (ADR-016) | PR #21 nháp, nhánh `claude/kiem-tai-kn-crm`, 5 commit | Đo xong, số ĐẠT trên máy ảo; **rà lại phát hiện TL-22 (mất dữ liệu) và TL-23** | Không gộp cho tới khi TL-22, TL-23 xong; anh/chị chốt Q67 "giờ chưa phải lúc tối ưu" |
| Bảng việc và nhật ký kiểm thử này | nhánh `claude/backlog-testlog` | Tạo 07.09 | — |

## Finished

- **11.09.2026 — Bàn điều hành KN CRM:** tổng hợp tối đa ba nguồn và chuyên sâu
  mọi bảng theo profile Marketing/Sale/Vận đơn/Chung; insight có bằng chứng và
  link xử lý, biểu đồ SVG, tách tiền tệ, giữ scope và tương thích thống kê cũ.
  [ADR-022](quyet-dinh/022-ban-dieu-hanh-kn-crm.md), AC-22.1–22.9. Hồi quy 159
  bài đạt; p95 20k Sale/100k Vận đơn/300k Vận đơn/tổng hợp lần lượt
  89,07/333,72/893,26/733,64ms; kiểm trình duyệt đủ ma trận trong test-log.

- **11.09.2026 — `vandonmoi`:** hoàn thiện đúng 10.000 dòng mẫu
  `MAU-20260910-*` trong Vận đơn mới bằng management command tái lập theo seed;
  giữ 500 danh tính cũ, thêm 9.500 dòng, chi tiết sản phẩm và phân công. Sửa ghi
  chú lỗi `?`, làm rõ ba cột ghim và toolbar theo phạm vi riêng của bảng mới.

- **09.09.2026 — `codex/sua-feedback`:** phân công Vận đơn mới và phạm vi theo
  tài khoản; bộ lọc nhanh/sản phẩm/thị trường/Marketing; xuất ngày/bộ lọc có
  mã nhân viên và kiểm quyền file nền. [ADR-020](quyet-dinh/020-phan-cong-loc-xuat-van-don-moi.md),
  AC-20.1 đến AC-20.7. H7 chưa làm; chưa commit/push trong tác vụ này.

Mọi thứ đã vào `main` (ở `3ab19a5`) hoặc đã xong trên nhánh. Số giai đoạn theo
`dashboard-tien-do.html`.

| Giai đoạn | Việc | PR | Quyết định |
|---|---|---|---|
| 0 → 6 | Nền tảng: đăng nhập, phân quyền ba cấp, bảng động, biểu mẫu, báo cáo, lên đơn, nhập/xuất Excel | — | ADR-001 → 008 |
| 7A | Nhập tệp bốn bước có xem trước, xuất kèm bộ lọc, tệp lớn chạy nền giữ 24 giờ | — | |
| 7B | Sao lưu `pg_dump` 02:00, giữ 30 bản, phục hồi bằng `scripts/restore.sh` | — | |
| 7C | Bảng tính vận đơn theo tệp thật, dịch vụ `bangtinh` 8021 | — | ADR-009 |
| 7D | Kiểm thử chín tầng: Playwright, Locust 50 người, 50.000 dòng, ma trận 45 ô, `docs/07` | — | |
| 7E | Bảng tính cho mọi bảng, viền ô, dòng trống, định dạng ô, thư mục | #4 | ADR-010 |
| 7F | Lưới như KN Demo: chọn vùng, dán, kéo điền, hoàn tác, chuột phải, 40 màu, hộp lọc, tự cập nhật | #5 | ADR-011 |
| 7G | KN CRM là app riêng, cây Bộ phận ▸ Quý ▸ Tháng | #5 | ADR-012 |
| 7H | Ô chọn có "Thêm mới…", màu cột, ngưỡng cảnh báo | #11 | ADR-013 |
| 7I | Bảng dữ liệu KN ERP chỉ để xem | #15 → #18 | ADR-014 |
| 7J | KN CRM có sidebar theo Teeze, trang chủ tổng quan, Leader như Manager, tạo bảng/nhập tệp/cấp quyền trong KN CRM, logo tự vẽ | #19 | ADR-015 |
| — | `KN JSC.bat` tự kéo mã, migrate khi mã đổi, báo rõ khi kéo thất bại | #6 → #10, #12 | |
| 7K (đo) | `seed_perf` 100.000 dòng + bảng Sale có cột tính sẵn; `do_hieu_nang` 25 đường kèm EXPLAIN; Locust 100 người bốn vai tự chấm; `scripts/kiem-tai-kn-crm.*` | #21 (nháp) | ADR-016 |
| 7K (sửa) | Ô lưới dựng bằng Python 638 → 154 ms; cột Trùng theo trang; `moi-nhat` không đếm dòng; `bulk_save` bằng VALUES; tính lại cột chạy nền 153 s → 19,6 s; 100 người p95 11 s → 0,85 s | #21 (nháp) | ADR-016 — **chưa gộp**, xem In progress |
| 7L | Vận đơn mới theo CRM Tân: hai bảng độc lập, ERP/CRM cùng luồng, chi tiết tiền từng sản phẩm, thống kê; 25 bài mới, toàn bộ hồi quy, migration hai chiều và giao diện desktop/mobile đều đạt | — | ADR-018 |
| 7L.1 | 10.000 vận đơn mẫu Canada/CAD có chi tiết, thanh toán, phân công; vùng ba cột nhận diện ghim rõ trên lưới | — | Nhánh `vandonmoi` · 11.09.2026 |
| 7M | Bàn điều hành KN CRM theo nguồn Marketing/Sale/Vận đơn/Chung; KNERP giữ báo cáo và thêm liên kết | — | ADR-022 |
| — | Rà lại toàn bộ KN CRM trên `main` và trên PR #21, ghi thành `test-log.md` | nhánh này | |

## Far Plan

Chưa tới lượt, không làm khi chưa có quyết định mới của anh/chị.

| Mã | Ý tưởng | Điều kiện để bắt đầu |
|---|---|---|
| S13 | Lưới KN CRM trả JSON, JS thuần vẽ ô, cuộn ảo — trang 20 KB thay vì 300 KB | Q67: chỉ khi máy thật đo đỏ hoặc khi làm S10 |
| S14 | Máy chủ đẩy sự kiện (SSE) thay cho 100 tab hỏi mỗi 8 giây | Cùng lúc với S13 |
| S15 | Cột tính sẵn để Postgres tính, không đi qua Python và chỉ mục GIN | Đụng cấu trúc nền tảng, phải hỏi trước |
| S10 | Công thức gõ ở thanh công thức (`=SUM(A1:A5)`) | Chờ "cách thứ ba" anh/chị chốt; đo lại kiểm tải khi có |
| GĐ 8 | Máy chủ thật, tên miền con cho KN CRM, nginx phục vụ tệp tĩnh, đo tải trên máy chủ, KN ERP dùng tốt trên điện thoại | Chờ V1 |
| S1 → S9, S11, S12 | Đồng bộ hai chiều đơn ↔ vận đơn, chia sẻ quyền cho cấp dưới, thông báo chủ động, kênh báo sự cố, bảng xoay chiều, nhiều người cùng sửa thời gian thực, thư mục lồng nhau, xuất Excel mang định dạng, chiều cao dòng, quản lý sản phẩm | Xem `backlog.md` mục 3 |
| N9 | Thống kê theo thị trường trong báo cáo | Chờ nguồn số liệu (Q36) |

### 10.09.2026 — Chín hạng mục lưới mới, thay quyết định lưu thủ công

Đã duyệt autosave, chọn hàng/màu xanh, hai chế độ, fs/c/bg, lịch sử và
đối chiếu conflict, Admin chọn Sale, thứ tự tạo tăng dần và số hàng từ 1.
Đã triển khai và kiểm chức năng trên database test: suite rộng 1.049 pass,
6 fixture skip được tách kiểm; 90 test tác động và E2E cuối đạt. Hiệu năng
lọc 300k còn chưa đạt; chạy bền dừng theo yêu cầu chủ dự án, để phiên sau
chạy lại đủ 30 phút. Không đổi H7/lưới cũ.
Xem [quyết định ADR-021](quyet-dinh/021-luoi-master-va-thong-ke-crm.md) và
[báo cáo chín hạng mục](kiem-chung-master-nine.md).
