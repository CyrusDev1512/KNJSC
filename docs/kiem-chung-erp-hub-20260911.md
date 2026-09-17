# Kiểm chứng ERP/thư viện và Lên đơn CRM — 11.09.2026

## Kết quả bàn giao local

Theo [ADR-023](quyet-dinh/023-dieu-huong-erp-va-len-don-crm.md): sắp xếp menu ERP, giữ Bảng dữ liệu chỉ đọc, đưa KN CRM lên cụm Nền/Đăng xuất; Biểu mẫu & tài liệu có hai tab đúng quyền. CRM là nơi lên đơn duy nhất, giữ service orders; xem đơn gốc từ thông báo tạo thành công hoặc chi tiết vận đơn, không có danh sách Đơn hàng riêng.

Lỗi biểu mẫu đã tái hiện trước sửa: `created_by=None`, template đọc `username` gây VariableDoesNotExist/500. Hồi quy trước sửa có 6 bài thất bại; sau sửa tab theo vai trò, người tạo trống và bookmark đều đạt. Nhóm chuyển đơn ở lượt trước có 7 lỗi kỳ vọng chức năng chưa có. Các kiểm tra bổ sung preview/không ghi và query budget được thêm sau triển khai. Lỗi URLconf do lượt sửa dở cũng đã được xử lý, không phục hồi/reset thay đổi tác vụ khác.

## Functional và hồi quy

```powershell
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest forms_builder/tests documents/tests orders/tests dashboard core/tests crm/tests/test_order_consolidation.py crm/tests/test_waybill_new.py crm/tests/test_waybill_feedback.py reports/tests taskboard/tests culture/tests -m "not cham and not trinh_duyet" --junitxml=/storage/erp-consolidation-regression.xml --tb=short
```

Kết quả cuối: **1.009 đạt, 2 lỗi, 13 deselected; 44,20 giây**. Đây là suite liên quan, không phải toàn bộ suite hoặc kiểm tải CRM lớn.

Hai lỗi có sẵn và ngoài phạm vi (cũng đã ghi tại báo cáo master 11.09 trước tác vụ này):
- `core/tests/test_giao_dien.py::test_moi_lop_css_dung_trong_template_deu_ton_tai[statistics.html]`: các lớp `exec-*` của Thống kê CRM không nằm trong danh sách CSS mà bài rà đọc.
- `core/tests/test_giao_dien.py::test_moi_o_nhap_deu_co_nhan[statistics.html]`: ô lọc nguồn/ngày/nhóm của Thống kê CRM thiếu nhãn theo bài rà.

Không sửa/loại hai bài này để làm xanh suite. Bài cũ trỏ tới danh sách Đơn hàng hoặc Tài liệu độc lập đã được chuyển sang kiểm endpoint thay thế, giữ kiểm quyền/phân trang. Các phép đo truy vấn trên biểu mẫu (Manager/Admin), tài liệu và chi tiết đơn gốc giữ trần 10; chi tiết đơn gốc ban đầu 11, sau lấy sẵn liên kết record đạt 10.

Cả `web` và `bangtinh`: `python manage.py check` đạt; `git diff --check` đạt. Không migration, dependency hay thay đổi database đang sử dụng.

## Chrome E2E

Server: pytest fixture `crm/tests/test_order_hub_browser_server.py` với `POSTGRES_DB=knjsc_hub_validation`, database thực tế bắt đầu `test_`; ERP cổng 8811, CRM 8812 dùng cùng database test. Chrome host qua `scripts/kiem-thu-erp-hub.cjs`; server pytest kết thúc **1 passed**, không skip. Chromium trong container không có executable nên dùng Chrome đã có trên host, không cài dependency mới.

Đã kiểm tại **1440×900 và 390×900**:
- Đăng nhập, menu Bảng dữ liệu còn hoạt động, nút KN CRM mở tab mới và không còn trong sidebar chính.
- Manager/Admin thấy hai tab; Staff/Leader chỉ thấy Tài liệu; Staff gọi tab forms trực tiếp nhận 403.
- Biểu mẫu thiếu người tạo; tìm/lọc và trang 2 Tài liệu; không tràn ngang trang ERP.
- CRM nhập thông tin khách và hai sản phẩm, tóm tắt Decimal 25.40 USD, lưu thành công, mở đơn gốc đúng tổng; Admin tạo sản phẩm ngay form.
- Admin mở vận đơn, tạo nháp với đường lưu bị chặn có chủ đích; mở Xem đơn gốc bằng liên kết thật sang tab mới. Nháp vẫn còn khi quay lại ở cả hai kích thước.

Các thao tác upload/download tài liệu, cấp quyền, lỗi ghi/rollback và bỏ đơn được bao phủ functional; không tuyên bố đã bấm từng nhánh này bằng Chrome. Tương tác nhập liệu lần này dùng dữ liệu tổng hợp, không dùng IME người dùng thật.

