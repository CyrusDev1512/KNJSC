# Kiểm chứng lọc theo cột ẩn vẫn chạy, kèm lời nhắc (TL-53) — 22.09.2026

Nhánh `claude/loc-cot-an-co-nhac` tách từ `codex/crm-update-solar-ui` (`87010d4`),
máy ảo Claude Code (không tới được VPS). Hướng chủ dự án chốt 22.09: **vẫn lọc +
hiện dòng nhắc kèm nút bỏ lọc**. Quyết định ghi ở
[ADR-039 bổ sung 22.09](quyet-dinh/039-an-cot-voi-ca-cong-ty.md).

## Phạm vi

Bộ lọc đọc trên mọi cột ở ba đường: `grid_service.build_grid` (lưới KN CRM và
Thống kê), `forms_builder.views.bang_xem` (Bảng dữ liệu KN ERP),
`export_service.build_queryset` (tệp Excel — vẫn "xuất đúng thứ đang hiện",
ADR-002; cột ẩn vẫn không ra tiêu đề tệp). Chip KN CRM thêm cờ cảnh báo
(`mg-chip-an`, nhãn "(cột đang ẩn) …"); KN ERP thêm dòng nhắc `bao-cho` cạnh nút
Xoá lọc; danh sách cột ẩn đang bị lọc tính một chỗ
`table_service.hidden_filtered_columns`. Hiển thị cột không đổi so với ADR-039.

## Kiểm tự động

| Lượt | Lệnh | Kết quả |
|---|---|---|
| Suite đầy đủ | `pytest -m "not trinh_duyet and not cham"` | **2.531 đạt, 1 bỏ qua, 0 đỏ** (301 s). Lượt đầu đỏ 1 bài không liên quan (`test_leader_chi_thay_so_lieu_team_minh` assert `"900" not in` cả trang HTML, dính mã cache static theo mtime tệp CSS vừa sửa) — vá theo đúng khuôn bài AC-3.1 cùng tệp (monkeypatch `PHIEN_BAN_TINH` + `strip_tags`), lượt hai sạch |
| Bài mới | `crm/tests/test_loc_cot_an.py` — 4 bài AC-39.8 | Lọc cột ẩn trả đúng dòng trên lưới + chip cảnh báo có cờ, link chip bỏ đúng một bộ lọc, bộ lọc cột hiện không dính cờ; tệp Excel xuất theo đúng bộ lọc, cột ẩn không ra tiêu đề; Bảng dữ liệu ERP lọc đúng + dòng nhắc, không lọc thì không nhắc, `build_queryset` cùng kết quả; **chiều bị từ chối**: Sale chỉ thấy dòng của mình dù bộ lọc cột ẩn khớp dòng người khác |
| Vùng đụng | `test_an_cot`, `test_bang_tinh`, `test_executive_statistics`, `forms_builder/tests` | đạt hết (AC-39.1→39.7 nguyên trạng) |
| Truy vết | `tests/test_truy_vet.py` + docs/06 | 240 tiêu chí (227 tự động), 203 đã có bài — khớp |

## Chromium (server dev 8021/8020 trên DB `knjsc_db` 120 nghìn dòng PERF)

Ảnh ở `docs/kiem-thu/loc-cot-an-2026-09-22/`. Ẩn cột `sl_retinol_cream` bằng đúng
dịch vụ `set_columns_hidden`, rồi mở URL mang bộ lọc cũ như người dùng còn bookmark:

| Bước | Kết quả |
|---|---|
| Lưới `?f_sl_retinol_cream__lon_bang=2&f_quoc_gia__trong=Canada` | **13.939 dòng khớp** (không còn bị bỏ lặng lẽ về 100.000); chip đầu nền vàng cảnh báo "(cột đang ẩn) Retinol Cream ≥ 2 ×", chip Quốc gia bên cạnh không cảnh báo (`01`) |
| Bấm × trên chip cảnh báo | về `?f_quoc_gia__trong=Canada`, còn 100.000 dòng, chip thường giữ nguyên (`02`); không lỗi JS |
| Bảng dữ liệu ERP `?f_sl_retinol_cream__lon_bang=2` | 13.940 dòng (13.939 Canada + 1 Hoa Kỳ — khớp đếm SQL trực tiếp); dòng nhắc vàng "Đang lọc theo cột đang ẩn: Retinol Cream. Bỏ lọc" (`03`) |
| Trả lại trạng thái | `set_columns_hidden(..., False)` — DB dev không còn cột ẩn |

## Chưa kiểm / còn nợ

- Chưa chạy trên VPS (không tới được). Không có migration — phát hành chỉ cần image mới.
- Bộ đếm docs/06 (240/227/203) **chỏi với PR #31 và PR #34** — ba nhánh cùng đặt số này;
  PR gộp sau cần rebase chỉnh bộ đếm theo thông báo của `test_truy_vet`.
- Tìm kiếm chung (`tim=`) trên cột tách vẫn quét cả cột ẩn có nhãn ý nghĩa (khách, SĐT…)
  — cùng tinh thần "dữ liệu vẫn còn, chỉ ẩn hiển thị"; nếu chủ dự án muốn loại thì làm lượt riêng.
