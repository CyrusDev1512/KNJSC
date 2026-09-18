# Hướng dẫn cho AI hỗ trợ viết mã

> Cập nhật 18.09.2026 (ADR-036 một bảng vận đơn, ADR-037 mã nhân sự, ADR-038 báo cáo Marketing,
> ADR-031 bổ sung bảy thị trường); lần trước 17.09 cho đúng nhánh đang chạy thật (`codex/crm-update-solar-ui`, phát hành VPS).

Đọc file này trước khi sửa bất kỳ mã nguồn nào trong dự án.

Đọc [AGENTS.md](AGENTS.md) cho quy tắc phối hợp chung đã chốt của dự án; khi
hướng dẫn ở đây khác với AGENTS.md, dùng AGENTS.md. Hai điều của AGENTS.md hay bị
quên nhất: **mọi tác vụ sửa mã phải được chủ dự án duyệt cách làm trước**, và
**chỉ commit, push, tạo PR hay gộp khi được yêu cầu**.

---

## Bắt đầu một phiên mới — đọc bốn chỗ này trước

**Lịch sử hội thoại không theo kho mã.** Đổi máy là mất, và điều đó không sao:
mọi thứ cần biết đều đã ghi vào `docs/`. Bốn chỗ dưới đây đủ để làm tiếp mà
không hỏi lại người dùng những gì họ đã trả lời.

| Đọc | Trả lời câu gì |
|---|---|
| `docs/backlog.md` **các mục ghi ngày ở đầu tệp** rồi **mục 0** | Việc gần nhất và **còn nợ những gì**; từ 14.09 mỗi tác vụ là một mục ghi ngày ở đầu tệp, mục 0 là bản tóm cũ hơn |
| `docs/backlog-kanban.md`, `docs/test-log.md` | Việc đang ở cột nào và **từng lỗi `TL-xx`** kèm mức, chỗ sai, blocker. Lưu ý: TL-01 → TL-34 rà trên lưới HTMX cũ (07.09); lưới đã thay, phải rà lại trước khi sửa |
| `docs/quyet-dinh/` | Vì sao làm thế. **Đừng quyết lại những gì đã chốt.** Bảng ở `README.md` trong đó đã đủ tới 038 (18.09: 036 một bảng vận đơn, 037 mã nhân sự, 038 báo cáo Marketing); hai tệp cùng số 022 |
| `docs/kiem-chung-*.md`, `docs/06-ke-hoach-kiem-thu.md` | Mỗi tác vụ từ 09.09 có một biên bản kiểm chứng: đã đo gì, số bao nhiêu, còn gì chưa kiểm; 06 là kế hoạch kiểm thử chung |

`docs/dashboard-tien-do.html` là tiến độ theo giai đoạn tới 08.09; sau đó tiến độ
ghi trong backlog và kanban. `docs/USER_INQUIRY.md` gom câu hỏi nghiệp vụ chờ chủ
dự án (H7 quyền nhập tiền còn mở). `docs/daily-tasks.md` là việc bàn giao giữa máy.

### Nhánh và nơi mã đang chạy

- **Nhánh làm việc chính là `codex/crm-update-solar-ui`**, không phải `main`. `main`
  dừng ở 08.09 và tụt sau khoảng 50 commit; VPS và máy chủ dự án chạy từ nhánh codex.
  Tách nhánh mới từ nhánh codex; PR trỏ về nhánh codex trừ khi chủ dự án nói khác.
- **VPS thật** (2 nhân, 4 GB): `deploy/production/compose.yml`, nginx trước hai
  hostname ERP và CRM, năm container `crm`, `erp`, `worker`, `heavy`, `beat` cùng một
  image tag bất biến `knjsc-app:<commit>-<nhãn>`, DB 1,25 GB. Phát hành do Codex làm
  từ máy chủ dự án: backup, `manage.py check`, `up -d`, `nginx -t` rồi reload, Chrome
  domain thật. Claude Code trên web **không** tới được VPS lẫn máy chủ dự án.
