# Nhật ký kiểm thử — lỗi cần sửa

Mỗi lỗi một dòng, mã `TL-xx`, không xoá dòng khi sửa xong mà đổi cột Trạng
thái. `backlog-kanban.md` tham chiếu mã ở đây để xếp việc; `backlog.md` (K28,
Q67) ghi bối cảnh.

Cách đọc các cột:

| Cột | Nghĩa |
|---|---|
| Mức | **S1** lộ quyền hoặc mất/sai dữ liệu âm thầm · **S2** người dùng gặp thường xuyên hoặc trang trắng · **S3** khó chịu, có đường vòng · **S4** kỹ thuật, người dùng không thấy |
| Ở đâu | Tệp và hàm/đường dẫn, tính từ `app/` |
| Blocker | Lỗi này **chặn** việc gì, hoặc **bị chặn bởi** việc gì |
| Ảnh hưởng | Hệ thống bị gì khi lỗi xảy ra |
| Nhánh | `main` (3ab19a5, đang chạy trên máy anh/chị) · `PR21` (`claude/kiem-tai-kn-crm`) · cả hai |
| Phát hiện | Ngày và cách: **video** anh/chị gửi, **rà mã** (đọc lại toàn bộ), **đo** (kiểm tải), **tái hiện** (Playwright trên máy ảo) |
| Trạng thái | Mới · Đang sửa · Đã sửa (PR) · Đã nghiệm thu |

Bài kiểm tự động toàn bộ đang **xanh** trên cả `main` lẫn PR21, nghĩa là không
lỗi nào dưới đây có bài kiểm; mỗi lỗi khi sửa phải kèm một bài kiểm chiều sai.

---

## Lỗi theo thứ tự nghiêm trọng

