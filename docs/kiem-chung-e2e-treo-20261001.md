# Kiểm chứng — CI e2e treo tới hết 20 phút (TL-71) — 01.10.2026

Nhánh `claude/chan-doan-e2e-treo` tách từ `main` (`9a2722c`). Chỉ sửa CI và `app/conftest.py` (hạ tầng kiểm
thử): không đụng mã ứng dụng, không thêm thư viện, không migration. Điều tra chạy trên máy ảo Claude Code:
PostgreSQL 16 cục bộ, Chromium không màn hình (Playwright 1.56), Python 3.11 và 3.12. Proxy của máy ảo chặn phông
Google nên 9 bài `test_pha_luoi_ghi_chu.py` luôn đỏ tại máy vì lỗi console `ERR_CERT_AUTHORITY_INVALID`. Đây là lỗi
môi trường đã biết (TL-67), trên CI không gặp.

## Hiện tượng

- Lượt #120 trên `main` (`b38505e`, sau khi gộp #72): "pytest (bộ chính)" xanh. Job "pytest e2e (Chromium)" bị
  GitHub huỷ ở phút 20: bước `pytest tests/e2e` chạy từ 02:15:05 tới 02:34:30, trong khi bình thường chỉ mất 3 phút
  40. Log không có dòng nào của pytest: `-q` của pytest.ini in mọi dấu chấm trên một dòng, mà dòng đó chưa xuống
  dòng nên GitHub chưa ghi.
- Đã gặp một lần trước, chưa ai ghi lại: lượt #107 lần 1 (29.09, PR #51, `0d3154b`) treo y hệt; chạy lại thì xanh.
- Không do mã của PR nào: cùng cây mã của #120 đã qua e2e ở lượt #118 và #119.

## Khoanh vùng: bài 18 `test_do_hieu_nang_1000_dong_ghi_chu_400`

Ba dấu vết độc lập cùng chỉ một chỗ.

**1. Postgres của CI ngừng ghi ở cùng một điểm.** Checkpoint định kỳ ở phút thứ 5 của hai lượt treo:

| Lượt | distance | sync files | redo → lsn |
|---|---|---|---|
| #120 | 21.424 kB | 9.036 | cách nhau 56 byte |
| #107 | 21.437 kB | 9.035 | cách nhau 56 byte |

Khoảng cách 56 byte giữa redo và lsn nghĩa là từ lúc checkpoint bắt đầu tới lúc xong, không ai ghi thêm gì. Để
quy điểm này ra bài kiểm, mình dựng tại máy một cụm Postgres 16 mới tinh y như dịch vụ của CI: khởi tạo, tạo
`knjsc_db`, khởi động lại. Rồi đo vị trí WAL sau từng pha của từng bài.

| Điểm (tại máy) | kB WAL |
|---|---|
| Hết thân bài 18 (vừa chèn 1000 dòng ghi chú 400 ký tự) | 20.692 – 20.767 |
| Hết dọn bảng bài 18 | 21.097 – 21.172 |
| Hết thân bài 19 | 21.236 – 21.305 |
| Hết dọn bảng bài 19 | 21.641 – 21.705 |
| Hết thân bài 18, rồi giả lập treo 30 giây: autovacuum dọn `forms_builder_datarecord` | **21.454** |
| … giả lập treo 150 giây | 21.460 |

Lúc đầu mình khoanh nhầm vào bài 19–20, vì chưa tính phần WAL mà autovacuum ghi thêm sau lúc treo. Khi giả lập
treo ngay sau thân bài 18, autovacuum dọn 1002 dòng vừa chèn và ghi thêm khoảng 700 kB, rồi đứng yên. CI dừng ở
21.424 và 21.437 kB, lệch 40 kB, nằm trong độ lệch giữa các lần chạy tại máy (±70 kB).

**2. Ảnh chụp.** Lượt treo vẫn tải lên 13 ảnh: 6 ảnh (đặt lại mật khẩu) + 4 (điện thoại) + 3 (bài 15–17).
Nghĩa là đã qua bài 17 nhưng chưa tới bài 22 (bài có chụp ảnh). Bài 18–21 không chụp ảnh.

**3. Tái hiện tại máy.** Chạy y như CI (Python 3.12, không Redis, cả `tests/e2e`), lượt thứ 5 treo đúng bài 18.
faulthandler in ở giây thứ 60:
- luồng chính đứng trong vòng lặp asyncio của Playwright, chờ trình duyệt trả lời;
- bốn luồng máy chủ thử rảnh, đứng ở `readinto` chờ yêu cầu mới trên kết nối giữ sẵn;
- không luồng nào nằm trong psycopg.

Vậy đây không phải chuyện khoá CSDL như TL-67.

Số lần chạy tại máy:

| Cách chạy | Số lần | Treo |
|---|---|---|
| Riêng bài 19, lặp trong một phiên (py3.11, có Redis) | 30 | 0 |
| Cả lượt e2e đầu (py3.11, có Redis) | 2 | 0 |
| 18–20 bài đầu, đo WAL (py3.11 và py3.12) | 6 | 0 |
| Cả lượt e2e đầu (py3.12, không Redis) | 5 | 1, bài 18 |
| 20 bài đầu, có bộ canh và cổng CDP (py3.12, không Redis) | 24 | 0 |
| Cả lượt e2e đầu, có bộ canh và nhật ký trang (py3.12, không Redis) | 12 | 0 |

