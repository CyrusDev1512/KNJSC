# Kế hoạch kiểm thử

| Mục | Nội dung |
|---|---|
| Dự án | Kim Ngân JSC — Hệ thống vận hành nội bộ |
| Giai đoạn | Phase 1 |
| Ngày | 29.08.2026 |
| Tài liệu liên quan | `04-tieu-chi-nghiem-thu.md` · `backlog.md` mục V4, V5 |

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

**Không bỏ qua phân quyền.** `docs/04` mục 12: *lỗi phân quyền dẫn tới rò rỉ dữ
liệu, và dữ liệu đã lộ thì không thu hồi được.*

---

## Hiện trạng

| | Số |
|---|---|
| Bài kiểm thử tự động | **748**, tất cả đạt |
| Bao phủ dòng mã | 83% |
| Tiêu chí nghiệm thu trong `docs/04` | 47 — 40 tự động, 7 thủ công |
| Tiêu chí tự động đã có bài kiểm | 28 trên 40 |
| Tiêu chí tự động còn hoãn | 12, đều thuộc Giai đoạn 6 tới 8 |

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

## Bảy tầng kiểm thử

| # | Tầng | Ở đâu | Kiểm cái gì | Đã thử gây lỗi |
|---|---|---|---|---|
| 1 | **Đơn vị** | `tests/test_hop_trang.py`, rải trong từng module | Hàm lẻ: ép kiểu, đọc tiền, bảng tương thích kiểu | Đổi kỳ vọng của một cặp kiểu |
| 2 | **Tệp chuyển đổi** | `core/tests/test_chuyen_doi.py` | Model khớp tệp, chạy xuôi và ngược, một nhánh lá | Bỏ `reverse_sql` của `0002_pg_trgm` → đỏ |
| 3 | **Kiểm khói** | `tests/test_khoi.py` | Mọi đường dẫn × mọi vai trò, không trả 500 | Gỡ `@login_required` một view → đỏ |
| 4 | **Chức năng** | Từng module, cộng `tests/test_luong_ba_bo_phan.py` | Luồng làm việc trọn vẹn qua HTTP | — |
| 5 | **Hộp đen** | `tests/test_ma_tran_phan_quyen.py` | 35 ô ma trận kiểm chéo `docs/04` mục 3 | Tìm ra 4 lỗi thật ngay lần chạy đầu |
| 6 | **Hộp trắng** | `tests/test_hop_trang.py`, bản đo bao phủ | Nhánh chỉ chạy khi có lỗi, đường huỷ giao dịch | Tìm ra lỗi đọc tiền sai gấp trăm lần |
| 7 | **Giao diện** | `core/tests/test_giao_dien.py` | Lớp CSS có thật, ô nhập có nhãn, bảng có tiêu đề | Thêm lớp bịa vào template → đỏ |

Cộng một tầng thứ tám không nằm trong danh sách: **truy vết**
(`tests/test_truy_vet.py`) đọc `docs/04` và khẳng định mọi tiêu chí tự động đều
có bài kiểm. Đây là `docs/04` mục 12 điều 1 viết thành mã chạy được.

---

## Vì sao bảy tầng, không phải một

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

12 tiêu chí tự động chưa có bài kiểm, tất cả vì tính năng chưa xây. Danh sách
này nằm trong `tests/test_truy_vet.py`, biến `HOAN`, và **rỗng dần theo tiến độ**
— thêm mã vào đó bắt buộc ghi lý do và giai đoạn.

| Tiêu chí | Chờ |
|---|---|
| `AC-5.1` → `AC-5.5` | Báo cáo tổng hợp — Giai đoạn 6 |
| `AC-7.5` → `AC-7.9` | Nhập xuất Excel — Giai đoạn 7 |
| `AC-7.1` | 50.000 bản ghi dưới 2 giây, cần `seed_perf.py` — Giai đoạn 8 |
| `AC-10.6` | Sao lưu tự động — Giai đoạn 8 |

---

## Danh sách kiểm thủ công

Chạy trước mỗi lần bàn giao. Máy không làm được những việc này.

### Tiêu chí thủ công trong `docs/04`

