# Bộ gom p95 thật của KN CRM từ log VPS — 22.09.2026

> **Đọc dòng này trước.** Biên bản này ghi phần **đã kiểm được trên máy ảo**:
> bộ gom chạy đúng. Nó **không chứa con số p95 thật nào của VPS**, vì Claude
> Code trên web không tới được VPS (CLAUDE.md). Mục cuối là chỗ trống có sẵn
> lệnh, để người có SSH điền vào.

## Câu hỏi này khác câu hỏi của biên bản 16.09

`kiem-chung-300k-10-nguoi-20260916.md` đo **tải giả lập kịch bản xấu nhất**:
300.000 dòng, 10 người cùng đập liên tục, và kết luận VPS vượt cả ba ngưỡng
(đọc p95 5.043 ms, lưu 2.341 ms, poll 3.868 ms). Đó là **trần**, không phải
đời thật.

Bộ gom này trả lời câu khác: **lưu lượng thật hằng ngày đang ở đâu.** Hai con
số sẽ khác nhau rất nhiều, và cả hai đều cần. Trần cho biết hệ thống gãy ở
đâu; số thật cho biết người dùng đang chịu gì. Đừng lấy số này phủ nhận số kia.

## Đo cái gì, lấy ở đâu

Không dựng đo mới. `deploy/production/compose.yml` đặt `CRM_REQUEST_METRICS: '1'`
từ đầu, nên `core/request_metrics.py` đã ghi **một dòng JSON cho mỗi yêu cầu**
ra stdout container, và Docker giữ lại. Số p95 thật đã nằm trên VPS nhiều ngày;
cái thiếu là bộ gom. `scripts/gom-p95-vps.py` chỉ đọc lại và tính phân vị —
không chạm dữ liệu, không khởi động lại gì, chạy được trong giờ làm việc.

| Nhóm | Gồm | Ngưỡng p95 (`core/constants.py`, ADR-016) |
|---|---|---|
| Hỏi thăm | tuyến kết thúc `moi-nhat/` | 300 ms |
| Ghi | mọi POST/PUT/PATCH/DELETE | 500 ms |
| Đọc | phần còn lại | 1000 ms |

Phân vị theo **thứ hạng gần nhất**, không nội suy: số trả về là một giá trị đã
thật sự xảy ra, nên truy nguyên được về đúng một dòng log.

## Đã kiểm được gì trên máy ảo

Môi trường: máy ảo Claude Code trên web, Python 3.12, PostgreSQL 16 cục bộ.
Nhánh `do-p95-vps` tách từ `codex/crm-update-solar-ui`.

| Kiểm | Lệnh | Kết quả |
|---|---|---|
| 13 bài của bộ gom | `pytest tests/test_gom_p95.py` | 13 đạt, 0,11 s |
| Toàn bộ bài không cần trình duyệt | `pytest -m "not trinh_duyet"` | xem mục dưới |
| Lint | `ruff check --select=E,W,F --line-length=110` | sạch |
| Độ phức tạp | `radon cc -a scripts/gom-p95-vps.py` | trung bình A (4,75), cao nhất B (7) |

Bài kiểm dựng từ **dòng log đúng khuôn thật** mà `request_metrics` phát ra, nên
đổi khuôn log mà quên bộ gom thì bài đỏ. Có một bài canh ba ngưỡng trong script
khớp `core/constants.py` — script chạy ngoài container nên phải chép ngưỡng, mà
chép thì sẽ trôi.

Thử mắt thường trên log giả lập 4.807 dòng hình dạng y hệt container `crm` (có
tiền tố `crm  |`, có dòng khởi động xen vào): đọc được 4.806 bản ghi, `moi-nhat/`
vào đúng nhóm Hỏi thăm chứ không lẫn vào Đọc, tuyến nhập tệp hiện trong bảng
nhưng mang dấu `*` và không kéo phán quyết nhóm Ghi xuống.

## Ba cái bẫy đã bịt, và vì sao chúng quan trọng

1. **`moi-nhat/` là GET nhưng ngưỡng 300 ms, không phải 1000 ms.** Xếp nó vào
   nhóm Đọc là che mất hẳn một nhóm đang vượt ngưỡng. Bộ gom xếp theo phương
   thức HTTP **cộng** đuôi tuyến, không theo danh sách liệt kê tay — thêm tuyến
   mới thì không phải sửa script, và không tuyến nào lặng lẽ rơi ra ngoài.
2. **Nhập tệp 20 giây là đúng thiết kế.** Tính nó vào nhóm Ghi thì nhóm nào cũng
   đỏ và con số mất hết ý nghĩa. Các tuyến chậm theo bản chất (nhập, xuất, tải
   mẫu, đăng nhập) vẫn in ra nhưng không tính vào phán quyết nhóm.
3. **p95 trên ba mẫu chỉ là số lớn nhất.** Dưới 20 mẫu script ghi "ít mẫu";
   dưới 5 mẫu thì không kết luận và trả mã thoát 2. Im lặng đưa ra "ĐẠT" ở đây
   là tự lừa — đúng thứ `docs/06` cấm.

## Chưa kiểm được gì

- **Chưa chạy trên VPS.** Đây là phần lớn nhất còn thiếu, xem mục cuối.
- **Cờ `--no-log-prefix`** chỉ có ở Docker Compose đủ mới. Không đoán phiên bản
  trên máy chủ nên script thử có cờ, hỏng thì thử lại không cờ; bộ đọc bắt JSON
  ở cuối dòng nên còn tiền tố cũng không sao. **Đường thử-lại này chưa chạy trên
  Compose cũ thật**, mới chỉ kiểm bằng log có sẵn tiền tố.
- **Chưa biết log còn lại bao nhiêu ngày.** `compose.yml` chưa đặt `logging:`
  nên Docker dùng `json-file` không giới hạn: log còn đủ để gom ngược nhiều
  ngày, nhưng cũng lớn dần không có trần trên VPS 2 nhân. Kiểm bằng
  `docker system df` trước.

## Chỗ trống cho người có SSH

Chạy trên VPS, chép kết quả vào đây rồi đổi ngày trên tiêu đề mục này:

```sh
cd /opt/knjsc-runtime
docker system df                                    # log còn bao nhiêu
python3 /opt/knjsc/scripts/gom-p95-vps.py --since 24h
python3 /opt/knjsc/scripts/gom-p95-vps.py --since 7d --json p95-$(date +%Y%m%d).json
```

| Nhóm | Số yêu cầu | p50 | p95 | p99 | Ngưỡng | Kết luận |
|---|---:|---:|---:|---:|---:|---|
| Đọc | | | | | 1000 | |
| Ghi | | | | | 500 | |
| Hỏi thăm | | | | | 300 | |

Khoảng đo: `--since ___`, ngày chạy ___, người chạy ___.

**Đọc bảng tuyến thế nào.** Cột `db p95` gần bằng `p95` nghĩa là nghẽn ở cơ sở
dữ liệu; chênh nhau nhiều nghĩa là nghẽn ở Python hoặc ở hàng đợi gunicorn. Cột
`TV` là số truy vấn — tuyến nào vọt lên là chỗ nghi N+1 trước tiên.

**Nếu nhóm nào dưới 20 mẫu:** nới `--since`, đừng kết luận. VPS này dưới 100
người dùng nên một ngày yên ả hoàn toàn có thể không đủ mẫu cho nhóm Ghi.

**Trước khi đặt `logging:` xoay vòng cho `compose.yml`:** gom và lưu `--json`
đã. Đặt giới hạn là xoá mất phần lịch sử chưa gom.
