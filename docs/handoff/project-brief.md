# Bản tóm tắt dự án KNJSC — cho người mới tiếp quản

| | |
|---|---|
| Ngày lập | 19.09.2026 |
| Trạng thái kho mã khi lập | `origin/main` = `aebb1f6`, `origin/codex/crm-update-solar-ui` = `7e42980` |
| Cách lập | `git fetch origin --prune --tags`, đọc lịch sử mọi nhánh, `docs/`, API pull request của GitHub |
| Đọc tiếp | `CLAUDE.md` (quy tắc viết mã) · `AGENTS.md` (quy tắc phối hợp) · `docs/backlog.md` (việc gần nhất, ở **đầu tệp**) |

> Tài liệu này chỉ mô tả hiện trạng, không quyết định gì. Nơi chốt quyết định vẫn là
> `docs/quyet-dinh/` và `docs/backlog.md`.

---

## 1. KNJSC là gì, gồm những phần nào, ai dùng

Hệ thống vận hành nội bộ cho Kim Ngân JSC, công ty thương mại điện tử xuyên biên giới:
Marketing chạy quảng cáo → Sale chốt đơn → Vận đơn giao hàng và đối soát tiền. Thay cho
dây chuyền Google Form, Google Sheets và Lark đang dùng, vốn chậm dần khi Sheet lên vài
chục nghìn dòng và không phân quyền được theo dòng.

**Hai ứng dụng, cùng một kho mã, cùng một cơ sở dữ liệu:**

| Ứng dụng | Dịch vụ | Cổng cục bộ | Làm gì |
|---|---|---|---|
| **KN ERP** | `web` | 8020 | Đăng nhập, nhân sự, biểu mẫu, báo cáo ngày, Báo cáo tổng hợp, Bảng dữ liệu **chỉ đọc**, nhóm Nội bộ |
| **KN CRM** | `bangtinh` | 8021 | **Nơi duy nhất sửa số liệu.** Lưới kiểu Excel cho mọi bảng, thư mục Bộ phận ▸ Quý ▸ Tháng, Lên đơn, Nhập tệp, Cấp quyền, Thống kê |

Luật cứng: Bảng dữ liệu ở ERP không sửa ô, dù chỉ một bảng (ADR-014, luật cấm số 13).
Lên đơn đã rời ERP sang CRM (ADR-023).

**Nhóm Nội bộ** (ADR-017) là năm app nhỏ trong ERP: `documents` Tài liệu, `feed` Bảng tin,
`taskboard` Công việc, `culture` Đánh giá nhân sự, `resources` Tài nguyên.

**Người dùng.** Dưới 100 tài khoản, tối đa 50 người đồng thời, tối đa 10 người cùng lúc
trên file Vận đơn; khoảng 100.000 đơn một năm, kiểm dự phòng 300.000 dòng.

| Bộ phận | Cấp bậc | Phạm vi thấy được |
|---|---|---|
| Sale, Marketing, Vận đơn (thêm Kế toán, CSKH ở bảng vận đơn) | Staff | Chỉ bản ghi của mình |
| | Leader | Cả team mình phụ trách; trong KN CRM thì như Manager trong bộ phận mình (ADR-015) |
| | Manager | Cả bộ phận |
| | Admin | Mọi bộ phận |

Riêng bảng vận đơn: nhân viên Vận đơn **xem và sửa mọi dòng**, nút Tôi / Toàn bộ chỉ lọc
theo cột phụ trách (ADR-033, thay ADR-026). Định danh nhân sự là mã `staff_code` kiểu
`THUANLT`, hiện mã trước tên sau (ADR-037).

---

## 2. Stack kỹ thuật và cách chạy

