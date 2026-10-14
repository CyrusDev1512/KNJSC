# Kế hoạch kiểm thử toàn diện KNJSC

> Lập 13.10.2026 trên `main` 3bfa9e6 bằng các agent chỉ đọc mã: 8 bản đồ phân hệ có kiểm chứng đối kháng, kiểm kê 154 đường dẫn × quyền, kiểm kê phép tính tiền, phân tích lọt lưới 87 lỗi TL trên mã hiện tại. Mọi khẳng định kèm đường dẫn tệp hoặc mã AC/ADR/TL; chỗ chưa xác minh được ghi rõ.

## Mục lục

| Phần | Nội dung | Ở đâu |
|---|---|---|
| 0 | Mục đích, phạm vi, bốn trục phân loại, quan hệ với docs/04, 05, 06, 07 | tệp này |
| 1 | Môi trường, dữ liệu, tài khoản và tiêu chí vào/ra từng chặng | [01-moi-truong-va-chang.md](08-ke-hoach-kiem-thu/01-moi-truong-va-chang.md) |
| 2 | Ma trận phân hệ × loại kiểm thử | [02-ma-tran-phan-he.md](08-ke-hoach-kiem-thu/02-ma-tran-phan-he.md) |
| 3.1–3.3 | Phân quyền (ma trận đường dẫn × vai), phiên và đăng nhập chung, tiền và oracle | [03a-phan-quyen-phien-tien.md](08-ke-hoach-kiem-thu/03a-phan-quyen-phien-tien.md) |
| 3.4–3.7 | Đồng thời và CAS, nhập/xuất Excel, tác vụ nền và lệnh, migration và toàn vẹn dữ liệu | [03b-dong-thoi-du-lieu-tac-vu.md](08-ke-hoach-kiem-thu/03b-dong-thoi-du-lieu-tac-vu.md) |
| 3.8–3.12 | Hiệu năng, bảo mật, giao diện, đơn vị JavaScript, vận hành và phát hành | [03c-phi-chuc-nang-van-hanh.md](08-ke-hoach-kiem-thu/03c-phi-chuc-nang-van-hanh.md) |
| 4 | Góc nhìn người dùng thật: hành trình theo vai | [04-goc-nguoi-dung.md](08-ke-hoach-kiem-thu/04-goc-nguoi-dung.md) |
| 5 | Góc nhìn QA: biên, giá trị xấu và đường lỗi | [05-goc-qa.md](08-ke-hoach-kiem-thu/05-goc-qa.md) |
| 6 | Danh sách kiểm tay Chặng 2 theo vùng đụng tới | [06-kiem-tay-chang-2.md](08-ke-hoach-kiem-thu/06-kiem-tay-chang-2.md) |
| 7 | Sổ tay gỡ lỗi | [07-so-tay-go-loi.md](08-ke-hoach-kiem-thu/07-so-tay-go-loi.md) |
| 8 | Phân tích lọt lưới các lỗi đã ghi nhận | [08-phan-tich-lot-luoi.md](08-ke-hoach-kiem-thu/08-phan-tich-lot-luoi.md) |
| 9 | **Lộ trình ưu tiên**: chuẩn bị, P0, P1, P2, dọn tài liệu, quyết định cần chủ dự án chốt | tệp này |
| 10 | Rủi ro còn lại và những gì cố ý không kiểm | tệp này |

**Đọc thế nào.** Chủ dự án: mục 0, rồi **mục 9** và 10 ngay trong tệp này. Người viết bài kiểm: mở đúng tệp phần. Người kiểm tay trước khi gộp `Staging` vào `main` (Chặng 2): mở [phần 6](08-ke-hoach-kiem-thu/06-kiem-tay-chang-2.md). Gặp lỗi: [phần 7](08-ke-hoach-kiem-thu/07-so-tay-go-loi.md), rồi ghi `TL-` mới vào `docs/test-log.md`.

---

## 0. Mục đích, phạm vi và cách đọc

**Mục đích.** Tài liệu này là một danh mục thống nhất các ca kiểm cho toàn bộ KNJSC: KN ERP (cổng 8020, `app/knjsc/urls.py`), KN CRM (cổng 8021, `app/knjsc/urls_bangtinh.py`), tác vụ nền Celery, hạ tầng Docker/nginx/VPS, dữ liệu và công cụ kiểm thử. Mỗi ca ghi rõ kiểm cái gì, ai kiểm, chạy ở đâu, mức ưu tiên, và dẫn tới mã AC/ADR/TL hoặc tệp mã cụ thể.

**Phạm vi.**
- Có: 12 app trong `app/` cùng `knjsc`, 19 tệp JS và 97 template, bộ kiểm thử (`app/<app>/tests/`, `app/tests/`, `app/tests/e2e/`), script `scripts/kiem-thu-*` (53 tệp), CI (`.github/workflows/ci.yml`), triển khai (`deploy/`, `deploy/production/`), launcher Windows (`KN JSC.bat`, `scripts/cap-nhat-local.*`), sao lưu và phục hồi (`scripts/backup.sh`, `scripts/restore.sh`), sổ tay vận hành (`docs/05-huong-dan-va-van-hanh.md` phần B), hướng dẫn sử dụng (docs/05 phần A, rà với ADR ở 1.5).
- Có, nhưng chỉ ở mức công cụ đo: `deploy/optimization-nginx.conf` và `deploy/optimization-proxy.conf`. Đây là proxy nginx cho bài đo tối ưu. Đầu tệp proxy ghi "Proxy chỉ cho thử nghiệm localhost; không dùng cấu hình này cho Internet". Không compose nào trong kho tham chiếu hai tệp này, và cách gắn chúng khi đo chưa xác minh. Chúng không phải cấu hình production (production là `deploy/production/nginx.conf.template`), nên không có ca an ninh prod cho chúng. Ca liên quan chỉ là: đo lại phải dùng đúng cấu hình đã ghi trong biên bản `docs/kiem-chung-*`.
- Có, làm dữ liệu đối chiếu chứ không phải đối tượng kiểm: `docs/verification/*.json` (10 tệp, do script ghi ra, ví dụ `scripts/bao-cao-optimization-final.cjs`, `scripts/grid-flags-check/report.py`) và `docs/evidence/` (`account-management-20260925.json`, `payment-20260912/`). Đây là bằng chứng đo mà các biên bản `docs/kiem-chung-*.md` dẫn tới. Ca hồi quy hiệu năng so với các số này, không sửa tay các số này.
- Không có:
  - `prototype/`: HTML/CSS tĩnh, chưa nối DB, không phải Django (theo `prototype/README.md`). Cố ý loại khỏi phạm vi.
  - Nội dung `compose.vps.yml`, vì tệp này không nằm trong kho (chưa xác minh).
  - Dữ liệu thật trên VPS, vì không đọc và không chép.

### 0.1 Bốn trục phân loại

Mỗi ca kiểm có một vị trí trên bốn trục:

| Trục | Giá trị | Ý nghĩa trong dự án | Ví dụ có thật |
|---|---|---|---|
| **Tầng** | Đơn vị | Một hàm hoặc lớp, không qua HTTP | `app/tests/test_ti_gia.py` (env_rates, ADR-031) |
| | Tích hợp | Nhiều thành phần chạy cùng nhau: DB, Celery eager, middleware, lệnh `manage.py` | `app/crm/tests/test_hang_doi_chet.py` (AC-10.13) |
| | Hệ thống | Cả ứng dụng qua HTTP hoặc trình duyệt, trên hai urlconf, cấu hình gần với thật | `app/tests/test_khoi.py`, `app/tests/e2e/test_mat_mang_e2e.py` (AC-10.12) |
| | Nghiệm thu | Đối chiếu với AC hoặc kịch bản theo vai, do người làm hoặc diễn tập | docs/07 mục 3.3 (VĐ), diễn tập `docs/kiem-chung-dien-tap-phat-hanh-staging-20261008.md`, docs/04 mục 17–18 |
| **Vị trí** | Backend | View, service, model, Custom Manager `in_scope`, tác vụ Celery | `app/core/tests/test_scope.py` |
| | Frontend | `app/static/js/*.js` (lưới `master-grid.js`), template HTMX | `scripts/kiem-thu-master-queue-unit.cjs`, `app/tests/e2e/*` |
| | Hạ tầng | Settings, Docker, entrypoint, nginx, CI, launcher, sao lưu | `app/core/tests/test_kiem_cau_hinh.py` (AC-1.11) |
| | Dữ liệu | Migration, bảng động `van_don`, toàn vẹn, lệnh nạp và xoá | `app/core/tests/test_chuyen_doi.py`, `app/crm/tests/test_ma_don_khong_trung.py` (TL-76) |
| **Cách chạy** | Tự động | pytest hoặc script tự khẳng định, máy tự kết luận đạt hay hỏng | Bài có trong CI |
| | Bán tự động | Công cụ chạy, người đọc kết quả và kết luận | `scripts/kiem-tai-kn-crm.sh`, `scripts/gom-p95-vps.py`, `scripts/kiem-thu-*.cjs` |
| | Thủ công | Người thao tác trên giao diện hoặc máy chủ | Chặng 2, AC thủ công (13 mã), diễn tập phục hồi AC-10.5, docs/04 mục 17 |
| **Mục tiêu** | Chức năng | Làm đúng nghiệp vụ và phân quyền (FR, BR, AC) | `app/tests/test_ma_tran_phan_quyen.py` (AC-3.1) |
| | Phi chức năng | Hiệu năng, bảo mật, độ tin cậy, khả dụng, vận hành, tiếng Việt (NFR) | `app/tests/test_hieu_nang.py` (NFR-1, AC-7.1) |

**Ví dụ phân loại một bài có thật.** `app/crm/tests/test_hang_doi_chet.py` kiểm rằng khi Redis chết thì tác vụ chuyển sang Thất bại, có lời báo tiếng Việt và không ra lỗi 500 (AC-10.13).

| Tầng | Vị trí | Cách chạy | Mục tiêu |
|---|---|---|---|
| Tích hợp (mock `apply_async`, `CELERY_TASK_ALWAYS_EAGER=False`) | Backend + hạ tầng (hàng đợi) | Tự động, chạy trong job CI `kiem-thu` | Phi chức năng (độ tin cậy) |

### 0.2 Quan hệ với các tài liệu sẵn có

