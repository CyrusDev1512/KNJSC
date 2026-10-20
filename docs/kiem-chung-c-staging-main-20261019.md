# Nhánh C — kiểm chứng trước khi đồng bộ Staging và main, 19.10.2026

## Phạm vi và mốc kiểm

- Nhánh kiểm chứng: `codex/kiem-chung-c-staging-main`, tách từ `origin/Staging` sau fetch.
- Staging: `ed7795b3e7f42233a1fbc4d3261c49d92faaf101`, đã gộp PR #137.
- Main trước lượt này: `3bfa9e61fa48c792a6350b8499a88b63622252fc`.
- Chủ dự án cho phép đồng bộ hai nhánh sau kiểm chứng, rồi xoá nhánh C; không phát hành VPS.
- Phần chênh Staging so với main gồm cả đợt P0 và hậu kiểm 14–15.10, KN OMS demo và PR #137; không chỉ riêng PR #137.
- Không có migration, requirements, Dockerfile hoặc entrypoint thay đổi trong phần chênh này.

## Bằng chứng đã có trên đúng mã ứng dụng

Tree của Staging `ed7795b` giống tree PR #137 tại `2a84147`; không suy kết quả từ một bản mã cũ hơn.
Mô phỏng `git merge-tree --write-tree origin/main HEAD` trước khi thêm biên bản này không xung đột và cho cùng tree với Staging.

| Kiểm | Kết quả |
|---|---|
| CI PR #137, run 39197889098, head `2a84147` | 3.926 test chính đạt; 91 + 30 test trình duyệt đạt |
| Kiểm lại local trước gộp #137 | 369 test server đạt (20 deselected), gồm báo cáo, phạm vi quyền, kiểu lọc, lưu lỗi và tính/xoá theo lô |
| Kiểm lại Chromium local | 10/10 đạt: dán vùng qua khối, đồng bộ, giữ nháp khi lỗi, đánh dấu ô sai, xoá thất bại, Manager desktop/390px |
| Cấu hình Django | `check`: không có vấn đề; `migrate --check` trên preview: không có migration chờ |
| Giao diện báo cáo mới | `activity.html` và `report-filters.js` không khác origin/main; PR #137 không sửa các tệp reports |

CI có 18 bài skip (fixture/môi trường kiểm riêng, kiểm tải và ca dòng trống không áp dụng) và một cảnh báo kết nối còn mở khi dọn database test.
Không gọi skip là đạt hoặc coi cảnh báo đã sửa. Không chạy lại tải 300k, không chứng nhận 10 người sửa + 5 Sale lên đơn.
TL-71, TL-83 và phần quyền Leader chưa chốt vẫn giữ trạng thái riêng; không tuyên bố toàn hệ thống không còn lỗi.
CI mới trên commit merge Staging và trên PR nhánh C phải được đọc kết quả thực tế trước khi gộp tiếp.

## Preview local đã chuẩn bị

- ERP `http://localhost:18062/`, CRM `http://localhost:18063/`, database fixture riêng.
- Đã sao lưu database fixture trước khi chạy `configure_erp_reports`; backup chỉ lưu local, ngoài Git.
- Đã cấu hình ba nguồn Marketing, Sale, Vận đơn; không seed hoặc đặt lại mật khẩu.
- Trước/sau: 1.005 DataRecord, 0 DailyReport, 0 Order. Metadata/cột tính báo cáo được cập nhật bằng lệnh chuẩn.
- Trình duyệt đã mở giao diện báo cáo mới, chuyển nguồn Sale/Marketing, mở bộ lọc, bật toàn màn hình và thoát bằng Esc.
- Năm dòng Marketing mẫu cũ chưa có loại tiền vẫn hiện cảnh báo; Sale chưa có dòng mẫu. Không dùng số liệu mẫu này nghiệm thu tiền thật.
- Preview chưa chạy worker/beat; kiểm browser không thay nghiệm thu tác vụ nền thực tế.
- VPS không được thay đổi; chưa đối chiếu trực tiếp lại giao diện VPS vì kết nối domain và SSH timeout trong lượt kiểm này.

## Chặng kiểm tay còn thiếu

