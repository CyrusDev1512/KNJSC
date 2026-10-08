# Biên bản kiểm chứng — Kiểm toàn diện `Staging` trước khi gộp `main` (08.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 08.10: kiểm toàn bộ phạm vi mới nhất trước khi gộp `main`: E2E, unit, functional, UI/UX, migration, smoke, backend; chạy liên tục tới hết. Chỉ kiểm và báo, không tự sửa, không tự gộp `main` |
| Phạm vi | `Staging` `450b6da` hơn `main` `a73f743` 10 PR, 175 tệp (+7.011 / −411): #91 săn lỗi đồng thời · #92 bảo mật · #93 săn lỗi tiếp · #94 tài liệu · #95 ma trận quyền, mã đơn duy nhất, xoá dòng bỏ đơn gốc, `kiem_tra_du_lieu` · #97 Báo cáo tổng hợp đầu trang gọn · #96 ERP mở rộng mặc định, phân trang, lưới bớt việc thừa · #98 CRM nhanh khi bảng lớn · #99 chỉ Admin xoá dòng · #100 biên bản đo |
| Migration mới | `core/0007_submission_receipt`, `forms_builder/0017_datarecord_val_order_code` |
| Môi trường | Máy ảo Claude Code trên web: Python 3.11 (CI 3.12), Django 5.2.17, PostgreSQL 16, Redis, Celery worker và beat, Chromium Playwright 1194. Mỗi loại kiểm một DB riêng |
| Kết luận | _điền ở cuối_ |

## 1. Unit, functional, backend

