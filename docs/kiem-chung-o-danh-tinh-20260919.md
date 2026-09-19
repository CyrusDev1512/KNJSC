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

## Đợt hai cùng ngày — khối theo ngày và cột STT (AC-22.15)

Chủ dự án "tiếp tục": làm nốt hai thứ ảnh mẫu có mà ta chưa có.

| Tệp | Thay đổi |
|---|---|
| `app/reports/aggregations.py` | `subtotals()` và `subtotal_cells()` — cộng `c_*` của các dòng cùng ngày, **cộng thêm `derived`** của từng dòng, rồi `_recompute` nên cột tính của Tổng ngày tính lại từ tổng, không phải trung bình các dòng. Thuần bộ nhớ, không truy vấn thêm |
| `app/reports/activity_views.py` | `day_blocks()` chèn dòng Tổng ngày trước dòng đầu của mỗi ngày trên trang và gắn STT đếm lại từ 1 (đếm trên toàn bộ dòng nên không đứt khi sang trang); `identity_layout` thêm cột `stt`; `label_span` thành 4 |
| `templates/reports/activity.html` | Nhánh `kind == 'subtotal'` cho dòng Tổng ngày; ô STT theo `identity_columns` |
| `app/static/css/solarpunk.css` | `--w-stt`, `.id-stt`, `.report-subtotal`; sọc chẵn lẻ và hover loại trừ dòng Tổng ngày |
| `app/reports/excel.py` | Cột STT; dòng `Tổng ngày dd.mm.yyyy` in đậm trước mỗi khối |

Đo trên Chromium (`mkt.manager`, kỳ 01/09–19/09), đọc thẳng từ DOM:

| Dòng | Số Mess | Số đơn |
|---|---|---|
| Tổng trong bộ lọc | 15.056 | 1.001 |
| 17.09.2026 · Tổng ngày | 2.370 | 163 |
| 17.09.2026 · STT 1 · ANHPM | 2.320 | 156 |
| 17.09.2026 · STT 2 · NAMVH | 50 | 7 |

2.320 + 50 = 2.370 và 156 + 7 = 163. Không ô nào tràn chữ. Cuộn ngang 300px thì cột định
danh trôi **0px** (vẫn ghim đúng, AC-22.13 không hỏng). Bài `reports/tests` + giao diện +
truy vết: 753 đạt, 0 đỏ; toàn bộ `pytest -m "not cham"`: **2.509 đạt, 9 bỏ qua, 0 đỏ** (266 s),
`test_query_budget` vẫn trong ngưỡng 10 truy vấn vì Tổng ngày cộng trong bộ nhớ.
Ảnh `04-khoi-1440-sang.png`, `05-khoi-1440-toi.png`, `06-khoi-390.png`.

## Chưa làm, chưa kiểm

- Chưa phát hành VPS.
- Ảnh mẫu còn tô màu ô theo ngưỡng (vàng/xanh/đỏ). Cơ chế ngưỡng đã có ở
  `forms_builder/styling.py` nhưng gắn với `ColumnDef`, trong khi Tỉ lệ chốt, CPO, Giá Mess của
  Marketing là `marketing.Metric` không có chỗ lưu ngưỡng; quy tắc màu trong `main.css` lại khoá
  sau `table.bang.bang-luoi` nên không áp cho `.report-table`. Cần chủ dự án chốt ngưỡng từng chỉ
  tiêu và chỗ lưu trước khi làm.
- Các cột "(TT)" của ảnh mẫu không có dữ liệu tương ứng bên mình.
- Dữ liệu kiểm chỉ có một ngày hai người; số hàng trên bảng thật = số cặp (ngày, người), phân
  trang 100 nhóm mỗi trang vẫn giữ.