| Tài liệu | Là gì | Hiện trạng đã đối chiếu | Tài liệu này bổ sung gì |
|---|---|---|---|
| `docs/04-tieu-chi-nghiem-thu.md` | **AC (tiêu chí nghiệm thu)**: mỗi dòng `\| AC-x.y \| … \|` là một điều kiện kiểm được. Cột cuối ghi "Thủ công" hoặc để trống (để trống nghĩa là Tự động). `app/tests/test_truy_vet.py` đối chiếu từng AC Tự động với docstring `"""AC-x.y` của bài kiểm. Mục 17 liệt kê 7 việc kiểm thủ công trước bàn giao. Mục 18 nêu 7 điều kiện coi là xong phase 1 | 390 dòng AC, 6 dòng bị gạch (AC-1.7, 11.37, 11.39, 18.9, 42.1, 42.2). Còn 384 dòng: 371 Tự động, 13 Thủ công. Ma trận mục 3 **lệch** với `app/tests/test_ma_tran_phan_quyen.py` ở 2/50 ô (dòng 120, 122; commit 5e710ed). Mục 17–18 chưa được ánh xạ vào chặng nào | Ca cho những phần AC không phủ: vận hành, launcher, sao lưu thật, cấu hình prod. Chỉ ra những AC bị "đếm là có bài" dù bài luôn bị bỏ qua (AC-20.6). Ánh xạ mục 17–18 ở 1.5 |
| `docs/05-huong-dan-va-van-hanh.md` | Phần A: hướng dẫn sử dụng theo màn hình (A1–A13). Phần B: sổ tay vận hành (B1 người chịu trách nhiệm, B3 việc hằng ngày, B4 thử phục hồi hằng quý, B5 khi không mở được, B6 cập nhật, B7 sự cố, B8 sao lưu, B9 bàn giao, B10 `storage/`) | B1 vẫn ghi "(điền tên)" ở cả ba dòng. B6 phần "Máy chủ thật" chỉ có 7 bước chung, không dẫn tới `deploy/production/README.md`. B8 ghi mã hoá bản sao lưu "Chưa có trong hệ thống", và `storage/tai-lieu/` không nằm trong `pg_dump` (K30). Phần A **lệch ADR**: dòng 157, tiêu đề A4 ghi "Bảng dữ liệu — dành cho Marketing và Vận đơn", trong khi theo AC-44.3 (ADR-045) Staff/Leader không thấy mục Bảng dữ liệu ERP và bị chặn. Dòng 315, tiêu đề A8 ghi "lưới kiểu Excel cho mọi bảng", còn dòng 337 ghi "Bảng tính: Bộ phận ▸ Quý ▸ Tháng ▸ bảng". Cả hai trái ADR-040 (CRM chỉ phục vụ bảng vận đơn). Phần A còn lại chưa rà với ADR-044 (chưa xác minh) | Ca rà hướng dẫn sử dụng (A4, A8) và ca kiểm runbook (thử phục hồi theo B4/B8, kiểm bàn giao theo B9) ở 1.5. Đây là bản bàn giao mà điều kiện 7 của docs/04 mục 18 yêu cầu |
| `docs/06-ke-hoach-kiem-thu.md` | Chín tầng kiểm thử: đơn vị, migration, khói, chức năng, ma trận, hộp trắng, giao diện, e2e, hiệu năng. Kèm bộ đếm AC | Ghi 348/371 có bài, 23 hoãn (khớp `HOAN` trong `test_truy_vet.py`). Đã cũ ở các chỗ: "không có CI", "pytest mặc định bỏ cham", "hai xfail", AC-10.3 "Chưa làm — K9", bảng thủ công thiếu AC-10.8, văn xuôi ghi "24 tiêu chí" (thực tế 23) | Gắn mỗi ca vào bốn trục ở 0.1 và vào chặng (mục 1). Thêm P0/P1/P2 và góc nhìn |
| `docs/07-kich-ban-nghiem-thu.md` | Kịch bản bấm tay theo vai: 3.1 Sale, 3.2 MKT, 3.3 VĐ, 3.4 Quản trị, 4 Vận hành | Lệch ADR-040 ở lưới MKT/Sale trong CRM và cây Quý ▸ Tháng. Lệch AC-11.37 (dòng trống cuối lưới) và AC-11.21 (chuột phải xoá hàng; nay chuột phải mở Lịch sử ô, `master-grid.js:1228`). Thiếu kịch bản cho CEO (ADR-044), Kế toán (ADR-038), CSKH (AC-33.6), ADR-049, ADR-050 | Ca Người dùng thay cho các bước lỗi thời. Ghi rõ vai nào chưa có tài khoản mẫu |
| `docs/test-log.md` | Sổ lỗi TL-01 → TL-89 | Trạng thái nhiều mục đã cũ (ví dụ TL-33, TL-35 vẫn ghi "Mới") | Mỗi ca hồi quy dẫn mã TL. Ca ở trạng thái "đỏ trên mã hiện tại" được đánh dấu |
| `docs/quyet-dinh/` (52 tệp: 51 tệp ADR đánh số 001–050, trong đó 022 có hai tệp là `022-ban-dieu-hanh-kn-crm.md` và `022-bao-cao-hoat-dong-erp.md`, cộng `README.md`), `docs/kiem-chung-*.md` | Quyết định thiết kế; biên bản đo và phát hành | Là nguồn sự thật khi docs/04, docs/05 hoặc docs/07 mâu thuẫn. Khi dẫn "ADR-022" phải ghi rõ tệp nào | Dẫn chiếu, không chép lại nội dung |

### 0.3 Quy ước

| Ký hiệu | Nghĩa |
|---|---|
| ✅ | Có bài tự động chạy trong CI và đạt. Bài thật sự chạy, không bị bỏ qua |
| ⚠️ | Rơi vào một trong các trường hợp: chỉ phủ một phần; bài chỉ chạy khi có biến môi trường hay Chromium (nên trong CI có thể bị bỏ qua); chỉ có kiểm tay hay diễn tập; dữ kiện còn "chưa xác minh" |
| ❌ | Chưa có bài hay quy trình nào, hoặc có lỗi đã xác nhận mà chưa sửa (bài mới viết sẽ đỏ trên mã hiện tại) |
| **P0** | Chặn phát hành. Gồm: mất hoặc hỏng dữ liệu; lộ quyền (sai `in_scope`, hở khoá đăng nhập); cấu hình prod sai về an ninh; lặp lại sự cố đã từng xảy ra (06.09.2026, TL-23, TL-80, TL-81). Phải có trước lượt phát hành VPS kế tiếp |
| **P1** | Sai nghiệp vụ hoặc vận hành nhưng có cách lách; NFR chưa đạt; tài liệu kiểm thử sai khiến người kiểm kiểm nhầm chỗ. Làm trong chu kỳ kế tiếp |
| **P2** | Bảo trì bộ kiểm, đo lường, dọn gọn. Làm khi có thời gian |
| **Người dùng** | Ca viết theo thao tác của một vai thật (sale.staff, vd.staff, quantri…): họ thấy gì và mong đợi gì |
| **QA** | Ca viết từ góc người kiểm thử: khẳng định nội bộ (DB, AuditLog, header, log, mã thoát), đột biến, kiểm tĩnh, cấu hình |
| Tự động / Bán tự động / Thủ công | Như trục "Cách chạy" ở 0.1 |
| **Chặng N** | Đánh số theo CLAUDE.md (bốn chặng, xem 1.1). Bước con ghi 1a, 1b, 4a, 4b |

**Cách đọc cho chủ dự án.** Đọc mục 1 trước để biết mỗi chặng phải chạy gì, rồi lọc các ca **P0**. Ca có ❌ kèm ghi chú "đỏ trên mã hiện tại" nghĩa là phải sửa mã, và sửa mã thì đi đúng quy trình nhánh việc. Muốn biết còn bao xa mới xong phase 1 thì đọc 1.5.

**Cách đọc cho agent.** Mỗi ca có đủ đường dẫn tệp, tên hàm và mã AC để viết bài. Bài mới phải đỏ được trước khi sửa (docs/06, "Một bài kiểm thử phải đỏ được"), và docstring phải bắt đầu bằng `"""AC-x.y`.

---

## 9. Lộ trình ưu tiên

**Quy ước**
- **Công sức** là ước lượng thô. Một "phiên" là một phiên agent, khoảng 3–4 giờ, gồm viết bài kiểm và chạy xanh/đỏ. Phần sửa mã khi bài đỏ chưa tính vào.
- **Thứ tự** trong mỗi mức sắp theo rủi ro chia công sức: việc rẻ mà rủi ro cao đứng trước.
- **Cách chạy**: TĐ = tự động trong CI; BTĐ = bán tự động (bài có sẵn nhưng phải bật biến môi trường, chạy tay script hoặc chạy trên VPS); TC = thủ công.
- **Góc nhìn**: ND = người dùng; QA = kiểm thử viên.
- Mỗi lỗi còn sống, khi sửa, phải kèm một bài kiểm chiều sai. Docs/test-log.md đã đặt quy tắc này.
- **Tình trạng bài hồi quy theo mã TL.** Grep mã TL trong `app/` (cả docstring lẫn chú thích) chỉ thấy 20 mã: TL-36, 41, 43, 46, 47, 49, 53, 58, 60, 63, 67, 69, 70, 71, 74, 75, 76, 77, 78, 89. Trong đó TL-63 nằm ở `reports/tests/test_bo_cuc_bao_cao_e2e.py`, TL-71 nằm ở `tests/e2e/test_ghi_chu_tu_gian_dong.py`. Mục 8.6 ghi thêm TL-02, 04, 07, 11, 16, 17, 48, 51 đã có bài nhưng bài không mang mã TL; phần này chưa xác minh lại từng bài đó. Trừ các mục trên, còn **34 mục TL chưa có bài hồi quy**: TL-01, 03, 05, 06, 08, 09, 10, 12, 13, 14, TL-18…TL-33, TL-42, TL-80…TL-85, TL-88. TL-88 không xuất hiện ở `app/` lẫn `scripts/`. Nó chỉ có trong `docs/test-log.md`, `docs/backlog.md` và `docs/kiem-chung-staging-len-main-20261012.md`. Có thêm hai mục mới có bài một phần: TL-11 (phần ERP còn thiếu, xem P1-12) và TL-36 (`crm/tests/test_khoa_trung_sdt.py` đã khoá phần so trùng; phần lọc, tô màu, phạm vi còn thiếu, xem P2-3). Bảng dưới gom những mục còn sống.

