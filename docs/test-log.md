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