| Thành phần | Lựa chọn |
|---|---|
| Khung ứng dụng | Django 5.2.6 |
| Cơ sở dữ liệu | PostgreSQL 16 |
| Giao diện | HTMX cho ERP; lưới CRM là JS thuần đọc JSON. **Không React, Vue, không thư viện bảng tính** (ADR-002, ADR-005) |
| Tác vụ nền | Celery với Redis, hai hàng đợi `worker` và `heavy` |
| Đóng gói | Docker Compose; VPS theo `deploy/production/` |
| Excel | openpyxl |
| Phụ thuộc | `app/requirements.txt` 7 gói; `app/requirements-dev.txt` thêm pytest, pytest-django, pytest-cov, playwright, locust |

### Chạy trên máy mình

```
KN JSC.bat                       Windows: nháy đúp ở thư mục gốc, tự kéo mã, bật Docker, mở 8020
./scripts/cap-nhat-local.sh      Mac và Linux
```

Làm tay thì đúng bốn lệnh, **phải đúng thứ tự này**:

```
docker compose -f deploy/docker-compose.yml up -d
docker compose -f deploy/docker-compose.yml exec web python manage.py du_lieu_mau
docker compose -f deploy/docker-compose.yml exec web python manage.py configure_erp_reports
docker compose -f deploy/docker-compose.yml exec web python manage.py configure_delivery_daily_report
```

Cơ sở dữ liệu không theo kho mã, nên máy mới dựng xong là **không có tài khoản nào để
đăng nhập** — `du_lieu_mau` tạo 12 tài khoản, danh sách ở `docs/tai-khoan-mau.md`. Hai lệnh
`configure_*` sinh metadata nguồn báo cáo; thiếu chúng thì Báo cáo tổng hợp **lặng lẽ** rơi
về bản tổng quát cũ, không báo lỗi. Chúng bỏ qua bảng chưa tồn tại mà không báo, nên chạy
trước `du_lieu_mau` là chạy hụt. Bảng vận đơn thì `deploy/entrypoint.sh` tự lo bằng
`tao_bang_van_don` ngay sau `migrate`.

### Cổng và dịch vụ

| Nơi | Cấu hình | Địa chỉ |
|---|---|---|
| Máy cá nhân | `deploy/docker-compose.yml`: `db` 5433, `web` 8020, `bangtinh` 8021, cộng `redis`, `worker`, `beat` | `http://127.0.0.1:8020/`, `http://127.0.0.1:8021/` |
| VPS thật (2 nhân, 4 GB) | `deploy/production/compose.yml` + `compose.vps.yml`, nginx trước hai hostname, năm container `crm` `erp` `worker` `heavy` `beat` cùng một image tag bất biến | `erp.thnsolution.io.vn`, `crm.thnsolution.io.vn` |

### Kiểm thử — hai đường, chạy riêng

```
# pytest trong Docker
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest
# pytest ngoài Docker, từ app/, cần Postgres đang chạy
python -m pytest --ds=knjsc.settings.test
# script Node điều khiển Chrome thật, chạy tay
node scripts/kiem-thu-master-ui.cjs
```

**Script Node** là hơn 70 tệp `.cjs` và một `.mjs` trong `scripts/`, dùng `playwright` điều
khiển Chrome thật (`channel:'chrome'`) để kiểm những thứ pytest không thấy: lưới, hộp lọc,
độ tương phản, hình học dòng. Hai điều phải biết trước khi chạy:

- **Không có `package.json`, không có bước `npm install` nào được ghi lại.** `playwright` chỉ
  nằm trong `requirements-dev.txt` phía Python; môi trường Node lấy Playwright từ đâu thì
  tài liệu không nói. Đây là chỗ hổng, không phải chỗ bạn làm sai.
- Gần như script nào cũng đòi một server pytest dựng sẵn ở cổng riêng (8031, 8035, 8135,
  8811/8812…) chạy song song ở terminal khác. Công thức từng bộ ở `docs/06` mục "Bổ sung".

Cờ `-m "not cham"` bỏ bài chậm, `-m "not trinh_duyet"` bỏ bài cần Chromium. **Không chạy
hai pytest cùng lúc** trên cùng một database kiểm thử.

