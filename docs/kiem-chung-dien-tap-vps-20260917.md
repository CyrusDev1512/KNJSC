# Diễn tập nâng cấp VPS — 17.09.2026

Đưa VPS từ `0907cdd` (bản đang chạy, 16.09) lên `49e2872` (đầu nhánh
`codex/crm-update-solar-ui`) — **13 commit**. Diễn tập trên máy ảo Claude Code,
**không chạm VPS thật**.

## Cách dựng

Không thử trên máy trắng, vì máy trắng không phản ánh rủi ro thật. Dựng đúng
tình huống VPS: database có sẵn dữ liệu ở trạng thái `0907cdd`, rồi mới nâng cấp.

```
git worktree add <tmp>/vps-cu 0907cdd
# tại worktree cũ, DB knjsc_vps:
migrate --noinput; tao_bang_van_don; du_lieu_mau; nap_du_lieu_van_don_moi
# rồi chuyển sang mã 49e2872, chạy đúng dãy lệnh của deploy/production/README.md
```

Postgres 16 cổng 5434, `knjsc.settings.dev` để dựng, `knjsc.settings.prod` để
kiểm khởi động, Chromium 1440×900 qua Playwright.

## Kết quả

| Kiểm | Kết quả |
|---|---|
| `migrate --noinput` | Áp đúng **một** migration mới: `reports.0003_report_revision` |
| `tao_bang_van_don` | `van_don` 41 cột, `van_don_db` 26 cột |
| `configure_erp_reports` | Cấu hình `bao_cao_sale`, `bao_cao_mkt`, `van_don_moi` |
| `configure_delivery_daily_report` | Xong, không tạo dòng nghiệp vụ |
| **Dữ liệu nghiệp vụ trước/sau** | **10.005 dòng → 10.005 dòng**, không mất, không sinh thừa |
| Quay lui `reports 0003 → 0002` | Được, dữ liệu nguyên vẹn |
| Tiến lại `0002 → 0003` | Được, dữ liệu nguyên vẹn |
| `manage.py check --deploy` (prod) | Chỉ một cảnh báo `security.W009` về `SECRET_KEY` — là khoá giả của diễn tập |
| `collectstatic --noinput` | 155 tệp |
| `docker compose config` (production) | Hợp lệ, 9 dịch vụ: db, broker, cache, erp, crm, proxy, worker, beat, heavy |
| Gunicorn `settings.prod` 2 worker × 2 thread | Khởi động được; ERP 301 → https (đúng, có nginx phía trước), sau `X-Forwarded-Proto: https` thì mọi đường trả 200/302 đúng |
| Báo cáo tổng hợp sau nâng cấp | **Ra bản mới** — có "Toàn màn hình", khung bảng `report-table-scroll` |
| Lưới CRM sau nâng cấp | "10.000 dòng khớp bộ lọc", vẽ 360 ô, không lỗi JS |
| Tổng quan ERP, Bảng dữ liệu | Mở được, có dữ liệu |

## Lần diễn tập thứ hai — sau khi Codex đẩy `9949062` (ADR-033)

Cùng cách dựng, DB lại ở `0907cdd` với 10.005 dòng; cố ý đặt
`delivery_view_all = TRUE` cho `van_don_moi` để xem migration bỏ cột ứng xử ra sao.

| Kiểm | Kết quả |
|---|---|
| `migrate` | Áp **hai** migration: `forms_builder.0013_remove_tabledef_delivery_view_all`, `reports.0003_report_revision` |
| Cột `delivery_view_all` | Bị bỏ; `delivery_view_version` giữ lại đúng ADR-033 |
| Dữ liệu trước/sau | 10.005 → 10.005 |
| Quay lui cả hai rồi tiến lại | Được; cột về `false` (giá trị `TRUE` đặt thử mất — chấp nhận, tính năng đã bỏ) |
| Chrome, đăng nhập `vd.staff` (nhân viên Vận đơn) | Thấy **10.000 dòng**; nút "Chế độ: Xem" **không còn**; có nút **Tôi / Toàn bộ** |
| Bấm "Tôi" | 5.000 dòng, URL có `cua_toi=1` |
| Sửa ô `ten_khach` của dòng không được giao | Ghi xuống DB, còn sau F5 — đúng quyết định ADR-033 |
| Lỗi JS | Không |
| `pytest` đầy đủ trên đầu nhánh (cả `cham`, `trinh_duyet`) | **2506 đạt, 18 bỏ qua, 0 đỏ** |

## Hai điều chủ dự án phải biết trước khi phát hành

**1. Cột tiền của Báo cáo Marketing sẽ trống.** Sau nâng cấp, màn hình hiện dải
vàng *"Bộ lọc có nhiều loại tiền hoặc báo cáo cũ chưa xác định loại tiền. Các chỉ
tiêu tiền tạm để trống…"* và mọi cột tiền hiện `—`. Đây là `currency_safe_result()`
cố ý không cộng lẫn tiền tệ (quy tắc 6), **không phải lỗi**. Đo trên dữ liệu diễn
tập: **5/5 dòng `bao_cao_mkt` không có `loai_tien`**.

Đã kiểm cách chữa: điền `loai_tien` cho các dòng cũ thì dải vàng biến mất, màn
hình hiện *"Đơn vị tiền: USD"* và mọi cột tiền có số lại. Nên **trước hoặc ngay
sau khi phát hành, phải bổ sung Loại tiền cho các dòng báo cáo cũ trên VPS**,
nếu không người dùng mở ra thấy bảng trống số.

**2. Hai bảng mới xuất hiện trên giao diện.** `configure_erp_reports` tạo
`bao_cao_sale`, `configure_delivery_daily_report` tạo `bao_cao_van_don_ngay` —
cả hai **rỗng**, 0 dòng. Nếu VPS chưa từng chạy hai lệnh này thì sau phát hành sẽ
có hai bảng mới trong danh sách. Không mất dữ liệu, nhưng là thay đổi nhìn thấy được.

## Chưa kiểm được ở đây

- **Không chạm VPS thật.** Máy ảo Claude Code không tới được VPS lẫn máy chủ dự án.
- **Không đo hiệu năng trên phần cứng VPS** (2 nhân, 4 GB). Số đo ở đây là máy ảo.
- **Không kiểm qua nginx và HTTPS thật.** Gunicorn `settings.prod` đặt
  `SESSION_COOKIE_SECURE = True` nên đăng nhập qua HTTP thuần không dính cookie —
  đúng hành vi, nhưng nghĩa là phần giao diện phải kiểm bằng `settings.dev`.
  Đăng nhập qua HTTPS thật chỉ kiểm được trên VPS.
- **Không chạy các bài `.cjs` cần Chrome thật** — kho không có `package.json`,
  máy ảo thiếu gói `playwright` phía Node.
- Diễn tập dùng dữ liệu mẫu, không phải 1,25 GB dữ liệu thật của VPS.

## Kết luận

Đường nâng cấp **sạch**: hai migration, đảo ngược được, không mất dữ liệu, quy
trình trong `deploy/production/README.md` chạy đúng thứ tự. Rủi ro còn lại không
nằm ở mã mà ở dữ liệu cũ thiếu Loại tiền — xử lý trước thì người dùng không thấy
bảng trống.
