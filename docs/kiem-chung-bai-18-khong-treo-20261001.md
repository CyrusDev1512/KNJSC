# Kiểm chứng — Bài đo hiệu năng 1000 dòng ghi chú không còn treo được (TL-71) — 01.10.2026

Nhánh `claude/sua-bai-18-khong-treo` tách từ `main` (`9a2722c`). Chỉ sửa bài kiểm
`app/tests/e2e/test_ghi_chu_tu_gian_dong.py`, không đụng mã ứng dụng, không thêm thư viện, không migration.
Chạy trên máy ảo Claude Code: PostgreSQL 16 cục bộ dựng như dịch vụ CI, Chromium không màn hình (Playwright
1.56), Python 3.12 như CI.

## Vì sao

Chẩn đoán ở PR #74 (biên bản `kiem-chung-e2e-treo-20261001.md`) khoanh hai lần CI treo 20 phút (lượt #107 ngày
29.09, #120 ngày 01.10) và một lần treo tại máy vào bài 18 `test_do_hieu_nang_1000_dong_ghi_chu_400`. Lúc treo,
luồng chính đứng chờ Playwright, máy chủ thử rảnh, không ai chờ khoá Postgres. Bài 18 có hai lời gọi
`page.evaluate` không giới hạn thời gian (Playwright không cho đặt timeout cho `evaluate`):

- Vòng cuộn hết 1000 dòng. Mỗi bước chờ hai khung vẽ bằng `requestAnimationFrame`, rồi chờ ô Mã đơn có dòng
  bằng rAF, hẹn 8 giây. Vòng có tối đa 600 bước. Nếu trang ngừng vẽ thì rAF không gọi lại và lời hứa treo mãi; nếu
  dữ liệu không về thì mỗi bước mất đủ 8 giây, cả vòng tới 80 phút.
- `_mo_luoi` chờ `document.fonts.ready` không có hẹn.

## Sửa

| Chỗ | Thay đổi |
|---|---|
| `CUON_HET_BANG`, `HAN_CUON_MS` (mới, đầu tệp) | Vòng cuộn tách thành hằng số, nhận hạn tổng 60 giây. Chờ khung vẽ đua với hẹn 1 giây; chờ dữ liệu bằng `setTimeout` 16 ms, hẹn 8 giây cho mỗi bước và không quá hạn tổng. Toàn bộ vòng còn đua với hẹn hạn tổng + 5 giây. Dừng thì trả trạng thái trang: số bước, đã tới cuối bảng chưa, vị trí cuộn, chiều cao bảng, số ô Mã đơn và số ô chưa có dòng, yêu cầu mạng (đang chờ, xong, lỗi; đếm bằng cách bọc `window.fetch` trong lúc cuộn rồi trả lại), rAF còn chạy không, thông báo của lưới |
| Bài 18 | Gọi `trang.evaluate(CUON_HET_BANG, HAN_CUON_MS)`, rồi kiểm đã cuộn tới cuối bảng: không tới thì đỏ, thông điệp kèm trạng thái trang. Phần đo p95 của AC-11.44 giữ nguyên |
| `_mo_luoi` | `document.fonts.ready` đua với hẹn 10 giây |

## Kiểm

**Ép tình huống bằng một bài tạm** (`tests/e2e/test_tam_bai18_treo.py`, đã xoá, không commit). Bài tạm nạp
1000 dòng như bài 18, mở lưới, rồi chạy `CUON_HET_BANG` với hạn 10 giây:

| Tình huống | Cách ép | Kết quả |
|---|---|---|
| Dữ liệu không về | `page.route("**/du-lieu/**")` không bao giờ trả lời | Dừng sau 10,0 giây: 69 bước, chưa tới cuối bảng, 2 ô Mã đơn chưa có dòng, 3 yêu cầu dữ liệu đang chờ |
| Trang ngừng vẽ | Thay `window.requestAnimationFrame` bằng hàm rỗng | Dừng sau 11,0 giây: `raf_chay: false` |
| Bình thường | — | Tới cuối bảng sau 8,0 giây: 240 bước, 10 yêu cầu, rAF chạy |

Với vòng cũ, hai tình huống đầu đều thành treo. Trang ngừng vẽ thì vòng cũ chờ rAF mãi. Dữ liệu không về thì mỗi
bước chờ đủ 8 giây; khoảng 240 bước tới cuối bảng là hơn 30 phút, vượt hạn 20 phút của job CI.

**pytest như CI:**

