# Kiểm chứng một bảng vận đơn duy nhất (ADR-036) — 18.09.2026

Nền `5b68dce`, nhánh `codex/crm-update-solar-ui`, máy ảo Claude Code trên web
(Postgres 16 local, Chromium headless qua Playwright). Quyết định:
[ADR-036](quyet-dinh/036-mot-bang-van-don-duy-nhat.md). Chưa phát hành VPS —
việc đó do CLI ở máy chủ dự án theo `docs/daily-tasks.md`.

## Phạm vi

`van_don` ("Vận đơn mới") là bảng vận đơn duy nhất, mang profile Vận đơn và cột
Trùng; crmThuận (`van_don_moi`) và Vận đơn DB (`van_don_db`) xoá cứng bằng lệnh
có hai cờ; trang Bảng nhận đơn bỏ, cột `receives_orders` bỏ (migration 0014);
dòng không có Chi tiết sản phẩm tạo được; tệp cũ nhập không cần Mã đơn/Loại
tiền/Chi tiết.

## pytest

Chạy từ `app/`, `--ds=knjsc.settings.test`, không chạy hai pytest cùng lúc.

| Lượt | Kết quả |
|---|---|
| `crm/tests orders/tests forms_builder/tests reports/tests core/tests tests -m "not trinh_duyet and not cham"` (lượt cuối, `scratchpad/suite36e.log`) | 2.384 đạt, 1 bỏ qua, 0 đỏ, mã thoát 0 |
| Cùng phạm vi, `-m "cham and not trinh_duyet"` | 13 đạt, 6 bỏ qua, 2 xfail (K24, có sẵn) |
| `crm/tests/test_mot_bang_van_don.py` (AC-36.1 → 36.7, migration 0014 xuôi/ngược) | 8 đạt |
| `tests/test_truy_vet.py` sau khi gạch AC-11.39, AC-18.9 và thêm mục 36 | Đạt; docs/06: 211 AC, 198 tự động, 174 đã có bài |
| `manage.py makemigrations --check --dry-run` | Không có thay đổi |
| `python scripts/dong-bo-skill.py --check` | PASS |

Ba bài đỏ ở lượt trước lượt cuối và cách sửa: tệp mẫu thật ghi "Đã Thanh Toán"
(khác hoa thường) → `waybill_service._payment_label` so không phân biệt hoa thường
và nhận nhãn cũ; bài metadata lưới vấp cột ảo `__duplicates` → bỏ qua cột ảo;
`Grant`/`WaybillItem` không có `all_objects` → dùng `_base_manager`.

**Phát hiện ngoài phạm vi, đã sửa:** teardown của `tests/test_hieu_nang.py`
(`seed_perf.clear()`) ném `AttributeError` nhưng dấu `xfail(strict=False)` của
module nuốt luôn lỗi teardown, để lại bộ phận `van-don` và 50.000 dòng trong DB
kiểm thử làm `test_hop_trang::test_lenh_tao_bang_van_don_tren_may_sach` đỏ ở lượt
chạy đủ. Sửa `clear()`; bài xfail vẫn xfail (K24: 12 và 16 truy vấn, ngân sách 10).

**Quan sát chưa giải thích:** một lượt chạy đủ (`-m "not trinh_duyet"`) treo hơn 17
phút ở chính lệnh `DELETE` 50.000 dòng của `seed_perf.clear()` (backend Postgres
`active`, không chờ khoá); cùng lệnh chạy riêng trong giao dịch rollback hết
0,45 s, và ba lượt sau (module riêng, sau tệp transactional, lượt `cham`) không
tái hiện. Ghi lại để theo dõi, không đổi mã.

## DB dev (dữ liệu giả: 100.521 dòng `PERF-*`, 10.000 `MAU-*`, 375.000 `KH-*`)

| Lệnh | Kết quả |
|---|---|
| `migrate --noinput` | `forms_builder.0014_remove_tabledef_receives_orders... OK` |
| `tao_bang_van_don` | "Bang van_don: 44 cot, bo phan Vận đơn", 1,7 s; bảng giữ ID, 100.521 dòng, `workflow=waybill`, tên "Vận đơn mới" |
| `xoa_bang_van_don_cu` (thiếu cờ) | `CommandError: Lệnh xoá cứng: cần cả --dong-y-xoa-cung và --backup-da-lam.` |
| `xoa_bang_van_don_cu --dong-y-xoa-cung --backup-da-lam` | `van_don_moi`: lịch sử ô 6, biên nhận 2, chi tiết 19.970, phân công 10.000, dòng 10.000, cột 25; `van_don_db`: phân công 375.000, dòng 375.000, cột 26 — **55,7 s** cho 385.000 dòng |
| Chạy lại | "không có gì để xoá" cả hai |
| `configure_erp_reports`, `configure_delivery_daily_report` | `ReportSource` delivery trỏ `van_don` |

Ước lượng VPS (6.667 + 2 dòng): dưới vài giây.

## Chromium (headless, 1440×900, `scratchpad/kiem_36.py`, `kiem_36b.py`)

| Điểm kiểm | Kết quả |
|---|---|
| Admin `/thu-muc/?bp=van-don&tat-ca=1` | Chỉ "Vận đơn mới · 100.522 dòng"; không crmThuận, không Vận đơn DB |
| Sidebar Admin | Không còn "Bảng nhận đơn"; `/cau-hinh/nhan-don/` → 404 |
| Sale `sale.staff` Lên đơn (Hoa Kỳ, Zelle, 2 × Retinol Cream 12,50) | "Đã lưu đơn DH-1809-0001 vào Vận đơn mới lúc 16:39 ngày 18/09/2026" |
| Sale vào `/bang-tinh/van_don/` sau khi có đơn | 200, lưới 1 dòng của mình (chưa có dòng → chuyển Lên đơn, AC-36.3 tự động) |
| Vận đơn `vd.staff` `/bang-tinh/van_don/?tim=0936036036` | 1 dòng, thấy khách vừa lên; cột Trùng có; nút Tôi/Toàn bộ có; bấm đúp ô Sản phẩm mở hộp `vd-detail` |
| Toàn bộ / Tôi | 100.522 / 0 (`?cua_toi=1`, chưa được phân công) |
| `/van-don/thong-ke/` | Chuyển `/thong-ke/?nguon=van_don`, 200 |
| ERP `quantri` `/bao-cao/tong-hop/?nguon=van_don` | 200, nguồn "Vận đơn mới" trong bộ lọc, có số liệu |

Sửa nhỏ nhờ kiểm: câu chú thích dưới nút Lưu đơn còn nói "bảng nhận đơn do Admin
cấu hình" → "bảng Vận đơn mới".

## Chưa kiểm

- Bài `trinh_duyet` (Playwright trong pytest) không chạy ở lượt này; bài
  `test_destination_*` đã xoá theo ADR-036.
- Script `.cjs` của Codex chỉ `node --check`, chưa chạy lại trên Chrome thật.
- VPS: chưa phát hành; số dòng thật của hai bảng cũ (6.667 + 2) lấy từ biên bản 17.09.
- Tệp thật `vandon-mau.xlsx`: 220/221 dòng vào; dòng PTTT "Cheque" bị từ chối vì
  PTTT chỉ còn Zelle/PayPal (ADR-031). Chủ dự án chốt: giữ từ chối, hay thêm
  "Cheque" vào danh sách lịch sử?
