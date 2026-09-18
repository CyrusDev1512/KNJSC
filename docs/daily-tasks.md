# Daily tasks — KNJSC

Prompt dán vào Claude Code CLI ở máy chủ dự án để làm hai mục bàn giao 18.09 dưới đây (phát hành
chung ADR-036 + bảy PTTT + ADR-037/038) rồi Việc A: `docs/prompt-cli-phat-hanh-adr036-mkt-20260918.md`.

## Bàn giao phát hành VPS — 18.09.2026 (tối): trang MKT hoàn thiện (ADR-037, ADR-038, ADR-031 bổ sung)

Đầu nhánh `codex/crm-update-solar-ui` sau commit "Hoan thanh trang MKT…" (xem `docs/backlog.md`
mục 18.09 tối). Quy trình chuẩn ở `deploy/production/README.md` **đã thêm hai lệnh `gan_ma_nhan_su_cu`**.
Thứ tự:

1. Backup có kiểm phục hồi. `.env`: thêm `EXCHANGE_RATES_VND` cho EUR/JPY/AUD nếu muốn khác mặc
   định (`USD=25500,CAD=17500,PHP=440,EUR=28500,JPY=155,AUD=17000`); **KRW chưa có** — kế toán chốt
   rồi thêm `KRW=…`, trước đó bảng xếp hạng báo "Chưa có tỉ giá cho KRW" nếu có đơn Hàn Quốc.
2. `migrate` — ba migration mới, đều đảo được: `org/0005_userprofile_staff_code`,
   `orders/0009_more_markets_currencies` (SQL no-op), `reports/0004_remove_report_unique_per_person_per_day`
   (chiều ngược **thất bại nếu đã có người nộp nhiều lần/ngày** → quay lui bằng backup).
3. `tao_bang_van_don` → `configure_erp_reports` (thêm cột Tệp khách hàng, bổ sung 4 thị trường và
   4 loại tiền vào cột có sẵn, gỡ trường Doanh thu nhập tay khỏi biểu mẫu MKT, bỏ cột tính
   `hoa_don_doanh_thu`) → `configure_delivery_daily_report` → `collectstatic`.
4. `gan_ma_nhan_su_cu` (xem trước) → gửi bảng "tên đăng nhập → mã" cho chủ dự án; muốn mã khác
   thì Admin gán tay ở Nhân sự → Sửa hồ sơ **trước** khi chạy `gan_ma_nhan_su_cu --xac-nhan`
   (gán rồi thì cố định). Lệnh chỉ đổi ô danh tính khớp đúng tên đăng nhập; chạy lại không đổi thêm.
5. `up -d` năm dịch vụ, `nginx -t`, reload. Chrome domain thật: đăng nhập tài khoản cũ như thường;
   tạo thử một tài khoản mới (mã gợi ý, đăng nhập bằng mã hoa/thường); Marketing nộp báo cáo
   hai lần cùng ngày có Tệp khách hàng; Kế toán mở Lịch sử → Sửa; Báo cáo tổng hợp MKT có cột
   Doanh thu (chỉ có số khi vận đơn đã phân công Marketing và đã thu tiền), Chọn nhanh, lọc Tệp.
6. Báo trước cho nhân viên: định danh hiện **mã · họ tên**; Marketing nộp bao nhiêu lần cũng
   được; Doanh thu không nhập nữa; Kế toán sửa được số liệu mọi bộ phận.

### Ghi chú cho Việc A (bố cục Báo cáo tổng hợp — mục bàn giao 18.09 phía dưới)

- Bộ lọc có thêm ô **Tệp khách hàng** (`name="tep"`, chỉ hiện với nguồn có `segment`) và hàng
  nút **Chọn nhanh** (`.report-presets`, `.report-preset[data-tu][data-den]`, JS đã có trong
  `static/js/report-filters.js` — gộp vào bản viết lại, không bỏ). Chip bộ lọc thêm chip `tep`.
- Ô Nhân sự/Leader đã hiện `MÃ · Họ tên` (Đợt 1 làm xong); bản vẽ dùng đúng định dạng này.
## Bàn giao cho Claude Code CLI trên máy chủ dự án — 18.09.2026 (chiều): phát hành ADR-036, một bảng vận đơn

Đọc trước: `docs/quyet-dinh/036-mot-bang-van-don-duy-nhat.md`,
`docs/kiem-chung-mot-bang-van-don-20260918.md`, mục 18.09 (chiều) ở `docs/backlog.md`.

**Điều nhìn thấy ngay sau phát hành:** chỉ còn một bảng vận đơn "Vận đơn mới"
(`van_don`); crmThuận và Vận đơn DB **biến mất hẳn** (6.667 + 2 dòng, xoá cứng theo
lệnh chủ dự án); mục "Bảng nhận đơn" không còn trên sidebar Admin; Lên đơn ghi vào
Vận đơn mới; nhập tệp không cần Chi tiết sản phẩm.

### Việc, theo thứ tự

