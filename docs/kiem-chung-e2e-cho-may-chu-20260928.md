# Kiểm chứng — Bài trình duyệt chờ máy chủ thử xong rồi mới dọn bảng (TL-67) — 28.09.2026

Nhánh `claude/e2e-cho-may-chu-truoc-khi-don` tách từ `main` (`f783001`), rồi đặt lại lên `69cceee` (sau #66 và
#56) trước khi đẩy. Chạy trên máy ảo Claude Code với
PostgreSQL 16 cục bộ (cổng 5434) và Chromium không màn hình (Playwright). Chỉ sửa mã kiểm thử: không đụng
mã ứng dụng, không migration, không thêm thư viện.

## Lỗi

CI trên `main` đỏ hai lượt liền: #94 sau khi gộp #63, #96 sau khi gộp #64. Cả hai đỏ ở job "pytest e2e
(Chromium)", bước `pytest tests/e2e`, kết quả "44 passed, 2 skipped, 1 error". Lỗi nằm ở bước dọn của
`test_bo_chip_loc_sau_khi_sap_xep_giu_thu_tu_moi`, bài cuối của `tests/e2e`:

```
django.db.utils.OperationalError: deadlock detected
django.core.management.base.CommandError: Database test_knjsc_db couldn't be flushed.
```

Log Postgres của CI cho thấy hai lệnh chờ khoá của nhau:
- lệnh `TRUNCATE …` mà pytest-django dùng để dọn bảng sau bài `transactional_db`;
- một `SELECT` của luồng máy chủ thử. Ở lượt #96 đó là truy vấn tải dữ liệu lưới (`forms_builder_datarecord`),
  ở lượt #94 là truy vấn lịch sử ô (`crm_gridcellhistory`).

## Nguyên nhân

Bài bấm × bỏ chip lọc rồi kết thúc ngay khi URL đổi, đúng lúc lưới vừa gửi yêu cầu tải lại dữ liệu.
Fixture `trang` đóng tab, nhưng máy chủ thử chạy ở luồng riêng nên vẫn chạy nốt truy vấn. Ngay sau đó,
pytest-django `TRUNCATE` mọi bảng và lấy khoá lần lượt từng bảng. Truy vấn giữ khoá bảng A và chờ bảng B,
còn `TRUNCATE` giữ B và chờ A. Postgres huỷ lệnh `TRUNCATE`, bài báo lỗi lúc dọn.

Đây là lỗi thứ tự dọn của bộ kiểm thử, không phải lỗi ứng dụng. PR #64 từng gặp lỗi này ở bài phân công
(4/6 lần) và tự vá riêng cho bài đó bằng cách về `about:blank` rồi chờ cứng 1 giây.

## Sửa

| Tệp | Thay đổi |
|---|---|
| `app/tests/live_server_requests.py` (mới) | `LiveServerRequests` đếm yêu cầu mà máy chủ thử đang xử lý dở, dựa trên hai tín hiệu `request_started` và `request_finished` của Django. Chỉ đếm yêu cầu đi qua `WSGIHandler`. Yêu cầu của test client (`ClientHandler`) chạy ngay trong luồng bài kiểm và có khi không phát `request_finished`, nên không đếm. `wait_idle(quiet=0.2, timeout=5)` chờ số đếm về 0 và giữ yên 0,2 s liền, để yêu cầu gửi ngay trước khi đóng tab kịp tới máy chủ. Quá 5 s thì thôi, không treo |
| `app/conftest.py` | Thêm fixture tự chạy `_live_server_idle_before_flush` cho mọi bài có `live_server`. Fixture gọi `transactional_db` trước, nên CSDL dựng trước và dọn sau nó. Sau khi các fixture của bài đã dọn (tab đã đóng), fixture chờ máy chủ yên. Quá hạn thì phát cảnh báo |
| `app/tests/e2e/test_phan_cong_o_chon.py` | Bỏ `roi_luoi` mà PR #64 thêm (về `about:blank` rồi chờ cứng 1 s), vì fixture chung đã lo việc này |
| `app/tests/test_live_server_requests.py` (mới) | 6 bài kiểm cơ chế, đều gắn TL-67: máy chủ rảnh thì chỉ chờ khoảng yên; chờ yêu cầu đang dở xong; chờ cả yêu cầu tới trong khoảng yên; yêu cầu treo thì tới hạn là thôi; không đếm test client; bộ đếm chung nối vào tín hiệu thật của Django |
| `CLAUDE.md` | Thêm một dòng ở mục Chạy kiểm thử: bài trình duyệt không cần tự chèn đoạn chờ |

## Kiểm

**Thứ tự fixture.** Chạy `pytest --setup-show` trên bài lỗi:

| Pha | Thứ tự |
|---|---|
| Dựng | `_django_db_helper` → `transactional_db` → `_live_server_helper` → `_live_server_idle_before_flush` → `trang` → `dang_nhap` |
| Dọn | `dang_nhap` → `trang` (đóng tab) → `_live_server_idle_before_flush` (chờ máy chủ yên) → `_live_server_helper` → `transactional_db` → `_django_db_helper` (`TRUNCATE`, sau cùng) |

**Chạy lặp riêng bài lỗi.** Dùng `--reuse-db`, cùng máy và cùng cách chạy cho cả trước và sau khi sửa:

| Mã | Số lần | Kẹt khoá |
|---|---|---|
| `main` `f783001`, chưa sửa, lượt 1 | 10 | 2. Hai lần chạy ngay sau đó hỏng theo vì bảng chưa dọn được (trùng khoá `org_department`, log Postgres xác nhận) |
| `main` `f783001`, chưa sửa, lượt 2 (worktree riêng) | 30 | 4. Mỗi lần kéo theo một lần hỏng như trên; chỉ 22/30 lần đạt sạch |
| Nhánh này | 30 | **0**, đạt 30/30 |
| Nhánh này, `tests/e2e/test_phan_cong_o_chon.py` (đã bỏ đoạn chờ cứng) | 10 × 2 bài | **0**, đạt 10/10 |
| Nhánh này sau khi đặt lại lên `main` `69cceee` | 10 | **0**, đạt 10/10 |

**pytest.** Chạy tuần tự, không có pytest nào chạy song song:

| Lệnh | Kết quả |
|---|---|
| `pytest tests/test_live_server_requests.py` | 6 đạt |
| `pytest tests/e2e -m trinh_duyet -rs` (lượt 1 của CI) | 35 đạt, 2 bỏ qua (như CI: không có dòng trống; kiểm tải 300k cần biến riêng). 9 bài đỏ **nhưng không có lỗi lúc dọn**, log không còn chữ `deadlock`. Cả 9 bài đỏ thuộc `test_pha_luoi_ghi_chu.py` và chỉ trượt vì lỗi console `ERR_CERT_AUTHORITY_INVALID`: proxy của máy ảo chặn phông Google. Lỗi này có sẵn trên `main` ở máy ảo và CI GitHub không gặp |
| `pytest -m trinh_duyet --ignore=tests/e2e --deselect crm/tests/test_luoi_dong_trong_va_ghim_e2e.py -rs` (lượt 2 của CI) | 3 đạt, 9 bỏ qua. Các bài bỏ qua là giá đỡ cho script Node, cần Chrome riêng, như CI. Có một cảnh báo "database đang có phiên khác" lúc xoá DB cuối phiên; cảnh báo này đã có từ trước khi sửa |
| `pytest -m "not trinh_duyet" --ignore=tests/perf -rs`, bộ đầy đủ kể cả bài chậm | **2.836 đạt**, 7 bỏ qua (thiếu điều kiện ngoài, như trước), chạy 8 phút 21 giây |
| Sau khi đặt lại lên `69cceee`: `tests/test_live_server_requests.py`, `tests/test_truy_vet.py`, `crm/tests/test_waybill_feedback.py` | 79 đạt |
| Sau khi đặt lại lên `69cceee`: `pytest tests/e2e -m trinh_duyet -rs` | 37 đạt, 2 bỏ qua. Vẫn 9 bài `test_pha_luoi_ghi_chu.py` đỏ vì phông bị chặn; **không có lỗi lúc dọn**, log không có `deadlock` |
| Sau khi đặt lại lên `69cceee`: lượt 2 của CI | 3 đạt, 9 bỏ qua |

**Thời gian.** Lượt `tests/e2e` chạy 260 s. Lượt đo trước đó trên nhánh PR #65 (chưa có 2 bài phân công của #64)
chạy 235 s. Phần tăng thêm gồm 2 bài phân công và khoảng 0,2 s chờ yên sau mỗi bài.

## Chưa kiểm / để lại

- CI GitHub: xem ở PR. Hai lượt CI của `main` sau #66 (#100) và #56 (#102) xanh vì lỗi chỉ xảy ra khi hai bên trùng
  thời điểm; chưa gộp bản sửa thì lượt sau vẫn có thể đỏ.
- Bài trình duyệt hỏng giữa chừng, trước khi tự đóng tab (tab tự mở, không qua `trang`), thì tab còn gọi máy
  chủ. Khi đó fixture chờ tối đa 5 s rồi cảnh báo; lỗi dọn vẫn có thể đi kèm cái đỏ sẵn có của bài.
- `crm/tests/test_luoi_dong_trong_va_ghim_e2e.py` vẫn bị CI loại, vì đỏ sẵn do lý do khác (xem `ci.yml`).
