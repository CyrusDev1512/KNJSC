# Kiểm chứng — Bỏ hộp đọc, ô phồng to tại chỗ kiểu Google Sheets — 26.09.2026

Nhánh `claude/o-phong-to-tai-cho` tách từ `main`, máy ảo Claude Code. Yêu cầu chủ dự án
chốt hai đợt (so với Google Sheets; đợt hai sau khi test bản đầu: "1 click thì y như
chúng ta, 2 click mới là mở rộng"): **click đơn chỉ chọn ô**; bấm đúp thì ô sửa được mở
ô nhập (khung nhập tự giãn), ô chỉ đọc bị cắt chữ thì phồng to tại chỗ, bấm chỗ khác/Esc
thu về; bỏ hẳn hộp đọc có tiêu đề + nút ×; giữ nguyên tự giãn dòng và trần 2000 px.
Ghi ở ADR-033 bổ sung 26.09.

## Đổi gì

- **Đợt 1:** `#mg-reader` giữ id — đổi trình bày: định vị theo khuôn `positionEditor`
  (fixed đúng rect ô, chia scale zoom, `clipPath` không đè tiêu đề/cột ghim), rộng ≥ ô
  (tối thiểu ~320 px cho cột hẹp), phồng xuống dưới, hết chỗ trong khung nhìn thì cuộn
  bên trong. Bấm đúp lên ô phồng tự chuyển tiếp mở editor; Esc và bấm ra ngoài đóng.
- **Đợt 2 (chỉnh theo test của chủ dự án):** bỏ mở phồng ở `pointerup` — click đơn chỉ
  `choose()`; trong `edit()` ô chỉ đọc **đang bị cắt chữ** thì bấm đúp/F2/Enter phồng
  thay cho message "Ô này chỉ đọc." (thấy đủ chữ vẫn message như cũ); đường gõ-phím-trên-
  ô-chỉ-đọc giữ nguyên (18.09). Ô sửa được bấm đúp vẫn mở ô nhập — khung nhập cột văn
  bản dài tự giãn theo nội dung tới trần 2000 px trong giới hạn khung nhìn
  (`positionEditor` + maxHeight), đúng "mở rộng ô" trong video Sheets.
- Không đụng `KNJSCRowGeometry.MAX`, `caoTuDong`, `auto_height`; cột chứng từ và chỗ
  bôi đen chép chữ giữ nguyên.

## Kiểm tự động (Chromium thật, live server)

| Bài | Kết quả |
|---|---|
| `test_ghi_chu_qua_tran_click_chi_chon_bam_dup_mo_o_nhap` (viết lại) | Click đơn: reader + editor đều im, ô mang `mg-current`; bấm đúp: ô nhập mở, textarea chứa trọn 12.600 ký tự, khung giãn hết chỗ khung nhìn; Esc đóng; 0 lỗi JS |
| `test_o_cat_ngang_click_chi_chon_bam_dup_mo_o_nhap` (viết lại) | Tên khách cắt ngang: click đơn chỉ chọn; bấm đúp mở ô nhập giữ nguyên giá trị; Esc đóng |
| `test_o_chi_doc_bi_cat_bam_dup_phong_to` (mới) | CSKH được giao chỉ xem (ADR-033): click đơn chỉ chọn; bấm đúp thì Ô PHỒNG đúng góc ô (lệch < 2 px), KHÔNG mở ô nhập; bấm chân trang thu về |
| `tests/e2e/test_ghi_chu_tu_gian_dong.py` trọn tệp | **12 đạt, 1 bỏ qua (dòng trống — như cũ), 0 đỏ** — tự giãn/kéo tay/trần 2000 nguyên trạng |
| `tests/e2e/test_pha_luoi_ghi_chu.py` | 3/9 đạt hôm nay; **6 bài đỏ đều do môi trường, không do diff**: chỉ đổ ở `assert not loi_js` với `console.error ERR_CERT_AUTHORITY_INVALID` (tài nguyên ngoài không tin CA proxy máy ảo), các khẳng định chức năng phía trên đều đạt; hôm nay proxy chặn rộng hơn hôm 26.09 sáng (3 bài) |
| `crm/tests` + `tests/test_truy_vet.py` | 0 đỏ trừ 3 bài `test_luoi_dong_trong_va_ghim_e2e` đỏ vì lưới không tải trong môi trường hôm nay — **đối chứng `git stash` trên mã chưa sửa: đỏ y hệt**, không do diff; không AC mới, docs/06 giữ nguyên |
| Suite đầy đủ `-m "not trinh_duyet and not cham"` | **2.797 đạt, 1 bỏ qua, 0 đỏ** (334 s) |

Ảnh: `docs/kiem-thu/o-phong-to-2026-09-26/` (3 ảnh từ chính ba bài trên).

## Chưa kiểm

- Các bài trình duyệt đỏ-môi-trường kể trên cần chạy lại ở máy có mạng không qua proxy
  (máy anh / CI).
- Scripts chạy tay `kiem-thu-master-row-height.cjs`, `-ui.cjs` (click→khẳng định không
  phồng→dblclick→editor) và hai script capacity (chỉ số `reader` đổi sang đo mở ô nhập
  bằng bấm đúp, giữ tên so sánh lịch sử): đã soát tay là khớp hành vi mới, chưa chạy
  thật (máy ảo không có bộ dữ liệu MASTER-*; ba script capacity vốn được PR #38 đánh
  dấu "cần làm lại").
- Chưa phát hành VPS.