| Mã | Mức | Lỗi | Ở đâu | Tái hiện | Blocker | Ảnh hưởng hệ thống | Nhánh | Phát hiện | Trạng thái |
|---|---|---|---|---|---|---|---|---|---|
| TL-01 | S1 | Manager bộ phận khác **tự cấp quyền Sửa** cho mình hoặc team trên bảng chỉ được cấp Xem; thu hồi được cả quyền bộ phận chủ đã cấp | `forms_builder/views.py` `bang_cap_quyen`, `bang_thu_quyen` (gắn 8021 ở `knjsc/urls_bangtinh.py`): chỉ `assert_rank(MANAGER)` + `_lay_bang` qua `in_scope` (gồm bảng được cấp), không kiểm cùng bộ phận như `bang_cot` | Sale cấp Xem `don_sale` cho `mkt.manager`; `mkt.manager` mở `/bang/don_sale/cot/` → Cấp quyền cho chính mình, action Sửa → sửa/xoá dòng của Sale | Chặn nghiệm thu phân quyền `docs/07` §3 và AC-8.x | Lộ quyền ghi chéo bộ phận; nhật ký ghi như thao tác hợp lệ | cả hai | 07.09 rà mã | Mới |
| TL-02 | S1 | **Hết phiên 60 phút** rồi dán, kéo điền, xoá dòng, định dạng: máy chủ trả 302 → trang đăng nhập 200, JS coi là thành công → "✓ Đã lưu", ghi bước hoàn tác, xoá dòng khỏi màn hình, báo "Đã xoá N dòng" | `core/middleware.py` `SessionTimeoutMiddleware` (302, không `HX-Redirect`); `static/js/bang-tinh-o.js` luu-o `ok = 2xx`, `xoaHang` `status === 200`; poll `hoiMoiNhat` nuốt lỗi JSON | Mở lưới, để yên 61 phút, dán 500 ô | Chặn nghiệm thu `docs/07` §3.3; cùng gốc TL-18 | Mất dữ liệu người dùng vừa nhập, không một lời báo | cả hai | 07.09 rà mã (TL-18 từ ảnh 07.09) | Mới |
| TL-03 | S1 | **Số có ≥ 3 chữ số lẻ bị nhân nghìn**: `parse_money` coi dấu chấm không theo sau 1–2 chữ số là ngăn nghìn → `0.125` → `125`, `12.345` → `12345`. Xảy ra khi Enter không sửa gì, dán, kéo điền, hoàn tác, lọc theo ô | `core/money.py` `parse_money`; `forms_builder/services/record_service.py` `parse_value` (MONEY/DECIMAL); JS gửi `data-goc` thô | Ô tiền có `0.125` (nhập từ Excel) → bấm vào, Enter → thành `125` | Chặn nghiệm thu số liệu tiền (BR-8) | Sai dữ liệu tiền âm thầm, nhật ký ghi như người dùng cố ý | cả hai | 07.09 rà mã, đã kiểm lại mã | Mới |
| TL-04 | S2 | **Lọc khoảng cột tiền/ngày với chuỗi lạ → 500**: bộ lọc chỉ bắt `FieldError, ValueError, TypeError`, bỏ sót `ValidationError` của cột tách | `forms_builder/query.py` `build` / áp `f_<cột>__lon_bang` lên `val_revenue`, `val_date` | Hộp lọc cột Doanh thu, gõ `1.000.000` hoặc `1,5` vào Từ/Đến → trang trắng | — | Trang trắng 500 cho người dùng gõ số kiểu Việt | cả hai | 07.09 rà mã | Mới |
| TL-22 | S1 | **PR21: làm lại giao dịch sau deadlock không ghi gì mà vẫn 200**. Lần đầu đã gán giá trị mới vào đối tượng; lần hai `_dat_o` thấy "không đổi" → `update_cells` trả 0, không `bulk_save`, không nhật ký; view vẽ lại từ bộ nhớ nên màn hình như đã lưu | `crm/views.py` `bang_tinh_luu_o` hàm `luu()`; `forms_builder/services/record_service.py` `_dat_o`, `update_cells` | Worker đang tính lại cột trên bảng vận đơn, Leader dán 500 ô cùng lô → Postgres huỷ phía web → làm lại → mất 500 ô | **Chặn gộp PR #21** | Mất dữ liệu đúng trong tình huống PR tạo ra (tính lại nền song song với dán ô) | PR21 | 07.09 rà mã | Mới |
| TL-23 | S2 | **PR21: job "Tính lại cột" kẹt RUNNING** khi worker chết (khởi động lại, hết bộ nhớ) → `moi-nhat/` trả tiến độ mãi → JS không bao giờ nạp lại → mọi tab của bảng hiện "Đang tính lại cột…" vĩnh viễn, không thấy người khác sửa | `core/tasks.py` `danh_dau_tac_vu_ket` chỉ xử lý PENDING; `table_service.recompute_job_of`; `bang-tinh-o.js` poll | Bắt đầu tính lại 100.000 dòng, `docker compose restart worker` | Chặn gộp PR #21 | Bảng ngừng tự cập nhật cho mọi người, không thoát được kể cả sửa cột lần nữa | PR21 | 07.09 rà mã | Mới |
| TL-18 | S2 | Sau hết phiên, HTMX dán **cả trang đăng nhập vào ô/dòng** đang sửa | `core/middleware.py` (302), không chỗ nào xử lý `HX-Redirect`/401 cho HTMX | Để yên 61 phút, bấm đúp một ô | K28 | Lưới hỏng hình, người dùng không hiểu chuyện gì | cả hai | 07.09 ảnh anh/chị gửi | Mới |
| TL-19 | S2 | Máy chủ trả **400** (giá trị sai kiểu, thiếu cột bắt buộc) nhưng thanh trên báo **"✓ Đã lưu"** vì `htmx:beforeSwap` đặt `isError=false` cho 400 | `static/js/bang-tinh.js` `htmx:beforeSwap`, `htmx:afterRequest` | Gõ chữ vào cột Số Mess của dòng trống, rời ô | K28 | Người dùng tin đã lưu; thực tế không có dòng | cả hai | 07.09 video anh/chị, tái hiện Playwright | Mới |
| TL-20 | S2 | **Lời báo lỗi `.o-loi-chu` có trong DOM nhưng bị giấu**: đặt tuyệt đối dưới ô và bị lưới cắt; ô không đỏ vì `--critical-soft` không có trong khung lưới | `templates/crm/_dong_moi.html`, `_o_sua.html`; `static/css/bang-tinh.css` `.o-loi-chu`, `td.o-loi` | Như TL-19 | K28 | Không có phản hồi khi nhập sai | cả hai | 07.09 video, tái hiện | Mới |
| TL-21 | S3 | **Tiêu đề bảng ngoài vận đơn màu vàng đồng** (`#b8952b`) do áp kiểu "sheet nhỏ" của demo cho mọi bảng; yêu cầu gốc: ô trắng, tiêu đề xanh, chỉ ô cảnh báo mới vàng/đỏ | `static/css/bang-tinh.css` `.luoi-vd table.bang thead tr.bt-hang-ten th.bt-ten-cot` (vàng) vs `.bt-luoi-xanh` (xanh) | Mở Báo cáo Marketing | K28 | Sai yêu cầu thiết kế, màn hình vàng khè | cả hai | 07.09 ảnh anh/chị | Mới |
| TL-05 | S2 | **Khôi phục dòng bỏ qua phạm vi quyền**: lấy dòng bằng `all_objects` rồi chỉ kiểm `can_delete_record`; Leader khôi phục được dòng đã xoá của team khác qua POST thẳng, phản hồi rỗng | `crm/views.py` `bang_tinh_khoi_phuc_dong` | POST `khoi-phuc-dong/` với pk dòng team khác | — | Vi phạm quy tắc 11; dữ liệu sống lại ngoài ý chủ | cả hai | 07.09 rà mã | Mới |
| TL-06 | S2 | **Dòng trống hoặc ô sửa gặp 403/500 thì kẹt vĩnh viễn** (`dangLuu` chỉ gỡ khi swap) và từ đó `ranh()` thấy dòng đang lưu → **tự cập nhật dừng** tới khi tải lại trang | `static/js/bang-tinh.js` `dangLuu`, `htmx:afterSwap`; `bang-tinh-o.js` `ranh()` | Dòng trống, làm máy chủ trả 403 (mất quyền) | — | Người dùng không gửi lại được, không thấy sửa đổi của người khác | cả hai | 07.09 rà mã | Mới |
| TL-07 | S3 | **Hoàn tác ghi đè sửa đổi của người khác** không cảnh báo: bước hoàn tác chỉ giữ cũ/mới phía trình duyệt | `static/js/bang-tinh-o.js` hoàn tác | A dán, B sửa cùng ô, A Ctrl+Z | — | Mất sửa đổi của B | cả hai | 07.09 rà mã | Mới |
| TL-08 | S3 | **Sau khi chính mình lưu, ≤ 8 giây sau lưới tự nạp lại cả thân bảng và báo "Có dữ liệu mới"**; dòng mới không khớp bộ lọc đang bật (mở từ nhánh Tháng, quên ngày) **hiện rồi biến mất**; dòng trống bị 400 mà rời chuột thì mất giá trị đã gõ | `crm/views.py` `bang_tinh_moi_nhat`; `bang-tinh-o.js` `hoiMoiNhat`, `napLaiThan` | Mở Tháng 9, gõ dòng mới không có ngày, chờ 8 giây | — | Người dùng tưởng mất dữ liệu; toast sai | cả hai | 07.09 rà mã | Mới |
| TL-09 | S3 | **Sắp xếp không ổn định giữa các trang**: chỉ `order_by` một cột, không khoá phụ → dòng lặp hoặc thiếu khi sang trang | `forms_builder/query.py` `build` | Sắp theo Trạng thái, lật trang 1 → 2 | — | Bỏ sót dòng khi rà theo trang | cả hai | 07.09 rà mã | Mới |
| TL-10 | S3 | **Cột tiền không mang nhãn Doanh thu sắp xếp và lọc khoảng theo chuỗi** (`"999" > "1234.50"`), khoảng rơi về so bằng | `forms_builder/query.py` (JSON `data__<code>`), tiền lưu dạng chuỗi | Sắp cột CPQC | — | Thứ tự sai, lọc khoảng vô hiệu | cả hai | 07.09 rà mã | Mới |
| TL-11 | S3 | **Trang chủ và trang chọn bảng đếm cả dòng ngoài phạm vi và dòng đã xoá** (`Count("records")` qua quan hệ ngược); cây thư mục đếm đúng → hai số mâu thuẫn | `crm/services/tong_quan_service.py`; `crm/views.py` `_chon_bang` | Staff mở trang chủ, so với cây thư mục | — | Lộ số dòng ngoài phạm vi; số liệu lệch | cả hai | 07.09 rà mã | Mới |
| TL-12 | S4 | **Xoá 2.000 dòng ≈ 6.000 truy vấn** trong một yêu cầu: `delete_record` từng dòng, mỗi dòng `save()` lấy lại cột và ghi nhật ký | `crm/views.py` `bang_tinh_xoa_dong`; `core/models.py` `SoftDeleteModel.delete` | Chọn 2.000 dòng → xoá | — | Chậm, có thể quá thời gian gunicorn | cả hai | 07.09 rà mã | Mới |
| TL-13 | S2 | **Màn Sửa cột cho bỏ cột hệ thống của bảng vận đơn** (Số điện thoại, Mã đơn, Trạng thái) — menu chuột phải có rào, màn này không | `forms_builder/views.py` `bang_xoa_cot` (không kiểm `GRID_ORDER`/`sl_`) | Sửa cột bảng vận đơn → Bỏ "Số điện thoại" | — | Lọc trùng, cột khoá, tô màu dòng, đẩy đơn từ ERP hỏng | cả hai | 07.09 rà mã | Mới |
| TL-14 | S3 | **Dán vượt trang tạo dòng mới** thay vì ghi tiếp vào trang sau → dòng trùng | `static/js/bang-tinh-o.js` dán | Dán 150 dòng lên trang 100 dòng | — | Dữ liệu trùng | cả hai | 07.09 rà mã | Mới |
| TL-15 | S3 | **Định dạng ô ngoài phạm vi bị bỏ qua lặng lẽ** thay vì 403 | `crm/views.py` `bang_tinh_dinh_dang` (`if pk in ban_ghi_theo_pk`) | POST `dinh-dang/` với pk ngoài phạm vi | — | Trái quy tắc 8; giao diện vẫn "Đã lưu" | cả hai | 07.09 rà mã | Mới |
| TL-16 | S3 | **Sửa một ô ghi cả dòng** (không `update_fields`): hai người sửa hai ô cùng dòng trong cùng khoảnh khắc thì người sau ghi đè | `forms_builder/services/record_service.py` `update_cell` | Hai tab sửa hai ô cùng dòng cùng lúc | — | Mất một ô | cả hai | 07.09 rà mã | Mới |
| TL-17 | S3 | **Sửa một ô không vẽ lại cột tính sẵn** của dòng cho tới lần tự cập nhật | `crm/views.py` `bang_tinh_o` | Sửa Số lượng, nhìn Doanh thu | — | Số cũ hiện tới 8 giây | cả hai | 07.09 rà mã | Mới |
| TL-34 | S2 | **Thêm/sửa/bỏ cột tính sẵn hay cột mang nhãn trên bảng lớn chạy đồng bộ trong request**: 100.000 dòng mất 153 s, chiếm một tiến trình web | `forms_builder/services/table_service.py` `resync_table` (bản `main`) | Manager thêm cột tính sẵn vào bảng vận đơn 100.000 dòng | — | Request quá thời gian, người khác chờ | `main` (PR21 đã sửa) | 07.09 đo | Đã sửa ở PR21, chưa gộp |
| TL-24 | S3 | PR21: chỉ `luu-o` có làm lại khi deadlock; định dạng, sửa một ô, dòng mới, xoá dòng không có → có thể 500 khi trùng lúc tính lại. Thứ tự khoá dòng của `UPDATE … FROM VALUES` không được Postgres bảo đảm như chú thích | `crm/views.py`; `forms_builder/models.py` `bulk_save` | Định dạng 100 ô đúng lúc worker tính lại lô đó | Sau TL-22 | Lỗi 500 rời rạc | PR21 | 07.09 rà mã | Mới |
| TL-25 | S3 | PR21: **không gộp job tính lại** — bỏ 5 cột một lần tạo 5 job; sửa công thức hai lần liên tiếp có thể để một lô giữ giá trị cũ | `table_service.schedule_resync` | Bỏ 5 cột bằng chuột phải | Sau TL-22 | Worker bận gấp 5; giá trị có thể cũ | PR21 | 07.09 rà mã | Mới |
| TL-26 | S4 | PR21: lỗi ở một lô không dừng các lô còn lại, job thất bại vẫn chạy trọn thời gian | `table_service.resync_table` (`pool.map`) | — | — | Tốn thời gian worker | PR21 | 07.09 rà mã | Mới |
| TL-27 | S4 | PR21: `do_hieu_nang` đo "tính lại" trên dữ liệu đã đồng bộ nên không ghi dòng nào; số 19,6–29 s ở báo cáo đơn lẻ không gồm phần ghi; cột "truy vấn" của hai dòng đó sai vì lô chạy ở luồng khác | `core/management/commands/do_hieu_nang.py` | — | — | Số đo dễ hiểu sai; số Locust mới đúng | PR21 | 07.09 rà mã | Mới |
| TL-28 | S4 | PR21: `moi-nhat/` không còn lọc theo phạm vi từng người; docstring bài `test_moi_nhat_tra_moc_trong_pham_vi` vẫn ghi "trong phạm vi" | `crm/views.py`; `crm/tests/test_bang_tinh_dong_cot.py` | — | — | Không lộ dữ liệu; tài liệu lệch mã | PR21 | 07.09 rà mã | Mới |
| TL-29 | S4 | **Tệp tĩnh không được phục vụ khi chạy gunicorn** (không nginx, không whitenoise, không `collectstatic`); `scripts/kiem-tai-kn-crm.*` bật gunicorn 5 phút → mở trình duyệt lúc đó thấy trang không CSS | `deploy/Dockerfile` CMD; `deploy/docker-compose.yml`; `knjsc/settings/base.py` | Chạy script kiểm tải rồi mở 8021 | GĐ 8 (nginx) | Chỉ khi chạy gunicorn thủ công; Locust không tải tệp tĩnh | cả hai | 07.09 tái hiện | Mới |
| TL-30 | S4 | Script kiểm tải chạy `du_lieu_mau` mỗi lần → đặt lại mật khẩu 12 tài khoản mẫu; `seed_perf --xoa-cu` xoá cứng `perf_sale` và dòng `PERF-*` | `scripts/kiem-tai-kn-crm.sh`, `.bat` | Chạy script | — | Đúng ý trên máy dev, cần biết trước | PR21 | 07.09 rà mã | Mới |
| TL-31 | S4 | Docstring `grid_service.cell_url` nhắc bài `test_bang_tinh_hieu_nang` không tồn tại (bài thật: `test_url_o_ghep_chuoi_khop_reverse`) | `crm/services/grid_service.py` | — | — | Tài liệu lệch | PR21 | 07.09 rà mã | Mới |
| TL-32 | S4 | JSON ngày dạng `2026-09-01T10:00` làm `bulk_save` ném `ValidationError` — giống đường `save()` cũ, nhưng nay hỏng cả lô 1.000 dòng | `forms_builder/models.py` `sync_indexed_columns`, `bulk_save` | Nhập tệp có cột ngày kèm giờ rồi tính lại | — | Tính lại dừng giữa chừng | PR21 | 07.09 rà mã | Mới |
| TL-33 | S4 | `tests/test_hieu_nang.py` xfail vì ngân sách 10 truy vấn, thực tế 12–13 | `tests/test_hieu_nang.py` (K24) | Chạy bài đó | — | Bài kiểm không có sức nặng | cả hai | 05.09 | Mới |

