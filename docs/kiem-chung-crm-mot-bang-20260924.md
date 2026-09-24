# Kiểm chứng ADR-040 — KN CRM chỉ một bảng Vận đơn — 24.09.2026

Nhánh `claude/crm-chi-mot-bang-van-don` tách từ `codex/crm-update-solar-ui` (`87010d4`),
máy ảo Claude Code (không tới được VPS). Quyết định và bốn bối cảnh của chủ dự án ghi
đủ ở [ADR-040](quyet-dinh/040-crm-chi-mot-bang-van-don.md); kế hoạch được duyệt trước
khi làm (plan mode 24.09).

## Phạm vi

Lọc một chỗ `crm/services/catalog.chi_van_don` áp ở mọi cửa KN CRM; thư mục phẳng
(bỏ Quý ▸ Tháng); trang chủ CRM (ô số, Bảng gần đây, Hoạt động gần đây) chỉ vận đơn;
guard `_chi_bang_van_don` cho các route forms_builder trên 8021; nút Tạo bảng ẩn,
đường dẫn còn; trang Đã xóa giữ mọi bảng; Thống kê không đụng. **Không đổi dữ liệu,
không migration.** Sửa kèm hai lỗi lộ ra khi kiểm: `sidebar_service` đổ 500 khi bảng
vận đơn thiếu cột chuẩn; mục Thống kê trên sidebar biến mất với người chỉ có bảng thường.

## Kiểm tự động

| Lượt | Lệnh | Kết quả |
|---|---|---|
| Suite đầy đủ | `pytest -m "not trinh_duyet and not cham"` | **2.529 đạt, 1 bỏ qua, 0 đỏ** (300 s) |
| Bài mới | `crm/tests/test_crm_chi_van_don.py` — AC-40.1→40.3 (3 bài) + AC-40.4 trong `test_shared_grid` | Trang chủ + thư mục chỉ nhắc vận đơn; mọi cửa của bảng thường 404/403 kể cả Admin, bảng vận đơn vẫn phục vụ (hai chiều); ERP nguyên vẹn, dữ liệu bảng thường không đổi một dòng |
| Bộ kiểm chỉnh theo ADR-040 | 12 tệp `crm/tests` | Bảng đạo cụ của bài tính năng mang `workflow="waybill"`; bài routing/cây viết lại theo trang phẳng và chiều bị từ chối; bài generic-qua-HTTP chuyển xuống mức dịch vụ |
| Truy vết | `tests/test_truy_vet.py` + docs/06 | 243 tiêu chí (230 tự động), 207 đã có bài, hoãn 23 (AC-11.14 rời danh sách hoãn — đã viết lại và có bài) — khớp |
| Migration | không có migration mới | `makemigrations --check` sạch |

## Chromium (server dev 8021/8020 trên DB `knjsc_db` — có đủ bảng MKT/Sale/perf thật)

Ảnh ở `docs/kiem-thu/crm-mot-bang-2026-09-24/`, tài khoản `quantri` (Admin — vai dễ lộ nhất):

| Bước | Kết quả |
|---|---|
| Trang chủ KN CRM | Không nhắc tới Báo cáo Marketing, không còn chữ "Quý" (`01`) |
| Thư mục `/thu-muc/` | Chỉ **Vận đơn mới**; không MKT/Sale, không cấp Quý/Tháng (`02`) |
| Gõ thẳng `/bang-tinh/bao_cao_mkt/` | **404** dù là Admin (`03`) |
| ERP `/bang/bao_cao_mkt/` | **200**, Bảng dữ liệu hiện như cũ — dữ liệu không đổi (`04`) |

## Chưa kiểm / còn nợ

- Chưa chạy trên VPS. Không migration — phát hành chỉ cần image mới.
- Bài trình duyệt (`trinh_duyet`) của cây thư mục cũ trong `tests/e2e` chưa rà lại trên
  môi trường máy ảo (nhóm này vốn flaky ở đây) — đường đi mới đã phủ bằng bài HTTP.
- Bộ đếm docs/06 (243/230/207) **chỏi với PR #31/#34/#35** — PR gộp sau rebase chỉnh
  số theo thông báo của `test_truy_vet`.
- Khoảng trống ghi trong ADR-040, chờ chủ dự án xếp lịch: Leader/Manager sửa & xoá báo
  cáo cấp dưới; nơi sửa từng ô cho bảng thường.