1. `git fetch`, checkout `codex/crm-update-solar-ui` ở commit ADR-036; `pytest -m "not cham"`.
2. SSH VPS, chỉ ghi nhận: `docker compose ps`, image, dung lượng DB, số dòng ba bảng
   (`van_don`, `van_don_moi`, `van_don_db`), `showmigrations forms_builder`.
3. **Dừng**, tóm tắt, hỏi chủ dự án xác nhận một lần. Nhắc rõ: lệnh xoá cứng không hoàn tác.
4. Backup DB, **kiểm phục hồi** vào DB tạm, đếm dòng ba bảng khớp. Không có thì không đi tiếp.
5. Build image `knjsc-app:<commit>-adr036`; dãy README: `config --quiet` → `up -d db broker
   cache` → `static-owner` → `migrate --noinput` (kỳ vọng `forms_builder 0014` và `orders 0009` của Codex và `orders 0010`, chỉ đổi choices) →
   `tao_bang_van_don` (nâng cấp tại chỗ `van_don`, in một bảng; cột PTTT nhận thêm 5 lựa chọn mới) →
   **`xoa_bang_van_don_cu --dong-y-xoa-cung --backup-da-lam`** (in số lượng từng loại) →
   `configure_erp_reports` → `configure_delivery_daily_report` → `collectstatic` →
   `up -d crm erp worker heavy beat proxy` → `nginx -t`, reload.
6. Kiểm Chrome domain thật: thư mục Vận đơn chỉ một bảng; sidebar Admin không có Bảng nhận
   đơn; `/bang-tinh/van_don/` 11 dòng, có cột Trùng và nút Tôi/Toàn bộ, bấm ô Sản phẩm mở hộp
   Chi tiết; Lên đơn một đơn thử → dòng mới ở `van_don` có chi tiết, rồi đánh dấu xoá;
   Thống kê `nguon=van_don`; ERP Báo cáo tổng hợp nguồn Vận đơn có dữ liệu.
7. Ghi `docs/kiem-chung-phat-hanh-vps-20260918-adr036.md`, backlog, kanban; commit
   "Ghi ket qua phat hanh ... (ADR-036) tren VPS", push khi chủ dự án bảo.

## Bàn giao cho Claude Code CLI — 18.09.2026: bố cục Báo cáo tổng hợp + mã nhân sự

> Cập nhật chiều 18.09: Codex đã phát hành `0d970f8` lên VPS (`8c78471`), nên mục
> "phát hành VPS 17.09" phía dưới **đã xong**, giữ làm lịch sử. Đợt A+B dưới đây khi
> phát hành sẽ cần thêm `migrate` (org/0005) và lệnh gán mã cũ.

Chủ dự án đã duyệt bản vẽ `docs/tham-khao/ban-ve-bao-cao-tong-hop-20260918.html`
(mở bằng trình duyệt: thử Thu gọn bộ lọc, Toàn màn hình, đổi sáng/tối, kéo hẹp
dưới 900px). Dán vào CLI:

> Đọc `docs/daily-tasks.md` mục "Bàn giao cho Claude Code CLI — 18.09.2026" và
> `docs/tham-khao/ban-ve-bao-cao-tong-hop-20260918.html`. Trình bày kế hoạch theo
> AGENTS.md rồi làm trọn hai việc A và B.

### Ba quyết định đã đề xuất, chủ dự án chưa phản đối — xác nhận lại ở bước kế hoạch

| Câu | Mặc định làm theo |
|---|---|
| Quy tắc mã | **Theo tệp "Quản trị nội bộ.xlsx", sheet Quy ước-Định nghĩa 2.0** (chủ dự án cung cấp 18.09): không dấu, viết hoa, viết liền **TÊN + chữ cái đầu họ + chữ cái đầu tên đệm** — Lê Thưởng Thuận → `THUANLT`; trùng thì thêm số từ 2: `THUANLT2`, `THUANLT3`. Bỏ đề xuất `PMA01` cũ. |
| Mã có đổi được sau khi tạo không | **Cố định** như mã nhân viên thật; Admin sửa được trước khi lưu lần đầu |
| **Mã là trường riêng hay chính tên đăng nhập?** | Sheet ghi "Tài khoản login: User = MÃ_NV". **Chưa chốt** — đề xuất: thêm `staff_code`, và **tài khoản tạo mới có tên đăng nhập = mã**; tài khoản đã có giữ tên đăng nhập cũ, chỉ gán mã. Không đổi tên đăng nhập của người đang dùng trên VPS. CLI hỏi chủ dự án trước khi làm. |
| Dữ liệu cũ trên VPS đang chụp tên đăng nhập | **Có lệnh chạy một lần** đổi tên đăng nhập → mã trong cột định danh; chạy trên VPS sau khi gán đủ mã |

### Việc A — Bố cục màn hình Báo cáo tổng hợp theo bản vẽ

Tệp đích: `app/templates/reports/activity.html`, `app/static/css/solarpunk.css`
(thay khối `.report-workspace` … `.sp-report-focus`, dòng ≈252–305, **không** để
hai bộ rule chồng nhau), `app/static/js/report-filters.js`.

