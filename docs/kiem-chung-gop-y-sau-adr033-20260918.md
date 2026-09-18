# 18.09.2026 — Bốn góp ý của chủ dự án sau phát hành ADR-033 (local, chưa VPS)

Chủ dự án thử trên domain thật (image `9949062-adr033`) và nêu bốn việc; kế hoạch được duyệt
trong phiên Claude Code, làm trên máy Windows với Compose local (bind-mount `app/`, mã chạy
ngay). Chromium: Playwright của `D:\DVS-baodon\.venv` cho ảnh chụp 8020/8021, và Chromium
cài thêm trong container `web` (`playwright install chromium`) để chạy bài `trinh_duyet`
của pytest. Ảnh trong `storage/gop-y-adr033/` (không vào kho).

## 1. Lưới: 1.000 dòng trống sẵn, tới dòng 999 thêm 1.000 (AC-11.37)

- Nguyên nhân: `ensureDrafts(1)` giữ đúng một dòng nháp; sau mỗi lần lưu dòng mới `saveAll`
  gọi `invalidate()` xoá cache, tải lại khối JSON, vẽ lại rồi mới thêm một dòng nháp.
- Sửa `static/js/master-grid.js`: `DRAFT_BATCH = 1000`; `ensureDrafts()` mặc định bù đủ
  1.000; `choose()` tới dòng áp chót thì thêm 1.000; `absorbCreated()` nối dòng vừa tạo vào
  khối cache cuối, không `invalidate()` (rơi về tải lại chỉ khi giao thức nén hoặc khối cuối
  chưa nạp); chân trang "N dòng khớp bộ lọc · 1.000 dòng trống để nhập".
  `master-row-geometry.js` thêm `resize(total)` giữ chiều cao hàng đã đặt khi đổi tổng
  (`reset()` xoá sạch); kiểm Node: `top(6)=240`, `top(2000)=56104` sau resize từ 1.000.
- Đo local 8021 (Vận đơn DB, `quantri`, Chromium 1440×900): mở bảng 0 dòng → tổng 1.000,
  chân trang đúng; Ctrl+End → 2.000; dán một dòng đủ trường → "Đã lưu", **0 request
  `du-lieu/` sau lưu**, chân trang "1 dòng khớp bộ lọc · 1.000 dòng trống để nhập", dòng mới
  có id thật, tải lại còn 1 dòng thật. Không lỗi JS.
- Lưu ý đo được: bấm ô là mở ô nhập ngay (ADR-033) nên Ctrl+End phải bấm sau Esc; dán
  ngày phải ở dạng ISO (`2026-09-17`), `17/09/2026` bị từ chối đúng kiểu; quốc gia US kèm
  USD mở hộp xác nhận tiền tệ. crmThuận local mang profile Vận đơn (`protect_table`) nên
  không có dòng nháp — đúng thiết kế, đơn vào bằng Lên đơn; trên VPS `van_don_moi` chưa mang
  profile nên có dòng nháp, là chỗ chủ dự án thấy lag.
- Bài kiểm: `crm/tests/test_luoi_dong_trong_va_ghim_e2e.py::test_mot_nghin_dong_trong_san_va_tao_dong_khong_tai_lai`
  (Chromium trong container, bảng thường bộ phận Vận đơn, Admin): đạt.

## 1b. Giật khi gõ rồi Enter — nguyên nhân thật và cách sửa (AC-11.40)

Chủ dự án báo giật cả trên local, "mỗi lần Enter như sinh thêm một hàng". Tracer theo frame
(`storage/gop-y-adr033/giat/*.json`: vị trí ô nhập, ô `…`, tổng dòng, chiều cao canvas,
`layout-shift`, `longtask`, request) trên hai tình huống, trước và sau sửa:

| Tình huống | Trước sửa | Sau sửa |
|---|---|---|
| Gõ 5 dòng có sẵn (crmThuận 10.000 dòng) | 8 s sau, poll `moi-nhat/` thấy mốc đổi (do **chính mình** lưu) → `invalidate()`: **360 ô trong tầm nhìn hoá `…`**, tải lại 4 khối | 0 ô `…`, 0 request khối, ô nhập không nhảy |
| Gõ 5 dòng trống (bảng thường) | Mỗi lần lưu: ô nhập **nhảy lên 33 px rồi tụt lại** (thanh thông báo "Đã tạo dòng…" ẩn lúc bắt đầu lưu, hiện lại khi xong, đẩy cả lưới), tổng dòng +1 và canvas +28 px mỗi dòng (bù nháp từng dòng), nháp bị bỏ trước khi dòng thật được nối | 0 lần nhảy, tổng và chiều cao **không đổi** suốt 5 dòng, 0 ô `…`, 0 layout shift > 0,001, 5 dòng vào DB |

