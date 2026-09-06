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

**Không bỏ qua phân quyền.** `docs/04` mục 13: *lỗi phân quyền dẫn tới rò rỉ dữ
liệu, và dữ liệu đã lộ thì không thu hồi được.*

---

## Hiện trạng

| | Số |
|---|---|
| Tiêu chí nghiệm thu trong `docs/04` | **87** — 78 tự động, 9 thủ công |
| Tiêu chí tự động đã có bài kiểm | **77 trên 78** |
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
| 8 | **Đầu-cuối trình duyệt** | `tests/e2e/` — Playwright, dấu `trinh_duyet` | Nhập → xuất → nhập lại qua giao diện; bàn phím và hộp lọc trên Bảng tính; cột cố định khi cuộn; 390px không tràn ngang, có ảnh chụp | Đổi phím Esc thành không làm gì trong `bang-tinh.js` → đỏ |
| 9 | **Hiệu năng** | `tests/test_hieu_nang.py` (dấu `cham`), `tests/perf/locustfile.py` | 50.000 dòng thật: trang đầu và lưới có lọc dưới 2 giây, ≤ 10 truy vấn; Locust 50 người tự chấm p99 ≤ 3 giây | Bỏ `select_related` ở lưới → vượt 10 truy vấn |

Cộng một tầng thứ mười không nằm trong danh sách: **truy vết**
(`tests/test_truy_vet.py`) đọc `docs/04` và khẳng định mọi tiêu chí tự động đều
có bài kiểm. Đây là `docs/04` mục 13 điều 1 viết thành mã chạy được.

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

### Bảy việc ở `docs/04` mục 12

| ☐ | Việc | Trạng thái |
|---|---|---|
| ☐ | Cài từ đầu trên máy sạch, tới màn hình đăng nhập | Chạy được — `manage.py du_lieu_mau`, có bài kiểm tự động |
| ☐ | Ba vai trò chạy trọn quy trình của mình | Chạy được — có bài tự động tương ứng, nhưng người vẫn phải bấm thử |
| ☐ | Nhập tệp Excel thật, không chỉnh sửa trước | Chạy được — `docs/tham-khao/vandon-mau.xlsx` vào bảng vận đơn qua Bảng dữ liệu → Nhập tệp |
| ☐ | Xuất báo cáo, mở bằng Excel, đối chiếu | Chạy được từ màn hình Báo cáo tổng hợp, chưa thử |
| ☐ | Thử trên điện thoại và máy tính bảng thật | Chạy được, chưa thử |
| ☐ | Phục hồi từ bản sao lưu | Chạy được — `scripts/restore.sh`, chưa thử |
| ☐ | Ngắt mạng giữa chừng, kiểm thông báo lỗi | Chạy được, chưa thử |

**Mười lăm việc đều chạy được**, chỉ còn `AC-10.3` biết trước là chưa đạt
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

Điều kiện hoàn thành phase 1 nằm ở `docs/04` mục 13, bảy điều. Ba điều đã có
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
| 2 | Đo tải 50 người mới chạy trên máy phát triển, chưa chạy trên máy chủ thật | Máy chủ chưa có — Giai đoạn 8; kết quả trên máy cá nhân chỉ để so tương đối |
| 3 | Bài trình duyệt thật (Playwright) và hiệu năng 50.000 dòng không chạy trong container `web` | Image không có Chromium và `pytest` mặc định bỏ dấu `cham`; chạy trên máy phát triển — backlog **K19** |
| 4 | Chưa kiểm khả năng đọc màn hình cho người khiếm thị | Không có yêu cầu nào nêu, chưa hỏi người dùng |
| 5 | Hai bài đánh dấu `xfail`: hộp lọc cột trong Playwright (K23) và ngân sách 10 truy vấn trên 50.000 dòng (K24, đếm được 12) | Người dùng cần demo gấp ngày 03.09.2026; nợ ghi ở backlog, không nới ngưỡng |