### 9.0 Bước chuẩn bị (làm trước P0, vì nhiều việc P0 cần)

| # | Việc | Phân hệ | Loại | Góc nhìn / Cách chạy | Công sức | Vì sao | Phụ thuộc |
|---|---|---|---|---|---|---|---|
| 0.1 | Thêm vào `app/conftest.py` (fixture `nguoi_dung`) các vai `ceo`, `cskh`, `leader_vd`, `manager_vd`. Thêm bộ phận `cskh` vào fixture `departments`. Sửa docstring "Chín vai trò" | Hạ tầng kiểm thử | Fixture | QA / TĐ | 2 giờ | Hiện CEO được dựng riêng trong 10 tệp, `leader_vd`/`manager_vd` trong 6 tệp (như mục 1.2). `assignment_service` có `care: ('sale','cskh')` nhưng fixture lại thiếu bộ phận này | Không |
| 0.2 | Thêm tài khoản mẫu Kế toán, CSKH, Leader VĐ, CEO vào `core/management/commands/du_lieu_mau.py` (dòng 48–60) và `docs/tai-khoan-mau.md` | Dữ liệu mẫu | Hỗ trợ kiểm tay | ND / TC | 2 giờ | Kiểm tay theo vai đang bỏ sót đúng những vai có luật riêng (AC-33.6, AC-21.17, ADR-038, ADR-044) | Không |
| 0.3 | **Chủ dự án chốt các quyết định nghiệp vụ** liệt kê ở 9.5 | Nhiều phân hệ | Quyết định | — | 1 buổi họp | Chưa chốt TL-03, vòng đời bảng CRM, phạm vi dòng Sale, đổi thị trường… thì chưa viết được bài kiểm đúng | Chủ dự án |

### 9.1 P0: làm ngay (sai tiền, mất dữ liệu, lộ quyền, lỗi S1/S2 còn sống)

| # | Việc | Phân hệ | Loại | Góc nhìn / Cách chạy | Công sức | Vì sao | Phụ thuộc |
|---|---|---|---|---|---|---|---|
| P0-1 | **TL-01 (S1)**: viết bài HTTP hai chiều, POST thẳng vào `/bang/<mã>/cap-quyen/` và `thu-quyen/<pk>/` ở cả 8020 lẫn 8021. Vai kiểm: Manager MKT được cấp Xem, Manager Kế toán (ADR-025), Manager Sale có dòng vận đơn (ADR-033). Kỳ vọng 403, có nhật ký DENIED, không Grant nào bị tạo hay xoá. Gộp luôn phần quản lý biểu mẫu nhờ quyền FILL (`bieu_mau_sua`, `bieu_mau_bo_truong`, `bieu_mau_cap_quyen`, `bieu_mau_thu_quyen`) | forms_builder, crm | Phân quyền HTTP | QA / TĐ | 1 phiên | Lộ toàn bộ dòng vận đơn và cho sửa. Trong `forms_builder/views.py`, `bang_cap_quyen` (486–507) và `bang_thu_quyen` (510–520) không gọi `can_manage_columns`. `test_ma_tran_quyen_hai_dich_vu.py` đang để hai URL này trong `CHUNG_KHONG_GET` | 0.1 |
| P0-2 | Bài **quét resolver mọi đường POST** của `knjsc.urls` và `knjsc.urls_bangtinh`, chạy với vai `ceo` và `staff_kt`: không được ra 2xx/302 thành công, không được đổi DB. Bài cũng phải bắt được 403 thiếu DENIED (`nhap_tep` và `cap_quyen` gọi `assert_business_write` trước, mà hàm này không ghi nhật ký) | Toàn hệ thống | Phân quyền (quét URL) | QA / TĐ | 1 phiên | `RANK_LEVEL` CEO=35 > MANAGER=30, nên `assert_rank` cho CEO qua ở tầng view. Hiện chỉ có tầng dịch vụ chặn (ADR-044). Endpoint mới quên chặn sẽ không bị bài nào bắt | 0.1 |
| P0-3 | **TL-03 (S1) và họ số**: bảng chân lý CSV viết tay cho `parse_money`; bài khứ hồi "đọc lại `str(d)` từ DB phải ra đúng d"; POST `luu-json` với '0.125' (dán, hoàn tác); nhánh INTEGER của `parse_value` với '1,5'; `_chuyen_kieu` MONEY→INTEGER và DECIMAL→MONEY; Lên đơn, Tóm tắt, Chi tiết với `unit_price='0.125'`; nhập CSV '0.125' và '12,345' | core, forms_builder, orders, reports, crm | Đơn vị, tích hợp, e2e lưới | QA / TĐ | 2 phiên | Tiền bị nhân nghìn âm thầm. `core/money.py` dòng 86–90; `record_service.py` 97–115; `table_service._chuyen_kieu` 157–189. Các bài hiện có lại đang khoá đúng luật gây lỗi | 0.3 (luật đọc chuỗi máy, ngoại tệ). Muốn kiểm thử thuộc tính bằng `hypothesis` thì phải xin duyệt (quy tắc 8). Không muốn thêm thư viện thì tự viết vòng lặp `random` + `Decimal` |
| P0-4 | Báo cáo tổng hợp **kiểu cũ cộng lẫn loại tiền**: bài cho `summary_service.build_context`, `build_export`, `_compare` và `dashboard_service._marketing` với dữ liệu CAD+USD. Thêm bài cho trang mặc định không có `?nguon` (`pick_table` lấy `tables[0]`) | reports, dashboard | Tích hợp + HTTP | ND+QA / TĐ | 0,5 phiên | Trái BR-8 và ADR-046. Lỗi lộ ra khi `configure_erp_reports` hỏng, mà `deploy/entrypoint.sh` dòng 49 chỉ echo cảnh báo | Không |
| P0-5 | **Tiền nhiều hơn 2 chữ số lẻ**: JSON lệch `val_revenue` numeric(18,2), làm `kiem_tra_du_lieu` báo lệch mãi và `--sua` không chữa được. Thêm bài cho nhánh "đơn đã bỏ, dòng còn sống" và đơn có `record=None` của `integrity_service.don_mo_coi` | forms_builder, orders | Tích hợp DB + lệnh | QA / TĐ | 0,5 phiên | Cổng phát hành (thoát mã 1) đỏ sai. Hai màn hiện hai số tiền khác nhau | 0.3 (có giới hạn số lẻ khi lưu hay không) |
| P0-6 | **Sửa báo cáo Sale đổi Thị trường** (`/bao-cao/<id>/sua/` và `?khung=1`): loại tiền tự đổi còn số giữ nguyên | reports | Tích hợp + HTTP | ND / TĐ | 2 giờ | 1.000.000 CAD thành 1.000.000 USD mà không có bước xác nhận (`amend` dòng 284, 56–63) | 0.3 |
| P0-7 | **TL-13 (S2)** và bỏ cột ở màn Cột: một bài parametrize "cùng một luật cho mọi đường vào" (`bang-tinh/<mã>/xoa-cot/` và `bang/<mã>/cot/<pk>/bo/`), áp cho cột chuẩn, cột EXTRA, `sl_*`, cột khoá, cột là vế của cột tính sẵn, cột đang nối biểu mẫu (ProtectedError). Kỳ vọng 400 kèm lời báo, không 500, cột còn nguyên | forms_builder, crm, orders | Tích hợp + HTTP | QA / TĐ | 0,5 phiên | Hiện ra 500. Bỏ được cột EXTRA và vế công thức, làm cột tính sẵn trống cả bảng (`views.bang_xoa_cot` 191–202 không gọi `removable_reason`) | Không |
| P0-8 | **`/quan-tri/login/` đi vòng qua khoá 5 lần sai**: bài HTTP gồm Admin sai mật khẩu 6 lần, Admin đang `locked_until` vẫn vào được, không có LOGIN/LOGIN_FAILED/LOGOUT. Sửa bài rỗng `client.get('/admin/')` ở `org/tests/test_account_management.py` dòng 312 | core, org | Bảo mật HTTP | QA / TĐ | 0,5 phiên | Dò mật khẩu Admin không giới hạn trên tên miền ERP công khai, không để lại dấu vết (FR-1.2, AC-1.9) | Không |
| P0-9 | **Admin cuối tự hạ cấp** qua `nhan_su_sua`; **trưởng nhóm chéo bộ phận** (`TeamForm` không lọc theo bộ phận); Manager không có bộ phận lại nhận danh sách rỗng thay vì bị từ chối (`SuaHoSoForm.clean`) | org | Dịch vụ + HTTP + phân quyền | QA / TĐ | 0,5 phiên | Mất quyền quản trị toàn hệ thống. Leader MKT đặt lại mật khẩu và xoá được Staff Sale | Không |
| P0-10 | **Kho chứng từ, các nhánh từ chối và replay**: CEO tạo/sửa; Sale, CSKH, MKT gọi `/chung-tu-thanh-toan/don/`; replay khác nội dung phải ra 409 và dọn tệp; ảnh không thuộc chứng từ; ảnh của chứng từ đã xoá; `?record` ngoài phạm vi; `file_path` trỏ ra ngoài thư mục. Gắn mã AC-26.1–26.6 vào docstring cấp hàm | orders, crm | Phân quyền + tích hợp | QA / TĐ | 1 phiên | Có thể lộ ảnh chứng từ tiền hoặc nhân bản chứng từ. `test_truy_vet.py` đang xếp AC-26 vào HOAN | 0.1 |
| P0-11 | **Vòng đời bảng ở CRM** (`xoa-bang/`, `khoi-phuc-bang/`, `bang-da-xoa/`) và bài AC-40.2 dạng **liệt kê resolver** mọi pattern `<slug:code>` của `urls_bangtinh`. Thêm lỗ hổng `_chi_bang_van_don` chạy `get_object_or_404` trước `login_required` (dò được mã bảng) | crm, forms_builder | Phân quyền HTTP | QA / TĐ | 0,5 phiên | Manager Sale/MKT xoá mềm được bảng thường của ERP qua 8021, trái ADR-040 và AC-40.2. `test_table_lifecycle.py::test_delete_and_restore_preserve_identity` đang khẳng định 302 | 0.3 (chốt có đóng cửa này không) |
| P0-12 | **Phạm vi dòng vận đơn của Leader/Manager Sale** so với `Order.in_scope`: ma trận Leader thấy dòng của Staff cùng team; Manager Sale bấm "Toàn bộ" so với "Tôi" | orders, crm, forms_builder | Phân quyền (ma trận) | ND+QA / TĐ | 0,5 phiên | Theo mã, nút Tôi/Toàn bộ của Manager Sale cho cùng một tập dòng, lệch ADR-033 (bổ sung 10.10) | 0.1, 0.3 |
| P0-13 | **TL-23 (S2)**: job RECOMPUTE/IMPORT/EXPORT và BACKUP kẹt ở RUNNING. Bài tạo job RUNNING có `updated_at` cũ, rồi `danh_dau_tac_vu_ket` phải đánh STALE/FAILED, ghi nhật ký, gửi thư, và không còn chặn xoá bảng. Kèm diễn tập `docker compose restart worker` (rồi `heavy`) giữa lúc đang tính lại 100k dòng | core, forms_builder | Tác vụ nền + diễn tập | QA / TĐ + TC | 0,5 phiên + 1 giờ diễn tập | Job treo vĩnh viễn, `lifecycle_service.delete` chặn xoá. `run_backup` chỉ bắt `BackupError`/`OSError` | Không |
| P0-14 | **TL-18 (S2), TL-02**: hết phiên khi còn nháp. HTTP: yêu cầu `HX-Request` ẩn danh ở 8021 phải nhận HX-Redirect hoặc 401, không được 302. E2E: đăng xuất ở tab khác rồi Lưu đơn, mở hộp lọc cột, Chi tiết; nháp lưới phải còn sau khi đăng nhập lại; `waybill-feedback.js` và `payments.js` không được báo "đã lưu" | core, crm, orders, JS | HTTP + e2e | ND / TĐ (Playwright, dấu `trinh_duyet`) | 1 phiên | Mất chữ vừa gõ (`master-grid.js` 858–861, 1291–1303). Báo lưu thành công giả (`waybill-feedback.js` không kiểm `redirected`) | Không |
| P0-15 | **Sao lưu, phục hồi thật**: round-trip pg_dump → pg_restore (dấu `cham`); nhánh `TimeoutExpired`/`FileNotFoundError` phải ghi audit "THẤT BẠI"; client 17 đọc server 16. **Tệp `storage/tai-lieu` không nằm trong bản sao lưu** (K30) | core, documents, vận hành | Tích hợp DB + diễn tập | QA / BTĐ + TC | 1 phiên + diễn tập trên VPS | Mất dữ liệu: bản sao lưu chưa phục hồi thử thì chưa được tính. AC-10.5 đang để Thủ công | Cần VPS. Cần runbook phục hồi cho production, vì `scripts/backup.sh` và `restore.sh` gọi dịch vụ `web` mà production không có |
| P0-16 | **Lệnh nguy hiểm với dữ liệu**: `do_hieu_nang` không có khoá DEBUG và ghi vào 5.000 dòng thật mới nhất; khoá DEBUG của `seed_perf` và `nap_du_lieu_van_don` chưa có bài | core, orders | Đơn vị lệnh quản trị | QA / TĐ | 2 giờ | Đè ghi chú của khách thật trên DB local đã nạp dữ liệu thật | Sửa mã, thêm khoá cho `do_hieu_nang` |
| P0-17 | `scripts/cap-nhat-local.bat` và `KN JSC.bat`: không kiểm `errorlevel` sau `migrate` và `tao_bang_van_don`, rồi vẫn ghi `storage/.kn-jsc-lan-truoc` | Vận hành local | Kiểm tĩnh + TC Windows | QA / TC | 2 giờ | Lặp lại sự cố 06.09.2026 (ProgrammingError, Bảng tính 404) | Máy Windows |

