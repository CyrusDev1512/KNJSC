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

> Cập nhật ngày 06.09.2026. Giai đoạn 7 phần E (ADR-010) đã vào `main` qua
> PR #4. Phần F (Bảng tính như KN Demo, ADR-011) và phần G (**KN CRM là app
> riêng**, trang chủ cây Bộ phận ▸ Quý ▸ Tháng, ADR-012) **đã vào `main` qua
> PR #5** tối 06.09; đợt chỉnh sửa KNERP đầu tiên — ô chọn có "Thêm mới…",
> danh tính người điền tự ghi, màu cột và viền ô (ADR-013) — vào qua PR #11;
> đợt thứ hai cùng ngày: **Bảng dữ liệu chỉ để xem với mọi bảng**, gỡ hẳn sửa
> ô ở KN ERP (ADR-015, Q62). **KN CRM đợt 2** (7J, ADR-015: khung sidebar theo
> Teeze, trang chủ tổng quan, Leader như Manager trong bộ phận, tạo bảng/nhập
> tệp/cấp quyền ngay trong KN CRM, logo tự vẽ) vào qua PR #19. Nghiệm thu bấm
> tay theo `docs/07` vẫn chờ anh/chị. **MVP Nội bộ** — Tài liệu, Bảng tin, Công
> việc, Văn hoá, Tài nguyên (ADR-017) — xong ngày 07.09. Rà soát
> lại nhánh ngày 07.09: bốn commit A → D sửa 22 lỗi và điểm yếu, cải tiến giao
> diện, gọn mã dùng chung, thêm bài kiểm và tài liệu; chốt **Q75** (chỉ cấp trên
> ghi nhận cấp dưới), **Q76** (mọi người bán tranh hạng), **Q77** (đồng hạng).
> Nghiệm thu bấm tay theo `docs/07` vẫn chờ anh/chị.
> Mục D chỉ còn `AC-5.1`.

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
định dạng số, hộp lọc theo giá trị, tự cập nhật khi người khác sửa. **KN CRM
là app riêng** (7G, ADR-012): KN ERP không còn lưới, chỉ có mục KN CRM mở tab
mới sang dịch vụ 8021; trang chủ KN CRM là cây Bộ phận ▸ Quý ▸ Tháng ▸ bảng tự
sinh từ cột Ngày, bấm tháng là mở lưới lọc sẵn tháng đó (tháng là góc nhìn,
không tách bảng), quyền theo bảng như cũ. **Chỉnh sửa KNERP 06.09** (ADR-013): mọi cột Chọn một là ô chọn có "＋ Thêm mới…"
cho Manager ở biểu mẫu, báo cáo ngày và Lên đơn; sản phẩm lấy từ
danh mục, Manager thêm tại chỗ; trường Người bán tự ghi tên người điền; Bảng dữ
liệu có viền, tiêu đề xanh lá, màu cột và ngưỡng cảnh báo. **Bảng dữ liệu chỉ để
xem** với mọi bảng (7I, ADR-014): gỡ hẳn đường sửa ô ở KN ERP, sửa số liệu là
việc của KN CRM; luật 13 trong `CLAUDE.md`. **KN CRM đợt 2** (7J, ADR-015): KN CRM
có sidebar theo Teeze (avatar, Trang chủ, Bảng tính gập theo bộ phận, Nhập tệp,
Cấp quyền, Tác vụ nền, KN ERP), trang chủ là tổng quan theo phạm vi, cây tháng
thành mục Bảng tính ở `/thu-muc/`, lưới vẫn toàn màn hình và chỉ lưới có ← (về
thư mục, không về ERP); Leader được như Manager trong bộ phận mình; tạo bảng, sửa
cột kèm cấp quyền, nhập tệp chạy ngay trong KN CRM; logo tự vẽ và favicon.
**Nhóm Nội bộ, bản MVP** (9, ADR-017): Tài liệu chia mục theo bộ phận, Bảng tin có thích, bình
luận, ghim và thiệp sinh nhật tự động, Công việc theo phạm vi cấp bậc, Văn hoá
với ghi nhận một sao, xếp hạng doanh số quy VND và thưởng 5/3/1 sao ngày 1,
Tài nguyên chia mục BM/Via/Page. 126 tiêu chí, 113 trên 114 tự động có bài
kiểm.

**Việc tiếp theo:** **nghiệm thu một đợt theo `docs/07`** — anh/chị bấm tay
từng vai, đánh ☑, gửi danh sách lỗi. Mọi thứ đã ở `main`, các nhánh cũ đã xoá:
máy nhà nháy đúp `KN JSC.bat` (hoặc `scripts\cap-nhat-local.bat main`), rồi bấm
**KN CRM** trên thanh bên (tab mới `localhost:8021/`). Rồi Giai đoạn 8: máy chủ, tên miền con cho KN
CRM, KN ERP dùng tốt trên điện thoại, đo tải trên máy chủ thật (chờ V1).
Với nhóm Nội bộ, bấm thử năm màn hình theo `docs/07` mục 3.1, 3.2, 3.4 và chốt
**N11** (tỉ giá), **N12** (năm giá trị văn hoá).

### A · Nghiệm thu — việc của anh/chị

**Chưa có gì được nghiệm thu.** Giai đoạn 0 tới 5 đều đã giao và toàn bộ bài
kiểm thử tự động đều đạt, nhưng anh/chị **chưa trực tiếp thử màn hình nào**. Phần
trăm trên `dashboard-tien-do.html` là tiến độ *đã làm*, không phải *đã nghiệm thu*.

**Mười tám việc làm được ngay bây giờ — kịch bản từng bước ở `docs/07`:**