| ☐ | Mã | Việc | Tài khoản | Đạt khi |
|---|---|---|---|---|
| ☐ | `AC-1.7` | Đăng nhập vào thẳng màn hình của bộ phận mình | `sale.staff`, `vd.staff` | Sale vào Lên đơn, Vận đơn vào Bảng vận đơn |
| ☐ | `AC-2.4` | Thêm team mới, dùng ngay không khởi động lại | `quantri` | Team mới hiện ở ô chọn trong cùng phiên |
| ☐ | `AC-5.6` | Xuất báo cáo, mở bằng Excel, đối chiếu số | — | **Chưa chạy được** — Giai đoạn 6 và 7 |
| ☐ | `AC-10.1` | 50 người thao tác đồng thời | — | **Chưa chạy được** — chưa chọn công cụ, backlog K6 |
| ☐ | `AC-10.3` | Gặp lỗi hiện thông báo tiếng Việt, không trang trắng | bất kỳ | Gõ đường dẫn sai → trang 404 tiếng Việt. **Chưa làm** — backlog K9 |
| ☐ | `AC-10.4` | Dùng được trên điện thoại và máy tính bảng | bất kỳ | Mở trên máy thật, không tràn ngang, bấm được |
| ☐ | `AC-10.5` | Phục hồi từ bản sao lưu | — | **Chưa chạy được** — Giai đoạn 8 |

### Bảy việc ở `docs/04` mục 11

| ☐ | Việc | Trạng thái |
|---|---|---|
| ☐ | Cài từ đầu trên máy sạch, tới màn hình đăng nhập | Chạy được, chưa thử |
| ☐ | Ba vai trò chạy trọn quy trình của mình | Chạy được — có bài tự động tương ứng, nhưng người vẫn phải bấm thử |
| ☐ | Nhập tệp Excel thật, không chỉnh sửa trước | **Chưa** — Giai đoạn 7 |
| ☐ | Xuất báo cáo, mở bằng Excel, đối chiếu | **Chưa** — Giai đoạn 6 và 7 |
| ☐ | Thử trên điện thoại và máy tính bảng thật | Chạy được, chưa thử |
| ☐ | Phục hồi từ bản sao lưu | **Chưa** — Giai đoạn 8 |
| ☐ | Ngắt mạng giữa chừng, kiểm thông báo lỗi | Chạy được, chưa thử |

**Bốn trong mười bốn việc chưa chạy được** vì tính năng chưa có. Ghi rõ ở đây
thay vì để trống — không phải bỏ sót.

---

## Khi nào nghiệm thu

Backlog **V4** để ngỏ mốc, đề xuất **hết Giai đoạn 5**. Backlog mục 6 ghi rõ:
Giai đoạn 0 tới 5 đều đã giao và đã chạy kiểm thử tự động, nhưng **người dùng
chưa trực tiếp thử màn hình nào**.

Phần trăm trong `dashboard-tien-do.html` là tiến độ **đã làm**, không phải
**đã nghiệm thu**. Hai con số đó có thể lệch nhau.

Điều kiện hoàn thành phase 1 nằm ở `docs/04` mục 12, bảy điều. Ba điều đã có
mã kiểm tự động:

| Điều | Kiểm bằng |
|---|---|
| 1 · Mọi tiêu chí Tự động đều có bài kiểm và đạt | `tests/test_truy_vet.py` |
| 2 · Ma trận kiểm chéo kiểm đủ, cả hai chiều | `tests/test_ma_tran_phan_quyen.py` |
| 6 · Ba vai trò chạy trọn quy trình | `tests/test_luong_ba_bo_phan.py` |

Bốn điều còn lại — phục hồi sao lưu, nhập tệp Excel thật, dữ liệu thật, bàn
giao tài liệu — cần người làm và cần Giai đoạn 6 tới 8.

---

## Việc còn thiếu trong chính kế hoạch này

Ghi ra để không tự lừa mình:

| # | Thiếu | Vì sao chưa làm |
|---|---|---|
| 1 | Không có gì chạy kiểm thử tự động khi đẩy mã lên kho | Người dùng chốt chưa dựng, vì backlog **V2** còn để ngỏ ai vận hành sau bàn giao |
| 2 | Chưa đo hiệu năng thật, chỉ đếm số lệnh truy vấn | Cần `seed_perf.py` và công cụ đo tải — backlog **K6** |
| 3 | Chưa kiểm bằng trình duyệt thật | Người dùng chốt không thêm thư viện; HTMX sửa ô và giao diện điện thoại vẫn phải bấm tay |
| 4 | Chưa kiểm khả năng đọc màn hình cho người khiếm thị | Không có yêu cầu nào nêu, chưa hỏi người dùng |