### 9.2 P1: làm sau P0 (rủi ro vừa, hoặc là nền cho CI tin cậy)

| # | Việc | Phân hệ | Loại | Góc nhìn / Cách chạy | Công sức | Vì sao | Phụ thuộc |
|---|---|---|---|---|---|---|---|
| P1-1 | CI **báo đỏ khi có bài `trinh_duyet` bị skip** (Chromium hỏng thì cả bộ bị bỏ qua) | Hạ tầng CI | CI | QA / TĐ | 1 giờ | 24 AC chỉ có bài trình duyệt (AC-6.14, 10.4, 10.12… 50.11). Hiện CI vẫn xanh khi các bài này bị bỏ qua | Không |
| P1-2 | Đưa 9 script Node đơn vị (`scripts/kiem-thu-*-unit.cjs`) vào CI. Thêm `assert(indexOf >= 0)` cho mọi mốc cắt mã | JS lưới | Đơn vị JS | QA / TĐ | 0,5 phiên | Hồi quy ở `master-working-copy.js`, `master-row-geometry.js`, `json`/`saveAll`/`poll` không ai biết. Phủ thêm AC-11.10 và AC-11.20 (hoàn tác 100 bước) | Cần duyệt việc thêm bước setup-node vào `ci.yml`. Script chỉ dùng `assert`, `fs`, `vm`, `crypto` nên không thêm thư viện mới |
| P1-3 | Nhật ký đăng nhập sai lưu chuỗi thô: mật khẩu gõ nhầm vào ô tên đăng nhập; `find_user('')` gán dòng LOGIN_FAILED cho người có email rỗng; tên có khoảng trắng | core | Đơn vị nhật ký | QA / TĐ | 2 giờ | Lộ mật khẩu trên `/nhat-ky/`, trái điều cấm 6. Gán nhầm thủ phạm | Không |
| P1-4 | Dữ liệu khách lọt vào log: nhật ký "Cập nhật khách" ghi SĐT/email (AC-18.3, AC-20.3); TL-82 (thiếu `log_min_error_statement=panic`, bài đọc tĩnh `deploy/production/compose.yml`); `mail_admins` gửi kèm dữ liệu POST (dùng `caplog` + `mail.outbox`) | orders, core, vận hành | Đơn vị + kiểm tĩnh cấu hình | QA / TĐ | 0,5 phiên | Quy tắc 6. Hiện không bài nào dùng `caplog` | TL-82: chưa xác minh `compose.vps.yml` (không có trong kho) |
| P1-5 | Khách được định danh theo SĐT đúng như gõ, còn "mua lại" lại dùng 9 số cuối: gõ '+1 (416) 555-0123' với khách đã có trong danh sách đen | orders | Tích hợp + HTTP | ND / TĐ | 2 giờ | Không báo danh sách đen, sinh Customer trùng | Không |
| P1-6 | Chiều từ chối của `len-don`, `tom-tat`, `kiem-khach` với Kế toán, CSKH, VĐ, CEO gắn bộ phận Sale | orders | Phân quyền HTTP | QA / TĐ | 2 giờ | `kiem-khach` trả tên, email, lý do danh sách đen. Chưa có bài chiều từ chối nào | 0.1 |
| P1-7 | Cấu hình phát hành: bài tiến trình con nạp `knjsc.settings.prod` (SSL redirect, cookie Secure, HSTS, X-Frame); `bangtinh` với `BANGTINH_GOC` mang giá trị lạ (TL-85); khẳng định `GRID_ONLY_TABLES = set()` và `ROOT_URLCONF` thật của 8021; thêm bước `check --deploy --fail-level WARNING` vào CI | knjsc, CI | Đơn vị cấu hình | QA / TĐ | 0,5 phiên | Xoá một cờ bảo mật mà CI vẫn xanh. Gõ sai biến thì CRM chạy với DEBUG=True | Không |
| P1-8 | `CELERY_BEAT_SCHEDULE` trỏ tới task có thật; `CELERY_TASK_ROUTES`/`crm_heavy` đúng; worker concurrency 1 bị đánh STALE nhầm khi chỉ đang bận (`JOB_STALE_MINUTES` so với `BACKUP_TIMEOUT_SECONDS` 30 phút) | core, vận hành | Đơn vị cấu hình Celery + diễn tập | QA / TĐ + TC | 0,5 phiên | Sao lưu và canh job kẹt lặng lẽ không chạy. Lượt nhập bị mất mà người dùng không biết vì sao | Không |
| P1-9 | Danh sách quyền hiện cả quyền đã thu, thu lại lần hai, cấp trùng (`grant_service` 318–327). Thu quyền và cấp cho team phải làm mất hiệu lực phiên (đăng nhập thật) | forms_builder | Tích hợp + phiên | QA / TĐ | 2 giờ | Manager không phân biệt được quyền nào còn hiệu lực. Có người bỏ `_mat_hieu_luc_phien` thì không bài nào đỏ | Đi sau P0-1 |
| P1-10 | `ColumnForm.clean_options` có mã chết sau `return ket_qua` (dòng 96–123): toán hạng không tồn tại, cột tính sẵn tham chiếu vòng | forms_builder | Đơn vị form | QA / TĐ | 2 giờ | Cột tính sẵn sai số, phụ thuộc thứ tự cột | Không |
| P1-11 | TL-26: một lô tính lại hỏng mà các lô sau vẫn commit. Cần bài `transactional_db` (ngoài atomic) để thật sự đi vào nhánh `ThreadPoolExecutor` | forms_builder | Tích hợp worker | QA / TĐ | 2 giờ | Bảng tính lại dở dang. Nhánh song song chưa từng được kiểm | Không |
| P1-12 | TL-11-ERP: Tổng quan ERP và `/bang/` đếm cả dòng đã xoá và dòng ngoài phạm vi (`record_count_scope`) | dashboard, forms_builder | Phân quyền + tích hợp | ND / TĐ | 2 giờ | Lộ số dòng ngoài phạm vi, hai số lệch nhau trên cùng trang | Không |
| P1-13 | `DailyReport.department/team` lệch dòng số liệu (Admin có hồ sơ khác bộ phận, quyền FILL chéo bộ phận) | reports | Phân quyền + tích hợp | QA / TĐ | 2 giờ | Leader bộ phận khác sửa được báo cáo MKT, còn Manager MKT thì không | 0.1 |
| P1-14 | Ngưỡng màu: `next=https://evil.test` và `//evil.test`; Leader POST; CEO POST; hai người lưu cùng lúc | reports | Bảo mật + phân quyền | QA / TĐ | 2 giờ | Chuyển hướng mở. Ghi đè dict mà không so phiên bản | Không |
| P1-15 | Gửi lại mã lần nộp của báo cáo đã bỏ ra 500 (`submit_current` dòng 82) | reports | Tích hợp HTTP | ND / TĐ | 1 giờ | NFR-6. Kịch bản: nộp, tự bỏ, bấm Back, nộp lại | Không |
| P1-16 | Lệnh `configure_erp_reports` và `configure_delivery_daily_report`: các nhánh lỗi (dòng 105, 131, 175; 24/29/33/38) và việc rollback cả ba nguồn | reports | Tích hợp lệnh | QA / TĐ | 2 giờ | Người vận hành kẹt lúc phát hành. Liên quan tới P0-4 | Không |
| P1-17 | Lệnh vận hành vỡ vì PROTECT: `seed_perf.delete_fake_records` khi dòng đã có `GridCellHistory` hoặc `PaymentDocument`; `xoa_bang_van_don_cu` khi còn đơn đã bỏ (`Order.objects` đã loại sẵn đơn xoá mềm) | core, orders | Lệnh quản trị | QA / TĐ | 2 giờ | Lệnh phát hành dừng giữa chừng | Không |
| P1-18 | Tài khoản: POST `/doi-mat-khau/` (xoá `must_change_password`, giữ phiên hiện tại, mật khẩu cũ sai, ghi nhật ký BR-5); khoá/mở qua `nhan_su_doi_trang_thai` (khoá tạm bị thành khoá hẳn, bộ lọc `bi-khoa`); sửa qua Django admin không ghi AuditLog; tạo superuser không có hồ sơ | core, org | HTTP + tích hợp admin | QA / TĐ | 1 phiên | Người mới kẹt trong vòng lặp đổi mật khẩu. Có cửa tạo Admin ngoài luồng | Không |
| P1-19 | `X-Forwarded-For` không phải IP làm việc ghi nhật ký ra 500 và cho giả IP (`core/audit.py _client_ip`) | core | Đơn vị + HTTP (fuzz header) | QA / TĐ | 1 giờ | Gặp ở Local và Staging khi truy cập thẳng 8020/8021. Production có nginx đè header | Không |
| P1-20 | Tệp tĩnh thiếu `?v=` (6 chỗ ở `crm/master_grid.html`, `payments.html`, `waybill_entry.html`): viết bài quét template | crm | Hồi quy cấu hình | QA / TĐ | 1 giờ | Cùng gốc với TL-80 và AC-10.11: trình duyệt giữ JS cũ sau phát hành | Không |
| P1-21 | Poll `moi-nhat/` mỗi 8 giây giữ phiên sống mãi (FR-1.3, AC-1.4): bài patch thời gian | core, crm | Phân quyền phiên | QA / TĐ | 2 giờ | Máy bỏ quên với tab lưới đang mở thì không bao giờ hết phiên | 0.3 (cần ADR: poll có tính là thao tác không) |
| P1-22 | Sửa bài cũ: `test_khoi` (bỏ chấp nhận 200 với vai không đủ quyền, dùng pk/code thật, thêm vai `ceo`/`staff_kt`); `test_truy_vet` (không tính bài luôn skip như AC-20.6, không tính docstring cấp module); bài thứ tự mặc định có giá trị trùng | Hạ tầng kiểm thử | Meta | QA / TĐ | 0,5 phiên | Chỉ số "348/371 AC có bài" đang phồng. Bài khói không bắt được view quên `in_scope` | 0.1 |
| P1-23 | Bài phụ thuộc ngày thật (23 tệp; TL-70 đã đỏ ngày 01.10): gom về một helper giả `timezone.now` bằng `monkeypatch`; thêm ca biên cuối tháng theo giờ Việt Nam (bảng xếp hạng `month_range`) | Hạ tầng, culture | Hồi quy thời gian | QA / TĐ | 0,5 phiên | Đỏ theo ngày, chặn gộp | `freezegun`/`time-machine` là thư viện mới, phải xin duyệt. Dùng `monkeypatch` thì không cần |
| P1-24 | Thưởng sao chạy lại khi hạng tháng trước đổi (`award_monthly_stars` get_or_create); đơn KRW làm bảng rỗng (nhánh `bao_nguoi_van_hanh` chưa có bài) | culture | Tích hợp | QA / TĐ | 2 giờ | Sổ sao chỉ ghi thêm nên ghi sai là không sửa được. Ở local, entrypoint chạy lệnh này mỗi lần bật máy | Không |
| P1-25 | Hiệu năng trên VPS theo đúng mốc AC-24.7/AC-27.8: 100k/300k dòng × 10/20 người, ấm 60 giây + đo 300 giây; nếu đạt thì chạy 300k/20 người/30 phút (đọc/lọc/lịch sử p95 ≤ 1 s, lưu ô ≤ 0,5 s, 2.000 ô ≤ 5 s), đo lại định kỳ. Kèm TL-83 (`kiem_tra_du_lieu` hết RAM ở 100k dòng, đo bằng tracemalloc dấu `cham`) và TL-33 (đo `du-lieu/` có lọc và `?trung=1` ở 50k dòng, thay cho trang khung) | crm, orders, vận hành | Hiệu năng | QA / BTĐ | 1 phiên + phiên VPS | Biên bản 16.09 vượt cả ba ngưỡng (5.043 / 2.341 / 3.868 ms). p95 sau phát hành chỉ có 7–52 mẫu. Mốc 20 người và bài 30 phút chưa từng chạy (AC-24.7, AC-27.8 đang ở HOAN) | Cần VPS. `locust` đã có trong `app/requirements-dev.txt`; kịch bản có sẵn ở `scripts/order-code-check/locust_mixed.py`, `scripts/crm-update-perf/endurance.ps1` (chưa xác minh còn khớp lưới hiện tại) |
| P1-26 | Diễn tập quay lui và tiến lại trên VPS; bỏ hoặc sửa `scripts/grid-flags-check/deploy.sh` (collectstatic không `--clear`, không migrate) | Vận hành | Diễn tập | QA / TC | 1 phiên VPS | TL-80/D1. Script cũ trái README | Cần VPS |
| P1-27 | Đưa vào CI: `pytest --cov` (pytest-cov đã có trong `requirements-dev.txt`), `docker build`, `docker compose config`, `nginx -t` với template | CI | CI | QA / TĐ | 0,5 phiên | Lỗi CRLF, entrypoint, nginx chỉ lộ ra lúc phát hành | Thay đổi `ci.yml` (cần duyệt). `pip-audit`/`npm audit` là công cụ mới, phải xin duyệt. Có đặt ngưỡng `--cov-fail-under` hay không thì chờ chủ dự án chốt `docs/04` mục 19 điều 2 (xem 9.5). Trước khi chốt, chỉ báo số bao phủ, không chặn gộp |
| P1-28 | Nhập lại cùng một tệp vào bảng thường có cột khoá (ADR-010) thì dòng bị nhân đôi | forms_builder | Chức năng | ND / TĐ | 2 giờ | Nhập lại sau lỗi mạng là nhân đôi doanh thu (`import_check_service.py` 13–15) | 0.3 (có mở kiểm trùng cho bảng thường không) |
| P1-29 | **Kiểm tay trên điện thoại và máy tính bảng thật** (cả hai loại máy), theo `docs/04` mục 17 điều 5 và AC-10.4 (Thủ công, NFR-7): đăng nhập, xem lưới vận đơn ở 8021, nộp báo cáo ngày, Lên đơn, Tổng quan; ghi tên máy, hệ điều hành, trình duyệt vào biên bản `docs/kiem-chung-*.md`. Làm cùng các điều còn lại của mục 17 (máy sạch, Excel thật, mở tệp xuất bằng Excel, phục hồi, ngắt mạng) | Toàn hệ thống | Thủ công giao diện | ND / TC | 1 buổi | `docs/04` mục 18 điều 3: chưa làm đủ mục 17 thì chưa coi là xong phase 1. Giả lập khung nhìn 390 px không thay được máy thật | Máy thật; 0.2 (tài khoản mẫu đủ vai) |

