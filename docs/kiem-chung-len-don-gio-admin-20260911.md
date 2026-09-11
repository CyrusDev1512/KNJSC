# Kiểm chứng ngày giờ và Admin tự đứng đơn — 11.09.2026

## Thay đổi

- Ô Ngày giờ (Việt Nam) hiển thị dd/mm/yyyy HH:mm, chỉ đọc và tự chuyển phút khi mở form. Thời gian tham khảo lấy từ server rồi tăng bằng đồng hồ monotonic của trình duyệt; không polling server. Thời gian lưu chính thức vẫn là Order.created_at, không lấy từ trình duyệt.
- Thông báo thành công có giờ/phút và ngày thực tế đã lưu. Database giữ toàn bộ timestamp, không cắt giây; cột Ngày trên vận đơn tiếp tục là ngày để giữ lọc/thống kê hiện có.
- Sale và Admin đều tự đứng đơn bằng mã đăng nhập, bỏ dropdown. Admin không thuộc Sale dùng Sale/team trống cho đơn thử theo quyết định chủ dự án; không thay hồ sơ, không tạo dữ liệu tổ chức giả. Không đổi quan hệ lịch sử hoặc giả định đã có cơ chế tách đơn thử khỏi dữ liệu lưu.
- Form chặn seller do người dùng gửi thêm; hợp đồng service nội bộ cũ giữ riêng. Không migration/dependency mới.

## Functional và E2E

- TDD tái hiện thiếu giờ hiển thị và form Admin còn bắt/chấp nhận chọn Sale. Các kỳ vọng cũ về dropdown trong test được thay theo quyết định mới; kiểm service nội bộ cũ vẫn giữ.
- Lệnh: `docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest crm/tests/test_order_identity_units.py crm/tests/test_order_consolidation.py crm/tests/test_waybill_new.py crm/tests/test_master_nine.py orders/tests -m "not cham and not trinh_duyet" --tb=short`.
- **117 passed, 23,09s**. Kiểm mở form 10:32/lưu 10:33:47: lưu timestamp 10:33:47 và hiển thị 10:33. Có kiểm qua ngày mới ở Việt Nam, giả giờ/seller qua POST, Admin không bộ phận, Staff ngoài phạm vi đơn Admin bị 404, đơn vị và bản sao vận đơn. Trần 10 truy vấn form/đơn gốc giữ đạt.
- Chrome **1440×900 và 390×900 đạt**, không pageerror: đăng nhập Sale/Admin, không dropdown, advance đồng hồ 61 giây để xác nhận chuyển phút, đơn nhiều sản phẩm, lỗi lưu giữ dữ liệu, thông báo giờ lưu, đơn gốc hiện mã tương ứng và sửa đơn vị bản sao không đổi bản gốc.
- Từng lần đo Chrome: tải form 201/96 ms, lưu Sale 128/140 ms; không phải percentile hoặc so sánh tốc độ. Script scripts/kiem-thu-order-entry.cjs; JSON storage/order-clock-browser.json. Dùng database test và hai server riêng từ fixture test_order_hub_browser_server; skip không tính đạt.
- Không chạy lại toàn bộ hệ thống vì thay đổi tập trung form/service lên đơn; hai lỗi rà statistics.html ghi từ trước không thuộc phần này.

## Kiểm tải đọc

**Đạt 4,782 request đo, 0 lỗi; p95 cao nhất 76,38 ms.** Locust 10/20 người bằng tài khoản Admin trên database test riêng, dữ liệu nhỏ; 10s làm nóng và khoảng 60s đo/mức. Đọc form, tính tóm tắt, xem đơn gốc; không kiểm tải ghi tạo đơn hoặc 100k/300k dòng. Không kết luận cải thiện tốc độ hay sức chịu tải toàn CRM. Không lấy mẫu CPU/RAM riêng.

| Người | Thao tác | Request | p50 ms | p95 ms | p99 ms | Lỗi |
|---|---|---|---|---|---|---|
| 10 | preview | 550 | 11.38 | 29.53 | 59.7 | 0 |
| 10 | original_order | 536 | 23.31 | 44.39 | 65.03 | 0 |
| 10 | entry | 529 | 14.58 | 28.82 | 47.63 | 0 |
| 20 | preview | 1055 | 14.07 | 62.74 | 119.65 | 0 |
| 20 | original_order | 1046 | 26.19 | 76.38 | 134.05 | 0 |
| 20 | entry | 1066 | 16.29 | 49.35 | 112.5 | 0 |

Lệnh: `docker exec -e HUB_USERS=10 -e HUB_ACTOR=quan_tri -e HUB_CHECK=clock knjsc-order-clock-validation locust -f tests/perf/locust_order_entry.py --headless -u 10 -r 2 -t 70s --host http://127.0.0.1:8812`; lượt 20 đổi HUB_USERS/-u thành 20 và -r thành 4. JSON/log storage/order-clock-load-10/20; kiểm manifest DB test trước chạy.

## Bàn giao

Quyết định thay thế ở ADR-023; KNJSC_PROBLEM và các bảng tiến độ cập nhật theo kết quả thực tế. Local, chưa commit/push. Mở CRM → Lên đơn, kiểm Ngày giờ và dòng Sale đứng đơn → Lưu đơn → kiểm giờ trong thông báo và mã trong đơn gốc.


## Bổ sung 11.09.2026 — Bắt buộc chọn ba thông tin đầu vào

- Chủ dự án yêu cầu Quốc gia, Loại tiền và PTTT lên đơn mặc định chưa chọn. Thêm option trống có nhãn Chọn, bỏ initial USD; ChoiceField vẫn required và kiểm danh sách hợp lệ. Không đổi mặc định service nội bộ hoặc dữ liệu cũ.
- Sau lưu thành công form mới trở về chưa chọn. Lưu lỗi giữ các lựa chọn hợp lệ đã nhập.
- TDD: trước sửa hai bài trạng thái ban đầu thất bại vì Quốc gia tự chọn us; chín trường hợp thiếu/trống/sai option đã bị server chặn từ trước. Sau sửa: **105 passed, 19,38s**, không skip trong nhóm đã chọn.
- Lệnh: `docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest crm/tests/test_order_required_choices.py crm/tests/test_order_identity_units.py crm/tests/test_order_consolidation.py crm/tests/test_waybill_new.py orders/tests -m "not cham and not trinh_duyet" --tb=short`.
- Chrome 1440/390 trên DB test riêng đạt: cả ba ô rỗng/required, bấm lưu khi còn thiếu bị chặn, chọn đủ thì lưu được; đơn tiếp theo lại rỗng, kiểm cả Admin và Sale. Các luồng ngày giờ, đơn vị, đơn gốc vẫn đạt; không pageerror. JSON `storage/order-required-choices-browser.json`.
- Kiểm hiệu năng phù hợp phạm vi: trần 10 truy vấn form/đơn gốc trong suite đạt; từng lần tải form Chrome 124/98 ms và lưu 132/118 ms. Không thêm truy vấn hoặc gọi mạng do thay lựa chọn. Không chạy lại Locust cho thay đổi metadata form này, không tuyên bố tăng tốc/khả năng chịu tải mới.
- `git diff --check` đạt. Không thêm dependency hoặc migration. Local, chưa commit/push.