## Đã kiểm, không thấy lỗi (để khỏi rà lại)

- Mọi view lưới lấy bảng và dòng qua `in_scope` (trừ TL-05); hộp lọc, xuất Excel, `moi-nhat`, cây thư mục đều có phạm vi; `GRID_ONLY_TABLES` rỗng ở 8021; Leader-như-Manager dùng chung `_quan_ly_bo_phan`.
- Không thấy XSS: template tự thoát, không `|safe`; JS dùng `textContent`; tham số lọc/sắp xếp chỉ nhận mã cột có thật, phép lọc là danh sách đóng; `cell_html` (PR21) thoát thuộc tính và chữ ô.
- CSRF đúng cho HTMX và `fetch`; cookie dùng chung 8020/8021 nên đăng xuất một bên là ra cả hai (đúng dự kiến).
- JS không đổ lỗi trên bảng không có cột Ngày, bảng rỗng, bảng không phải vận đơn; `localStorage` có try/catch.
- PR21: SQL tay trong `bulk_save` an toàn (tên qua `quote_name`, giá trị qua tham số, ép kiểu tường minh); luồng trong worker có kết nối riêng và tuần tự khi trong giao dịch; migration đảo ngược được; compose/Dockerfile hợp lệ; không vòng import Celery.

## Số đo đã có (máy ảo 4 nhân, 100.010 dòng, 07.09)

