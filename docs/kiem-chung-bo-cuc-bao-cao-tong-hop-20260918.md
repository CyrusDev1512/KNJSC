# 18.09.2026 — Bố cục Báo cáo tổng hợp theo bản vẽ (Việc A)

Theo bàn giao "Bàn giao cho Claude Code CLI — 18.09.2026" trong `docs/daily-tasks.md` và bản vẽ
`docs/tham-khao/ban-ve-bao-cao-tong-hop-20260918.html` (tệp chủ dự án đưa ở Downloads giống hệt bản
trong kho). Làm trên máy Windows, Compose local; đặt lên đầu nhánh `3748ea9` của Codex.

## Việc B (mã nhân sự) — không làm lại

Trong lúc CLI làm A và B song song, Codex đã hoàn thành B theo **quy tắc `THUANLT` của sheet Quy ước**
(ADR-037, `staff_code_service`, lệnh `gan_ma_nhan_su_cu --xac-nhan`, migration `org/0005`) — khác quy
tắc `NTLH01` mà CLI đã xác nhận với chủ dự án theo bàn giao buổi sáng. Bản bàn giao mới trên nhánh
ghi rõ "Ô Nhân sự/Leader đã hiện MÃ · Họ tên (Đợt 1 làm xong)", nên bản B của CLI (cùng tên trường, cùng
tên migration, quy tắc khác) được **bỏ**, giữ ở nhánh cục bộ `backup/a-b-local-20260918` để tra cứu; A
được đặt lại lên đầu nhánh và gộp với hai bổ sung của Codex trên cùng màn hình: ô **Tệp khách hàng**
(`tep`) và hàng **Chọn nhanh kỳ** (`.report-presets`, ADR-038).

## A. Bố cục (AC-22.13)

- `templates/reports/activity.html`: thanh điều khiển (Thu gọn/Mở bộ lọc có icon, Xuất Excel, Toàn
  màn hình), hàng chip từ `params` (Kỳ, Cách xem, Sản phẩm, Thị trường, Tệp, Team, Nhân sự; × là link
  cùng URL bỏ đúng tham số, bỏ Team thì bỏ luôn Nhân sự; Xóa lọc chỉ giữ nguồn), `#report-workspace`
  với `data-filters` và `data-active`, panel có đầu/thân/thanh dọc (`.panel-rail` + huy hiệu), backdrop;
  giữ nguyên ô Tệp khách hàng, Chọn nhanh kỳ và ghi chú Doanh thu MKT của Codex.
- Bảng: cột định danh ghim trái theo lớp tổng quát `.report-identity` + lớp loại (`id-ngay`, `id-nhom`,
  `id-team`, `id-nhan-su`, `id-leader`), `left` của cột 2–4 là biến CSS đặt trên `<table>` từ
  `activity_views.identity_layout`; ô định danh xuống dòng, **bỏ rule cắt tên**; tiêu đề và dòng Tổng
  ghim trên (`--head-h` đo từ thead); ô số `nowrap`, đệm 8×10 px, 13px.
- `solarpunk.css`: thay trọn khối `.report-*` … `.sp-report-focus` bằng khối theo bản vẽ (giữ 4 rule
  Chọn nhanh của Codex), không rule cũ chồng lên; chỉ token có sẵn; hai ô ngày xếp dọc vì bộ chọn ngày
  có nút lịch 30px.
- `report-filters.js`: ba trạng thái (`open` 260px, `rail` 48px, dưới 900px là ngăn kéo mặc định đóng),
  `sessionStorage` `{filters, focus}` đọc được khoá cũ `{hidden}`; Toàn màn hình → rail; Escape đóng ngăn
  kéo trước, thoát toàn màn hình sau; giữ `sp-erp-table-focus` và khối Chọn nhanh của Codex.
- Đo Chromium local 8020 trước khi gộp (sale.manager, Báo cáo Sale, sáng và tối, 1440/900/390): trạng
  thái mặc định open/closed/closed; thu gọn → panel 48px; ngăn kéo 320px với backdrop; cuộn ngang 346px ở
  390px thì cột định danh **đứng yên** (dx 0) trong khi tiêu đề số dịch −346; Toàn màn hình → rail, Escape
  thoát; không lỗi JS, không tràn ngang. Ảnh `storage/bo-cuc-bao-cao/*.png`. Sau khi gộp: chụp lại
  `sau-gop-*.png` (xem Hồi quy).
- Bài kiểm: `reports/tests/test_bo_cuc_bao_cao.py` (chip + link bỏ tham số, cột định danh theo cách xem,
  Staff lọc người khác 403) và `test_bo_cuc_bao_cao_e2e.py` (Chromium: ba trạng thái, nhớ phiên, khoá cũ,
  toàn màn hình, ngăn kéo, Escape, ghim); `core/tests/test_giao_dien.py`; `tests/test_truy_vet.py`.

## Hồi quy

`reports/tests` (kèm hai bài Chromium mới) + `core/tests/test_giao_dien.py` + `tests/test_truy_vet.py` trên đầu nhánh `3748ea9` của Codex: 0 đỏ sau khi sửa hai khẳng định (`test_activity` so header cột định danh, chip Nhân sự theo nhãn mã của ADR-037); bộ đếm docs/06 225 tiêu chí, 212 tự động, 188 có bài kiểm; Chromium 8020 sau gộp (`storage/bo-cuc-bao-cao/sau-gop-*.png`): 1440 mở, 390 đóng, chip đủ, 5 nút Chọn nhanh, nhãn `mã · họ tên` của Codex, không tràn ngang, không lỗi JS

## Chưa kiểm — ghi nợ

- Chưa phát hành VPS; đợt phát hành kế tiếp theo bàn giao tối 18.09 của Codex (ba migration, hai lệnh
  `gan_ma_nhan_su_cu`), bố cục này đi kèm không cần bước riêng ngoài `collectstatic`.
- Chưa chạy bộ `.cjs` của Codex (máy này không có Playwright cho Node).