---

## 3. Cấu trúc thư mục và tài liệu quan trọng

```
KNJSC/
├── KN JSC.bat          Windows: nháy đúp là chạy
├── CLAUDE.md           quy tắc viết mã — 16 điều cấm, 13 điều bắt buộc
├── AGENTS.md           quy tắc phối hợp; khi vênh với CLAUDE.md thì AGENTS.md thắng
├── PRODUCT.md          hồ sơ sản phẩm cho skill thiết kế
├── DESIGN.md           hướng giao diện Solarpunk Office (ADR-028)
├── app/                12 app Django: core org forms_builder reports orders crm dashboard
│                       documents feed taskboard culture resources
├── deploy/             Dockerfile, compose máy cá nhân, production/ cho VPS
├── scripts/            launcher .bat, 70+ script Node kiểm trình duyệt, tiện ích Python
├── docs/               tài liệu — xem bảng dưới
├── prototype/          bản dựng HTML tĩnh, chỉ để đối chiếu
└── tests/              (rỗng; bài kiểm thật nằm trong app/)
```

| Tài liệu | Nội dung |
|---|---|
| `docs/backlog.md` | **Đọc đầu tiên.** Từ 14.09 mỗi lượt việc là một mục ghi ngày ở **đầu tệp**; mục 0 là bản tóm cũ hơn |
| `docs/backlog-kanban.md` | Cùng việc đó xếp theo To do / In progress / Finished / Far Plan |
| `docs/test-log.md` | Từng lỗi `TL-xx` kèm mức, chỗ sai, blocker |
| `docs/quyet-dinh/` | 39 ADR. Không quyết lại những gì đã chốt. Lưu ý **hai tệp cùng số 022** |
| `docs/04-tieu-chi-nghiem-thu.md` | Tiêu chí nghiệm thu — xem giải thích bên dưới |
| `docs/06-ke-hoach-kiem-thu.md` | Kế hoạch kiểm thử, chín tầng, bộ đếm tiêu chí |
| `docs/kiem-chung-*.md` | Mỗi tác vụ từ 09.09 một biên bản: đã đo gì, số bao nhiêu, còn gì chưa kiểm |
| `docs/daily-tasks.md` | Việc bàn giao giữa các máy và giữa Claude web với Claude Code CLI |
| `docs/USER_INQUIRY.md` | Câu hỏi nghiệp vụ còn chờ chủ dự án |
| `docs/dashboard-tien-do.html` | Tiến độ theo giai đoạn, **chỉ tới 08.09**; sau đó xem backlog |

### `docs/04` — AC là gì

`AC-x.y` là **tiêu chí nghiệm thu** (acceptance criterion): một câu mô tả "thế nào là xong",
tham chiếu ngược tới mã yêu cầu `FR-x.y` ở `docs/02`. Mỗi tiêu chí đánh dấu **Tự động** hoặc
**Thủ công**.

Ràng buộc làm cho hệ thống mã này không trôi được: mỗi tiêu chí Tự động phải có một hàm
kiểm thử mà **docstring ghi đúng mã đó**.

```python
def test_staff_khong_xem_duoc_du_lieu_nguoi_khac():
    """AC-3.1 — Staff chỉ xem được dữ liệu do chính mình tạo"""
```

Bài `app/tests/test_truy_vet.py` đọc thẳng `docs/04`, đối chiếu với docstring trong mã, và
đỏ ngay khi có tiêu chí Tự động chưa có bài kiểm. Tra được hai chiều: từ tài liệu ra mã và
từ mã về tài liệu. Thêm AC mới thì phải cập nhật bộ đếm ở `docs/06` theo thông báo của bài đó.

### `docs/06` — ba con số 239 / 226 / 202

Nằm ở bảng "Hiện trạng", dòng đầu `docs/06-ke-hoach-kiem-thu.md`:

| Số | Nghĩa |
|---|---|
| **239** | Tổng số tiêu chí nghiệm thu đang có trong `docs/04` |
| **226** | Trong đó bao nhiêu đánh dấu **Tự động**; 13 cái còn lại là **Thủ công**, người phải bấm tay |
| **202** | Trong 226 cái tự động, bao nhiêu **đã có bài kiểm thật**. Còn **24 cái hoãn** |

24 cái hoãn không phải là bài kiểm bị bỏ quên: phần lớn là tiêu chí của việc **đang làm dở**
(AC-24 CRM-Optimization, AC-26 chứng từ thanh toán, AC-27 vòng đời bảng), ghi vào danh sách
hoãn để bài truy vết đếm đúng thay vì lờ đi. Danh sách nằm trong biến `HOAN` của
`tests/test_truy_vet.py`, thêm mã vào đó **bắt buộc ghi lý do**. Ba trường hợp đáng chú ý:

- `AC-11.10`, `AC-11.20`: tính năng **vẫn chạy**, nhưng bài kiểm nằm ở script Node chạy Chrome
  thật nên pytest không đếm được.
- `AC-11.14`, `AC-11.21`: tính năng **không còn** trong lưới mới (dòng trống cuối lưới, menu
  chuột phải) — chờ chủ dự án chốt bỏ tiêu chí hay làm lại tính năng.
- `AC-5.1`: tab thị trường chờ chốt nguồn số liệu (backlog N9, Q36).

Ba con số này đổi mỗi lần thêm AC, và **có bài kiểm canh** nên không trôi lệch với `docs/04`.

---

## 4. Hai nhánh chính: `main` và `codex/crm-update-solar-ui`

**Nhánh làm việc chính là `codex/crm-update-solar-ui`, không phải `main`.** VPS và máy chủ
dự án đều chạy từ nhánh codex. Tách nhánh mới từ nhánh codex; PR trỏ về nhánh codex trừ khi
chủ dự án nói khác (`CLAUDE.md`).

### So sánh hai chiều

| Chiều | Số commit |
|---|---|
| Có ở `main`, **không** có ở codex | **0** |
| Có ở codex, không có ở `main` | **37** |

Điểm chung gần nhất (`git merge-base`) chính là đỉnh `main` hiện tại, `aebb1f6` ngày 17.09.
Nghĩa là hai nhánh **không phân kỳ**: codex đi thẳng tiếp từ main. `main` chỉ đơn giản là
tụt lại 37 commit, không giữ thứ gì riêng. Gộp codex vào main sẽ là fast-forward, không xung đột.

Lý do lịch sử: PR #25 ngày 17.09 đã mang trọn nhánh codex vào main, sau đó main được gộp
ngược lại vào codex (`a13037b`) rồi codex chạy tiếp một mình.

### 37 commit của codex, gom theo nhóm

| Nhóm | Số | Nội dung chính |
|---|---|---|
| **Tính năng** | 12 | ADR-036 một bảng vận đơn duy nhất (xoá cứng crmThuận và Vận đơn DB) · ADR-037 mã nhân sự · ADR-038 hoàn thiện trang Marketing · ADR-039 ẩn cột với cả công ty · ADR-033 nút Tôi/Toàn bộ và Vận đơn sửa toàn bảng · lưới thao tác như Excel · bảy PTTT theo sheet Vận đơn · Báo cáo tổng hợp: bố cục mới, nhóm ngày × nhân sự, khối theo ngày, tô màu chỉ tiêu (AC-22.13 → 22.16) |
| **Sửa lỗi** | 4 | TL-41 cột Loại tiền thiếu USD/CAD/PHP · TL-46 hộp lọc cột mất kiểu dáng do một chú thích CSS thiếu `*/` nuốt 24 luật · TL-47 đơn thứ hai lấy nhầm tên khách cũ · chắn lỗi gõ nhầm số điện thoại làm đổi tên danh bạ · bốn góp ý sau ADR-033 |
| **Tài liệu** | 18 | 6 biên bản phát hành VPS · 2 biên bản diễn tập nâng cấp · các biên bản kiểm chứng, bàn giao cho Claude Code CLI, runbook, đính chính trạng thái VPS |
| **Kiểm thử** | 3 | Thêm bài đầu-cuối đi trọn hành trình nhân viên · xoá 12 bài E2E viết cho lưới HTMX cũ · stub cho bài hàng đợi lưới |

