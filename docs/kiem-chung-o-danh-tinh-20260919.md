# Kiểm chứng — Ô danh tính Báo cáo tổng hợp liệt kê mỗi người một dòng (AC-22.14)

| Mục | Nội dung |
|---|---|
| Ngày | 19.09.2026 |
| Yêu cầu | Chủ dự án gửi ảnh một hệ thống khác và nói: "ở trường nhân viên hiện tại đang bị tình trạng nhiều nhân sự bị nhét chung 1 ô thay vì chia ra thành hàng". Chốt cách làm: **giữ gộp theo ngày**, chỉ bỏ cắt chữ, "đảm bảo view đơn giản và mạch lạc như ảnh" |
| Không làm | Không đổi cách nhóm. Cách xem Tổng hợp vẫn **mỗi ngày một dòng** đúng ADR-035 quyết định 1 (bản nháp nhóm theo ngày × nhân sự đã bị chủ dự án hoàn lại hôm 18.09). Muốn mỗi người một hàng thì dùng cách xem **Theo nhân viên** đã có |
| Nền | `ea8942c` — sau khi phiên khác làm bố cục theo bản vẽ (AC-22.13) và đổi ô bảng thành **chỉ mã nhân sự** (bổ sung ADR-037). Hai commit đó đã bỏ luật cắt chữ, nhưng nhiều người vẫn nối bằng dấu phẩy trong một ô rộng 130px |
| Môi trường | Máy ảo Claude Code trên web; Postgres 16 cổng 5434, DB kiểm `knjsc_mkt` (đã `migrate` thêm `forms_builder 0014`, `orders 0010`), server dev 8020, Chromium của Playwright |

## Nguyên nhân còn lại sau AC-22.13

`with_day_people` nối tên nhiều người bằng `StringAgg` dấu phẩy, view trả nguyên chuỗi cho
template. Cột Nhân sự rộng cố định `--w-nhan-su:130px` và `.report-identity` có
`overflow-wrap:anywhere`, nên "ANHPM, NAMVH" bị bẻ **giữa mã** chứ không theo người.

## Đã sửa

| Tệp | Thay đổi |
|---|---|
| `app/core/identity.py` | Thêm `JOIN = ", "` và `split_labels()` — một chỗ khai dấu nối nhiều người (quy tắc 7) |
| `app/reports/services/activity_service.py` | `StringAgg` dùng `JOIN` thay vì viết thẳng `", "` |
| `app/reports/activity_views.py` | `row['person']`, `row['leader']` thành **danh sách** nhãn; Excel vẫn đọc `person_name`/`leader_name` gốc nên không đổi |
| `app/templates/reports/activity.html` | Hai ô lặp danh sách, mỗi nhãn một `<span class="report-name">` |
| `app/static/css/solarpunk.css` | `.report-name {display:block}` và khoảng cách 2px giữa hai dòng |

Không đụng bố cục, cột ghim, chip hay bộ lọc của AC-22.13.

## Đã đo

| Kiểm | Lệnh | Kết quả |
|---|---|---|
| Báo cáo + giao diện | `pytest reports/tests core/tests/test_giao_dien.py -m "not trinh_duyet"` | **716 đạt, 0 đỏ** |
| Toàn bộ bộ nhanh | `pytest -m "not cham"` | **2.494 đạt, 9 bỏ qua, 0 đỏ** (288 s) |

Chromium trên server dev 8020, tài khoản `mkt.manager`, nguồn Báo cáo Marketing, kỳ
01/09–19/09:

- Dòng 17.09.2026 có hai marketer → ô Nhân sự hiện `ANHPM` và `NAMVH` trên **hai dòng
  riêng**. Bốn dòng còn lại một người, một dòng.
- Quét mọi ô của bảng: **không ô nào có `scrollWidth > clientWidth`**, tức không chữ nào bị cắt.
- Cột định danh vẫn `position: sticky` (bố cục AC-22.13 không hỏng).
- Ảnh: `docs/kiem-thu/o-danh-tinh-2026-09-19/` — `01-sau-1440-sang.png`,
  `02-sau-1440-toi.png` (đặt `data-theme=dark`), `03-sau-390.png`.

## Chưa kiểm

- Chưa chạy trên VPS; đợt phát hành gộp ADR-036 + bảy PTTT + ADR-037/038 + bố cục chưa làm.
- Dữ liệu kiểm chỉ có ngày nhiều nhất hai người, nên chưa thấy ô sáu, bảy dòng cao bao nhiêu
  trong cột ghim. Bài tự động có bốn người một ngày và đạt.
- Ảnh "trước" không chụp lại được vì bố cục đã đổi trong cùng ngày; mô tả bằng lời ở mục
  Nguyên nhân.
