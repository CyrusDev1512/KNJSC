# Kế hoạch kiểm thử

| Mục | Nội dung |
|---|---|
| Dự án | Kim Ngân JSC — Hệ thống vận hành nội bộ |
| Giai đoạn | Phase 1 |
| Ngày | 29.08.2026 |
| Tài liệu liên quan | `04-tieu-chi-nghiem-thu.md` · `backlog.md` mục V4, V5 |

> **Danh sách mọi thứ còn nợ nằm ở `backlog.md` mục 0** — cả việc kiểm thử lẫn
> mọi thứ khác. Tài liệu này chỉ nói *kiểm bằng cách nào*.
>
> Tài liệu này trả lời: **kiểm cái gì, bằng cách nào, ai kiểm, và thế nào là đạt.**
> `docs/04` định nghĩa *thế nào là xong*; tài liệu này định nghĩa *làm sao biết
> là đã xong*.

---

## Nguyên tắc

**Một bài kiểm thử phải đỏ được.** Bài không bao giờ đỏ thì không kiểm gì cả,
chỉ làm con số đẹp. Mỗi tầng dưới đây đều đã được thử bằng cách **cố ý gây lỗi**
để chắc chắn nó bắt được — cột "Đã thử gây lỗi" ghi cách thử.

**Đo bằng mã tiêu chí, không đo bằng phần trăm.** Backlog **K5** chốt ngày
29.08.2026: có đo bao phủ để biết chỗ hổng, nhưng **không đặt ngưỡng chặn** —
ngưỡng đẻ ra bài kiểm viết cho đủ số chứ không bắt được lỗi.

**Không bỏ qua phân quyền.** `docs/04` mục 18: *lỗi phân quyền dẫn tới rò rỉ dữ
liệu, và dữ liệu đã lộ thì không thu hồi được.*

---

## Hiện trạng

| | Số |
|---|---|
| Tiêu chí nghiệm thu trong `docs/04` | **159** — 146 tự động, 13 thủ công |
| Tiêu chí tự động đã có bài kiểm | **145 trên 146** |
| Tiêu chí tự động còn hoãn | **1**, đều thuộc diện chờ người dùng chốt — `AC-5.1`, backlog N9 |
| Bao phủ dòng mã | khoảng 85% |

Ba con số đầu **có bài kiểm canh** — `app/tests/test_truy_vet.py` đọc chính
`docs/04` và đối chiếu với mã, nên chúng không trôi được.

Số bài kiểm thử thì đổi mỗi lần thêm bài, nên **không ghi cứng ở đây** — chạy
lệnh dưới để biết số hiện tại.

Chạy toàn bộ:

```
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest
```

Kèm bản đo bao phủ:

```
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest --cov
```

Bỏ qua các bài chạy chậm khi cần vòng lặp nhanh: `pytest -m "not cham"`.

---

## Chín tầng kiểm thử

