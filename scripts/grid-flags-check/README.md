# Kiểm chứng cờ lưới — 16.09.2026

Harness theo đợt đo, dùng lại `../order-code-check/`; đọc script trước khi chạy.
Không dùng tài khoản, database hoặc Compose đang vận hành. Runtime chứa session
test trong `storage/grid-flags-20260916`, không đưa cả thư mục lên Git.

- `prepare.py`: đóng băng HEAD và ứng viên trong working tree; loại riêng thay
  đổi ngày của task ERP. Đây là phép chụp cho đợt đo này, không phải công cụ
  tự tách mọi diff tương lai. Từ chối ghi đè manifest đã có.
- `run.py setup`: PostgreSQL/Redis/network riêng, seed 100.000 đơn test.
- `run.py start before|after|render|read|sync`: đặt lại **database test** về mẫu,
  khởi động cấu hình chọn. Không gọi khi một phase còn chạy.
- `run.py phase TEN after delivery|mixed 362`: 60 giây làm nóng và 300 giây đo;
  đổi `362` thành `3662` để đo 60 phút. Một Chrome nằm trong tổng 10 Vận đơn.
- `browser-real.cjs`: Chrome/API thật, 1440/390px, cuộn/chọn/nhập và reload
  kiểm lưu. `shared.py`: E2E lưới chung trên database test khác.
- `contract.py`, `invalidation_audit.py`: tái hiện hợp đồng metadata và token
  bị vô hiệu bởi đơn ngoài phạm vi. Các script này có ghi dữ liệu test;
  không chạy giữa bài tải hoặc trỏ sang production.
- `report.py TEN...`: xuất kết quả đã bỏ session/giá trị ô sang tài liệu.
- `cleanup.py`: chỉ dọn các container/volume/network đã kiểm thuộc đợt này,
  cùng `runtime.env`/`ready.json`. Giữ số đo và nguồn chụp.
- `deploy.sh COMMIT off`: script phát hành có backup và rollback image;
  chỉ chấp nhận các cờ tắt theo kết quả sàng lọc. Không tự chạy khi kiểm tải.

Không so số đo giữa profile CPU khác nhau, không tính lượt thiếu thời gian
hoặc Chrome lỗi là đạt. Local 12 CPU logic không tương đương VPS 2 vCPU.
Chi tiết, lỗi harness và giới hạn: [biên bản](../../docs/kiem-chung-co-toi-uu-20260916.md).
