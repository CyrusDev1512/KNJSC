# Kiểm chứng ADR-041 — bỏ & khôi phục báo cáo cấp dưới — 24.09.2026

Nhánh `claude/xoa-khoi-phuc-bao-cao` tách từ `codex/crm-update-solar-ui` (`b43b20e`,
đã gồm #27/#28/#29), máy ảo Claude Code. Kế hoạch duyệt qua plan mode; 4 quyết định
của chủ dự án ghi đủ trong [ADR-041](quyet-dinh/041-xoa-khoi-phuc-bao-cao.md).
Chỉ local — không đụng VPS.

## Kiểm tự động

| Lượt | Lệnh | Kết quả |
|---|---|---|
| Suite đầy đủ | `pytest -m "not trinh_duyet and not cham"` | **2.566 đạt, 1 bỏ qua, 0 đỏ** (293 s) |
| Bài mới | `reports/tests/test_bao_cao_xoa_khoi_phuc.py` — 5 hàm / 19 ca (AC-4.9, AC-4.10) | Bỏ: 9 vai hai chiều (người nộp/Leader team/Manager bộ phận/Admin được; nhân viên khác/Leader team khác/Manager bộ phận khác/Kế toán bị 403 hoặc 404 có nhật ký); xoá mềm cả dòng số liệu → rời Báo cáo tổng hợp, nội dung còn nguyên; bấm đúp không nhân đôi; service kiểm quyền trong giao dịch. Khôi phục: 6 vai hai chiều; số liệu sống lại nguyên vẹn; trang Đã bỏ đúng phạm vi từng Manager |
| Bài cũ chỉnh | `test_ngoai_quyen_khong_bo_duoc_bao_cao` (viết lại theo ADR-041), `reports/` trọn gói 94 bài | đạt; `test_ke_toan_bao_cao` (Kế toán không bỏ) **giữ nguyên, vẫn xanh** |
| Truy vết | `tests/test_truy_vet.py` + docs/06 | 241 tiêu chí (228 tự động), 204 đã có bài — khớp |
| Migration | không có migration mới | `makemigrations --check`: "No changes detected" |

## Chromium (server dev 8020, DB `knjsc_db`, tài khoản `quantri`)

Ảnh ở `docs/kiem-thu/xoa-khoi-phuc-bao-cao-2026-09-24/`:

| Bước | Kết quả |
|---|---|
| Lịch sử báo cáo | Liên kết **"Đã bỏ"** hiện với Admin (`01` — kèm nút Sửa/Bỏ trong ô đọc) |
| Bấm "Bỏ báo cáo này" | 302 về Lịch sử, báo cáo biến khỏi danh sách (`02`) |
| Trang `/bao-cao/da-bo/` | 1 dòng: ngày, biểu mẫu, người nộp, **người bỏ + lúc bỏ**, nút Khôi phục (`03`) |
| Bấm Khôi phục | báo cáo rời trang Đã bỏ, về lại Lịch sử (`04`); **0 lỗi JavaScript** cả vòng |

Ghi chú môi trường: DB dev của máy ảo còn mang cột `val_phone_key` bản cũ (từ lúc thử
PR #34 trước khi vá `db_default`) nên lần nộp báo cáo đầu nổ NOT NULL — đúng hiện tượng
bản vá `202691f` của PR #34 xử lý; vá tại chỗ bằng `ALTER COLUMN ... SET DEFAULT ''` là
hết. Không liên quan nhánh này.

## Chưa kiểm / còn nợ

- Chưa chạy VPS (ngoài tầm với; không migration nên phát hành chỉ cần image mới).
- Bộ đếm docs/06 (241/228/204) **chỏi với các PR đang mở #31/#34/#35/#39** — PR gộp sau
  rebase chỉnh số theo thông báo `test_truy_vet`.
- Khi #39 (ADR-040) gộp: mục "khoảng trống" trong ADR-040 coi như đã xử lý bởi ADR-041
  (đã ghi chéo trong ADR-041).
