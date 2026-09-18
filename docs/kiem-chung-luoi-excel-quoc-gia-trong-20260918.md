# Kiểm chứng — Lưới thao tác như Excel; xoá Quốc gia thì Loại tiền trống — 18.09.2026

Chủ dự án gửi video trên `crm.thnsolution.io.vn/bang-tinh/van_don/`: (1) Ctrl+A không
bôi đen cả bảng; (2) xoá cả bảng xong không lưu được, báo "Chọn quốc gia hợp lệ để
xác định loại tiền", dữ liệu trở lại như cũ.

## Nguyên nhân

| Lỗi | Nguyên nhân |
|---|---|
| Ctrl+A | Từ 17.09 (ADR-033) bấm ô là mở ô nhập ngay; ô nhập `#mg-editor` nằm ngoài `#mg-viewport` nên Ctrl+A là chọn chữ trong ô, không tới lưới. Bấm ▦ góc trên trái vẫn chọn hết được (khung hình 9–10 của video) |
| Xoá bị chặn | Xoá trống ô Quốc gia → `waybill_service.derived_grid_cells` → `currency_service.change` → `for_label('')` ném lỗi (ADR-031: tiền theo quốc gia). Lượt ghi là nguyên tử nên cả lượt xoá bị từ chối, "Bỏ bản nháp" thì dữ liệu về như cũ |

Chốt với chủ dự án (hỏi hai câu): **như Excel** và **quốc gia trống thì tiền cũng trống**.

## Sửa

- `static/js/master-grid.js`: bấm chỉ chọn ô (ô tràn thì mở hộp đọc như trước 17.09);
  gõ phím chữ/số → `edit(true, ký_tự)` mở ô nhập với ký tự vừa gõ; Enter/F2/bấm đúp
  mở ô giữ giá trị cũ; `advance()` (Enter/Tab trong ô nhập) chỉ chuyển ô; mũi tên
  chỉ di chuyển. Chân lưới đổi hướng dẫn.
- `orders/services/currency_service.py`: `for_label(label, allow_empty=False)`; `change()`
  dùng `allow_empty=True`, chuẩn hoá `''`/`None` để chữ ký xác nhận khớp giữa
  `derived_grid_cells` và `record_service.update`; dòng có tiền vẫn hỏi xác nhận
  ("Đổi hoặc xoá quốc gia…"). `record_service.update` với cột Thị trường của báo cáo
  cũng cho trống. Nhập tệp (`prepare_values`) và Lên đơn vẫn bắt buộc quốc gia.
- Script Codex `kiem-thu-master-nine-ui.cjs`, `kiem-thu-master-admin-click.cjs` sửa theo
  mô hình mới (bấm → gõ, Tab → gõ, F2 trước khi điền); chỉ `node --check`, chưa chạy
  lại vì máy ảo thiếu Playwright cho Node.

## Bài kiểm tự động (máy ảo, Postgres local)

| Nhóm | Kết quả |
|---|---|
| `crm/tests/test_market_currency.py` (thêm AC-33.8: xoá Quốc gia không tiền → xong; có tiền → 400 xác nhận rồi 200, tiền giữ, Bang trống; điền lại → CAD; `for_label('')` không `allow_empty` vẫn lỗi) | 16 đạt |
| `crm/tests orders/tests reports/tests tests/test_truy_vet.py` (`-m "not trinh_duyet"`) | khoảng 550 bài, 0 đỏ, 6 bỏ qua, mã thoát 0 |
| `node scripts/kiem-thu-grid-interaction-unit.cjs`, `kiem-thu-master-queue-unit.cjs` | 2 + 2 PASS. Sau khi rebase lên `20f5bc5` (Codex, dòng trống 1.000 và cột ghim) harness interaction đỏ `config is not defined` ngay trên bản Codex; thêm stub `config`/`drafts` vào ctx của harness, không đổi mã lưới |
| `docs/06` | 199 tiêu chí, 186 tự động, 162 trên 186 |

## Trình duyệt (Chromium 1440×900, 8021 `settings.bangtinh`, crmThuận, `vd.manager`)

| Kiểm | Kết quả |
|---|---|
| Bấm ô Tên khách | chọn `B1:B1 · 1 ô`, ô nhập ẩn |
| Gõ `X` | ô nhập mở, giá trị `X` |
| Enter trên ô | ô nhập mở, giá trị cũ `Bianca Abad` |
| Mũi tên xuống | chỉ chuyển chọn, ô nhập ẩn |
| Ctrl+A | `A1:Y1 · 25 ô được chọn` (bộ lọc 1 dòng) |
| Delete cả dòng | hỏi xác nhận tiền (chấp nhận) → lượt bị từ chối đúng luật vì **Mã đơn bắt buộc**, báo rõ "Dòng #…, cột ma_don"; dữ liệu giữ nguyên |
| Chọn Quốc gia → Thành phố rồi Delete | xem bảng dưới |

Lượt xoá Quốc gia (dòng `MAU-20260910-0004`, Canada/CAD, giá 247,20):

| Bước | Kết quả |
|---|---|
| Chọn `F1:H1 · 3 ô` (Quốc gia, Bang, Thành phố), Delete | Hộp xác nhận "Đổi hoặc xoá quốc gia sẽ đổi loại tiền của 1 dòng đã có tiền…" |
| Chấp nhận | `Đã lưu`; Quốc gia trống, Loại tiền trống, Bang trống, giá **giữ 247,20** |
| Enter trên ô Quốc gia, chọn Hoa Kỳ | hỏi xác nhận lại, `Đã lưu`, Loại tiền `USD`, giá giữ |

## Chưa kiểm

- VPS thật; bảng `van_don` cũ 41 cột trên VPS (video) — cùng mã lưới và cùng policy nên
  cùng hành vi, chưa chạy trên dữ liệu đó.
- IME tiếng Việt thật khi gõ phím đầu tiên (chỉ có sự kiện mô phỏng).
