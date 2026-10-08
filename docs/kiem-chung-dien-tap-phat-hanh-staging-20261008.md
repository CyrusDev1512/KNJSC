# 08.10.2026 — Diễn tập phát hành Staging `450b6da` lên VPS (đang chạy `c7065fe`)

## Mốc và kết luận

- **VPS:** `main c7065fe` (biên bản phát hành 29.09), image `knjsc-app:c7065fe-adr046`. Không có lượt phát hành nào sau
  đó; `main a73f743` chưa lên VPS.
- **Đích diễn tập:** `Staging 450b6da`, tree `415f46271828fe4d002180f7ced57c9e346c32c6`; hơn VPS 122 commit, 258 tệp. Phiên KN
  CRM sẽ gộp Staging → main → VPS. Main có thêm commit gộp nên SHA đổi: trước khi phát hành phải so tree của main với
  tree trên. Tree khác thì diff phần chênh.
- **Kết luận: phát hành được, kèm điều kiện.** Đổi dãy lệnh theo mục "Dãy phát hành đề xuất". Dãy README hiện tại và
  cách quay lui 29.09 đều có lỗi đã tái hiện được (D1–D4). Hai lỗi mã (D5, D6) đã sửa trong nhánh
  `claude/dien-tap-phat-hanh-vps`. Không gộp nhánh đó thì VPS vẫn chạy được, nhưng:
  - ô chữ NFD (nếu có) không sửa được trên lưới;
  - `kiem_tra_du_lieu` hỏng nếu `migrate` dừng giữa chừng.

## Môi trường và chỗ lệch so với VPS thật

| Mục | Diễn tập | VPS |
|---|---|---|
| Máy | Máy ảo 4 lõi; mọi container ghim 2 lõi (`cpuset 0-1`) | 2 lõi, 4 GB |
| RAM container | crm 640, erp 512, worker 384, heavy 512, beat 192 MiB (theo biên bản 15.09, 17.09). db 1 GiB `shared_buffers=512MB`, broker và cache 256 MiB là **giả định** | `compose.vps.yml` thật, không có trong kho |
| Compose, nginx | `deploy/production/compose.yml` và `nginx.conf.template` y nguyên trong kho, cộng một `compose.vps.yml` tự viết | Như kho + `compose.vps.yml` |
| Tên miền | nginx thật ở cổng 443, chứng chỉ tự ký, `erp.knjsc.test`/`crm.knjsc.test`, cookie domain chung, tên cookie riêng, có `OPERATOR_EMAILS` | Tên miền thật |
| Image | Dựng từ `deploy/Dockerfile`, **bỏ dòng `apt-get`** vì proxy máy ảo chặn kho Debian. `python:3.12-slim` (Debian 13) đã có tzdata; libpq có sẵn trong `psycopg[binary]`. Image không có `pg_dump`, nên `sao_luu` đêm không chạy được ở đây | Đủ gói |
| Dữ liệu S0 | Ghi bằng service của bản `c7065fe`: 15 tài khoản 8 vai; 25 vận đơn sống + 3 xoá mềm, 18 dòng thiếu mã hoặc tên khách; 4 đơn (2 mồ côi); 14 báo cáo (2 rút); 3 lần sửa ô qua lưới cũ (biên nhận, lịch sử); chuỗi đánh dấu trong ô để dò log. 47 DataRecord, 51 bảng, dump 316.800 byte | 42 DataRecord, 51 bảng, dump 379.253 byte. Vận đơn 38 cột (diễn tập 44: số sản phẩm khác); MKT 19, Sale 11 (diễn tập 16, 9) |

Trình duyệt duy nhất có trong máy ảo là Chromium. Không có Safari, Firefox, Windows, dữ liệu thật hay VPS thật.

## Kết quả từng bước

### 1. Kiểm tĩnh và cấu hình

