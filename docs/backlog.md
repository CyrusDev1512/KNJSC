# Backlog

Nơi ghi lại mọi phát hiện, ý tưởng và câu hỏi chưa được quyết định.

> **Quy tắc:** phát hiện gì thì ghi vào đây trước, **không sửa tài liệu ngay**.
> Chỉ cập nhật tài liệu sau khi đã quyết định thực hiện.
>
> Phát hiện được ghi lại không có nghĩa là sẽ làm. Có thứ đáng làm, có thứ để sau,
> có thứ không bao giờ làm.

---

## Cách đọc

| Cột | Nghĩa |
|---|---|
| Mức | Chặn · Cao · Trung bình · Thấp |
| Trạng thái | Chờ quyết định · Đã duyệt · Từ chối · Đã làm |
| Nguồn | Ai hoặc cái gì phát hiện ra |

**Mức Chặn** nghĩa là không làm thì không triển khai được.

---

## 0. Còn nợ những gì — xem ở đây trước

Một chỗ duy nhất liệt kê **mọi thứ chưa xong**, cả việc của người dùng lẫn việc
của người viết mã. Chi tiết từng mục nằm ở các phần bên dưới; phần này là bản
tóm để không phải lục.

> Cập nhật ngày 05.09.2026. Giai đoạn 7 phần E (ADR-010) đã vào `main` qua
> PR #4. Phần F — Bảng tính nhìn và thao tác như bảng tính KN Demo (ADR-011) —
> đã xong nhưng **còn trên nhánh riêng** `claude/bang-tinh-nhu-kn-demo` (PR #5,
> base `main`), chờ anh/chị nghiệm thu. Mục D chỉ còn `AC-5.1`.

**Đang ở đâu:** xong Giai đoạn 0 tới 7. Nhập tệp Excel/CSV bốn bước có xem
trước và tiến độ, xuất kèm bộ lọc, tệp lớn chạy nền giữ 24 giờ (7A). Sao lưu
`pg_dump` 02:00 mỗi đêm giữ 30 bản, hỏng thì thư cho người vận hành, phục hồi
bằng `scripts/restore.sh` (7B). **Bảng tính vận đơn** theo tệp thật — lọc từng
cột, sửa ô có danh sách chọn, Lọc trùng, tô màu Hủy/Hoàn, mỗi sản phẩm một cột
— chạy ở dịch vụ `bangtinh` `localhost:8021/bang-tinh/`, Bảng dữ liệu chỉ xem
(7C, ADR-009). Kiểm thử chín tầng: thêm Playwright (bàn phím, hộp lọc, cột cố
định, 390px), 50.000 dòng dưới 2 giây, Locust 50 người tự chấm, ma trận 45 ô;
`docs/07` là kịch bản bấm tay (7D). **Bảng tính cho mọi bảng** (7E, ADR-010):
`/bang-tinh/<mã bảng>/` cho bảng nào trong phạm vi; viền ô như Excel, dòng
trống cuối lưới gõ là thành bản ghi; định dạng ô (đậm, nền, cỡ, căn) lưu vào
cơ sở dữ liệu; cột khoá bấm ⌕ là lọc; thanh lọc bên trái (chọn nhanh, khoảng
ngày, sản phẩm); thanh công cụ; thư mục chứa bảng. **Bảng tính như KN Demo**
(7F, ADR-011): khung tối viền vàng, thanh công thức có ô địa chỉ, số dòng,
chữ cột tới Z, chân trang có tab; kéo chọn vùng, dán từ Excel, kéo điền, hoàn
tác, menu chuột phải (xoá/khôi phục dòng, Manager chèn/xoá cột), 40 màu và
định dạng số, hộp lọc theo giá trị, tự cập nhật khi người khác sửa. 94 tiêu
chí, 83 trên 84 tự động có bài kiểm.

**Việc tiếp theo:** **nghiệm thu một đợt theo `docs/07`** — anh/chị bấm tay
từng vai, đánh ☑, gửi danh sách lỗi; sửa trên nhánh `claude/bang-tinh-nhu-kn-demo`
rồi mới gộp PR #5. Xem Bảng tính mới ở máy nhà bằng
`scripts\cap-nhat-local.bat claude/bang-tinh-nhu-kn-demo`; chạy không tham số
thì về `main` — lưới ADR-010, chưa có dáng KN Demo. Rồi Giai đoạn 8: máy chủ,
subdomain cho Bảng tính, đo tải trên máy chủ thật (chờ V1).

### A · Nghiệm thu — việc của anh/chị

**Chưa có gì được nghiệm thu.** Giai đoạn 0 tới 5 đều đã giao và toàn bộ bài
kiểm thử tự động đều đạt, nhưng anh/chị **chưa trực tiếp thử màn hình nào**. Phần
trăm trên `dashboard-tien-do.html` là tiến độ *đã làm*, không phải *đã nghiệm thu*.

**Mười bốn việc làm được ngay bây giờ — kịch bản từng bước ở `docs/07`:**

| ☐ | Việc | Mã |
|---|---|---|
| ☐ | Thêm team mới, dùng ngay không khởi động lại | `AC-2.4` |
| ☐ | Mở trên điện thoại và máy tính bảng thật | `AC-10.4` |
| ☐ | Cài từ đầu trên máy sạch, chạy tới màn hình đăng nhập | `docs/04` mục 12.1 |
| ☐ | Ba vai trò đăng nhập, chạy trọn quy trình của mình | `docs/04` mục 12.2 |
| ☐ | Thử trên điện thoại và máy tính bảng thật | `docs/04` mục 12.5 |
| ☐ | Ngắt mạng giữa chừng, kiểm thông báo lỗi | `docs/04` mục 12.7 |
| ☐ | Xuất báo cáo tổng hợp, mở bằng Excel, đối chiếu số | `AC-5.6` · mục 12.4 |
| ☐ | Nhập tệp vận đơn thật (`docs/tham-khao/vandon-mau.xlsx`) qua Bảng dữ liệu → Nhập tệp | mục 12.3 |
| ☐ | Sao lưu rồi phục hồi trên máy thử: `scripts/backup.sh`, `scripts/restore.sh --toi-chac-chan` | `AC-10.5` · mục 12.6 |
| ☐ | 50 người đồng thời: `manage.py seed_perf` rồi Locust 1 phút, in ĐẠT | `AC-10.1` |
| ☐ | Bảng tính: cuộn ngang dọc, cột đầu và tiêu đề đứng yên | `AC-11.1` |
| ☐ | Bảng tính trên điện thoại và máy tính bảng thật | `AC-11.11` |
| ☐ | Bảng tính: mọi ô có viền, thanh công cụ đủ mục, ẩn cột nhớ được, thanh bên thu gọn được | `AC-11.18` |
| ☐ | Bảng tính đặt cạnh ảnh `docs/tham-khao/kn-demo/`: khung, thanh công thức, số dòng, chữ cột, cột trống, chân trang, ⛶; kéo chọn vùng, dán từ Excel, chuột phải | `AC-11.27` |

**Một việc biết trước là chưa đạt:**

| Việc | Mã | Chờ |
|---|---|---|
| Gặp lỗi hiện thông báo tiếng Việt, không trang trắng | `AC-10.3` | Trang 404 và 500 chưa làm — **K9**, người dùng chốt chưa phải lúc |

### B · Câu hỏi chờ anh/chị quyết

Sáu câu này **chặn việc thật**, không phải bàn cho vui:

| # | Câu hỏi | Chặn gì |
|---|---|---|
| **V4** | Mốc nào thì nghiệm thu toàn diện | Cả mục A ở trên |
| **V2** | Ai vận hành hằng ngày sau bàn giao | **K17** — có nên dựng chạy kiểm thử tự động không |
| **V1** | Máy chủ đặt ở đâu | Giai đoạn 8 |
| **N1** | Nộp báo cáo có bắt buộc đúng giờ không | **K16** — cột Trạng thái trên Lịch sử báo cáo |
| **N3** · **N6** | Chăm sóc khách hàng có trong phase 1 không | Biểu mẫu báo cáo CSKH ở Giai đoạn 4 |
| **N7** | Quản trị viên có phải thuộc một bộ phận không | BR-1 đang mâu thuẫn với mã |

Còn sáu câu **H1 tới H6** cần hỏi trực tiếp người dùng cuối, không phải anh/chị
trả lời thay — xem mục 5. Hai câu **N9** và **N10** anh/chị đã chốt hoãn ngày
03.09.2026 — hỏi lại sau, không chặn gì.

### C · Lỗ hổng kỹ thuật đã biết

Không cái nào chặn triển khai. Xếp theo mức.

| # | Nội dung | Mức |
|---|---|---|
| **K9** | Chưa có trang lỗi 404 và 500 tiếng Việt — người dùng chốt 03.09.2026: chưa phải lúc | Trung bình |
| **K7** | Khoảng 60 định danh tiếng Việt trong mã Python, trái quy ước `CLAUDE.md` | Trung bình |
| **K13** | Cấp quyền đi hai cơ chế song song, xem lại có gộp được không | Trung bình |
| **K16** | Cột Trạng thái trên Lịch sử báo cáo — chờ **N1** | Trung bình |
| **K17** | Chưa có gì chạy kiểm thử tự động khi đẩy mã — chờ **V2** | Trung bình |
| **K23** | Bài Playwright hộp lọc cột: form gửi lần hai với ô trống ngay sau khi trang tải, chạy tay thì đúng — bài đánh dấu xfail | Trung bình |
| **K24** | Trang Bảng dữ liệu và Bảng tính trên 50.000 dòng tốn 12 lệnh truy vấn, hơn ngân sách 10 (Q2) hai lệnh; thời gian vẫn đạt 0,4 s và 1,1 s — bài hiệu năng đánh dấu xfail | Trung bình |
| **K19** | Bài Playwright và bài 50.000 dòng chỉ chạy trên máy phát triển, không chạy trong container `web` (không có Chromium, `pytest` mặc định không bỏ `cham` nhưng image không có trình duyệt) | Thấp |
| **K21** | Thư mục `storage/` là bind mount, container chạy uid 1000: máy Linux mà chủ thư mục khác thì nhập tệp và sao lưu hỏng — entrypoint chỉ cảnh báo, chưa tự sửa | Thấp |
| **K22** | Danh sách chọn cho cột *Chọn một* của bảng tự tạo — bảng vận đơn có sổ đăng ký (ADR-009), bảng tự tạo chưa | Thấp |
| **K8** | `ScopedModel` chưa có cột "người sửa" | Thấp |
| **K10** | Quy tắc Q3 chưa áp ở màn hình nào | Thấp |
| **K14** | Nhánh Staff trong `apply_scope` không đọc phạm vi cấp thêm | Thấp |

### D · Tiêu chí nghiệm thu chưa có bài kiểm

2 tiêu chí đánh dấu *Tự động* nhưng chưa viết được. Danh sách này nằm trong
`app/tests/test_truy_vet.py`, biến `HOAN`, và
**có bài kiểm bắt phải ghi lý do** — không giấu được.

| Tiêu chí | Chờ |
|---|---|
| `AC-5.1` | Bốn cách nhóm mới chạy ba — tab thị trường chờ **N9** |
| `AC-7.1` | 50.000 bản ghi dưới 2 giây, cần `seed_perf.py` — Giai đoạn 7D |

### E · Màn hình chưa có

**Không còn.** Cả 10 màn hình của bản dựng ở `prototype/` đã có bản Django —
riêng Bảng tính làm theo tệp thật thay vì theo bản dựng (ADR-009). Chi tiết ở
mục 6.

---

## 1. Chờ quyết định

### 1.1. Kỹ thuật

| # | Nội dung | Mức | Nguồn |
|---|---|---|---|
| K7 | Đổi khoảng 60 định danh tiếng Việt trong mã Python sang tiếng Anh theo quy ước CLAUDE.md, gồm cả tên ràng buộc `team_unique_trong_bo_phan` đã vào PostgreSQL | Trung bình | Rà soát GĐ 1–2 |
| K8 | `docs/03` mục 2.1 đòi mọi bảng có cột "người sửa"; `ScopedModel` mới có `created_by`, chưa có `updated_by` | Thấp | Rà soát GĐ 1–2 |
| K9 | Chưa có trang lỗi 404 và 500 bằng tiếng Việt — NFR-6 mới đạt một phần. Người dùng chốt 03.09.2026: chưa phải lúc, để lại chờ xếp giai đoạn | Trung bình | Rà soát GĐ 1–2 |
| K10 | Quy tắc Q3 "chỉ lấy cột cần hiển thị" chưa áp ở màn hình nào | Thấp | Rà soát GĐ 1–2 |
| K13 | `core/scope.py _granted_scope` vẫn trả về rỗng. Cấp quyền theo bảng và biểu mẫu đi đường riêng ở `forms_builder/services/grant_service.py` — hai cơ chế song song, nên xem lại có gộp được không | Trung bình | GĐ 3B |
| K14 | Nhánh Staff trong `apply_scope` không đọc `department_ids` lẫn `team_ids`, nên cấp thêm cả một bộ phận cho Staff không có tác dụng | Thấp | GĐ 3B |
| K16 | Cột **Trạng thái** trên Lịch sử báo cáo (Đã nộp · Nộp muộn · Chưa nộp) chưa làm được vì chưa chốt **N1** — lịch nộp báo cáo có bắt buộc đúng giờ không. Không có hạn nộp thì không tính được thế nào là muộn | Trung bình | Đối chiếu 8010 |
| K17 | Chưa có gì chạy kiểm thử tự động khi đẩy mã lên kho. Người dùng chốt chưa dựng vì **V2** còn để ngỏ ai vận hành sau bàn giao | Trung bình | Kế hoạch kiểm thử |
| K23 | `tests/e2e/test_bang_tinh_ui.py::test_hop_loc_cot_doi_so_dong_va_url`: sau khi gửi form hộp lọc (URL đã có `f_…`), trang lại tải lần nữa với form trống (`?q=&loc_trong_…=`). Thử tay bằng Playwright script trên dịch vụ 8021 thì đúng một lần. Nghi vấn: HTMX xử lý lại `#hop-loc` hoặc `autofocus` của ô tìm; cần bắt `htmx:beforeRequest` để soi. Bài đánh dấu `xfail(strict=False)` ngày 03.09.2026 vì người dùng cần demo gấp | Trung bình | GĐ 7D |
| K24 | Bài `tests/test_hieu_nang.py` trên 50.000 dòng: thời gian đạt (0,4 s Bảng dữ liệu, 1,1 s Bảng tính có lọc) nhưng đếm 12 lệnh truy vấn, hơn ngân sách 10 của Q2 hai lệnh. Chưa soi được lệnh nào thừa (nghi: phiên + hồ sơ + phạm vi + bảng + cột + đếm + trang + quyền cấp + sổ danh sách nhân viên). Bài đánh dấu `xfail(strict=False)` | Trung bình | GĐ 7D |
| K19 | Bài kiểm trình duyệt thật (`tests/e2e/`, Playwright) và bài hiệu năng 50.000 dòng cần Chromium và thời gian, không chạy trong container `web` — tự bỏ qua kèm lý do. Chạy trên máy phát triển: `pip install -r requirements-dev.txt && playwright install chromium && pytest -m trinh_duyet` | Thấp | GĐ 7D |
| K21 | Thư mục `storage/` là bind mount, container chạy uid 1000. Trên máy Linux mà chủ thư mục là người khác thì nhập tệp và sao lưu hỏng vì không ghi được; `entrypoint.sh` mới chỉ cảnh báo, chưa tự sửa quyền | Thấp | GĐ 7B |
| K22 | `ColumnDef` kiểu *Chọn một* chưa có trường lưu danh sách lựa chọn. Bảng vận đơn dùng sổ đăng ký `forms_builder.choice_registry` (crm đăng ký lúc khởi động — ADR-009); bảng tự tạo vẫn nhận mọi giá trị. Muốn có danh sách cho bảng tự tạo thì thêm trường `options` kèm tệp chuyển đổi | Thấp | GĐ 7C |