| ☐ | Việc | Mã |
|---|---|---|
| ☐ | Thêm team mới, dùng ngay không khởi động lại | `AC-2.4` |
| ☐ | Mở trên điện thoại và máy tính bảng thật | `AC-10.4` |
| ☐ | Cài từ đầu trên máy sạch, chạy tới màn hình đăng nhập | `docs/04` mục 17.1 |
| ☐ | Ba vai trò đăng nhập, chạy trọn quy trình của mình | `docs/04` mục 17.2 |
| ☐ | Thử trên điện thoại và máy tính bảng thật | `docs/04` mục 17.5 |
| ☐ | Ngắt mạng giữa chừng, kiểm thông báo lỗi | `docs/04` mục 17.7 |
| ☐ | Xuất báo cáo tổng hợp, mở bằng Excel, đối chiếu số | `AC-5.6` · `docs/04` mục 17.4 |
| ☐ | Nhập tệp vận đơn thật (`docs/tham-khao/vandon-mau.xlsx`) qua Bảng dữ liệu → Nhập tệp | `docs/04` mục 17.3 |
| ☐ | Sao lưu rồi phục hồi trên máy thử: `scripts/backup.sh`, `scripts/restore.sh --toi-chac-chan` | `AC-10.5` · `docs/04` mục 17.6 |
| ☐ | 50 người đồng thời: `manage.py seed_perf` rồi Locust 1 phút, in ĐẠT | `AC-10.1` |
| ☐ | Bảng tính: cuộn ngang dọc, cột đầu và tiêu đề đứng yên | `AC-11.1` |
| ☐ | Bảng tính trên điện thoại và máy tính bảng thật | `AC-11.11` |
| ☐ | Bảng tính: mọi ô có viền, thanh công cụ đủ mục, ẩn cột nhớ được, thanh bên thu gọn được | `AC-11.18` |
| ☐ | Bảng tính đặt cạnh ảnh `docs/tham-khao/kn-demo/`: khung, thanh công thức, số dòng, chữ cột, cột trống, chân trang, ⛶; kéo chọn vùng, dán từ Excel, chuột phải | `AC-11.27` |
| ☐ | KN CRM: bấm mục trên thanh bên ERP mở tab mới; trang chủ cây Bộ phận ▸ Quý ▸ Tháng; bấm tháng → Mở → lưới lọc tháng → ← về đúng nhánh | `docs/07` mục 3.3 |
| ☐ | KN CRM đợt 2: trang chủ tổng quan có menu trái; Bảng tính → thư mục → Mở → lưới full → ← về thư mục; Leader tạo thư mục, cột, bảng, nhập tệp trong bộ phận mình; Nhập tệp và Cấp quyền trên sidebar | `AC-11.31` → `AC-11.34` · `docs/07` |
| ☐ | Nhóm Nội bộ — Bảng tin, Tài liệu, Công việc, Văn hoá, Tài nguyên — bấm thử theo vai | `docs/07` mục 3.1, 3.2, 3.4 |
| ☐ | Bảng tin trên điện thoại | `AC-13.6` |

**Một việc biết trước là chưa đạt:**

| Việc | Mã | Chờ |
|---|---|---|
| Gặp lỗi hiện thông báo tiếng Việt, không trang trắng | `AC-10.3` | Trang 404 và 500 chưa làm — **K9**, người dùng chốt chưa phải lúc |

### B · Câu hỏi chờ anh/chị quyết

Tám câu này **chặn việc thật**, không phải bàn cho vui:

| # | Câu hỏi | Chặn gì |
|---|---|---|
| **V4** | Mốc nào thì nghiệm thu toàn diện | Cả mục A ở trên |
| **V2** | Ai vận hành hằng ngày sau bàn giao | **K17** — có nên dựng chạy kiểm thử tự động không |
| **V1** | Máy chủ đặt ở đâu | Giai đoạn 8 |
| **N1** | Nộp báo cáo có bắt buộc đúng giờ không | **K16** — cột Trạng thái trên Lịch sử báo cáo |
| **N3** · **N6** | Chăm sóc khách hàng có trong phase 1 không | Biểu mẫu báo cáo CSKH ở Giai đoạn 4 |
| **N7** | Quản trị viên có phải thuộc một bộ phận không | BR-1 đang mâu thuẫn với mã |
| **N11** | Tỉ giá USD, CAD, PHP sang VND cho bảng xếp hạng doanh số — đang tạm 25.400 / 18.500 / 440 | Số trên bảng xếp hạng Văn hoá đúng hay sai; gộp PR #20 |
| **N12** | Năm giá trị văn hoá của công ty — đang tạm Tận tâm, Chính trực, Hợp tác, Sáng tạo, Trách nhiệm | Ghi nhận mang đúng tên giá trị; đổi sau khi có ghi nhận thật thì phải chuyển dữ liệu |

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
| **K25** | Bảng tính (`crm`) chưa đọc `choice_registry.for_column`: ô Chọn một của bảng tự tạo ở đó vẫn là ô chữ, máy chủ vẫn chặn giá trị lạ — một dòng trong `grid_service.choice_list`, giao thread KN CRM | Thấp |
| **K26** | `GRID_ONLY_TABLES` và `is_grid_only` chỉ còn KN CRM dùng sau khi KN ERP gỡ hẳn sửa ô (ADR-014); ở dịch vụ `bangtinh` danh sách đã rỗng — thread KN CRM xem xét bỏ luôn | Thấp |
| **K30** | Tệp tài liệu ở `storage/tai-lieu/` không nằm trong `pg_dump` — phục hồi từ bản sao lưu là mất tệp nếu không chép thư mục đi kèm | Trung bình |
| **K31** | `docs/so-do-kien-truc.html` và sơ đồ trong `docs/kien-truc.md` chưa vẽ năm app Nội bộ | Thấp |
| **K29** | Bài Playwright `test_dong_trong_thanh_dong_that_va_loc_theo_o_khoa` (lưới KN CRM) đỏ cả trên `main` 345e1c0: bấm ⌕ ở ô Mã đơn không chuyển sang `?f_ma_don=…`; `test_ban_phim_di_chuyen_sua_va_huy` đỏ khi chạy đủ `cham`, chạy riêng xanh trên cả hai nhánh — thread KN CRM xem | Trung bình |
| **K8** | `ScopedModel` chưa có cột "người sửa" | Thấp |
| **K10** | Quy tắc Q3 chưa áp ở màn hình nào | Thấp |
| **K14** | Nhánh Staff trong `apply_scope` không đọc phạm vi cấp thêm | Thấp |

### D · Tiêu chí nghiệm thu chưa có bài kiểm

1 tiêu chí đánh dấu *Tự động* nhưng chưa viết được. Danh sách này nằm trong
`app/tests/test_truy_vet.py`, biến `HOAN`, và
**có bài kiểm bắt phải ghi lý do** — không giấu được.