| Kiểm | Kết quả |
|---|---|
| `makemigrations --check --dry-run` | No changes |
| `migrate --plan` từ schema VPS | Đúng ba migration, theo thứ tự `core.0007` → `forms_builder.0017` → `reports.0006` |
| `check --deploy --fail-level WARNING`, image mới, crm và erp | Thoát 0 |
| Thiếu `SESSION_COOKIE_DOMAIN`, hoặc thiếu `CSRF_COOKIE_DOMAIN` | `core.E001`, thoát 1. Bản cũ với cùng cấu hình thì thoát 0, nên đây là chốt chặn mới |
| crm không có `BANGTINH_GOC` | `ImproperlyConfigured`, container không khởi động được |
| crm có `BANGTINH_GOC=production` (gõ sai) | Chỉ ra cảnh báo W018. **`check --deploy` thường thoát 0** trong khi `DEBUG=True` và `SESSION_COOKIE_SECURE=False`; chỉ `--fail-level WARNING` chặn được (D9) |
| `schedule_resync` mất `@writing` | Không ảnh hưởng phát hành: `resync_table` vẫn khoá bảng theo từng lô |

### 2. Phát hành V1 theo đúng README (container cũ phục vụ tới `up -d`)

- **Thời gian:** mọi bước thoát 0, cả lượt 50 s, riêng `migrate` 3,6 s.
- **Backup:** phục hồi thử bằng `--exit-on-error`, số dòng 51 bảng khớp.
- **SQL kiểm trước:** 0 mã trùng, 0 ô chữ NFD, 0 việc nền đang chạy.
- **collectstatic:** chép 136 tệp, bỏ qua 22 (phần lớn số chép là static admin của Django 5.2.17). So hash: 31/31 tệp
  nginx phục vụ khớp với image. Hai tệp JS mới trả 200; cache 1 giờ.
- **Probe:** 3.100 lượt đọc, cả ẩn danh lẫn có phiên, qua hai tên miền. Chỉ 5 lỗi, cùng nằm trong 11 s quanh `up -d`:
  4 lỗi 502, và 1 yêu cầu treo 10 s (đúng thời gian Docker chờ dừng container cũ).
- **Khoá:** trong lúc `migrate`, có 1 phiên chờ khoá 0,11 s.
- **Sức khoẻ container:** RestartCount 0, OOMKilled false.
- **Đối chiếu từng dòng:** chỉ 13 dòng MKT đổi (nhãn tiền VND, kể cả 2 dòng đã rút). 0 dòng vận đơn đổi `data`. Thêm bảng
  `submission_receipt` và 2 bản ghi `crm_gridchange` (trigger của UPDATE trong 0017).
- **DB bị tạo lại:** `up -d crm erp worker heavy beat proxy` theo README đã tạo lại container `db`. Lý do: `.env` đổi
  `KNJSC_IMAGE`, mà `db` đọc cùng `env_file`. DB tắt 3 s (tắt sạch). Biên bản 29.09 cũng ghi "Compose cũng tái tạo DB" (D3).

### 3. Cửa sổ code cũ chạy trên schema mới (từ `migrate` tới `up -d`)

| Thao tác bằng code cũ | Kết quả |
|---|---|
| Tạo dòng có mã `VPS-0019`, trùng một dòng đang sống | Tạo được: khoá mã đơn của dòng mới để rỗng nên lọt ràng buộc |
| Đổi mã `VPS-0020` → `VPS-0020-DOI` | Đổi được, nhưng khoá cũ `VPS-0020` vẫn nằm lại |
| Nộp báo cáo MKT, chọn Canada | Lưu `CAD`, trái ADR-047. Không lệnh nào gắn lại VND |
| Nộp MKT sau khi `configure_erp_reports` mới đã chạy | Hỏng: "Hãy chọn thị trường trong danh mục quốc gia." |
| Sửa ô từ tab lưới cũ | Lưu được (200) |

Sau khi chuyển image:
- `kiem_tra_du_lieu` báo: trùng mã `VPS-0019`, 2 dòng lệch khoá, 3 đơn mồ côi.
- `--sua` văng traceback `BusinessError` và không sửa được gì.
- Admin đổi mã dòng trùng xong thì `--sua` sửa hết khoá lệch. Chỉ còn đơn mồ côi.
- Biến thể B (mục 9) bỏ hẳn được cửa sổ này.