### 1.2. Nghiệp vụ

| # | Nội dung | Mức | Nguồn |
|---|---|---|---|
| N1 | Lịch nộp báo cáo có bắt buộc đúng giờ không — chỉ ghi nhận, nhắc nhở, hay chặn nộp muộn | Trung bình | Bàn phạm vi |
| N2 | Nhân viên vận đơn có tự thêm cột vào bảng không | Thấp | Đã hỏi, trả lời là không |
| N3 | Vai trò Chăm sóc khách hàng có thuộc phase 1 không | Trung bình | Tệp vận đơn có cột CSKH, phase 1 chưa có vai trò này |
| N6 | Chăm sóc khách hàng có trong phase 1 không — `README.md` xếp vào phạm vi, `docs/02` mục 12 để ngỏ. Trùng với N3 nhưng nay có thêm chứng cứ vênh giữa hai tài liệu | Cao | Rà soát GĐ 1–2 |
| N7 | BR-1 nói mỗi người thuộc đúng một bộ phận, nhưng Admin hiện không thuộc bộ phận nào. Giữ nguyên hay bắt Admin cũng phải có bộ phận | Trung bình | Rà soát GĐ 1–2 |
| N9 | Cách nhóm theo thị trường của báo cáo tổng hợp lấy số liệu từ đâu — cột Quốc gia bảng vận đơn chưa có nhãn ý nghĩa (ADR-007 để ngỏ); ba đường: thêm nhãn thứ tám kèm tệp chuyển đổi, lấy từ đơn hàng, hay nhóm cột JSON. Người dùng chốt 03.09.2026: **chưa quan trọng, hỏi lại sau**. Tab vẫn hiện kèm ghi chú — Q36 | Trung bình | Kế hoạch GĐ 6 |
| N10 | Có tách loại tiền VND và USD khi cộng doanh thu không — bảng động chưa lưu loại tiền theo dòng có nhãn (Q10 lưu kèm loại tiền chỉ áp cho đơn hàng). GĐ 6 chọn cách đơn giản nhất: cộng thẳng `val_revenue`, không kèm ký hiệu tiền. Hỏi lại cùng lúc với N9 | Thấp | Kế hoạch GĐ 6 |

### 1.3. Vận hành

| # | Nội dung | Mức | Nguồn |
|---|---|---|---|
| V1 | Máy chủ đặt ở đâu — thuê ngoài hay đặt tại văn phòng | Trung bình | Chưa chốt |
| V2 | Ai chịu trách nhiệm vận hành hằng ngày sau khi bàn giao | Cao | Chưa chốt |
| V3 | Kênh gửi thông báo nếu làm tính năng nhắc nộp báo cáo | Thấp | Phụ thuộc N1 |
| V4 | **Mốc nào thì nghiệm thu toàn diện.** Hiện quá ít màn hình để đánh giá được giao diện và trải nghiệm — người dùng không nghiệm thu từng phần nữa, dồn về một đợt. Đề xuất mốc: hết Giai đoạn 5, khi một bộ phận làm trọn được việc hằng ngày. Chờ người dùng chốt | Cao | Người dùng, 29.08.2026 |
| V5 | **Kế hoạch kiểm thử và nghiệm thu chưa lập.** Người dùng chốt để sau, làm cùng lúc với đợt nghiệm thu ở V4. Nội dung cần có: ai kiểm, kiểm trên dữ liệu nào, bao lâu, tiêu chí nào coi là đạt, và xử lý thế nào khi không đạt | Cao | Người dùng, 29.08.2026 |

---

## 2. Đã quyết định

