# Kiểm chứng — Nút Tôi / Toàn bộ, nhân viên Vận đơn sửa toàn bảng, bỏ Chế độ xem (ADR-033) — 17.09.2026

Quyết định: [ADR-033](quyet-dinh/033-pham-vi-toi-toan-bo-va-quyen-sua-van-don.md).
Môi trường: máy ảo Claude Code trên web (Linux, Postgres 16 local, Chromium
Playwright), **không phải VPS**. Nhánh `codex/crm-update-solar-ui`.

## Bài kiểm tự động

Lệnh, từ `app/`, Postgres dev đang chạy, một tiến trình pytest:

```
python -m pytest --ds=knjsc.settings.test -p no:cacheprovider -q -m "not trinh_duyet" \
  crm/tests orders/tests forms_builder/tests tests
```

| Nhóm | Kết quả |
|---|---|
| `crm/tests/test_pham_vi_toi_toan_bo.py` (AC-33.1 → 33.7 + ngân sách truy vấn) | 8 đạt |
| `crm/tests/test_waybill_feedback.py`, `test_optimization.py`, `test_prepare_destination.py` sau khi sửa theo ADR-033 | 63 đạt |
| Toàn bộ `crm/tests orders/tests forms_builder/tests tests core/tests` sau khi rebase lên 8 commit Codex 17.09 (đợt sửa 19 bài đỏ) | 3 bài đỏ do quyết định mới, sửa cùng lượt: `test_market_currency::test_assigned_delivery_can_confirm_on_any_waybill_profile` (dòng chưa giao nay sửa được → 400 xác nhận tiền thay vì 403), `test_luong_ba_bo_phan::test_mot_ngay_cua_cong_ty` (Vận đơn thấy đơn mới ngay); 2 bài đếm `test_truy_vet` → cập nhật docs/06. Chạy lại: 0 đỏ |
| `manage.py makemigrations --check --dry-run` | Không thiếu migration |
| AC-33.7 | Migration 0013 lùi về 0012 rồi tiến lại trên DB test: `delivery_view_all` mất, `delivery_view_version` còn, dữ liệu còn |
| `python scripts/dong-bo-skill.py --check` | PASS |

Bộ đếm `docs/06` cập nhật theo thông báo của `test_truy_vet`: 198 tiêu chí,
185 tự động, 13 thủ công, 161 trên 185 có bài kiểm (24 hoãn của Codex giữ nguyên).

## Trình duyệt (Chromium headless, dịch vụ 8021 `settings.bangtinh`, bảng crmThuận `van_don_moi`)

Dữ liệu `manage.py nap_du_lieu_van_don_moi`: 10.000 đơn, 5.000 giao `vd.staff`,
5.000 giao `vd.manager`. Đo bằng `scratchpad/kiem_pham_vi.py`, `kiem_o.py`.

| Kiểm | vd.staff 1440 | vd.staff 390 | vd.manager 1440 | quantri 1440 |
|---|---|---|---|---|
| Có `#mg-pham-vi`, không còn `#mg-mode` | có / không | có / không | có / không | **không** / không |
| Mở bảng lần đầu | 10.000 dòng | 10.000 | 10.000 | 10.000 |
| Bấm **Tôi** → URL `?cua_toi=1`, nút Tôi `aria-pressed=true` | 5.000 dòng | 5.000 | 5.000 | — |
| Tải lại `/bang-tinh/van_don_moi/` không tham số | vẫn `?cua_toi=1`, 5.000 | như trái | như trái | — |
| Bấm **Toàn bộ** → URL bỏ tham số | 10.000 | 10.000 | 10.000 | — |
| Bấm ô Tên khách một lần | mở `<input class="o-nhap">` ngay | — | như trái | — |
| Enter trong ô | ô hiện tại xuống dòng kế (`mg-501559` → `mg-501560`), ô nhập vẫn mở | — | như trái | — |
| Bấm một lần ô Phụ trách VD | mở vùng đọc `#mg-reader`, không hộp thoại | — | như trái (hộp Phân công vẫn mở bằng F2/Enter/bấm đúp hoặc nút Phân công) | — |

`sale.staff` cũng có nút (cột phụ trách CSKH), bấm ô mở ô nhập, Enter xuống hàng.
Ảnh: `vd.staff-1440-toi.png`, `vd.staff-390-toi.png`, `vd.manager-1440-toi.png`,
`quantri-1440-toan-bo.png` (gửi chủ dự án trong phiên; không đưa vào kho mã).

## Chưa kiểm

- Chưa chạy trên VPS; chưa đo tải với `cua_toi=1` ở 300.000 dòng (bộ lọc là một
  điều kiện `assignment.<trường>_id = ?` trên bảng phân công có chỉ mục, cùng dạng
  với bộ lọc phạm vi cũ của Staff Vận đơn).
- Script Codex đã sửa (`kiem-thu-shared-grid.cjs` và 7 tệp khác, bỏ bấm `#mg-mode`)
  chưa chạy lại vì máy ảo không có `playwright` cho Node; chỉ đọc lại mã.
- IME thật, Firefox, Safari.