- Máy ảo của Claude Code trên web là bản clone riêng: chạy được Postgres, Docker,
  pytest, Playwright, nạp dữ liệu giả; mọi thứ ở đó không đụng máy ai.

### Bật hệ thống — nháy đúp một tệp, máy nào cũng vậy

```
KN JSC.bat                   Windows — ở thư mục gốc; clone về, nháy đúp, xong
./scripts/cap-nhat-local.sh  Mac và Linux
```

`KN JSC.bat` tự kéo mã mới từ GitHub (có git và có mạng), tạo hoặc làm mới lối
tắt "KN JSC" có logo ngoài Desktop, mở Docker Desktop nếu chưa chạy, bật
container, đợi web lên rồi mở trình duyệt ở `http://127.0.0.1:8020/`. Mã trên
máy **khác lần chạy trước** (dù ai kéo; nhớ bằng `storage/.kn-jsc-lan-truoc`) thì
tự `migrate`, `tao_bang_van_don`, khởi động lại worker, và dựng lại image chỉ khi
Dockerfile, requirements hay entrypoint đổi. Máy sạch thì tự nạp dữ liệu mẫu và
đặt mật khẩu mẫu một lần (`cap_nhat_mat_khau_mau`). Kéo mã **thất bại** (kho đang
gộp dở, sửa tay chưa commit, mất mạng) thì màn hình đen nói rõ và vẫn bật bản đang
có; nó in nhánh đang đứng, vì `git pull` chỉ kéo nhánh đang đứng.

`scripts\cap-nhat-local.bat [nhánh]` là bản "làm hết cho chắc": chuyển nhánh,
kéo mã, luôn dựng lại image, migrate, nạp dữ liệu mẫu. Máy chưa có lối tắt: gửi
`scripts/Cai dat KN JSC.bat`, nháy đúp một lần ở bất kỳ đâu.

Bên trong các tệp đó chỉ là hai lệnh dưới đây, muốn làm tay thì làm:

```
docker compose -f deploy/docker-compose.yml up -d
docker compose -f deploy/docker-compose.yml exec web python manage.py du_lieu_mau
docker compose -f deploy/docker-compose.yml exec web python manage.py configure_erp_reports
docker compose -f deploy/docker-compose.yml exec web python manage.py configure_delivery_daily_report
```

**Vì sao cần lệnh thứ hai.** Cơ sở dữ liệu không theo kho mã, nên máy mới dựng
xong là hệ thống trống, **không có tài khoản nào để đăng nhập**. `du_lieu_mau`
tạo 12 tài khoản ba bộ phận bốn cấp bậc, bảng Báo cáo Marketing, biểu mẫu, sản
phẩm và dữ liệu mẫu cho nhóm Nội bộ. Danh sách tài khoản kèm mật khẩu ở
`docs/tai-khoan-mau.md`; `quantri` vào được trang quản trị Django ở `/quan-tri/`.

**Vì sao hai lệnh cuối, và vì sao phải đứng sau.** Nguồn báo cáo (ADR-022) cũng
là metadata của bảng động: `migrate` chỉ tạo bảng rỗng, ánh xạ cột do
`configure_erp_reports` sinh ra. Thiếu chúng thì màn hình Báo cáo tổng hợp **lặng
lẽ** rơi về bản tổng quát cũ, không báo gì. Và chúng **bỏ qua bảng chưa tồn tại mà
không báo lỗi**, trong khi `bao_cao_mkt` cùng bộ phận `sale` là do `du_lieu_mau`
tạo — chạy trước `du_lieu_mau` là chạy hụt. Bốn tệp launcher đã xếp đúng thứ tự này.

Riêng **bảng vận đơn** thì không cần lệnh nào: `deploy/entrypoint.sh` gọi
`tao_bang_van_don` ngay sau `migrate`, vì bảng động (quyết định 001) không do
`migrate` sinh ra. Từ ADR-036 lệnh này tạo hoặc nâng cấp tại chỗ **một** bảng `van_don`.

### Hai dịch vụ, ba bảng vận đơn