### 9.3 P2: làm khi còn thời gian (S3/S4, giao diện, trải nghiệm)

| # | Việc | Phân hệ | Loại | Góc nhìn / Cách chạy | Công sức | Vì sao | Phụ thuộc |
|---|---|---|---|---|---|---|---|
| P2-1 | TL-09: sắp xếp không ổn định ở Bảng dữ liệu ERP (`query.apply_sort` thiếu `pk`); TL-10: cột tiền trong JSON sắp theo chuỗi, lọc theo khoảng rơi về so bằng | forms_builder | Tích hợp truy vấn | ND / TĐ | 2 giờ | Lật trang thì sót hoặc lặp dòng; '999' xếp trên '1234.50' | Không |
| P2-2 | TL-25 (không gộp job tính lại); TL-12 (xoá 2.000 dòng, ngân sách truy vấn bằng `CaptureQueriesContext`); TL-32 (cột DATETIME mang nhãn Ngày vào `val_date`) | forms_builder, crm | Tích hợp + hiệu năng | QA / TĐ | 0,5 phiên | Worker bận vô ích; một request hơn 20k truy vấn (ước tính); hỏng cả lô | Không |
| P2-3 | TL-36: cột Trùng không lọc, không tô màu, không bấm xem được; số đếm bỏ qua phạm vi | crm | e2e + phân quyền | ND / TĐ | 0,5 phiên | Staff thấy số 2 mà không tìm được dòng kia | 0.3 |
| P2-4 | Dữ liệu NFD cũ khi lọc, tìm, đếm trong hộp lọc, Thống kê | crm, forms_builder | Chức năng | ND / TĐ | 2 giờ | Lọc ra 0 dòng; một giá trị tách thành hai mục | Không |
| P2-5 | Nhánh kiểm hợp lệ của `luu-json/` (payload là list, operation không phải UUID, ô trùng, kind lạ, JSON hỏng) | crm | HTTP biên | QA / TĐ | 2 giờ | 7 thông điệp lỗi chưa có bài nào khoá | Không |
| P2-6 | Admin xoá dòng trong lúc người khác đang sửa (403 sai bản chất, nháp ở dòng khác phải còn); nút Tôi/Toàn bộ và ẩn cột trên trình duyệt | crm, JS | Tích hợp + e2e | ND / TĐ | 0,5 phiên | Lời báo sai; `kiem-thu-solarpunk.cjs` dòng 38 đã ngược với luật mới (commit 3f32a92) | Không |
| P2-7 | Liên kết cụt: "Mọi tác vụ" ở CRM dẫn tới 403 (AC-44.4, ADR-045); bảng vận đơn `is_active=False` vẫn hiện ở sidebar và `/thu-muc/` (AC-40.6); Leader thấy "＋ Thêm mới…" rồi bị 403 | core, crm, forms_builder | Giao diện + phân quyền | ND / TĐ | 0,5 phiên | Người dùng kẹt; mỗi lần bấm sinh một dòng DENIED | Không |
| P2-8 | Màn biểu mẫu nổ 500 với tham số bẩn (`?truong=abc`, `?ve=` không phải slug, FieldDef đã commit trước đó); luồng HTTP quản lý biểu mẫu (sửa AC-8.1 đang gắn nhầm ở `test_man_hinh_bang.py:122`); biểu mẫu chặn xoá bảng vĩnh viễn | forms_builder | HTTP biên + chức năng | QA / TĐ | 0,5 phiên | 500 rồi gửi lại thì trùng mã | Đi sau P0-1 |
| P2-9 | Sản phẩm ngừng bán: Tóm tắt nhận nhưng Lưu báo "không tìm thấy"; đường thêm sản phẩm thứ hai không theo TL-72; JPY/KRW nhận phần lẻ (ADR-031) | orders | Tích hợp | ND / TĐ | 2 giờ | Hai bước cho hai kết luận khác nhau; số hiện lệch số lưu | 0.3 (JPY/KRW) |
| P2-10 | Số âm ở báo cáo ngày; hai người sửa cùng một báo cáo (2 luồng); Tổng quan với `?sale_nguon` ngoài phạm vi (bị nuốt thành log lỗi, không có DENIED) | reports, dashboard | Đồng thời + phân quyền | QA / TĐ | 0,5 phiên | CPO âm; mất dữ liệu khi có người bỏ `select_for_update` | 0.3 (số âm) |
| P2-11 | Nhóm Nội bộ: đổi trạng thái việc từ tab cũ; sửa đồng thời tài nguyên hoặc việc; CEO không có bộ phận không tạo được việc của mình; lọc Công việc theo người ngoài phạm vi trả rỗng; HTMX năm màn trên trình duyệt | taskboard, resources, feed, documents, culture | Tích hợp + e2e | ND / TĐ | 1 phiên | Mở lại việc đã Xong mà không ai biết; trái quy tắc "từ chối, không trả rỗng" | 0.1 |
| P2-12 | Nguồn bảng xếp hạng (chỉ đếm Order, lệch lưới vận đơn); làm tròn ROUND_HALF_UP theo nhóm; chạy bù thiệp sinh nhật và thưởng sao trên VPS | culture | Nghiệp vụ + vận hành | QA / TĐ + TC | 0,5 phiên | Sai hạng, sai người nhận sao | 0.3; cần VPS (chưa xác minh beat có chạy bù không) |
| P2-13 | Hai Admin tạo trùng mã nhân sự ra 500; nhập Excel giữ khoá độc quyền và tiến độ đứng ở 0% | org, forms_builder | Đồng thời + hiệu năng | QA / TĐ | 0,5 phiên | 500; trang tác vụ nhảy thẳng từ 0% lên 100% | Không |
| P2-14 | `RequestMetricsMiddleware` (log không chứa query string, lọc `X-Request-ID`, đếm thiếu với streaming); gunicorn timeout mặc định 30 s (công cụ đo dùng 60 s) | core, vận hành | Đơn vị middleware + hiệu năng | QA / TĐ | 2 giờ | SĐT có thể lọt vào log; một lần 502 kéo đứt 3 yêu cầu khác cùng tiến trình | Không |
| P2-15 | Trang lỗi không phải tiếng Việt: 413/502/504 của nginx, 400, CSRF (thiếu `400.html`, `403_csrf.html`); `server_tokens off`; healthcheck và giới hạn log json-file | vận hành | HTTP + TC qua proxy | ND / BTĐ | 0,5 phiên | Trái NFR-6; đầy đĩa VPS | Cần VPS cho phần nginx |
| P2-16 | Cache Redis "crm" chỉ có ở production: chạy Chặng 2 kèm `CRM_CACHE_URL`; kiểm `KN JSC.bat` dựng lại image khi `LAN_TRUOC` hỏng | vận hành | BTĐ / TC Windows | QA | 0,5 phiên | Đường làm mất hiệu lực cache (AC-10.26) chưa từng được kiểm tay | Máy Windows |
| P2-17 | Bật các bài trình duyệt đang phải bật biến môi trường (`SHARED_LOGIN_BROWSER`, `ACCOUNT_BROWSER`, `*_browser_server.py`) trong một job CI riêng hoặc chạy định kỳ | Hạ tầng CI | e2e | QA / BTĐ → TĐ | 0,5 phiên | Cookie domain, CSRF hai hostname, giao diện chứng từ AC-26.6 thực chất đang là kiểm tay | Bài cần thư mục `/evidence` |
| P2-18 | TL-71: theo dõi bài 18 (`test_do_hieu_nang_1000_dong_ghi_chu_400`), chạy lặp nhiều lần để tái hiện gốc lỗi | Hạ tầng CI | Độ ổn định | QA / BTĐ | Theo dõi | Bài treo là chặn gộp; chưa biết gốc lỗi | Không |
| P2-19 | TL-27 (phương pháp đo của `do_hieu_nang`), TL-29 (gunicorn local không phục vụ `/static/`), TL-30 (script kiểm tải đặt lại mật khẩu 12 tài khoản mẫu): thêm cảnh báo và bài khói | Công cụ | Rà công cụ | QA / TC | 2 giờ | Số đo sai; người kiểm bất ngờ bị đổi mật khẩu | Không |