| Đường | `main` | PR21 |
|---|--:|--:|
| Lưới 100 dòng × 39 cột | 638 ms | 154 ms |
| Chỉ dòng trùng | 1.089 ms | 478 ms |
| Dán 500 ô | 1.670 ms | 207 ms |
| Tính lại cột 100.000 dòng | 153 s trong request | 19,6 s ở worker |
| 100 người 5 phút, p95 đọc / ghi / hỏi | ~11 s, 14 lỗi | 853 / 371 / 143 ms, 0 lỗi |

Ba điều kiện đo do tôi đặt, chờ anh/chị xác nhận: nhịp người ảo 4–12 giây một
thao tác; bỏ 20 giây đầu khi cả 100 người đăng nhập; lượt bị từ chối vì dòng
vừa bị người khác xoá không tính là lỗi.


### 09.09.2026 — BC MKT trên KNERP, triển khai local

Đã hoàn thiện các chỉ tiêu xác định theo Excel, lịch sử lọc biểu mẫu/phòng ban,
khối Marketing trên Tổng quan và đổi tên Đánh giá nhân sự. Chi tiết và giới hạn
ở [BC MKT ERP](bc-mkt-erp.md). `KNJSC_PROBLEM.txt` đánh dấu `-> đã làm` riêng
phần hoàn thành; không đánh dấu cả nhóm 05/06 hoặc các mục hoãn.