**KN ERP** (dịch vụ `web`, cổng 8020, `knjsc/urls.py`): đăng nhập, nhân sự, biểu
mẫu, báo cáo ngày và báo cáo hoạt động (ADR-022, 032), Bảng dữ liệu **chỉ đọc với
mọi bảng** (ADR-014), nhóm Nội bộ. Lên đơn không còn ở ERP, chỉ còn URL GET chuyển
tiếp sang CRM (ADR-023).

**KN CRM** (dịch vụ `bangtinh`, cổng 8021, `knjsc/urls_bangtinh.py`, settings
`knjsc.settings.bangtinh`): nơi duy nhất sửa số liệu. Khung sidebar theo Teeze
(`templates/crm/base_crm.html`, `crm/navigation.py`) cho trang chủ tổng quan, mục
Bảng tính = trang thư mục `/thu-muc/` (cây Bộ phận ▸ Quý ▸ Tháng ▸ bảng), Nhập tệp,
Cấp quyền, Lên đơn, Thống kê `/thong-ke/`. (Bảng nhận đơn đã bỏ, ADR-036.)
Lưới `/bang-tinh/<mã bảng>/` toàn màn hình, chỉ lưới có nút ← và nó về thư mục CRM,
không về ERP (ADR-012, 015). **Leader như Manager trong bộ phận mình**
(`grant_service._quan_ly_bo_phan`), cấp quyền cho người khác vẫn Manager.
Bài kiểm của `crm/tests` chạy ở URLconf 8021 nhờ `crm/tests/conftest.py`.

**Lưới là một bộ duy nhất cho mọi bảng** (ADR-021, 027): `templates/crm/master_grid.html`
+ `static/js/master-grid.js` (cùng `master-working-copy.js`, `master-row-geometry.js`,
`grid-focus.js`). Máy chủ trả JSON theo khối 100 dòng (`du-lieu/`), ghi bằng
`luu-json/` có so phiên bản CAS (409 khi ô vừa bị người khác đổi) và biên nhận
chống lặp (`GridMutationReceipt`), lịch sử ô (`GridCellHistory`), tự lưu 500 ms,
nhập ngay trong ô, ghim cột bằng `position: sticky`. Lưới **thao tác như Excel**
(ADR-033, 18.09): bấm chỉ chọn ô, gõ phím là nhập ngay, Enter/F2/bấm đúp mở ô, Tab/Enter
chỉ chuyển ô; không còn nút Chế độ Xem/Chỉnh sửa. Xoá Quốc gia thì Loại tiền trống (ADR-031 bổ sung). Renderer HTML/HTMX ghi ô cũ
(`bang-tinh.js`, `bang-tinh-o.js`, `_o.html`) **đã bỏ, không đưa lại**. Profile
nghiệp vụ của bảng lấy qua `forms_builder/record_policies.py` (`register_grid`,
`register_workflow`), không nhận diện nghiệp vụ bằng mã cột. Cột **Trùng** nằm trong
`crm/services/waybill_grid.py` cùng các hook profile (ADR-036).

**Một bảng vận đơn duy nhất** (ADR-036, 18.09): `van_don`, tên hiển thị **Vận đơn mới**,
`ACTIVE_WAYBILL_TABLE_CODE = WAYBILL_TABLE_CODE = "van_don"`. Cấu trúc = 25 cột chuẩn
`waybill_service.COLUMNS` + 9 cột giữ từ tệp thật (`dispatch_service.EXTRA_COLUMNS`) + `sl_*`
theo sản phẩm; `tao_bang_van_don` tạo mới hoặc nâng cấp tại chỗ (`waybill_service.upgrade_schema`).
crmThuận (`van_don_moi`) và Vận đơn DB (`van_don_db`) đã **xoá cứng** theo quyết định chủ dự án
(lệnh `xoa_bang_van_don_cu --dong-y-xoa-cung --backup-da-lam`, chỉ chạy sau backup); trang Bảng
nhận đơn, `receives_orders` đã bỏ (migration 0014). Dòng không có Chi tiết sản phẩm vẫn tạo được.
Hook lưới ở `crm/services/waybill_grid.py` gộp cột Trùng với profile (TL-35/36 đóng).