| # | Tầng | Ở đâu | Kiểm cái gì | Đã thử gây lỗi |
|---|---|---|---|---|
| 1 | **Đơn vị** | `tests/test_hop_trang.py`, rải trong từng module | Hàm lẻ: ép kiểu, đọc tiền, bảng tương thích kiểu | Đổi kỳ vọng của một cặp kiểu |
| 2 | **Tệp chuyển đổi** | `core/tests/test_chuyen_doi.py` | Model khớp tệp, chạy xuôi và ngược, một nhánh lá | Bỏ `reverse_sql` của `0002_pg_trgm` → đỏ |
| 3 | **Kiểm khói** | `tests/test_khoi.py` | Mọi đường dẫn × mọi vai trò, không trả 500 | Gỡ `@login_required` một view → đỏ |
| 4 | **Chức năng** | Từng module, cộng `tests/test_luong_ba_bo_phan.py` | Luồng làm việc trọn vẹn qua HTTP | — |
| 5 | **Hộp đen** | `tests/test_ma_tran_phan_quyen.py` | 45 ô ma trận kiểm chéo `docs/04` mục 3 | Tìm ra 4 lỗi thật ngay lần chạy đầu |
| 6 | **Hộp trắng** | `tests/test_hop_trang.py`, bản đo bao phủ | Nhánh chỉ chạy khi có lỗi, đường huỷ giao dịch | Tìm ra lỗi đọc tiền sai gấp trăm lần |
| 7 | **Giao diện** | `core/tests/test_giao_dien.py` | Lớp CSS có thật, ô nhập có nhãn, bảng có tiêu đề | Thêm lớp bịa vào template → đỏ |
| 8 | **Đầu-cuối trình duyệt** | `tests/e2e/` — Playwright, dấu `trinh_duyet` | Nhập → xuất → nhập lại qua giao diện; bàn phím và hộp lọc trên Bảng tính; kéo chọn vùng, dán TSV, kéo điền, hoàn tác, ô địa chỉ, chuột phải xoá hàng rồi hoàn tác (ADR-011); trang chủ KN CRM bấm tháng → lưới lọc tháng → ← (ADR-012); cột cố định khi cuộn; 390px không tràn ngang, có ảnh chụp | Đổi phím Esc thành không làm gì trong `bang-tinh.js` → đỏ |
| 9 | **Hiệu năng và kiểm tải** | `tests/test_hieu_nang.py` (dấu `cham`), `tests/perf/locustfile.py`, **`manage.py seed_perf` + `do_hieu_nang` + `tests/perf/locustfile_kn_crm.py`**, `crm/tests/test_kiem_tai.py` | 50.000 dòng thật: trang đầu và lưới có lọc dưới 2 giây; Locust 50 người p99 ≤ 3 giây (AC-10.1). **KN CRM ở cỡ 100 nghìn khách** (AC-10.8, ADR-016): 100.000 dòng vận đơn ≈ 3 triệu ô + bảng Sale 20.000 dòng có cột tính sẵn; đo một người rồi **100 người 5 phút** (70 nhân viên vận đơn di qua di lại, 20 Sale/MKT, 7 trưởng nhóm dán/xoá, 3 Manager đổi cột tính sẵn giữa phiên) trên gunicorn — ĐẠT khi p95 đọc ≤ 1 s, ghi ≤ 0,5 s, `moi-nhat/` ≤ 0,3 s, 0 lỗi, tính lại 100.000 dòng ≤ 30 s không chặn người khác; ngân sách truy vấn của các đường đã sửa khoá bằng AC-11.36 | Bỏ `select_related` ở lưới → vượt ngân sách; quay lại `{% include %}` từng ô → lưới 630 ms, 100 người p95 11 s |

**Kiểm tải KN CRM — cách chạy và số đo** (ADR-016, K27). Ba lệnh trong `app/`
(hoặc nháy đúp `scripts/kiem-tai-kn-crm.bat`, chạy `scripts/kiem-tai-kn-crm.sh`;
xem `app/tests/perf/README.md`):

```
python manage.py seed_perf --xoa-cu --so-dong 100000 --so-thang 24 --dien-day --bang-sale
python manage.py do_hieu_nang --giai-thich          # một người, không tải → storage/perf/<ngày>-don-le.md
locust -f tests/perf/locustfile_kn_crm.py --host http://localhost:8021 --users 100 --spawn-rate 10 --run-time 5m --headless
```

Số đo ngày 07.09.2026 trên máy ảo 4 nhân, PostgreSQL 16 mặc định, gunicorn 3
worker, 100.010 dòng (2,95 triệu ô, 85.954 số điện thoại), một người không tải,
trung vị 3 lần:

