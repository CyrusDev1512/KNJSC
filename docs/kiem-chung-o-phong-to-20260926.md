# Kiểm chứng — Bỏ hộp đọc, ô phồng to tại chỗ kiểu Google Sheets — 26.09.2026

Nhánh `claude/o-phong-to-tai-cho` tách từ `main`, máy ảo Claude Code. Yêu cầu chủ dự án
(so với Google Sheets): bấm ô thì phồng to tại chỗ, bấm chỗ khác thu về, bỏ hẳn hộp đọc
có tiêu đề + nút ×; giữ nguyên tự giãn dòng và trần 2000 px. Ghi ở ADR-033 bổ sung 26.09.

## Đổi gì

`#mg-reader` giữ id và mọi đường kích hoạt (bấm ô bị cắt; gõ phím trên ô chỉ đọc/phân
công/chi tiết; cột chứng từ; bôi đen chép chữ) — chỉ đổi trình bày: định vị theo khuôn
`positionEditor` (fixed đúng rect ô, chia scale zoom, `clipPath` không đè tiêu đề/cột
ghim), rộng ≥ ô (tối thiểu ~320 px cho cột hẹp), phồng xuống dưới, hết chỗ trong khung
nhìn thì cuộn bên trong. Bấm đúp lên ô phồng tự chuyển tiếp mở editor; Esc và bấm ra
ngoài (kể cả ngoài lưới) đóng. Không đụng `KNJSCRowGeometry.MAX`, `caoTuDong`,
`auto_height`.

## Kiểm tự động (Chromium thật, live server)

| Bài | Kết quả |
|---|---|
| `test_ghi_chu_qua_tran_cat_o_2000_va_o_phong_to` (viết lại) | Phồng đúng góc ô (lệch < 2 px), rộng đủ, phần quá trần **cuộn được**, bấm chân trang thu về; 0 lỗi JS |
| `test_o_cat_ngang_phong_tai_cho_va_bam_dup_mo_editor` (mới) | Ô Tên khách cắt ngang ở dòng 28 px phồng đủ chữ; **bấm đúp lên ô phồng mở đúng editor**; Esc đóng |
| `tests/e2e/test_ghi_chu_tu_gian_dong.py` trọn tệp (12 bài) | 0 đỏ — tự giãn/kéo tay/trần 2000 nguyên trạng |
| `tests/e2e/test_pha_luoi_ghi_chu.py` | 6/9 đạt; **3 bài đỏ do môi trường, không do diff**: `test_dan_nhieu_dong_tu_excel`, `test_dien_thoai_390`, `test_phong_to_125` báo `console.error ERR_CERT_AUTHORITY_INVALID` (tài nguyên ngoài không tin CA proxy máy ảo) — đã chạy đối chứng **trên mã gốc chưa sửa, vẫn đỏ y hệt** |
| `crm/tests` + `tests/test_truy_vet.py` | 0 đỏ; không AC mới, docs/06 giữ nguyên |
| Suite đầy đủ `-m "not trinh_duyet and not cham"` | **2.797 đạt, 1 bỏ qua, 0 đỏ** (329 s) |

Ảnh: `docs/kiem-thu/o-phong-to-2026-09-26/` (2 ảnh từ chính hai bài trên).

## Chưa kiểm

- 3 bài `pha_luoi` kể trên cần chạy lại ở máy có mạng không qua proxy (máy anh / CI).
- Scripts chạy tay `kiem-thu-master-row-height.cjs`, `-ui.cjs`: chuỗi click→Esc→dblclick
  đã soát tay là còn khớp, chưa chạy thật (máy ảo không có bộ dữ liệu MASTER-*).
- Chưa phát hành VPS.