### 4. Trình duyệt mở từ bản cũ, nói chuyện với server mới

| Ca | Kết quả |
|---|---|
| Tab lưới cũ sửa ô | 200, DB đổi và có dòng lịch sử. Trong 40 s không tự tải lại, 0 lỗi JS |
| Form MKT cũ: còn 4 ô đã bỏ, không có khoá lần nộp | Tạo đúng 1 bản ghi, tiền VND |
| Form Sale cũ: còn ô Ngày ra đơn | Tạo 1 bản ghi (USD theo thị trường) |
| Bấm Nộp lần hai trên form cũ | Ra bản ghi thứ hai. Form mở trước phát hành không có khoá lần nộp, nên hành vi giống bản cũ (D13) |
| Trang báo cáo cũ bấm Gộp | Trang tải lại sang giao diện mới (có ⋯), 0 lỗi JS |
| Đăng xuất rồi đăng nhập lại ở ERP (CSRF xoay), sau đó tab CRM cũ lưu ô | 403, lưới hiện "Lỗi lưu", DB không đổi. Không có "Đã lưu" giả |

### 5. Chức năng bản mới qua nginx HTTPS hai tên miền

- **Ma trận quyền:** 8 vai × 8 đường dẫn chung × 2 host = 128 ô, sai 0. Mong đợi lấy từ
  `core/tests/test_ma_tran_quyen_hai_dich_vu.py`; có 74 dòng nhật ký từ chối.
- **Ghi lưới CRM, 13/13 đạt:**
  - hai người sửa cùng ô thì người sau bị 409, ô giữ giá trị của người lưu trước;
  - gửi lại đúng biên nhận không ghi lần hai; cùng mã thao tác mà khác nội dung thì 409;
  - đổi sang mã đơn đã có: 400 với lời tiếng Việt;
  - xoá dòng: Manager Vận đơn bị 403 và có nhật ký; Admin xoá rồi khôi phục được;
  - Sale (người tạo đơn) bấm Bỏ đơn bị chặn, chuyển về `/thu-muc/` — trang này 404 với Sale (D17);
  - `moi-nhat/`, `bo-loc/?panel=1`, `?cua_toi=1` đều 200 với ba vai;
  - xuất Excel ghi ô `=1+1` dạng chữ.
- **ERP:**
  - menu ⋯ đủ 6 mục; Gộp đổi tại chỗ; Xuất Excel tải được;
  - nộp MKT bấm đúp chỉ ra 1 bản ghi, tiền VND;
  - trang 404 tiếng Việt ở cả hai host.
- **Mở rộng mặc định (R10):**
  - máy chưa từng chọn, hoặc đã chọn "1": vào thẳng giao diện mở rộng;
  - máy đã chọn "0" ở bản cũ (kể cả vì từng bấm Escape): vẫn giao diện cũ (D14).

### 6. Diễn tập sự cố

| Sự cố | Kết quả |
|---|---|
| `stop cache` | Lưới và panel Bộ lọc vẫn 200; trung vị 35 → 50 ms |
| `pause cache` (Redis treo) | Vẫn 200; trung vị 35 → 548 ms, tối đa 674 ms (D16) |
| `stop broker`, rồi xác nhận nhập Excel | Báo lỗi hàng đợi tiếng Việt sau 0,69 s |
| `restart db` | 20/20 yêu cầu sau khi DB healthy đều đạt |

### 7. Quay lui về `c7065fe`, rồi tiến lại

**Cách của biên bản 29.09** (đổi image, `collectstatic` bằng image cũ, `up -d`) **không quay lui được giao diện (D1).**
- `collectstatic` chép 0 tệp, vì so theo giờ sửa tệp. Kết quả là 7/29 tệp static vẫn bản mới: `master-grid.js`,
  `report-filters.js`, `solarpunk-shell.js`, `waybill.js`, `report-entry.js`, `master-grid.css`, `solarpunk.css`.
- Lưới và báo cáo vẫn mở được. Nhưng mở panel Bộ lọc thì JS mới gọi một đường dẫn server cũ không có (404), rồi văng
  lỗi "Cannot set properties of null".