Bảng có `workflow = "waybill"` mang profile Vận đơn: phân công Vận đơn/CSKH/Marketing
(`WaybillAssignment`, ADR-020); **nhân viên Vận đơn thấy và sửa mọi dòng, nút Tôi /
Toàn bộ (`?cua_toi=1`) lọc theo cột phụ trách của bộ phận mình** (ADR-033 thay
ADR-026, 17.09; Sale/CSKH vẫn theo phân công), chi tiết sản phẩm `WaybillItem`, trạng thái
thanh toán sửa trực tiếp (ADR-025; kho chứng từ tắt bằng `PAYMENT_DOCUMENTS_ENABLED`).
Tiền theo quốc gia US/USD, CA/CAD, PH/PHP, EU/EUR, KR/KRW, JP/JPY, AU/AUD (ADR-031 và bổ sung
18.09; KRW chưa có tỉ giá), PTTT chỉ Zelle/PayPal. **Định danh nhân sự là mã `UserProfile.staff_code`**
(ADR-037, quy ước `THUANLT`): mọi chỗ hiện mã trước tên sau qua `core/identity.py` và bộ lọc `|ma`,
`|ma_ten`; không tự ghép `username`; tài khoản mới đăng nhập bằng mã.

**Cờ tối ưu `CRM_OPT_*`** (ADR-024) mặc định tắt, trên VPS cũng tắt: READ/SYNC gây
lỗi mở editor, RENDER chưa thấy lợi. Không bật cờ khi chưa có biên bản kiểm chứng.

**Nhóm Nội bộ** (ADR-017) là năm app nhỏ cùng khuôn: `documents` (Tài liệu),
`feed` (Bảng tin), `taskboard` (Công việc), `culture` (nhãn hiển thị **Đánh giá nhân
sự**), `resources` (Tài nguyên). Phụ thuộc một chiều: `feed → culture, org`;
`culture → orders`; không ai import `feed`. Bảng tin, Đánh giá nhân sự, Tài nguyên
là của toàn công ty (Q69, Q70) nên không có `in_scope`; Tài liệu lọc theo bộ phận ở
`documents/managers.py`, Công việc theo cấp bậc ở `taskboard/managers.py`. Bảng xếp
hạng doanh số là ngoại lệ phạm vi có chủ ý (Q71), quy VND bằng `EXCHANGE_RATES_VND`
(số tạm, N11). Hai tác vụ nền `culture.thuong_sao_thang` (ngày 1, 01:00) và
`feed.thiep_sinh_nhat` (06:00); `entrypoint.sh` chạy bù khi bật máy. Ghi nhận đi
từ trên xuống (Q75). Khuôn dùng chung ở `core`: `AliveManager`, `pagination_context`,
`filter_query`, `htmx.is_htmx`, bộ lọc `|ten`, thẻ `{% avatar %}`.

### Chạy kiểm thử

```
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest
```

Kèm đo bao phủ thì thêm `--cov`. Bỏ bài chạy chậm thì thêm `-m "not cham"`; bài
trình duyệt mang dấu `trinh_duyet` và tự bỏ qua khi thiếu Chromium — bỏ qua không
phải là đã kiểm. Ngoài Docker: từ `app/`, `python -m pytest --ds=knjsc.settings.test`
với Postgres đang chạy. **Không chạy hai pytest cùng lúc** trên một database kiểm thử.

**Đừng chạy `migrate ... zero` trên cơ sở dữ liệu phát triển** — nó xoá bảng
thật. Bài kiểm thử tự lo việc đó trên cơ sở dữ liệu riêng.

`tests/test_truy_vet.py` đối chiếu docs/04 với docstring bài kiểm. Ba bài đỏ có
sẵn đã sửa 17.09: bài đọc được cả ba dạng bảng của docs/04 (bốn, ba và hai cột)
nên AC-22.x, AC-24.x và AC-27.3 không còn bị coi là mã bịa, và AC-11.23 lấy lại
docstring bị rút gọn mất. Thêm AC mới thì cập nhật bộ đếm ở docs/06 theo thông
báo của bài đó.

