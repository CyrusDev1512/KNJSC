# Kiểm chứng Lên đơn: ngày, đơn vị và mã nhân viên — 11.09.2026

> Phần chọn Sale của Admin và chỉ hiện ngày bên dưới là kết quả ở thời điểm kiểm chứng này. Quyết định mới bổ sung giờ HH:mm và Admin tự đứng đơn đã thay thế; xem [kiểm chứng tiếp theo](kiem-chung-len-don-gio-admin-20260911.md).

## Phạm vi đã chốt

- Ngày hiện tại theo giờ Việt Nam hiển thị chỉ đọc. Ngày chính thức lấy ở server khi lưu; tham số ngày giả không được sử dụng. Giữ timestamp UTC và ngày Việt Nam trên vận đơn.
- Mỗi dòng sản phẩm chọn hộp/cái/chiếc/túi, mặc định theo danh mục. Đơn vị danh mục khác đã có vẫn được giữ. Lưu bản chụp vào OrderLine và WaybillItem; sửa vận đơn không sửa đơn gốc. Giữ Đơn vị phụ riêng.
- Sale/Marketer mới ghi mã đăng nhập; phân công và lịch sử thao tác dùng mã tài khoản. Admin chọn Sale thì Sale đứng đơn và Admin thực hiện là hai danh tính riêng. Không sửa audit, báo cáo hoặc dữ liệu cũ; lịch sử có tài khoản liên kết hiển thị mã, thiếu tài khoản giữ nhãn lịch sử.
- Chống lặp/gộp lần mua tạm hoãn. Mỗi lần lên đơn vẫn tạo một đơn và một dòng vận đơn theo luồng hiện hành.

## Functional và migration

- TDD: 3 bài thất bại ban đầu đúng nguyên nhân thiếu ngày, không kiểm đơn vị, chưa có bản chụp đơn vị.
- Hồi quy orders/forms_builder/reports/core và CRM liên quan: **984 passed, 2 failed, 13 deselected**, 44,52s. Hai lỗi có sẵn tại core/tests/test_giao_dien.py cho statistics.html: lớp exec-* không có trong tập CSS của bài rà; bộ lọc thiếu nhãn. Không sửa/che hai lỗi ngoài phạm vi.
- Sau bổ sung kiểm xuôi/ngược và tương thích caller cũ: **72 passed**, 19,47s (test_order_identity_units, test_waybill_new, test_waybill_feedback; không cham/trinh_duyet).
- Kiểm đơn vị tùy chọn, mặc định danh mục, dữ liệu sai rollback, đổi danh mục không đổi bản chụp, xuất/nhập chi tiết đơn vị cũ, bỏ dòng đầu bằng caller cũ vẫn giữ đơn vị dòng còn lại, Admin khác Sale, giả ngày, mẫu qua nửa đêm Việt Nam. Giữ trần 10 truy vấn form/đơn gốc.
- Migration orders.0006_line_unit_snapshot thêm hai CharField 40 ký tự, giá trị cũ rỗng; kiểm xuôi/ngược trên DB test. Rollback bỏ cột nên mất dữ liệu đơn vị mới, không dùng rollback trên DB vận hành để thử. Đã kiểm plan chỉ có 0006 và áp dụng xuôi vào local, không seed/backfill.
- manage.py check cho web và bangtinh đạt; makemigrations --check --dry-run: không thiếu migration.

## Chrome

**Đạt Chrome 1440×900 và 390×900 trên mã cuối**, không có pageerror. Đăng nhập Sale/Admin, ngày readonly, đơn vị mặc định, thêm hai sản phẩm, lưu lỗi giữ đơn vị, lưu thành công và xem đơn gốc; Admin chọn Sale tách mã người đứng đơn/người thực hiện. Sửa đơn vị trong popup vận đơn, mở lại thấy đã lưu, đơn gốc vẫn là đơn vị ban đầu.

Một lần đo ở mỗi chiều rộng: tải form 91/83 ms; lưu đơn 120/126 ms. Ảnh đơn gốc ở storage/order-entry-screens; JSON kết quả ở storage/order-entry-browser.json. Lượt bổ sung ban đầu gặp cache template cũ khi sửa source giữa phiên server test; đã dựng lại server và chạy thành công toàn bộ kịch bản cuối, không coi lượt timeout là đạt.

## Hiệu năng có giới hạn

Locust hiện có trên database test riêng, server Django WSGI test cổng 8812. 10 và 20 người, 10 giây làm nóng + khoảng 60 giây đo/mức; pacing 0,2–0,5s. Đọc form, POST xem trước chỉ tính Decimal, đọc đơn gốc. Không kiểm tải ghi tạo đơn, không đo năng lực CRM 100k/300k hay năng lực VPS. Fixture nhỏ: hai sản phẩm, vài đơn kiểm thử; dùng chung máy đang có tác vụ khác. Không có baseline tương đương nên không tuyên bố tăng tốc.

| Người | Thao tác | Request đo | p50 ms | p95 ms | p99 ms | Lỗi |
|---|---|---|---|---|---|---|
| 10 | entry | 538 | 26.62 | 51.54 | 69.86 | 0 |
| 10 | preview | 525 | 13.14 | 33.74 | 53.24 | 0 |
| 10 | original_order | 500 | 37.93 | 60.46 | 96.08 | 0 |
| 20 | preview | 1047 | 18.35 | 74.36 | 105.27 | 0 |
| 20 | original_order | 977 | 43.49 | 122.12 | 157.03 | 0 |
| 20 | entry | 1031 | 31.26 | 92.77 | 123.14 | 0 |

Tổng 4.618 request đo, 0 lỗi; tất cả p95 dưới 1 giây. Số đo browser là từng lần thao tác, không phải percentile hoặc benchmark so sánh. Tài nguyên CPU/RAM chưa lấy mẫu riêng. JSON/log nằm ở storage/order-entry-*; dữ liệu nhạy cảm vận hành không được dùng.

## Chạy lại

```powershell
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest crm/tests/test_order_identity_units.py crm/tests/test_waybill_new.py crm/tests/test_waybill_feedback.py -m "not cham and not trinh_duyet" --tb=short
```

E2E dùng fixture crm/tests/test_order_hub_browser_server.py (KN_ORDER_HUB_BROWSER=1, POSTGRES_DB riêng, cổng 8811/8812) và scripts/kiem-thu-order-entry.cjs với Playwright/Chrome có sẵn. Chỉ chạy Locust tests/perf/locust_order_entry.py khi manifest xác nhận DB test; HUB_USERS=10 rồi 20, --headless -u tương ứng -r 2/4 -t 70s --host http://127.0.0.1:8812. Đóng fixture bằng kết quả thực sau kiểm chứng, không coi skip là đạt.

## Kiểm tra nhanh cho Admin

Mở CRM → Lên đơn: kiểm Ngày và Sale đứng đơn, chọn sản phẩm → kiểm/đổi đơn vị → lưu → Xem đơn gốc. Trong vận đơn mở Chi tiết sản phẩm để xem bản sao đơn vị; đơn gốc không đổi theo sửa vận đơn. Bàn giao local, chưa commit/push.