### 9.4 Dọn tài liệu kiểm thử (làm cùng P1, vì người nghiệm thu đọc những tệp này)

| # | Việc | Tệp | Công sức | Vì sao |
|---|---|---|---|---|
| D-1 | Sửa ma trận phân quyền: ô "Bảng vận đơn × Staff VĐ" và "Nhập tệp vào bảng của Sale × Leader Sale" phải là **Từ chối**. Sửa docstring dẫn "Mục 13 điều 2" thành mục 18 điều 2. Sửa docstring `test_nhap_xuat.py::test_quyen_nhap_hai_chieu` | `docs/04-tieu-chi-nghiem-thu.md` dòng 120, 122; `app/tests/test_ma_tran_phan_quyen.py` | 1 giờ | Lệch thật 2/50 ô so với commit 5e710ed và ADR-045, mà đây là điều kiện nghiệm thu phase 1 |
| D-2 | Mục "Việc còn thiếu": dòng 1 ("Không có gì chạy kiểm thử tự động") sai vì đã có `.github/workflows/ci.yml`. Dòng 3 (`cham`) và dòng 5 ("Hai bài xfail") sai theo kiểm chứng. Dòng 142 ghi "24 tiêu chí", thực tế HOAN có 23. Bảng thủ công (184–197) thiếu AC-10.8. AC-10.3 ghi "Chưa làm — K9", thực tế đã có `core/tests/test_trang_loi.py`. Dòng 80 nhắc `bang-tinh.js`, dòng 373 nhắc `van_don_moi` | `docs/06-ke-hoach-kiem-thu.md` | 2 giờ | Người mới đọc sẽ tin là chưa có CI và bỏ sót AC-10.8 lúc bàn giao |
| D-3 | Viết lại kịch bản theo vai: bỏ "1.060 bài tự động" (dòng 31), cây Quý ▸ Tháng, Báo cáo Marketing trong CRM (trái ADR-040), dòng trống cuối lưới, menu chuột phải Xoá/Chèn (nay chuột phải mở Lịch sử ô, AC-21.13), Leader Nhập tệp và Manager Cấp quyền bảng Sale trong CRM, 404 "Chưa làm". **Thêm** bước cho CEO, Kế toán, CSKH, ADR-049, ADR-050 | `docs/07-kich-ban-nghiem-thu.md` | 0,5 phiên | Người kiểm theo vai sẽ ghi Hỏng sai chỗ |
| D-4 | Bảng "Lỗi theo thứ tự nghiêm trọng": cập nhật trạng thái theo kiểm chứng. TL-18 đã sửa phần chính (HX-Redirect), còn biến thể ở khung CRM. TL-02, TL-18, TL-23 mô tả `bang-tinh-o.js`/`bang-tinh.js`, hai tệp không còn trong `app/static/js`. Bỏ câu "đang xanh trên cả main lẫn PR21". Ghi thêm các mục mới chưa có mã TL: quyền FILL, Admin cuối, trưởng nhóm chéo bộ phận, vòng đời bảng CRM, `/quan-tri/login/` | `docs/test-log.md` (khoảng dòng 1190+); `docs/backlog-kanban.md` dòng 711–713 | 2 giờ | Sổ lỗi đang lệch mã; các TL S1/S2 vẫn ghi "Mới" |
| D-5 | TL-28, TL-31: sửa AC-11.26 (mốc tính trên cả bảng, khớp AC-10.21), AC-11.36 (`cell_html`, `bang_tinh_o`, ngân sách 25/8 truy vấn đã cũ; bài thật dùng 35/9). Sửa ADR-016 dòng 41–44. Sửa docstring `crm/views.py:bang_tinh_moi_nhat`, `test_moi_nhat_tra_moc_trong_pham_vi` và docstring `crm/services/catalog.py` | `docs/04`, `docs/quyet-dinh/016-…`, mã nguồn | 1 giờ | Tài liệu hứa một đằng, mã làm một nẻo |
| D-6 | Đánh dấu lỗi thời hoặc sửa `scripts/kiem-thu-solarpunk.cjs` (dòng 38). Ghi vào `docs/06` danh sách **53 tệp `scripts/kiem-thu-*`** chạy tay (51 `.cjs`, 1 `.mjs` là `kiem-thu-bao-cao-chi-ma.mjs`, 1 `.py` là `kiem-thu-erp-export.py`), kèm trạng thái còn đúng hay không. Sửa hai chú thích sai trong `.github/workflows/ci.yml`: "Hơn 70 script" (dòng 140) và "Tám tệp `*_browser*.py`" (dòng 174, bước "bài trình duyệt còn lại"). Thực tế có **9 tệp** ngoài `tests/e2e`: 7 ở `crm/tests/` (`test_market_currency_browser.py`, `test_statistics_labels_browser.py`, `test_order_hub_browser_server.py`, `test_payment_browser_server.py`, `test_feedback_browser_server.py`, `test_shared_browser_server.py`, `test_master_browser_server.py`), cộng `org/tests/test_account_browser_server.py` và `core/tests/test_shared_login_browser.py`. Không tính `tests/perf/optimization_align_browser_fixture.py`, vì đó là giá đỡ chứ không phải tệp `test_` | `scripts/`, `docs/06`, `.github/workflows/ci.yml` | 2 giờ | Bộ script tay sẽ đỏ hoặc gây hiểu nhầm. Con số 70 trong chú thích CI đang lan sang tài liệu, còn số 8 làm người đọc bỏ sót bài đăng nhập dùng chung |
| D-7 | Sau mỗi việc ở 9.6: gắn mã AC vào docstring cấp hàm và gỡ mã khỏi `HOAN`. `test_danh_sach_hoan_khong_chua_tieu_chi_da_lam` sẽ báo đỏ nếu quên gỡ. Mã nào chủ dự án chốt Bỏ (AC-11.21, có thể cả phần gõ địa chỉ của AC-11.25) thì đánh dấu Bỏ trong `docs/04`. Sửa luôn chú thích lỗi thời trong khối `HOAN` (dòng 73–77) ghi "`grep` trong `master-grid.js` không thấy `contextmenu`". Thực tế `master-grid.js` dòng 1228 và 1233 đang có listener `contextmenu`, dùng để mở Lịch sử ô (AC-21.13). Thứ không còn là menu Xoá/Chèn | `app/tests/test_truy_vet.py`, `docs/04` | 1 giờ | Giữ chỉ số truy vết trung thực. Chú thích sai dễ khiến người chốt AC-11.21 tưởng lưới không còn bắt chuột phải |