| # | Nội dung | Quyết định | Ngày |
|---|---|---|---|
| Q1 | Đơn hàng chảy sang bảng vận đơn theo chiều nào | Một chiều cho phase 1 | (điền) |
| Q2 | Có làm quản lý tài nguyên và kho thông tin đăng nhập không | Không làm | (điền) |
| Q3 | Mảng nhân sự, kế toán, kho | Để giai đoạn sau | (điền) |
| Q4 | Có tích hợp với phần mềm kế toán không | Không, ít nhất trong phase 1 | (điền) |
| Q5 | Ứng dụng di động | Không làm bản cài đặt, chỉ cần giao diện dùng được trên điện thoại | (điền) |
| Q6 | Trợ lý AI | Không làm trong phase 1 | (điền) |
| Q7 | Khung ứng dụng | Django 5.2, PostgreSQL 16, HTMX, Celery với Redis, Docker Compose — ADR-005 | 28.08.2026 |
| Q8 | Danh sách module trong `app/` | Bảy module: core, org, forms_builder, reports, orders, dashboard, crm | 28.08.2026 |
| Q9 | Quản trị viên trong mô hình bộ phận × cấp bậc | Cấp bậc thứ tư tên Admin, phạm vi mọi bộ phận, có tất cả các quyền | 28.08.2026 |
| Q10 | Loại tiền tệ | Phase 1 dùng VND và USD, mỗi số tiền lưu kèm loại tiền, không quy đổi khi lưu | 28.08.2026 |
| Q11 | Mức độ công thức trên bảng — K1, FR-7.8 | Bảng dữ liệu chỉ có cột tính sẵn; gõ công thức tự do tách sang màn hình Bảng tính, không ghi ngược — ADR-006 | 29.08.2026 |
| Q12 | Bảng đích khi tạo biểu mẫu — K2 | Luôn chọn bảng có sẵn, không tự sinh bảng mới — ADR-007 | 29.08.2026 |
| Q13 | Bảy nhãn ý nghĩa — K3 và N8 | Theo `docs/03` mục 2.5: Ngày, Khách hàng, Số điện thoại, Doanh thu, Người bán, Sản phẩm, Trạng thái — ADR-007 | 29.08.2026 |
| Q14 | Chia Giai đoạn 3 làm mấy đợt | Hai đợt có điểm dừng: 3A bảng dữ liệu, 3B biểu mẫu và phân quyền theo bảng | 29.08.2026 |
| Q15 | Màn hình Bảng tính xếp vào giai đoạn nào | Giai đoạn 7, làm chung với nhập xuất Excel | 29.08.2026 |
| Q16 | Có làm màn hình Ma trận phân quyền không | Có, bản chỉ đọc sinh thẳng từ mã nguồn — làm trong 3A | 29.08.2026 |
| Q17 | Ai thấy định nghĩa bảng | Cả bộ phận, mọi cấp bậc. Phạm vi theo cấp bậc chỉ áp cho bản ghi trong bảng | 29.08.2026 |
| Q18 | Cấu trúc trường biểu mẫu | Bốn bảng đúng `docs/03` mục 2.2: FieldDef, FormDef, FormField, FormTableLink | 29.08.2026 |
| Q19 | Mức chi tiết của phân quyền — FR-8.4 | Cấp thêm cho từng người hoặc từng team, cộng vào phạm vi cấp bậc | 29.08.2026 |
| Q20 | K11 và K12 | Đã xong ở 3B: màn hình điền biểu mẫu, và quyền sửa ô tính qua `grant_service.can_edit_record` | 29.08.2026 |
| Q21 | Nội dung báo cáo hằng ngày lưu ở đâu | Trong `DataRecord` do biểu mẫu sinh ra; `DailyReport` chỉ giữ ai nộp, ngày nào, lúc nào — ADR-008 | 29.08.2026 |
| Q22 | Dựng vỏ hết màn hình trước hay làm từng giai đoạn | Làm từng giai đoạn, mỗi màn hình chạy thật rồi mới sang màn tiếp | 29.08.2026 |
| Q23 | Thị trường thật — N5 | Ba nước: Hoa Kỳ, Canada, Philippines. Ô chọn cố định, khai một chỗ trong `orders/constants.py` | 29.08.2026 |
| Q24 | Sáu trường không có trong bảng vận đơn — N4 | Thêm sáu cột vào bảng vận đơn. Vận đơn cần liên lạc được với khách khi giao hỏng | 29.08.2026 |
| Q25 | BLACK LIST — G1 | Cờ đánh dấu trên khách hàng kèm lý do. Lên đơn cho khách trong danh sách đen thì **cảnh báo, không chặn** — chưa có yêu cầu nào cho chặn | 29.08.2026 |
| Q26 | Trạng thái vận chuyển và thanh toán — G2 | Bộ phận Vận đơn sửa thẳng trên bảng, dùng lại chức năng sửa ô của Giai đoạn 3. Không viết màn hình riêng | 29.08.2026 |
| Q27 | Dòng trên bảng động thuộc bộ phận nào | Bộ phận **sở hữu bảng**, không phải bộ phận người ghi. Thêm cờ `is_shared` cho bảng là hàng đợi việc chung | 29.08.2026 |
| Q28 | Ô "Có chỉ mục" trong bản dựng — K15 | Bỏ. Chỉ mục suy ra từ nhãn ý nghĩa, không phải lựa chọn của người dùng — ADR-001 | 29.08.2026 |
| Q29 | Cột "Chỉ mục GIN" trên danh sách bảng | Bỏ. Mọi bảng động đều có chỉ mục GIN trên cột JSON, hiện lên không nói thêm được gì | 29.08.2026 |
| Q30 | Ngưỡng bao phủ kiểm thử — K5 | Đo bằng `pytest-cov` để biết chỗ hổng, **không đặt ngưỡng chặn**. Ngưỡng đẻ ra bài kiểm viết cho đủ số | 29.08.2026 |
| Q31 | Kiểm giao diện tự động tới đâu | Ở mức HTML, không thêm thư viện trình duyệt. Phần cần trình duyệt thật thì bấm tay | 29.08.2026 |
| Q32 | Ai vào được màn hình Lên đơn | Chỉ bộ phận Sale, theo ma trận kiểm chéo `docs/04` mục 3. Thêm bộ lọc bộ phận cho `NavItem` và `assert_departments` | 29.08.2026 |
| Q33 | Ai vào được màn hình Quản lý biểu mẫu | Manager trở lên. Nhân viên điền biểu mẫu qua màn hình Nộp báo cáo ngày | 29.08.2026 |
| Q34 | Điều hướng sau đăng nhập theo bộ phận — K18, FR-1.6, `AC-1.7` | **Bỏ.** Tất cả đăng nhập đều vào trang tổng quan chung, không nhảy thẳng vào chỗ làm việc — phân quyền đã ẩn các tính năng ngoài phận sự nên không cần | 03.09.2026 |
| Q35 | Nguồn số liệu của báo cáo tổng hợp | Chọn đúng **một** bảng trong phạm vi quyền qua ô "Nguồn số liệu" (thay ô "Bộ phận" của bản dựng). Không cộng gộp nhiều bảng — doanh số trên Báo cáo Marketing và Bảng vận đơn ghi cùng một khoản bán, cộng lẫn là đếm trùng | 03.09.2026 |
| Q36 | Cách nhóm theo thị trường | **Hoãn** — người dùng chốt chưa quan trọng, hỏi lại sau (N9). Màn hình giữ tab Theo thị trường kèm ghi chú chờ chốt nguồn, không có bảng số; `AC-5.1` giữ trong danh sách hoãn | 03.09.2026 |
| Q37 | Bảng tính lưu dữ liệu ở đâu | **Dùng chung một cơ sở dữ liệu** — lưới đọc ghi thẳng dòng của bảng vận đơn, không có bảng riêng, không đồng bộ hai chiều — ADR-009 | 03.09.2026 |
| Q38 | Bảng tính chạy ở đâu | **Dịch vụ riêng trong cùng kho mã** — container `bangtinh` cùng image, settings `knjsc.settings.bangtinh`, cổng 8021, tương lai subdomain chia sẻ phiên đăng nhập — ADR-009 | 03.09.2026 |
| Q39 | Số lượng sản phẩm trên bảng vận đơn | **Mỗi sản phẩm một cột** như tệp thật (`sl_<mã sản phẩm>`), tự sinh từ danh mục sản phẩm đang bán, lên đơn điền tự động | 03.09.2026 |
| Q40 | Trạng thái vận đơn và thanh toán | **Đúng danh sách của tệp thật**: tám trạng thái vận đơn, ba trạng thái thanh toán; nhãn cũ đổi bằng tệp chuyển đổi `orders/0002` có chiều ngược | 03.09.2026 |
| Q41 | Tiền tệ | Thêm **CAD** và **PHP** — tệp thật ghi "Giá tiền(CAD)"; ba thị trường ba đồng tiền cộng VND | 03.09.2026 |
| Q42 | Bảng vận đơn sửa ở đâu — sửa Q26 | **Chỉ xem ở Bảng dữ liệu, sửa ở Bảng tính.** `GRID_ONLY_TABLES` trong settings, kiểm ở máy chủ; dịch vụ `bangtinh` để rỗng — AC-11.7 | 03.09.2026 |
| Q43 | Tệp vận đơn thật | **Ẩn danh hoá rồi đưa vào kho** — `scripts/an-danh-vandon.py` → `docs/tham-khao/vandon-mau.xlsx`; bản gốc chỉ ở `storage/`, không vào git. Là thước đo của AC-11.9 | 03.09.2026 |
| Q44 | Công cụ kiểm thử trình duyệt và tải — sửa Q31 | **Thêm Playwright và Locust, chỉ trong `requirements-dev.txt`**, không vào image chạy thật. K6 đóng ngày 03.09.2026 khi `tests/perf/locustfile.py` chạy được và tự chấm | 03.09.2026 |
| Q45 | Ai được nhập tệp Excel vào bảng; sao lưu ở giai đoạn nào | Quản lý trở lên của bộ phận sở hữu bảng hoặc người được cấp quyền **Sửa**; sao lưu thuộc **Giai đoạn 7**; thứ tự làm 7A → 7B → 7C → 7D | 03.09.2026 |
| Q46 | Bảng tính áp cho bảng nào — sửa ADR-009 mục 1 | **Mọi bảng trong phạm vi quyền** ở `/bang-tinh/<mã>/`; `/bang-tinh/` mặc định mở bảng vận đơn; ngoài phạm vi 404 như Bảng dữ liệu; phần riêng của vận đơn bật theo `is_waybill`; luật hai dịch vụ giữ nguyên — ADR-010 | 04.09.2026 |
| Q47 | Ai thêm được dòng thẳng trên lưới (dòng trống cuối lưới) | Cùng bộ phận sở hữu bảng (mọi cấp), hoặc cấp quyền Sửa, hoặc Admin — `can_create_record`; bảng chỉ xem ở dịch vụ này thì không — AC-11.14 | 04.09.2026 |
| Q48 | Cột khoá | `ColumnDef.is_key`, mỗi bảng một cột, Manager đặt trong Sửa cột, bảng vận đơn lấy Mã đơn; ô cột khoá có nút ⌕ lọc theo giá trị — AC-11.16 | 04.09.2026 |
| Q49 | Định dạng ô lưu ở đâu — sửa ADR-002 phần "Mất gì" | **Cơ sở dữ liệu** (`DataRecord.style`), mọi người cùng thấy; sổ giá trị đóng (đậm, sáu màu nền, cỡ 10–18, căn lề), không nhận CSS tự do; quyền bằng quyền sửa ô — AC-11.15, ADR-010 | 04.09.2026 |
| Q50 | "Tạo folder" nghĩa là gì | **Thư mục chứa bảng**, phẳng, thuộc bộ phận, model ở `forms_builder` (không ở `crm` vì ADR-004); Manager bộ phận quản lý; chỉ sắp xếp thanh bên, không ảnh hưởng phạm vi — AC-11.17 | 04.09.2026 |
| Q51 | Bảng tính nhìn và thao tác thế nào | **Y hệt bảng tính KN Demo** về cách nhìn và cách thao tác (ảnh `docs/tham-khao/kn-demo/`), trên nền dữ liệu KNJSC giữ nguyên; làm trên nhánh riêng `claude/bang-tinh-nhu-kn-demo`; bảng "không làm" ghi ở ADR-011 (công thức, tab là trang, chèn hàng giữa, chiều cao dòng, cột trống gõ được) | 04.09.2026 |
| Q52 | Ai xoá được dòng trên lưới | **Đúng bằng quyền sửa dòng** — `grant_service.can_delete_record` gọi `can_edit_record`, đặt tên riêng để sau này tách được mà không phải đổi mô hình quyền; xoá là xoá mềm, Ctrl+Z khôi phục — AC-11.21, ADR-011 | 04.09.2026 |
| Q53 | Bấm một lần vào ô là gì | **Chọn ô**, không mở sửa; bấm đúp, Enter, F2 hoặc gõ chữ mới sửa — như demo và Excel, không thế thì không kéo chọn vùng được; thay cách "bấm ô là sửa" của ADR-009 — AC-11.25, ADR-011 | 04.09.2026 |

