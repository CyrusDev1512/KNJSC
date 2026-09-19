# Kiểm chứng — Báo cáo tổng hợp nhóm theo ngày × nhân sự, mỗi người một hàng (AC-22.14)

| Mục | Nội dung |
|---|---|
| Ngày | 19.09.2026 |
| Yêu cầu | Chủ dự án gửi ảnh một hệ thống khác (LUMI OMS) và yêu cầu màn hình giống ảnh: trong một ngày **mỗi marketer là một hàng riêng** với số liệu của chính mình |
| Bản bị bác | `98d5c1e` giữ mỗi ngày một hàng, chỉ cho các mã xuống dòng trong một ô. Chủ dự án: "tao bảo cần view giống cái ảnh" |
| Quyết định | Đảo ADR-035 quyết định 1 ("Tổng hợp giữ nguyên mỗi ngày một dòng"), ghi thành mục Bổ sung 19.09 trong chính ADR-035. Không mở ADR mới |
| Nền | `3c61e86` (đầu nhánh `codex/crm-update-solar-ui`) |
| Môi trường | Máy ảo Claude Code trên web; Postgres 16 cổng 5434, DB kiểm `knjsc_mkt` (đã `migrate` tới `forms_builder 0015`), server dev 8020, Chromium của Playwright |

## Cách làm

| Tệp | Thay đổi |
|---|---|
| `app/reports/aggregations.py` | `summarize()` nhận `extra_groups` (thêm khoá vào `.values()` trước `annotate`) và `derived_key`; `SummaryResult.derived_key`; `derived_key_of()`; `row_values()` tra `derived` theo khoá nhiều cột |
| `app/reports/services/activity_service.py` | `build()` truyền `person_expressions(source)` làm `extra_groups` cho cách xem Tổng hợp, `derived_key=("nhom","person_name")`; `marketing_revenue()` nhóm tiền theo cặp (ngày, marketer); `attach_derived()` so khoá nhiều cột; `delivery()` nhóm ngày × người phụ trách; xoá `with_day_people()` và `StringAgg` |
| `app/reports/activity_views.py`, `templates/reports/activity.html`, `static/css/solarpunk.css`, `core/identity.py` | Gỡ phần xuống dòng trong ô của `98d5c1e` (`split_labels`, `JOIN`, `.report-name`) vì mỗi hàng nay chỉ một người |
| Bài kiểm | AC-22.10 đổi kỳ vọng sang "ngày lặp, mỗi người một hàng"; AC-22.14 viết lại thành `test_day_view_groups_by_date_and_person`; `test_mkt_derived_revenue` khoá theo cặp (ngày, mã) |

Cạm bẫy đã tránh: Doanh thu suy ra (ADR-038) trước khoá theo ngày. Tách hàng theo người mà giữ
khoá cũ thì **mỗi người trong ngày nhận trọn tiền cả ngày** và tổng phồng lên. Nay khoá theo cặp
(ngày, marketer); bài `test_doanh_thu_suy_ra_tu_van_don` giữ điều này: 01.08 A = 100, B = 200,
tổng vẫn 325.

## Đã đo

| Kiểm | Lệnh | Kết quả |
|---|---|---|
| Báo cáo | `pytest reports/tests -m "not trinh_duyet"` | 146 đạt, 0 đỏ |
| Toàn bộ bộ nhanh | `pytest -m "not cham"` | **2.508 đạt, 9 bỏ qua, 0 đỏ** (294 s) |
| Truy vết tài liệu | `pytest tests/test_truy_vet.py` | xem dòng cuối |

Chromium trên server dev 8020, `mkt.manager`, nguồn Báo cáo Marketing, kỳ 01/09–19/09:

| Ngày | Nhân sự | Số Mess | Số đơn |
|---|---|---|---|
| 18.09.2026 | ANHPM | 4.684 | 307 |
| 17.09.2026 | ANHPM | 2.320 | 156 |
| 17.09.2026 | NAMVH | 50 | 7 |
| 16.09.2026 | ANHPM | 3.907 | 264 |

Trước đó 17.09 là một hàng gộp 2.370 Mess và 163 đơn. Dòng Tổng trong bộ lọc vẫn 15.056 và
1.001. Không ô nào có `scrollWidth > clientWidth`. Cột định danh vẫn ghim trái (AC-22.13).
Ảnh: `docs/kiem-thu/o-danh-tinh-2026-09-19/` — `01-sau-1440-sang.png`, `02-sau-1440-toi.png`
(đặt `data-theme=dark`), `03-sau-390.png`.

## Chưa làm, chưa kiểm

- Chưa phát hành VPS.
- Ảnh mẫu còn cột STT và dòng Tổng cộng riêng cho từng ngày; chưa yêu cầu nên chưa làm.
- Dữ liệu kiểm chỉ có một ngày hai người; số hàng trên bảng thật = số cặp (ngày, người), phân
  trang 100 nhóm mỗi trang vẫn giữ.