**Kiểm tải và dữ liệu giả.** Mốc thực tế chủ dự án chốt 16.09: khoảng 100.000
đơn một năm, kiểm dự phòng **300.000 dòng, tối đa 10 người**; ngưỡng p95 đọc 1 s,
ghi 0,5 s, poll 0,3 s (`core/constants.py`, `PERF_*`). Số đã đo và điểm nghẽn ở
`docs/kiem-chung-300k-10-nguoi-20260916.md`. Công cụ:

| Lệnh | Làm gì |
|---|---|
| `manage.py seed_perf --so-dong 100000 --bang-sale` | Dòng giả `PERF-*` vào `van_don` cũ + bảng Sale có cột tính sẵn (ADR-016) |
| `manage.py nap_du_lieu_van_don` | Đúng 10.000 mẫu `MAU-*` có chi tiết, thanh toán, phân công vào `van_don` |
| `manage.py nap_khach_mau --so-khach 300000` | 375.000 dòng `KH-*` vào `van_don`, 20 % khách mua lại (AC-10.9); `--xoa-cu` để xoá |
| `manage.py do_hieu_nang`, `tests/perf/locustfile_*.py`, `scripts/kiem-tai-kn-crm.*` | Đo một người và nhiều người; báo cáo vào `storage/perf/` |

Mọi lệnh dữ liệu giả từ chối chạy khi DEBUG tắt. Ghi hàng loạt qua
`DataRecord.bulk_save`; cột tính sẵn trên bảng lớn tính lại ở tác vụ nền
(`table_service.schedule_resync`, ADR-016) — sửa hai chỗ đó thì chạy lại
`crm/tests/test_kiem_tai.py`.

### Skill dùng chung cho Codex và Claude

Nội dung thật của 10 skill nằm **một bản duy nhất** ở `.agents/skills/<tên>/`
(Codex đọc thẳng). Claude Code chỉ khám phá `.claude/skills/<tên>/SKILL.md`, nên ở
đó có 10 **tệp cầu nối** sinh tự động: chép `name` và `description` để Claude tự
chọn skill, thân tệp chỉ bảo đọc tệp thật. Cách làm và lý do (không symlink vì
Windows, không chép nội dung vì lệch) ở `docs/dong-bo-ai-nhieu-may.md`.

```
python scripts/dong-bo-skill.py --check         # kiểm nguồn, hash, cầu nối
python scripts/dong-bo-skill.py --tao-cau-noi   # sửa skill xong thì sinh lại cầu nối
```

`app/tests/test_dong_bo_skill.py` chạy cùng kiểm tra đó trong pytest. Sửa skill:
chỉ sửa ở `.agents/skills`, cập nhật hash trong `.agents/skill-sources.json`, chạy
`--tao-cau-noi`, rồi commit cả hai thư mục. Đừng sửa tay tệp trong `.claude/skills`.

Năm skill quy trình: `test-driven-development`, `verification-before-completion`,
`performance-optimization`, `web-perf`, `performance-testing-skill`. Năm skill
thiết kế: `impeccable` (hướng dẫn thủ công, hồ sơ ở `.agents/design-state`, không tự
chạy engine hay hook, không tạo lại `.impeccable` ở gốc), `design-taste-frontend`,
`redesign-existing-projects`, `high-end-visual-design`, `minimalist-ui`. Bốn agent ở
`.claude/agents` là của Impeccable, không tự kích hoạt. Dự án dùng HTMX, CSS/JS
thuần (ADR-005): gợi ý React, Tailwind, GSAP trong skill phải chuyển sang thuần;
quy tắc 8 "không thêm thư viện" đứng trên skill. Hướng giao diện đang chạy là
Solarpunk Office (ADR-028, `DESIGN.md`); PRODUCT.md còn ghi hướng Google Workspace
07.09, hai bên chưa hợp nhất — hỏi trước khi đổi diện mạo.

### Đã thoả thuận với người dùng