| Đường | Trước | Sau | Ngưỡng |
|---|--:|--:|--:|
| Lưới vận đơn 100 dòng × 39 cột | 638 ms | 154 ms | 1.000 ms |
| Lưới trang 500 | 846 ms | 280 ms | 1.000 ms |
| Sắp xếp theo khoá JSON | 755 ms | 350 ms | 1.000 ms |
| Chỉ dòng trùng `?trung=1` | 1.089 ms | 478 ms | 1.000 ms |
| `moi-nhat/` | 65 ms (quét cả bảng) | 72 ms (chỉ mục, thêm tiến độ tác vụ) | 300 ms |
| Dán 500 ô | 1.670 ms, 1.013 lệnh | 207 ms, 13 lệnh | 500 ms |
| Tính lại cột tính sẵn 20.000 dòng | 29,5 s | 4,2 s | 30 s |
| Tính lại cột 100.000 dòng | 153 s trong request | 19,6 s ở tác vụ nền (2 lô song song) | 30 s |

Kết quả 100 người 5 phút trên máy ảo (22,8 yêu cầu/giây, chấm từ lúc cả 100 người
đã đăng nhập — `--reset-stats`): **trước** p95 mọi nhóm ~11 giây, 14 lỗi;
**sau** p95 đọc 853 ms, ghi 371 ms, `moi-nhat/` 143 ms, 0 lỗi, tính lại cột
100.000 dòng 24,4–24,8 s mà p95 người khác trong lúc đó 900 ms — **ĐẠT** cả năm
tiêu chí. Báo cáo chi tiết ở `storage/perf/<ngày>-tai-100.md` (không đưa lên kho
mã); bảng trước/sau đầy đủ ở ADR-016. Trên máy anh/chị, script in ĐẠT / KHÔNG ĐẠT
từng tiêu chí — số trên máy thật mới là số để nghiệm thu NFR-2.

Cộng một tầng thứ mười không nằm trong danh sách: **truy vết**
(`tests/test_truy_vet.py`) đọc `docs/04` và khẳng định mọi tiêu chí tự động đều
có bài kiểm. Đây là `docs/04` mục 18 điều 1 viết thành mã chạy được.

---

## Vì sao nhiều tầng, không phải một

Mỗi tầng bắt một loại lỗi mà tầng khác không thấy. Bằng chứng từ chính dự án
này — bốn lỗi thật, mỗi lỗi lọt qua mọi tầng trừ đúng một tầng:

| Lỗi | Lọt qua | Bị bắt bởi |
|---|---|---|
| Bốn màn hình dùng lớp CSS không tồn tại, hiện một cột suốt ba giai đoạn | 218 bài kiểm chức năng | Tầng 7 — giao diện |
| Bộ phận Vận đơn mở bảng ra thấy rỗng | 218 bài, kể cả bài kiểm phân quyền | Chạy thử tay, nay có tầng 4 |
| Vận đơn vào được màn hình Lên đơn, trái tài liệu | 525 bài | Tầng 5 — ma trận |
| Số tiền hiện `1.234,56` nhưng đọc lại thành `123456` | 596 bài | Tầng 6 — hộp trắng |

Ba trong bốn lỗi đó **không sập trang, không báo lỗi, không làm bài kiểm nào
đỏ**. Đó là lý do không thể chỉ có một tầng.

---

## Tiêu chí còn hoãn

1 tiêu chí tự động chưa có bài kiểm. Danh sách này nằm trong
`tests/test_truy_vet.py`, biến `HOAN`, và **rỗng dần theo tiến độ**
— thêm mã vào đó bắt buộc ghi lý do và giai đoạn.

| Tiêu chí | Chờ |
|---|---|
| `AC-5.1` | Bốn cách nhóm mới chạy ba — tab thị trường chờ chốt nguồn số liệu, backlog **N9** và **Q36** |

---

## Danh sách kiểm thủ công

### Vận đơn CRM Tân — bổ sung 08.09.2026