Sửa: (1) phản hồi `luu-json` mang mốc `latest` (cùng hàm `latest_stamp` với view
`moi-nhat`), lưới ghi `state.poll` nên không coi mốc do mình lưu là người khác sửa; (2) khi
người khác sửa thật thì `refreshSoft()`: giữ bản cũ (`state.stale`) làm nền, khối mới về tới
đâu thay tới đó — không hoá `…`; (3) `absorbCreated` bỏ nháp và nối dòng thật trong cùng một
bước, chỉ bù nháp khi còn dưới 500; (4) bỏ thanh thông báo "Đã tạo dòng" khi dòng đã nối tại
chỗ. Bài kiểm `test_go_lien_tiep_roi_enter_khong_giat` (AC-11.40) chạy tracer trong Chromium,
kể cả chờ qua kỳ poll 8 s.

## 2. Bảng nhận đơn hiện mọi bảng vận đơn (AC-11.39, ADR-034)

- Nguyên nhân: `candidates()` lọc theo bộ phận Vận đơn và loại `van_don`; báo cáo ngày cùng
  bộ phận lọt vào. Sửa `orders/services/destination_service.py`: `_is_waybill_like` (profile
  Vận đơn, `van_don_moi`, `van_don` cũ, hoặc bộ phận Vận đơn có cột Mã đơn đúng cấu trúc);
  bỏ lý do cứng "bảng cũ chỉ giữ lịch sử" khỏi `_schema_error`.
- Đo local: `candidates()` → `van_don` ("Cột Loại tiền chưa có hoặc không đúng cấu trúc Vận
  đơn"), `van_don_moi` (chọn được), `van_don_db` ("Cột PTTT lên đơn thiếu lựa chọn chuẩn" —
  local chưa `chuan_bi_bang_nhan_don`); `bao_cao_van_don_ngay`, `bao_cao_*` không hiện.
  **Chủ dự án chốt 18.09: `van_don` là bảng duy nhất của Lên đơn.** `prepare_existing` thêm bước
  `_upgrade_schema`; chạy `chuan_bi_bang_nhan_don --table van_don --actor quantri --expected-rows 234`
  trên local: 42 → 45 cột, `loai_tien`/`pttt` thành danh sách, 234 dòng nguyên, đủ điều kiện,
  đã chọn (`current() == van_don`); `order_service.create_order` ghi `DH-1809-0001` vào `van_don`;
  lưới `van_don` mở 235 dòng, còn cột Trùng, không lỗi JS. Bài kiểm
  `test_prepare_upgrades_legacy_schema_then_selectable` (Admin làm được, Staff/Leader/Manager bị chặn).
- Bài kiểm: `crm/tests/test_order_destination.py::test_candidates_list_every_waybill_table`
  đạt; 13 bài cũ của trang nhận đơn và chuẩn bị bảng đạt (Staff/Leader/Manager vẫn 403).

## 3. Bôi đen sai cột khi cột ghim không đứng đầu (AC-11.38)

- Nguyên nhân (`master-grid.js` bố cục): `x` tính theo thứ tự cột gốc, cột ghim chỉ vẽ đè bên
  trái; ở Vận đơn DB ba cột ghim ở vị trí 6/16/19 nên vùng chọn theo chỉ số gốc (kéo từ cột 6
  tới cột 4 bôi 4..6 đúng như ảnh chủ dự án), ô trống ở chỗ cũ của cột G, ba cột đầu bị che.
- Sửa: cột ghim đứng đầu `state.visible` (giữ thứ tự tương đối) rồi mới tính `x`; `pinX = x`.
- Đo local 8021 (crmThuận, `quantri`, đổi thứ tự cột qua `localStorage` để ba cột ghim đứng
  sau bốn cột khác): sau tải lại ba cột đầu là `ma_don, ten_khach, so_dien_thoai` (ghim),
  cột thứ tư là `ngay`; **khoảng trống giữa các cột 0 px**; kéo chọn từ cột ghim tới cột thứ
  5 bôi đúng 5 cột liền nhau, địa chỉ `A1:E4 · 20 ô được chọn`. Mã ghim/sticky không đổi
  giữa `0907cdd` và `9949062` nên lỗi có từ trước, chỉ lộ khi cột ghim không ở đầu.
- Bài kiểm: `test_luoi_dong_trong_va_ghim_e2e.py::test_cot_ghim_dung_dau_va_boi_den_theo_thu_tu_nhin_thay` đạt.