Kiểm chứng: 13 test mới đạt (công thức, tổng, zero/missing, 4 cấp quyền trên
lịch sử/thống kê/Tổng quan/xuất, lọc và lỗi khối). Hồi quy reports, culture,
core/tests/test_giao_dien.py, core/tests/test_mau_dung_chung.py và crm/tests đạt.
Phát hiện rồi sửa vượt trần truy vấn do bộ lọc; test lịch sử/tổng hợp <=10 đạt.
Sau tách helper lịch sử và sửa comment lộ trên UI, chạy lại reports đạt.
Trình duyệt 1440px/390px đạt, không có console error được ghi nhận.
Chưa commit/push; chưa áp quy tắc báo cáo muộn hoặc mở mục thị trường.
## 09.09.2026 — Kiểm chứng feedback Vận đơn mới (ADR-020)

Nhánh `codex/sua-feedback`. Thay đổi phân công theo tài khoản, phạm vi dùng
chung CRM/ERP, bộ lọc và Excel; không triển khai H7 hoặc Lên đơn nhúng.

- Hồi quy trước sửa: hai test đỏ chứng minh nhân viên Vận đơn thấy đơn chưa
  giao và lọc mã sản phẩm chưa tác động tới chi tiết. Sau sửa đạt.
- Suite không gồm bài chậm: **1.923 passed, 1 skipped, 33 deselected**,
  94,40 giây. Bài skip là cầu Chrome riêng chưa bật biến môi trường trong
  suite; đã chạy riêng bằng Chrome thật và đạt **1 passed** (13,38 giây).