Tài liệu chiếm gần một nửa số commit. Đó là nếp của dự án, không phải dấu hiệu ít việc:
mỗi lượt sửa có đo đều để lại một biên bản `docs/kiem-chung-*.md`.

### PR #5 tới #25 gộp vào nhánh nào

**Tất cả 25 PR đều đã đóng, không còn PR nào mở.**

| PR | Gộp vào | Ghi chú |
|---|---|---|
| #5 → #11, #13 → #23, #25 | `main` | 19 PR, đều đã gộp |
| #24 | `codex/crm-update-solar-ui` | PR duy nhất trỏ về nhánh codex; gộp 17.09 |
| #12 | — | Đóng **không gộp**, nội dung thay bằng #13 |
| #1, #3 | — | Đóng không gộp (ngoài khoảng bạn hỏi) |

PR #25 "Gộp nhánh KN CRM vào main" ngày 17.09 là cái mang trọn nhánh codex vào main, kèm ba
phần sửa: nút lịch trên nền tối, cấu hình nguồn báo cáo trong entrypoint, và 19 bài kiểm đỏ
có sẵn. Ghi nhận trong commit: `pytest -m "not cham"` 2.499 đạt, 13 bỏ qua, 0 đỏ.

---

## 5. Ai đang commit — 30 ngày gần đây, mọi nhánh

Tổng **212 commit**.

| Tác giả git | Số commit | Thực chất là ai |
|---|---|---|
| `Claude <noreply@anthropic.com>` | 103 | Claude Code trên web, commit dưới danh nghĩa Claude |
| `cyrusdev1512 <cyrusdev1512@gmail.com>` | 91 | Chủ dự án commit từ máy mình hoặc từ Claude Code CLI trên máy chủ dự án |
| `CyrusDev1512 <…@users.noreply.github.com>` | 18 | Cùng người, nhưng commit gộp PR tạo trên giao diện web GitHub |

Theo mô hình đứng sau (dòng `Co-Authored-By`): **Claude Fable 5.1** 88 lần, **Claude Opus 5**
36 lần, **Claude Fable 5** 4 lần. Sáu phiên Claude Code khác nhau để lại dấu `Claude-Session`.

**Không có commit nào của Codex, GPT hay OpenAI.** Tên nhánh `codex/crm-update-solar-ui` và
chữ "Codex" trong vài thông điệp commit là cách chủ dự án và Claude **gọi lẫn nhau** giữa hai
môi trường làm việc, không phải chữ ký của công cụ. Trong 37 commit riêng của nhánh codex:
27 tác giả `Claude`, 10 tác giả `cyrusdev1512`.

### Commit `e71c1dc`

| | |
|---|---|
| Tiêu đề thật | "Ghi ket qua phat hanh 72af235 (ADR-039, AC-22.14/15/16, TL-46/47, loc cot, nhac khach) tren VPS" |
| Tác giả và người commit | `cyrusdev1512 <cyrusdev1512@gmail.com>` |
| Ngày | **19.09.2026, 18:50 giờ Việt Nam** |
| Đứng sau | `Co-Authored-By: Claude Opus 5` — làm trong phiên Claude Code CLI trên máy có SSH |
| Nằm ở | Chỉ trên `codex/crm-update-solar-ui`, **chưa có ở `main`** |
| Đổi gì | 3 tệp, 102 dòng thêm: biên bản `docs/kiem-chung-phat-hanh-vps-20260919-gop.md`, cộng cập nhật `backlog.md` và `backlog-kanban.md` |