| Thoả thuận | Vì sao |
|---|---|
| **Duyệt cách làm trước, rồi tự làm trọn** — nêu mục tiêu, phạm vi, cách sửa, cách kiểm; được gật thì làm hết, không hỏi từng bước | AGENTS.md mục 1 |
| **Chỉ commit, push, tạo PR, gộp khi được yêu cầu**; bàn giao bằng diff | AGENTS.md mục 1 |
| **Không dừng lại xin nghiệm thu từng giai đoạn.** Cứ chạy kiểm thử, báo cáo kết quả thật, rồi làm tiếp | Người dùng chốt dồn nghiệm thu về một đợt — backlog **V4** và **V5** |
| Làm từng giai đoạn cho chạy thật, không dựng vỏ hết màn hình trước | Backlog **Q22** |
| Mỗi lượt xong thì ghi một mục có ngày ở đầu `docs/backlog.md`, kèm biên bản `docs/kiem-chung-<việc>-<ngày>.md` khi có đo | Không thì phiên sau không biết đang ở đâu |
| Ưu tiên hiện tại: sửa feedback khách hàng; nhắc việc chủ động và AI là giai đoạn sau | Chủ dự án chốt 09.09.2026 |

---

## Dự án là gì

Hệ thống vận hành nội bộ cho công ty thương mại điện tử xuyên biên giới.
Ba bộ phận Sale, Marketing, Vận đơn làm việc trên cùng một hệ thống, mỗi người
chỉ thấy dữ liệu trong phạm vi quyền của mình; thêm Kế toán và CSKH ở bảng vận đơn.

**Quy mô:** dưới 100 người dùng, tối đa 50 người đồng thời toàn hệ thống, tối đa 10
người cùng lúc trên file Vận đơn, khoảng 100.000 đơn mỗi năm, kiểm dự phòng 300.000.

**Tài liệu đầy đủ nằm ở `docs/`.** Đọc `docs/03-thiet-ke-ky-thuat.md` trước khi
thiết kế bất cứ thứ gì.

---

## Công nghệ

| Thành phần | Lựa chọn |
|---|---|
| Khung ứng dụng | Django 5.2 |
| Cơ sở dữ liệu | PostgreSQL 16 |
| Giao diện | HTMX cho ERP; lưới CRM là JS thuần đọc JSON; không dùng khung giao diện riêng |
| Tác vụ nền | Celery với Redis (hàng đợi `worker` và `heavy`) |
| Đóng gói | Docker Compose; VPS theo `deploy/production/` |
| Đọc ghi Excel | openpyxl |

Lý do chọn ghi ở `docs/quyet-dinh/005-chon-django.md`.

**Không thêm khung giao diện như React hay Vue.** Bảng dữ liệu là màn hình phức
tạp nhất của KN ERP và HTMX làm được — lọc, sắp xếp, phân trang. Sửa ô là việc
của lưới KN CRM (ADR-014), không phải của Bảng dữ liệu.

---

## Đọc gì trước khi làm

| Việc | Đọc trước |
|---|---|
| Thêm chức năng mới | `docs/02-yeu-cau-san-pham.md` — tìm mã FR tương ứng |
| Sửa cấu trúc dữ liệu | `docs/03-thiet-ke-ky-thuat.md` mục 2 |
| Đụng tới phân quyền | `docs/03-thiet-ke-ky-thuat.md` mục 3; ADR-020, 033 cho vận đơn |
| Viết truy vấn | `docs/03-thiet-ke-ky-thuat.md` mục 5 |
| Viết kiểm thử | `docs/04-tieu-chi-nghiem-thu.md` — tìm mã AC tương ứng |
| Đụng lưới CRM | ADR-021, 027, 033; `crm/services/master_grid_service.py`, `static/js/master-grid.js` |
| Đụng vận đơn | ADR-018, 020, 025, 031, 033, 036; `orders/services/waybill_service.py`, `orders/services/assignment_service.py` |

---

## Không được làm