Tỉ lệ treo thấp: CI 2 trên khoảng 18 lượt, tại máy 1 trên 49 lần đi qua bài 18. Chưa bắt lại được lần thứ hai có
ngăn xếp greenlet.

## Nghi phạm

Bài 18 có hai lời gọi Playwright không có giới hạn thời gian (`page.evaluate` không nhận `timeout`):

- **Vòng cuộn hết 1000 dòng.** Mỗi bước cuộn một khung, chờ hai khung vẽ, rồi chờ mọi ô Mã đơn có `data-id`, tối
  đa 8 giây. Vòng có tối đa 600 bước. Nếu dữ liệu không về, mỗi bước mất đủ 8 giây và cả bài kéo dài tới 80 phút.
  Lúc in ngăn xếp, máy chủ không xử lý yêu cầu nào; điều đó khớp với việc lưới không còn xin dữ liệu.
- **`document.fonts.ready` trong `_mo_luoi`.** Trên CI phông tải thật từ Google nên có thể chờ lâu; tại máy phông
  bị chặn nên lỗi ngay.

Sửa gốc cần biết chính xác lời gọi nào, nên trước hết cho CI in được ngăn xếp.

## Sửa (chẩn đoán)

| Tệp | Thay đổi |
|---|---|
| `.github/workflows/ci.yml` | Hai bước pytest e2e thêm `-vv` (mỗi bài một dòng; pytest.ini có `-q` nên phải hai v) và `-o faulthandler_timeout=120` (bài nào đứng quá 2 phút thì in ngăn xếp các luồng; bài chậm nhất hiện mất chừng 15 giây). Thêm `timeout-minutes` 10 và 8 cho hai bước, để bước treo tự dừng mà job vẫn còn thời gian giữ ảnh và in log Postgres |
| `app/conftest.py` | Hook `pytest_runtest_protocol`: khi có `faulthandler_timeout`, sau mốc đó một giây thì in thêm ngăn xếp mọi greenlet ra stderr thật (fd mà faulthandler của pytest dùng). Playwright đồng bộ chạy thân bài trong một greenlet nên faulthandler không thấy được dòng của bài. Không đặt `faulthandler_timeout` thì hook không làm gì |
| `docs/test-log.md`, `backlog.md`, `backlog-kanban.md` | TL-71 |

Đề xuất ban đầu có bật `log_lock_waits` cho Postgres của job e2e. Mình đã bỏ, vì ngăn xếp lúc treo cho thấy không
phiên nào chờ khoá.

## Kiểm

| Việc | Kết quả |
|---|---|
| Ép in: bài 19 với `-o faulthandler_timeout=12` (py3.12) | Dòng tên bài kèm `Timeout (0:00:12)!`, ngăn xếp các luồng, rồi khối "== TL-71 …" chứa ngăn xếp greenlet, chỉ tới `test_ghi_chu_tu_gian_dong.py` dòng 519 (`wait_for_function` chờ lần hỏi mốc). Bài vẫn đạt |
| `ci.yml` đọc bằng PyYAML | Hợp lệ; hai lệnh và hai hạn giờ đúng như bảng trên |
| `pytest tests/e2e -m trinh_duyet -vv -rs --durations=10 -o faulthandler_timeout=120` (py3.12) | 37 đạt, 2 bỏ qua, 4 phút 45. 9 đỏ đều ở `test_pha_luoi_ghi_chu.py` do proxy chặn phông (đã biết). Mỗi bài một dòng, không lần in ngăn xếp nào. Bài chậm nhất 12,4 giây |
| `pytest -m trinh_duyet --ignore=tests/e2e -vv -rs --durations=10 -o faulthandler_timeout=120` (py3.12) | 8 đạt, 9 bỏ qua như CI (giá đỡ cho script Node), 1 phút 41. Bài chậm nhất 27 giây. Cảnh báo cũ "database đang có phiên khác" lúc xoá CSDL cuối phiên (TL-67) |
| Bộ chính `pytest -m "not trinh_duyet" -rs` (py3.12) | 2.856 đạt, 7 bỏ qua (thiếu điều kiện ngoài, như trước). Chạy trên một cụm Postgres khác, song song với hai lượt e2e |
| Chạy lại job e2e của lượt #120 trên GitHub (chủ dự án duyệt) | Lần chạy thứ 2 của lượt #120 (`b38505e`) xanh; bước `tests/e2e` mất 3 phút 44. Lượt #122 (`9a2722c`, sau #73) cũng xanh cả hai job |

## Chưa làm / để lại

- Chưa sửa gốc. Lần treo sau trên CI sẽ có tên bài và ngăn xếp greenlet; khi đó sửa đúng lời gọi đang chờ. Nếu
  muốn chặn ngay, có thể giới hạn tổng thời gian vòng cuộn của bài 18 để treo thành đỏ có thông báo. Cách này đổi
  bài kiểm nên cần chủ dự án duyệt.
- Các công cụ tạm chỉ nằm trên máy ảo, không vào kho mã: bộ đo WAL theo bài, bộ canh in ngăn xếp greenlet kèm nhật
  ký trang, các cụm Postgres mô phỏng CI.
