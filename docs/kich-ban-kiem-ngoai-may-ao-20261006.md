# Kịch bản kiểm ngoài máy ảo — đợt săn lỗi 06.10.2026

Những việc máy ảo của Claude Code trên web không làm được: cần VPS, máy chủ dự án hay máy thật của người dùng. Viết
sẵn để chủ dự án, Codex hoặc Claude Code CLI chạy. Mỗi mục ghi: chạy ở đâu, lệnh, đạt khi nào. Chạy xong thì ghi kết quả
vào biên bản phát hành VPS của lượt đó (`docs/kiem-chung-phat-hanh-vps-<ngày>.md`). **Không ghi địa chỉ, cổng, khoá SSH
vào kho.**

Thứ tự đề nghị: mục 1 trước khi phát hành nhánh này lên VPS; mục 2–4 ngay sau phát hành; mục 5–6 khi tiện.

## 1. Migration của nhánh trên bản sao dữ liệu VPS

**Ở đâu:** máy có SSH tới VPS. **Vì sao:** nhánh này thêm `core/0007_submission_receipt` và đổi cấu hình; migration
mới chạy xuôi/ngược trên dữ liệu thử, chưa chạy trên dữ liệu thật.

1. Làm theo khuôn backup và phục hồi thử của [biên bản 29.09](kiem-chung-phat-hanh-vps-20260929.md): dump, phục hồi vào
   **database tạm riêng** với `--exit-on-error`.
2. Dựng image của commit cần phát hành, trỏ một container tạm (`docker compose run --rm`) vào database tạm, chạy
   `python manage.py migrate`, rồi `python manage.py migrate core 0006` (ngược) và `migrate` lại (xuôi).
3. `python manage.py makemigrations --check --dry-run` không sinh gì.
4. Đếm số dòng từng bảng trước/sau: chỉ bảng `submission_receipt` mới thêm, các bảng khác không đổi.
5. Xoá database tạm.

**Đạt khi:** ba lượt migrate không lỗi, số dòng không đổi, ghi thời gian chạy.

## 2. Diễn tập sự cố trên VPS (AC-10.13, AC-10.15)

**Ở đâu:** VPS, giờ không có người dùng. **Vì sao:** máy ảo đo trên `runserver` và gunicorn giả lập; VPS có nginx và
5 container thật.

| Bước | Lệnh (thư mục `deploy/production`) | Đạt khi |
|---|---|---|
| Postgres khởi động lại | `docker compose restart db`, đợi `healthy`, rồi mở 10 lần trang Báo cáo tổng hợp và lưới Vận đơn trên domain thật | Không lần nào lỗi 500 sau khi `db` đã healthy (trước bản sửa: mỗi luồng gunicorn lỗi một lần) |
| Redis tắt | `docker compose stop broker`, bấm Xuất Excel trên lưới Vận đơn (bảng đủ lớn để chạy nền) | Trong khoảng 1 giây hiện lời "Không gửi được vào hàng đợi tác vụ nền…" trên lưới; không trang lỗi |
| Redis bật lại | `docker compose start broker`, đợi 30 giây, xuất lại | Tác vụ chạy xong, tải được tệp; `docker compose logs worker` có dòng nối lại |
| Bộ đệm CRM tắt | `docker compose stop cache`, mở Thống kê CRM, lưới | Vẫn mở được, chậm hơn không đáng kể; bật lại `cache` |

## 3. Trang lỗi và đĩa đầy trên VPS (AC-10.14)

1. Mở một đường dẫn không có trên cả hai domain: phải là trang "Không tìm thấy trang" tiếng Việt.
2. **Không** làm đầy đĩa thật. Thay vào đó kiểm dung lượng: `df -h` cho ổ chứa volume `storage` và volume `postgres`.
   Ghi phần trăm đã dùng vào biên bản. Trên 80 % thì báo chủ dự án.
3. Đặt `OPERATOR_EMAILS` nếu chưa đặt — không có thì thư cảnh báo "Máy chủ hết chỗ lưu tệp" chỉ nằm trong nhật ký.

## 4. Đo hiệu năng trên VPS