| # | Cấm | Vì sao |
|---|---|---|
| 1 | Viết truy vấn dữ liệu ngoài tầng truy cập | Phạm vi quyền phải áp ở một chỗ duy nhất |
| 2 | Đặt quy tắc nghiệp vụ trong tầng xử lý yêu cầu | Tác vụ nền không dùng lại được |
| 3 | Lọc dữ liệu theo quyền ở tầng giao diện | Gọi thẳng đường dẫn là lộ dữ liệu |
| 4 | Xoá cứng bản ghi | Quy tắc BR-4, xoá là đánh dấu (dữ liệu giả `PERF-*`, `MAU-*`, `KH-*` là ngoại lệ) |
| 5 | Sửa tệp chuyển đổi cấu trúc đã chạy | Luôn tạo tệp mới |
| 6 | Ghi dữ liệu nhạy cảm vào nhật ký ứng dụng | Kể cả khi gỡ lỗi |
| 7 | Sửa hoặc xoá bản ghi nhật ký hoạt động | Quy tắc BR-6 |
| 8 | Thêm thư viện mới mà không hỏi trước | Mỗi thư viện là một phụ thuộc phải bảo trì |
| 9 | Dùng số thực dấu phẩy động cho tiền tệ | Quy tắc BR-8, cộng tiền bị sai số |
| 10 | Lấy toàn bộ bảng trong màn hình danh sách | Quy tắc Q4 |
| 11 | Dùng `.objects.filter()` trực tiếp cho dữ liệu có phạm vi quyền | Phải qua Custom Manager |
| 12 | Dùng Django Admin cho nghiệp vụ hằng ngày | Admin bỏ qua tầng dịch vụ, chỉ dùng cho quản trị viên |
| 13 | Cho sửa ô tại chỗ ở Bảng dữ liệu của KN ERP, dù chỉ một bảng | Bảng dữ liệu chỉ để xem — ADR-014 |
| 14 | Đưa lại renderer HTML/HTMX ghi ô cũ, hay thêm công thức Excel tự do từng ô | ADR-021, 027; công thức ô chưa chốt (S10) |
| 15 | Bật cờ `CRM_OPT_*` hay đổi đích nhận đơn mà không có biên bản kiểm chứng và lệnh của chủ dự án | ADR-024, 029 |
| 16 | Đổi nghiệp vụ, luồng thao tác, quyền ngoài phạm vi đã duyệt | AGENTS.md mục 1 |

---

## Bắt buộc làm

| # | Quy tắc |
|---|---|
| 1 | Mọi màn hình danh sách phải có phân trang, mặc định 25 dòng |
| 2 | Truy vấn có quan hệ phải lấy sẵn dữ liệu liên quan trong cùng một lệnh |
| 3 | Mỗi đường dẫn mới phải có kiểm thử cho cả ba cấp bậc, gồm cả trường hợp bị từ chối |
| 4 | Mỗi thay đổi cấu trúc dữ liệu phải kèm tệp chuyển đổi đảo ngược được |
| 5 | Mọi thời gian lưu theo giờ quốc tế, hiển thị theo giờ Việt Nam; ngày nhập `DD/MM/YYYY` (ADR-032) |
| 6 | Mọi số tiền lưu dạng số thập phân chính xác, kèm loại tiền; không cộng lẫn tiền tệ |
| 7 | Các giá trị cố định khai báo ở một chỗ duy nhất, không viết rải rác |
| 8 | Truy cập ngoài phạm vi quyền phải trả lỗi từ chối, không trả danh sách rỗng |
| 9 | Cột dùng để lọc hoặc tìm kiếm phải có chỉ mục |
| 10 | Docstring của hàm kiểm thử phải ghi mã tiêu chí nghiệm thu tương ứng |
| 11 | Phạm vi quyền áp bằng Custom Manager, không viết điều kiện lọc ở từng view |
| 12 | Cột JSON dùng để lọc phải có chỉ mục GIN |
| 13 | Ghi lưới phải so phiên bản (CAS) và báo xung đột, không âm thầm ghi đè; lỗi mạng phải hiện đúng, không báo "Đã lưu" |

---

## Quy ước đặt tên