---

## 3. Ý tưởng cho giai đoạn sau

Những thứ đáng làm nhưng chưa tới lượt.

| # | Ý tưởng | Ghi chú |
|---|---|---|
| S1 | Đồng bộ hai chiều giữa đơn hàng và bảng vận đơn | Cần xử lý xung đột khi hai bên cùng sửa |
| S2 | Cho phép cấp trên chia sẻ quyền xem cho cấp dưới | Khung phạm vi đã thiết kế sẵn chỗ mở rộng |
| S3 | Thông báo chủ động khi có việc cần xử lý | Cần tầng dịch vụ tách khỏi giao diện |
| S4 | Kênh báo sự cố cho nhân viên không có tài khoản | Biểu mẫu công khai, người quản lý xử lý |
| S5 | Bảng tổng hợp dạng xoay chiều | Chưa rõ nhu cầu thật |
| S6 | Nhiều người cùng sửa một bảng theo thời gian thực | Phức tạp, cần đánh giá lại nhu cầu |
| S7 | Thư mục lồng nhau trên Bảng tính | Chưa ai cần; thêm sau chỉ là FK `parent` trên `Folder` — ADR-010 |
| S8 | Xuất Excel mang theo định dạng ô (đậm, màu nền) | `export_service.build_workbook` chưa đọc `DataRecord.style`; làm khi có người hỏi |
| S9 | Kéo đổi chiều cao dòng trên Bảng tính | Dòng đổi chỗ khi sắp xếp và phân trang nên chiều cao theo chỉ số dòng vô nghĩa; nếu cần thì lưu theo bản ghi như `style` — ADR-011 |
| S10 | Công thức gõ ở thanh công thức của Bảng tính | Ô `fx` đã có, gõ `=` đang báo chưa hỗ trợ; chờ "cách thứ ba" người dùng nói tới sau ADR-006; khi có thì cắm vào đúng chỗ này — ADR-011 |

---

## 4. Rủi ro đã nhận diện

| # | Rủi ro | Mức ảnh hưởng | Cách giảm |
|---|---|---|---|
| R1 | Dữ liệu cũ dần vì phụ thuộc người dùng cập nhật | Cao | Nhắc nhở, và làm sao cho nhập liệu nhanh hơn cách hiện tại |
| R2 | Chỉ một người biết vận hành hệ thống | Cao | Sổ tay vận hành đủ chi tiết để người khác tiếp nhận |
| R3 | Phạm vi phình ra trong quá trình làm | Trung bình | Danh sách ngoài phạm vi trong tài liệu, thay đổi phải được duyệt |
| R4 | Bảng do người dùng tự tạo làm chậm truy vấn | Trung bình | Tách cột có nhãn ý nghĩa ra cột riêng có chỉ mục |
| R5 | Người dùng thấy hệ thống chậm hơn cách làm cũ nên không dùng | Cao | Đo thời gian thao tác thực tế, so với cách làm hiện tại |
| R6 | Bản sao lưu chưa từng được phục hồi thử | Cao | Thử phục hồi trước khi bàn giao |
| R7 | Nghiệm thu dồn về một đợt cuối nên sai về giao diện và trải nghiệm phát hiện muộn, lúc đó sửa đắt hơn | Cao | Bám sát bản dựng ở `prototype/` làm chuẩn giao diện; mỗi giai đoạn vẫn chạy thử tay và báo cáo, chỉ không đòi người dùng nghiệm thu |

---

## 5. Câu hỏi cần hỏi người dùng

Những câu chưa có đáp án, cần hỏi trực tiếp người sử dụng.

| # | Câu hỏi | Hỏi ai |
|---|---|---|
| H1 | Trong tệp Excel hiện tại, anh chị có gõ công thức không? Gõ những gì? | Vận đơn, Marketing |
| H2 | Anh chị có hay kéo góc ô để điền cả cột không? | Vận đơn, Marketing |
| H3 | Anh chị có dán dữ liệu từ tệp Excel khác vào không? | Vận đơn, Marketing |
| H4 | Mỗi ngày mất bao lâu cho việc nhập liệu và tổng hợp thủ công? | Cả ba bộ phận |
| H5 | Lần gần nhất cần tìm một thông tin mà tìm không ra là khi nào? | Cả ba bộ phận |
| H6 | Một bộ phận hiện có mấy team, ai phân team? | Quản lý |

---

## 6. Hiện trạng màn hình — chưa nghiệm thu

Người dùng nêu ngày 29.08.2026: **hiện quá thiếu màn hình để đánh giá được
giao diện và trải nghiệm.** Không nghiệm thu từng phần nữa; dồn về một đợt
kiểm thử toàn diện khi đủ màn hình. Mốc cụ thể xem **V4**, kế hoạch kiểm thử
xem **V5** — cả hai đều chưa chốt.

> **Chưa có gì được nghiệm thu.** Giai đoạn 0 tới 5 đều đã giao và đã chạy
> kiểm thử tự động, nhưng **người dùng chưa trực tiếp thử màn hình nào**. Mọi
> phần trăm trong `dashboard-tien-do.html` là tiến độ *đã làm*, không phải
> tiến độ *đã nghiệm thu*. Hai con số đó có thể lệch nhau, và chỉ đóng lại
> được sau đợt kiểm thử ở V4.