## 4. Báo cáo tổng hợp: Nhân sự, Leader, phạm vi, 100 dòng, bảng gọn (AC-22.10, 22.11, ADR-035)

- Màn hình thật là nhánh báo cáo hoạt động ERP (`activity_views.report`, ADR-022). Sửa:
  `activity_service.person_expressions` + `with_day_people` (Nhân sự = người lập dòng, Vận đơn
  = người được phân công; Leader = `Team.leader`; gộp tên bằng `StringAgg` trên đúng dòng của
  ngày — **mỗi ngày vẫn một dòng**, bản nháp đầu nhóm theo ngày × nhân sự đã hoàn lại theo yêu
  cầu chủ dự án), Theo nhân viên thêm Leader; view đặt `default_size=100`, `label_span`;
  template hai cột sau Ngày; Excel cùng cột; CSS `.report-*` 13px, ô 5×8 px, khung
  `calc(100vh - 230px)`, panel 224px.
- Phạm vi quyền **đã có sẵn** qua `apply_scope` + `filter_people`; không viết lại, chỉ kiểm lại.
- pytest `reports/tests`: **133 đạt, 0 đỏ** (gồm `test_query_budget` ≤ 10 truy vấn với cột
  mới, hai bài mới AC-22.10 bốn cấp bậc + lọc `nhan_su` + 403 ngoài phạm vi + Excel, AC-22.11
  100 dòng/trang; ba bài cũ so vị trí cột Excel đã cập nhật theo hai ô danh tính).
- Chromium local 8020 (Báo cáo Sale, 4 dòng mẫu nạp thêm `KIEM ADR-035`, 1440 và 390 px, không
  lỗi JS, không tràn ngang): header `Ngày · Nhân sự · Leader · Số Mess…`, **mỗi ngày một dòng**;
  `sale.staff` thấy 2 ngày của mình, Nhân sự = mình, Leader "Trần Thị Lan"; `sale.manager` thấy
  3 ngày, ngày 16.09 gộp "sale.staff — Nguyễn Thị Hà, sale.staff2 — Lý Thu Hằng" và Leader
  "Lê Văn Long, Trần Thị Lan"; `sale.leader` chỉ thấy dòng của mình (DB mẫu local đặt leader
  team Sale 1 là tài khoản khác — đúng quy tắc phạm vi). Bảng ôm đúng số dòng, không khối trắng.
  Ảnh `*-1440-mot-dong-moi-ngay.png`.

## Hồi quy

- Lần cuối (sau mọi sửa của ngày, gồm cả chiều): `crm/tests orders/tests forms_builder/tests core
  reports/tests tests` với `-m "not cham or trinh_duyet"` (bài trình duyệt chạy bằng Chromium trong
  container): **khoảng 2.421 đạt, 23 bỏ qua, 2 đỏ** — hai bài `test_dong_bo_skill.py` đỏ vì container
  không mount `scripts/` (`/scripts/dong-bo-skill.py` không tồn tại), lỗi môi trường có sẵn; trên host
  `python scripts/dong-bo-skill.py --check` cũng FAIL vì hai thư mục chưa theo dõi có sẵn trên máy này
  (`.claude/skills/impeccable/scripts/`, `.impeccable/`), không liên quan đợt này.
- Hai bài từng đỏ do đợt này và đã sửa: `test_prepare_rejects_count_drift_bad_schema_and_non_admin`
  (cột thiếu nay được tự bổ sung nên bài đổi sang lỗi không tự sửa được: sai bộ phận) và
  `test_compact_receipt_survives_flag_rollback` (mốc `latest` phải nằm trong biên nhận để replay trả
  đúng mốc lúc lưu — chuyển `latest_stamp` vào `master_grid_service.save`).
- `tests/test_truy_vet.py` đạt với bộ đếm docs/06: 204 tiêu chí, 191 tự động, 167 có bài kiểm.

## Chưa kiểm — ghi nợ

- Chưa phát hành VPS; chưa kiểm trên dữ liệu thật 6.667 dòng Vận đơn DB và 51 dòng MKT.
- Chưa đo tải `cua_toi=1` hay bảng Tổng hợp ngày × nhân sự ở 300.000 dòng.
- Bài `.cjs` của Codex chưa chạy lại (máy này không có Playwright cho Node); bài trình duyệt
  mới viết bằng pytest `trinh_duyet` để chạy được trong container.
- `van_don` cũ chọn làm bảng nhận đơn: cần chuyển đổi cấu trúc (Loại tiền) — chưa làm.