- Bộ lọc ba trạng thái qua `data-filters` trên `#report-workspace`: `open` (260px),
  `rail` (thanh 48px, huy hiệu = số bộ lọc đang áp), dưới 900px là ngăn kéo
  **mặc định đóng**. Toàn màn hình tự chuyển sang `rail`. Escape: đóng ngăn kéo
  trước, thoát toàn màn hình sau. Giữ việc bật `sp-erp-table-focus` như hiện có.
- Nhớ trạng thái: đổi `sessionStorage` khoá `knjsc-report-layout` từ
  `{hidden, focus}` sang `{filters:'open'|'rail', focus}`; đọc khoá cũ thì coi
  `hidden:true` là `rail`.
- Hàng chip bộ lọc đang áp, render từ `params` phía máy chủ; nút × của mỗi chip
  là link cùng URL bỏ đúng tham số đó. Không cần chip "Nguồn".
- Bảng: tiêu đề và dòng Tổng ghim trên; **cột định danh ghim trái**. Template có
  cột định danh thay đổi theo `show_team` và cách xem (ngày / nhân sự / sản phẩm /
  thị trường) — ghim theo lớp `.report-identity` **tổng quát**, chiều rộng bằng
  biến CSS, không cứng `col-ngay`/`col-nhan-su` như bản vẽ. Tiêu đề dài xuống
  hai dòng (`white-space:normal; max-width`), ô số `nowrap`, đệm 8px 10px, 13px,
  `tabular-nums`. Ô định danh không cắt chữ.
- **ADR-035 (Codex, 18.09) đã thêm cột Nhân sự và Leader vào cách xem theo ngày**
  (`show_person`, `show_leader`) — giữ nguyên hai cột đó; cả hai là cột định danh
  cần ghim và **xuống dòng**. Rule mới `.report-identity {max-width:220px; overflow:hidden;
  text-overflow:ellipsis}` chính là thứ cắt tên mà chủ dự án phàn nàn — **bỏ**, thay
  bằng `white-space:normal; overflow-wrap:anywhere` như bản vẽ. Sau việc B, ô Nhân sự
  hiện `THUANLT · Lê Thưởng Thuận` (nhiều người trong một ngày thì nối bằng dấu phẩy như
  `StringAgg` đang làm).
- Chỉ dùng token có sẵn; không thêm thư viện; không đưa `.demo-bar` và nút đổi
  theme của bản vẽ vào app.

### Việc B — Mã nhân sự xuyên hệ thống (ADR-037, viết ADR trước khi sửa; 034 và 035 đã có)

Hiện trạng đã rà: `UserProfile` **không có** trường mã; `core/identity.py` đã
tập trung `employee_code()` và `display_name()` nhưng `employee_code()` trả tên
đăng nhập; **10 chỗ đi tắt** tự ghép `username` — `reports/services/activity_service.py`
dòng 100–107, 145–147 và 179–180 (chính Báo cáo tổng hợp, gồm cả cột Nhân sự/Leader của ADR-035), `forms_builder/services/choice_service.py`
47–48, `orders/services/waybill_service.py` 282–283, `orders/services/assignment_service.py`
72, `crm/services/master_grid_service.py` 309, `forms_builder/query.py` 68,
`reports/views.py` 103, `crm/choices.py` 26, `crm/payment_views.py` 66,
`crm/services/statistics_service.py` 317. Lên đơn và biểu mẫu **chụp**
`employee_code(actor)` vào ô dữ liệu (`nguoi_ban`…) lúc tạo — dữ liệu cũ đang
chứa tên đăng nhập.

1. `UserProfile.staff_code`: CharField, viết hoa không dấu, ràng buộc duy nhất
   khi khác rỗng (`UniqueConstraint` có `condition`). Migration `org/0005`, đảo được.
2. Gợi ý mã ở `TaoTaiKhoanForm` theo quy tắc THUANLT (tên + chữ đầu họ + chữ đầu
   tên đệm; trùng thì hậu tố 2, 3…); nếu chốt "User = MÃ_NV" thì điền luôn tên đăng nhập; `SuaHoSoForm` chỉ cho sửa khi hồ sơ chưa có dữ liệu chụp mã.
3. `employee_code()` trả `staff_code`, rỗng thì tên đăng nhập. Thêm bộ lọc `|ma`.
   Quy ước: bảng, danh sách, lịch sử, Excel — **mã trước, tên sau**; lời chào và
   avatar giữ tên. Tìm kiếm nhận cả mã (`reports/views.py` 103, `org/views.py` 45).
4. Sửa 10 chỗ đi tắt cho đi qua `identity`; trong truy vấn ORM dùng
   `Coalesce(F('...__profile__staff_code'), F('...__username'))`.
5. Lệnh `gan_ma_nhan_su_cu`: đổi tên đăng nhập → mã trong các cột định danh của
   bảng động (cột có `meaning=seller` và cột phụ trách), có `--thu` (dry run) và
   ghi nhật ký. Không chạy tự động; ghi vào quy trình phát hành VPS.
6. `du_lieu_mau` gán mã cho 12 tài khoản. Tài liệu: ADR-037, `docs/02`, `docs/04`
   (AC mới → cập nhật bộ đếm `docs/06` theo `tests/test_truy_vet.py`), backlog.