| Giai đoạn | Đã giao | Người dùng đã thử |
|---|---|---|
| 0 · Tài liệu và quyết định | ✓ | — |
| 1 · Nền móng | ✓ | Chưa |
| 2 · Cơ cấu tổ chức và giao diện chung | ✓ | Chưa |
| 3 · Biểu mẫu và bảng động | ✓ | Chưa |
| 4 · Báo cáo hằng ngày | ✓ | Chưa |
| 5 · Lên đơn và vận đơn | ✓ | Chưa |
| 6 · Báo cáo tổng hợp | ✓ | Chưa |
| 7 · Nhập xuất, sao lưu, Bảng tính, kiểm thử toàn diện, Bảng tính mọi bảng | ✓ | Chưa — kịch bản ở `docs/07` |

Bản dựng giao diện tĩnh ở `prototype/` là chuẩn để đối chiếu. Nó có 10 màn
hình mà bản Django chưa có; bảng dưới đây theo dõi việc lấp dần.

| Màn hình trong bản dựng | Giai đoạn | Trạng thái |
|---|---|---|
| Bảng vận đơn — bảng dữ liệu chung | 3A | Đã có, dưới tên `/bang/<mã>/` |
| Ma trận phân quyền | 3A | Đã có, bản chỉ đọc |
| Quản lý biểu mẫu | 3B | Đã có |
| Trình tạo biểu mẫu | 3B | Đã có |
| Nộp báo cáo ngày | 4 | Đã có |
| Lịch sử báo cáo | 4 | Đã có |
| Lên đơn | 5 | Đã có |
| Báo cáo tổng hợp | 6 | Đã có — tab Theo thị trường treo ghi chú chờ N9, Q36 |
| Bảng tính | 7 | Đã có — lưới cho **mọi bảng** ở `/bang-tinh/<mã>/` (ADR-010): viền ô, dòng trống, cột khoá, thanh lọc bên trái, thanh công cụ, định dạng ô, thư mục; bảng vận đơn vẫn sửa ở dịch vụ `bangtinh` (ADR-009); nhìn và thao tác như bảng tính KN Demo — chọn vùng, dán từ Excel, kéo điền, chuột phải, hoàn tác, hộp lọc giá trị, tự cập nhật (ADR-011, nhánh `claude/bang-tinh-nhu-kn-demo`) |
| Bảng tính, màn hình chi tiết | 7 | Không làm engine công thức (ADR-009); phần thanh công cụ định dạng của bản dựng đã có lại dưới dạng sổ đóng (ADR-010); thanh công cụ và thanh công thức theo KN Demo (ADR-011), công thức chờ S10 |

**Thiếu sót đã biết, không phải màn hình riêng nhưng ảnh hưởng trải nghiệm:**

| # | Nội dung | Giai đoạn xử lý |
|---|---|---|
| 1 | ~~Bảng động chưa có chỗ thêm dòng mới~~ — xong ở 3B, màn hình điền biểu mẫu | — |
| 2 | Chưa có trang lỗi 404 và 500 tiếng Việt — K9 | Chưa xếp |
| 3 | Giao diện chưa kiểm trên điện thoại và máy tính bảng — NFR-7, AC-10.4 | 8 |
| 4 | ~~Điều hướng sau đăng nhập theo bộ phận — FR-1.6~~ — bỏ theo Q34, ngày 03.09.2026 | — |
| 5 | Chưa có dữ liệu mẫu đủ lớn để thấy bảng chạy thật thế nào | 8, `seed_perf.py` |

**Khi tới đợt kiểm thử toàn diện, chạy theo `docs/04` mục 3 và mục 10:** ma
trận kiểm chéo chín vai trò, các tiêu chí thủ công `AC-8.1`, `AC-10.3`,
`AC-10.4`, `AC-5.6`, và đối chiếu từng màn hình với bản dựng ở `prototype/`.

---

## Nhật ký cập nhật

