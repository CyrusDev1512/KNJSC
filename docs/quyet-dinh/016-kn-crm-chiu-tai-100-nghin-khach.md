# ADR-016 — KN CRM chịu được 100 nghìn khách và 100 người cùng lúc: đo trước, sửa đúng chỗ đo được

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã chốt |
| Ngày | 07.09.2026 |
| Liên quan | ADR-001 (cột tách), ADR-006 (cột tính sẵn), ADR-011 (lưới như KN Demo), NFR-1, NFR-2, AC-10.8, AC-11.35, AC-11.36, backlog K27 |

## Bối cảnh

Anh/chị yêu cầu kiểm thử KN CRM ở cỡ **hàng triệu ô, 100 nghìn khách**, rồi mô phỏng
**100 người làm việc cùng lúc** — "di qua di lại" (mở, lọc, chuyển trang, sắp xếp,
sửa ô) và "lập công thức" (cột tính sẵn, vì công thức từng ô S10 chưa có) — không
bấm giao diện bằng Playwright mà gọi thẳng HTTP như trình duyệt. Ngưỡng chốt là
**"như Excel trên máy thường"**: 95% lượt mở/lọc/chuyển trang dưới 1 giây, lưu ô
dưới 0,5 giây, không lỗi, tính lại cột tính sẵn 100 nghìn dòng dưới 30 giây và
không chặn người khác.

Trước đó hệ thống chỉ có bài 50.000 dòng (AC-7.1, xfail K24) và Locust 50 người
(AC-10.1) trên `runserver`. Chưa ai đo ở cỡ này.

## Đã đo được gì (máy ảo 4 nhân, PostgreSQL 16 mặc định, gunicorn 3 worker)

Dữ liệu: 100.010 dòng vận đơn × 30 cột = **2,95 triệu ô**, 85.954 số điện thoại
khác nhau, 209 MB; bảng Sale 20.000 dòng có cột tính sẵn. Đo **một người, không tải**
(`manage.py do_hieu_nang`) rồi **100 người 5 phút** (`tests/perf/locustfile_kn_crm.py`).

| Đường | Trước | Sau | Vì sao |
|---|--:|--:|---|
| Lưới 100 dòng × 39 cột | 638 ms (DB 58 ms) | 154 ms | 95% là **vẽ template**: 3.900 `{% include %}` + 7.800 `{% url %}` |
| Lưới trang 500 | 846 ms | 280 ms | subquery đếm trùng chạy cho 50.000 dòng trước khi cắt trang |
| Chỉ dòng trùng `?trung=1` | 1.089 ms | 478 ms | subquery tương quan 100.000 lần + JIT 228 ms |
| Dán 500 ô | 1.670 ms, 1.013 lệnh | 207 ms, 13 lệnh | mỗi dòng một `save()` |
| Tính lại cột tính sẵn 20.000 dòng | 29,5 s | 4,2 s | mỗi dòng một `save()`; `bulk_update` của Django cũng 26 s vì ghép `CASE WHEN` với JSON 3 KB |
| Tính lại 100.000 dòng | 153 s **trong request** | 19,6 s **ở tác vụ nền**, 2 lô song song (28 s một luồng) | như trên, và chặn worker web; phần còn lại là Postgres ghi lại chỉ mục GIN của JSON cho từng dòng (đọc + tính chỉ 6 s), không tránh được khi giữ GIN |
| `moi-nhat/` | 65 ms, quét cả bảng | 72 ms, dùng chỉ mục | `COUNT(*)` toàn bảng × 100 tab × mỗi 8 giây |
| 100 người 5 phút (22,8 yêu cầu/giây) | p95 đọc 11,4 s, ghi 11 s, hỏi 11,2 s, 14 lỗi | **ĐẠT**: p95 đọc 853 ms, ghi 371 ms, `moi-nhat/` 143 ms, 0 lỗi; tính lại 100.000 dòng 24,4–24,8 s trong lúc p95 người khác 900 ms | ba worker đồng bộ xếp hàng sau các lượt vẽ lưới 600 ms; sau khi sửa còn đuôi p99 ~3 s lúc xuất Excel và tính lại trùng nhau |

## Quyết định

1. **Ô của lưới dựng bằng Python** (`grid_service.cell_html`), không `{% include %}`
   từng ô. Đây là nơi duy nhất quyết định ô trông thế nào — dùng cả khi vẽ lưới,
   khi HTMX trả về sau lưu, huỷ sửa, đổi định dạng (`templates/crm/_o.html` bỏ).
   URL sửa ô ghép chuỗi trên gốc lưới (`cell_url`), khớp `reverse()` bằng bài kiểm.
2. **Cột Trùng đếm theo trang** (`attach_duplicate_counts`, một GROUP BY trên các
   số điện thoại của trang) thay vì annotate subquery cho cả queryset; `?trung=1`
   lọc bằng `val_phone IN (số điện thoại xuất hiện > 1 lần)`. Chỉ mục mới
   `(table, val_phone)`.
3. **`moi-nhat/` không đếm dòng**: chỉ `Max(updated_at)` **theo cả bảng** trên
   `all_objects` (dòng xoá mềm vẫn mang mốc xoá nên xoá cũng đổi mốc) + số cột +
   tiến độ tính lại. Không lọc theo phạm vi từng người: `_bang()` đã kiểm quyền xem
   bảng, mốc chỉ nói "có gì đổi" không lộ dữ liệu, còn JOIN phạm vi cản chỉ mục và
   thành quét cả bảng 78 ms. Chỉ mục mới `(table, updated_at)` → Index Only Scan
   0,1 ms.