| Tiêu chí | Chờ |
|---|---|
| `AC-5.1` | Bốn cách nhóm mới chạy ba — tab thị trường chờ **N9** |

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
| K25 | Bảng tính (`crm`) chưa đọc `choice_registry.for_column` nên ô Chọn một của bảng tự tạo trên lưới vẫn là ô chữ (máy chủ vẫn chặn giá trị lạ qua `parse_value`). Sửa là một dòng trong `grid_service.choice_list` — thuộc thread KN CRM, không sửa ở đây. ~~K22~~ đóng ngày 06.09.2026 bằng `ColumnDef.options` và sổ theo nhãn (ADR-012) | Thấp | KNERP 06.09 |
| K26 | `GRID_ONLY_TABLES` và `grant_service.is_grid_only` chỉ còn KN CRM dùng (lưới báo chỉ xem; bảy tệp `crm/tests` dựa vào nó để kiểm chiều 403) sau khi KN ERP gỡ hẳn sửa ô (ADR-014); ở dịch vụ `bangtinh` danh sách đã rỗng nên thread KN CRM xem xét bỏ luôn — thread KNERP không đụng `app/crm/` | KNERP 06.09 |
| K30 | Tài liệu tải lên nằm ở `storage/tai-lieu/`, ngoài `pg_dump`: `scripts/backup.sh` chưa chép thư mục này, `restore.sh` cũng không; hiện `docs/05` B8 và B10 dặn chép tay cùng bản sao lưu. Tài liệu đã gỡ (xoá mềm) thì tệp vẫn nằm trên đĩa — tệp mồ côi, chưa có lệnh dọn | Trung bình | ADR-017 |
| K31 | Sơ đồ `docs/so-do-kien-truc.html` và hình vẽ trong `docs/kien-truc.md` chưa có năm app Nội bộ; bảng module ở `docs/kien-truc.md` và `docs/cau-truc-thu-muc.md` đã cập nhật chữ | Thấp | ADR-017 |
| K29 | `tests/e2e/test_bang_tinh_ui.py::test_dong_trong_thanh_dong_that_va_loc_theo_o_khoa` đỏ ngày 07.09.2026 khi chạy đủ `cham` — chạy riêng trên `main` 345e1c0 (worktree sạch, cơ sở dữ liệu kiểm thử riêng) cũng đỏ y hệt: sau khi gõ dòng trống thành dòng thật, bấm `.o-khoa-loc` ở ô Mã đơn `DH-1` không chuyển tới `?f_ma_don=DH-1…` trong 15 giây. Không phải do nhánh Nội bộ; cùng họ với K23 (hộp lọc gửi form hai lần). Cùng lần chạy đủ `cham` (28 đạt, 3 xfail), `test_ban_phim_di_chuyen_sua_va_huy` cũng đỏ (chờ ô Trạng thái VC đổi sau khi chọn danh sách quá 15 giây) nhưng chạy riêng thì xanh trên cả `main` lẫn nhánh Nội bộ — nghi do tải Chromium khi chạy nhiều bài liền, cần chờ có điều kiện thay vì đếm giây. Thread KN CRM xem, thread KNERP không đụng `app/crm/` | Trung bình | KNERP 07.09 |

### 1.2. Nghiệp vụ