- Nộp MKT bằng code cũ hỏng vì form đã bị `configure` mới bỏ 4 ô (D4).
- DB lại bị tạo lại (D3).

**Cách đã sửa** đạt hết. Các bước:
1. Dừng các app.
2. Dùng image cũ chạy `configure_erp_reports`, `configure_delivery_daily_report`, `collectstatic --clear`.
3. `up -d --no-deps`, reload nginx.

Kết quả:
- static lệch 0;
- lưới, panel Bộ lọc, báo cáo 0 lỗi JS;
- nộp MKT bằng code cũ chạy, lưu `CAD` theo luật cũ.

Hệ quả phụ: vòng `configure` mới → cũ tạo lại các ô MKT với mã khác (`san_pham` → `erp_2_san_pham`…) và để lại 7 FieldDef
không còn dùng.

**Tiến lại sau quay lui:**
- `collectstatic` thường chép đúng 2 tệp hoàn toàn mới; 7 tệp đã sửa vẫn là bản cũ. Chạy với `--clear` thì lệch 0.
- Sau cả vòng, bảng MKT lẫn 2 dòng `CAD` giữa 14 dòng VND. Đó là các báo cáo code cũ nhận trong cửa sổ phát hành và lúc
  quay lui.

### 8. Dữ liệu xấu (mỗi biến thể một DB, tạo từ S0)

**V2: hai dòng sống trùng mã**
- `migrate` thoát 1 với lời "VPS-0019 (2 dòng)". Khi đó `core.0007` đã áp, `0017` và `0006` chưa, chưa có cột khoá.
- Code cũ vẫn ghi được. Sửa trùng bằng code cũ (Admin) xong, `migrate` lại thì đạt, và các lệnh `configure` đều chạy được.
- Chạy `kiem_tra_du_lieu` ngay sau khi migrate dừng (như lời báo hướng dẫn): `ProgrammingError: column val_order_code does
  not exist` (D6, **đã sửa**).

**Vpass: dòng sống trùng mã với dòng xoá mềm, mã chỉ khác NBSP, ô chữ NFD**
- SQL kiểm trước câu 2 (cách so như Python) bắt được cặp `VPS-T` / `VPS-T`+NBSP; câu 1 (đúng biểu thức của 0017) không bắt.
  `migrate` đạt.
- Khôi phục dòng xoá có mã trùng: lỗi tiếng Việt, dòng vẫn ở trạng thái xoá (đúng thiết kế).
- Dòng có mã kèm NBSP: sửa bất kỳ ô nào cũng báo "Mã đơn VPS-T đã có ở một dòng khác". Dòng đó không sửa được cho tới khi
  đổi mã, và `--sua` văng traceback (D10, D11).
- Ô chữ NFD: sửa đúng ô đó thì lần nào cũng 409 (D5, **đã sửa**). Sửa ô khác của cùng dòng thì 200.

### 9. Biến thể B: dừng các dịch vụ ghi trước migrate

- **Gián đoạn:** khoảng 17–21 s, tính từ lúc dừng app tới khi sẵn sàng. DB không bị tạo lại nhờ `--no-deps`. Cửa sổ ở
  mục 3 không còn.