### Lỗi chặn phát hiện khi kiểm tay: ô có dấu sửa gần đây lệch hàng

- Chủ dự án báo không sửa được Ghi chú khi dùng `quantri` trên preview local.
- Tái hiện trực tiếp trên Chromium với tài khoản Admin mẫu: ô Ghi chú được server cho sửa, nhưng bấm đúp không mở editor.
- Ô có lớp `mg-moi-sua` và không ghim bị CSS `position:relative` ghi đè định vị absolute của lưới. Đo trực tiếp: hàng ở top157, ô của hàng đó ở top185; lệch đúng 28px. `elementFromPoint` tại phần chữ nhìn thấy trả về hàng kế tiếp, không phải ô Ghi chú.
- Quy tắc ở `app/static/css/master-grid.css` đã có trên main (nguồn commit `bea5d51c` ngày 28.09); không kết luận lỗi mới do #137.
- Bài E2E lịch sử ô hiện có kiểm lớp đánh dấu, chưa chứng minh ô không ghim có dấu vẫn nhận bấm và sửa được.
- **Chặn đưa lên main:** đề xuất bỏ ghi đè vị trí, giữ dấu góc và quyền; thêm hồi quy nhiều dòng có dấu, hình học/hit-test, sửa/lưu/tải lại trên desktop và 390px. Đang chờ duyệt cách sửa; chưa sửa mã ứng dụng.

Chủ dự án xác nhận ngày 19.10: mới lướt qua local, chưa biết nên kiểm gì. Đây **chưa phải xác nhận kiểm tay đạt**.

Kịch bản ngắn dùng dữ liệu mẫu local:

1. Báo cáo tổng hợp: mở/ẩn lọc; đổi Marketing/Sale; bật toàn màn hình và Esc; xác nhận bố cục mong muốn.
2. CRM: sửa ghi chú một dòng mẫu, chờ Đã lưu rồi tải lại; đối chiếu nội dung.
3. Dán vùng nhỏ từ Excel; lọc ngày/tiền rồi bỏ lọc; kiểm các dòng mong đợi.
4. Tài khoản mẫu Manager: đọc vận đơn người khác; không tự có quyền sửa hoặc menu Quản trị.

Máy kiểm các ca lỗi kỹ thuật; chủ dự án xác nhận trải nghiệm/luồng phù hợp. Nếu có lỗi thì ghi lại và kiểm lại sau sửa.

## Thứ tự gộp được phép

1. Nhánh C → PR nháp về Staging; chỉ gộp khi CI đạt theo phê duyệt có điều kiện của chủ dự án.
2. Chỉ sau xác nhận kiểm tay đạt: Staging → PR về main, kiểm CI và gộp.
3. Nếu cần đồng bộ lịch sử, mở PR main → Staging; không push thẳng. Hai nhánh phải cùng nội dung mã, không bắt buộc cùng SHA. Dừng nếu có thay đổi từ phiên khác.
4. Xoá nhánh C đã hoàn tất, giữ bốn nhánh nền. Không đụng PR #136 đang mở hoặc đưa nhánh chưa duyệt vào lượt này.

Biên bản này ghi tình trạng chuẩn bị, không chứng nhận các bước gộp ở trên đã xảy ra. Kết quả thực tế phải đối chiếu ref/PR khi thực hiện.

## Kiểm lại trên bản sạch ngày 19.10.2026 — CHẶN MERGE

Mục này bổ sung và giới hạn các kết luận phía trên. Mốc kiểm là C
`1ba9a59a47102c88864f02e6b21ab7a43d275855`; remote Staging/main vẫn ở các SHA
đầu biên bản khi bắt đầu lượt kiểm. Dùng git archive toàn repository, không lấy
thay đổi chưa commit. Preview ERP 18062/CRM 18063 phục vụ bản trích xuất sạch.
Hash nội dung HTTP của master-grid.js, report-filters.js và master-grid.css
khớp tệp trong bản trích xuất đang chạy.

### Kết quả ba nhóm CI chạy local