### Kiểm chứng bắt buộc trước khi bàn giao diff

- `pytest -m "not cham"` xanh; bài mới cho A (chips, ba trạng thái, ghim) và B
  (mã duy nhất, gợi ý mã, `employee_code`, nhãn Báo cáo tổng hợp, tìm theo mã,
  lệnh gán mã cũ chạy hai lần không đổi gì thêm) — phân quyền kiểm hai chiều.
- `core/tests/test_giao_dien.py` phải qua: mọi lớp CSS mới trong template đều có
  trong CSS.
- Chrome 1440 / 900 / 390, sáng và tối: bộ lọc mở, thu gọn, ngăn kéo, toàn màn
  hình; cuộn ngang bảng mà cột định danh đứng yên. Ảnh vào biên bản
  `docs/kiem-chung-bo-cuc-bao-cao-tong-hop-<ngày>.md`.
- Chỉ push khi được bảo. VPS phát hành đợt này sẽ cần thêm `migrate` (org/0005)
  và lệnh gán mã cũ — ghi vào mục bàn giao phát hành.

## Bàn giao cho Claude Code CLI trên máy chủ dự án — 17.09.2026: phát hành VPS

Claude Code trên web **không tới được VPS** (mạng môi trường trả
`x-deny-reason: host_not_allowed`, cổng 22 không mở, không có `ssh`). Việc phát
hành làm từ máy có SSH vào VPS. Mở Claude Code CLI trong thư mục kho, dán:

> Đọc `docs/daily-tasks.md` mục "Bàn giao cho Claude Code CLI ... 17.09.2026" và
> làm theo. SSH tới VPS: `<điền>`. Đường dẫn kho trên VPS: `<điền>`. Cách dựng
> image: `<build tại VPS | build ở đây rồi đẩy>`.

### Bối cảnh — đã kiểm chứng, không kiểm lại

- Nhánh làm việc là `codex/crm-update-solar-ui`, **không phải** `main`. Đọc
  `CLAUDE.md` mục "Nhánh và nơi mã đang chạy" trước.
- VPS đang chạy `knjsc-app:0907cdd-grid` (16.09). Đầu nhánh gồm cả `9949062`
  (ADR-033, Codex đẩy chiều 17.09) — xác nhận HEAD bằng `git log -1`.
  **Hai migration mới**, cả hai đảo ngược được, đã thử xuôi ngược:
  `forms_builder.0013_remove_tabledef_delivery_view_all` (bỏ cột cấu hình
  ADR-026, quay lui thì cột về `false`) và `reports.0003_report_revision`.
- Đã diễn tập nâng cấp **hai lần** trên DB có dữ liệu ở trạng thái `0907cdd`
  (lần hai gồm `9949062`): 10.005 dòng trước/sau không đổi, quay lui được,
  `check --deploy` sạch, gunicorn prod khởi động được. Biên bản:
  `docs/kiem-chung-dien-tap-vps-20260917.md` — **đọc trước khi làm**.
- **ADR-033 là thay đổi nghiệp vụ nhìn thấy ngay**: nhân viên Vận đơn thấy và
  **sửa được mọi dòng** của bảng vận đơn (trước chỉ dòng được giao); nút
  "Chế độ: Xem" và trang "Chế độ xem bảng" bị bỏ; thay bằng nút **Tôi / Toàn
  bộ** trên thanh công cụ lưới. Đã kiểm trên DB nâng cấp bằng Chrome với
  `vd.staff`: thấy 10.000 dòng, "Tôi" còn 5.000, sửa dòng người khác ghi được.
  Báo nhân viên Vận đơn trước khi phát hành để họ không tưởng lỗi.
- Quy trình chuẩn ở `deploy/production/README.md`, **đã thêm** hai lệnh
  `configure_erp_reports` và `configure_delivery_daily_report` sau
  `tao_bang_van_don`. Thiếu chúng thì Báo cáo tổng hợp lặng lẽ hiện bản cũ.
  Production đặt `RUN_MIGRATIONS=0` nên entrypoint không chạy giúp — phải gọi tay.
- Khuôn phát hành các lần trước: các tệp `docs/kiem-chung-*-vps-*.md` và các
  commit "Ghi ket qua phat hanh ... tren VPS" — đọc để làm đúng khuôn tên tag
  image, backup, `nginx -t`, kiểm Chrome domain thật.

### Việc, theo thứ tự

1. Trên máy này: `git fetch`, checkout `codex/crm-update-solar-ui`, xác nhận
   HEAD chứa `9949062` (`git log --oneline | grep 9949062`). `pytest -m "not cham"` cho chắc (~2.500 đạt).
2. SSH vào VPS, **không đổi gì**, chỉ ghi nhận: `docker compose ps`, tag image
   đang chạy, dung lượng DB, `manage.py showmigrations reports`. Báo chủ dự án.
3. **Dừng lại**, tóm tắt kế hoạch, hỏi chủ dự án xác nhận **một lần** trước khi
   động vào production. Dữ liệu thật ~1,25 GB, không hoàn tác được như máy ảo.
