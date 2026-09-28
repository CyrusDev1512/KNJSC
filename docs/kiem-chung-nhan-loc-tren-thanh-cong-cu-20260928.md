# Kiểm chứng — Nhãn bộ lọc trên thanh công cụ lưới (AC-21.14) — 28.09.2026

Nhánh `claude/nhan-loc-tren-thanh-cong-cu` tách từ `main` (`05f8f4f`), máy ảo Claude Code, PostgreSQL 16,
Chromium.

## Vấn đề

Chủ dự án: "thông báo đã chọn filter nên nằm ở giữa Cột và Định dạng, không đẩy trang tính xuống".
`#mg-chips` là một hàng riêng dưới `.mg-toolbar`; có nhãn thì hàng cao thêm và lưới tụt xuống.

## Sửa

- `templates/crm/master_grid.html`: chuyển `#mg-chips` vào `.mg-toolbar`, ngay trước nút Định dạng.
- `static/css/master-grid.css`: trong thanh công cụ, nhãn chiếm chỗ trống còn lại (`flex:1 1 0`), một
  hàng, nhiều nhãn thì cuộn ngang; có nhãn thì rộng tối thiểu 140 px. JS không đổi (vẫn thay nội dung
  `#mg-chips` theo id, bấm × vẫn bỏ lọc tại chỗ).

## Kiểm

| Kiểm | Kết quả |
|---|---|
| `tests/e2e/test_nhan_loc_tren_thanh_cong_cu.py` (AC-21.14, 1440 và 1280 px) trên mã cũ | **đỏ**: nhãn không nằm trong thanh công cụ; đo riêng đỉnh lưới: **103 → 137 px** khi bật lọc |
| Cùng bài sau sửa | 2 đạt: đỉnh lưới giữ nguyên, khung nhãn nằm giữa Cột và Định dạng, cùng hàng, nhãn đầu thấy trọn, không tràn ngang |
| `tests/test_truy_vet.py`, `core/tests/test_giao_dien.py`, `crm/tests/test_master_grid.py` (docs/06 → 280 / 267 / 244) | đạt |

Ảnh: `docs/kiem-thu/nhan-loc-tren-thanh-cong-cu-2026-09-28/`.

## Chưa kiểm

- Màn hẹp hơn khoảng 1100 px: thanh công cụ vốn xuống dòng, nhãn có thể sang hàng mới cùng các nút.
- Chưa phát hành VPS.
