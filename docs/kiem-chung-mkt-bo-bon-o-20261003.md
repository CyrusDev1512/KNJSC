# Biên bản kiểm chứng — Form báo cáo Marketing bỏ bốn ô (03.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 03.10.2026: "Bỏ cả bốn ô" Sản phẩm, Thị trường, Tệp khách hàng, Loại tiền khỏi form Nộp báo cáo Marketing; tiền vẫn VND (ADR-047), làm Marketing trước |
| Quyết định | [ADR-048](quyet-dinh/048-form-mkt-bo-bon-o.md) |
| Tiêu chí | AC-48.1 → 48.6 (mới); AC-22.13, 22.24, 22.25, 38.4, 42.7, 42.11, 43.2, 43.6, 46.4, 47.2 đổi chữ |
| Nhánh | `claude/mkt-bo-bon-o` từ `claude/bao-cao-mkt-vnd` `5e96bb7` (PR #83, chưa gộp), PR nháp về `Staging` — gộp #83 trước |
| Môi trường | Máy ảo Claude Code trên web: Python 3.11.15, Django 5.2.6, PostgreSQL 16.13 cục bộ, Redis, Chromium của Playwright 1.56 |

## Đã đo

| Kiểm | Lệnh (từ `app/`) | Kết quả |
|---|---|---|
| Bài mới trên mã nền | 5 bài máy chủ chạy trên bản sao `5e96bb7` (git worktree); bài trình duyệt AC-48.5 cũng vậy | **6/6 đỏ** đúng chỗ: form còn bốn ô (48.1); cờ bắt buộc cấp cột không được gỡ (48.2); URL cũ `thi_truong=Klingon` trả 400 (48.3); kết quả chưa có `fixed_currency`, bảng còn cột Loại tiền (48.4); form còn ô Sản phẩm (48.5); Thống kê MKT còn biểu đồ theo sản phẩm (48.6) |
| Bài mới sau sửa | `python -m pytest reports/tests/test_mkt_bo_bon_o.py crm/tests/test_thong_ke_mkt_bo_san_pham.py`; `reports/tests/test_o_nhap_so_e2e.py` | 6/6 đạt |
| Bài cũ theo luật cũ | `reports forms_builder crm dashboard core tests/test_truy_vet.py -m "not trinh_duyet"` | 12 bài đỏ đúng dự kiến (form MKT có bốn ô, lọc `sp`/`tep` trên nguồn MKT, cột Loại tiền của bảng MKT) và bài truy vết (AC-48.x chưa vào docs/04); sửa bài theo ADR-048, thêm AC-48.x vào docs/04 và bộ đếm docs/06 |
| Các tệp bài vừa sửa | 12 tệp `reports/tests/…` liên quan và hai tệp bài mới, `-m "not trinh_duyet"` | Đạt hết |
| Bước trình duyệt 1 như CI | `python -m pytest tests/e2e -m trinh_duyet -vv -rs --durations=10 -o faulthandler_timeout=120` | 37 đạt, 2 bỏ qua, 9 đỏ — cả 9 là `test_pha_luoi_ghi_chu.py` vì chứng chỉ proxy (xem dưới); lượt 02.10 trên máy này cũng đúng 9 bài đó |

## Chưa kiểm / để lại

- **Đang chạy lúc ghi biên bản này** (bổ sung kết quả ở commit sau): toàn bộ `-m "not trinh_duyet"` (tới 70 % chưa có
  bài đỏ), bước trình duyệt 2 như CI, kiểm tay trước/sau trên máy chủ thử với dữ liệu MKT cỡ thật.
- Chưa chạy trên máy chủ dự án và VPS. Lên VPS: bước `configure_erp_reports` có sẵn trong quy trình phát hành gỡ bốn
  ô; không có tệp chuyển đổi mới (`reports/0006` thuộc #83).
- 9 bài `tests/e2e/test_pha_luoi_ghi_chu.py` đỏ trên máy ảo này vì trình duyệt không tin chứng chỉ của proxy
  (lỗi console `net::ERR_CERT_AUTHORITY_INVALID`) — giống mọi lượt chạy trước trên máy này; CI không gặp.
- Báo cáo Sale chưa đổi (chủ dự án: làm Marketing trước). DS Chốt (TT) của MKT vẫn "—" (ADR-047).
- `scripts/kiem-thu-erp-ui.cjs` (kịch bản tay, không chạy trong CI) chỉ sửa phần điền Sản phẩm và Thị trường; bước chọn
  ô Cách xem `#nhom` (bỏ từ 01.10) vẫn còn trong kịch bản, chưa chạy lại kịch bản này.
