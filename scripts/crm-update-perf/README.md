# Kiểm tải CRM-UPDATE

Harness của chiến dịch ADR-027, chỉ dùng dữ liệu synthetic trong môi trường
`knjsc-crm-update-test`. Không chạy seed hoặc tải lên Compose đang sử dụng.
Kết quả và giới hạn: [biên bản](../../docs/kiem-chung-crm-update-20260912.md).

## Điều kiện

- Docker, image ứng dụng `knjsc-web` đã có Locust và các dependency của dự án.
- PostgreSQL riêng `knjsc-crm-update-db`; database
  `test_crm_update_load_100000` và `test_crm_update_load_300000`.
- Snapshot trước sửa và manifest tại `storage/crm-update/baseline`,
  `storage/crm-update/manifest.json`. Không thay bằng HEAD đang làm dở.
- Chrome/Playwright host đã có. Chỉ dùng cổng test 8853; các fixture E2E khác
  dùng cổng và database pytest riêng.
- Đọc script trước khi chạy. `seed.py` tạo dữ liệu/tài khoản test;
  `start-app.ps1` thay container test tên `knjsc-crm-update-before`.
  Không dùng các tên này cho dịch vụ thật.

## Trình tự

1. Dựng hai database test bằng `seed.py`; mỗi kích thước gồm ba bảng với
   số dòng tương ứng **trên mỗi bảng**, 20 tài khoản/bộ phận. `ready.json`
   chứa session test, không đưa vào Git hoặc báo cáo công khai.
2. Chạy `resources.ps1` để lấy CPU/RAM. Dùng `matrix.ps1 -Stage before`,
   rồi `matrix.ps1 -Stage after`: mỗi tổ hợp 60 giây warmup + 300 giây đo.
   Không chạy functional/seed cùng cửa sổ đo đối chứng.
3. `python scripts/crm-update-perf/check_matrix.py`: chỉ cho phép đi tiếp
   khi đủ bốn lượt bản sau, đúng dữ liệu và đạt ngưỡng.
4. `start-app.ps1 -Rows 300000 -Browser -Stage before|after`, chạy
   `browser.cjs` với `LOAD_DIR` và `LOAD_STAGE` tương ứng. Mỗi cấu hình
   1440/1280/390/zoom thật 125% có 100 mẫu chọn, cuộn, nhập. Không ép click
   xuyên cột ghim nếu baseline không thao tác được.
5. Chạy `bulk.py` qua `docker exec` vào app test: 30 lượt, mỗi lượt 400
   dòng × 5 ô, đối chiếu 12.000 dòng. Kiểm p95 riêng với trần 5 giây.
6. **Sau tất cả so sánh**, `normalize_test_time.py` đưa timestamp synthetic
   tương lai về quá khứ để kiểm thay đổi trong bài bền. Không dùng kết quả
   sau bước này để ghép lại vào đối chứng before/after cũ.
7. `start-background.ps1` tạo Redis/worker riêng; khởi động app bằng
   `start-app.ps1 -Rows 300000 -Browser -Background`. `background.py` kiểm
   nhập 100 dòng, xuất nền 11.111 dòng và nội dung Excel.
8. `endurance.ps1`: 19 Locust + 1 Chrome = 20 client tương tác, cộng worker
   nền; 60 giây warmup + 1800 giây đo, 31 vòng nhập/xuất. Không thay code
   ứng dụng giữa lượt. Script dừng nếu child lỗi hoặc Chrome báo lỗi.
9. `check_endurance.py`, `summarize.py`, `resources_summary.py` và
   `package_diff.py` kiểm/tổng hợp kết quả. Phải xem đầy đủ lỗi và skip,
   không chỉ nhìn file cổng đạt từ một lượt trước.

Nếu đo lại, lưu riêng artifact của lượt bị loại trước khi chạy. Lượt dừng
sớm không được tính thành 300/1800 giây; `measured` bắt đầu từ 0 nếu chưa
hết làm nóng. HTTP 409 đổi phiên bản của giao thức đọc được xác minh JSON
và kiểm phục hồi, ghi riêng; không bỏ qua mọi 409 hoặc lỗi console.

## Bằng chứng và dọn dẹp

Giữ JSON mẫu thô, oracle, log server/worker, ảnh và bảng tổng hợp. Metadata
không có dữ liệu khách hàng thật. Thời gian UI là automation tới animation
frame, không phải INP/FPS; IME mô phỏng không thay kiểm bộ gõ hệ điều hành.

Sau khi hoàn tất: dừng sampler và container test, xóa session/Chrome profile
test cùng file nhập/xuất tạm sau khi đã đối chiếu. Chỉ xóa đường dẫn tuyệt
đối đã xác nhận nằm trong thư mục bằng chứng của chiến dịch; giữ snapshot,
manifest, diff và số đo. Không xóa Docker volume/container của Compose
đang sử dụng. Chưa commit/push hoặc kích hoạt checkout chính tự động.
