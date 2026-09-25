# Kiểm chứng — Một ô Team duy nhất trên form Nộp báo cáo ngày (ADR-043 bổ sung) — 25.09.2026

Nhánh `claude/mot-o-team-bao-cao` tách từ `main` (`a23573d`), máy ảo Claude Code (Postgres 16 cổng
5434, Chromium Playwright). Chủ dự án chụp màn hình 25.09: form MKT trên dữ liệu thật có **hai ô Team**
(dropdown mới ở hàng đầu và ô gõ tay "Team" trong lưới). Nguyên nhân: bảng Báo cáo Marketing của dữ liệu
thật có sẵn cột Team dạng chữ, `configure_forms` tự đưa mọi cột nhập lên form; dữ liệu mẫu không có cột này
nên kiểm chứng 24.09 không thấy.

## Kiểm tự động

| Lượt | Kết quả |
|---|---|
| Bài mới AC-43.5 (`reports/tests/test_form_nhap_bao_cao.py::test_mot_o_team_tren_form_nhap`) | Cột Team dạng chữ (`team_mau`, nhãn "Team") có trường trên form → `configure_source` gỡ, chạy lại không tạo lại, `ReportSource.columns["team"] == "team_mau"`, cột còn nguyên; form có đúng một nhãn Team và một `#o-team`, không còn `name=*team_mau`; nộp chọn MKT B kèm chữ gõ tay → `data["team_mau"] == "MKT B"`; không chọn → team hồ sơ "MKT A"; người chưa có team → cột trống, vẫn nộp được (302); Bảng dữ liệu `?dang=tho` hiện "MKT A"/"MKT B"; bảng Sale do lệnh dựng có cột mã `team` → ánh xạ và gỡ trường như MKT |
| Bốn bài AC-43.1 → 43.4 cùng tệp | Xanh (5 passed, 6,9 s) |
| Suite đầy đủ `-m "not trinh_duyet"` | Lượt 1 (bắt đầu trước khi sửa docs/04): **2.024 đạt, 7 bỏ qua, 1 đỏ** là `test_truy_vet` vì bài này đọc docs/04 lúc thu thập, trước khi dòng AC-43.5 được thêm; chạy lại `tests/` sau khi sửa tài liệu: **1.070 đạt, 0 đỏ** (107 s), `test_truy_vet` + `test_dong_bo_skill` 38 đạt. Không sửa bài nào để qua |
| `makemigrations --check --dry-run` | "No changes detected" (không đổi model) |
| `tests/test_truy_vet.py` + docs/06 | 270 tiêu chí, 257 tự động, 234 có bài — khớp |

## Chromium (server dev 8020, DB `knjsc_mkt`, dữ liệu mẫu + cột Team dạng chữ thêm vào `bao_cao_mkt`)

Tái hiện trước bằng `configure_forms(table)` không `skip` (đúng cách cũ) rồi chạy `manage.py
configure_erp_reports` bản mới; script `chup-team.py` đếm phần tử trên trang thật. Ảnh ở
`docs/kiem-thu/mot-o-team-bao-cao-2026-09-25/`:

| Ảnh | Đếm trên trang | Kết quả |
|---|---|---|
| `01-truoc-quantri-hai-o-team` | nhãn Team **2**, `#o-team` 1, ô gõ tay `input[name$=team]` **1** | Tái hiện đúng ảnh chủ dự án (kèm ô Hóa đơn vì cách cũ đưa mọi cột lên) |
| `02-truoc-mkt-staff-hai-o-team` | nhãn Team 2, ô gõ tay 1, option `MKT 1` | Cùng lỗi với tài khoản có team |
| `03-sau-quantri-mot-o-team` | nhãn Team **1**, `#o-team` 1, ô gõ tay **0** | Một ô Team; Hóa đơn cũng biến (skip MKT) |
| `04-sau-mkt-staff-mot-o-team` | nhãn Team 1, ô gõ tay 0, option `MKT 1` chọn sẵn | — |
| `05-bang-du-lieu-tho-cot-team` | nộp 21 / 63 / 4 / 250, chọn MKT 1, cố tình chèn `team_go_tay=gõ tay` → về `/bao-cao/lich-su/`; Bảng dữ liệu thô dòng đầu `['2026-09-25', 'ANHPM', '21', 'MKT 1', '63', '4', '250', '—']` | Cột Team dạng chữ nhận tên team đã chọn, chữ gõ tay bị bỏ |

## Không đổi

Dòng cũ giữ chữ Team đã gõ (BR-4); nhập Excel vẫn nhận cột Team từ tệp (`create_records_bulk` không
đổi); Sửa báo cáo (`amend`) không đụng cột này; Bảng dữ liệu và tệp xuất vẫn có cột Team; dropdown Team
và phạm vi Leader như ADR-043.

## Chưa kiểm

VPS và dữ liệu thật của chủ dự án (mã cột Team thật chưa biết — lệnh nhận diện theo mã `team` hoặc nhãn
"Team", không phân biệt hoa thường; cột kiểu số hay ngày thì không nhận). Bài `trinh_duyet` của suite
không chạy trong lượt này (ảnh chụp ở trên là kiểm trình duyệt của riêng việc này).