**Ở đâu:** VPS. **Vì sao:** các số `PERF_*` mới đo trên máy ảo; bản sửa thêm `CONN_HEALTH_CHECKS` (một lượt hỏi
Postgres nhẹ ở đầu mỗi yêu cầu) và middleware chuẩn hoá chữ.

- **Không** chạy `scripts/kiem-tai-kn-crm.*` trên VPS: script đó nạp dữ liệu giả và bật lại container, chỉ dành cho
  máy local.
- Sau phát hành, để hệ thống chạy một ngày dùng bình thường rồi gom p95 thật bằng
  `python3 scripts/gom-p95-vps.py --since 24h` (đọc nhật ký đo yêu cầu có sẵn, không đo thêm). So với lượt gom trước
  phát hành (`--since 7d` trước khi phát hành, lưu `--json`).

**Đạt khi:** p95 đọc ≤ 1 s, ghi ≤ 0,5 s, poll ≤ 0,3 s (`core/constants.py`); không tuyến nào tệ hơn lượt trước quá 10 %.

## 5. Khôi phục sao lưu thật — đo RTO, RPO

**Ở đâu:** máy chủ dự án hoặc VPS, database tạm. **Vì sao:** đã phục hồi thử dump lúc phát hành; chưa đo thời gian
dựng lại cả hệ thống từ bản sao lưu đêm (`sao_luu` lúc 02:00).

1. Lấy bản sao lưu đêm mới nhất (`python manage.py phuc_hoi` không cờ chỉ liệt kê). Ghi giờ tạo bản → **RPO** (mất
   tối đa bao nhiêu giờ dữ liệu).
2. Bấm giờ: phục hồi vào database tạm, trỏ một cặp ERP/CRM tạm vào đó, đăng nhập, mở Báo cáo tổng hợp tháng trước →
   **RTO**.
3. Đối chiếu tổng Báo cáo tổng hợp tháng trước giữa bản thật và bản phục hồi (cách đối chiếu ở
   [biên bản đối soát](kiem-chung-san-loi-doi-soat-20261006.md)).

**Đạt khi:** số khớp; ghi RTO, RPO vào biên bản để chủ dự án quyết có cần sao lưu dày hơn không.

## 6. Trình duyệt và bộ gõ thật (AC-9.6, AC-10.12)

**Ở đâu:** máy Windows và máy Mac của người dùng.

| Máy | Thao tác | Đạt khi |
|---|---|---|
| Windows + Unikey (Telex), Windows + EVKey | Gõ "Nguyễn Ngọc Ánh" vào ô Tên khách trên lưới, Enter; gõ vào ô Ghi chú; nộp một báo cáo có tên sản phẩm có dấu | Lưu đúng, không rớt hay lặp chữ |
| Mac + bộ gõ Telex của macOS, Safari | Như trên; rồi từ máy **Windows** tìm "Ngọc Ánh" ở ô tìm kiếm lưới | Ra đúng dòng do máy Mac nhập |
| Safari, Firefox | Mở lưới, tắt Wi-Fi, sửa một ô, đợi "Lỗi lưu", bật Wi-Fi | Lời báo tiếng Việt "Mất kết nối mạng…", có mạng thì tự lưu đúng một lần |
| Điện thoại (4G yếu) | Nộp báo cáo, bấm Nộp hai lần | Một báo cáo (AC-4.12) |

## 7. Việc chờ chủ dự án chốt (không cần máy, cần quyết định)

Gom từ các biên bản của đợt này:
- Báo cáo ngày có nhận Doanh số âm không ([giờ, tiền, số](kiem-chung-san-loi-gio-tien-so-20261006.md)).
- Lời "đang bị khoá tạm" lộ tài khoản có thật; chuỗi gõ nhầm vào ô tên đăng nhập vào nhật ký hoạt động; chặn dò rải
  theo IP ([đăng nhập và nhật ký](kiem-chung-san-loi-dang-nhap-nhat-ky-20261006.md)).
- nginx `server_tokens off` và Content-Security-Policy ([bảo mật](kiem-chung-san-loi-bao-mat-20261006.md)).
- Excel Báo cáo tổng hợp ghi tỉ lệ dạng số thực đủ chữ số ([đối soát](kiem-chung-san-loi-doi-soat-20261006.md)).