- Chrome desktop 1440×1000 và mobile 390×844: phân công một dòng bằng Enter,
  chọn vùng/giao hàng loạt, giữ trường khác, chọn tên dài, xung đột 409 rồi
  tải lại, URL/bộ lọc/sắp xếp, sidebar, trạng thái rỗng, không tràn ngang trang.
  Ảnh và log local: `.agents/design-state/review/feedback/`.
- Sau khi chốt lưu ID từ chính những dòng đã ghi vào workbook, chạy lại
  nhóm phân công/xuất/nhập/truy vết: **65 passed** (14,91 giây), database
  pytest riêng `test_knjsc_feedback_verify`.
- Có test hai kết nối phân công cùng hai dòng với thứ tự đầu vào ngược nhau:
  một lượt lưu, một lượt xung đột; không ghi đè. Có kiểm đổi/bỏ, rollback,
  sai bộ phận/tài khoản khoá, CSKH chỉ xem, grant không vượt phạm vi, API/dán/
  nhập/định dạng/khôi phục, thống kê và gợi ý; xuất trực tiếp/nền, worker và tải
  lại sau đổi quyền, mã trùng tên, ngày và dòng thiếu liên kết Sale.
- Migration `0004/0005` có kiểm ngược/xuôi trên DB test, giữ dữ liệu dòng,
  không tự phân công. Đã chạy cả nhóm `core/tests/test_chuyen_doi.py` riêng.
  Trên DB local chỉ migrate xuôi: trước/sau vẫn 13 dòng bảng cũ, 20 dòng bảng
  mới, 0 phân công. Không dùng dữ liệu local để thử ghi phân công.
- Lưới mới 100 dòng kiểm ngân sách tối đa 22 truy vấn; ngân sách lưới/bulk/
  polling bảng cũ vẫn đạt. Đây không phải kiểm tải 100 nghìn khách hoặc
  nghiệm thu 10–20 người thao tác liên tục.
- Đánh dấu đúng 7 ý trong `KNJSC_PROBLEM.txt`: Problem 01 ý 6–7, Problem 02
  ý 4–5, Problem 03 ý 1–3. Phụ lục nguồn và Problem 02 ý 6 giữ nguyên.

Lệnh từ gốc repository (giữ database test riêng, bỏ entrypoint seed):

```powershell
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest -m 'not cham' -o addopts='--strict-markers --ds=knjsc.settings.test' -q
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest core/tests/test_chuyen_doi.py
```

