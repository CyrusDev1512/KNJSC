# Tích hợp phần local vào CRM-UPDATE — 14.09.2026

## Phạm vi và nguồn

Chủ dự án duyệt khôi phục ERP từ stash, ghép sửa Thống kê và chế độ xem Vận đơn,
kiểm thử, commit/push rồi dọn các bản local đã được bảo toàn. Solarpunk giữ riêng.
Nền kiểm chứng: `9bac840`; không đổi checkout đang chạy 8020/8021 hoặc dữ liệu thật.

- ERP: stash `f4d3ae1a899a7d7ff845ab79582bd1f22e3596fa`, gồm ReportSource,
  báo cáo Sale/Marketing/thị trường/hoạt động Vận đơn không tiền, Tổng quan,
  định danh và mật khẩu tạm. Giữ mã nhân viên cho mọi biểu mẫu theo quyết định mới.
- Chế độ xem Vận đơn: `c5c81ca`; giữ lưới chung, vòng đời bảng và chứng từ của CRM-UPDATE.
  Chỉ Manager Vận đơn đúng bộ phận/Admin đổi chế độ; xem toàn bảng không mở quyền sửa.
- Thống kê: worktree `fix-thong-ke-css-nhan-bo-loc`, sửa CSS và liên kết nhãn bộ lọc.
- Stash `0514ed424c1251c9d6f73491ffde7010043dfd46`: code đã có trong lịch sử;
  giữ lại báo cáo kiểm tải 30 Sale/10 Vận đơn chưa được theo dõi trước đây.
- Các báo cáo ngày 10–12.09 được khôi phục là bằng chứng lịch sử, không phải kết quả đo mới.

## Tích hợp và kiểm chứng mới

Code nguồn đã có trước tác vụ này; tái sử dụng test hồi quy, không nhận là viết test trước
cho toàn bộ phần khôi phục. Lượt ERP đầu: 139 đạt, 2 lỗi test menu cũ. Test được cập nhật
đúng ADR-023: Staff/Leader mở tab Tài liệu nhưng tab `forms` trả 403.
Lượt tích hợp: 867 đạt, 1 lỗi endpoint chế độ xem trên bảng cũ; thêm giới hạn bảng mới,
giữ hợp đồng 404 của đường không áp dụng. Bài hồi quy này đạt trong lượt toàn bộ sau sửa.

Lệnh (Docker image `knjsc-web`, mount app/docs của worktree, PostgreSQL test riêng):

```text
pytest org/tests reports/tests forms_builder/tests dashboard crm/tests/test_delivery_view_mode.py core/tests/test_giao_dien.py --ds=knjsc.settings.test
pytest --ds=knjsc.settings.test
pytest tests/test_du_lieu_mau.py tests/test_hop_trang.py tests/test_luong_ba_bo_phan.py tests/test_ma_tran_phan_quyen.py crm/tests/test_dich_vu_bangtinh.py tests/test_truy_vet.py --ds=knjsc.settings.test
```

- Toàn bộ: **2327 passed, 17 failed, 31 skipped, 2 xfailed**, 254,89 giây.
- Đối chứng nhóm lỗi trên nguyên bản `9bac840`: **115 passed, cùng 17 failed**.
  Đã so tập tên test tự động: không có lỗi mới trong tập thất bại.
- Lỗi nền: giả định dữ liệu mẫu chưa có Kế toán (2); luồng/ma trận ERP cũ (8);
  so chuỗi markup KN CRM (2); truy vết mã AC/số lượng tài liệu (5).
  Chưa sửa các lỗi nền ngoài phạm vi; skip/xfail không tính đạt.
- Chrome thật 1440/390: tạo tài khoản mật khẩu tự sinh/nhập tay → đổi mật khẩu →
  nộp báo cáo → tìm mã/họ tên → chi tiết/xuất; **4 lượt đạt**. Không ảnh/trace mật khẩu.
- Ma trận bốn vai trò × hai kích thước: **8 lượt đạt**, giữ lọc/phân trang,
  tab Biểu mẫu bị chặn đúng quyền. Dữ liệu riêng gồm 100.000 dòng mẫu, thêm 4 báo cáo E2E.
- Chrome chế độ xem: **2 lượt đạt**, reload hai chiều, chỉ đọc dòng người khác,
  chặn POST trái quyền, liên kết cấu hình và bố cục hẹp đạt; không lỗi JS.
- Chrome Thống kê: **4 tổ hợp vai trò/kích thước đạt**, CSS tải được, label liên kết
  đúng input, lọc/nhóm giữ tham số. Không lỗi JS.
- `makemigrations --check --dry-run`: không phát sinh migration ngoài hai bản khôi phục.
  `manage.py check` cả ERP/CRM: không lỗi.
- ReportSource kiểm xuôi/ngược trong pytest; chế độ xem kiểm lùi 0010 rồi tiến 0011
  trên DB riêng: giữ đủ **100.004 DataRecord**.

## Giới hạn và vận hành

Đây là kiểm chứng tích hợp, không phải chạy lại chiến dịch chịu tải toàn CRM. Trần truy vấn
của test liên quan vẫn giữ nguyên. Thời gian Chrome là số đo thao tác trên máy test;
test settings dùng bộ băm nhanh nên không dùng thời gian tạo tài khoản để dự báo production.
Không chạy Locust mới hoặc tuyên bố cải thiện tốc độ. Báo cáo tải lịch sử giữ nguyên ngày đo.

Khi kích hoạt môi trường đích, cần kiểm migration hiện có trước khi áp dụng reports 0002
và forms_builder 0011. Lệnh `configure_erp_reports` là thay đổi metadata có chủ đích,
không tự chạy trong tác vụ dọn Git. Chưa kích hoạt runtime chính; không seed dữ liệu thật.

Bằng chứng thô: `storage/integration-20260914/`, `storage/erp-verification/`,
`storage/delivery-view-verification/`. Bản sao stash gốc nằm tại checkout chính
`storage/branch-audit-20260914/`; không phụ thuộc stash còn trong danh sách để phục hồi.

Các commit triển khai: `83cbf89` (ERP), `bdc4f66` (Thống kê), `b43ba15` (chế độ xem).
Bằng chứng tóm tắt đã theo dõi tại `docs/kiem-thu/integration-2026-09-14/`.