Chạy `pytest crm/tests/test_waybill_new.py`, rồi kiểm migration xuôi/ngược
bằng `pytest core/tests/test_chuyen_doi.py -m cham -k orders` trên DB kiểm thử.
Theo ADR-019, bảng chỉ có lưới và thống kê, không tự tải form Lên đơn;
thử thêm/bớt sản phẩm tại trang Lên đơn riêng. PTTT tách riêng,
Blacklist vắng mặt; bấm ô tổng nhập tiền cho hai sản phẩm, kiểm Tổng hợp và
Theo sản phẩm; sửa SALE/CSKH và Quốc gia rồi kiểm hai cách nhóm còn lại.
Lọc Ngày, đổi trang lưới, thống kê không bị cắt theo trang. Đổi loại tiền không
quy đổi số đã nhập. Mở 390px, cuộn ngang lưới, thu gọn Thống kê.
Script kiểm đọc giao diện local: `node scripts/kiem-thu-van-don-ui.cjs`
(cần Playwright đã có ở môi trường kiểm thử và Chrome; tài khoản mẫu hoặc
biến `KN_TEST_USER`, `KN_TEST_PASSWORD`, `KN_CRM_URL`). Script không tạo đơn.

Chạy trước mỗi lần bàn giao. Máy không làm được những việc này — **kịch bản
bấm tay từng bước ở `docs/07-kich-ban-nghiem-thu.md`**.

### Tiêu chí thủ công trong `docs/04`

| ☐ | Mã | Việc | Tài khoản | Đạt khi |
|---|---|---|---|---|
| ☐ | `AC-2.4` | Thêm team mới, dùng ngay không khởi động lại | `quantri` | Team mới hiện ở ô chọn trong cùng phiên |
| ☐ | `AC-5.6` | Xuất báo cáo, mở bằng Excel, đối chiếu số | `mkt.manager` | Số trong tệp khớp màn hình — cả báo cáo tổng hợp lẫn bảng dữ liệu kèm bộ lọc |
| ☐ | `AC-10.1` | 50 người thao tác đồng thời | người vận hành | `seed_perf` rồi Locust 50 người 1 phút in **ĐẠT** — `app/tests/perf/README.md` (Q44) |
| ☐ | `AC-10.3` | Gặp lỗi hiện thông báo tiếng Việt, không trang trắng | bất kỳ | Gõ đường dẫn sai → trang 404 tiếng Việt. **Chưa làm** — backlog K9 |
| ☐ | `AC-10.4` | Dùng được trên điện thoại và máy tính bảng | bất kỳ | Mở trên máy thật, không tràn ngang, bấm được; máy đã đo phần "không tràn ngang" ở `tests/e2e/test_dien_thoai.py`, ảnh ở `storage/e2e/` |
| ☐ | `AC-10.5` | Phục hồi từ bản sao lưu | người vận hành | `scripts/backup.sh` rồi `scripts/restore.sh --toi-chac-chan` trên máy thử; đăng nhập lại thấy đủ dữ liệu |
| ☐ | `AC-11.1` | Bốn cột đầu và tiêu đề Bảng tính đứng yên khi cuộn | `vd.staff` | Cuộn ngang và dọc lưới 8021; máy đã đo bằng Playwright, mắt người xác nhận |
| ☐ | `AC-11.11` | Bảng tính trên điện thoại và máy tính bảng | `vd.staff` | Lưới cuộn trong khung, bấm được ô, hộp lọc mở được |
| ☐ | `AC-8.10` | Bảng dữ liệu có viền ô, tiêu đề xanh lá, màu cột và ô cảnh báo | `mkt.manager` | Mở `/bang/bao_cao_mkt/` ở nền sáng rồi nền tối: mọi ô có viền, tiêu đề xanh lá, cột Tỉ lệ chốt vàng, ô CPO vượt 1.500.000 đỏ, ô đạt xanh lá; mở một báo cáo ở Lịch sử báo cáo thấy cùng màu |
| ☐ | `AC-11.18` | Bảng tính là trang toàn màn hình riêng; độ rộng, thứ tự, cột ẩn nhớ trên trình duyệt | `mkt.manager` | Không thanh bên hệ thống; kéo mép chữ cột, kéo thả chữ cột, ẩn cột rồi tải lại vẫn giữ; Đặt lại cột về mặc định |
| ☐ | `AC-13.6` | Bảng tin trên điện thoại | `sale.staff` | Mở `/bang-tin/` trên máy thật: bài đọc được, bấm Thích và gửi bình luận được, thanh bên xếp xuống dưới bài, không tràn ngang |
| ☐ | `AC-11.27` | Bảng tính nhìn và thao tác như KN Demo | `mkt.manager`, `vd.staff` | Đặt cạnh ảnh `docs/tham-khao/kn-demo/`: khung, thanh công cụ, thanh công thức, số dòng, chữ cột, cột trống, chân trang, ⛶; kéo chọn vùng thấy viền vàng và tay kéo điền |