| # | Nội dung | Mức | Nguồn |
|---|---|---|---|
| N1 | Lịch nộp báo cáo có bắt buộc đúng giờ không — chỉ ghi nhận, nhắc nhở, hay chặn nộp muộn | Trung bình | Bàn phạm vi |
| N2 | Nhân viên vận đơn có tự thêm cột vào bảng không | Thấp | Đã hỏi, trả lời là không |
| N3 | Vai trò Chăm sóc khách hàng có thuộc phase 1 không | Trung bình | Tệp vận đơn có cột CSKH, phase 1 chưa có vai trò này |
| N6 | Chăm sóc khách hàng có trong phase 1 không — `README.md` xếp vào phạm vi, `docs/02` mục 17 để ngỏ. Trùng với N3 nhưng nay có thêm chứng cứ vênh giữa hai tài liệu | Cao | Rà soát GĐ 1–2 |
| N7 | BR-1 nói mỗi người thuộc đúng một bộ phận, nhưng Admin hiện không thuộc bộ phận nào. Giữ nguyên hay bắt Admin cũng phải có bộ phận | Trung bình | Rà soát GĐ 1–2 |
| N9 | Cách nhóm theo thị trường của báo cáo tổng hợp lấy số liệu từ đâu — cột Quốc gia bảng vận đơn chưa có nhãn ý nghĩa (ADR-007 để ngỏ); ba đường: thêm nhãn thứ tám kèm tệp chuyển đổi, lấy từ đơn hàng, hay nhóm cột JSON. Người dùng chốt 03.09.2026: **chưa quan trọng, hỏi lại sau**. Tab vẫn hiện kèm ghi chú — Q36 | Trung bình | Kế hoạch GĐ 6 |
| N10 | Có tách loại tiền VND và USD khi cộng doanh thu không — bảng động chưa lưu loại tiền theo dòng có nhãn (Q10 lưu kèm loại tiền chỉ áp cho đơn hàng). GĐ 6 chọn cách đơn giản nhất: cộng thẳng `val_revenue`, không kèm ký hiệu tiền. Hỏi lại cùng lúc với N9 | Thấp | Kế hoạch GĐ 6 |
| N11 | Tỉ giá cố định để quy doanh số về VND trên bảng xếp hạng Văn hoá: đang tạm USD 25.400, CAD 18.500, PHP 440 trong `EXCHANGE_RATES_VND` (`knjsc/settings/base.py`, đè bằng biến môi trường cùng tên, **bắt buộc** dạng `USD=25400,CAD=18500,PHP=440` — số nguyên, không dấu chấm hay phẩy; sai thì hệ thống không lên và nêu tên biến, rà soát 07.09). Anh/chị chốt số, và có cần đổi theo tháng không (S21) | Trung bình | ADR-017 |
| N12 | Danh sách giá trị văn hoá để ghi nhận: đang tạm năm giá trị Tận tâm, Chính trực, Hợp tác, Sáng tạo, Trách nhiệm (`culture/constants.py`). Đổi sau khi có ghi nhận thật thì cần tệp chuyển đổi dữ liệu | Trung bình | ADR-015 |

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
| Q2 | Có làm quản lý tài nguyên và kho thông tin đăng nhập không | Không làm — **sửa bởi Q68** ngày 06.09.2026: có kho tài nguyên bản MVP, vẫn không có kho thông tin đăng nhập | (điền) |
| Q3 | Mảng nhân sự, kế toán, kho | Để giai đoạn sau | (điền) |
| Q4 | Có tích hợp với phần mềm kế toán không | Không, ít nhất trong phase 1 | (điền) |
| Q5 | Ứng dụng di động | Không làm bản cài đặt, chỉ cần giao diện dùng được trên điện thoại | (điền) |
| Q6 | Trợ lý AI | Không làm trong phase 1 | (điền) |
| Q7 | Khung ứng dụng | Django 5.2, PostgreSQL 16, HTMX, Celery với Redis, Docker Compose — ADR-005 | 28.08.2026 |
| Q8 | Danh sách module trong `app/` | Bảy module: core, org, forms_builder, reports, orders, dashboard, crm — **sửa bởi Q74**: mười hai module | 28.08.2026 |
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
| Q54 | Bảng tính đặt ở đâu so với ERP, có làm app không | **KN CRM là app riêng trong hệ sinh thái**: dịch vụ `bangtinh` 8021, tên miền con, mở tab mới từ ERP, **cùng kho mã cùng cơ sở dữ liệu** (cách B trong bảng so sánh A/B/C); KN ERP không còn lưới. **Không** làm app cài đặt (native, PWA) — quá đắt; cái cần trên điện thoại là KN ERP (Giai đoạn 8) — AC-11.30, ADR-012 | 06.09.2026 |
| Q55 | "Thư mục Quý → Tháng → file vận đơn" nghĩa là gì | **Tháng là góc nhìn trên một bảng**, cây tự sinh từ cột Ngày; bấm tháng là mở lưới lọc sẵn. Không tách bảng theo tháng (Lên đơn ghi vào một bảng, Lọc trùng và mua lại lần đếm cả lịch sử) — AC-11.28, AC-11.29, ADR-012 | 06.09.2026 |
| Q56 | Quyền trong KN CRM cấp ở mức nào | **Theo bảng như hiện có** (Manager cấp Xem/Sửa từng bảng ở KN ERP); cây chỉ hiện thứ được xem; không thêm quyền theo thư mục hay theo tháng — ADR-012 | 06.09.2026 |
| Q58 | Danh sách chọn của cột Chọn một lấy từ đâu, ai thêm — K22 | **Ba tầng, một chỗ phân giải** (`choice_registry.for_column`): sổ (bảng, cột) của crm → nhãn ý nghĩa (Sản phẩm = danh mục sản phẩm, chặt; Người bán = nhân sự bộ phận, gợi ý) → `ColumnDef.options` (chặt). **Manager quản lý, Staff chỉ chọn**; cột chưa có danh sách không nhận giá trị nào; bảng vận đơn giữ sổ crm — ADR-013, AC-8.7, AC-8.8 | 06.09.2026 |
| Q59 | Danh tính người điền ghi dạng gì, ép ở đâu | **Họ tên trong hồ sơ, không có thì tên đăng nhập** (`core.identity.display_name`, cùng luật với bảng vận đơn); ép ở tầng dịch vụ `form_service.fill`, không tin POST; chỉ áp cho điền biểu mẫu và nộp báo cáo, nhập tệp và lên đơn giữ nguyên — AC-4.6 | 06.09.2026 |
| Q60 | Tô màu chỉ số quan trọng trên Bảng dữ liệu theo cách nào | **Màu cột** (vàng, đỏ, xanh lá, xanh dương) tô tiêu đề lẫn ô, cộng **ngưỡng cảnh báo** cho cột số (đỏ khi lớn hơn / nhỏ hơn X, còn lại xanh lá); tiêu đề mặc định **xanh lá cố định**; là thuộc tính của cột, khác định dạng từng ô của ADR-010; viền chỉ ở bảng mang lớp `bang-luoi` — ADR-013, AC-8.9, AC-8.10 | 06.09.2026 |
| Q62 | Bảng dữ liệu ở KN ERP có sửa ô không — sửa Q26, Q42 và ADR-010 mục 1 | **Không, với mọi bảng.** Bảng dữ liệu chỉ để xem; sửa số liệu là việc của KN CRM. Gỡ hẳn view `bang_sua_o`, `_o.html`, `choice_service.attach_lists`, khối script sửa ô; nút "Mở trong KN CRM" và dòng báo hiện với mọi bảng; `GRID_ONLY_TABLES` chỉ còn KN CRM dùng (K26) — ADR-014, AC-7.4, AC-11.7, luật 13 `CLAUDE.md` | 06.09.2026 |
| Q61 | Ai thêm sản phẩm, thêm ở đâu | **Manager bất kỳ bộ phận (hoặc Admin) thêm ngay tại ô chọn** — trên biểu mẫu, ô bảng và Lên đơn; mã tự sinh từ tên, đồng bộ cột `sl_` trên bảng vận đơn ngay. Màn hình quản lý sản phẩm đầy đủ để sau (S11) — AC-6.9 | 06.09.2026 |
| Q63 | KN CRM cần trang chủ và menu trái không, lưới có sidebar không | **Có khung riêng như một app**: sidebar theo Teeze (ảnh anh/chị gửi), trang chủ là tổng quan như ERP, cây tháng là mục **Bảng tính** ở `/thu-muc/`; **lưới vẫn full như Excel**, chỉ khi chủ động quay về mới thấy menu trái; chỉ lưới có ← và nó về thư mục, không về ERP — AC-11.31, AC-11.32, ADR-015 | 07.09.2026 |
| Q64 | Leader được làm gì trong KN CRM | **Như Manager trong bộ phận mình**: thư mục, cột, tạo bảng, nhập tệp, xuất, sửa/xoá dòng người khác (một hàm `_quan_ly_bo_phan`); cấp quyền cho người khác vẫn Manager; phạm vi xem không đổi — AC-11.33, ADR-015 | 07.09.2026 |
| Q65 | Nhập tệp, tạo bảng, cấp quyền có phải bật sang ERP không | **Không** — gắn view forms_builder vào 8021, template kế thừa khung KN CRM qua biến `khung`; mục Nhập tệp (Leader+) và Cấp quyền (Manager) trên sidebar — AC-11.34, ADR-015 | 07.09.2026 |
| Q68 | Có làm quản lý tài nguyên không — sửa Q2 | **Có, bản MVP**: danh sách chia mục (BM, Via, Page, Tài khoản QC, SIM), Manager trở lên thêm mục và thêm, sửa, gỡ tài nguyên; mọi người xem; **không lưu mật khẩu** (ghi chú bị chặn từ khoá bí mật); chưa có sổ bàn giao (S16) — ADR-017, FR-13.x | 06.09.2026 |
| Q69 | Tài nguyên có phạm vi theo bộ phận không | **Không** — danh mục dùng chung toàn công ty, cột Bộ phận chỉ ghi nhớ ai đang dùng — ADR-017 | 06.09.2026 |
| Q70 | Bảng tin ai đăng, ai ghim, có thiệp sinh nhật không | Mọi người đăng, bình luận, thích; Manager và Admin ghim và gỡ bài bất kỳ, tác giả gỡ bài mình; thiệp sinh nhật tự động 06:00 từ ngày sinh trong hồ sơ (thêm cột `birthday`, org 0003) — ADR-017, FR-10.x | 06.09.2026 |
| Q71 | Bảng xếp hạng doanh số đọc số liệu từ đâu, ai xem | Từ **Đơn hàng** toàn công ty (ngoại lệ phạm vi có chủ ý, ghi trong docstring), tháng này theo người bán, quy về VND bằng `EXCHANGE_RATES_VND` cố định (N11); cả công ty xem hạng, số đơn, tổng — không thấy chi tiết đơn — ADR-017 mục 5 | 06.09.2026 |
| Q72 | Sao tính thế nào | **Một ghi nhận = một sao**; ngày 1 hằng tháng ba người dẫn đầu tháng trước nhận **5, 3, 1** sao, ràng buộc (người, kỳ, nguồn) nên chạy lại không nhân đôi; sổ ghi nhận và sổ sao chỉ ghi thêm, không sửa xoá (S19) — ADR-017 | 06.09.2026 |
| Q73 | Tài liệu chia mục thế nào, ai tải lên | Mục theo bộ phận hoặc toàn công ty; Manager tải lên mục bộ phận mình, Admin cả mục chung; PDF, Word, Excel, CSV, ảnh hoặc chỉ liên kết; tệp ở `storage/tai-lieu/`, tải về qua view kiểm quyền — ADR-017, FR-9.x | 06.09.2026 |
| Q74 | Danh sách module trong `app/` — sửa Q8 | **Mười hai module**: bảy cũ cộng `documents`, `feed`, `taskboard`, `culture`, `resources`; phụ thuộc một chiều `feed → culture → orders`, không ai import `feed` — ADR-017 | 06.09.2026 |
| Q75 | Ai ghi nhận văn hoá được ai — sửa FR-12.1, AC-15.1, ADR-017 mục 5 | **Chỉ cấp trên ghi nhận cấp dưới**: Leader ghi nhận nhân viên team mình, Manager ghi nhận Leader và nhân viên bộ phận, Admin ghi nhận mọi người; nhân viên chỉ xem, không có form; không đặt trần số ghi nhận mỗi ngày (anh/chị chọn cách này thay cho trần). Dịch vụ kiểm bằng `UserProfile.objects.in_scope(giver)` và cấp bậc thấp hơn | 07.09.2026 |
| Q76 | Ai tranh hạng doanh số | **Mọi người bán**, kể cả Leader, Manager, Admin có đơn — không loại quản lý khỏi bảng | 07.09.2026 |
| Q77 | Hoà điểm trên bảng xếp hạng — sửa Q72 | **Đồng hạng, cùng nhận sao** kiểu thi đấu 1, 1, 3: bằng tổng VND và bằng số đơn thì cùng hạng, cùng sao thưởng, người kế tiếp nhảy hạng | 07.09.2026 |

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
| S11 | Màn hình quản lý sản phẩm đầy đủ: sửa tên, nhóm, ngừng bán | Hiện chỉ thêm nhanh tại ô chọn (Q61); ngừng bán mới làm được qua dòng lệnh. |
| S12 | Xuất Excel Bảng dữ liệu mang theo màu cột và ô cảnh báo | Cùng chỗ với S8 |
| S16 | Sổ bàn giao tài nguyên: ai nhận, ai trả, khi nào | MVP chỉ có cột Người giữ; lịch sử đổi người giữ đang nằm trong Nhật ký — Q68 |
| S17 | Ảnh trong bài Bảng tin và ảnh đại diện | MVP chỉ chữ; avatar là chữ cái đầu — ADR-017 |
| S18 | Bảng kanban kéo thả cho Công việc, việc con, đính kèm | MVP là danh sách với nút đổi trạng thái — ADR-017 |
| S19 | Sửa hoặc thu hồi ghi nhận | Hiện là sổ cái chỉ ghi thêm để sao không lệch (Q72); nếu làm thì thu hồi phải trừ sao kèm nhật ký |
| S20 | Thông báo khi được giao việc, được ghi nhận, được bình luận | Cần chuông trên thanh trên hoặc thư — trùng hướng S3 |
| S21 | Tỉ giá theo ngày lên đơn | Hiện quy đổi bằng bảng cố định tại lúc tính, nên đổi `EXCHANGE_RATES_VND` giữa tháng là hạng đổi ngược thời gian; đã ghi tỉ giá vào nhật ký thưởng (rà soát 07.09). Muốn đúng hẳn thì lưu tỉ giá theo ngày trên từng đơn — N11, ADR-017 |

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
| 8 · Máy chủ, điện thoại, tối ưu | Chưa — chờ V1 | — |
| 9 · Nội bộ, bản MVP — Tài liệu, Bảng tin, Công việc, Văn hoá, Tài nguyên | ✓ trên nhánh riêng, PR #20 nháp | Chưa — kịch bản ở `docs/07` mục 3.1, 3.2, 3.4 |