4. Sau khi được gật: backup DB theo cách các lần trước, **kiểm phục hồi được**.
   Không có backup kiểm được thì không đi tiếp.
5. Dựng/kéo image `knjsc-app:<commit>-<nhãn>` đúng khuôn cũ.
6. Tại `deploy/production`, chạy đúng dãy trong README: `config --quiet` →
   `up -d db broker cache` → `static-owner` → `migrate --noinput` →
   `tao_bang_van_don` → `configure_erp_reports` →
   `configure_delivery_daily_report` → `collectstatic --noinput` →
   `up -d crm erp worker heavy beat proxy`. Rồi `nginx -t` và reload.
7. Kiểm sau phát hành bằng Chrome trên domain thật:
   - ERP `/bao-cao/tong-hop/` phải là bản **mới**: có nút "Toàn màn hình".
   - CRM `/bang-tinh/van_don/` mở được, chân trang "N dòng khớp bộ lọc",
     console không lỗi JS.
   - Đăng nhập chung ERP/CRM còn hoạt động.
8. Ghi một mục ngày vào đầu `docs/backlog.md` và một tệp
   `docs/kiem-chung-phat-hanh-vps-<ngày>.md`: tag image, lệnh đã chạy, số đo,
   phần chưa kiểm. Commit theo khuôn "Ghi ket qua phat hanh ... tren VPS", push
   lên `codex/crm-update-solar-ui` khi chủ dự án bảo.

### Hai thứ sẽ xảy ra sau phát hành — không phải lỗi, báo để chủ dự án quyết

- **Báo cáo Marketing: mọi cột tiền hiện `—` kèm dải vàng**, vì dòng cũ không
  có `loai_tien`; `currency_safe_result()` cố ý không cộng lẫn tiền tệ. Đếm số
  dòng `bao_cao_mkt` trên VPS thiếu `loai_tien` và báo. Điền `loai_tien` cho
  dòng cũ thì số hiện lại — đã kiểm. **Không tự điền**, hỏi loại tiền nào.
- **Hai bảng rỗng** `bao_cao_sale` và `bao_cao_van_don_ngay` sẽ xuất hiện nếu
  VPS chưa từng chạy `configure_*`. Chỉ báo, không xoá.

### Nếu hỏng

Quay lui bằng image `knjsc-app:0907cdd-grid`, rồi `migrate forms_builder 0012`
và `migrate reports 0002` (thứ tự này). Cột `delivery_view_all` về `false` cho
mọi bảng — chấp nhận được vì bản cũ mặc định cũng `false`.
**Không restore DB chỉ để lùi mã** (README production nói rõ).

### Quy tắc

- Không bật cờ `CRM_OPT_*`, không đổi đích nhận đơn, không đụng dữ liệu nghiệp vụ.
- Chỉ push khi được bảo. Không dán mật khẩu/khoá vào đâu; dùng `ssh` có sẵn.
- Báo kết quả thật: lệnh nào đỏ thì dán nguyên log, không tóm tắt cho đẹp.

## 16.09.2026 — Dừng phép đo hỗn hợp, đưa toàn bộ thay đổi lên GitHub

Theo yêu cầu chủ dự án, dừng kiểm tải 10 người Vận đơn + 5 Sale lên đơn. Mới chuẩn bị tài khoản/sản phẩm/bảng nhận đơn trong DB thử; chưa chạy kịch bản hỗn hợp, chưa có kết quả để kết luận. App/DB benchmark local và VPS đã dừng; giữ dữ liệu giả riêng để tái lập. Phạm vi bàn giao Git gồm toàn bộ thay đổi code, migration, kiểm thử và tài liệu hiện có; dữ liệu local/manifest phiên thử trong storage vẫn được gitignore.

## 16.09.2026 — Mốc thực tế: 300.000 dòng + tối đa 10 người

Chủ dự án xác nhận khoảng 100.000 đơn/năm, kiểm dự phòng 300.000 dòng và tối đa 10 người dùng file Vận đơn. Đã đo trên hai DB giả độc lập: 10 người, đọc toàn bảng p95 local/VPS 1,37/5,04 giây; lọc tháng 8.496 dòng 0,83/3,09 giây. Lưu tương ứng toàn bảng 0,49/2,34 giây, theo tháng 0,31/1,57 giây; không lỗi HTTP hoặc sai giá trị cuối ở 8 lượt chính. SQL phiên bản vẫn quét 300k dòng dù lọc tháng; CPU DB VPS gần hết hai core. Browser VPS nhảy dòng 150k vượt chờ 10 giây; chọn ô vẫn khoảng 36 ms. **Chưa đạt mục tiêu mượt**; cần duyệt tác vụ xử lý server/cache rồi đo lại đúng mốc này, không lấy khảo sát 20 người trước làm yêu cầu. Môi trường đo đã dừng, production giữ nguyên. [Bằng chứng và giới hạn](kiem-chung-300k-10-nguoi-20260916.md).


## 16.09.2026 — Đo đồng thời Vận đơn DB trên VPS và local

