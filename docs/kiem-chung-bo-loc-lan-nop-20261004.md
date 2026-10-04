# Biên bản kiểm chứng — Báo cáo Sale bỏ cột Lần nộp; bộ lọc kéo tới được nút Áp dụng (04.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án thử `Staging` ở máy local 04.10.2026: (1) "tôi nhớ là cái lần nộp này đã bỏ rồi mà" — ảnh báo cáo Sale còn cột Lần nộp; hỏi lại thì chọn **bỏ cột Lần nộp ở Sale**, giữ Loại tiền; (2) "thanh kéo không kéo được hết xuống chỗ áp dụng mà phải kéo cả page xuống" |
| Quyết định | [ADR-047 bổ sung 04.10](quyet-dinh/047-bao-cao-mkt-tien-viet.md); [ADR-042 sửa 04.10](quyet-dinh/042-bao-cao-tong-hop-nhu-anh-mau.md) (TL-73) |
| Tiêu chí | AC-47.7, AC-42.17 (mới); AC-47.6, AC-42.15, AC-22.13, AC-22.25, AC-42.7 đổi chữ |
| Nhánh | `claude/knerp-erp-chinh-sua-hfi7w8` từ `Staging` `a4fd869`; PR nháp về `Staging` |
| Môi trường | Máy ảo Claude Code trên web: Python 3.11.15, Django 5.2.6, PostgreSQL 16.13 cục bộ, Redis, Chromium của Playwright 1.56 |

## Đã đo

### Dựng lại lỗi trước khi sửa (mã `Staging` `a4fd869`)

CSDL nháp có 726 báo cáo MKT; `sale.manager`, `mkt.manager` mở Báo cáo tổng hợp kỳ 01–30/09/2026; trang ở đầu, kéo
thanh cuộn của bộ lọc tới cuối rồi đo (kịch bản Playwright, 5 cỡ khung nhìn × 2 nguồn).

| Đo | Trước sửa | Sau sửa |
|---|---|---|
| Đáy nút Áp dụng so với đáy vùng nội dung `main.noi-dung` | **lọt dưới 71 px** ở cả 10 trường hợp | **nằm trên 51 px** ở cả 10 trường hợp |
| Điểm giữa nút Áp dụng có trúng chính nút | Không (trúng thanh menu dưới đáy) | Có |
| Chiều cao bộ lọc ở 1366×768 (`--report-panel-fit`) | 550 px, đáy ở y = 759 (vùng nội dung tới 669) | 428 px, đáy ở y = 637 |
| Trang cuộn được thêm vì bộ lọc (1366×768) | 123 px | 1 px (làm tròn) |

Cỡ đã đo: 1366×768, 1366×657, 1920×937, 1536×730, 1280×720. Nguyên nhân: bộ lọc đứng dưới hàng chip, thấp hơn đỉnh vùng
nội dung 115 px, mà chiều cao lại đặt bằng cả vùng nội dung trừ 24 px.

### Bài kiểm

| Kiểm | Lệnh (từ `app/`) | Kết quả |
|---|---|---|
| Bài mới trên mã `Staging` (giữ nguyên bài, cất phần sửa bằng `git stash`) | `python -m pytest reports/tests/test_sale_an_lan_nop.py "reports/tests/test_bo_cuc_bao_cao_e2e.py::test_ap_dung_trong_man_hinh_khong_can_cuon_trang"` | **3/3 đỏ** đúng chỗ: khối ngày Sale còn cột `lan` (AC-47.7); đáy bộ lọc 759 > 669, nút Áp dụng không bấm trúng, ở nguồn Sale và MKT (AC-42.17) |
| Bài mới sau sửa | cùng lệnh, thêm AC-42.15 | 4/4 đạt |
| Nhóm báo cáo, biểu mẫu, Tổng quan, truy vết | `python -m pytest reports forms_builder dashboard tests/test_truy_vet.py -m "not trinh_duyet"` | Trước khi sửa bài cũ: 2 đỏ đúng dự kiến — AC-22.13 (khối ngày Sale mong cột Lần nộp) và truy vết (AC-42.17, 47.7 chưa vào docs/04); sửa bài, thêm AC vào docs/04 và bộ đếm docs/06 |
| Toàn bộ phía máy chủ | `python -m pytest -m "not trinh_duyet"` | **2.915 đạt, 7 bỏ qua**; 3 bài truy vết đỏ vì docs/04 được sửa giữa lượt (bài đọc docs/04 lúc nạp, docs/06 lúc chạy nên hai bên lệch 318/320) — chạy lại riêng `tests/test_truy_vet.py` trên tài liệu cuối: 36/36 đạt |
| Bước trình duyệt 2 như CI | `python -m pytest -m trinh_duyet --ignore=tests/e2e -vv -rs --durations=10 -o faulthandler_timeout=120` | **16 đạt, 9 bỏ qua, 0 đỏ** (bài bỏ qua cần Chrome trên máy thật, như mọi lượt); đạt đủ 11 bài bố cục báo cáo gồm AC-42.15 và hai lượt AC-42.17, 3 bài form nhập, 2 bài lưới |

### Kiểm tay trên máy chủ thử

- `sale.staff` nộp **hai** báo cáo Sale trong ngày bằng form thật (Thị trường Canada): cả hai lưu được, về Lịch sử.
- `sale.manager` mở Báo cáo tổng hợp nguồn Sale hôm nay, cùng dữ liệu trên hai bản mã:

| Chỗ | `Staging` | Nhánh này |
|---|---|---|
| Khối ngày (Không gộp), cột định danh | STT · Team · Nhân sự · Leader · **Lần nộp** · Loại tiền | STT · Team · Nhân sự · Leader · Loại tiền |
| Khối Gộp | Ngày · Nhân sự · **Lần nộp** · Loại tiền | Ngày · Nhân sự · Loại tiền |
| Số dòng của hai lần nộp | 2 | 2 |
| Excel | có cột "Lần nộp", ô "Lần 1 · 21:12", "Lần 2 · 21:13" | không có; vẫn có "Loại tiền" |
| Lỗi JavaScript | 0 | 0 |

## Chưa kiểm / để lại

- Bước trình duyệt 1 như CI (`tests/e2e`, lưới KN CRM): mã đổi lần này không nằm ở lưới; để CI của PR chạy. Trên máy ảo
  này 9 bài `tests/e2e/test_pha_luoi_ghi_chu.py` vốn đỏ vì phông Google qua proxy, CI không gặp.
- Toàn màn hình và ngăn kéo màn hình hẹp không đổi (quy tắc chiều cao chỉ áp ở màn ≥ 901 px, ngoài Toàn màn hình).
- Chưa chạy trên máy chủ dự án, Windows thật và VPS. Không migration; phát hành chỉ cần mã mới.