| Lệnh (từ app, settings test, database riêng) | Kết quả thực tế |
|---|---|
| `pytest -m "not trinh_duyet"` | 3.923 đạt, **3 lỗi**, 7 skip, 132 deselected; 666,18 giây |
| `pytest tests/e2e -m trinh_duyet` | 91 đạt, 2 skip; 489,13 giây |
| `pytest -m trinh_duyet --ignore=tests/e2e` | 30 đạt, 9 skip, 3.933 deselected; 258,62 giây |

Ba lỗi thuộc core/tests/test_sao_luu.py: phục hồi vào database tạm, phục hồi
dump cắt giữa chừng và phục hồi đè database test đang chạy. Log cho thấy
`unrecognized configuration parameter "transaction_timeout"`; pg_dump/pg_restore
trong image test là 17.11, server test là 16.14. Đây là chênh phiên bản môi trường
đã xác minh, chưa sửa môi trường hoặc chạy lại; **không tính ba bài này là đạt**.

18 skip gồm fixture/kiểm tải riêng, 300k không bật, ca dòng trống không áp dụng
và bài cần Chrome host/proxy/server riêng. Nhóm trình duyệt còn lại có một cảnh
báo dọn database test khi còn một kết nối; chưa xử lý. Không thay skip bằng đạt.
Log và JUnit XML đầy đủ lưu local trong
`storage/test-results/premerge-20261019/final-results/` (ngoài Git).

### Ghi chú: kết luận chính xác hơn

- Admin, nhiều hàng liền nhau, ô ID 6 có dấu cam: bấm đúp không mở editor;
  hàng top 157, ô top 185, hit-test trả hàng kế tiếp.
- **Cùng ô ID 6, cùng phiên bản và tài khoản, lọc còn một hàng: bấm đúp mở được.**
  Vì vậy không được kết luận mọi ô có dấu cam đều không sửa được.
- Admin, ô không dấu cam ID 1004: nhập hai dòng có nhãn QA-20261019, tự lưu,
  reload và đối chiếu database giữ nguyên nội dung.
- Vận đơn vd.staff: chọn ô bằng bàn phím/F2, sửa ID 6 và lưu thành công;
  đã đối chiếu database. Chưa lấy thao tác này thay cho nghiệm thu bấm đúp đầy đủ.
- Ảnh: `admin-note-blocked.png`, `admin-orange-one-row-opens.png`,
  `admin-note-saved-reloaded.png` trong thư mục bằng chứng local trên.
- Đối chứng lịch sử bằng bản sạch trên cùng fixture hiện tại: a0313be mở được;
  bea5d51 không mở; main 3bfa9e6, trước PR137 2d5fb04 và C cũng tái hiện.
  Quy tắc CSS xuất hiện 28.09 không chứng minh người dùng đã gặp lỗi hôm đó.
  Kết quả trước đây dùng worktree bẩn không được dùng làm đối chứng lịch sử.
  Chưa xác minh trực tiếp bản VPS hiện tại; không kết luận VPS đang lỗi.

### Worker và dữ liệu thử

Đã backup database fixture trước ghi, SHA256 dump:
`4E31D1558660096603B1464AFE93A28F69235382E89F8094A5D24334A2D72028`.
Backup chỉ lưu local, chưa dùng nó để tuyên bố phục hồi thử thành công.
Redis/worker riêng, không beat; email dùng locmem. Hai job thật qua worker:

- Export job 1 của vd.staff: done, 1 dòng, có file; chủ sở hữu và Admin tải 200,
  Sale Staff/Leader/Manager và CEO bị 404 khi đổi sang ID này.
- Recompute job 2: done; bảng QA riêng ID 4, dòng ID 1006, 10/2 → 5.00.
  Harness chỉ hạ ngưỡng chọn async ở tiến trình gửi để dùng fixture nhỏ;
  worker thực thi bình thường. Không phải phép đo tải hay nghiệm thu giới hạn lớn.

Hai ô ghi chú thử có nhãn QA; không sửa dữ liệu nghiệp vụ. Các fixture và log
worker giữ local. Trước đó biên bản nói chưa chạy worker; phần này thay thế nhận
định đó cho lượt kiểm mới. Chưa chứng nhận đủ tất cả trạng thái file lỗi/hết hạn.

### Phần chưa nghiệm thu và quyết định dừng

