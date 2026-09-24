# Kiểm chứng toàn hệ thống: unit + functional + migration + smoke — 24.09.2026

Nhánh `claude/crm-chi-mot-bang-van-don` (nền ADR-040), máy ảo Claude Code, PostgreSQL 16
cục bộ. Mục đích: bằng chứng hệ thống hoạt động trước khi chủ dự án check local và quyết
gộp — theo yêu cầu chủ dự án 24.09.

## 1. Unit + functional (pytest đầy đủ, trừ bài trình duyệt và bài chậm)

```
pytest -m "not trinh_duyet and not cham" --junitxml
```

| Số | Kết quả |
|---|---|
| Tổng bài | 2.530 |
| Đạt | **2.529** |
| Đỏ / lỗi | **0 / 0** |
| Bỏ qua | 1 |
| Thời gian | 294 giây |

Gồm đủ: phân quyền hai chiều mọi đường dẫn mới, CAS/biên nhận của lưới, truy vết
docs/04 ↔ docstring (`test_truy_vet` xanh, 243 tiêu chí / 230 tự động / 207 có bài).

Lưu ý trung thực: lượt chạy đầu bị đứt giữa chừng vì thao tác vận hành của phiên
(xoá nhầm `postmaster.pid` làm Postgres tự tắt) — không phải lỗi mã; dựng lại và
chạy trọn lượt hai ra số ở trên.

## 2. Migration (xuôi và ngược)

- Trong suite có **16 bài chuyên migration** (roundtrip 0013/0015, payment legacy,
  activity, units, `test_chuyen_doi` đối chiếu model ↔ tệp chuyển đổi...) — đạt hết.
- Trên DB trống `knjsc_smoke`: `migrate` xuôi toàn bộ **5,1 s**; quay lùi
  `forms_builder 0015 → 0014` rồi tiến lại: OK, không kẹt khoá.
- `makemigrations --check`: "No changes detected" — không thiếu tệp chuyển đổi.

## 3. Smoke — diễn tập máy sạch (kịch bản đúng launcher `KN JSC.bat`)

DB trống → `migrate` → `tao_bang_van_don` → `du_lieu_mau` → `configure_erp_reports`
→ `configure_delivery_daily_report` → `manage.py check`: **tất cả OK** (script ở
scratchpad, các bước in `== ... OK`). Sau đó bật thật hai dịch vụ (8020 + 8021) trên
DB đó và đi qua các trang chính bằng Chromium, tài khoản `quantri`:

| Trang | Kết quả |
|---|---|
| Đăng nhập KN CRM → trang chủ | vào được, về `/` (`01`) |
| Thư mục `/thu-muc/` | 200 — chỉ Vận đơn mới, không Quý/Tháng |
| Lưới `/bang-tinh/van_don/` | 200, JSON `total = 0` (máy sạch chưa có đơn — đúng ADR-018: `du_lieu_mau` không tạo đơn demo) (`02`) |
| Thống kê `/thong-ke/` | 200 |
| `/bang-tinh/bao_cao_mkt/` | **404** — đúng ADR-040 |
| ERP trang chủ + Bảng dữ liệu MKT | 200 + 200, dữ liệu mẫu hiện đủ (`03`, `04`) |
| Lỗi JavaScript | **0** trên cả đường đi |

Ảnh ở `docs/kiem-thu/smoke-2026-09-24/`. Ghi chú môi trường: mật khẩu mẫu phải đặt
bằng settings chạy thật (settings test dùng hasher MD5 nên đặt từ đó thì server
thật không xác thực được — đặc thù máy kiểm, không phải lỗi hệ thống; launcher
thật chạy `cap_nhat_mat_khau_mau` đúng settings nên không gặp).

## Chưa kiểm

- Bài trình duyệt `trinh_duyet`/`cham` (e2e Playwright, hiệu năng) không nằm trong
  lượt này — nhóm e2e vốn flaky trên máy ảo; hiệu năng có biên bản riêng 16.09 và
  22.09. Bỏ qua không phải là đã kiểm.
- VPS và domain thật: ngoài tầm với của máy ảo.