| Kiểm | Lệnh (từ `app/`) | Kết quả |
|---|---|---|
| Toàn bộ trừ trình duyệt, gồm bài chậm, có Redis | `python -m pytest -m "not trinh_duyet" -rs` | **3.124 đạt, 7 bỏ qua, 0 đỏ**, 11 phút 38 giây |
| Như trên, Redis không với tới (như CI) | Như trên, `CRM_CACHE_URL` và `REDIS_URL` trỏ cổng đóng | **3.124 đạt, 7 bỏ qua, 0 đỏ**, 12 phút 14 giây |
| 7 bài bỏ qua | `-rs` | Cả 7 là bài kiểm tải hay đo dung lượng, đòi DB thử riêng: `test_scroll_fixture`, `test_executive_statistics_capacity`, `test_master_capacity`, `test_master_nine_capacity`, `test_master_nine_storage`, `test_master_row_capacity`, `test_optimization_capacity` |
| Cấu hình Django | `manage.py check` với `test`, `dev`, `bangtinh` | Không có vấn đề |
| Cấu hình phát hành, một tên miền | `check --deploy --settings=knjsc.settings.prod` (khoá và tên máy giả) | Không có vấn đề |
| Cấu hình phát hành, hai tên miền ERP và CRM (AC-1.11, mới ở #95) | Như trên, `MAIN_APP_URL`, `BANGTINH_URL` khác tên miền | Thiếu `SESSION_COOKIE_DOMAIN`, `CSRF_COOKIE_DOMAIN`: dừng ở `core.E001`, đúng. Đặt `.vidu.test`: không có vấn đề. **VPS phải có hai biến này trước khi phát hành bản này** |
| CI trên đầu `Staging` `450b6da` | GitHub Actions | "pytest (bộ chính)" và "pytest e2e (Chromium)" đều xanh |

## 2. Migration

DB riêng `knjsc_mig`, mã `Staging`:

| Bước | Kết quả |
|---|---|
| `makemigrations --check --dry-run` | "No changes detected" |
| Dựng từ trống: `migrate` → `tao_bang_van_don` → `du_lieu_mau` → `configure_erp_reports` → `configure_delivery_daily_report` → `nap_du_lieu_van_don` | Chạy hết, không lỗi (`migrate` 7,3 s) |
| Thêm 5 đơn qua `create_order_once` | 10.005 dòng vận đơn, 5 biên nhận lần nộp |
| `forms_builder` 0017 → 0016 | Bỏ cột `val_order_code` và chỉ mục duy nhất; mã băm `data` và mã đơn của 10.005 dòng y nguyên |
| 0016 → 0017 | Điền lại khoá cho đủ 10.005 dòng, tạo lại chỉ mục duy nhất (10,8 s); `data` y nguyên |
| `core` 0007 → 0006 → 0007 | Bảng `submission_receipt` bỏ rồi tạo lại; 5 biên nhận mất theo, đúng ý tệp (biên nhận chỉ chống gửi lặp) |
| `migrate --check`, `kiem_tra_du_lieu` | Không còn migration chưa chạy; "Dữ liệu khớp." |

## 3. Cập nhật như máy chủ dự án (`main` → `Staging`)

Dữ liệu tạo bằng mã `main` (worktree cùng cây tệp với `main`), rồi đổi sang mã `Staging` và chạy đúng chuỗi lệnh của
launcher.

**Ca dữ liệu sạch** (`knjsc_nc`: 10.005 dòng vận đơn, 380 báo cáo MKT, 5 đơn lên trên `main`):

| Kiểm | Kết quả |
|---|---|
| `migrate` trên `Staging` | Áp `core/0007` và `forms_builder/0017` trong **8,0 s** |
| Dữ liệu trước và sau | Mã băm `data` của mọi dòng vận đơn, số đơn, dòng đơn, số báo cáo: y nguyên. Khoá mã đơn điền đủ |
| `kiem_tra_du_lieu` | Mã đơn trùng 0, đơn mồ côi 0. Báo **5 dòng `bao_cao_mkt` lệch cột tính sẵn** — xem mục 9 |

**Ca dữ liệu có hai dòng sống cùng mã đơn** (`knjsc_nc2`): **TL-76**, xem mục 8.

| Kiểm | Kết quả |
|---|---|
| `kiem_tra_du_lieu` trước `migrate` | Đổ `ProgrammingError: column … val_order_code does not exist` |
| `migrate` | Dừng ở `0017`, báo "mã đơn trùng … MAU-20260910-0001 (2 dòng)". `forms_builder` không đổi dở; `core/0007` đã áp |
| Mã `Staging` chạy trên DB chưa có `0017` | ERP `/` 200; CRM `/`, `/thu-muc/`, khung lưới 200; **ERP `/bang/van_don/` và CRM `du-lieu/` 500** |
| Xoá mềm dòng thừa bằng SQL rồi `migrate` | Qua; `kiem_tra_du_lieu` "Dữ liệu khớp." |

## 4. Smoke trên hệ thống thật

ERP `runserver` 8020, CRM 8021 (`knjsc.settings.bangtinh`), Celery worker (hàng `celery`, `crm_heavy`) và beat, Redis.
DB `knjsc_ht` dựng như máy mới: chuỗi lệnh launcher, `nap_du_lieu_van_don` (10.000 dòng), `nap_bao_cao_mau --nguoi 10
--lan 2` (760 báo cáo).

| Kiểm | Kết quả |
|---|---|
| 12 tài khoản mẫu × 7 trang ERP + 6 trang CRM (HTTP, có đăng nhập) | **0 trả lời 5xx.** 403/404 chỉ ở chỗ ngoài quyền: Nhân sự với Staff; Bảng dữ liệu `van_don` ngoài Admin, Sale Manager, Vận đơn Manager; Nhật ký ngoài Admin; MKT ở thư mục và lưới CRM; Vận đơn ở Lên đơn. `sale.moi` mọi trang chuyển sang đổi mật khẩu |
| Tác vụ nền | `feed.thiep_sinh_nhat` gửi qua worker: "succeeded". `thiep_sinh_nhat`, `thuong_sao_thang` chạy tay: rc 0. Beat khởi động, không lỗi |
| `collectstatic` | 158 tệp, 1,6 s |

## 5. E2E

| Kiểm | Lệnh | Kết quả |
|---|---|---|
| Lượt 1 của CI | `pytest tests/e2e -m trinh_duyet -vv -rs -o faulthandler_timeout=120` | 55 đạt, 2 bỏ qua có chủ ý, 9 đỏ — xem dòng dưới; 7 phút 20 giây |
| 9 bài đỏ `tests/e2e/test_pha_luoi_ghi_chu.py` | Như trên | Đỏ vì Chromium của máy ảo không tải được phông Google qua proxy (`ERR_CERT_AUTHORITY_INVALID`), bài coi đó là lỗi console. Như lượt 04.10. Chạy lại với phông Google trả rỗng cho cả tab máy tính lẫn tab điện thoại (vá `conftest` tạm, **không commit**, đã gỡ): **9/9 đạt**. Trên CI có mạng thật thì xanh |
| Lượt 2 của CI | `pytest -m trinh_duyet --ignore=tests/e2e …` | 19 đạt, 9 bỏ qua (giá đỡ cho script Node, đòi biến môi trường riêng) |
| 6 tệp e2e mới hoặc đã sửa trong đợt này, chạy 3 lần liền | `test_admin_xoa_dong`, `test_erp_mo_rong_mac_dinh`, `test_luoi_hoi_nhe`, `test_mat_mang_e2e`, `test_phan_trang_khong_tai_lai`; `reports/tests/test_bo_cuc_bao_cao_e2e.py` | **9/9 và 14/14 đạt cả 3 lần**, không chập chờn |

## 6. UI/UX — đóng vai bằng Playwright trên hệ thống thật

Mọi bước dưới **không có lỗi JS và không có trả lời 5xx**; tài nguyên ngoài (phông Google) bị chặn có chủ ý.

| PR | Vai | Thao tác | Kết quả |
|---|---|---|---|
| #91, #93 | `sale.staff` | Lên đơn bằng giao diện, đơn giá gõ "1.200,50", bấm đúp Lưu đơn | Một đơn `DH-0810-0001`; đơn giá lưu 1200.50 |
| #93 | `sale.staff` | Lên đơn, tên khách gõ dạng tổ hợp (NFD) | Tên lưu NFC; tìm trên lưới ra 1 dòng |
| #99 | `sale.staff` | Trang đơn gốc; gửi thẳng lệnh Bỏ đơn | Không có nút; báo "Chỉ Quản trị mới bỏ được đơn."; đơn còn |
| #95 | `vd.manager` | Sửa Mã đơn trên lưới thành mã của dòng khác | Báo "Mã đơn … đã có ở một dòng khác trong bảng. Mỗi mã đơn chỉ một dòng."; ô giữ mã cũ |
| #99 | `vd.manager` | Menu "…"; gửi thẳng `delete_rows` | Không có nút Xoá dòng; **403** |
| #99 | `quantri` | Xoá dòng có đơn gốc | Dòng xoá mềm, đơn gốc bị bỏ |
| #99 | `quantri` | Ctrl+Z | Máy chủ khôi phục dòng và đơn. Lưới đang lọc còn đúng dòng đó thì **không hiện lại cho tới khi tải trang: TL-77**. Không lọc: 10.001 → 10.002 dòng, đúng |
| #99 | `quantri` | Shift + bấm số dòng 1 rồi 5 | Hộp xác nhận ghi 5 dòng |
| #93 | `vd.staff` | Mất mạng lúc lưu ô, rồi có mạng | "Lỗi lưu · Mất kết nối mạng — thay đổi chưa được gửi lên máy chủ…"; có mạng lại tự lưu, lịch sử ô đúng 1 lần |
| #91 | `mkt.staff` | Nộp báo cáo, bấm đúp Nộp | Một báo cáo; sang Lịch sử |
| #96 | `mkt.manager` | Vào ERP; bấm hiện nền; tải lại; bấm lại | Mở rộng mặc định; nhớ lựa chọn sau khi tải lại |
| #96 | `mkt.manager` | Lịch sử báo cáo sang trang 2 | Tại chỗ, `?trang=2` |
| #96 | `quantri` | Nhật ký lọc `hanh_dong=create` sang trang 2 | Giữ lọc, tại chỗ |
| #97 | `mkt.manager` | Báo cáo tổng hợp | Thanh trên có "Báo cáo Marketing", kỳ "01/10 – 08/10/2026"; menu ⋯ đủ Gộp, Không gộp, Ngưỡng màu, Giải thích số liệu, Toàn màn hình, Xuất Excel; đổi Gộp và sang trang 2 tại chỗ, giữ `gop=1` |
| #96, #98 | `vd.manager` | Mở lưới; mở panel Bộ lọc; lọc Canada | Panel chỉ tải khi bấm; lọc tại chỗ; panel ghi "Canada (10000)", lưới 10.000 dòng |
| #98 | 7 vai | Trang chủ và thư mục CRM so với đếm theo phạm vi cũ trong DB | Khớp cả 7: `quantri`, `vd.manager`, `vd.staff` 10.002; `sale.manager` 1.667; `sale.leader` 3.335; `sale.staff` 1.668; `sale.staff2` 1.667 |
| Bố cục | 4 vai × 4–6 trang × 1366×768, 1920×1080, 390×844 | 57 lượt mở trang, không trang nào tràn ngang |

**Quét liên kết** (11 tài khoản, mỗi vai đi hết liên kết trong trang, tối đa 70 trang):

| Dịch vụ | Trang đã mở | Vấn đề |
|---|---|---|
| ERP | 445 | `sale.manager`: nút "Cột" của `van_don` ra 403 (**TL-78**, có từ trước). 20 lượt "tải tài liệu" chuyển ra Google Docs, máy ảo chặn mạng ngoài — không phải lỗi |
| CRM | 72 | Hai lượt mở `mau-nhap.xlsx` là tải tệp mẫu, không phải trang — không phải lỗi |

Không trang nào trả 5xx hay có lỗi JS.

## 7. Hiệu năng — chỉ kiểm không tụt

_điền khi xong_

## 8. Lỗi mới — chưa sửa

Chi tiết, cách tái hiện, cách sửa đề xuất ở [test-log](test-log.md) mục 08.10.2026.

| Mã | Mức | Lỗi | Chặn gộp `main`? |
|---|---|---|---|
| TL-76 | Vừa | Dữ liệu có mã đơn trùng thì cập nhật lên `0017` kẹt. Mã mới làm lưới 500, nên không dọn trùng trên lưới được như lời báo; `kiem_tra_du_lieu` cũng không chạy được trước `migrate` | Không chặn dùng hằng ngày. Cần rà trùng trước mỗi lần cập nhật máy có dữ liệu thật |
| TL-77 | Nhẹ | Ctrl+Z sau khi xoá dòng duy nhất đang lọc: máy chủ khôi phục đúng, lưới không hiện lại tới khi tải trang | Không |
| TL-78 | Nhẹ, có từ trước | Danh sách Bảng dữ liệu hiện nút "Cột" của `van_don` cho `sale.manager`, bấm 403 | Không — `main` cũng vậy |

**Rà mã đơn trùng trước khi cập nhật (TL-76), chỉ đọc, chạy được trên dữ liệu cũ.** Ra rỗng là cập nhật được; ra dòng
nào thì sửa mã hay xoá dòng thừa trên lưới **trước khi** kéo mã mới.

```sql
SELECT btrim(r.data->>'ma_don') AS ma_don, count(*) AS so_dong
FROM forms_builder_datarecord r JOIN forms_builder_tabledef t ON t.id = r.table_id
WHERE (t.code = 'van_don' OR t.workflow = 'waybill') AND r.deleted_at IS NULL
  AND btrim(coalesce(r.data->>'ma_don', '')) <> ''
GROUP BY r.table_id, btrim(r.data->>'ma_don') HAVING count(*) > 1;
```

Máy local: `docker compose -f deploy/docker-compose.yml exec db psql -U knjsc -d knjsc_db -c "<câu trên>"`. Đã thử trên
máy ảo: DB sạch ra rỗng; DB có cặp trùng ra `MAU-20260910-0001 | 2`.

## 9. Ghi chú, có từ trước (`main` cũng vậy)

- Ô Tìm của lưới không tìm theo Mã đơn. Nó chỉ tìm các cột có nhãn nghiệp vụ: khách, SĐT, Sale, sản phẩm, trạng thái
  (`ColumnMap.searchable_paths`, không đổi trong đợt này).
- `sale.manager` thấy 1.667 dòng vận đơn, ít hơn `sale.leader` 3.335. Mã `main` ra đúng các số này trên cùng dữ liệu.
  ADR-020 ghi "Leader/Manager Sale giữ phạm vi hiện có".
- Sau khi cập nhật, 5 dòng `bao_cao_mkt` do `du_lieu_mau` của `main` tạo lệch cột tính sẵn (CPO, Giá Mess, AOV lưu đã làm
  tròn; thiếu `cpqc_doanh_so`). Dòng nộp qua form không lệch. `kiem_tra_du_lieu --sua` tính lại.
- Sale bị từ chối Bỏ đơn thì về `/thu-muc/`, không về trang đơn; thông báo đúng.

## 10. Chưa kiểm được

- Docker image và `KN JSC.bat` thật: proxy chặn `apt-get`. `Dockerfile`, `entrypoint.sh` không đổi trong đợt này;
  `requirements.txt` đổi Django 5.2.6 → 5.2.17 (#92), nên máy local sẽ dựng lại image lần đầu.
- Máy Windows, VPS.
- Chặng 2: chủ dự án tự thử ở local. Lượt này không thay được.