Số đo Chrome cuối (ms, một lần mỗi tình huống, không phải percentile):

| Rộng | Tải biểu mẫu | Áp dụng lọc tài liệu | Lưu đơn |
|---|---:|---:|---:|
| 1440 | 101 | 108 | 219 |
| 390 | 75 | 111 | 111 |

## Kiểm tải đọc có giới hạn

Dùng `performance-testing-skill`, Locust sẵn có. Dữ liệu fixture: **1.000 biểu mẫu, 1.000 tài liệu, số ít đơn có nhiều chi tiết và các tài khoản đại diện**. Không phải 100.000/300.000 vận đơn. Server là Django test WSGI trên Docker local, không phải topology production.

Chạy lần lượt 10/20 người: tổng 70 giây/mức, bỏ 10 giây đầu; cửa sổ đo khoảng 59,5–59,7 giây. Locust kiểm status/nội dung đăng nhập, ghi request/percentile/lỗi theo từng thao tác. Chỉ đọc, không kiểm tải tạo đơn hoặc cập nhật lưới. Kết quả cuối trên server đã nạp code bàn giao: **4.666 request đo, 0 lỗi; p95 cao nhất 69,62 ms**, đạt ngưỡng 1 giây trong phạm vi phép thử.

| Người | Thao tác | Request | p50 ms | p95 ms | p99 ms | req/s | Lỗi |
|---:|---|---:|---:|---:|---:|---:|---:|
| 10 | documents | 495 | 25.37 | 48.22 | 67.4 | 8.31 | 0 |
| 10 | forms | 529 | 25.97 | 52.48 | 66.0 | 8.88 | 0 |
| 10 | original_order | 546 | 20.4 | 34.99 | 46.15 | 9.17 | 0 |
| 20 | original_order | 1021 | 19.53 | 42.41 | 63.15 | 17.12 | 0 |
| 20 | documents | 1035 | 28.87 | 65.95 | 126.84 | 17.35 | 0 |
| 20 | forms | 1040 | 29.38 | 69.62 | 118.86 | 17.44 | 0 |

Không có baseline so sánh, không tuyên bố tăng tốc hay đủ năng lực cho toàn CRM. Không đo CPU/RAM ở đợt này. File số đo thô local: `storage/erp-hub-load-10.json`, `erp-hub-load-20.json`, `erp-hub-browser.json`; XML và log hồi quy cũng trong storage (không đồng bộ Git).

## Chạy lại

1. Mở server fixture: `docker compose -f deploy/docker-compose.yml run --rm --name knjsc-hub-validation -p 8811:8811 -p 8812:8812 -e RUN_MIGRATIONS=0 -e POSTGRES_DB=knjsc_hub_validation -e KN_ORDER_HUB_BROWSER=1 web pytest crm/tests/test_order_hub_browser_server.py --liveserver=0.0.0.0:8811`.
2. Chờ `.order-hub-ready.json` xuất hiện; dùng Node có Playwright sẵn: `node scripts/kiem-thu-erp-hub.cjs` (máy này dùng runtime bundled và NODE_PATH tương ứng).
3. Chạy lần lượt `docker exec -e HUB_USERS=10 knjsc-hub-validation locust -f tests/perf/locust_order_hub.py --host http://127.0.0.1:8811 --users 10 --spawn-rate 10 --run-time 70s --headless --only-summary`; thay HUB_USERS/users thành 20 cho lượt sau.
4. Chỉ khi ba báo cáo JSON đều có `ok:true`, ghi `{"ok":true}` vào `app/.order-hub-result.json`; pytest kiểm kết quả và dọn hai signal, dừng server CRM, tháo database test. Nếu không đạt ghi `ok:false`, không xác nhận đạt hộ bài kiểm.

## Admin kiểm nhanh

- ERP: xem thứ tự nhóm, Bảng dữ liệu, nút KN CRM trên thanh trên; mở Biểu mẫu & tài liệu và đổi tab.
- CRM: Lên đơn → nhập khách/sản phẩm → kiểm tóm tắt → Lưu → Xem đơn gốc. Trong chi tiết vận đơn, người đủ quyền có liên kết Xem đơn gốc.
- Không có menu Đơn hàng riêng. URL cũ chuyển sang CRM hoặc từ chối POST; quyền lên đơn không đồng nghĩa quyền xem cả bảng vận đơn.

Đã cập nhật KNJSC_PROBLEM theo phần giao diện hoàn thành, không đóng nhóm danh mục sản phẩm/đơn vị hàng hóa. Chưa commit/push. Các thay đổi master-grid và tài liệu kiểm chứng lưới có sẵn của tác vụ khác được giữ nguyên.