### Bảy việc ở `docs/04` mục 17

| ☐ | Việc | Trạng thái |
|---|---|---|
| ☐ | Cài từ đầu trên máy sạch, tới màn hình đăng nhập | Chạy được — `manage.py du_lieu_mau`, có bài kiểm tự động |
| ☐ | Ba vai trò chạy trọn quy trình của mình | Chạy được — có bài tự động tương ứng, nhưng người vẫn phải bấm thử |
| ☐ | Nhập tệp Excel thật, không chỉnh sửa trước | Chạy được — `docs/tham-khao/vandon-mau.xlsx` vào bảng vận đơn qua Bảng dữ liệu → Nhập tệp |
| ☐ | Xuất báo cáo, mở bằng Excel, đối chiếu | Chạy được từ màn hình Báo cáo tổng hợp, chưa thử |
| ☐ | Thử trên điện thoại và máy tính bảng thật | Chạy được, chưa thử |
| ☐ | Phục hồi từ bản sao lưu | Chạy được — `scripts/restore.sh`, chưa thử |
| ☐ | Ngắt mạng giữa chừng, kiểm thông báo lỗi | Chạy được, chưa thử |

**Mười chín việc đều chạy được**, chỉ còn `AC-10.3` biết trước là chưa đạt
(trang 404 tiếng Việt — K9, người dùng chốt chưa làm). `AC-1.7` từng nằm ở bảng trên nhưng đã
bỏ theo **Q34** — không cần điều hướng sau đăng nhập nữa.

---

## Khi nào nghiệm thu

Backlog **V4** để ngỏ mốc, đề xuất **hết Giai đoạn 5** — mốc đó nay đã qua.
Backlog mục 6 ghi rõ: Giai đoạn 0 tới 7 đều đã giao và đã chạy kiểm thử tự
động, nhưng **người dùng chưa trực tiếp thử màn hình nào**. Kịch bản bấm tay
trọn một đợt nằm ở `docs/07-kich-ban-nghiem-thu.md`.

Phần trăm trong `dashboard-tien-do.html` là tiến độ **đã làm**, không phải
**đã nghiệm thu**. Hai con số đó có thể lệch nhau.

Điều kiện hoàn thành phase 1 nằm ở `docs/04` mục 18, bảy điều. Ba điều đã có
mã kiểm tự động:

| Điều | Kiểm bằng |
|---|---|
| 1 · Mọi tiêu chí Tự động đều có bài kiểm và đạt | `tests/test_truy_vet.py` |
| 2 · Ma trận kiểm chéo kiểm đủ, cả hai chiều | `tests/test_ma_tran_phan_quyen.py` |
| 6 · Ba vai trò chạy trọn quy trình | `tests/test_luong_ba_bo_phan.py` |

Bốn điều còn lại — phục hồi sao lưu, nhập tệp Excel thật, dữ liệu thật, bàn
giao tài liệu — cần người làm và cần Giai đoạn 7 và 8.

---

## Việc còn thiếu trong chính kế hoạch này

Ghi ra để không tự lừa mình:

| # | Thiếu | Vì sao chưa làm |
|---|---|---|
| 1 | Không có gì chạy kiểm thử tự động khi đẩy mã lên kho | Người dùng chốt chưa dựng, vì backlog **V2** còn để ngỏ ai vận hành sau bàn giao |
| 2 | Đo tải 50 người và kiểm tải 100 người / 100 nghìn khách mới chạy trên máy phát triển (máy ảo 4 nhân), chưa chạy trên máy chủ thật | Máy chủ chưa có — Giai đoạn 8; `scripts/kiem-tai-kn-crm.*` chạy lại được trên bất kỳ máy có Docker, kết quả trên máy cá nhân chỉ để so tương đối |
| 3 | Bài trình duyệt thật (Playwright) và hiệu năng 50.000 dòng không chạy trong container `web` | Image không có Chromium và `pytest` mặc định bỏ dấu `cham`; chạy trên máy phát triển — backlog **K19** |
| 4 | Chưa kiểm khả năng đọc màn hình cho người khiếm thị | Không có yêu cầu nào nêu, chưa hỏi người dùng |
| 5 | Hai bài đánh dấu `xfail`: hộp lọc cột trong Playwright (K23) và ngân sách 10 truy vấn trên 50.000 dòng (K24, đếm được 12) | Người dùng cần demo gấp ngày 03.09.2026; nợ ghi ở backlog, không nới ngưỡng |

## Bổ sung 10.09.2026 — AC-21, lưới master Vận đơn mới

Các lệnh dưới đây chạy từ gốc repository. Chỉ dùng DB pytest, không dùng
launcher hoặc `seed_perf` trên database đang làm việc. Hai bộ Chrome cũ
`kiem-thu-feedback-ui.cjs`/`test_feedback_browser_server.py` chuyển sang bộ
master; số liệu baseline cũ được giữ theo snapshot trước ADR-021.

```powershell
# Hồi quy ứng dụng
 docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest crm/tests orders/tests forms_builder/tests core/tests
# Terminal 1: server test cho Chrome host, DB riêng
 docker compose -f deploy/docker-compose.yml run --rm -p 8031:8031 -e RUN_MIGRATIONS=0 -e POSTGRES_DB=knjsc_master_ui -e KN_MASTER_BROWSER=1 web pytest crm/tests/test_master_browser_server.py --liveserver=0.0.0.0:8031
# Terminal 2: Node có Playwright và Chrome được cài sẵn
 node scripts/kiem-thu-master-ui.cjs
```

Capacity: tạo snapshot Git trước sửa vào `.agents/design-state/review/master/before/app`
(ví dụ `git archive HEAD app` **trước triển khai**, không lấy HEAD sau khi đã
commit thay đổi để gọi là baseline). Gắn chỉ đọc `/before`, kết quả vào
`/evidence`. Trên Windows, thay `C:/KNJSC/KNJSC` bằng gốc checkout thực tế:

```powershell
 docker compose -f deploy/docker-compose.yml run --rm -p 8032:8032 -p 8033:8033 -v C:/KNJSC/KNJSC/.agents/design-state/review/master/before:/before:ro -v C:/KNJSC/KNJSC/.agents/design-state/review/master:/evidence -e RUN_MIGRATIONS=0 -e POSTGRES_DB=knjsc_master_capacity -e KN_MASTER_CAPACITY=1 web pytest crm/tests/test_master_capacity.py -s
# Song song, terminal host:
 node scripts/kiem-thu-master-capacity.cjs
```

Fixture kiểm tên DB `test_knjsc_master_capacity*`, tạo 100k/300k dòng ×25 cột
và một chi tiết/dòng; 20 tài khoản test có scope toàn bảng để đo tình huống
đọc rộng. Gunicorn 3 worker ×4 thread, keep-alive5 giây, cùng settings trước/sau, DB PostgreSQL16.
Mỗi stage 45 giây (bỏ 10 giây đầu), 10 hoặc20 người, nghỉ1–3 giây; đọc/lọc/ghi
trọng số5/1/2, poll khi đến hạn8 giây trong lượt đọc. Không gọi nhập/xuất nền
trong workload này; chúng được kiểm hồi quy chức năng riêng.