Đây đúng là biên bản phát hành VPS bạn hỏi, và là commit áp chót của nhánh.

---

## 6. Phát hành lên VPS

**Không có CI, không có script phát hành một lệnh.** Phát hành là **chạy tay theo runbook**,
từ một máy Windows có SSH vào VPS, trong phiên Claude Code CLI, do **chủ dự án** khởi động.
Claude Code trên web **không tới được VPS** — máy ảo của nó là bản clone riêng.

| Mục | Nội dung |
|---|---|
| Quy trình chuẩn | `deploy/production/README.md` — danh sách lệnh theo đúng thứ tự |
| Bàn giao từng đợt | `docs/daily-tasks.md` và `docs/prompt-cli-phat-hanh-*.md` — prompt dán vào Claude Code CLI |
| Biên bản kết quả | `docs/kiem-chung-phat-hanh-vps-<ngày>[-nhãn].md`, mỗi lần phát hành một tệp |
| Ảnh image | `knjsc-app:<commit>-<nhãn>`, tag bất biến, dựng bằng `deploy/Dockerfile --build-arg INSTALL_DEV=0` |

Khung một lần phát hành: backup **có kiểm phục hồi thật** → `git merge --ff-only` tại
`/opt/knjsc` → build image → `check --deploy` → `migrate` → `tao_bang_van_don` →
`configure_erp_reports` → `configure_delivery_daily_report` → `collectstatic` →
đổi `KNJSC_IMAGE` trong `.env` → `up -d` năm service → `nginx -t` và reload → mở hai domain.

**Sáu biên bản phát hành** hiện có trên nhánh codex: 17.09, 18.09 (bản chính, `-excel`,
`-tl41`), 19.09 (`-adr036-mkt`, `-xac-nhan`, `-gop`).

### Lần phát hành gần nhất

| | |
|---|---|
| Thời điểm | **19.09.2026, 18:44 giờ Việt Nam** |
| Commit phát hành | **`72af235`**, image `knjsc-app:72af235-gop` |
| Ghi lại ở | `docs/kiem-chung-phat-hanh-vps-20260919-gop.md`, commit `e71c1dc` |
| Nội dung | Gộp 10 commit `1e09cfd..220fd22`: ADR-039 ẩn cột, AC-22.14/15/16, TL-46/47, hộp lọc cột, nhắc khách |
| Kết quả | 5 service cùng image, 0 restart, 0 dòng lỗi trong 3 phút log; một migration `forms_builder 0015`; hai domain trả 200 |

Đỉnh nhánh codex hiện là `7e42980` (thêm bài kiểm đầu-cuối), **chưa phát hành** — nhưng đó là
commit chỉ thêm bài kiểm, không đổi hành vi.

**Hai chỗ tài liệu vênh nhau, cần biết trước khi tin:** `deploy/production/README.md` mở đầu
bằng "Chưa triển khai/đo trên VPS" và lấy khởi điểm 12 CPU / 24 GB, trong khi `CLAUDE.md` và
sáu biên bản phát hành nói VPS thật là **2 nhân / 4 GB** và đã phát hành nhiều lần. Phần lệnh
trong README vẫn đúng và vẫn đang dùng; phần mô tả phần cứng và câu "chưa triển khai" là tàn dư cũ.

---

## 7. Nhánh còn sống trên GitHub và PR đang mở

| Nhánh | Đỉnh | Ngày cuối | So với codex | Trạng thái |
|---|---|---|---|---|
| `codex/crm-update-solar-ui` | `7e42980` | 19.09 | — | **Nhánh chính đang chạy**, VPS lấy mã từ đây |
| `main` | `aebb1f6` | 17.09 | sau 37 commit, không có gì riêng | Còn sống nhưng không phải nơi làm việc |
| `CRM-UPDATE` | `12415a5` | 14.09 | sau 72 commit, không có gì riêng | Đã gộp hết, bỏ được |
| `codex/ui-solarpunk` | `373fbae` | 14.09 | sau 79 commit, không có gì riêng | Đã gộp hết, bỏ được |