### 9.5 Quyết định chủ dự án cần chốt (chặn P0/P1)

| Câu hỏi | Chặn việc | Căn cứ |
|---|---|---|
| Luật đọc chuỗi tiền: '0.125' do máy gửi lại thì là 0,125 hay 125? Ngoại tệ USD/CAD có đọc theo luật riêng không? Có giới hạn số chữ số lẻ khi lưu không? | P0-3, P0-5 | TL-03, `core/money.py`, ADR-046 |
| Đổi Thị trường khi sửa báo cáo Sale: đổi luôn loại tiền, giữ loại tiền, hay đòi xác nhận? | P0-6 | `reports/services/daily_service.py` amend |
| CRM có được xoá/khôi phục bảng thường không (ADR-040)? | P0-11, H-27.4 | `crm/lifecycle_views.py`; `crm/tests/test_table_lifecycle.py` |
| Manager Sale thấy dòng vận đơn nào: theo đơn gốc hay theo dòng của mình? | P0-12 | ADR-033 bổ sung 10.10 |
| Poll 8 giây có tính là thao tác (gia hạn phiên) không? | P1-21 | FR-1.3, AC-1.4 |
| Bảng thường có kiểm trùng khi nhập theo cột khoá không? Báo cáo ngày có cho số âm không? JPY/KRW có cho phần lẻ khi lưu không? Cột Trùng đếm toàn bảng hay theo phạm vi? | P1-28, P2-3, P2-9, P2-10 | ADR-010, ADR-031 |
| Số lượng bài kiểm thử tự động tối thiểu là bao nhiêu? Có đặt ngưỡng tỉ lệ bao phủ không (nếu có thì bao nhiêu, và đỏ CI khi tụt)? | P1-27 (có bật `--cov-fail-under` không) | `docs/04` mục 19 điều 2 (dòng 433–439), vẫn ghi "chưa quyết định" |
| Cách nhóm theo thị trường của báo cáo tổng hợp lấy số liệu từ đâu (đang hoãn từ 03.09.2026, "hỏi lại sau")? | H-5.1 | AC-5.1, `docs/backlog.md` N9, Q36 |
| Menu chuột phải Xoá/Chèn (AC-11.21) và phần "gõ địa chỉ + Enter để nhảy ô" (AC-11.25): bỏ hay làm lại trong lưới mới? Lưu ý chuột phải hiện đã dùng để mở Lịch sử ô (AC-21.13) | H-11.21, H-11.25 | `test_truy_vet.py` HOAN; `master-grid.js` dòng 1228, 1233 |

### 9.6 Phân loại lại 23 mã đang hoãn (`HOAN` trong `app/tests/test_truy_vet.py`)

Mã việc **H-x.y** ứng với mã AC. Một bài chỉ được tính cho **một** mã, vì `MA_TRONG_DOCSTRING` chỉ đọc mã đứng ngay đầu docstring. Vì vậy, bài đã mang mã khác thì phải tách thành bài riêng.

| Mã việc | AC (docs/04) | Đã có gì | Việc cần làm | Góc nhìn / Cách chạy | Ưu tiên | Gắn với |
|---|---|---|---|---|---|---|
| H-5.1 | AC-5.1: bốn cách nhóm cho số đúng khi đối chiếu dữ liệu gốc (Tự động) | Ba cách nhóm chạy; tab thị trường chỉ có ghi chú, không có bảng số | Sau khi chốt N9: bài đối chiếu bốn cách nhóm với dữ liệu gốc, tách theo loại tiền (BR-8) | ND+QA / TĐ | P1 | 9.5; P0-4 |
| H-11.10 | AC-11.10: bàn phím lưới | `scripts/kiem-thu-master-ui.cjs` (Chrome thật, chạy tay) | Chuyển sang `app/tests/e2e` dấu `trinh_duyet`; phần thuần logic thì đưa vào P1-2 | ND / TĐ | P1 | P1-2 |
| H-11.20 | AC-11.20: hoàn tác/làm lại | `scripts/kiem-thu-shared-grid.cjs` (Ctrl+Z/Ctrl+Y) | Như trên | ND / TĐ | P1 | P1-2 |
| H-11.21 | AC-11.21: menu chuột phải | Menu Xoá/Chèn không còn trong lưới mới. Chuột phải hiện mở Lịch sử ô (`master-grid.js` dòng 1228, 1233, AC-21.13). Chú thích HOAN ghi "không thấy `contextmenu`" là lỗi thời | Chờ chốt; nếu Bỏ thì đánh dấu Bỏ trong `docs/04`. Sửa chú thích HOAN ngay (D-7) | — | P2 | 9.5, D-7 |
| H-11.25 | AC-11.25: ô địa chỉ hiện `A1`/`C3:F7`, gõ địa chỉ + Enter thì nhảy ô, thanh công thức, bấm đúp mở sửa | Theo HOAN: hiện A1:C3 đúng; phần gõ địa chỉ chưa rà lại | e2e Playwright: chọn ô đơn, chọn vùng, gõ `C3` + Enter, giá trị thô trên thanh công thức, Enter lưu rồi xuống dòng | ND / TĐ | P2 | 9.5 |
| H-24.2 | AC-24.2: mọi đường ghi phát revision trong cùng transaction; rollback thì không phát; giới hạn journal | Chưa có bài mang mã | Bài `transactional_db`: ghi rồi rollback, commit đảo thứ tự, ghi hàng loạt vượt 10k phiên bản/2k ID | QA / TĐ | P1 | P1-11 |
| H-24.3 | AC-24.3: sync ≤ 4k ID, chỉ trả dòng còn trong phạm vi; mất quyền hoặc bị khoá thì dữ liệu bị gỡ khỏi UI; cache nóng không vượt quyền | Chưa có bài mang mã | Phần phạm vi/cache: bài HTTP thu quyền rồi sync (**P0**, cùng nhóm lộ quyền với P0-1, P1-9). Phần gỡ khỏi UI: e2e | QA / TĐ | P0 (phạm vi), P1 (UI) | P0-1, P1-9 |
| H-24.4 | AC-24.4: v1/v2 cùng giữ CAS, nguyên tử, Undo, replay; biên nhận không nhân lịch sử, kể cả khi tắt cờ | Có bài biên nhận đồng thời ở `crm/tests/test_master_grid.py` (mang mã khác) | Bài riêng mang AC-24.4: replay hai lần, tắt cờ v2, so số `GridCellHistory` | QA / TĐ | P1 | P0-3 |
| H-24.5 | AC-24.5: sticky lệch ≤ 1 CSS px, UI p95 ≤ 100 ms với ≥ 100 mẫu, Chrome 1440/1280/390 | Chưa có | Đo trên Chrome thật, lưu số thô vào `docs/kiem-chung-*.md` | QA / BTĐ | P2 | P1-29 |
| H-24.7 | AC-24.7: tải 100k/300k × 10/20, bản cuối 300k/20/30 phút | Biên bản 300k/10 người 16.09 (vượt ngưỡng) | Chạy đủ ma trận trên VPS | QA / BTĐ | P1 | P1-25 |
| H-26.1…26.6 | AC-26.1–26.6: kho chứng từ thanh toán | Có bài trình duyệt AC-26.6 phải bật biến môi trường | Xem P0-10; AC-26.6 xem P2-17 | QA / TĐ, BTĐ | P0 | P0-10, P2-17 |
| H-27.1 | AC-27.1: mọi bảng động dùng chung shell/JSON/virtual grid; ERP chỉ đọc; Vận đơn mới giữ Lên đơn/Bill/phân công | Chưa có bài mang mã | Bài quét registry renderer + bài HTTP ERP chỉ đọc (ADR-014) | QA / TĐ | P2 | P0-2 |
| H-27.2 | AC-27.2: CAS hai đầu vào đồng thời; ô khoá hoặc sai kiểu làm cả lượt rollback, báo đúng vị trí | Chưa có bài mang mã | Bài hai luồng (`ThreadPoolExecutor`) + lượt dán có một ô sai kiểu | QA / TĐ | P1 | P0-3 |
| H-27.4 | AC-27.4: Manager đúng bộ phận/Admin xoá khi gõ đúng tên, khôi phục giữ ID; Staff/Leader/Grant bị từ chối; Vận đơn mới được bảo vệ | **Đã có** `crm/tests/test_table_lifecycle.py` (4 bài, chưa mang mã AC) | Gắn AC-27.4 vào docstring rồi gỡ khỏi HOAN, **sau khi** chốt ADR-040 ở 9.5: hiện bài khẳng định 302 qua `/bang-tinh/…/xoa-bang/`, trùng đúng lỗ P0-11 | QA / TĐ | P0 | P0-11, 9.5 |
| H-27.5 | AC-27.5: biểu mẫu/job đang ghi chặn xoá; khoá chia sẻ/độc quyền; bảng đã xoá thì ngừng đọc/ghi/tải tệp, tab nóng gỡ dữ liệu | `test_active_form_blocks_delete` phủ phần biểu mẫu | Thêm job RUNNING chặn xoá (P0-13), tải tệp của bảng đã xoá, hai luồng ghi + xoá | QA / TĐ | P1 | P0-13 |
| H-27.6 | AC-27.6: không còn renderer/asset ghi cũ; URL ghi cũ trả 409; nháp giữ theo mã cột khi đổi cấu trúc | **Đã có** `crm/tests/test_master_grid.py::test_legacy_writers_cannot_bypass_master_cas` (409 cho `o/<pk>/ghi_chu/` và `luu-o/`), nhưng docstring mang AC-21.3 | Tách bài riêng mang AC-27.6; thêm quét nguồn không còn asset ghi cũ (gộp P1-20); nháp theo mã cột giao cho e2e | QA / TĐ | P1 | P1-20 |
| H-27.7 | AC-27.7: 1440/1280/390, zoom Chrome thật 125%, p95 ≤ 100 ms, ≥ 100 mẫu, phân biệt IME mô phỏng/thật | Chưa có | Đo trên Chrome thật, gộp với H-24.5 | QA / BTĐ | P2 | H-24.5 |
| H-27.8 | AC-27.8: 100k/300k × 10/20, 60 s ấm + 300 s đo, rồi 300k/20/30 phút; không sai/mất/trùng/lộ dữ liệu | Chưa chạy đủ | Locust + SQL đối chiếu + số liệu tài nguyên trên VPS, gộp H-24.7 | QA / BTĐ | P1 | P1-25 |

