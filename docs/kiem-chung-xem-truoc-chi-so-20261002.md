# Biên bản kiểm chứng — Xem trước chỉ số khi nộp báo cáo ngày (02.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Khách hàng: Marketing gõ số thì thấy ngay chỉ số trước khi nộp; chủ dự án chốt mockup 02.10.2026 |
| Quyết định | [ADR-043 bổ sung 02.10](quyet-dinh/043-form-nhap-bao-cao.md) |
| Tiêu chí | AC-43.6 |
| Nhánh | `claude/xem-truoc-chi-so` từ `Staging` `7f8fb82`, PR nháp về `Staging` |
| Môi trường | Máy ảo Claude Code trên web: Python 3, PostgreSQL 16 cục bộ, Chromium Playwright có sẵn |

## Đã đo

| Kiểm | Lệnh (từ `app/`) | Kết quả |
|---|---|---|
| Bài mới trên mã cũ | `python -m pytest reports/tests/test_xem_truoc_chi_so.py` và `-k xem_truoc` của `test_o_nhap_so_e2e.py` | **đỏ** đúng chỗ: chưa có `daily_service.preview_columns`, trang chưa có khối "Xem trước chỉ số", trình duyệt không thấy thẻ `.cs` |
| Bài mới sau sửa | như trên | 2/2 + 1/1 đạt; bài trình duyệt chạy lặp 3 lần đều đạt |
| Trình duyệt (gõ thật) | `test_xem_truoc_chi_so_khi_go` | Số Mess 120, CPQC 13.250.000, Số đơn 8, Doanh số 24.000.000 → CPO **1.656.250 CAD**, Giá Mess **110.416,67 CAD**, CPQC/Doanh số **0,5521**, AOV **3.000.000 CAD**, Tỉ lệ chốt **6,67 %**; xoá Số đơn → CPO, AOV "—"; Số đơn 0 → "chia cho 0"; Hoa Kỳ → hậu tố USD; nộp thật → máy chủ lưu 1656250 / 110416.6667 / 0.5521 / 3000000 / 6.67, khớp số đã xem trước; không lỗi JS |
| Truy vấn | `test_form_co_khoi_xem_truoc` | Thêm một cột tính sẵn, số truy vấn của trang không đổi |
| Ảnh màn hình | Chromium 1440×900 sáng và tối, 390×844 | Thẻ đúng mockup; không tràn ngang ở 390 (hai thẻ một hàng) |
| Toàn bộ | `python -m pytest -m "not trinh_duyet and not cham"` | 2.844 bài, 377 s: 2.842 đạt, 1 bỏ qua, **1 đỏ** — `test_bo_cuc_ngang_form_nhap` (AC-43.4) ghim dòng chip cũ; sửa bài theo thẻ mới, chạy lại tệp đó và bài trình duyệt của form đều đạt |

## Chưa kiểm / để lại

- Chưa chạy trên VPS và máy chủ dự án (Claude Code trên web không tới được); phát hành là bước riêng.
- Form Sale dùng cùng khối; Sale hiện có Tỉ lệ chốt — kiểm qua bài máy chủ, chưa có bài trình duyệt riêng.
- Làm tròn nửa về chẵn bằng số thực JS: đúng với số liệu thường; số cực lớn có thể lệch một đơn vị ở chữ số
  cuối của thẻ, số lưu do máy chủ tính vẫn đúng.