Docker PostgreSQL hiện có `/dev/shm`64MB: kết nối WSGI **test** đặt
`max_parallel_workers_per_gather=0` cho cả hai snapshot sau khi baseline
ban đầu phát sinh thiếu shared memory. Không ALTER SYSTEM hoặc sửa Compose
đang dùng. Ghi rõ điều này khi so sánh. Dừng nếu sai DB/auth, process lỗi
hoặc lỗi HTTP vượt5%; lỗi dưới ngưỡng vẫn lưu, không coi là đạt nghiệm thu.
Các biến resume chỉ dùng lại kết quả cùng mã/cấu hình vừa kiểm, không thay
kết quả lịch sử thành số đo mới.

Báo riêng p95/đếm mẫu/lỗi theo request, byte phản hồi, số khối/DOM và heap
sau GC của Chrome. Browser không chạy chồng cửa sổ đo HTTP. Thời gian từ
phát event đến hai frame là phép đo phản hồi vẽ, không phải INP người dùng
thật. Kết quả local ngắn không thay kiểm endurance hoặc máy chủ sản xuất.


### Kéo chiều cao hàng Vận đơn mới — bổ sung ADR-021

**Cập nhật lưu thủ công 10.09.2026:** chạy `node scripts/kiem-thu-master-working-copy.cjs`
để kiểm buffer và Undo/Redo. Với server `test_master_browser_server.py` như
bên dưới, chạy `node scripts/kiem-thu-master-manual-ui.cjs` để kiểm Enter
không POST, popup X, lưu ô ngoài bộ lọc, reload bỏ nháp, mất phản hồi/replay
và menu mobile. Mỗi runner Chrome dùng một lượt fixture mới, không chạy hai
runner cùng server/tệp tín hiệu. Bài master UI hiện có đã đổi sang Ctrl+S
sau các thao tác cần kiểm ghi database.

Kiểm toán học hình học: `node scripts/kiem-thu-master-row-geometry.cjs`.
Bộ Chrome hiện có gọi thêm `scripts/kiem-thu-master-row-height.cjs`; dùng
server pytest `test_master_browser_server.py` với DB `knjsc_master_rows` và
`KN_MASTER_BROWSER=1`, cổng 8031 như hướng dẫn master ở trên.

Chỉ đo trình duyệt 100k/300k, không chạy lại HTTP load:

```powershell
docker compose -f deploy/docker-compose.yml run --rm -p 8033:8033 -v C:/KNJSC/KNJSC/.agents/design-state/review/master:/evidence -e RUN_MIGRATIONS=0 -e POSTGRES_DB=knjsc_master_capacity_rows -e KN_MASTER_ROW_CAPACITY=1 web pytest crm/tests/test_master_row_capacity.py --tb=short
# Khi fixture đã tạo dữ liệu, chạy ở terminal thứ hai với Node/Playwright hiện có:
node scripts/kiem-thu-master-row-capacity.cjs
```

Thay đường dẫn mount bằng checkout trên máy tương ứng. Fixture chặn database
không có tiền tố test; dữ liệu tổng hợp 25 cột và một chi tiết sản phẩm mỗi dòng.
Không chạy trên DB thật, không dùng 20 khách mẫu. Kết quả/ảnh ở thư mục review
local; báo p95, số mẫu, cách đo, cache/DOM/heap và hạn chế riêng cho bản này.

## Kiểm chứng chín hạng mục Vận đơn mới — 10.09.2026

Kế hoạch đủ Unit, Functional, E2E, UI/UX và Performance. Các fixture ghi chỉ
chạy trên DB test. Xem [báo cáo và giới hạn](kiem-chung-master-nine.md).

```powershell
node scripts/kiem-thu-master-autosave-unit.cjs
node scripts/kiem-thu-master-queue-unit.cjs
node scripts/kiem-thu-master-scope-unit.cjs
node scripts/kiem-thu-master-conflict-unit.cjs
node scripts/kiem-thu-master-working-copy.cjs
node scripts/kiem-thu-master-row-geometry.cjs
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 -e POSTGRES_DB=knjsc_nine_verify web pytest crm/tests orders/tests forms_builder/tests core/tests tests/test_luong_ba_bo_phan.py -ra
# Server UI test cổng 8035, sau đó chạy script Chrome từ terminal khác:
docker compose -f deploy/docker-compose.yml run --rm -p 8035:8035 -e RUN_MIGRATIONS=0 -e POSTGRES_DB=knjsc_nine_browser -e KN_MASTER_BROWSER=1 web pytest crm/tests/test_master_browser_server.py --liveserver=0.0.0.0:8035 -q
node scripts/kiem-thu-master-nine-ui.cjs
```