Đã đo 1/5/10/20 người trên 10.000 dòng giả, 26 cột, môi trường riêng. VPS 20 người: p95 đọc 965 ms, lưu 848 ms, poll 804 ms; vượt mục tiêu lưu/poll. Local tương ứng 288/272/199 ms. Các lượt hợp lệ không lỗi HTTP, kiểm lại giá trị cuối khớp. Browser 9 Locust + 1 Chrome: local cuộn p95 351 ms, VPS 245 ms; chưa chứng minh tối ưu local giữ lợi ích khi có ghi nền. Ghi nhận 409 đọc gây bỏ cache: cần chốt tác vụ riêng để xử lý, chưa sửa ứng dụng hoặc phát hành. [Phương pháp, số đo và giới hạn](kiem-chung-tai-dong-thoi-20260916.md).

## 16/09/2026 — Chọn ô/nhập trong lúc lưu: đã tối ưu và đo local

Đã tách cập nhật vùng chọn/mở/hủy editor khỏi dựng lại nội dung lưới.
40 lượt/10.000 dòng mô phỏng, trình duyệt Codex 1280×720, giữ request lưu:
p95 chọn/mở/nhập ~33–34 ms; baseline cũng ~34 ms nhưng một lượt chọn 58,1 ms.
Bản cuối max 34,2 ms; DOM tạo mới giảm 51.891 → 466. Đây là phép đo tới hai
rAF của fixture, không phải số đo API/VPS hoặc bảo đảm trên mọi máy.
Giữ nháp mới khi phản hồi cũ về; lỗi lưu và Undo/Redo đã kiểm; 48 test server
và nhóm Node liên quan đạt. Local, chưa push/VPS. Không đánh dấu toàn bộ bảy
hạng mục tối ưu hoàn thành hoặc coi kiểm này là kiểm bộ nhớ dài hạn.
[Chi tiết](kiem-chung-nhap-khi-luu-20260916.md).

Mở lại file này mỗi ngày để xem việc còn nợ. Thêm nhật ký theo ngày thực tế;
không tự chuyển việc chưa kiểm chứng sang hoàn thành. Đây là sổ công việc,
không phải lịch tự chạy hoặc nhắc việc tự động.

## Bàn giao cho Codex ở PC nhà — 15/09/2026

- Repository: `CyrusDev1512/KNJSC`, nhánh `codex/crm-update-solar-ui`.
  Pull nhánh này trước khi đọc; kiểm Git và giữ thay đổi riêng của máy đó.
- Ý định đã chọn: **phương án 1**, tải dữ liệu theo vùng nhìn/tải trước có
  giới hạn, kết hợp cải thiện vẽ lưới. Không tải toàn bảng vào RAM theo
  phương án 2/3, không thay framework hoặc viết lại bằng Canvas.
- Bước tiếp theo khi chủ dự án yêu cầu tiếp tục: đo baseline local, trình
  bày kế hoạch cụ thể theo AGENTS.md; sau khi duyệt thì tự hoàn tất sửa,
  kiểm thử và tài liệu. Việc chọn hướng không phải xác nhận mọi chi tiết
  nghiệp vụ hoặc quyền. Lệnh hiện tại chỉ yêu cầu ghi bàn giao và push
  những gì đang có, chưa yêu cầu bắt đầu viết tối ưu.
- Đợt đầu ưu tiên điều phối request, bỏ yêu cầu đọc lỗi thời, cache theo
  vùng thực dùng và giảm dựng/cập nhật DOM. Đo server/sync để quyết định
  phần cần làm tiếp trong 7 hạng mục; không tự bật tất cả cờ toàn hệ thống.
- Bàn giao mong muốn của đợt tối ưu: bản chạy local, so sánh trước/sau cùng
  dữ liệu, hồi quy thao tác ô và push GitHub khi được yêu cầu. Các khoảng
  ms bên dưới là kỳ vọng, không phải tốc độ đã đo hay điều kiện được phép
  bỏ kiểm thử. Không dùng ước lượng thời gian trong chat làm giới hạn công việc.
- Bảng thử “Vận đơn optimize” trên VPS là ý định trước đó, **chưa tạo**;
  tách khỏi bước tối ưu local, không tự deploy hoặc chạm bảng gốc. VPS có
  task từ máy khác đang làm; phải kiểm lại trạng thái trước thao tác.
- Lỗi thiếu 3.333 dòng là tác vụ nhập dữ liệu riêng. Chủ dự án nhắc đối
  soát đã tắt; không tự thêm lựa chọn, bật chức năng hay nhập bù.
- File Excel/video/ảnh trong Downloads, Videos, Temp và chứng cứ trong
  `storage/` ở PC hiện tại không đi theo Git. Nếu PC nhà không có, đọc
  các phát hiện đã ghi rồi chuẩn bị dữ liệu thử tương đương để đo; không
  tuyên bố đã xem lại video hoặc chạy lại test khi chưa có chứng cứ.
- Script báo cáo mẫu được lưu để truy vết việc đã làm; không tự chạy lại
  trên VPS. Không có mật khẩu/private key trong gói bàn giao này.

## 15/09/2026 — Tối ưu lưới CRM, phương án 1

