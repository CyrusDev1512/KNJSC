# Kiểm chứng sửa trùng mã đơn đồng thời — 11.09.2026

Trạng thái: đạt nghiệm thu local cho lỗi cấp mã đơn đồng thời theo kịch bản
đã duyệt. Chưa commit/push/merge; không đóng các vấn đề hiệu năng toàn CRM.

## Phạm vi và nền đối chứng

- Nhánh `fix/trung-ma-don-dong-thoi`, worktree riêng, nền chính xác
  `a81decd1d0a641ace77ae5f4d4d4340b3ba3e180` của `CRM-Optimization`.
- Code ứng dụng chỉ sửa `app/orders/services/order_service.py`.
  Không migration, dependency, thay UI/quyền hoặc bật cờ tối ưu của môi trường dùng thật.
- Giữ `DH-DDMM-…`, hậu tố tối thiểu 4 chữ số; lấy max theo số,
  tính cả mã của đơn xóa mềm. Cùng ngày–tháng năm sau tiếp tục dãy cũ.
- Giữ nguyên giao dịch đơn, sản phẩm, bản sao Vận đơn và audit. Không giải quyết
  gửi trùng POST, phân công tự động hoặc các vấn đề truy vấn/render của lưới.

## Cách sửa và giới hạn vận hành

Service lấy `pg_advisory_xact_lock(namespace, DDMM)` trước lần ghi khách hàng
đầu tiên; namespace ổn định `0x4B4E4F52`, dùng chung giữa worker/process.
Database kiểm chứng xác nhận mức cô lập `read committed`.
Sau khi lấy khóa mới chạy truy vấn max hậu tố bằng câu SQL riêng.
Khóa giữ đến commit/rollback giao dịch ngoài cùng.

Chỉ thao tác lấy khóa dùng `lock_timeout=5s`. Savepoint giúp rollback trước
khi bắt SQLSTATE `55P03`; đổi thành `BusinessError` có mã `order_code_busy`.
Thông báo: “Hệ thống đang bận cấp mã đơn. Vui lòng thử lại.”
Khôi phục timeout cũ khi thành công hoặc rollback; không bắt chung các lỗi DB
khác, không retry POST, không bỏ ràng buộc unique.

