# Kiểm chứng Bảng nhận đơn — 15.09.2026

## Kết quả

Triển khai local trên `codex/crm-update-solar-ui`, nền `072cee4`; chưa commit/push hoặc cập nhật VPS.
Admin mở CRM → Bảng nhận đơn (`http://localhost:8021/cau-hinh/nhan-don/`), chọn bảng và lưu.
Local đã áp migration 0012; bảng mặc định vẫn `van_don_moi` (Vận đơn), `van_don_db` đủ điều kiện.
Không tạo đơn thử hoặc chuyển dữ liệu tại DB đang dùng. Kiểm local bằng GET có phiên Admin rồi đăng xuất.

## Kiểm thử

- TDD endpoint: 4 bài thất bại đúng vì chưa có đường cấu hình (404); sau triển khai nhóm ban đầu 8 đạt.
- Hồi quy `crm/tests orders/tests forms_builder/tests reports/tests` trên PostgreSQL riêng:
  lượt trước sửa cuối **608 passed, 1 failed, 14 skipped**. Lỗi là bảng mới chưa mang cấu hình
  hàng đợi nên nhân viên được phân công vẫn bị từ chối ghi. Đã sửa tại bước kích hoạt profile.
- Sau sửa chạy `crm/tests/test_order_destination.py`, `test_waybill_feedback.py`,
  `test_payment_documents.py`, `test_delivery_view_mode.py`, `orders/tests/test_destination_concurrency.py`:
  **67 passed**. Không nhận 14 bài skip của lượt rộng là đã đạt.
- Hai trường hợp 30 Sale đồng thời trên đích mới: khách riêng/cùng khách đều đủ 30 đơn,
  mã duy nhất, đúng Sale, Decimal, đủ hai sản phẩm và bản sao. Oracle tái sử dụng từ test cấp mã.
- Migration xuôi/ngược tại DB pytest: **1 passed**, dòng và liên kết còn nguyên.
- Chrome thật **1440/390**, lần cuối: chọn Vận đơn DB → lưu đơn → xem đơn gốc → mở lưới →
  đổi về Vận đơn; cả hai đạt, không lỗi JS, không tràn ngang. DB test xác nhận hai đơn
  đã tạo vẫn ở Vận đơn DB sau đổi lại. Ảnh và JSON: `storage/order-destination/`.
- `makemigrations --check --dry-run`: không có thay đổi ngoài migration 0012.
- `manage.py check` ERP và CRM local: không lỗi. GET cấu hình local: 200, hai bảng đủ điều kiện.
- `git diff --check`: đạt. Worker/beat local đã khởi động lại, web/CRM dùng runserver tự nạp code.

Docker test dùng network/container `knjsc-destination-*`, tách DB vận hành; `RUN_MIGRATIONS=0`.
Không chạy seed/Locust trên DB dùng thật. Đây là kiểm đồng thời và hồi quy, không phải chiến dịch
chịu tải 100k/300k hoặc bằng chứng p95 production. Không tuyên bố cải thiện tốc độ.

## Giới hạn

Chọn đích làm bảng trống nhận profile vận hành Vận đơn. Bảng đã có dữ liệu mà chưa có profile
bị chặn để tránh đổi quyền/cách hiểu dữ liệu cũ. Chưa hỗ trợ ánh xạ cột tùy ý hoặc di chuyển đơn cũ.
Các thao tác chứng từ tiếp tục theo quyền hiện hành ADR-025, không đổi nghiệp vụ trong tác vụ này.

[Quyết định ADR-029](quyet-dinh/029-bang-nhan-don-crm.md).

## Kiểm lại các luồng theo yêu cầu chủ dự án — 15.09.2026

