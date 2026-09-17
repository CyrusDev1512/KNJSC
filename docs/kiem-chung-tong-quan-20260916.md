# Tổng quan ERP — sửa bố cục ngày 16.09.2026

## Phạm vi phát hành

Chủ dự án yêu cầu sửa riêng lỗi Tổng quan, push GitHub và cập nhật VPS.
Bản nền: `9ff2dec`. Chỉ đổi template Tổng quan và CSS riêng của màn hình.
Không đưa các thay đổi báo cáo, công thức, ngày tháng, dữ liệu, migration và tối ưu lưới còn ở local vào bản này.

## Trước / sau

- Trước: danh sách dt/dd dùng định dạng mặc định, giá trị nằm dưới nhãn và bị thụt vào; các thẻ bị kéo cao theo Marketing.
- Sau: mỗi chỉ tiêu có một hàng nhãn–giá trị, số căn phải, đường kẻ giữa hàng; thẻ có chiều cao theo nội dung. Lưới tự xếp lại khi màn hình hẹp.
- Giữ nguồn, thứ tự chỉ tiêu, giá trị, bộ lọc và URL chi tiết/theo nhân viên/phòng ban. Không sửa hay suy đoán loại tiền của báo cáo lịch sử.

## Kiểm chứng trước phát hành

- Xuất đúng nội dung Git index vào `storage/overview-fix/release/`, không kiểm chỉ bằng working tree có các tác vụ khác.
- `docker compose -f deploy/docker-compose.yml run --rm --no-deps -e RUN_MIGRATIONS=0 -e POSTGRES_DB=overview_fix -v C:/KNJSC/KNJSC/storage/overview-fix/release/app:/app web pytest reports/tests/test_activity.py -q`: exit 0, không skip. Kiểm phạm vi Staff/Leader/Manager/Admin và lỗi từng nguồn theo suite hiện có.
- Chạy preview riêng localhost:18026 từ bản xuất. Trình duyệt: 1280px và 390px không tràn ngang; nhãn và số nằm đúng hai cột; kiểm thêm 1440px nền tối. Các thẻ có chiều cao khác nhau theo số chỉ tiêu.
- Bấm Kết quả theo nhân viên mở Báo cáo tổng hợp và giữ nguồn/khoảng ngày/nhóm person. Console không có lỗi khi kiểm.
- Working tree local vẫn giữ cảnh báo tiền tệ thuộc tác vụ báo cáo trước; cảnh báo đó không có trong commit này.

## Vận hành

Phát hành bằng image theo commit, giữ hai compose hiện hành và giới hạn tài nguyên.
Không migration, seed hoặc sửa dữ liệu. Lưu image/cấu hình trước phát hành để quay lui.
Kiểm Django, collectstatic, tải CSS mới qua HTTPS, ERP/CRM trả HTTP 200 và trạng thái container.
Kiểm giao diện trực tiếp trên domain cần phiên đăng nhập còn hiệu lực.

## Kết quả phát hành 16.09.2026, 12:35 giờ Việt Nam

- Commit ứng dụng: `da6e2c0`, đã push nhánh `codex/crm-update-solar-ui` và xác nhận SHA GitHub khớp local.
- VPS fast-forward sạch từ `9ff2dec`; ERP/CRM/worker/heavy/beat chạy image `knjsc-app:da6e2c0-overview-20260916`. Giữ giới hạn bộ nhớ và cả hai compose hiện hành.
- Django check ERP và CRM: không lỗi. collectstatic: 2 file mới/cập nhật, 150 giữ nguyên. nginx config hợp lệ và đã reload upstream.
- Hai domain `/dang-nhap/` trả HTTP 200. CSS Tổng quan tải qua HTTPS và so byte với source VPS: khớp.
- Không migration, seed, sửa báo cáo lịch sử hoặc thay đổi dữ liệu nghiệp vụ.
- Cấu hình và tên image cũ: `/opt/knjsc-runtime/release-overview-20260916-123448/`. Log local: `storage/overview-fix/deploy.log`.
- Giao diện trình duyệt đã kiểm trên bản preview phát hành; phiên VPS hết hạn, đã nhờ đăng nhập lại và chưa có xác nhận. Không coi HTTP 200 là kiểm chứng màn hình Tổng quan sau đăng nhập.