Bản dựng giao diện tĩnh ở `prototype/` là chuẩn để đối chiếu. Nó có 10 màn
hình mà bản Django chưa có; bảng dưới đây theo dõi việc lấp dần.

| Màn hình trong bản dựng | Giai đoạn | Trạng thái |
|---|---|---|
| Bảng vận đơn — bảng dữ liệu chung | 3A | Đã có, dưới tên `/bang/<mã>/`, chỉ xem như mọi bảng (ADR-014) |
| Ma trận phân quyền | 3A | Đã có, bản chỉ đọc |
| Quản lý biểu mẫu | 3B | Đã có |
| Trình tạo biểu mẫu | 3B | Đã có |
| Nộp báo cáo ngày | 4 | Đã có |
| Lịch sử báo cáo | 4 | Đã có |
| Lên đơn | 5 | Đã có |
| Báo cáo tổng hợp | 6 | Đã có — tab Theo thị trường treo ghi chú chờ N9, Q36 |
| Bảng tính | 7 | Đã có — lưới cho **mọi bảng** ở `/bang-tinh/<mã>/` (ADR-010): viền ô, dòng trống, cột khoá, thanh lọc bên trái, thanh công cụ, định dạng ô, thư mục; bảng vận đơn vẫn sửa ở dịch vụ `bangtinh` (ADR-009); nhìn và thao tác như bảng tính KN Demo — chọn vùng, dán từ Excel, kéo điền, chuột phải, hoàn tác, hộp lọc giá trị, tự cập nhật (ADR-011); là **app riêng KN CRM** ở 8021 với trang chủ cây Bộ phận ▸ Quý ▸ Tháng, ERP chỉ liên kết (ADR-012) — nhánh `claude/bang-tinh-nhu-kn-demo` |
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
| 06.09.2026 | Người dùng muốn một tệp `.bat` nháy đúp là mở ngay `localhost` trên máy đó và tự bật Docker. `cap-nhat-local.bat` làm được nhưng kéo mã, dựng lại image và nạp dữ liệu mẫu nên mất vài phút — quá nặng cho việc mở lại hằng ngày. Thêm `scripts/KN JSC.bat` (tên do người dùng chọn; kèm biểu tượng `KN JSC.ico` vẽ từ `KN JSC.svg` — chữ KN trắng trên nền xanh, vạch cam, chữ JSC; lần đầu chạy tự tạo lối tắt "KN JSC" ngoài Desktop bằng PowerShell, đường dẫn Desktop lấy từ Registry để đúng cả khi OneDrive dời Desktop): mở Docker Desktop nếu chưa chạy (tìm cả trong Registry khi cài ở thư mục khác), `up -d` không `--build`, kiểm web ngay trước khi ngủ nên container đang chạy sẵn là mở trình duyệt tức thì; lần đầu trên máy sạch (chưa có container `web`) thì nạp `du_lieu_mau` trước khi mở, không thì không có tài khoản để đăng nhập. `cap-nhat-local.bat` cũng gọi nó (tham số `loi-tat`) ngay sau `git pull`, vì người dùng kéo mã xong là mong thấy logo ngay chứ không đi tìm tệp `.bat`. Người dùng bực vì vẫn phải tìm thư mục để nháy đúp lần đầu: yêu cầu thật là *mỗi ngày ấn một nút, không gõ gì*. Thêm `scripts/Cai dat KN JSC.bat` gửi thẳng qua chat để nháy đúp một lần ở bất kỳ đâu: tự tìm thư mục KNJSC trên máy (chỗ hay clone, rồi quét `dir /s`), `git pull`, gọi `KN JSC.bat` để tạo logo ngoài Desktop và mở hệ thống. Từ đó chỉ còn logo trên Desktop. Rồi người dùng chốt: **một tệp `.bat` ở thư mục gốc, máy nào clone về cũng nháy đúp là lên** — chuyển `KN JSC.bat` lên gốc, thêm tự `git pull --ff-only`; có mã mới thì migrate, `tao_bang_van_don`, khởi động lại worker/beat, dựng lại image chỉ khi Dockerfile/requirements/entrypoint đổi; gọi lại chính nó sau pull (tham số `da-keo`) vì cmd đọc `.bat` theo byte, tệp tự đổi là đọc lệch dòng. Lối tắt Desktop làm mới mỗi lần chạy để trỏ đúng chỗ khi kho mã chuyển. `cap-nhat-local.bat` giữ làm bản "làm hết cho chắc", và cũng được sửa theo cùng kiểu gọi lại chính nó sau `git pull` (mô phỏng cho thấy bản cũ trên máy người dùng, khi kéo mã đè lên chính nó, đọc tiếp rơi vào giữa dòng `set /a DEM+=1` rồi dừng ngang nếu Docker đang chạy sẵn). Bài học: **tệp `.bat` nào tự `git pull` thì phần sau `pull` phải nằm trong khối `( ... )` và `call` lại chính nó.** Chỉ Windows, chưa làm bản `.sh` vì Mac/Linux chỉ cần `docker compose up -d` |
| 06.09.2026 | Anh/chị hỏi lại câu gốc: vì sao cần Bảng tính, so với Excel, Google Sheets, Lark thì sao; kể lại dây chuyền Google Form → Sheet của Vận đơn lag dần sau vài tháng (6.000 khách một tháng). Chốt: KN ERP xem nhanh, **Bảng tính là app riêng KN CRM** tách tên miền, không làm app cài đặt, cái cần trên điện thoại là ERP. Bốn yêu cầu cho KN CRM (trang mới, thấy thư mục trước, quyền do Manager cấp, cây Bộ phận → Quý → Tháng → file); phản biện được chấp nhận: tháng là góc nhìn trên một bảng, quyền theo bảng. Làm 7G trên cùng nhánh: bỏ `crm.urls` khỏi ERP, một mục KN CRM mở tab mới, `crm/tests/conftest.py` đặt URLconf 8021, `test_khoi` duyệt hai URLconf; `crm/services/tree_service.py` + trang chủ `/` (cây tự sinh từ `val_date`, đếm một truy vấn cho cả bộ phận), nhãn tháng trên lưới, nút ← về đúng nhánh, tạo thư mục từ trang chủ; AC-11.28 → AC-11.30, 97 tiêu chí; ADR-012; Q54 → Q56 |
| 06.09.2026 | Anh/chị xem ảnh trước/sau (main 7E so với nhánh KN CRM) rồi chốt **gộp PR #5 vào `main`**. Gộp `main` (PR #6 → #10, `KN JSC.bat`) vào nhánh trước để hết xung đột ở chính bảng này, rồi gộp PR #5 bằng merge commit, giữ nhánh như lần PR #4. Máy anh/chị đang ở `main` nên nháy đúp `KN JSC.bat` là kéo được KN CRM; mã mount thẳng vào container, không cần dựng lại image. `/bang-tinh/` ở 8020 từ nay trả 404, lưới chỉ có ở KN CRM 8021 |
| 06.09.2026 | Đợt chỉnh sửa KNERP đầu tiên (thread KNERP, chỉ hệ thống chính, không đụng `app/crm/`). Bốn yêu cầu: (1) mọi chỗ chọn lựa là ô chọn có "＋ Thêm mới…", sản phẩm lấy từ danh mục và Manager thêm tại chỗ; (2) trường Người bán tự ghi tên người điền; (3) Bảng dữ liệu tô màu cột và ngưỡng cảnh báo, tiêu đề xanh lá; (4) viền mọi ô. Chốt Q58 → Q61, ghi ADR-013, đóng K22, mở K25, S11, S12. `ColumnDef` thêm `options`, `highlight`, `alert_op`, `alert_value` (migration 0008); `choice_registry` ba tầng; `choice_service`, `product_service`, `core/identity`, `forms_builder/styling`; `components/o_chon.html`, `static/js/chon.js`; hai đường dẫn POST mới. Sửa nhân tiện: chú thích nhiều dòng `{# #}` ở màn nộp báo cáo bị hiện ra màn hình; lỗi sửa ô 400 bị HTMX nuốt nay hiện ngay trong ô. AC-4.6, AC-6.9, AC-8.7 → AC-8.10. PR #5 (KN CRM) vào `main` trước nên đánh số lại ADR-012 → ADR-013, Q54 → Q57 thành Q58 → Q61, nhãn 7G thành 7H; sau khi gộp: 103 tiêu chí, 91 trên 92 tự động có bài kiểm |
| 06.09.2026 | Sau khi gộp PR #5, anh/chị nháy `KN JSC.bat` mà vẫn thấy "Bảng tính" thay vì KN CRM. `git status -sb` trên máy cho thấy kho đứng ở nhánh `claude/bang-tinh-nhu-kn-demo` tại `f11b788` (bản 04.09), `[behind 6]`, và **đang gộp dở**: `UU docs/backlog.md` cùng loạt tệp của main đã stage — dấu vết lần `cap-nhat-local.bat <nhánh>` trước đó `git pull` vướng xung đột ở `docs/backlog.md` rồi dừng, còn `KN JSC.bat` sau đó `git pull --ff-only -q` bị từ chối vì đang merge nhưng `-q` nuốt lỗi, chạy tiếp bằng mã cũ. Gỡ trên máy: `git merge --abort`, `git checkout main`, `git pull --ff-only`. Sửa cho hết lặng lẽ: `KN JSC.bat` thấy `.git/MERGE_HEAD` (hay `rebase-merge`, `rebase-apply`) thì in cách gỡ và không kéo; in nhánh đang đứng, cảnh báo khi không phải `main`; bỏ `-q`, pull lỗi thì in rõ và đợi 8 giây rồi vẫn bật bản đang có; `cap-nhat-local.bat` checkout hay pull lỗi thì dừng có thông báo thay vì dựng tiếp bằng mã cũ và để lại merge dở. Gỡ xong, 8021 báo `ProgrammingError: column forms_builder_columndef.options does not exist` — mã mới đã chạy nhưng **chưa migrate**: `KN JSC.bat` chỉ migrate khi chính nó kéo được mã (`TRUOC` ≠ `SAU`), người dùng kéo tay thì nó thấy "không có mã mới" và bỏ qua. Sửa: nhớ commit của lần chạy trước ở `storage/.kn-jsc-lan-truoc`, khác `HEAD` là migrate và cân nhắc `--build`, dù ai kéo; `cap-nhat-local.bat` migrate xong cũng ghi tệp đó. Bài học: **tệp `.bat` gọi git thì không được `-q`, phải kiểm `errorlevel` sau mỗi lệnh, và "có mã mới" phải so với lần chạy trước chứ không phải với lần kéo của chính nó** |
| 06.09.2026 | Người dùng muốn thêm skill thiết kế như bên Codex: **Impeccable** và **taste-skill** ("teach taste" của Impeccable nay là `/impeccable init`, `teach` là bí danh). Trong phiên web, `impeccable.style` bị chính sách mạng chặn (403) và `npx skills add` bị bộ phân loại chặn, nên chép thẳng từ kho nguồn GitHub: Impeccable skill 4.2.1 (Apache-2.0) vào `.claude/skills/impeccable/` kèm 4 subagent ở `.claude/agents/`, và 4 trên 13 skill của taste-skill (MIT): `design-taste-frontend`, `redesign-existing-projects`, `high-end-visual-design`, `minimalist-ui`; bỏ các skill sinh ảnh và bản riêng cho Codex, Stitch. Không commit hook detector (chạy engine sau mỗi lần sửa tệp), bật tay bằng `/impeccable hooks on`; engine tải về `~/.impeccable/bin/` lần đầu chạy, không nằm trong kho. Ghi nguồn và cách cập nhật ở `.claude/skills/NGUON.md`; CLAUDE.md thêm mục "Skill thiết kế giao diện" nhắc quy tắc 8 đứng trên gợi ý thư viện của skill |
| 06.09.2026 | Chạy `/impeccable init`. Ba câu hỏi, ba câu trả lời: (1) tên chính thức **KNERP** cho hệ thống chính, **KN CRM** cho bảng tính, **Kim Ngân JSC** là công ty; (2) **máy tính là chính, điện thoại phụ** để nộp báo cáo ngày và xem nhanh; (3) **nhiều người dùng máy yếu hoặc mạng yếu**, không có yêu cầu trợ năng nào được nêu (ghi là chưa quyết). Viết `PRODUCT.md` ở thư mục gốc theo lược đồ của Impeccable, phần còn lại lấy từ docs và ADR; không ghi hướng thẩm mỹ. Không có công cụ sinh ảnh trong phiên nên chưa ghi `buildPath`; chế độ live chưa cấu hình vì ứng dụng không chạy trong phiên web. Ngay sau đó chủ dự án nói thêm: *hiện chưa cần quá lo về hiệu năng*, nên PRODUCT.md hạ "máy yếu, mạng yếu" từ ràng buộc xuống điều cần biết, không lấy làm cớ cắt hiệu ứng hay tính năng |
| 06.09.2026 | Anh/chị hỏi vì sao bảng vận đơn không sửa được mà Báo cáo Marketing lại sửa được ngay trên Bảng dữ liệu: vì `GRID_ONLY_TABLES` chỉ có `van_don` (ADR-009 mục 4), bảng khác còn luật sửa ô của Giai đoạn 3 (FR-7.4) và ADR-010 mục 1 giữ nguyên điều đó; đợt KNERP đầu tiên không nêu mâu thuẫn này ra. Anh/chị hỏi tiếp gỡ hết dấu vết sửa ô có nhẹ đi không — trả lời thật: không bớt dữ liệu, tính toán khi ghi chuyển sang KN CRM cùng bộ mã; nhẹ ở mã và ở trang bảng có cột chọn; lý do thật là một cửa ghi duy nhất. Chốt **Bảng dữ liệu chỉ để xem với mọi bảng, sửa số liệu là việc của KN CRM** (Q62, ADR-014, luật 13 `CLAUDE.md`) và gỡ hết phía ERP: view `bang_sua_o` + đường dẫn, `_o.html`, khối script trong `bang_xem.html`, nhánh `editable` của `styling`, `choice_service.attach_lists`, handler 400 trong `chon.js`, CSS `o-loi-ly-do`; nút "Mở trong KN CRM" và dòng báo hiện với mọi bảng. Giữ `can_edit_record`, `record_service`, `GRID_ONLY_TABLES` vì lưới KN CRM dùng (K26). 14 bài kiểm thử sửa ô viết lại thành bài chỉ xem (AC-7.4, AC-11.7, AC-8.7) và bài gọi thẳng `update_cell` (BR-5, ADR-006, AC-7.10); một khẳng định ở `crm/tests/test_bang_tinh.py` đổi 403 → 404 |
| 07.09.2026 | Anh/chị mở KN CRM sau khi gộp PR #5 và nêu bốn điểm: bấm ← mãi rơi về ERP; chưa có trang chủ, chưa có sidebar; thư mục phải là một mục trên sidebar; Leader và Manager được thêm/sửa/xoá/tạo/nhập/xuất. Chốt qua ba câu hỏi và ảnh Teeze: trang chủ tổng quan như ERP, sidebar theo Teeze, Leader như Manager trong bộ phận, lưới vẫn full như Excel và chỉ khi chủ động quay về mới thấy menu trái. Làm **7I** trên nhánh `claude/kn-crm-khung-sidebar` (ADR-015): `grant_service._quan_ly_bo_phan` một chỗ cho mọi phép kiểm quản lý bộ phận, Sửa cột ở ERP kiểm thêm `can_manage_columns` (bịt lỗ Manager bộ phận khác được cấp Xem vẫn sửa cột); `base_crm.html` + `crm/navigation.py` + context processor `khung_crm`; trang chủ `/` = `tong_quan_service`; cây tháng sang `/thu-muc/`; view forms_builder gắn vào 8021 với `{% extends khung %}`, tên `bang`/`bang_xem` chuyển hướng có đăng nhập. Ba lần đụng **tên lớp CSS trùng** giữa sidebar và trang thư mục (`crm-nhan`, `crm-nhom`) làm chữ hoá đơn cách — đặt tiền tố `crm-nav-` cho sidebar. AC-11.31 → AC-11.34, sửa AC-8.8/8.9/11.17/11.19/11.21/11.22/3.6 và ma trận; 107 tiêu chí, 95 trên 96. Số ADR: thread KNERP đã lấy 013 nên đợt này là **014**, sửa dòng trùng "012" trong danh sách ADR |
| 07.09.2026 | Anh/chị muốn thay ▦ trên thanh trên lưới bằng **logo tự thiết kế**, bấm logo về trang chủ; chốt tôi vẽ, đặt ở thanh trên lưới, đầu menu trái KN CRM, đầu menu trái KN ERP và favicon. Vẽ `static/img/kn-crm.svg` cùng họ KN JSC (ô xanh gradient, KN trắng, vạch cam) thêm dấu lưới 3×2 vàng nhạt và chữ CRM; `static/img/kn-jsc.svg` là bản web của `scripts/KN JSC.svg`. Context processor `khung_crm` trả `logo` theo dịch vụ để một dòng favicon dùng chung ở bốn khung; trang đăng nhập cũng mang logo. Trước đó hệ thống chưa có favicon nào |
| 07.09.2026 | **MVP Nội bộ** (ADR-017): năm app `documents`, `feed`, `taskboard`, `culture`, `resources`; nhóm Nội bộ trên thanh bên; ngày sinh hồ sơ (org 0003); `FileKind` PDF, Word; `EXCHANGE_RATES_VND`. 23 tiêu chí mới AC-12.1 → AC-16.3 (một thủ công), 126 tiêu chí, 113 trên 114 tự động có bài kiểm, 1.637 bài đạt (chưa kể `cham`). Chốt Q68 → Q74 (sửa Q2, Q8), mở N11, N12, K30, K31, S16 → S20. Sửa nhân tiện: `|default:a.b.c` với `a` trống trong template ném lỗi — rào `{% if %}` ở bốn template |
| 07.09.2026 | **Rà soát lại MVP Nội bộ**: sửa 22 lỗi và điểm yếu trong bốn commit A → D, cải tiến giao diện, gọn mã dùng chung, thêm bài kiểm và tài liệu. Chốt **Q75** (chỉ cấp trên ghi nhận cấp dưới), **Q76** (mọi người bán tranh hạng), **Q77** (đồng hạng); mở **S21**; sửa K30, N11. 1.677 bài đạt (chưa kể `cham`); K29 vẫn của thread KN CRM |