Chưa hoàn tất toàn bộ ma trận thao tác tay ở 1440/1366/390 và zoom 125%/200%,
toàn bộ vai trò, chứng từ/thư viện/OMS và các luồng báo cáo. Form Vận đơn trên
fixture báo chưa có mẫu: kiểm mã lệnh cho thấy cần cấu hình mẫu báo cáo ngày
Vận đơn riêng; chưa chạy lệnh đó trong lượt này, chưa coi đây là lỗi sản phẩm.
Các test tự động đạt không thay cho các mục thao tác tay còn thiếu.

**Không merge PR138, không mở/gộp Staging → main, không xoá nhánh C.**
Lỗi bấm đúp nhiều hàng vẫn là chốt chặn; ba lỗi môi trường backup cũng chưa đạt.
Chủ dự án chưa xác nhận kiểm tay đạt. Không sửa mã ứng dụng, không triển khai VPS.
Chỉ cập nhật tài liệu local; chưa commit/push phần tài liệu lượt này vì điều kiện
chuyển sang giai đoạn merge chưa đạt. Chưa phê duyệt cách sửa mới.

## Lượt sửa tiếp theo cùng ngày — chủ dự án đã duyệt

Yêu cầu tiếp theo “sửa các lỗi đó trước” cho phép sửa tối thiểu và kiểm lại;
thay thế trạng thái chưa duyệt sửa phía trên. Không mặc nhiên cho merge/VPS.

- Thêm hồi quy vào `test_lich_su_o_tren_luoi.py`, chạy trước khi sửa CSS:
  đỏ với hình học thực tế `{cell: 185, row: 157}`. Bản ghi lấy ID fixture,
  hai hàng liên tiếp được người khác sửa qua service thật để có dấu cam.
- Bỏ duy nhất `.mg-cell.mg-moi-sua:not(.mg-pinned){position:relative}`.
  Pseudo-element dấu cam vẫn định vị trong ô absolute/sticky hiện có.
  Không thay quyền, nội dung, chiều cao tự động, sự kiện hoặc logic lưu.
- Cả file lịch sử ô đạt **7/7**, không skip, 51,174 giây; bốn ca mới kết hợp
  Admin/Vận đơn với 1366/390 px. Chỉ bấm đúp tại điểm hit-test đúng ô, không
  force-click; sửa hai hàng, đối chiếu database đúng ID và reload còn nội dung.
- Bản preview 18062/18063 đã nhận CSS sửa; hash CSS qua HTTP khớp tệp đang chạy.
  Preview từ đây là SHA 1ba9a59 cộng diff CSS trên, không còn tuyên bố nguyên SHA sạch.
- Backup: container test đã cài `postgresql-client-16`, chạy nhóm bằng
  `PATH=/usr/lib/postgresql/16/bin:/usr/local/bin:/usr/bin:/bin`.
  `pg_dump` và `pg_restore` đều 16.15, server 16.14: **35/35 đạt**, không skip,
  14,854 giây. Không nới assertion hoặc bỏ `--single-transaction`.
  Mã backup/Dockerfile không đổi. Khi dựng lại container test phải chọn client
  cùng major; image mặc định còn dùng package theo distro, chưa được khắc phục
  ở bước đóng gói. Không suy rằng backup VPS đã được kiểm hoặc sửa.

Các log mới: `backup-fixed.log/xml`, `notes-fixed.log/xml`; ảnh hồi quy
`ghi-chu-dau-cam-{admin,staff_vd}-{1366,390}.png`, lưu ngoài Git.
Hồi quy bổ sung `test_ghi_chu_tu_gian_dong.py` và `test_pha_luoi_ghi_chu.py`:
**21 đạt, 1 skip** (ca dòng trống không có dòng/quyền thêm dòng trong fixture).
Không lỗi mới; log/XML `notes-regression` lưu cùng bộ bằng chứng. Không chạy 300k.
Chưa chạy lại toàn bộ ba nhóm CI trên một commit mới, chưa xác nhận kiểm tay của
chủ dự án; không chuyển trạng thái thành đủ điều kiện merge.

## Lượt sửa Dockerfile cùng ngày — thay giới hạn chỉ sửa môi trường test

