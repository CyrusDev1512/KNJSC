# Kiểm chứng — Bố cục thẻ Báo cáo tổng hợp trên Tổng quan ERP — 26.09.2026

Nhánh `claude/sua-bo-cuc-tong-quan` tách từ `main` (`97bff53`), máy ảo Claude Code.
Chủ dự án chụp Tổng quan ERP: chỉ tiêu trong thẻ Marketing/Sale xếp nhiều cột chật, số tiền
bị bẻ giữa chữ số ("626.1 / 00.65 / 3.751 ₫"). Ghi ở `docs/test-log.md` TL-60, tiêu chí AC-22.17.

## Nguyên nhân

| Ngày | Commit | Việc |
|---|---|---|
| 16.09 | `da6e2c0` | "Sửa bố cục chỉ tiêu trên Tổng quan ERP": `static/css/dashboard.css` — mỗi chỉ tiêu một hàng nhãn trái – số phải; đã kiểm 1280/390/1440 ([biên bản](kiem-chung-tong-quan-20260916.md)) |
| 17.09 | `d84a8c1` | "Sửa 19 bài kiểm đỏ": chép 10 dòng `.dashboard-*` bản cũ vào `solarpunk.css` để `core/tests/test_giao_dien.py` hết đỏ — bài quét danh sách `CAC_TEP_CSS` **không có `dashboard.css`** |

`dashboard.css` không ghi đè `grid-template-columns` của `.dashboard-metrics`, nên luật cũ
`repeat(auto-fit,minmax(120px,1fr))` của `solarpunk.css` vẫn áp: lưới nhiều cột × mỗi ô lại
chia đôi nhãn/số → số còn vài chục px và bị bẻ. Lỗi có trên `main` từ 17.09, tức cả VPS.

Khối "Hoạt động" bị cắt bên phải trong ảnh chủ dự án là do ảnh chụp cắt khung (thanh điều
hướng đáy căn giữa ở ~930 px → cửa sổ ~1860 px); đo bằng bài dưới: không tràn ngang.

## Sửa

- `static/css/solarpunk.css`: gỡ khối 10 luật `.dashboard-*` — luật của khối chỉ còn ở
  `dashboard.css` (nạp riêng ở `dashboard/tong_quan.html`, nơi duy nhất include `_activity.html`).
- `core/tests/test_giao_dien.py`: thêm `dashboard.css` vào `CAC_TEP_CSS`.
- Không đổi template, số liệu, nguồn, công thức, URL.

## Kiểm (TDD)

| Bài | Trước sửa | Sau sửa |
|---|---|---|
| `core/tests/test_giao_dien.py::test_luat_the_bao_cao_tong_quan_chi_khai_mot_cho` (AC-22.17, tĩnh) | **đỏ**: luật `.dashboard-*` lẫn trong `solarpunk.css` | xanh |
| `reports/tests/test_bo_cuc_bao_cao_e2e.py::test_the_tong_quan_moi_chi_tieu_mot_hang` (AC-22.17, Chromium thật, Manager Sale, Doanh số 4.419.192.172.800) | **đỏ**: 1440 px chỉ tiêu xếp 2 cột (left 537/726), "Doanh số" **bẻ 3 dòng** | xanh: 1440 px một cột, mọi số một dòng, nhãn–số cùng hàng; 390 px không tràn ngang |
| `core/tests/test_giao_dien.py` trọn tệp + bài trên | — | **624 đạt, 0 bỏ qua, 0 đỏ** |
| `tests/test_truy_vet.py` (docs/06 → 276 / 263 tự động / 240 có bài) | — | 36 đạt |
| Suite đầy đủ `-m "not trinh_duyet and not cham"` | — | **2.799 đạt, 1 bỏ qua, 0 đỏ** (330 s) |

Ảnh `docs/kiem-thu/bo-cuc-tong-quan-2026-09-26/`: `truoc-1440.png` (mã cũ, cùng dữ liệu),
`sau-1440.png`, `sau-390.png` — chụp từ chính bài Chromium.

## Chưa kiểm

- Nền tối chưa chụp riêng (luật màu không đổi, chỉ gỡ luật bố cục trùng).
- Chưa phát hành VPS — chủ dự án quyết.