| Đối tượng | Ngôn ngữ | Ví dụ |
|---|---|---|
| Tên biến, hàm, lớp | Tiếng Anh | `get_user_scope`, `OrderItem` |
| Tên bảng và cột trong cơ sở dữ liệu | Tiếng Anh | `daily_report`, `created_at` |
| Nhãn hiển thị trên giao diện | Tiếng Việt | "Báo cáo hằng ngày" |
| Thông báo lỗi cho người dùng | Tiếng Việt | "Bạn không có quyền truy cập" |
| Chú thích trong mã nguồn | Tiếng Việt | |
| Thông điệp ghi thay đổi mã nguồn | Tiếng Việt không dấu | |

---

## Kiểm thử

**Mỗi tiêu chí nghiệm thu có một hàm kiểm thử, và docstring ghi mã tiêu chí:**

```
def test_staff_chi_xem_duoc_du_lieu_cua_minh():
    """AC-3.1 — Staff chỉ xem được bản ghi do chính mình tạo"""
```

Nhờ vậy truy vết được hai chiều giữa tài liệu và mã nguồn.

**Kiểm thử phân quyền phải kiểm cả hai chiều:** trường hợp được phép và trường
hợp bị từ chối. Chỉ kiểm chiều được phép thì không phát hiện được rò rỉ dữ liệu.

**Mỗi tác vụ có đo hay có thao tác trình duyệt để lại biên bản**
`docs/kiem-chung-<việc>-<ngày>.md`: lệnh, môi trường, số đo, phần chưa kiểm.
Không tuyên bố đạt những kiểm tra chưa chạy.

---

## Định nghĩa hoàn thành

Một việc chỉ được coi là xong khi đủ bốn điều:

| # | Điều kiện |
|---|---|
| 1 | Tiêu chí nghiệm thu tương ứng đã có kiểm thử và đạt |
| 2 | Phân quyền đã kiểm cả trường hợp cho phép và từ chối |
| 3 | Tệp chuyển đổi cấu trúc chạy xuôi và ngược đều được |
| 4 | Không có dữ liệu nhạy cảm nào lọt vào nhật ký |

---

## Khi gặp việc chưa rõ

**Không tự quyết những việc sau — hỏi trước:**

- Thêm hoặc đổi cấu trúc dữ liệu nền tảng
- Thêm thư viện bên ngoài
- Thay đổi cách phân quyền
- Bỏ qua một quy tắc trong danh sách trên
- Đổi nghiệp vụ hay luồng thao tác của người dùng cuối

**Với việc chưa rõ khác:** chọn cách đơn giản nhất chạy được, ghi lại lựa chọn
đó vào `docs/backlog.md` để xem lại sau.

---

## Trước khi tự viết một thành phần phức tạp

Kiểm tra xem có thư viện mã nguồn mở nào đã giải bài toán đó chưa.
Nếu có, đề xuất trước khi viết — kèm lý do nên dùng hoặc không nên dùng.

Nhưng cũng đừng thêm thư viện cho việc đơn giản. Mỗi phụ thuộc là một thứ
phải bảo trì và cập nhật.

---

## Cấu trúc thư mục

```
KNJSC/
├── KN JSC.bat             Windows: nháy đúp là mở hệ thống
├── AGENTS.md              quy tắc phối hợp chung Codex và Claude — đứng trên tệp này
├── CLAUDE.md              file này: ngữ cảnh cho Claude
├── PRODUCT.md, DESIGN.md  mục tiêu sản phẩm; hồ sơ thiết kế Solarpunk
├── .agents/               skills/ (nguồn 10 skill), skill-sources.json, design-state/
├── .claude/               skills/ (cầu nối sinh tự động), agents/ (Impeccable)
├── docs/                  tài liệu, quyet-dinh/ (ADR), kiem-chung-*.md
├── app/                   mã nguồn ứng dụng (13 app Django)
├── config/                cấu hình, không đưa lên kho mã nguồn
├── deploy/                compose local, Dockerfile, entrypoint; production/ cho VPS
└── scripts/               launcher, kiểm tải, kiểm trình duyệt (kiem-thu-*.cjs), dong-bo-skill.py
```

**Không đưa lên kho mã nguồn:** tệp cấu hình, tệp cơ sở dữ liệu, bản sao lưu,
tệp người dùng tải lên, khoá bí mật, `storage/`, ảnh review thiết kế.