Chủ dự án yêu cầu sửa Dockerfile và kiểm trước merge. Đã thay client theo distro
bằng `postgresql-client-16` từ PGDG dùng signed-by; cố định base Trixie và PATH
binary 16. Bước build kiểm major cả pg_dump/pg_restore. Giữ cập nhật patch 16.x,
không nâng server hoặc thay service backup. Hướng dẫn vận hành đã ghi rằng
image mới không tự sửa dump cũ tạo bởi client 17.

Build từ archive HEAD cộng đúng diff CSS, test và Dockerfile của lượt sửa:

| Image local | Image ID | Kiểm chứng |
|---|---|---|
| `knjsc-backup16-test:20261019` (`INSTALL_DEV=1`) | `sha256:88af6d9a1af94473473c631bda88bbc5e768f97fb19893fda4fadf565b70a582` | 35/35 bài backup đạt, không skip |
| `knjsc-backup16-prod:20261019` (`INSTALL_DEV=0`) | `sha256:01f62c27441401bb9c0b4b65cca40d5c65b42663a10d553e71ba62c8d85f7040` | dump/restore thật và Django check đạt |

Không cài thêm công cụ hoặc override PATH sau build. Các lệnh qua entrypoint
với RUN_MIGRATIONS=0, uid 1000; công cụ đều 16.15, PostgreSQL test 16.14.
Smoke production tạo hai DB QA riêng, giữ đúng chữ Việt/xuống dòng/numeric và
primary key sau restore, rồi dọn hai DB QA đó. Không chạm DB preview/nghiệp vụ.
Không chỉ liệt kê dump để kết luận phục hồi đạt.

Đã kiểm diff; ứng dụng chỉ có thay đổi CSS/test ghi chú được duyệt từ lượt trước.
Không phát hành, không tự đưa image mới vào các dịch vụ đang chạy. Không merge
PR138 hoặc hai nhánh nền; kiểm tay và CI commit cuối vẫn là các chốt còn thiếu.

## Kiểm lại CI ngày 20.10 — fixture hiệu năng thiếu ANALYZE

CI PR #138 run `39365309926` đã chạy tới cuối thay vì bị huỷ. E2E Chromium đạt;
bộ chính có **1 lỗi, 3.925 đạt, 7 skip, 136 deselected**. Lỗi duy nhất là
`tests/test_hieu_nang.py::test_bang_tinh_50000_dong_co_loc_duoi_2_giay`:
bộ lọc `?trung=1` mất 412,05 giây, vượt ngưỡng 2 giây.

Đối chứng Docker local trên cùng commit trước sửa:

- chạy riêng test lưới: đạt; bốn request cộng 4,44 giây;
- chạy nguyên module đúng thứ tự CI: 2/2 đạt; call 0,99 và 0,63 giây.

Khác biệt đã xác định ở khâu chuẩn bị: management command `seed_perf` luôn
`VACUUM ANALYZE` sau bulk insert, còn fixture module gọi thẳng `run()` rồi đo.
Database CI mới chưa có thống kê nên PostgreSQL có thể chọn kế hoạch lồng rất
chậm; local auto-analyze kịp nên không tái hiện. Fixture được sửa để chạy
`ANALYZE forms_builder_datarecord` trước khi bấm giờ. Không đổi truy vấn sản
phẩm, dữ liệu, quyền, số truy vấn hoặc ngưỡng 2 giây.

Sau sửa, chạy nguyên `tests/test_hieu_nang.py` trên Docker/database test riêng:
**2/2 đạt**, call lần lượt 0,75 và 0,67 giây, tổng 31,08 giây. Hai cảnh báo
`.pytest_cache` do quyền bind mount không ảnh hưởng phép đo hoặc kết quả test.

Biên bản rà 27 mã của #136 được giữ tại
`docs/kiem-chung-ra-27-ma-cu-20261015.md`. Mã sửa từ kết quả rà đã vào Staging
qua #137; không gộp ngược các trạng thái backlog cũ đang conflict từ #136.
Kết quả test sau sửa và CI commit cuối phải được ghi tiếp trước khi merge #138.
Chặng kiểm tay vẫn là điều kiện riêng trước khi đưa Staging sang main.