4. **Ghi hàng loạt bằng `DataRecord.bulk_save`** — một lệnh `UPDATE … FROM (VALUES …)`
   cho mỗi 1.000 dòng, tham số qua `get_db_prep_save`, ép kiểu theo `db_type`.
   Đây là chỗ **duy nhất** ghi SQL tay cho bản ghi. Dùng cho dán/kéo điền/hoàn tác
   (`update_cells`), định dạng (`update_styles`) và tính lại cột (`resync_table`).
5. **Tính lại cột chạy nền trên bảng lớn** (`table_service.schedule_resync`): bảng
   tới `RECOMPUTE_SYNC_MAX_ROWS` (2.000) dòng thì tính ngay tại chỗ; hơn thì tạo
   `BackgroundJob` loại **Tính lại cột** (`JobKind.RECOMPUTE`), worker Celery làm theo
   lô 1.000 dòng có `select_for_update`, báo tiến độ. Cột hiện ngay; màn Sửa cột nói
   rõ có tác vụ nền; lưới báo "Đang tính lại cột… n%" qua `moi-nhat/` và **nạp lại
   một lần khi xong** (không để 100 tab cùng tải lại mỗi 8 giây trong lúc tính).
   Người sửa ô trong lúc đó không mất dữ liệu: `save()` của họ tính đủ cột tính sẵn
   trong bộ nhớ và chờ lô đang khoá ghi xong. Hai bên khoá dòng **cùng chiều khoá
   chính** (`bulk_save` sắp theo pk, worker `ORDER BY pk`); lỡ deadlock (gặp một lần
   khi đo) thì worker thử lại lô, còn `luu-o` làm lại giao dịch một lần — người dùng
   không thấy gì. Chỉ ghi dòng và cột thật sự đổi. Ở worker (ngoài giao dịch) chạy
   **2 lô song song** (`RECOMPUTE_THREADS`): phần nặng là Postgres ghi lại chỉ mục
   GIN của JSON, hai kết nối là hai nhân — 100.000 dòng 28 s → 19,6 s; trong giao
   dịch (bảng nhỏ, bài kiểm) vẫn tuần tự.
6. **Compose có chế độ gunicorn**: `KNJSC_LENH_WEB` đổi lệnh của `web` và `bangtinh`
   (mặc định vẫn `runserver` để sửa mã là thấy ngay). Đo tải phải trên gunicorn.
   Dockerfile chạy **3 tiến trình × 4 luồng** (`gthread`) thay vì 3 tiến trình đồng
   bộ: với worker đồng bộ, một lượt xuất Excel 1–7 s hay dán 500 ô chiếm trọn một
   tiến trình, ba lượt như thế cùng lúc là mọi yêu cầu ngắn (moi-nhat 15 ms) xếp
   hàng 7–8 s — đo được p99 7–8 s ở mọi đường; luồng cho yêu cầu ngắn chen vào.
7. **Ngưỡng ghi một chỗ** ở `core/constants.py` (`PERF_READ_P95_MS`, `PERF_WRITE_P95_MS`,
   `PERF_POLL_P95_MS`, `PERF_RECOMPUTE_SECONDS`, `PERF_LOAD_USERS`, `PERF_LOAD_ROWS`);
   `do_hieu_nang` và Locust cùng đọc từ đó.

## Đã cân nhắc và không làm

- **Đệm (cache) lưới hay hộp lọc bằng Redis**: chưa cần — sau khi bỏ vẽ template
  từng ô, lưới còn 130 ms mà phần DB chỉ ~60 ms; đệm thêm lớp phải vô hiệu hoá
  đúng lúc, sai là người này thấy dữ liệu cũ của người kia. Ghi backlog, chỉ làm
  khi máy thật đo đỏ.
- **`SESSION_ENGINE = cached_db`**: mỗi request bớt 1 SELECT ~1 ms; không đáng
  thêm một phụ thuộc vận hành. Ghi backlog.
- **Tăng số worker gunicorn hay chỉnh Postgres** (`shared_buffers`, `work_mem`):
  là việc của máy chủ thật (Giai đoạn 8), số đo ở đây ghi rõ cấu hình mặc định để
  so sánh sau.
- **Đổi `bulk_update` của Django bằng cách chia lô nhỏ hơn**: đã thử lô 50, vẫn
  1,1 giây/1.000 dòng — nút thắt là ghép `CASE WHEN`, không phải kích thước lô.
- **Bỏ chỉ mục GIN trên `data` để tính lại nhanh hơn**: GIN là thứ làm lọc theo
  khoá JSON dùng được (quy tắc 12); tính lại cột là việc hiếm, chậm thêm 20 giây
  ở nền chấp nhận được, lọc chậm hằng ngày thì không.
- **Chấm cả 20 giây đầu khi 100 người đăng nhập cùng lúc**: băm mật khẩu PBKDF2
  cố ý chậm (NFR-4), 100 người đăng nhập trong 10 giây là cảnh không có thật;
  Locust chạy với `--reset-stats`, chấm từ lúc mọi người đã vào.

## Hệ quả

- `docs/06` tầng 9 là kịch bản 100 người trên 100 nghìn khách; AC-10.8 (thủ công,
  chạy `scripts/kiem-tai-kn-crm.*`), AC-11.35 (tính lại nền), AC-11.36 (lưới không
  phình theo số ô) tự động.
- Hai tệp chuyển đổi: `core 0006` (loại tác vụ), `forms_builder 0009` (hai chỉ mục) —
  đảo ngược được.
- Khi có công thức từng ô (S10) thì đo lại kịch bản này với người dùng gõ công thức.