- **Có một giao dịch đọc đang mở, kèm `PGOPTIONS='-c lock_timeout=10s'`:** 0017 dừng sạch sau khoảng 10 s ("canceling statement
  due to lock timeout"); 0007 đã áp; chạy lại được ngay.
- **Không có `lock_timeout`:** migrate đứng chờ, và một truy vấn đọc mới bị chặn 14,2 s, tức cả app đứng theo.

### 10. Hiệu năng trên 2 lõi, 100.047 dòng (dữ liệu nạp bằng bản cũ)

Kịch bản: 10 người dùng Vận đơn, 3 phút, qua nginx HTTPS (đọc khối lưới, hỏi mới, sửa ô). 0 lỗi ở cả hai bản.

| p95 | c7065fe | 450b6da |
|---|---|---|
| Đọc khối lưới `du-lieu/` | 310 ms | 210 ms |
| Lưu ô `luu-json/` | 220 ms | 100 ms |
| Mở trang lưới | 2.400 ms | 55 ms |
| Hỏi mới `moi-nhat/` | 120 ms | 33 ms |
| 20 người đăng nhập cùng lúc (trung vị / chậm nhất) | 3,72 / 5,86 s | 3,76 / 6,43 s |
| RAM đỉnh crm / db | 232 / 439 MiB | 233 / 528 MiB |

- **migrate ở 100k:** 46,7 s. Bảng phình 174 → 309 MB với 100.074 dòng chết, nên với bảng lớn phải `VACUUM`, không chỉ
  `ANALYZE`. Trên VPS hiện chỉ 28 dòng.
- **`kiem_tra_du_lieu` chạy bằng `exec` trong container crm:** bị diệt vì hết RAM (thoát 137) và container `crm` bị gắn cờ
  OOMKilled; gunicorn không chết. Chạy trong container riêng thì cần khoảng 410 MiB (D8).
- **Xuất Excel 100k dòng:** bị từ chối có chủ ý, với lời "vượt giới hạn xuất 50.000 dòng".

### 11. Bảo mật và log

- **Header:** HSTS 1 năm có `includeSubDomains` và `preload`; X-Frame-Options DENY; nosniff; Referrer-Policy same-origin;
  COOP. Header `Server: nginx/1.30.5` lộ phiên bản (D18).
- **Cookie:** phiên là Secure, HttpOnly, SameSite=Lax, hết khi đóng trình duyệt; CSRF là Secure, Lax; domain `.knjsc.test`.
- **Chuyển hướng và chặn:** HTTP chuyển 301 sang HTTPS. Host là một IP thì 400. Staff mở `/quan-tri/` thì bị chuyển sang trang
  đăng nhập quản trị.
- **`OPERATOR_EMAILS`:** đặt mà chưa có máy gửi thư thì mỗi lần Host sai, Django in một "thư" khoảng 400 dòng vào log
  `erp`. Cookie không lộ vì Django tự che (D12).
- **Dò log:** chuỗi đánh dấu (nội dung ô) xuất hiện **1 lần trong log Postgres**, trong câu `UPDATE` đầy đủ khi vi phạm
  `record_ma_don_unique`. Django gửi giá trị nằm luôn trong câu lệnh, nên `log_parameter_max_length_on_error=0` không che
  được (D7). Mật khẩu mẫu: 0 lần. Log ứng dụng: 0 traceback; ERROR chỉ có DisallowedHost cố ý.

## Lỗi tìm được

| # | Mức | Lỗi | Xử lý |
|---|---|---|---|
| D1 | Cao | Quay lui theo cách 29.09 giữ static bản mới, panel Bộ lọc văng lỗi JS | `collectstatic --clear` ở cả phát hành, quay lui và tiến lại |
| D2 | Cao | Cửa sổ code cũ trên schema mới: trùng mã lọt ràng buộc, báo cáo MKT lưu CAD, nộp MKT hỏng | Biến thể B: dừng các dịch vụ ghi trước `migrate` |
| D3 | Vừa | `up -d` theo README tạo lại DB khi `.env` đổi | `up -d --no-deps crm erp worker heavy beat` |
| D4 | Vừa | Quay lui thiếu `configure` của bản cũ, nộp MKT hỏng | Viết lại quy trình quay lui (dưới) |
| D5 | Vừa | Ô lưu chữ NFD (gõ trên Mac) bị 409 ở mọi lần sửa | **Đã sửa:** `record_service.same_value` so ở dạng NFC, dùng ở lưu ô và bỏ chi tiết |
| D6 | Vừa | `kiem_tra_du_lieu` hỏng khi `0017` chưa áp, đúng lúc lời báo của 0017 chỉ tới nó | **Đã sửa:** bỏ qua phép rà cột tách (ghi rõ), vẫn liệt kê mã trùng; `--sua` không ghi gì |
| D7 | Vừa | Vi phạm ràng buộc mã đơn thì Postgres ghi nguyên câu `UPDATE` có dữ liệu khách vào log (quy tắc 6) | Thêm `-c log_min_error_statement=panic` vào lệnh `db`, ở chỗ VPS đang đặt lệnh đó |
| D8 | Vừa | `kiem_tra_du_lieu` chạy bằng `exec` trong crm có thể hết RAM khi bảng lớn | Dùng `docker compose run --rm`; đọc theo lô để sau (backlog) |
| D9 | Vừa | `check --deploy` thường không chặn `BANGTINH_GOC` gõ sai (DEBUG bật) | Luôn chạy `--fail-level WARNING` trên crm và erp |
| D10 | Nhẹ | `--sua` văng traceback khi còn mã trùng, không sửa phần nào | Đọc kết quả, sửa trùng trên lưới trước rồi mới `--sua` |
| D11 | Nhẹ | Mã chỉ khác NBSP hay tab vẫn qua migrate, nhưng dòng đó không sửa được | SQL kiểm trước câu 2 bắt được; đổi mã trên lưới |
| D12 | Nhẹ | `OPERATOR_EMAILS` khi chưa có máy gửi thư làm log phình | Chỉ đặt khi có `EMAIL_BACKEND` thật |
| D13 | Nhẹ | Form mở trước phát hành bấm Nộp hai lần ra 2 bản ghi | Nhắc người dùng tải lại form sau phát hành |
| D14 | Nhẹ | Máy từng thoát mở rộng (kể cả bấm Escape) giữ giao diện cũ | Chủ dự án quyết có đặt lại hay không |
| D15 | Nhẹ | 20 người đăng nhập cùng lúc chờ tới khoảng 6 s (PBKDF2, 2 lõi), không đổi so với bản cũ | Đã có trong backlog (Argon2 chờ chủ dự án) |
| D16 | Nhẹ | Redis cache treo thì mỗi lượt đọc chậm thêm khoảng 0,5 s | Theo dõi container `cache` |
| D17 | Nhẹ | Sale bị chặn Bỏ đơn thì chuyển về `/thu-muc/`, trang đó 404 với Sale | Backlog |
| D18 | Thông tin | nginx lộ phiên bản; FieldDef thừa sau vòng `configure` | Chờ quyết định `server_tokens off` |

## Dãy phát hành đề xuất

Chạy ở `/opt/knjsc-runtime`, mọi lệnh đều với `docker compose -f compose.yml -f compose.vps.yml`.

**0. Chỉ đọc, trước khi làm gì.** Chỉ in số đếm, không in giá trị.
- tree của main bằng `415f4627…`;
- `.env` có `SESSION_COOKIE_DOMAIN`, `CSRF_COOKIE_DOMAIN`, `BANGTINH_URL`/`MAIN_APP_URL` dạng https; có `OPERATOR_EMAILS` thì
  phải có cả `EMAIL_BACKEND`;
- việc nền đang chờ hoặc chạy = 0; `df -h`, `free -m`;
- bốn câu SQL ở cuối biên bản.

**1–3. Chuẩn bị**
1. Backup và phục hồi thử, như biên bản 29.09.
2. Build image; chạy `check --deploy --fail-level WARNING` trên **crm và erp** bằng image mới.
3. `stop crm erp worker heavy beat`: gián đoạn bắt đầu, khoảng 20 s ở cỡ dữ liệu VPS.

**4. Migrate**
- Chạy `run --rm --no-deps -e PGOPTIONS='-c lock_timeout=10s' crm python manage.py migrate --noinput`.
- Thoát khác 0 thì **dừng, không đổi image**:
  - do mã trùng: chạy `kiem_tra_du_lieu` (cần bản sửa D6) hoặc câu SQL 1;
  - bật lại bản cũ, sửa mã trên lưới, rồi chạy lại.
- Do khoá thì chạy lại.

**5–7. Cấu hình và chuyển image**
5. Dùng image mới, `--no-deps`, chạy `tao_bang_van_don`, `configure_erp_reports`, `configure_delivery_daily_report`.
6. `collectstatic --noinput --clear` bằng image mới.
7. Đổi `KNJSC_IMAGE` trong `.env` → `up -d --no-deps crm erp worker heavy beat` → `exec proxy nginx -t`, rồi
   `nginx -s reload` ngay.

**8. Sau khi chuyển**
- kiểm RestartCount và OOMKilled;
- `run --rm crm python manage.py kiem_tra_du_lieu --bang van_don`: đọc từng dòng; 2 đơn mồ côi là đã biết;
- `VACUUM ANALYZE forms_builder_datarecord`;
- so hash `master-grid.js`, `report-filters.js`, `phan-trang.js` trên domain thật với tệp trong image;
- gom p95.

Kèm theo:
- thêm `-c log_min_error_statement=panic` vào lệnh `db` (D7);
- nhắc người dùng tải lại các trang đang mở (D13).

**Quay lui**
1. `stop crm erp worker heavy beat`.
2. Dùng image cũ chạy `configure_erp_reports`, `configure_delivery_daily_report`, `collectstatic --noinput --clear`.
3. Đổi `.env` về image cũ, `up -d --no-deps crm erp worker heavy beat`, reload nginx.
4. **Không đảo migration nào.** Đảo `0006` làm mất dữ liệu; để nguyên `0017` thì code cũ chỉ ghi khoá rỗng.
5. Trước khi tiến lại: `kiem_tra_du_lieu`, sửa trùng trên lưới, rồi `--sua`. Báo cáo MKT nộp trong lúc quay lui mang tiền
   theo thị trường; chủ dự án quyết có gắn lại VND không.

**Câu SQL kiểm trước:** cùng câu đã dùng trong diễn tập.
1. Trùng mã, đúng biểu thức của 0017: `left(btrim(coalesce(data->>'ma_don','')),200)`, dòng sống, bảng `van_don` hoặc
   `workflow='waybill'`, `GROUP BY table_id, mã HAVING count(*)>1`.
2. Trùng mã theo cách so của Python: bỏ mọi khoảng trắng Unicode ở hai đầu (`\s`, NBSP, ` - `, `　`…).
3. Số mã có khoảng trắng ở đầu/cuối, hoặc không phải chuỗi.
4. Số dòng có chữ NFD: `NOT (data::text IS NFC NORMALIZED)`.

## Chưa kiểm được

- VPS thật: CPU, đĩa, mạng, `compose.vps.yml`, chứng chỉ; dữ liệu thật (bao nhiêu mã trùng, ô NFD, tiền MKT gốc).
- Safari, Firefox, Windows, bộ gõ thật.
- Nhập Excel ở các ca biên (500 ô một hàng, tệp 12 MB gặp `client_max_body_size 11m`); diệt một việc xuất đang chạy giữa
  chừng.
- 300.000 dòng: diễn tập chỉ đo 100k. Staging đã đo 385k ở `kiem-chung-mo-luoi-lan-dau-20261008.md`.
- Bản sao lưu đêm `sao_luu` (image diễn tập không có `pg_dump`).
- Phát hành từ main: SHA sẽ khác, cần so tree như mục 0.

## Lệnh và công cụ

Mọi script nằm ở scratchpad của phiên, không đưa vào kho:
- `dc`: compose với hai tệp;
- `buoc`: chạy một bước, ghi giờ, mã thoát và đầu ra;
- `snap` / `manifest-diff`: số dòng từng bảng, id + md5 của từng DataRecord, danh sách migration;
- `static-hash`: so tệp trong image với bytes nginx phục vụ;
- `probe.py`: 5 lượt/giây, ghi CSV;
- `pglocks`: phiên chờ khoá, mỗi 0,2 s;
- `chay-db`: chạy lệnh Django của một image trên DB bất kỳ;
- `r19.py`: code cũ ghi trong cửa sổ;
- Playwright nối CDP vào một Chromium sống suốt lượt;
- locust Vận đơn.

Pytest của phần sửa: `crm/tests`, `orders/tests`, `forms_builder/tests`, `tests/test_truy_vet.py` cho 752 đạt, 7 bỏ qua.
Hai bài mới chạy đỏ trên `450b6da` trước khi sửa.