**Trạng thái:** đã chọn hướng; đã khảo sát code/cấu hình VPS, chưa triển khai
các thay đổi dưới đây. Chưa tạo bảng thử “Vận đơn optimize”.

**Mục tiêu:** tải theo vùng nhìn, tải trước vùng lân cận có giới hạn và giảm
chi phí vẽ lưới. Giữ nghiệp vụ, quyền, nháp trong RAM, Undo, CAS và autosave.
Bảng thử dự kiến sao chép cấu trúc/dữ liệu Vận đơn DB; phải đối chiếu số dòng
thực tế và tách khỏi bảng gốc, không làm ảnh hưởng instance VPS khác.

| Trạng thái | Phần | Hiện trạng qua code | Hướng xử lý |
|---|---|---|---|
| Chưa làm | Điều phối tải | Yêu cầu dữ liệu khi vùng cần vẽ còn thiếu; chưa có ưu tiên theo hướng cuộn | Ưu tiên vùng đang nhìn, tải trước phía đang kéo; giới hạn yêu cầu đồng thời |
| Chưa làm | Yêu cầu lỗi thời | Đổi bộ lọc có hủy yêu cầu; cuộn sang vùng khác chưa có cơ chế tương đương | Hủy hoặc hạ ưu tiên yêu cầu đọc không còn cần, tránh vùng mới phải chờ |
| Chưa làm | Cache | Giới hạn 10 khối nhưng việc đọc ô không cập nhật mức độ sử dụng của khối | Giữ vùng đang nhìn và vùng vừa dùng; tránh phản hồi cũ về muộn đẩy vùng cần dùng ra khỏi cache |
| Chưa làm | Vẽ và chọn ô | Có tái sử dụng DOM; nhánh bỏ qua hàng không đổi đang tắt. Cuộn vẫn cập nhật cả trạng thái phụ | Kiểm chứng nhánh tối ưu có sẵn; giảm cập nhật ô, tiêu đề và thanh trạng thái khi không thay đổi |
| Chưa làm | Server và dữ liệu truyền | Đường đọc thông thường tính tổng, phiên bản và dựng metadata mỗi khối; trả nhiều thuộc tính cho từng ô | Đo SQL, thời gian dựng JSON, dung lượng truyền; giảm phần lặp lại có chi phí đáng kể |
| Chưa làm | Đồng bộ nền | Kiểm tra mỗi 8 giây; đường hiện tại có thể xóa cache khi bảng thay đổi | Cập nhật hoặc vô hiệu hóa đúng vùng bị ảnh hưởng, giữ kiểm quyền và nháp |
| Chưa làm | Bộ nhớ, lưu nền | Cache, nháp và Undo cùng tồn tại | Kiểm khi cuộn lâu và đang chờ lưu; tải trước không được gây mất nháp hoặc làm lưu chậm |

### Bằng chứng và giới hạn

- Đọc cấu hình Django trong container CRM VPS ngày 15/09/2026:
  `CRM_OPT_READ`, `CRM_OPT_RENDER`, `CRM_OPT_SYNC` đều False.
- Code có tái sử dụng node qua `syncRow`/`updateBody`; không kết luận mọi lần
  cuộn đều thay toàn bộ DOM. Nhánh bỏ qua dựng lại hàng chưa đổi có cờ riêng.
- `van_don_db` không thuộc profile vận đơn mà đường đọc/sync tối ưu hiện tại
  yêu cầu. Chỉ bật cờ không đủ; không đổi workflow nghiệp vụ để lách điều kiện.
- Nguồn: `app/static/js/master-grid.js`,
  `app/crm/services/master_grid_service.py`, `app/crm/services/optimization.py`,
  `app/crm/master_views.py`; đối chiếu ADR-024 và ADR-027 trước triển khai.
- Video người dùng cho thấy khoảng trống/đợi thông tin cỡ 1–1,5 giây ở một
  đoạn kéo nhanh. Đây là quan sát video, chưa phải trace mạng/CPU hay p95.

### Dự đoán trước/sau — giả định kỹ thuật, chưa phải kết quả đo

Giả định: cùng PC, trình duyệt, mạng và bộ lọc; khoảng 6.667–10.000 dòng,
server không quá tải. Khoảng dự đoán dưới đây dùng để lập kế hoạch, sẽ thay
bằng số đo trên cùng dữ liệu. Không áp cho mọi thiết bị hoặc mọi lần thao tác.

| Tình huống | Trước, bằng chứng hiện có | Sau, khoảng kỳ vọng có điều kiện |
|---|---|---|
| Cuộn vào vùng đã có cache | Chưa đo riêng | Khoảng 16–50 ms từ thao tác đến khung có dữ liệu; không chờ request đọc |
| Cuộn đều cùng hướng | Có đoạn chờ cỡ 1–1,5 giây trong video kéo nhanh, chưa có baseline cuộn đều | Nếu tải trước kịp: khoảng 16–100 ms chờ hiển thị; giảm mạnh khoảng trống |
| Nhảy xa tới vùng chưa tải | Video có khoảng chờ; chưa tách chính xác loại thao tác | Khoảng 200–600 ms nếu request đọc hoàn tất trong 150–500 ms và xử lý/vẽ thêm 20–100 ms; mạng/server chậm vẫn có thể vượt 1 giây |
| Chọn ô, gõ khi đang lưu | Chưa đo trên dữ liệu đối chiếu | Mục tiêu phản hồi nhìn thấy dưới 50 ms; không đồng nghĩa đã lưu server trong 50 ms |
| RAM, CPU, dung lượng truyền | Chưa đo baseline | Cache có giới hạn; tải trước có thể tăng RAM và byte tải so với không tải trước. Chưa dự đoán phần trăm giảm |