---

## 10. Rủi ro còn lại và những gì cố ý không kiểm

### 10.1 Rủi ro còn lại sau khi làm hết P0 và P1

| Rủi ro | Vì sao vẫn còn | Giảm nhẹ đề xuất |
|---|---|---|
| Hiệu năng VPS ở 300k dòng / 10 người đã vượt ngưỡng (biên bản `docs/kiem-chung-300k-10-nguoi-20260916.md`); mốc 20 người và bài 30 phút chưa từng chạy | Kiểm thử chỉ đo được. Đạt ngưỡng hay không phụ thuộc tối ưu mã và cấu hình máy | Chạy đủ ma trận AC-24.7/AC-27.8 sau mỗi phát hành (P1-25), giữ biên bản p95 có từ 20 mẫu trở lên |
| Chưa biết gốc lỗi TL-71 (tab sập hoặc luồng chính kẹt khi cuộn 1.000 dòng) | Bài đã có hạn giờ và đồ chẩn đoán, nhưng chưa tái hiện được | Chờ lần treo sau để đọc ngăn xếp (P2-18) |
| Môi trường local khác production: không có nginx, không có cache Redis "crm", chạy `runserver`, dùng launcher Windows | Chặng 2 kiểm tay ở local không chạm được đường production | Diễn tập trên Staging/VPS. `deploy/production/compose.vps.yml` không có trong kho nên các cờ trên VPS (TL-82…) **chưa xác minh** |
| Phần lớn ca chịu lỗi worker và phục hồi vẫn là diễn tập tay trên VPS | Cần VPS, cần người vận hành, không đưa vào CI được | Diễn tập theo mỗi lần phát hành lớn; ghi biên bản vào `docs/kiem-chung-*.md` |
| Kiểm trên máy thật (P1-29) chỉ phủ vài mẫu điện thoại/máy tính bảng có sẵn | Không có phòng máy thử; mỗi lần kiểm là một buổi làm tay | Ghi rõ tên máy, hệ điều hành, trình duyệt trong biên bản; kiểm lại khi đổi bố cục lưới hoặc CSS |
| Bài đơn vị JS cắt mã `master-grid.js` bằng `indexOf`, chạy trong `vm` | Vẫn mong manh dù đã assert mốc cắt; không thay được e2e | Khi tái cấu trúc JS, tách hàm thành module để kiểm trực tiếp |
| Dữ liệu cũ ghi trước các bản vá (NFD trước TL-79, tiền đã bị nhân nghìn trước TL-03, MKT lẫn CAD trước AC-47.3) | Bài kiểm khoá hành vi mới, không sửa được dữ liệu đã ghi sai | Dùng lệnh rà `kiem_tra_du_lieu` hoặc viết lệnh rà riêng sau khi chốt luật; **chưa xác minh** quy mô dữ liệu sai trên VPS |
| Thư cảnh báo vận hành: `EMAIL_HOST/PORT/USER/PASSWORD` không đọc từ biến môi trường | Muốn gửi thư thật phải sửa mã (NFR-8); bài kiểm chỉ thấy được `mail.outbox` | Việc sửa mã riêng, ngoài kế hoạch kiểm thử |
| Sao lưu ra ngoài máy chủ (NFR-20) | Phụ thuộc hạ tầng và người vận hành, không phải mã | Chủ dự án chọn nơi lưu; diễn tập phục hồi theo P0-15 |
| Các quyết định ở 9.5 chưa chốt | Bài kiểm sẽ khoá hành vi hiện tại, có thể khoá luôn hành vi sai | Ghi ADR trước khi viết bài |
| 53 tệp `scripts/kiem-thu-*` (51 `.cjs`, 1 `.mjs`, 1 `.py`) vẫn chạy tay; chỉ 9 script đơn vị được đưa vào CI | Phần lớn cần app đang chạy, trình duyệt và dữ liệu mẫu | Chỉ giữ script còn đúng (D-6); dần chuyển sang `app/tests/e2e` |
| Bảng xếp hạng chỉ đọc Order, lệch với lưới vận đơn | Đây là câu hỏi nghiệp vụ, kiểm thử chỉ phát hiện được | Chủ dự án chốt nguồn số liệu (P2-12) |

### 10.2 Những gì cố ý không kiểm

| Không kiểm | Lý do |
|---|---|
| Kiểm thử chaos có hệ thống (ngắt mạng ngẫu nhiên, diệt container hàng loạt, đầy đĩa, lệch giờ) | Một VPS, một DB, không có HA. Chỉ diễn tập các sự cố đã gặp: restart worker/heavy (P0-13), mất mạng (`test_mat_mang_e2e.py`), đĩa đầy (`DiskFullMiddleware`, trang 507). Muốn làm có hệ thống thì cần công cụ mới (quy tắc 8) |
| Firefox và Safari **trên máy tính** | CI và Playwright chỉ dựng Chromium. Người dùng nội bộ dùng Chrome/Edge trên máy tính (Edge cũng là Chromium). **Không** thuộc mục này: điện thoại và máy tính bảng thật, với trình duyệt có sẵn trên máy, bắt buộc kiểm tay theo `docs/04` mục 17 điều 5, mục 18 điều 3 và AC-10.4 (P1-29). Giả lập 390 px chỉ bổ trợ, không thay thế |
| Quy mô **vượt** mốc AC-24.7/AC-27.8 (quá 300k dòng hoặc quá 20 người đồng thời, chạy dài hơn 30 phút); 100 người / 100k khách chỉ đo trên máy phát triển | Mốc nghiệm thu nằm trong AC-24.7 và AC-27.8 (đến 300k/20 người/30 phút). Phần trong mốc thì **phải** kiểm (H-24.7, H-27.8, P1-25), không thuộc mục này. Vượt mốc thì cần ADR mới kèm máy chủ lớn hơn |
| Kiểm bằng phần mềm đọc màn hình thật (NVDA, VoiceOver) và quét a11y tự động (axe) | docs/06 "Việc còn thiếu" dòng 4 ghi không có yêu cầu nào nêu; axe là thư viện mới (quy tắc 8). Các ca bàn phím, focus và `role=alert` ở mục 3.10 (GD-04 đến GD-08) **vẫn kiểm**, vì đó là hành vi giao diện bình thường (gắn với AC-11.10), không phải kiểm đọc màn hình |
| Kiểm thử xâm nhập từ bên ngoài, DDoS, quét lỗ hổng tự động bằng công cụ trả phí | Ngoài phạm vi đội. Chỉ kiểm các lỗ cụ thể đã thấy (P0-8, P1-14, P1-19). `pip-audit` chờ duyệt |
| Toàn bộ chức năng Django admin `/quan-tri/`, trừ xác thực, nhật ký và cờ quyền | Chỉ là công cụ cứu hộ của Admin, không có trong FR. Chỉ kiểm đăng nhập, khoá, audit và cửa tạo superuser (P0-8, P1-18) |
| Excel ngoài định dạng .xlsx/.csv mà openpyxl đọc được; LibreOffice; Excel bản địa hoá khác tiếng Việt và tiếng Anh | Chỉ kiểm các ca biên đã liệt kê ở bảng tiền (CSV '12,345', ô số so với ô chữ). Giới hạn 15 chữ số có nghĩa là giới hạn của Excel. Việc mở tệp xuất bằng Excel thật và nhập tệp Excel thật của công ty vẫn kiểm tay theo mục 17 điều 3–4 (P1-29) |
| Tỉ giá KRW và quy đổi tiền nói chung | Hệ thống cố ý không quy đổi (BR-8, ADR-046). `deploy/production/README.md` dòng 118–120 ghi KRW chưa có tỉ giá; chỉ kiểm nhánh lỗi (P1-24) |
| Múi giờ khác Asia/Ho_Chi_Minh; ngôn ngữ giao diện khác tiếng Việt | Công ty dùng một múi giờ, một ngôn ngữ. Chỉ kiểm biên tháng theo giờ Việt Nam (P1-23) |
| Nâng cấp PostgreSQL bản chính, chuyển máy chủ, chạy nhiều VPS | Chưa có kế hoạch. Chỉ kiểm độ tương thích của pg_dump 17 với server 16 trong round-trip (P0-15) |
| Tự động hoá launcher Windows (`KN JSC.bat`, `cap-nhat-local.bat`) | Không có runner Windows trong CI. Kiểm tĩnh và kiểm tay theo P0-17, P2-16 |
| Gửi thư thật qua SMTP | Chưa cấu hình được qua biến môi trường (xem 10.1). Chỉ kiểm `mail.outbox` |

### Critical Files for Implementation
- /home/user/KNJSC/app/tests/test_truy_vet.py
- /home/user/KNJSC/.github/workflows/ci.yml
- /home/user/KNJSC/app/conftest.py
- /home/user/KNJSC/docs/04-tieu-chi-nghiem-thu.md
- /home/user/KNJSC/app/static/js/master-grid.js
