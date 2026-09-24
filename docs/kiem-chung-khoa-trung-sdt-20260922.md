# Kiểm chứng khoá so trùng số điện thoại (TL-36) — 22.09.2026

Nhánh `claude/khoa-trung-so-dien-thoai` tách từ `codex/crm-update-solar-ui` (`87010d4`),
máy ảo Claude Code (không tới được VPS). Quy tắc chủ dự án chốt 22.09: **bỏ ký tự không
phải số, so 9 chữ số cuối**; ô hiển thị giữ nguyên chữ nhân viên gõ. Quyết định ghi ở
[ADR-036 bổ sung 22.09](quyet-dinh/036-mot-bang-van-don-duy-nhat.md).

## Phạm vi

Cột `DataRecord.val_phone_key` + chỉ mục `(table, val_phone_key)` + backfill (migration
`forms_builder/0016`, đảo được); khoá sinh một chỗ duy nhất `forms_builder.models.phone_key`
trong `sync_indexed_columns`; `bulk_save` ghi kèm (danh sách cột mặc định và
`nap_du_lieu_van_don` liệt kê cứng); bốn chỗ đọc trong `crm/services/grid_service.py`
(cột Trùng cả trang, đếm dòng lẻ, `?trung=1`) GROUP BY theo khoá. **Không đổi** tra khách
ở Lên đơn (`Customer.phone`) — câu hỏi mở cho chủ dự án.

## Môi trường

PostgreSQL 16 cục bộ (socket /tmp), venv Python 3.11 + Django 5.2; DB pytest
`test_knjsc_db`, DB dev `knjsc_db` 120.547 dòng `van_don` (dữ liệu giả `PERF-*`).

## Kiểm tự động

| Lượt | Lệnh | Kết quả |
|---|---|---|
| Suite đầy đủ | `pytest -m "not trinh_duyet and not cham"` | **2.530 đạt, 1 bỏ qua, 0 đỏ** (298 s); gồm `crm/tests/test_kiem_tai.py` (đụng `bulk_save`) và AC-11.36 (một truy vấn một trang cho cột Trùng) vẫn xanh |
| Bài mới | `crm/tests/test_khoa_trung_sdt.py` — 3 bài AC-36.8 | `+1 (416) 555-0123`, `(416) 555-0123`, `4165550123` đếm là một khách (Trùng = 3, `?trung=1` trả cả ba); số khác 9 đuôi không gom; ô trống không gom; ô hiển thị giữ chữ gốc; `sync_indexed_columns` và `bulk_save` mặc định cùng ra một khoá, xoá số thì khoá rỗng; migration 0016 xuôi/ngược + backfill đúng cho dòng có sẵn |
| AC-11.5 | bài cũ của cột Trùng, docstring sửa lời theo khoá | đạt |
| Truy vết | `tests/test_truy_vet.py` + docs/06 | 240 tiêu chí (227 tự động), 203 đã có bài — bộ đếm docs/06 khớp |
| Migration | `makemigrations --check --dry-run` | "No changes detected" |

## Backfill trên DB dev 120 nghìn dòng

`manage.py migrate forms_builder` (0016: AddField + AddIndex + một lệnh UPDATE):
**112 giây** trọn gói trên máy ảo 2 nhân. 120.535/120.535 dòng có số đều có khoá;
soát mẫu `0900009929 → 900009929`, `4030001588 → 030001588`; 18.373 nhóm khoá trùng
(dữ liệu giả cố ý sinh khách mua lại).

## Chưa kiểm / còn nợ

- Chưa chạy trên VPS: backfill thật làm trong lượt phát hành (`migrate` trong
  `entrypoint.sh` tự chạy 0016); DB VPS ~cùng cỡ nên dự kiến ~2 phút, các dịch vụ khác
  không đọc cột mới trong lúc đó nên không cần bảo trì.
- Bộ đếm docs/06 (240/227/203) **chỏi với PR #31** — cả hai cùng đặt số này; PR nào gộp
  sau cần một lần rebase chỉnh bộ đếm theo thông báo của `test_truy_vet`.
- Tra khách ở Lên đơn vẫn so đúng như gõ — chờ chủ dự án quyết có theo khoá không.