Kiểm Chrome: chạy lệnh server dưới đây, rồi chạy script Node trên host trong
khi server đợi. `POSTGRES_DB` này chỉ đặt tên cho DB pytest, không phải DB dev.
Script dùng tài khoản fixture của pytest, không dùng tài khoản khách hàng.

```powershell
docker compose -f deploy/docker-compose.yml run --rm -p 8031:8031 -e RUN_MIGRATIONS=0 -e POSTGRES_DB=knjsc_feedback_ui -e KN_FEEDBACK_BROWSER=1 web pytest crm/tests/test_feedback_browser_server.py --liveserver=0.0.0.0:8031
$env:NODE_PATH='C:\Users\PC\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules'
& 'C:\Program Files\nodejs\node.exe' scripts/kiem-thu-feedback-ui.cjs
```

Chưa commit/push trong tác vụ này. Nhật ký lịch sử bên trên giữ nguyên.

---

## 10.09.2026 — Chín hạng mục CRM, bàn giao khi tạm dừng chạy bền

- Đã triển khai autosave, chọn hàng/xanh dương, hai chế độ, fs/c/bg, lịch sử
  và conflict, Admin chọn Sale, đơn cũ trước/mới cuối, số hàng từ 1.
- Suite `crm/tests orders/tests forms_builder/tests core/tests tests/test_luong_ba_bo_phan.py`:
  1.049 passed, 6 fixture chuyên dụng skipped, 87,87s. Sau bổ sung cuối,
  `crm/tests/test_master_nine.py orders/tests crm/tests/test_waybill_new.py`:
  90 passed. Không cộng hai lượt thành một con số suite.
- Node working copy, autosave, queue, scope, conflict, geometry đạt.
  Chrome cuối 16 nhóm E2E/UI đạt: nhiều vai trò, replay sau mất phản hồi,
  409 hai lựa chọn, thu quyền giữa dán hai hàng (không ghi một phần),
  Undo/Redo, định dạng, hàng/cột, bấm đúp 120ms, copy/paste và viewport.
- Migration history/cover index xuôi/ngược trên DB test đạt; local đã áp
  dụng xuôi. Mọi thử ghi dùng DB test, không dùng khách mẫu đang làm việc.
- Ma trận trước/sau đủ 100k/300k ×10/20, 60s làm nóng +300s đo mỗi lượt.
  Sau: p95 đọc khối 164–664ms, ghi ô 86–124ms; lọc 300k 1.135–1.340ms
  chưa đạt 1s. Sáu lỗi ngắt kết nối trong 11.815 request cuối, không loại
  khỏi số đo; kiểm tính toàn vẹn không báo sai dữ liệu ở ma trận ngắn.
- Chrome 100 mẫu/thao tác p95 30–49ms, cache ≤10 và DOM hữu hạn. History
  300k khoảng 69,28 MiB; receipt 320 lượt 2,26 MiB, số đo riêng từng bảng.
- Chủ dự án yêu cầu dừng chạy bền và push: đã dừng sau mẫu Chrome phút 15,
  chưa đủ 30 phút và chưa có tổng HTTP chạy dài. Giữ trạng thái chưa kiểm
  chứng để phiên sau chạy lại. IME Windows thật/native zoom chưa xác nhận.
- KNJSC Problem 02 ý 8 chỉ đánh dấu phần thao tác CRM được kiểm chứng;
  không đánh dấu H7 hoặc toàn bộ hiệu năng. Báo cáo và bằng chứng:
  [chín hạng mục](kiem-chung-master-nine.md).

---

## 11.09.2026 — 10.000 vận đơn mẫu và vùng cột ghim

Phạm vi nhánh `vandonmoi`: management command chỉ tác động nhóm
`MAU-20260910-*`, giao diện riêng của master grid Vận đơn mới và tài liệu vận hành.

- Trước khi ghi database local đã tạo `storage/backups/knjsc-20260911-015637.dump`.
  Dry-run dự báo đúng 500 dòng cập nhật/9.500 dòng tạo mới; chạy thật mất khoảng
  10,6 giây. Chạy lại cùng seed không ghi thêm hoặc tăng phiên bản phân công.
- Đối chiếu local: 10.000 dòng, 10.000 mã đơn và 10.000 số điện thoại duy nhất;
  19.970 chi tiết sản phẩm; 10.000 phân công. Không có dòng thiếu địa chỉ, ghi chú
  `???`, sai tổng chi tiết, sai bộ phận Vận đơn/CSKH hoặc có Marketing tự gán.
  Trạng thái thanh toán gồm 3.334 chưa thanh toán, 4.584 một phần và 2.082 đã
  thanh toán; đơn chưa trả không có ngày/bill/PTTT thực tế.