| Lệnh | Kết quả |
|---|---|
| `pytest tests/e2e -m trinh_duyet -vv -rs --durations=10 -o faulthandler_timeout=120` | 37 đạt, 2 bỏ qua, 4 phút 49. 9 đỏ đều ở `test_pha_luoi_ghi_chu.py` do proxy máy ảo chặn phông Google (đã biết, CI không gặp). Bài 18 đạt, thân bài 11,3 giây như trước. Mọi bài khác của tệp, đều qua `_mo_luoi` mới, đạt |
| `pytest -m trinh_duyet --ignore=tests/e2e -vv -rs --durations=10 -o faulthandler_timeout=120` | 8 đạt, 9 bỏ qua như CI, 1 phút 41. Cảnh báo cũ "database đang có phiên khác" lúc xoá CSDL cuối phiên (TL-67) |
| `pytest tests/test_truy_vet.py` | 36 đạt |

## Lần 2 — lượt CI #126 vẫn treo, đổi cách chờ

Chủ dự án bảo gộp #75. Mình gộp `main` (`b2ba0a0`, có #74) vào nhánh, head mới `d49a470`. Lượt CI #126 trên head
đó: bộ chính xanh, job e2e treo lại ở bài 18. Nhờ chẩn đoán của #74, lần này log có đủ dấu vết:

| Giờ (UTC) | Log |
|---|---|
| 08:04:40 | Bài 17 đạt, bài 18 bắt đầu |
| 08:06:40 | `faulthandler_timeout` (120 giây): luồng chính đứng trong vòng sự kiện asyncio của Playwright; greenlet của bài đứng ở dòng 512 `trang.evaluate(CUON_HET_BANG, HAN_CUON_MS)`; sáu luồng máy chủ thử đều rảnh, chờ đọc yêu cầu mới |
| 08:13:40 | Bước `pytest e2e (tests/e2e)` bị cắt sau 10 phút; 13 ảnh tải lên, Postgres ghi 21.462 kB WAL — như hai lần trước |

Hạn tổng trong trang là 65 giây mà sau hơn 9 phút vẫn không chạy, tức trang không còn chạy JS: tab sập hoặc luồng
chính kẹt. Hẹn giờ đặt trong trang không cứu được trường hợp này.

### Playwright 1.56 khi trang không còn chạy JS

Đọc mã driver (`server/frames.js`, `server/page.js`, `server/chromium/crConnection.js`) rồi thử tại máy bằng
một trang có vòng `for (;;)`:

| Cách chờ hay gọi | Trang kẹt | Tab sập |
|---|---|---|
| `page.evaluate` (chờ promise) | Đứng mãi, không có hạn | Đứng mãi: tab sập chỉ huỷ các thao tác đua với `openScope`, còn `evaluate` thì không, nên callback CDP không bao giờ có trả lời |
| `wait_for_function(timeout=4000)` | **Đứng hơn 40 giây:** hết hạn xong còn gọi `handle.evaluate(h => h.abort())` vào trang rồi chờ | Không thử |
| `expect_console_message(timeout=4000)` | Hết hạn đúng 4,0 giây (hạn đếm trong Python) | Ném `Page crashed` ngay |
| Lệnh CDP gửi thẳng vào tab | `Debugger.enable` đứng mãi | `Page.crash` đứng mãi |
| Lệnh qua phiên DevTools của trình duyệt, tới tab bằng `Target.sendMessageToTarget` | Trả lời ngay. Debugger bật từ trước thì `Debugger.pause` dừng đúng dòng vòng lặp | — |

### Sửa