Cả ba nhánh ngoài codex đều **ahead = 0**: không nhánh nào giữ commit mà codex thiếu. Xoá hai
nhánh cũ không mất gì, nhưng hãy hỏi chủ dự án trước.

**PR đang mở: không có.** Cả 25 PR đều đã đóng.

---

## 8. Lỗi và nợ kỹ thuật đã biết, việc đang dở

### Việc đang dở, theo `docs/backlog-kanban.md`

| Ai làm | Việc |
|---|---|
| Admin | Bấm **ẩn nhóm cột số lượng theo sản phẩm** một lần trên domain thật (ADR-039 — ẩn là trạng thái trong DB, phát hành xong cột vẫn hiện cho tới khi có người bấm), rồi kiểm lưới, tệp Excel, Bảng dữ liệu ERP |
| Chủ dự án | Kiểm mục 7 của hai đợt phát hành trên domain thật (không có tài khoản kiểm nên CLI chưa mở được trang cần đăng nhập); tạo hồ sơ cho `admin` và `quantri` để hai tài khoản này có mã nhân sự |
| CLI | Chạy `pytest` toàn bộ trên `72af235` khi máy có Docker |
| Chưa xếp | Phát hành `7e42980`; thu gọn panel "Bộ lọc" (chờ hỏi nhân viên); ngưỡng 50 giá trị của hộp lọc cột chưa có số đo |

### Lỗi còn mở trong `docs/test-log.md`

| Mã | Mức | Nội dung |
|---|---|---|
| TL-48 | — | Hộp lọc cột trên bảng 100.522 dòng mở mất ~5 giây và chỉ hiện 200 giá trị đầu; với cột nhiều giá trị như Tên khách thì gần như vô dụng. Chờ chủ dự án chốt có đổi cách lọc không |
| TL-36 | S2 | Cột Trùng đếm số điện thoại **đúng như gõ**: `4165550123`, `+1 (416) 555-0123`, `416 555 0123` là ba khách khác nhau; chỉ hiện con số, không bấm được để xem các dòng kia |
| TL-43 | — | `DELETE` 50.000 dòng của `seed_perf.clear()` treo hơn 17 phút một lần, không tái hiện được |
| TL-06 → TL-17 | S2–S4 | **Rà trên lưới HTMX cũ ngày 07.09.** Lưới đã thay bằng `master-grid.js`, nên phải rà lại trước khi sửa — đừng tin nguyên trạng |
| TL-24 → TL-33 | S3–S4 | Ghi nhận từ PR #21 (kiểm tải): thiếu retry deadlock ở vài đường ghi, không gộp job tính lại, `moi-nhat/` không lọc theo phạm vi, tệp tĩnh không được phục vụ khi chạy gunicorn trần |

### Nợ ở tầng hệ thống

| # | Nợ | Ghi chú |
|---|---|---|
| 1 | **Không có CI** — không gì chạy kiểm thử khi đẩy mã | Chốt chưa dựng vì còn ngỏ ai vận hành sau bàn giao (backlog V2) |
| 2 | Kiểm tải mới chạy trên máy phát triển, chưa trên VPS thật | VPS 2 nhân 4 GB nhỏ hơn máy đo nhiều |
| 3 | Bài Playwright và bài 50.000 dòng không chạy trong container `web` | Image không có Chromium; chạy trên máy phát triển |
| 4 | Hai bài đánh dấu `xfail` | K23 hộp lọc cột trong Playwright; K24 ngân sách 10 truy vấn, thực tế đếm 12–13 |
| 5 | Chưa kiểm khả năng đọc màn hình cho người khiếm thị | Chưa ai nêu yêu cầu |
| 6 | Cờ tối ưu `CRM_OPT_*` **tắt** ở mọi nơi kể cả VPS | READ/SYNC gây lỗi mở editor; không bật khi chưa có biên bản kiểm chứng |
| 7 | `PRODUCT.md` ghi hướng thiết kế Google Workspace (07.09), `DESIGN.md` ghi Solarpunk Office (ADR-028) | Hai bên chưa hợp nhất — hỏi trước khi đổi diện mạo |
| 8 | Chưa nghiệm thu chính thức màn hình nào | Chủ dự án chốt dồn về một đợt (backlog V4, V5) |