- Test command có dry-run, giữ ID/danh tính, không tạo Customer/Order/OrderLine,
  tổng Decimal, phân công hợp lệ, chạy lại giữ ID/phiên bản/audit, thiếu nhân sự
  không ghi và lỗi giữa lượt rollback toàn bộ.
- Trình duyệt thật tại cổng 8021 xác nhận 10.000 dòng tải được, ba cột Mã đơn/Tên
  khách/Số điện thoại cùng ghim khi cuộn ngang và cột cuối có ranh giới. Script
  lớp chồng cột cố định đạt. Không dùng thao tác sửa dữ liệu để kiểm giao diện.
- Suite toàn workspace trong thư mục đang làm việc không dùng làm bằng chứng đạt:
  có thay đổi chưa commit khác về Executive statistics xuất hiện trong lúc chạy,
  gây 17 lỗi ngoài phạm vi (template/CSS/nhãn/truy vết). Các file này được giữ
  nguyên và không đưa vào commit `vandonmoi`.
- Trên worktree sạch của commit, nhóm command + master grid đạt **22 bài**. Suite
  đầy đủ dùng container và test database riêng đạt **2.019 bài**, 24 skip, 2 xfail;
  còn bốn lỗi truy vết có sẵn do AC-21.8/9/11 chưa được nối tới test và `docs/06`
  còn số đếm cũ. Đã bổ sung mã vào chính các bài hiện có và đồng bộ thành 159 tiêu
  chí, 146 tự động, 145 đã có bài; chạy lại nhóm truy vết rồi suite sạch trước push.
- Sau đồng bộ truy vết: **13 bài truy vết đạt**; suite đầy đủ cuối trên worktree,
  container và test database riêng đạt **2.023 passed, 24 skipped, 2 xfailed**
  trong 288,39 giây. Các bài trình duyệt bị skip không được tính là đã kiểm bằng
  suite; phần ghim/cột chồng đã được kiểm riêng bằng trình duyệt thật và script Node.

---

## 11.09.2026 — Bàn điều hành KN CRM (ADR-022)

- TDD đỏ trước triển khai: 8 bài đầu của `test_executive_statistics.py` cùng thất
  bại vì trang chỉ nhận `van_don_moi`, chưa có profile, kỳ so sánh, chọn nguồn
  hoặc owner. Sau triển khai mở rộng thành 15 bài, gồm cả nguồn `van_don` lịch sử,
  scope bốn cấp, lỗi cô lập, hình học biểu đồ, tách tiền và liên kết KNERP.
- Nhóm hồi quy tập trung:
  `crm/tests/test_executive_statistics.py crm/tests/test_master_grid.py
  crm/tests/test_waybill_new.py crm/tests/test_waybill_feedback.py reports/tests`:
  lần đầu còn một lỗi loại tiền của đơn thiếu chi tiết bị rơi khỏi bảng tổng; đã
  sửa để giữ nhóm với giá trị 0. Lần bàn giao cuối đạt **159 passed trong
  41,22 giây**.
- `python -m compileall -q app/crm app/orders` đạt.
- `scripts/kiem-thu-ban-dieu-hanh-ui.cjs` đạt ở 1440px, 1280px, 390px, sáng,
  tối + `prefers-reduced-motion` và zoom 125%: không tràn ngang, tối đa ba
  insight, SVG đều có title/focus, biểu đồ đều có bảng đối chiếu; màn Vận đơn
  chuyên sâu có đủ 6 biểu đồ, 4 KPI và link ngày/trạng thái đúng.
- `KN_EXECUTIVE_CAPACITY=1` trên database test riêng, mỗi mốc warmup rồi đo 20
  request: Sale 20.000 dòng p50/p95 **73,72/89,07ms**; Vận đơn 100.000 dòng
  **289,93/333,72ms**; Vận đơn 300.000 dòng **781,53/893,26ms**; tổng hợp Sale
  20.000 + Vận đơn 300.000 **498,61/733,64ms**. Vận đơn giữ 12 query ở cả hai
  cỡ; đỉnh cấp phát Python cùng **0,25MiB**, không tăng theo số dòng. AC-22.9 đạt
  trên máy phát triển; đây không thay thế kiểm tải đồng thời trên máy chủ thật.