Node cần Playwright có sẵn trong runtime trên máy, không tự thêm dependency.
Capacity dùng `test_master_nine_capacity.py`, `KN_NINE_CAPACITY=1`, mount snapshot
workspace trước sửa tại `/before/app` (chỉ đọc) và thư mục artifact `/evidence`.
DB phải có tiền tố `knjsc_master_capacity_nine`; pytest tạo DB `test_...`.
Chạy lần lượt `NINE_STAGE=before` rồi `after`, cùng cổng 8036/cấu hình.
Mặc định 60s warmup +300s đo, 100k/300k ×10/20; Chrome phối hợp qua
`scripts/kiem-thu-master-nine-capacity.cjs`. `NINE_ENDURANCE=1` thêm 30 phút
đo với 20 người và Admin/Leader tranh chấp cùng dòng sau ma trận thường.
Dung lượng dùng `KN_NINE_STORAGE=1`, DB `knjsc_nine_storage` và
`test_master_nine_storage.py`; đo bảng, TOAST và index riêng cho history/receipt.
Không lấy bài mô phỏng IME làm bằng chứng đã kiểm bộ gõ Windows thật.

## Bàn điều hành KN CRM — ADR-022

Chạy vòng chức năng tập trung trước, dùng database test do pytest quản lý:

```powershell
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest `
  crm/tests/test_executive_statistics.py `
  crm/tests/test_master_grid.py `
  crm/tests/test_waybill_new.py `
  crm/tests/test_waybill_feedback.py `
  reports/tests -ra
```

Ma trận bắt buộc gồm: bảng Marketing hiện tại; bảng Sale có Ngày/Người bán/Số
đơn/Doanh thu; `van_don_moi`; `van_don` cũ; bảng chung đủ/thiếu nhãn. Kiểm
CPO/AOV/tỷ lệ từ tổng, kỳ trước 0, tiền USD/VND/CAD/PHP riêng, thiếu loại tiền,
tổng Sale–Vận đơn lệch/khớp và tối đa ba insight. Với Staff, Leader, Manager,
Admin kiểm cả nguồn được phép và URL nguồn bị từ chối; kiểm owner cấu hình nhưng
không phải Admin. Xóa mềm/ngừng bảng, ngày sai, bảng rỗng, số không hợp lệ, thiếu
chi tiết sản phẩm và lỗi giả lập một profile phải có kết quả rõ.

Trình duyệt mở 1440px, 1280px, 390px và zoom 125% ở sáng/tối. Dùng Tab tới form,
nút insight, SVG và `details`; kiểm focus nhìn thấy, bảng thay thế đọc được và
không có tràn ngang toàn trang. Bật `prefers-reduced-motion: reduce`; đường giữ
phẳng, mặt trước cột giữ tỷ lệ số liệu và phần sâu luôn 6px. Kiểm link insight có
`f_ngay__lon_bang`, `f_ngay__nho_bang` và đúng bộ lọc trạng thái.

Hiệu năng chạy riêng, không dùng database thật: fixture phải chặn tên DB không có
tiền tố test. Tạo 20.000 dòng Sale rồi 100.000/300.000 Vận đơn, warmup trước khi
đo ít nhất 20 request cho mỗi nguồn và góc tổng hợp. Ghi p50/p95/max, lỗi, số
query và đỉnh cấp phát Python của một request riêng; p95 mục tiêu ≤1 giây. So
sánh số query và bộ nhớ ở hai cỡ dữ liệu để phát hiện N+1 hoặc nạp dòng thô.
Không chạy chồng với browser hoặc bài tải lưới ADR-021; không coi kết quả dữ
liệu nhỏ là đã đạt AC-22.9.