---

## 9. Kiểm thử: có gì, chạy thế nào, chỗ nào chưa được kiểm

### Đang có

| Số | Nội dung |
|---|---|
| 119 | Tệp `test_*.py` trong `app/` |
| ~841 | Hàm `def test_`; chạy thật ra nhiều hơn nhờ `parametrize` |
| **2.527** | Số bài **đạt** ở lần chạy đầy đủ gần nhất (`-m "not trinh_duyet and not cham"` trên `220fd22`), 1 bỏ qua, 0 đỏ |
| 70+ | Script Node điều khiển Chrome thật trong `scripts/` |
| ~85% | Bao phủ dòng mã, đo bằng `pytest --cov`; **cố ý không đặt ngưỡng chặn** (backlog K5) |

### Chín tầng kiểm thử (`docs/06`)

Đơn vị · tệp chuyển đổi · kiểm khói mọi đường dẫn × mọi vai trò · chức năng · hộp đen
(ma trận phân quyền 50 ô) · hộp trắng · giao diện (lớp CSS có thật) · đầu-cuối trình duyệt ·
hiệu năng và kiểm tải. Cộng tầng thứ mười là **truy vết**: `tests/test_truy_vet.py` đối chiếu
`docs/04` với docstring.

Nguyên tắc của dự án: **một bài kiểm phải đỏ được.** Mỗi tầng đều đã thử bằng cách cố ý gây
lỗi, và cột "Đã thử gây lỗi" trong `docs/06` ghi cách thử.

### Chưa được kiểm

| Chỗ hổng | Vì sao |
|---|---|
| 24 tiêu chí tự động chưa có bài kiểm | Xem mục 3; phần lớn là việc đang làm dở |
| Nối giữa các màn hình | Vừa lấp một phần ngày 19.09 bằng `tests/e2e/test_hanh_trinh_nhan_vien.py`. Hai lỗi chủ dự án báo sáng 19.09 **đều nằm giữa các màn hình** và 2.528 bài pytest cùng 50 script Node đều không bắt được, vì mỗi bài chỉ cắt một mảnh |
| Dữ liệu thật | Bài e2e chạy trên DB test dựng sẵn, không phải dữ liệu dev; lặp lại được nhưng không phản ánh dữ liệu thật |
| Hành vi trên domain thật sau phát hành | Mỗi biên bản phát hành đều có mục "Chưa kiểm — ghi nợ"; CLI không có tài khoản nên không mở được trang cần đăng nhập |
| 50 script Node | Chỉ chạy tay, không có trong vòng lặp nào; gần như cái nào cũng đòi dựng server pytest ở cổng riêng trước |

---

## Ba điều nên làm trong tuần đầu

1. **Chạy được hệ thống trên máy mình** bằng `KN JSC.bat` hoặc bốn lệnh ở mục 2, đăng nhập
   bằng tài khoản ở `docs/tai-khoan-mau.md`, mở cả 8020 và 8021.
2. **Đọc theo thứ tự**: `AGENTS.md` → `CLAUDE.md` → `docs/backlog.md` (đầu tệp, không phải
   mục 0) → `docs/backlog-kanban.md` → ADR-033, 036, 037, 038, 039 là năm quyết định gần nhất.
3. **Hỏi chủ dự án hai câu** trước khi động vào mã: có gộp codex vào `main` và xoá hai nhánh
   chết không; và ai bấm ẩn nhóm cột sản phẩm trên domain thật (đang chặn ADR-039 có hiệu lực thật).
