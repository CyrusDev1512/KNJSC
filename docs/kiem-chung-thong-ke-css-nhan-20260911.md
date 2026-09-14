# Sửa hai lỗi kiểm thử Thống kê — 11.09.2026

- Nhánh: `fix/thong-ke-css-nhan-bo-loc`, worktree riêng từ `3c3fd09`. Chỉ chuyển hai thay đổi thuộc lỗi từ checkout chung; các thay đổi khác ở vandonmoi giữ nguyên. Chưa commit/push.
- CSS exec-* đã tồn tại trong executive-statistics.css và được template nạp. Bộ rà thiếu tệp này: bổ sung vào danh sách CSS cần kiểm, không thêm ngoại lệ bỏ qua tên lớp.
- Bảy ô lọc đã có nhãn bọc ngoài (HTML hợp lệ), nhưng bài rà chỉ nhận for/id. Bổ sung for/id duy nhất cho nguồn phân tích, hai ngày, cách nhóm và ba nguồn bộ phận. Không đổi bố cục, truy vấn, dữ liệu, quyền hoặc công thức.

## Bằng chứng

- Trước sửa: hai bài test_giao_dien cho statistics.html thất bại đúng lỗi danh sách CSS và liên kết nhãn.
- Sau sửa trên worktree: **612 passed, 14,41s**, gồm core/tests/test_giao_dien.py, crm/tests/test_executive_statistics.py và crm/tests/test_waybill_new.py; lệnh có `-m "not cham and not trinh_duyet"`.
- Chrome thật trên database test riêng: Admin/Sale ở 1440×900 và 390×900 đều đạt. Kiểm stylesheet đã tải và có CSS rules, display:flex thực tế; nhận diện nhãn, liên kết for/id, bấm nhãn đưa focus vào ô; chọn Vận đơn, lọc ngày và nhóm sản phẩm, URL giữ bộ lọc; không tràn trang, không pageerror. Fixture trình duyệt chạy riêng thành công, không tính skip là đạt.
- Một lượt E2E đầu thất bại vì selector exact của script không tính phần text trong select lồng label; sửa selector theo tiền tố nhãn và kiểm trực tiếp quan hệ labels/for/id. Mã sản phẩm không thay sau đó. Lượt cuối đủ bốn trường hợp đều đạt.
- Thời gian Chrome trên fixture nhỏ: tải Tổng hợp 196–205 ms, đổi nhóm 97–126 ms. Đây là từng lần thao tác, không phải percentile hay bằng chứng tải lớn; không chạy lại Locust do chỉ đổi thuộc tính nhãn và cấu hình bài rà, không thêm truy vấn. Không đóng các vấn đề hiệu năng API/lưới từ task khác.
- Diff check đạt. Không thêm dependency/migration.

## Chạy lại từ worktree

```powershell
docker compose -f deploy/docker-compose.yml run --rm --no-deps -e RUN_MIGRATIONS=0 -e POSTGRES_DB=knjsc_fix_statistics web pytest core/tests/test_giao_dien.py crm/tests/test_executive_statistics.py crm/tests/test_waybill_new.py -m "not cham and not trinh_duyet" --tb=short
```

E2E: bật STAT_LABEL_BROWSER=1 cho crm/tests/test_statistics_labels_browser.py, database cơ sở riêng `knjsc_fix_stats_browser`, map cổng 8812. Chạy scripts/kiem-thu-statistics-labels.cjs bằng Node/Playwright/Chrome đã có. Script kiểm manifest database test và ghi kết quả để fixture tự đóng server, dọn database test. Dùng --no-deps để không thay container DB/Redis của checkout đang chạy.

JSON/ảnh trong storage/statistics-label-*; stylesheet và nhãn được kiểm trên bản cuối. Đánh dấu phần hỗ trợ giao diện nhóm 05 trong KNJSC_PROBLEM, không đóng toàn yêu cầu thống kê.