Tham khảo: [PostgreSQL 16: advisory locks và set_config](https://www.postgresql.org/docs/16/functions-admin.html#FUNCTIONS-ADVISORY-LOCKS).
Khi triển khai cần cập nhật đồng bộ mọi process có thể tạo đơn;
phiên bản cũ chưa lấy khóa không được chạy lẫn phiên bản mới.

## Functional và E2E đã chạy

| Lượt | Kết quả |
|---|---|
| TDD trên bản cũ, hai test mới | 2 failed: trùng mã khi hai giao dịch chồng lấn; sai max sau `9999` |
| Hai test sau sửa | 2 passed |
| Hồi quy `orders/tests crm/tests` | 289 passed, 2 lỗi nền, 9 skipped; 107,33 giây |
| Đối chứng hai lỗi trên `a81decd` | Tái hiện cùng 2 lỗi, 1 passed |
| Focused cuối, bao gồm 30 Sale mỗi đơn hai sản phẩm | 9 passed; 22,09 giây |
| Chrome Sale/Admin, 1440px và 390px | 10 trường hợp đạt, 4 đơn hai sản phẩm được đối chiếu DB |
| Hai URLconf ERP/CRM | Không có lỗi system check |

Focused kiểm riêng kết nối từng thread; barrier đặt trước khi gọi service.
Bao gồm khách khác/cùng khách, đúng Sale, Decimal 40,40 USD, đủ hai chi tiết
và một dòng Vận đơn mỗi đơn; bảng rỗng, mã xóa mềm, `9999→10000→10001`,
ngày Việt Nam/đổi ngày/cùng DDMM khác năm và hậu tố cũ không hợp lệ.
Gây lỗi ở bước ghi Vận đơn để kiểm rollback, sau đó kết nối khác lấy khóa được.

Chrome thực hiện nộp đơn, kiểm thông báo/mã, mở đơn gốc, kiểm tài khoản ngoài
phạm vi nhận 404 và nhân viên Vận đơn không thấy đơn mới chưa phân công.
Hai trường hợp giữ khóa cho timeout trả lỗi sau 5.150/5.136 ms, giữ đầy đủ
form và sản phẩm; gửi lại sau giải phóng khóa thành công. Không có pageerror.
Ảnh desktop/mobile và dữ liệu đối chiếu nằm trong bằng chứng local.

Hai lỗi nền là `test_dich_vu_bangtinh_chi_co_bang_tinh_va_dang_nhap` và
`test_erp_chi_con_lien_ket_sang_kn_crm` trong `crm/tests/test_dich_vu_bangtinh.py`:
kỳ vọng chuỗi markup điều hướng không khớp. Không sửa ngoài phạm vi.
Các bài có marker/môi trường riêng bị skip không được tính đạt;
E2E của đợt này dùng Chrome riêng, không thay bằng test HTML.

## Môi trường và phương pháp đo

- Network `knjsc-code-test`; PostgreSQL 16, Redis và app/load container riêng.
  Không seed, migrate hoặc kiểm tải database đang sử dụng.
- Docker local: 12 CPU, 8.192.139.264 byte RAM (~7,63 GiB); không phải VPS 24 GB.
  Máy vẫn có các dịch vụ local khác nên không suy ra cam kết năng lực VPS.
- Gunicorn 3 worker × 4 thread, cùng image `knjsc-web`, cấu hình giữ nguyên trước/sau.
- 100.000 đơn/khách/dòng Vận đơn, 200.000 OrderLine và WaybillItem;
  30 Sale, 10 Vận đơn, mỗi Vận đơn được phân công 10.000 dòng.
  Ngày nghiệp vụ phân bố cả 2026; `Order.created_at` của fixture là lúc seed.
  Mã seed dạng `TEST-…`; đơn đo thực dùng service cấp `DH-DDMM-…`.
- Clone từ cùng database test gốc trước từng lượt chính; không dùng baseline
  cũ trên `vandonmoi` để tuyên bố cải thiện.
- Chín Vận đơn Locust cộng một Chrome thật; Sale nghỉ 20–40 giây giữa đơn.
  Vận đơn cuộn/lọc/tìm, sửa ghi chú, poll và kiểm phạm vi.
- Lượt chính cấu hình 362 giây, bỏ 60 giây làm nóng và yêu cầu thực đo ≥300 giây.
  Cờ READ/SYNC/RECEIPTS/RENDER/STATS/EXPORT/QUEUES tắt.
- Log riêng từng PID/thread. `lock_ms` là thời gian thực thi câu lấy khóa
  (gồm roundtrip PG), xấp xỉ thời gian chờ; SQL và request được ghi riêng.
  `edit-to-save` trên Chrome gồm debounce 500 ms, không dùng thay độ trễ server.
- Đối chiếu mã/actor/Decimal/chi tiết/Vận đơn với phản hồi lưu; ID ghi ô lấy
  từ phản hồi và đối chiếu DB/lịch sử. Lượt dừng trước warm-up ghi 0 giây đo.

## Kết quả hiệu năng

Ba lượt chính đều đủ thời lượng sau warm-up: trước sửa 301,49 giây,
sau sửa 301,50 giây, hỗn hợp 301,52 giây. Tổng request Locust trong cửa sổ
đo lần lượt 2.192 / 2.208 / 3.083, đều 0 lỗi. Các mẫu warm-up giữ riêng.

### HTTP — p95, mili giây

| Thao tác | Nền a81decd, 10 Vận đơn | Bản sửa, 10 Vận đơn | Bản sửa, 30 Sale + 10 Vận đơn |
|---|---:|---:|---:|
| Tạo đơn | — | — | **170,58** |
| Lấy khối dữ liệu | 147,12 | 154,14 | **156,13** |
| Tìm kiếm | 261,42 | 248,51 | **278,29** |
| Lọc trạng thái | 133,78 | 135,79 | **137,84** |
| Poll | 116,09 | 109,34 | **115,02** |
| Kiểm phạm vi | 45,34 | 45,62 | **46,90** |
| Lưu ô | 101,04 | 113,05 | **108,69** |

Trong lượt hỗn hợp, tạo đơn p50/p95/p99 = 101,98/170,58/218,53 ms;
297 mẫu sau warm-up, khoảng 0,98 đơn/giây theo nhịp nghỉ đã cấu hình.
SQL p95 104,84 ms, app p95 164,51 ms. Câu lấy khóa p50/p95/p99 =
0,11/13,34/59,18 ms. Không trừ các percentile này cho nhau để suy ra thành phần.
Số truy vấn trung vị: tạo đơn 73, lấy khối 12, lưu ô 19; chưa tối ưu các truy vấn đó.

Toàn lượt hỗn hợp gồm warm-up tạo **361/361 đơn** được xác nhận; đối chiếu DB
đủ mã duy nhất, đúng Sale, Decimal 40,40 USD, hai OrderLine, hai WaybillItem và
một dòng Vận đơn mỗi đơn. Không có đơn commit nhưng thiếu phản hồi thành công,
đơn lưu dở, sai phạm vi hoặc ô đã xác nhận bị mất. Kiểm 58 ô cuối/lịch sử của
mỗi lượt chính. Đơn mới vẫn chưa phân công và không lọt vào phạm vi Vận đơn.

### Đợt dồn 30 Sale

30 thread đồng bộ trước POST; cả **30/30 HTTP 200, 30 mã khác nhau**,
đối chiếu đầy đủ dữ liệu. Toàn đợt 1,53 giây; request p50/p95/p99 =
931,01/1.487,26/1.519,00 ms. Câu lấy khóa p95 **584,28 ms**, không timeout.
Đây là độ trễ đợt dồn, báo riêng theo kế hoạch; không trộn vào p95 lượt hỗn hợp.

### Chrome và tài nguyên

| Số đo | Nền 10 Vận đơn | Sau sửa 10 Vận đơn | Hỗn hợp 30 + 10 |
|---|---:|---:|---:|
| Cuộn đến lúc có nội dung, p95 ms | 805 | 334 | 819 |
| Chọn ô đến paint, p95 ms | 72 | 82 | 73 |
| Lọc đến nội dung, p95 ms | 330 | 328 | 343 |
| Kết thúc nhập đến xác nhận lưu, p95 ms (có debounce) | 654 | 655 | 687 |
| Render p95 ms | 14,5 | 13,2 | 15,2 |
| App CPU p95 (% một core) | 38,20 | 41,71 | 60,72 |
| PostgreSQL CPU p95 (% một core) | 124,32 | 140,50 | 147,18 |
| App RAM cuối lượt, MiB | 229,6 | 230,8 | 233,7 |
| PostgreSQL RAM cuối lượt, MiB | 328,8 | 644,6 | 600,4 |

Mỗi lượt có 83–85 mẫu cuộn và 43 mẫu tài nguyên sau warm-up. Không có
long task ≥50 ms hoặc lỗi Chrome trong cửa sổ đo. Lần mở Chrome đầu tiên
mất 2,061/2,555/2,171 giây đến lúc có ô, ghi riêng ngoài warm-up; không gọi
đây là thời gian HTTP. Chrome 390px bổ sung đạt 16 thao tác cuộn/chọn/lọc/
tự lưu; kiểm giá trị đã lưu trong DB và lịch sử, không pageerror.

Số cuộn trước/sau biến động; **không tuyên bố lưới nhanh hơn** từ lượt đo này.
PostgreSQL dùng chung container qua các lần clone DB test; chỉ ghi nhận RAM,
không kết luận rò rỉ hay cải thiện bộ nhớ. Đây không phải bài kiểm tải bền
hoặc mô phỏng toàn bộ 100 nhân sự dùng cả báo cáo ERP qua mạng VPS.

### Tương thích cờ tối ưu

Chỉ trong môi trường test, bật READ/SYNC/RECEIPTS/RENDER, giữ các cờ khác tắt.
Lượt ngắn 44,55 giây, 30 Sale + 9 Vận đơn Locust + 1 Chrome: **446 request,
43 đơn, 0 lỗi HTTP/SQL/Chrome hoặc đối chiếu dữ liệu**. Có đọc protocol 2,
41 request sync v2 và 40 lưu ô với receipt gọn. Đây là kiểm tương thích,
không thay lượt nghiệm thu đủ thời gian với cờ tắt.

Kết luận: đạt ngưỡng tạo đơn/API đọc p95 ≤1s, lưu ô ≤500ms ở lượt hỗn hợp;
đạt đủ 30 đơn ở đợt dồn, không timeout. Phần cấp mã được nghiệm thu local.

Một lượt hỗn hợp đầu bị dừng do lỗi harness: tên đơn vị “hộp” bị đọc bằng
locale Windows rồi ghi lại sai UTF-8. Các POST Sale trả 400 ở validation,
chưa vào cấp mã; không có đơn được tạo. Lượt này chỉ có 26,44 giây sau
warm-up, lưu riêng dưới tên `invalid-harness-mixed`, loại khỏi nghiệm thu.
Đã sửa mã hóa/literal và dừng ngay khi Sale bị từ chối ngoài dự kiến.
Smoke sau sửa harness: 1 Sale + 1 Vận đơn, 38 request/0 lỗi, một đơn đủ
hai sản phẩm/Vận đơn được đối chiếu; reset dữ liệu rồi đo lại toàn bộ lượt hỗn hợp.

## Tái chạy và bằng chứng

Harness và trình tự: [scripts/order-code-check](../scripts/order-code-check/README.md).
Số đo, p50/p95/p99, throughput, lỗi và tên bài skip:
[bằng chứng tổng hợp](kiem-chung-trung-ma-don-20260911.json).
Kết quả chi tiết local: `storage/order-code-verification/results/`;
không đưa env/session tạm vào Git. Hồi quy chạy bằng container test với
`RUN_MIGRATIONS=0`, mount app/docs/runtime và lệnh:

```text
pytest orders/tests crm/tests --tb=short --junitxml=/runtime/results/regression.xml
pytest orders/tests/test_order_code_concurrency.py --tb=short --junitxml=/runtime/results/functional-final.xml
```

Đã gỡ ba container test app/PostgreSQL/Redis, hai volume ẩn danh và network
riêng; xác nhận các volume/database test không còn. Đã xóa env/session tạm
và tín hiệu giữ khóa. Giữ số đo, XML, ảnh, harness và bản sao app baseline
trong storage local làm bằng chứng; không đưa bản sao app vào Git.
Không tác động container/database đang sử dụng. Chưa commit, push hoặc merge.