| Ngày | Nội dung |
|---|---|
| (điền) | Tạo tài liệu |
| 28.08.2026 | Rà soát Giai đoạn 1 và 2 — 19 phát hiện. Sửa 18, hoãn K7. Thêm K7–K10 và N5–N8 |
| 29.08.2026 | Chốt K1, K2, K3 và N8 — gỡ hết điểm chặn Giai đoạn 3. Ghi ADR-006 và ADR-007 |
| 29.08.2026 | Xong Giai đoạn 3 phần A. Chốt Q14 tới Q17. Thêm AC-3.8, AC-7.10 tới AC-7.12 vào `docs/04`. Mở K11 và K12 |
| 29.08.2026 | Người dùng nêu: quá thiếu màn hình để nghiệm thu. Hoãn nghiệm thu tới một đợt toàn diện — mở V4 và R7, thêm mục 6 theo dõi hiện trạng màn hình |
| 29.08.2026 | Xong Giai đoạn 4 — báo cáo hằng ngày. Chốt Q21 và Q22. Ghi ADR-008 |
| 29.08.2026 | Thêm lệnh `manage.py du_lieu_mau` — máy mới chạy một lệnh là có 12 tài khoản và dữ liệu thật để dùng thử. Trước đó `docker compose up` trên máy sạch cho ra hệ thống không đăng nhập được, và việc số 1 trong danh sách kiểm thủ công **không làm được** dù tôi đã ghi là "chạy được" |
| 29.08.2026 | Cho một tác nhân đóng vai phiên mới đọc kho mã, tìm ra 11 chỗ tài liệu sai hoặc thiếu. Sửa hết: bảng tiến độ báo "mã nguồn chưa bắt đầu" và chỉ hiện tới GĐ 1; số tiêu chí ghi 47 và 58 trong khi thật là 68; `docs/06` ghi 28/40 trong khi thật là 49/61; mục 6 kẹt ở GĐ 4; `docs/05` tả tính năng chưa có như đã chạy; thiếu ADR-008; K1–K4 vẫn ghi là đang chờ. Thêm bốn bài canh con số |
| 29.08.2026 | Lập kế hoạch kiểm thử toàn diện — `docs/06`. Từ 249 lên **779 bài đạt**, bao phủ 83%. Thêm bốn tầng: tệp chuyển đổi, kiểm khói, ma trận 35 ô, truy vết. Tìm ra 4 lỗi phân quyền, 1 lỗi tiền, 3 lỗi giao diện. Chốt Q30 tới Q33, đóng K5 và K15, mở K17 |
| 29.08.2026 | Đối chiếu toàn bộ 8020 với 8010 theo từng trường. Bổ sung: cột Doanh số ở Lịch sử báo cáo, cột Người tạo và Cập nhật ở Quản lý biểu mẫu, Giá trị mặc định cho định nghĩa trường, cột tính sẵn hiện ngay trên biểu mẫu. Làm K15 thành bài kiểm thật. Chốt Q28 Q29, mở K16 |
| 29.08.2026 | Người dùng đối chiếu màn Lên đơn với bản dựng: thiếu cột Thành tiền, khối Tóm tắt, khối Sau khi lưu. Phát hiện thêm `.luoi-2cot` không tồn tại nên bốn màn hình hiện một cột, và ba lớp `.o-tinh` `.o-loi` `.o-trong-bang` chưa có kiểu dáng. Đã bổ sung hết, mở K15 |
| 29.08.2026 | Xong Giai đoạn 5 — lên đơn và vận đơn. Chốt thêm Q27 sau khi chạy thử tay phát hiện Vận đơn không thấy dòng nào |
| 29.08.2026 | Bàn Giai đoạn 5. Chốt Q23 tới Q26 — gỡ N4, N5, G1, G2 |
| 29.08.2026 | Người dùng xác nhận chưa thử màn hình nào, chưa nghiệm thu được. Kế hoạch kiểm thử cũng để sau — mở V5, ghi bảng đã giao / đã thử vào mục 6 |
| 29.08.2026 | Xong Giai đoạn 3 phần B, khép lại Giai đoạn 3. Chốt Q18 tới Q20, đóng K11 và K12, mở K13 và K14. Bỏ model `Position` khỏi tài liệu vì nó không tồn tại |
| 03.09.2026 | Chốt Q34 — bỏ K18: tất cả đăng nhập vào trang tổng quan chung, phân quyền đã ẩn tính năng ngoài phận sự. Gạch FR-1.6 và AC-1.7 khỏi `docs/02` và `docs/04`, còn 67 tiêu chí. K9 (trang lỗi 404 và 500) người dùng chốt chưa phải lúc, giữ trong backlog |
| 03.09.2026 | Xong Giai đoạn 7 phần A — nhập xuất Excel và tác vụ nền: `core/excel.py`, `BackgroundJob`, luồng nhập bốn bước có xem trước và tiến độ, xuất kèm bộ lọc, tệp lớn chạy nền giữ 24 giờ. Gỡ `AC-7.5` tới `AC-7.9` khỏi HOAN. Ẩn danh tệp vận đơn thật (Q43). Sửa Q26 thành Q42 |
| 03.09.2026 | Xong Giai đoạn 7 phần B — sao lưu `pg_dump` hằng đêm giữ 30 bản, thất bại thì thư cho người vận hành; lệnh `sao_luu`, `phuc_hoi --toi-chac-chan`; service `beat` và `bangtinh` trong compose. Gỡ `AC-10.6` khỏi HOAN, mở K21 |
| 03.09.2026 | Xong Giai đoạn 7 phần C — Bảng tính vận đơn theo tệp thật (ADR-009): lưới lọc theo cột, sửa ô tại chỗ có danh sách chọn, Lọc trùng, tô màu Hủy/Hoàn, cột số lượng theo sản phẩm; tám trạng thái mới và tiền tệ CAD/PHP (`orders/0002`); dịch vụ `bangtinh` cổng 8021. Thêm `docs/04` mục 11 (AC-11.1 → 11.11), đánh số lại mục 12–14. Chốt Q37 tới Q45, mở K22 |
| 03.09.2026 | Xong Giai đoạn 7 phần D — kiểm thử toàn diện: Playwright (bàn phím, hộp lọc, cột cố định, 390px không tràn ngang, nhập→xuất→nhập lại qua giao diện), `seed_perf` 50.000 dòng và bài hiệu năng dưới 2 giây, Locust 50 người tự chấm p99, ma trận phân quyền 35 → 45 ô. HOAN chỉ còn `AC-5.1`: 70 trên 70 tiêu chí tự động có bài kiểm. Viết `docs/07-kich-ban-nghiem-thu.md`, cập nhật docs/03, 05, 06; đóng K6, mở K19, K23 (hộp lọc trong Playwright), K24 (12 truy vấn trên 50.000 dòng) — hai bài đó đánh dấu xfail vì người dùng cần demo gấp; bảng tiến độ sang GĐ 8 |
| 03.09.2026 | Người dùng phàn nàn mở `localhost:8020` không lên sau khi đổi phiên làm việc. Nguyên nhân: container không tự bật lại sau khi tắt máy, và mã mới chưa kéo về. Thêm `restart: unless-stopped` cho bốn dịch vụ compose, và `scripts/cap-nhat-local.sh` + `.bat` — một lệnh kéo mã, dựng lại, bảo đảm dữ liệu mẫu |
| 03.09.2026 | Xong Giai đoạn 6 — báo cáo tổng hợp: `reports/aggregations.py` dịch nhãn ý nghĩa sang phép tính, màn hình ba cách nhóm kèm lọc, dòng tổng cộng, bốn ô số và xuất Excel có ghi nhật ký (P5). Chốt Q35 (ô chọn một bảng nguồn) và Q36 (hoãn tab thị trường), mở N9 và N10. Gỡ `AC-5.2` tới `AC-5.5` khỏi HOAN — còn 8 tiêu chí hoãn, 53 trên 61 đã có bài kiểm. Sửa luôn: phân trang giữ tham số lọc (`qs_loc`), đệm phạm vi quyền theo lượt yêu cầu để màn hình đứng dưới trần 10 lệnh truy vấn |
| 04.09.2026 | Người dùng dựng ở máy nhà, gặp lần lượt: Docker chưa mở nên 8020 không lên; gõ `/bangtinh` thiếu gạch nên 404; rồi màn hình Bảng tính 404 vì "Chưa có bảng vận đơn". Người dùng hỏi đúng: *vì sao đã viết mã rồi mà còn phải chạy lệnh tay?* Chốt: bảng vận đơn là bảng động nên `migrate` không sinh ra, nhưng mã đòi nó tồn tại, vậy `entrypoint.sh` phải tự gọi `tao_bang_van_don` sau `migrate`. Lệnh này giờ tự tạo bộ phận Vận đơn trên máy sạch (trước đó chạy trên máy sạch thì đổ lỗi thiếu bộ phận — phát hiện khi thử thật). Gộp vào `scripts/cap-nhat-local.sh` và `.bat` phần tự mở Docker Desktop, đợi web lên và mở trình duyệt — một lệnh là chạy. `du_lieu_mau` vẫn phải chạy tay vì tài khoản mẫu không được tự sinh trên máy chủ thật |
| 04.09.2026 | Người dùng gửi ảnh Lumi OMS, yêu cầu Bảng tính như CRM chuyên biệt. Chốt bốn câu (Q46 → Q50) rồi làm Giai đoạn 7 phần E, ADR-010: lưới cho mọi bảng (A), định dạng ô lưu DB (B), thư mục chứa bảng (C). Thêm `forms_builder/0006` (`is_key`, `style`) và `0007` (`Folder`, `TableDef.folder`); `export_service` có sổ builder để Bảng tính xuất đúng lưới kể cả `trung=` và `sp=` (lỗ hổng cũ: xuất bỏ qua `trung=1`). Phát hiện và sửa lỗi tiềm ẩn: màn hình Sửa cột không lưu thay đổi vì ModelForm đã ghi vào instance trước khi dịch vụ so cũ với mới. AC-11.12 → 11.18; 85 tiêu chí. Ngân sách truy vấn `/bang-tinh/<mã>/` đặt 14 (thanh bên thêm hai lệnh trên K24). Bài Playwright thêm hai: dòng trống + ⌕, chọn vùng + định dạng |
| 04.09.2026 | Người dùng kéo nhánh về máy nhà, mở 8021 gặp `column forms_builder_tabledef.folder_id does not exist`: mã mới vào container qua bind mount nên container không dựng lại, `migrate` trong entrypoint không chạy. Sửa `cap-nhat-local.sh` và `.bat` gọi tường minh `migrate` và `tao_bang_van_don` sau `up` |
| 04.09.2026 | Trên Windows, cả bốn container `Restarting` với `exec /entrypoint.sh: no such file or directory`: git checkout đổi `entrypoint.sh` sang CRLF, `#!/bin/sh\r` không có trình thông dịch. Sửa hai tầng: `.gitattributes` giữ LF cho `.sh .py .html .css .js` (gộp ý từ nhánh `claude/project-status-progress-7ajcqg`), và Dockerfile `sed -i 's/\r$//'` trước `chmod` để image dựng đúng dù git cấu hình thế nào |
| 04.09.2026 | Người dùng cập nhật xong vẫn thấy Bảng tính vỡ bố cục: trình duyệt dùng `bang-tinh.css` cũ trong bộ đệm (cùng tên với tệp đã có trên `main`). Thêm `?v=<mốc sửa tệp tĩnh>` vào mọi đường dẫn CSS và JS (`core/context_processors.PHIEN_BAN_TINH`) — đổi mã là trình duyệt tự tải mới, không phải Ctrl+F5 |
| 04.09.2026 | Người dùng thêm hai yêu cầu: (1) kéo đổi độ rộng từng cột và tự quyết thứ tự cột A B C; (2) Bảng tính phải là một trang toàn màn hình khác hẳn, chức năng chính là lưới. Làm ngay trong 7E: khung riêng `crm/base_bang_tinh.html` (không thanh bên hệ thống, menu ☰), chữ cột A B C, kéo mép tiêu đề đổi rộng, kéo thả tiêu đề đổi thứ tự, nút Đặt lại cột — ba thứ nhớ trên trình duyệt theo mã bảng (ADR-010 mục 8, 9). Sửa AC-11.18 |
| 04.09.2026 | Người dùng gửi gói KN Demo (`Kim_Ngan_DEMO.rar`), chốt *"tạo nhánh riêng và làm cái view y hệt như ảnh"*. Nhánh `claude/bang-tinh-nhu-kn-demo` tách từ đầu nhánh 7E. Đọc trọn mã demo: bảng tính JSON tự viết, công thức tính ở trình duyệt, tự lưu cả tài liệu, không phân trang — KNJSC chỉ lấy cách nhìn và thao tác (ảnh ở `docs/tham-khao/kn-demo/`). Giai đoạn 1 (ADR-011): khung tối viền vàng 48px, thanh công cụ đúng thứ tự demo, thanh công thức có ô địa chỉ `A1`, cột số dòng 46px, hàng chữ cột có nút ▼ và mép kéo, hàng tên cột là hàng 1 (vận đơn xanh, bảng khác vàng), cột trống tới Z, chân trang có tab bảng và `+100 dòng`, trạng thái lưu, nút ⛶ toàn màn hình, bấm một lần là chọn / bấm đúp hoặc gõ chữ là sửa, thanh bên ẩn mặc định. Sổ định dạng mở rộng theo demo: nghiêng, gạch chân, gạch ngang, xuống dòng, viền, bảng 40 màu chữ và nền (`m01…m40`, CSS sinh bằng `scripts/sinh-css-mau.py`), cỡ 10–28, định dạng số. Sửa nhân tiện: `tests/test_hieu_nang.py` để lại bộ phận và bảng giả trong cơ sở dữ liệu kiểm thử (xoá mềm vẫn chiếm tên unique) làm mọi bài chạy sau đỏ khi chạy cả bộ kể cả `cham` — dọn thật ở teardown |
| 04.09.2026 | Giai đoạn 2 của ADR-011 trên nhánh `claude/bang-tinh-nhu-kn-demo`: kéo chuột chọn vùng (ô địa chỉ hiện `C3:F7`, số dòng và chữ cột tô sáng, thống kê Tổng · TB · Số ô), bấm số dòng chọn hàng, chữ cột chọn cột, góc chọn cả trang; Shift+mũi tên, Ctrl+A; cắt/chép/dán qua clipboard hệ thống (TSV — dán từ Excel được, dán nội bộ mang theo định dạng, lặp khối khi vùng là bội số, tràn xuống dòng trống thì tạo bản ghi); tay kéo điền bốn hướng (số cách đều thì tiếp chuỗi, không thì lặp khối); Delete xoá nội dung; hoàn tác/làm lại 100 bước phía trình duyệt (giá trị và định dạng). Máy chủ: `record_service.update_cells` + `POST luu-o/` được cả hoặc không gì, `CellError` chỉ đúng ô, quyền kiểm từng dòng, ngoài phạm vi 403 có nhật ký; AC-11.19, AC-11.20. Ba lỗi ngầm của htmx 2 gặp trên đường: (1) `afterRequest` bắn trước khi thay ô — phải chờ `afterSettle`; (2) phần tử mới trùng id với phần tử cũ thì trong lúc settle mang tạm thuộc tính cũ — trình sửa ô không được mang id; (3) `processNode` chạy sau settle 20ms nên `requestSubmit()` sớm hơn là trình duyệt tự nộp biểu mẫu — `guiSua` chờ hết `htmx-settling`. Và: mảnh HTML có `<td>` đứng trước `<tr>` thì trình duyệt bỏ `<tr>` — phản hồi luu-o trả dòng trước ô |
| 04.09.2026 | Giai đoạn 3 của ADR-011: menu chuột phải đúng nhãn demo (Cắt · Sao chép · Dán · Chèn N hàng trống · Xoá N hàng · Chèn N cột trái/phải · Xoá N cột · Xoá nội dung · Xoá định dạng; mục không có quyền mờ đi); xoá dòng là xoá mềm sau hộp xác nhận, Ctrl+Z khôi phục về chỗ cũ (`xoa-dong/`, `khoi-phuc-dong/`, `record_service.restore_record`, quyền `can_delete_record` = quyền sửa dòng — Q52); Manager của bộ phận sở hữu chèn/bỏ cột ngay trên lưới (`them-cot/`, `xoa-cot/`, `table_service.insert_columns`, `removable_reason`; cột khoá, vế cột tính sẵn, cột hệ thống vận đơn thì giữ; `can_manage_columns`); hộp lọc cột theo demo (tên cột · số giá trị, ô tìm, danh sách giá trị kèm số cho mọi kiểu cột, Điều kiện khác gập, Chọn tất cả · Không chọn · Xóa lọc · Áp dụng); lưới hỏi `moi-nhat/` mỗi `GRID_POLL_SECONDS` giây khi rảnh, có gì mới thì nạp lại thân bảng và toast. AC-11.21 → AC-11.26, 93 tiêu chí, 83 trên 84 tự động có bài kiểm. Nhãn "Bỏ chọn" của demo đổi thành "Không chọn" vì luật nút nguy (test_giao_dien) bắt chữ "Bỏ"; các mục Xoá trong menu mang `nut-nguy` (chữ đỏ) theo cùng luật |
| 04.09.2026 | Giai đoạn 4 của ADR-011 — tài liệu: viết `quyet-dinh/011-bang-tinh-theo-mau-kn-demo.md` (kèm bảng "không làm"), thêm 009/010/011 vào danh sách ADR; `docs/02` FR-7.9 → FR-7.12; `docs/03` §4.6 thêm các dòng lưu nhiều ô, xoá/khôi phục dòng, chèn/bỏ cột, hộp lọc giá trị, tự cập nhật, hoàn tác, cột trống, hai tệp JS; `docs/04` AC-11.27 (thủ công, đối chiếu ảnh) — 94 tiêu chí; `docs/05` A8 viết lại theo giao diện mới; `docs/06` bảng thủ công thêm AC-11.18 (thiếu từ 7E) và AC-11.27; `docs/07` thêm bước dán từ Excel, kéo điền, chuột phải xoá hàng, chèn cột, hộp lọc, tự cập nhật, và sửa các bước cũ theo giao diện mới (bấm đúp mới sửa, Nhập tệp trong ⋯, Tải Excel ở thanh trên, Bộ lọc mở thanh bên); chốt Q51 → Q53, mở S9, S10; dashboard 7F |
| 05.09.2026 | Gộp PR #4 (Giai đoạn 7E, ADR-010) vào `main` bằng merge commit `3facc87`, giữ nguyên SHA và giữ nhánh 7E. PR #5 (7F, ADR-011) đổi base về `main`, vẫn mở trên nhánh riêng theo ý anh/chị — chờ nghiệm thu `docs/07` rồi mới gộp. Nhánh 7F gộp `main` vào để không tụt sau |
