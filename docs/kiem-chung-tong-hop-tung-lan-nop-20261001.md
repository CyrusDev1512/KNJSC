# Biên bản kiểm chứng — Báo cáo tổng hợp luôn từng lần nộp, nút Chọn nhanh sáng một (01.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 01.10.2026: (1) ngày 01 "Hôm nay" và "Tháng này" cùng sáng; (2) bỏ ô Cách xem và ô Chế độ, mặc định từng lần nộp |
| Quyết định | [ADR-046 bổ sung 01.10.2026](quyet-dinh/046-che-do-so-lieu-khong-quy-doi.md) |
| Tiêu chí | AC-22.22, AC-22.23 (mới); AC-22.20, 38.5, 42.6, 42.7, 46.3, 46.4 (đổi chữ) |
| Nhánh | `claude/tong-hop-tung-lan-nop` từ `main` `b38505e` |
| Môi trường | Máy ảo Claude Code trên web: Python 3, PostgreSQL 16 cục bộ, Chromium Playwright có sẵn |

## Đã đo

| Kiểm | Lệnh (từ `app/`) | Kết quả |
|---|---|---|
| Bài mới trên mã cũ | `python -m pytest reports/tests/test_tung_lan_nop_mac_dinh.py` | 4/4 **đỏ** đúng chỗ (`['hom-nay','thang-nay'] != ['hom-nay']`, còn `name="nhom"`, `parameters` chưa có `ky`) |
| Bài mới sau sửa | như trên | 4/4 đạt |
| Bài cũ ghim cách xem/chế độ trên màn hình | `reports forms_builder dashboard core/tests/test_giao_dien.py tests/test_truy_vet.py` | 23 trường hợp đỏ sau sửa mã (đúng dự kiến: chip Cách xem/Chế độ, `nhom=person`, `che_do=cong`, cột Lần nộp làm nhãn TỔNG CỘNG ôm 5 cột, ghi chú TL-70 "hai nút cùng sáng"); viết lại theo quyết định mới → 1.055 đạt |
| Trình duyệt | `python -m pytest reports/tests/test_bo_cuc_bao_cao_e2e.py` | 5/5 đạt, gồm bài mới AC-22.22 (ngày giả 01.10: bấm Tháng này → chỉ Tháng này sáng, URL `ky=thang-nay`; bấm Hôm nay → chỉ Hôm nay; sửa tay ô ngày → `ky` trống; không có `#nhom`, `#report-che-do`) |
| Ảnh màn hình | Chromium 1440×900 và 390×844, Báo cáo tổng hợp và Bảng dữ liệu dạng báo cáo | Bộ lọc còn Nguồn, Chọn nhanh, Từ/Đến ngày, Sản phẩm, Thị trường, Team, Nhân sự; không tràn ngang ở 390 |
| Toàn bộ | `python -m pytest -m "not trinh_duyet and not cham"` | **2.842 bài: 0 đỏ, 0 lỗi, 1 bỏ qua**, 387 s |

## Viết lại bài cũ — giữ ý, đổi đường kiểm

- Số liệu theo nhóm (Theo nhân viên, sản phẩm, team) và Cộng theo ngày: kiểm ở tầng `activity_service.build`
  (bài tầng service đã có giữ nguyên; AC-46.3 thêm phần Cộng theo ngày ở service).
- Màn hình: URL cũ `nhom=…`, `che_do=cong` khẳng định vẫn 200 và ra từng lần nộp.
- AC-42.6 "(tiếp)": dữ liệu đổi để một ngày vẫn bị tách trang khi mỗi lần nộp là một dòng.
- AC-42.7 Gộp: nguồn Sale/MKT nay là một bảng mọi lần nộp.
- AC-22.19 (lăn chuột, bảng ngắn): trước dùng `nhom=person`; nay lọc một nhân sự để bảng vẫn vừa khung dọc.

## Chưa kiểm / để lại

- Chưa chạy trên VPS và máy chủ dự án; Claude Code trên web không tới được.
- `scripts/kiem-thu-erp-ui.cjs`, `kiem-thu-erp-delivery-ui.cjs` (kịch bản tay, không trong CI) còn chọn `#nhom`
  và đọc `tfoot` — đã lỗi thời từ bố cục khối ADR-042, không sửa trong lượt này.
- Màn tổng quát cũ cho bảng chưa cấu hình nguồn (`reports/views.py`, tab `nhom=`) không đổi.