Không hứa toàn hệ thống nhanh hơn một hệ số cố định; phương án 1 không đảm
bảo nhảy ngẫu nhiên tới vùng chưa tải sẽ tức thì. Giữ lịch gửi autosave
500 ms/tối đa 2 giây theo quyết định đã chốt.

### Kiểm chứng cần thực hiện

- [ ] Chụp baseline: cùng bộ dữ liệu/quyền, cuộn xuống/lên, kéo thanh cuộn
  nhảy xa, vùng có cache và chưa có cache, cuộn ngang, hàng cao/cột ghim.
- [ ] Đo riêng thời gian server, truyền/đọc JSON, cập nhật DOM và khung hiện dữ liệu.
- [ ] Thử phản hồi về sai thứ tự, đổi lọc khi đang tải, lỗi mạng, đồng bộ từ
  người khác và thay đổi quyền; không hiển thị dữ liệu cũ dưới số dòng mới.
- [ ] Kiểm sửa ô tiếng Việt, dán vùng, Undo/Redo, lỗi lưu/xung đột và cuộn
  trong khi chờ lưu; chỉ ghi vào dữ liệu thử được phép.
- [ ] So sánh trước/sau và kiểm bộ nhớ sau nhiều lần cuộn. Cập nhật kết quả,
  chưa kiểm chứng và diff; không tự bật toàn hệ thống hoặc deploy.

## 15/09/2026 — Vì sao nhập 10.000 dòng chỉ có 6.667

**Trạng thái:** đã xác định nguyên nhân bằng đọc dữ liệu; chưa sửa cấu hình,
chưa nhập bù, không chỉnh bảng gốc.

- File `C:/Users/PC/Downloads/mau-import-van-don-db-10000.xlsx`, sheet
  `Du lieu Van don DB`, tiêu đề hàng 3, có đúng 10.000 hàng dữ liệu.
- Cột 26 “Đối soát kế toán”: 6.667 ô trống, 3.333 ô có `Đã về TK`.
- VPS: BackgroundJob #3, target `van_don_db`, tạo lúc **08:23:18 ngày
  15/09/2026 giờ Việt Nam**, đã xử lý 10.000, tạo 6.667, lỗi 3.333.
- Job giữ 200 lỗi đầu; tất cả cùng thông báo giá trị `Đã về TK` không có
  trong danh sách cột “Đối soát kế toán”, cột chưa có danh sách chọn.
  Hàng lỗi đầu trong Excel: 6, 9, 12, 15, 18, 21…
- Cấu hình hiện tại `doi_soat` là kiểu choice, nguồn lựa chọn rỗng.
  Tổng DataRecord còn hoạt động của bảng trên VPS là 6.667.
- `preview_error_count=0` nhưng worker ghi lỗi: lần nhập đó không báo được
  lỗi này ở bước xem trước. `status=done` nghĩa là xử lý xong, không có nghĩa
  tất cả dòng nhập thành công.

Kết luận: 3.333 dòng bị từ chối lúc nhập do danh sách lựa chọn, không phải
3.333 dòng đã lưu nhưng renderer không vẽ được. Tối ưu cuộn không phục hồi
các dòng này. Cần duyệt riêng cách khắc phục nhập dữ liệu, đối chiếu cấu hình
và quy tắc đã chốt, rồi chỉ nhập phần thiếu sau kiểm trùng; không nhập lại
toàn bộ 10.000 dòng một cách mù quáng.

### Nhật ký lần mở tiếp theo

**Bổ sung 15/09/2026 — Chủ dự án nhắc chức năng đối soát đã bị tắt:**
không coi đề xuất thêm lựa chọn `Đã về TK` là phương án được duyệt. ADR-025
ghi quyết định ngày 14/09 tạm khóa kho chứng từ bằng
`PAYMENT_DOCUMENTS_ENABLED=0`, giữ Bill dạng text; quyền xác nhận đối soát
không được mở. Cột dữ liệu `doi_soat` vẫn tồn tại độc lập và đang được
validator nhập file kiểm tra. Nguyên nhân từ chối 3.333 dòng đã xác định,
nhưng cách xử lý giá trị của cột đang ngừng dùng chưa chốt; không bật lại
chức năng, tự bỏ dữ liệu đối soát hoặc nhập bù trước khi chốt phạm vi.

Thêm mục ngày mới cùng việc đã làm, bằng chứng, việc còn nợ và bước tiếp theo;
giữ nguyên các phát hiện ngày 15/09/2026 để truy vết.