- Chạy lại trên PostgreSQL tạm riêng, không đổi bảng mặc định hay tạo đơn trong database local đang sử dụng.
- Nhóm trực tiếp: `crm/tests/test_order_destination.py`, `test_destination_migration.py`, `test_waybill_feedback.py`, `test_payment_documents.py`, `test_delivery_view_mode.py`, `orders/tests/test_destination_concurrency.py`: **68 passed, không skip**, 29.11s.
- Bao gồm: Admin đổi đích; từ chối nhân viên/Manager truy cập cấu hình; đơn nhiều sản phẩm đúng Decimal; giữ đơn cũ; phân công và phạm vi xem/sửa; chứng từ và xuất; bảng không hợp lệ/bị ngừng hoạt động; rollback không ghi nhầm đích; bảo vệ xóa bảng; hai ca 30 Sale đồng thời; migration xuôi/ngược.
- Chrome 1440/390 chạy lại: đổi sang Vận đơn DB → lưu đơn → xem đơn gốc → mở lưới → đổi về Vận đơn. Cả hai đạt, không lỗi JS. Test server xác nhận hai đơn vẫn ở Vận đơn DB: **1 passed**, 24.41s.
- Hồi quy rộng `crm/tests orders/tests forms_builder/tests reports/tests`: **616 passed, 1 failed, 14 skipped**, 151.82s. Không coi toàn bộ suite đã đạt.
- Bài thất bại `crm/tests/test_trang_chu.py::test_bam_thang_mo_luoi_loc_dung_thang` còn yêu cầu nhãn “Sửa”. Diff template thư mục của tác vụ Tải mẫu Excel đã bỏ nhãn theo phạm vi ghi trong báo cáo tác vụ đó. Cần cập nhật kỳ vọng test tại tác vụ đó; lượt này không sửa code/test ngoài phạm vi. Các khẳng định phía sau dòng thất bại của bài này chưa được thực thi.
- Bằng chứng: `storage/order-destination/user-flow-regression.log`, `user-flow-targeted.log`, `user-flow-browser.log`, `user-flow-browser-server.log`, `browser-result.json` và ảnh 1440/390.
- Đây là kiểm chức năng/hồi quy/đồng thời, không phải kiểm tải kéo dài hoặc đo p95. Chưa có bài chuyên biệt đổi cấu hình đúng lúc một giao dịch tạo đơn đang giữ khóa.

## E2E Admin đổi bảng, nhân sự lưu đơn — 15.09.2026

Theo yêu cầu kiểm như người dùng thật: Chrome mở ba browser context độc lập, đăng nhập Admin, staff_sale_1 và staff_sale_2 qua form. Các lần đổi cấu hình và tạo đơn đều bấm giao diện, không gọi service/API thay thao tác.

Chạy ở 1440px và 390px, mỗi kích thước có bốn đơn:

1. Admin chọn Vận đơn; Sale 1 mở form và lưu → Vận đơn.
2. Admin chọn Vận đơn DB; Sale 2 mở form và lưu → Vận đơn DB.
3. Sale 1 nhập form khi đích là DB; Admin đổi về Vận đơn; Sale không reload form, lưu → Vận đơn.
4. Sale 2 nhập form khi đích là Vận đơn; Admin đổi sang DB; Sale không reload form, lưu → Vận đơn DB.

Cả tám đơn thành công. Từng Sale mở đơn gốc; Admin mở hai lưới để đối chiếu. Sale truy cập trang cấu hình trực tiếp nhận 403. Kiểm DB cuối lượt: đúng bảng, đúng seller/created_by, tổng Decimal 25.00, một dòng sản phẩm cho mỗi đơn; đủ tám đơn, đơn cũ vẫn ở nguyên bảng. Không lỗi JavaScript. Đây là bằng chứng bảng đích lấy lúc lưu, không chốt lúc mở form.

Lượt đầu dừng ở bước tìm tên khách trên lưới DB mobile vì kịch bản chưa cuộn ngang tới cột. Bổ sung thao tác mouse wheel ngang trong harness, không sửa code ứng dụng. Chạy lại từ database test sạch: `crm/tests/test_destination_staff_browser.py` **1 passed, 37.80s**; Node `scripts/kiem-thu-order-destination-staff.cjs` trả `ok:true`, đủ tám đơn và hai kích thước. Bằng chứng `storage/order-destination/staff-result.json`, `staff-browser-final.log`, `staff-server-final.log`, các ảnh `staff-*.png`. Lượt đầu giữ riêng log, không nhận là đạt.

Database/container tạm đã dọn sau kiểm thử; không đổi dữ liệu hoặc cấu hình bảng đích của local đang sử dụng. Chỉ bổ sung kịch bản và tài liệu, chưa commit/push.