| Chỗ | Thay đổi |
|---|---|
| `_chay_co_han(trang, ham_js, doi_so, han_ms, capsys)` | Khởi động hàm chạy nền bằng một `evaluate` ngắn. Hàm xong thì `console.log` kết quả kèm tiền tố `DAU_KET_QUA`. Python chờ dòng đó bằng `expect_console_message`. Quá hạn hay tab sập thì in chẩn đoán ngay ra log bằng `capsys.disabled()` (lỡ bước dọn sau đó đứng thì tóm tắt cuối phiên không in) rồi `pytest.fail` |
| `_DevToolsCuaTab` | Gắn vào tab trước khi chạy, qua phiên DevTools của trình duyệt (`Target.attachToTarget` không phẳng), bật Debugger. Quá hạn thì ghi lại: Playwright báo gì, tab sập chưa, CPU từng tiến trình trong 2 giây (`SystemInfo.getProcessInfo`), ngăn xếp JS lúc `Debugger.pause` (12 khung đầu). Bước nào hỏng thì ghi lỗi rồi làm bước sau. Gắn không được thì bài vẫn chạy, chỉ thiếu chẩn đoán |
| Bài 18 | `cuon = _chay_co_han(trang, CUON_HET_BANG, HAN_CUON_MS, HAN_CHO_CUON_MS, capsys)`; `HAN_CHO_CUON_MS` = 60 + 15 giây, dài hơn hạn trong trang để trang còn sống luôn tự trả kết quả trước. Phần đo p95 AC-11.44 giữ nguyên |
| `_mo_luoi` | Giữ hạn 10 giây đặt trong trang. Kế hoạch định đổi sang `wait_for_function`, nhưng thử thấy hàm đó cũng đứng khi trang kẹt; ba lần treo đều ở vòng cuộn, lúc mở lưới trang vẫn sống |

### Kiểm lần 2

**Ép tình huống bằng bài tạm** (`tests/e2e/test_tam_ep_treo.py`, đã xoá, không commit). Ba bài chạy liền nhau
trong một phiên pytest cùng bài 18 thật:

| Ca | Cách ép | Kết quả |
|---|---|---|
| Luồng chính kẹt | `add_script_tag` một hàm `quay_mai_tam` có `for (;;)`, gọi sau 1 giây; hạn thử 8 giây | Đỏ sau 10,2 giây. Chẩn đoán: `renderer` chạy 1,98 trong 2 giây, ngăn xếp `quay_mai_tam :3:3` (đúng dòng vòng lặp), tab chưa sập. Dọn bài 0,78 giây |
| Tab sập | Giết tiến trình vẽ bằng `SIGKILL` sau 2 giây; hạn thử 15 giây | Đỏ sau 4,0 giây: `Page crashed`, `tab_sap: true`, không còn tiến trình vẽ |
| Bình thường ngay sau đó | Hàm trả `21 * 2` | Đạt; trình duyệt dùng chung còn dùng tiếp được |

**Số đo AC-11.44** (Debugger bật suốt vòng cuộn so với bản cũ), mỗi lượt một phiên pytest:

| Bản | p95 một khối (ms) | Việc dài ≥ 50 ms |
|---|---|---|
| Cũ (`d49a470`), 3 lượt | 18,3 / 15,0 / 10,1 | 0 |
| Mới, 4 lượt | 12,9 / 13,4 / 16,7 / 17,7 | 0 |

Vòng so sánh đầu có một lượt của bản mới không in số đo; log lượt đó không giữ lại nên không biết lý do. Các
lượt sau lặp lại bài 18 đều lưu log, xem dòng cuối.

**pytest như CI** (bản mới):

| Lệnh | Kết quả |
|---|---|
| `pytest tests/e2e -m trinh_duyet -vv -rs --durations=10 -o faulthandler_timeout=120` | 37 đạt, 2 bỏ qua, 4 phút 30. 9 đỏ đều ở `test_pha_luoi_ghi_chu.py`, do proxy máy ảo chặn phông Google (`ERR_CERT_AUTHORITY_INVALID`), như lần 1 |
| `pytest -m trinh_duyet --ignore=tests/e2e -vv -rs --durations=10 -o faulthandler_timeout=120` | 8 đạt, 9 bỏ qua, 1 phút 34 |
| `pytest tests/test_truy_vet.py` | 36 đạt |

**Lặp riêng bài 18 tại máy** (cụm Postgres riêng, mỗi lượt một phiên pytest, dừng khi đỏ hoặc hết 40 phút):
lúc commit đã chạy 6 lượt, cả 6 đạt, mỗi lượt khoảng 20 giây, p95 từ 8,3 tới 14,0 ms. Vòng
chạy tiếp tới khi đỏ hoặc hết 40 phút; kết quả cuối báo lại trong PR #75.

## Chưa làm / để lại

- Chưa biết vì sao trên CI trang ngừng chạy JS. Lần sau gặp lại, bài 18 đỏ sau khoảng 80 giây, khối
  `== TL-71` trong log có ngăn xếp JS (luồng chính kẹt ở đâu) hay dấu tab sập; khi đó mới sửa gốc, có thể ở lưới.
- `_o_ghi_chu` và vài bài khác trong tệp vẫn `evaluate` chờ rAF không hẹn. Chưa thấy treo ở đó; nếu treo lan sang
  thì chuyển sang `_chay_co_han`.
