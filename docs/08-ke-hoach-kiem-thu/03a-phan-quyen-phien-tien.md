> Phần của [Kế hoạch kiểm thử toàn diện KNJSC](../08-ke-hoach-kiem-thu-toan-dien.md) — mục lục, lộ trình P0/P1/P2 và rủi ro còn lại nằm ở tệp đó.

## 3. Bộ kiểm thử xuyên suốt

Các bộ dưới đây cắt ngang nhiều phân hệ; mỗi bộ chạy được độc lập.

---

### 3.1 Phân quyền: ma trận đường dẫn × vai

#### 3.1.1 Số liệu tổng

| Dịch vụ | Tệp URLconf | Số đường | Có kiểm chiều cho phép | Có kiểm chiều từ chối (theo vai/phạm vi) | Từ chối chỉ một phần | Từ chối không có bài |
|---|---|---|---|---|---|---|
| KN ERP (8020) | `app/knjsc/urls.py` | 85 (84 đường có tên + cây `/quan-tri/`) | 70/85 | 56/85 | 27 | 2 |
| KN CRM (8021) | `app/knjsc/urls_bangtinh.py` (12 riêng + `core.urls` 9 + `crm.urls` 48) | 69 mục, 68 đường khớp được (mục `bang_tinh` bị `tong_quan` che) | 61/69 (4 chỉ kiểm ở ERP, 4 không có bài) | 47/69 | 19 | 3 |

Cách chấm:
- **"Một phần"**: bài duy nhất là chưa đăng nhập → 302 (`app/tests/test_khoi.py::test_chua_dang_nhap_thi_bi_chuyen_ve_trang_dang_nhap`), hoặc chỉ 404 vì dữ liệu đã gỡ, hoặc chỉ kiểm cờ tắt, hoặc chỉ kiểm ở URLconf bên kia.
- `test_khoi::test_khong_duong_dan_nao_no` nhận cả {200,302,403,404,405} nên **không** được tính là bài từ chối.
- `test_khoi` bỏ qua `dang_nhap`, `dang_xuat`, `doi_mat_khau`, `/quan-tri/`. Nó cũng bỏ các cặp (tên, path) trùng ERP khỏi danh sách CRM, nên 9 đường `/bang/...` và 9 đường core không có bài khói nào dưới URLconf CRM.
- `scripts/kiem-thu-*.cjs` và `app/tests/e2e/` không được tính.

Bài làm bằng chứng chính:
- `app/tests/test_ma_tran_phan_quyen.py`: 10 dòng × 5 vai. Ở CRM chỉ có 1 đường là `/bang-tinh/van_don/`.
- `app/core/tests/test_ma_tran_quyen_hai_dich_vu.py` (AC-1.12): 8 vai × 8 đường chung. Có bài canh `test_duong_dan_chung_deu_da_ra_quyen`.
- `app/core/tests/test_quyen_menu_erp.py`, `app/core/tests/test_quyen_ceo_erp.py` (AC-44.6).
- `app/org/tests/test_account_management.py`, `app/org/tests/test_erp_navigation_matrix.py`.
- `app/reports/tests/test_ma_tran_phan_quyen_bao_cao.py`.
- Bài của từng app.

#### 3.1.2 Nhóm đường KN ERP

| Nhóm (app) | Đường | Cái chặn chính | Số đường | Cho phép có kiểm | Từ chối: có / một phần / không |
|---|---|---|---|---|---|
| Xác thực (core) | `dang_nhap`, `dang_xuat`, `doi_mat_khau` | công khai / CSRF / `login_required` | 3 | 3 | 0 / 2 / 1 |
| Quản trị và tác vụ (core) | `nhat_ky`, `ma_tran_quyen`, `tac_vu`, `tac_vu_xem`, `tac_vu_tien_do`, `tac_vu_tai` | `assert_admin`; `BackgroundJob.in_scope` → 404 | 6 | 6 | 6 / 0 / 0 |
| Nhân sự (org) | `nhan_su`, `nhan_su_moi`, `nhan_su_goi_y_ma`, `nhan_su_sua`, `nhan_su_dat_lai_mat_khau`, `nhan_su_xoa`, `nhan_su_doi_trang_thai`, `bo_phan` | `assert_rank(LEADER/ADMIN)`, `AccountPolicy.require`, `locked_target` | 8 | 7 (thiếu `nhan_su_doi_trang_thai`) | 8 / 0 / 0 |
| Tổng quan (dashboard) | `tong_quan` | `login_required` + phạm vi trong `dashboard_service` | 1 | 1 | 0 / 1 / 0 |
| Bảng dữ liệu `/bang/` (forms_builder) | 13 đường | `erp_table_view` = `assert_rank(MANAGER)`; `_lay_bang` in_scope; `grant_service.can_import/can_manage_columns`; `assert_business_write` | 13 | 10 | 10 / 3 / 0 |
| Biểu mẫu `/bieu-mau/` (forms_builder) | 8 đường | `assert_business_write` + `assert_rank(MANAGER)` + `FormDef.in_scope`; `can_fill` | 8 | 2 (`bieu_mau`, `bieu_mau_dien`) | 4 / 4 / 0 |
| Báo cáo (reports) | 12 đường | `daily_service` (history, can_restore, can_amend, can_withdraw), `summary_service.pick_table`, `threshold_service.can_set`; CEO bị `assert_business_write` | 12 | 12 | 10 / 2 / 0 |
| Chuyển sang CRM (orders/handoff.py) | `len_don`, `kiem_khach`, `san_pham_moi`, `don_hang`, `don_xem`, `don_bo` | `assert_departments(SALES_ONLY)`; có `code` thì chỉ dựa `orders_of` | 6 | 2 | 2 / 4 / 0 |
| Bảng tin (feed) | 8 đường | `login_required`; `can_moderate`, `can_delete_post`, `can_delete_comment` | 8 | 8 | 3 / 5 / 0 |
| Tài liệu (documents) | 5 đường | `assert_rank(MANAGER)`, `Document.in_scope`, `can_manage_document` | 5 | 5 | 4 / 1 / 0 |
| Công việc (taskboard) | 6 đường | `tasks_of` → 404; `can_edit`, `can_change_status`, `can_delete` | 6 | 6 | 4 / 2 / 0 |
| Văn hoá (culture) | 3 đường | `can_recognize`, `active_user` | 3 | 3 | 1 / 2 / 0 |
| Tài nguyên (resources) | 5 đường | `assert_rank(MANAGER)` + `resources_qs` | 5 | 5 | 4 / 1 / 0 |
| Django admin | `/quan-tri/` | `is_staff`; chặn xoá cứng (`core/admin.py`, `org/admin.py`) | 1 | 0 | 0 / 0 / 1 |
| **Tổng** | | | **85** | **70** | **56 / 27 / 2** |

#### 3.1.3 Nhóm đường KN CRM

| Nhóm | Đường | Cái chặn chính | Số đường | Cho phép có kiểm | Từ chối: có / một phần / không |
|---|---|---|---|---|---|
| Xác thực (core) | `dang_nhap`, `dang_xuat`, `doi_mat_khau` | như ERP | 3 | 3 | 1 / 1 / 1 |
| Quản trị và tác vụ (core) | `nhat_ky`, `ma_tran_quyen`, `tac_vu`, `tac_vu_xem`, `tac_vu_tien_do`, `tac_vu_tai` | `assert_admin`; in_scope → 404 | 6 | 3 (3 chỉ kiểm ở ERP) | 4 / 2 / 0 |
| Trang chủ và điều hướng | `tong_quan`, `bang` (`/danh-sach-bang/`), `bang_tinh` (che), `thu_muc`, `bang_tinh_mac_dinh`, `bang_xem` (`/bang/<code>/mo/`) | `login_required`; `catalog.chi_van_don` + in_scope → 404 | 6 | 5 (thiếu `bang_xem`) | 6 / 0 / 0 |
| Quản lý bảng dùng chung với ERP | `bang_moi`, `bang_cot`, `bang_xoa_cot`, `bang_nhap`, `bang_mau_nhap`, `bang_nhap_xem_truoc`, `bang_nhap_xac_nhan`, `bang_cap_quyen`, `bang_thu_quyen` | `_chi_bang_van_don` (404, chạy **trước** `login_required`; `bang_moi` không bọc) + guard của forms_builder | 9 | 6 | 5 / 2 / 2 |
| Trang CRM nhập tệp, cấp quyền | `nhap_tep`, `cap_quyen` | `assert_business_write` + `assert_rank(LEADER/MANAGER)` | 2 | 2 | 2 / 0 / 0 |
| Thư mục | `thu_muc_moi`, `thu_muc_sua`, `thu_muc_xoa`, `bang_tinh_chuyen_thu_muc` | `Folder.in_scope`, `_kiem_quan_ly_thu_muc` | 4 | 4 | 4 / 0 / 0 |
| Lưới vận đơn (khung và JSON) | `bang_tinh_xem`, `master_data`, `master_save`, `master_clear_details`, `master_history`, `master_scope`, `master_sync`, `master_filters`, `bang_tinh_moi_nhat`, `bang_tinh_loc_cot`, `bang_tinh_xuat` | `master_grid_service.table_for` (403 JSON); `_bang` (404); quyền sửa từng dòng; CAS 409 | 11 | 11 | 8 / 3 / 0 |
| Cột lưới | `bang_tinh_them_cot`, `bang_tinh_xoa_cot`, `bang_tinh_an_cot` | `_kiem_quan_ly_cot` | 3 | 3 | 3 / 0 / 0 |
| Đường cũ đã tắt (luôn 409) | `bang_tinh_o`, `bang_tinh_dong_moi`, `bang_tinh_dinh_dang`, `bang_tinh_luu_o`, `bang_tinh_xoa_dong`, `bang_tinh_khoi_phuc_dong` | `_bang` (404) rồi 409 | 6 | 6 | 2 / 4 / 0 |
| Vòng đời bảng | `deleted_tables`, `delete_table`, `restore_table` | `lifecycle_service.manageable`, `can_delete`; **không lọc `chi_van_don`** | 3 | 3 | 1 / 2 / 0 |
| Chứng từ thanh toán | `payment_library`, `payment_rows`, `payment_create`, `payment_detail`, `payment_update`, `payment_image` | cờ `PAYMENT_DOCUMENTS_ENABLED` (404, trước login); `payment_service.can_create/can_manage/document_for` | 6 | 5 (thiếu `payment_rows`) | 3 / 3 / 0 |
| Vận đơn và lên đơn | `waybill_preview`, `don_xem`, `don_bo`, `kiem_khach`, `san_pham_moi`, `waybill_assignment`, `waybill_create`, `waybill_detail`, `waybill_statistics` | `assert_departments(SALES_ONLY)`, `orders_of`, `can_assign`, `items_for`, `can_edit_record`; `waybill_statistics` gọi `master_grid_service.table_for(user, ACTIVE_WAYBILL_TABLE_CODE)` rồi 302 sang `crm_statistics` | 9 | 9 | 7 / 2 / 0 |
| Thống kê | `crm_statistics` | `resolve_source` → 403 + `record_denied` | 1 | 1 | 1 / 0 / 0 |
| **Tổng** | | | **69** | **61** | **47 / 19 / 3** |

#### 3.1.4 Đường thiếu kiểm chiều từ chối — KN ERP (29 đường)

Cột "Bài hiện có" ghi bài từ chối đang có. Ô ghi **không** nghĩa là chưa có bài nào.

| Nhóm | Đường (tên — path — phương thức) | Bài hiện có | Ca từ chối cần thêm → mã mong đợi | Ưu tiên |
|---|---|---|---|---|
| Xác thực | `doi_mat_khau` — `/doi-mat-khau/` — GET/POST | **không** | Chưa đăng nhập → 302 `/dang-nhap/?next=` | P1 |
| Xác thực | `dang_nhap` — `/dang-nhap/` | sai mật khẩu 200, khoá tạm | Đăng nhập rồi GET → 302 (`redirect_authenticated_user`); `next` ngoài host ở ERP | P2 |
| Xác thực | `dang_xuat` — `/dang-xuat/` — POST | POST 302, thiếu CSRF 403 | GET → 405 và phiên còn nguyên | P2 |
| Django admin | `/quan-tri/` (cả cây) | **không**: `test_account_management.py:312` gọi `/admin/`, đường không tồn tại ở ERP | Staff, Leader, Manager, CEO, KT → 302 về `/quan-tri/login/`; Admin 200 | P0 |
| Tổng quan | `tong_quan` — `/` | chỉ chưa đăng nhập | Số liệu không chứa dòng ngoài phạm vi, kiểm qua HTTP cho từng vai | P2 |
| Bảng dữ liệu | `bang_xoa_cot` — `/bang/<code>/cot/<pk>/bo/` — POST | chỉ chưa đăng nhập | Staff, Leader 403; Manager bộ phận khác 404/403; CEO 403; cột không đổi | P0 |
| Bảng dữ liệu | `bang_cap_quyen` — `/bang/<code>/cap-quyen/` — POST | chỉ chưa đăng nhập (bài Leader nằm ở URLconf CRM) | Staff, Leader 403; CEO 403; Manager bộ phận khác: xem TL-01 (§3.1.9) | P0 |
| Bảng dữ liệu | `bang_thu_quyen` — `/bang/<code>/thu-quyen/<pk>/` — POST | chỉ chưa đăng nhập | Như trên; Grant của bảng khác → 404 | P0 |
| Biểu mẫu | `truong_moi` — `/bieu-mau/truong-moi/` | chỉ chưa đăng nhập | Staff, Leader 403; CEO POST 403 | P1 |
| Biểu mẫu | `bieu_mau_bo_truong` — `/bieu-mau/<code>/bo-truong/<pk>/` — POST | chỉ chưa đăng nhập | Staff, Leader 403; Manager bộ phận khác 404 (in_scope); CEO 403 | P1 |
| Biểu mẫu | `bieu_mau_cap_quyen` — `/bieu-mau/<code>/cap-quyen/` — POST | chỉ chưa đăng nhập | Như trên; không tạo Grant | P0 |
| Biểu mẫu | `bieu_mau_thu_quyen` — `/bieu-mau/<code>/thu-quyen/<pk>/` — POST | chỉ chưa đăng nhập | Như trên; Grant vẫn còn | P0 |
| Báo cáo | `bao_cao_hoat_dong` — `/bao-cao/hoat-dong/` | chỉ chưa đăng nhập | Đi theo chuyển hướng: nguồn ngoài phạm vi → 403 ở trang đích | P2 |
| Báo cáo | `bao_cao_hoat_dong_xuat` — `/bao-cao/hoat-dong/xuat/` | chỉ chưa đăng nhập | Như trên, với `bao_cao_tong_hop_xuat` | P2 |
| Chuyển sang CRM | `kiem_khach` — `/len-don/kiem-khach/` | chỉ chưa đăng nhập | MKT, VĐ, KT, CSKH → 403 | P1 |
| Chuyển sang CRM | `san_pham_moi` — `/len-don/san-pham-moi/` | chỉ chưa đăng nhập | MKT, VĐ, KT, CSKH → 403 | P1 |
| Chuyển sang CRM | `don_hang` — `/don-hang/` | chỉ chưa đăng nhập | Bộ phận khác Sale → 403 | P1 |
| Chuyển sang CRM | `don_bo` — `/don-hang/<code>/bo/` | chỉ chưa đăng nhập | Đơn ngoài `orders_of` → 404 | P1 |
| Bảng tin | `bang_tin` — `/bang-tin/` | chỉ chưa đăng nhập | Thiết kế là toàn công ty; chỉ cần khẳng định bài đã gỡ không hiện ra | P2 |
| Bảng tin | `bang_tin_dang` — `/bang-tin/dang/` — POST | GET 405, chưa đăng nhập | CEO POST: mã chưa xác minh (ADR-044 có cho CEO đăng bài không?), cần chốt | P2 |
| Bảng tin | `bang_tin_xem` — `/bang-tin/<pk>/` | bài gỡ 404 | Thiết kế toàn công ty; giữ ca 404 | P2 |
| Bảng tin | `bang_tin_thich` — `/bang-tin/<pk>/thich/` | bài gỡ 404, GET 405 | Như trên | P2 |
| Bảng tin | `bang_tin_binh_luan` — `/bang-tin/<pk>/binh-luan/` | bài gỡ 404 | Như trên | P2 |
| Tài liệu | `tai_lieu` — `/tai-lieu/` | chỉ chuyển trang | Không cần thêm (chuyển sang `bieu_mau?tab=documents`) | P2 |
| Công việc | `cong_viec` — `/cong-viec/` | chỉ chưa đăng nhập | Danh sách không chứa việc ngoài `tasks_of` | P2 |
| Công việc | `cong_viec_moi` — `/cong-viec/moi/` | giao ngoài phạm vi → 200 kèm lỗi form | CEO POST bị chặn ở `task_service.create_task`: khẳng định không tạo Task. Chủ dự án chốt 200 kèm lỗi form hay 403 | P1 |
| Văn hoá | `van_hoa` — `/van-hoa/` | chỉ chưa đăng nhập | Thiết kế toàn công ty | P2 |
| Văn hoá | `van_hoa_thanh_vien` — `/van-hoa/thanh-vien/<pk>/` | 404 khi người đã khoá | Thiết kế không giới hạn phạm vi; ghi rõ là có chủ ý | P2 |
| Tài nguyên | `tai_nguyen` — `/tai-nguyen/` | bộ lọc lạ 404 | Thiết kế danh sách chung | P2 |

Có kiểm từ chối nhưng thiếu vai CEO, ghi riêng:
- `tai_nguyen_moi`, `tai_lieu_tai_len`: `assert_rank(MANAGER)` cho CEO (rank 35) qua ở GET, còn ghi thì bị chặn ở tầng dịch vụ. Chưa có bài xác minh hành vi của CEO.
- Các app feed, documents, resources, culture, taskboard không có bài HTTP nào cho CEO.

#### 3.1.5 Đường thiếu kiểm chiều từ chối — KN CRM (22 đường)

| Nhóm | Đường (tên — path) | Bài hiện có | Ca từ chối cần thêm → mã mong đợi | Ưu tiên |
|---|---|---|---|---|
| Quản lý bảng | `bang_xoa_cot` — `/bang/<code>/cot/<pk>/bo/` | **không** (chỉ ghi tên trong `CHUNG_KHONG_GET`) | Staff 403; Leader bộ phận khác 404/403; CEO 403 (nhờ `can_manage_columns`, view không có `assert_business_write`); bảng thường 404 | P0 |
| Quản lý bảng | `bang_thu_quyen` — `/bang/<code>/thu-quyen/<pk>/` | **không** | Staff, Leader 403; Manager bộ phận khác: xem TL-01; Grant của bảng khác 404 | P0 |
| Quản lý bảng | `bang_nhap_xem_truoc` — `/bang/<code>/nhap/<pk>/` | chỉ ở ERP (`test_nhap_xuat.py`) | Tác vụ nhập của người khác → 404 dưới URLconf CRM | P1 |
| Quản lý bảng | `bang_nhap_xac_nhan` — `/bang/<code>/nhap/<pk>/xac-nhan/` | chỉ ở ERP | Như trên; DataRecord không đổi | P1 |
| Quản lý bảng (lỗ chung) | 8 đường bọc `_chi_bang_van_don` | **không** | Chưa đăng nhập với mã **không** phải bảng vận đơn → hiện là 404, mong đợi 302 (không để dò ra mã bảng) | P1 |
| Xác thực | `doi_mat_khau` | **không** | Chưa đăng nhập → 302 | P1 |
| Xác thực | `dang_nhap` | next ngoài bị chặn | Sai mật khẩu, khoá tạm, thiếu CSRF → 403 dưới URLconf CRM | P2 |
| Tác vụ | `tac_vu_xem` — `/tac-vu/<pk>/` | chỉ ở ERP | Tác vụ người khác → 404 ở CRM | P1 |
| Tác vụ | `tac_vu_tien_do` — `/tac-vu/<pk>/tien-do/` | chỉ ở ERP | Như trên | P1 |
| Vòng đời bảng | `deleted_tables` — `/bang-da-xoa/` | chỉ chưa đăng nhập | Staff, Leader, KT, CSKH, CEO: hiện trả **200 rỗng**, mong đợi 403 (FR-3.5). Bảng thường không được liệt kê (ADR-040) | P0 |
| Vòng đời bảng | `restore_table` — `/bang-tinh/<code>/khoi-phuc-bang/` | chỉ CSRF | Manager bộ phận khác 404; Staff, Leader 403/404; bảng thường 404 | P1 |
| Chứng từ thanh toán | `payment_library` — `/chung-tu-thanh-toan/` | chỉ cờ tắt 404 | Cờ bật: MKT, Sale chỉ thấy chứng từ của dòng trong phạm vi; `include_deleted` bị bỏ qua với người không `can_manage` | P1 |
| Chứng từ thanh toán | `payment_rows` — `/chung-tu-thanh-toan/don/` | chỉ cờ tắt 404 | Cờ bật: MKT, Sale, CSKH, CEO → 403 JSON | P0 |
| Chứng từ thanh toán | `payment_detail` — `/chung-tu-thanh-toan/<pk>/` | chỉ cờ tắt 404 | Cờ bật: chứng từ của dòng ngoài phạm vi → 403 JSON | P0 |
| Vận đơn | `kiem_khach` — `/van-don/len-don/kiem-khach/` (trả tên khách theo SĐT) | chỉ chưa đăng nhập | VĐ, MKT, KT, CSKH, CEO → 403 kèm DENIED, không lộ tên khách | P0 |
| Vận đơn | `waybill_statistics` — `/van-don/thong-ke/` (`app/crm/waybill_views.py statistics`: gọi `table_for(request.user, ACTIVE_WAYBILL_TABLE_CODE)` rồi 302 sang `/thong-ke/?<query cũ>&nguon=van_don`) | chỉ chưa đăng nhập | (a) MKT → 403. (b) **Sale**: `docs/kiem-chung-database-phan-quyen-20261006.md` (dòng 22, mục "Ghi nhận, chưa sửa") ghi Sale nhận 403 ở đường này, trong khi `/thong-ke/` mở cho mọi vai. Viết bài ghi lại hành vi hiện tại, chờ chốt L8. (c) Chiều cho phép: VĐ, AD → 302 tới `/thong-ke/?...&nguon=van_don` và **giữ nguyên query** (ví dụ `?tu=2026-09-01&den=2026-09-11` → `/thong-ke/?tu=2026-09-01&den=2026-09-11&nguon=van_don`). KT, CSKH, CEO: chưa xác minh | P1 |
| Lưới JSON | `master_scope` — `/bang-tinh/<code>/quyen-dong/` | chỉ kiểm lọc dòng (CSKH) | MKT → 403 ở mức bảng; bảng thường 403 kể cả Admin | P1 |
| Lưới JSON | `master_sync` — `/bang-tinh/<code>/dong-bo/` | chỉ chưa đăng nhập | Bật `CRM_OPT_SYNC`: MKT → 403, bảng thường 403. Khi cờ tắt, đường trả `unsupported` **trước** khi kiểm bảng: khẳng định không lộ gì | P1 |
| Lưới JSON | `master_filters` — `/bang-tinh/<code>/bo-loc/` | chỉ mã bảng lạ 404 | MKT, Sale → 404 | P1 |
| Đường cũ | `bang_tinh_dinh_dang`, `bang_tinh_luu_o`, `bang_tinh_xoa_dong`, `bang_tinh_khoi_phuc_dong` | 409 cho người có quyền; chỉ chưa đăng nhập | MKT, Sale GET+POST → 404 (giống `o/`, `dong-moi/`); dữ liệu không đổi | P2 |

#### 3.1.6 Đường thiếu chiều cho phép

| Dịch vụ | Đường | Ca cần thêm | Ưu tiên |
|---|---|---|---|
| ERP | `nhan_su_doi_trang_thai` | Admin khoá rồi mở khoá qua HTTP (chi tiết ở PH-09, §3.2) | P1 |
| ERP | `bang_xoa_cot`, `bang_cap_quyen`, `bang_thu_quyen` | Manager bộ phận sở hữu → 302 và dữ liệu đổi đúng (chờ chốt ADR-014 ở §3.1.7) | P1 |
| ERP | `bieu_mau_moi`, `truong_moi`, `bieu_mau_sua`, `bieu_mau_bo_truong`, `bieu_mau_cap_quyen`, `bieu_mau_thu_quyen` | Manager tạo, sửa, bỏ trường, cấp và thu quyền qua HTTP → 302 | P1 |
| ERP | `kiem_khach`, `san_pham_moi`, `don_xem`, `don_bo` | Sale → 302 sang đúng URL CRM | P2 |
| ERP | `/quan-tri/` | Admin → 200 | P0 (gộp với PQ-03) |
| CRM | `bang_xem` (`/bang/<code>/mo/`), `bang_xoa_cot`, `bang_thu_quyen`, `payment_rows` | Vai hợp lệ → 302 / 200 | P1 |
| CRM | `waybill_statistics` (`/van-don/thong-ke/`) | VĐ, AD → 302, `Location` = `/thong-ke/?<query cũ>&nguon=van_don`; không có query thì `/thong-ke/?nguon=van_don`. Đi theo chuyển hướng → 200 | P1 |
| CRM | `bang_nhap_xac_nhan`, `tac_vu_xem`, `tac_vu_tien_do`, `tac_vu_tai` | Chạy lại ca thành công dưới URLconf CRM | P2 |

#### 3.1.7 Lệch thiết kế phát hiện khi kiểm kê (cần chủ dự án chốt trước khi viết kỳ vọng)

| Mã | Lệch | Bằng chứng | Kỳ vọng đề xuất |
|---|---|---|---|
| L1 | ADR-014 ghi Bảng dữ liệu ERP chỉ đọc, nhưng ERP vẫn mở đường ghi cho Manager: `bang_moi`, `bang_cot` POST, `bang_nhap`, `bang_nhap_xac_nhan`, `bang_them_lua_chon`, cấp và thu quyền | `erp_table_view` chỉ kiểm MANAGER. `test_ma_tran_quyen_hai_dich_vu.py` khẳng định `manager_vd` nhận 200 ở `/bang/<code>/nhap/` trong ERP | Đối chiếu ADR-014 với ADR-045. Chưa xác minh đây là chủ ý hay lệch |
| L2 | Vòng đời bảng ở CRM không lọc `catalog.chi_van_don` | `app/crm/lifecycle_views.py`, `lifecycle_service.manageable`. `test_table_lifecycle.py::test_delete_and_restore_preserve_identity` cho `manager_mkt` xoá bảng thường `shared_marketing` qua CRM (302) | Bảng thường → 404 mọi vai (ADR-040) |
| L3 | `/bang-da-xoa/` trả trang rỗng thay vì từ chối; Leader bị loại dù CRM coi Leader như Manager (ADR-015) | `lifecycle_service.manageable`; `docs/kiem-chung-database-phan-quyen-20261006.md` dòng 21 | 403 cho vai không quản lý; chốt vai Leader |
| L4 | `_chi_bang_van_don` chạy `get_object_or_404` trước `login_required` | `app/knjsc/urls_bangtinh.py` | Chưa đăng nhập → luôn 302 |
| L5 | `don_bo` (CRM) từ chối bằng 302 kèm thông báo và DENIED, không phải 403 | `orders/views.py don_bo`, ADR-049 | Giữ 302, nhưng bài phải khẳng định đơn còn nguyên và có DENIED; hoặc đổi sang 403 |
| L6 | Trang tác vụ ở CRM hiện liên kết "Mọi tác vụ" dẫn tới trang 403 | `core/context_processors.py khung_chung` (`can_list_jobs = is_crm_request(...) or ...`) | Ẩn liên kết (AC-44.4) |
| L7 | `bang_cap_quyen` / `bang_thu_quyen` không kiểm bộ phận sở hữu | TL-01 (`docs/test-log.md`, trạng thái "Mới"). Đã đọc lại `app/forms_builder/views.py:488-518`: chỉ có `assert_business_write`, `assert_rank(MANAGER)`, `_lay_bang`; `grant_service.grant/revoke` không kiểm thêm | 403 + DENIED (§3.1.9) |
| L8 | `/van-don/thong-ke/` (liên kết cũ) gate bằng `table_for` bảng vận đơn, còn trang đích `/thong-ke/` mở cho mọi vai. Sale nhận 403 ở liên kết cũ | `app/crm/waybill_views.py statistics` (dòng 124–131); `docs/kiem-chung-database-phan-quyen-20261006.md` dòng 22 ("Ghi nhận, chưa sửa") | Chốt một trong hai: (a) Sale → 302 như các vai khác, rồi trang đích tự lọc nguồn bằng `resolve_source`; (b) giữ 403 và ghi rõ là có chủ ý. Chưa xác minh `/thong-ke/?nguon=van_don` trả gì với Sale |

#### 3.1.8 Thiết kế bài kiểm tham số hoá cho ma trận

**Tệp đề xuất**: `app/tests/test_ma_tran_duong_dan_vai.py` (chưa có). Bài này không thay thế `test_ma_tran_quyen_hai_dich_vu.py`; nó mở rộng ra mọi đường.
- Chạy trong bộ chính của CI: `.github/workflows/ci.yml` chạy `pytest -m "not trinh_duyet"`, tức là gồm cả các bài dấu `cham`.
- Đánh dấu `cham` nếu thời gian chạy vượt 45 giây.

**Vai cần có (14 cột).** Fixture `nguoi_dung` trong `app/conftest.py` mới có `staff_sale_1`, `staff_sale_1b`, `staff_sale_2`, `leader_sale_1`, `leader_sale_2`, `manager_sale`, `staff_mkt`, `manager_mkt`, `staff_vd`, `staff_kt`, `admin` (username `quan_tri`). Còn thiếu năm vai. Cần thêm fixture `vai_day_du`, dựng theo đúng cách các bài hiện có đang làm:

| Ký hiệu | Vai | Nguồn |
|---|---|---|
| CĐN | Chưa đăng nhập | `Client()` |
| S-S / L-S / M-S | Staff / Leader / Manager Sale | `staff_sale_1`, `leader_sale_1`, `manager_sale` |
| S-M / L-M / M-M | Staff / Leader / Manager MKT | `staff_mkt`, **`leader_mkt`** (thêm, như `crm/tests/test_quyen_leader.py::leader_mkt`), `manager_mkt` |
| S-V / L-V / M-V | Staff / Leader / Manager VĐ | `staff_vd`, **`leader_vd`**, **`manager_vd`** (thêm, như `test_ma_tran_quyen_hai_dich_vu.py:67-68`) |
| KT | Staff Kế toán (ADR-038) | `staff_kt` |
| CS | Staff CSKH | **thêm**, như `crm/tests/test_waybill_feedback.py::cskh_staff` (bộ phận `cskh`) |
| CEO | CEO (ADR-044) | **thêm** `make_user(..., Rank.CEO)` |
| AD | Admin | `admin` |

**Dữ liệu mồi** (một fixture `the_gioi`):
- Bảng vận đơn (`orders.constants.ACTIVE_WAYBILL_TABLE_CODE`) có dòng của từng bộ phận.
- Bảng thường `don_sale` (Sale, không có workflow) và `shared_marketing` (MKT).
- Bảng có `workflow="waybill"` của Sale, như `bang_sale` trong `test_quyen_leader.py`.
- Một Grant VIEW `don_sale` → `manager_mkt`.
- Mỗi model đích một bản: BackgroundJob của `staff_sale_1`, FormDef, DailyReport, Order, Folder, chứng từ thanh toán (bật `PAYMENT_DOCUMENTS_ENABLED`), Post, Document, Task, Resource.

**Cấu trúc kỳ vọng:**
- `KY_VONG = [(dich_vu, phuong_thuc, url_mau, du_lieu, mac_dinh, {vai: ma})]`. `mac_dinh` là mã cho mọi vai không liệt kê.
- Một bài canh duyệt `get_resolver("knjsc.urls")` và `get_resolver("knjsc.urls_bangtinh")` (giống `_duong_dan` trong `test_ma_tran_quyen_hai_dich_vu.py`). Bài khẳng định mọi pattern nằm trong `KY_VONG` hoặc trong `MIEN = {pattern: "lý do"}`. Có đường mới mà chưa điền quyền thì bài đỏ.
- Tham số hoá theo `(dòng KY_VONG) × 14 vai`; dùng `override_settings(ROOT_URLCONF=...)` cho từng dịch vụ.

**Quy tắc khẳng định cho mỗi ô:**
1. Mã trả về **đúng một giá trị**. Không dùng `in (403, 404)`, vì hai mã mang nghĩa khác nhau: 403 là thấy nhưng không được làm; 404 là ngoài phạm vi, không lộ là có tồn tại.
2. Quy tắc 8 / FR-3.5: với đường danh sách, vai ngoài phạm vi phải nhận 403/404, **không** được nhận 200 với danh sách rỗng. Ô 200 thì khẳng định thêm là không có bản ghi nào ngoài `in_scope` của vai.
3. Ô 403 ở view có gọi `record_denied`: số dòng AuditLog DENIED tăng đúng 1 (AC-3.7).
4. Ô từ chối với POST: chụp số dòng TableDef, ColumnDef, DataRecord, Grant, DailyReport, Order, Task, Post trước và sau; không bảng nào đổi.
5. Bảng thường ở CRM: 404 cho **mọi** vai đã đăng nhập, kể cả AD (ADR-040). Riêng JSON lưới (`master_data`, `master_save`, `master_history`, `master_scope`) trả 403 JSON.
6. CĐN: 302 về `/dang-nhap/?next=`. Ngoại lệ có chủ ý: đường sau cờ `documents_enabled` khi cờ tắt (404). `/quan-tri/` thì về `/quan-tri/login/`.
7. Ô 302 của đường chuyển hướng (`waybill_statistics`, `len_don`, `don_hang`): khẳng định cả `Location`, kể cả query được giữ lại, không chỉ khẳng định mã.

**Bảng kỳ vọng mẫu.** Cột "Nguồn": "Bài" là đã có bài khẳng định; "Guard" là suy từ guard, chưa chạy; "Chốt" là phụ thuộc §3.1.7.

| # | Dịch vụ, đường | CĐN | S-S | L-S | M-S | S-M | L-M | M-M | S-V | L-V | M-V | KT | CS | CEO | AD | Nguồn |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | ERP GET `/nhat-ky/` | 302 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 200 | Bài |
| E2 | ERP GET `/nhan-su/` | 302 | 403 | 200 | 200 | 403 | 200 | 200 | 403 | 200 | 200 | 403 | 403 | 200 | 200 | Bài + Guard (KT, CS) |
| E3 | ERP GET `/nhan-su/moi/` | 302 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 200 | Bài |
| E4 | ERP GET `/bang/` | 302 | 403 | 403 | 200 | 403 | 403 | 200 | 403 | 403 | 200 | 403 | 403 | 200 | 200 | Bài + Guard |
| E5 | ERP GET `/bang/<vận đơn>/nhap/` | 302 | 403 | 403 | 404¹ | 403 | 403 | 404¹ | 403 | 403 | 200 | 403 | 403 | 403¹ | 200 | Bài (chấp nhận 403/404) + Chốt L1 |
| E6 | ERP POST `/bang/don_sale/cap-quyen/` | 302 | 403 | 403 | 302 | 403 | 403 | **403** (hiện 302, TL-01) | 403 | 403 | 404 | 403 | 403 | 403 | 302 | Guard + TL-01 |
| E7 | ERP GET `/len-don/` | 302 | 302→CRM | 302→CRM | 302→CRM | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403¹ | 302→CRM | Bài (5 vai) + Guard |
| E8 | ERP GET `/don-hang/` | 302 | 302 | 302 | 302 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403¹ | 302 | Guard (chưa có bài 403) |
| E9 | ERP GET `/bao-cao/` | 302 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200¹ | 200¹ | 403 | 200 | Bài + Guard |
| E10 | ERP GET `/bao-cao/da-bo/` | 302 | 403 | 403 | 200 | 403 | 403 | 200 | 403 | 403 | 200 | 403 | 403 | ¹ | 200 | Bài + Guard |
| E11 | ERP GET `/doi-mat-khau/` | 302 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | Bài (trừ CĐN) |
| E12 | ERP GET `/quan-tri/` | 302² | 302² | 302² | 302² | 302² | 302² | 302² | 302² | 302² | 302² | 302² | 302² | 302² | 200 | Guard (chưa có bài) |
| C1 | CRM GET `/bang-tinh/<vận đơn>/` | 302 | 302→Lên đơn | 302→Lên đơn | 302→Lên đơn | 403 | 403 | 403 | 200 | 200 | 200 | ¹ | 200¹ | 200 | 200 | Bài (5 vai) + Guard |
| C2 | CRM GET `/bang-tinh/shared_marketing/` (bảng thường) | 302 | 404 | 404 | 404 | 404 | 404 | 404 | 404 | 404 | 404 | 404 | 404 | 404 | 404 | Bài (ADR-040) |
| C3 | CRM GET `/bang-tinh/shared_marketing/du-lieu/` | 302 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | Bài |
| C4 | CRM GET `/bang/shared_marketing/cot/` | **302** (hiện 404, L4) | 404 | 404 | 404 | 404 | 404 | 404 | 404 | 404 | 404 | 404 | 404 | 404 | 404 | Bài + Chốt L4 |
| C5 | CRM POST `/bang-tinh/<vận đơn>/luu-json/` (sửa 1 ô dòng VĐ) | 302 | 403 | 403 | 403 | 403 | 403 | 403 | 200 | 200 | 200 | ¹ | 403¹ | 403 | 200 | Bài (CEO, theo vai) + Guard |
| C6 | CRM POST `/bang/<vận đơn>/cap-quyen/` | 302 | 404¹ | 404¹ | 404¹ | 403 | 403 | 404¹ | 403 | 403 | 302 | 403 | 403 | 403 | 302 | Bài (Leader 403) + Guard + TL-01 |
| C7 | CRM GET `/cap-quyen/` | 302 | 403 | 403 | 200 | 403 | 403 | 200 | 403 | 403 | 200 | 403 | 403 | 403 | 200 | Bài + Guard |
| C8 | CRM GET `/nhap-tep/` | 302 | 403 | 200 | 200 | 403 | 200 | 200 | 403 | 200 | 200 | 403 | 403 | 403 | 200 | Bài + Guard |
| C9 | CRM GET `/bang-da-xoa/` | 302 | **403** | **403** | 200 | **403** | **403** | 200 | **403** | **403** | 200 | **403** | **403** | **403** | 200 | Chốt L3 (hiện 200 rỗng) |
| C10 | CRM POST `/bang-tinh/shared_marketing/xoa-bang/` | 302 | 404 | 404 | 404 | 404 | 404 | **404** (hiện 302) | 404 | 404 | 404 | 404 | 404 | 404 | 404 | Chốt L2 |
| C11 | CRM GET `/van-don/len-don/kiem-khach/` | 302 | 200 | 200 | 200 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 403¹ | 200 | Bài (Sale) + Guard |
| C12 | CRM GET `/chung-tu-thanh-toan/don/` (cờ bật) | 302 | 403 | 403 | 403 | 403 | 403 | 403 | 200 | 200 | 200 | 200 | 403 | 403 | 200 | Guard (`can_create`) |
| C13 | CRM POST `/van-don/phan-cong/` | 302 | 403 | 403 | 403 | 403 | 403 | 403 | 403 | 200 | 200 | 403 | 403 | 403 | 200 | Bài + Guard |
| C14 | CRM POST `/van-don/don-goc/<code>/bo/` | 302 | 302+DENIED³ | 404¹ | 302+DENIED³ | 404 | 404 | 404 | 404 | 404 | 404 | 404 | 404 | ¹ | 302 (đã bỏ) | Bài + Chốt L5 |
| C15 | CRM GET `/van-don/thong-ke/?tu=…&den=…` | 302 | 403⁴ | 403⁴ | 403⁴ | 403 | 403 | 403 | 302⁵ | 302⁵ | 302⁵ | ¹ | ¹ | ¹ | 302⁵ | Biên bản 06.10 (Sale) + Guard (`table_for`) + Chốt L8 |

¹ Chưa xác minh: phụ thuộc `in_scope` của bảng hoặc đơn với vai đó, hoặc `assert_departments` với CEO không có bộ phận. Phải chạy thử để chốt một mã rồi mới đưa vào `KY_VONG`.
² Về `/quan-tri/login/?next=/quan-tri/` (Django admin, chỉ `is_staff`; theo ADR-044, CEO không có `is_staff`).
³ Người lên đơn trong phạm vi: đơn vẫn còn, có thêm 1 dòng DENIED (`app/orders/tests/test_bo_don_chi_admin.py`).
⁴ Hành vi hiện tại theo `docs/kiem-chung-database-phan-quyen-20261006.md` dòng 22, chưa có bài pytest. Mã cuối cùng phụ thuộc L8.
⁵ `Location` phải là `/thong-ke/?tu=…&den=…&nguon=van_don` (giữ query cũ, nối `nguon=van_don`).

#### 3.1.9 Ca riêng TL-01: Manager bộ phận khác tự cấp quyền Sửa

Bối cảnh: `docs/test-log.md` TL-01 (S1, "Mới"). `bang_cap_quyen` / `bang_thu_quyen` chỉ có `assert_rank(MANAGER)` + `_lay_bang` (in_scope gồm cả bảng được cấp Xem), không kiểm `grant_service.can_manage_columns` như `bang_cot`. Ở CRM, bảng phải thoả `waybill_condition` thì mới qua được `_chi_bang_van_don`.

| Bước | ERP (`knjsc.urls`, bảng thường `don_sale` của Sale) | CRM (`knjsc.urls_bangtinh`, bảng Sale có `workflow="waybill"`) |
|---|---|---|
| Mồi | `manager_sale` cấp VIEW cho `manager_mkt` qua `grant_service.grant` | như ERP |
| Ca 1 (P0): tự cấp Sửa | `manager_mkt` POST `/bang/don_sale/cap-quyen/` {user=manager_mkt, action=EDIT} → mong đợi **403**, +1 DENIED, số Grant không đổi | POST `/bang/<mã>/cap-quyen/` → như ERP |
| Ca 2 (P0): cấp cho team mình | {team=team MKT, action=EDIT} → 403 | như ERP |
| Ca 3 (P0): thu quyền chủ đã cấp | `manager_sale` cấp EDIT cho `staff_vd`; `manager_mkt` POST `/bang/don_sale/thu-quyen/<pk>/` → **403**, Grant còn (`deleted_at` rỗng) | POST `/bang/<mã>/thu-quyen/<pk>/` → như ERP |
| Ca 4 (P0): sau ca 1 thử ghi | `manager_mkt` không sửa được dòng Sale (`grant_service.can_edit_record` False) | POST `/bang-tinh/<mã>/luu-json/` → 403 |
| Đối chứng (P1) | `manager_sale` (chủ) POST cấp → 302, có Grant, có PERMISSION | `manager_sale` → 302 (khớp `test_quyen_leader.py`) |
| Đối chứng (P1) | `manager_mkt` khi chưa được cấp Xem → 404 | → 404 |
| Đối chứng (P1) | CEO → 403 (`assert_business_write`); Leader → 403 | như ERP |

Hiện dự kiến ca 1–4 đỏ. Làm theo hướng TDD: viết bài đỏ trước, rồi sửa view (thêm `_kiem_sua_cau_truc` / `can_manage_columns`). Đóng TL-01 khi bài xanh ở cả hai dịch vụ.

#### 3.1.10 Danh sách ca kiểm 3.1

| ID | Ca kiểm | Góc nhìn | Loại | Mức | Ưu tiên | Tham chiếu |
|---|---|---|---|---|---|---|
| PQ-01 | Bài ma trận tham số hoá §3.1.8 cho mọi đường ERP và CRM × 14 vai | QA | Phân quyền HTTP | Tự động | P0 | FR-3.1–3.6, AC-3.6, AC-3.7, AC-1.12 |
| PQ-02 | Bài canh: mọi URLPattern của hai resolver có trong `KY_VONG` hoặc `MIEN` | QA | Truy vết / hồi quy | Tự động | P0 | AC-1.12 |
| PQ-03 | `/quan-tri/` và `/quan-tri/org/userprofile/`: mọi vai trừ AD → 302 về đăng nhập admin; AD 200. Sửa assert `/admin/` ở `test_account_management.py:312` | QA | Phân quyền HTTP | Tự động | P0 | Điều cấm 12, ADR-044 |
| PQ-04 | TL-01: 4 ca + đối chứng ở §3.1.9 | QA | Phân quyền HTTP (bảo mật) | Tự động | P0 | TL-01, FR-8.4, ADR-015 |
| PQ-05 | Đường ghi `/bang/` ở ERP: `bang_xoa_cot`, `bang_cap_quyen`, `bang_thu_quyen` hai chiều | QA | Phân quyền HTTP | Tự động | P0 | ADR-014, ADR-045 |
| PQ-06 | Quản lý biểu mẫu (`bieu_mau_moi`, `truong_moi`, `bieu_mau_sua`, `bieu_mau_bo_truong`, `bieu_mau_cap_quyen`, `bieu_mau_thu_quyen`): Manager được; Staff, Leader 403; Manager bộ phận khác 404; CEO 403 | QA | Phân quyền HTTP | Tự động | P1 | FR-8.x |
| PQ-07 | `kiem_khach` ở CRM: vai không phải Sale → 403 + DENIED, phản hồi không chứa tên khách | QA | Bảo mật dữ liệu cá nhân | Tự động | P0 | AC-3.7 |
| PQ-08 | Chứng từ thanh toán khi bật cờ: `payment_rows`, `payment_detail`, `payment_library` theo vai và phạm vi | QA | Phân quyền HTTP | Tự động | P0 | ADR-046 |
| PQ-09 | Vòng đời bảng ở CRM: bảng thường 404; `/bang-da-xoa/` 403 với vai không quản lý; `restore_table` bộ phận khác 404 | QA | Phân quyền HTTP | Tự động (sau khi chốt L2, L3) | P0 | ADR-040, FR-3.5 |
| PQ-10 | Lỗ dò mã bảng: chưa đăng nhập gọi 8 đường bọc `_chi_bang_van_don` với mã có và mã không có → cùng 302 | QA | Bảo mật HTTP | Tự động | P1 | L4 |
| PQ-11 | Các đường chỉ kiểm ở ERP chạy lại dưới URLconf CRM: `bang_nhap_xem_truoc`, `bang_nhap_xac_nhan`, `tac_vu_xem`, `tac_vu_tien_do` | QA | Phân quyền HTTP | Tự động | P1 | AC-44.4 |
| PQ-12 | JSON lưới phụ: `master_scope`, `master_sync` (bật `CRM_OPT_SYNC`), `master_filters` theo vai | QA | Phân quyền HTTP | Tự động | P1 | ADR-040 |
| PQ-13 | Quét POST `{}` mọi endpoint bằng CEO và `staff_kt`: không bảng nghiệp vụ nào đổi; mã ∈ {302 đăng nhập, 400, 403, 404, 405}; có danh sách ngoại lệ kèm lý do | QA | Phân quyền (quét URL) | Tự động | P0 | ADR-044, ADR-045, AC-44.6 |
| PQ-14 | Liên kết "Mọi tác vụ" không hiện ở `/tac-vu/<pk>/` dưới URLconf CRM với `staff_vd`; AD vẫn thấy | QA | Giao diện + phân quyền | Tự động | P1 | AC-44.4, L6 |
| PQ-15 | `/ma-tran-quyen/` khớp `visible_navigation` cho từng Rank (CEO: "Nộp báo cáo ngày" = False) | QA | HTTP nội dung | Tự động | P2 | ADR-045 |
| PQ-16 | Leader khác bộ phận làm trưởng team Sale (dựng bằng ORM): không đặt lại mật khẩu, xoá hay xem Staff Sale; `TeamForm` từ chối chọn Leader khác bộ phận | QA | Phân quyền (cấu hình) | Tự động | P0 | ADR-003, ADR-044, FR-3.2 |
| PQ-17 | Manager hoặc Leader không có bộ phận/team gọi `/nhan-su/`, `/bao-cao/tong-hop/`, `/bang/` → 403 chứ không phải rỗng | QA | Phân quyền | Tự động | P1 | FR-3.5, AC-3.6 |
| PQ-18 | Kiểm tay trên Staging: đăng nhập bằng 5 vai mẫu (`docs/tai-khoan-mau.md`), gọi thẳng URL của vai khác (theo `docs/07-kich-ban-nghiem-thu.md` §3), xác nhận trang 403/404 tiếng Việt, không có trang trắng | Người dùng | Nghiệm thu | Thủ công | P1 | NFR-6, FR-3.5 |
| PQ-19 | `/van-don/thong-ke/` hai chiều (C15): MKT → 403; Sale → ghi hành vi hiện tại (403 theo biên bản 06.10), chờ chốt L8 rồi khoá mã; VĐ, AD → 302 với `Location` giữ nguyên query cũ và nối `nguon=van_don`; đi theo chuyển hướng → 200 | QA | Phân quyền HTTP + chuyển hướng | Tự động | P1 | L8, ADR-040, `docs/kiem-chung-database-phan-quyen-20261006.md` |

### 3.2 Phiên, đăng nhập chung ERP↔CRM và hết phiên

#### 3.2.1 Cơ chế cần kiểm (tóm tắt để định vị)

| Thành phần | Tệp | Điểm then chốt |
|---|---|---|
| Đăng nhập | `core/views.py LoginView`, `core/forms.py LoginForm.clean`, `core/services/auth_service.py`, `core/auth_backends.py CaseInsensitiveModelBackend` | Ghi `session['auth_epoch']`. Khoá tạm sau 5 lần sai (`LOGIN_MAX_FAILED`, `LOGIN_LOCK_MINUTES`). Hồ sơ có `deleted_at` không xác thực được |
| Phiên chung | `knjsc/settings/base.py` (dòng 186–192), `prod.py`, `bangtinh.py`, `core/checks.py kiem_phien_chung` (core.E001), `config/.env.example`, `deploy/production/compose.yml` | Tên và tên miền cookie **đọc từ biến môi trường**. `base.py` mặc định `SESSION_COOKIE_NAME='sessionid'`, `CSRF_COOKIE_NAME='csrftoken'`, domain rỗng → None. `prod.py` chỉ đặt `SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE=True`, không đặt tên cookie. `deploy/production/compose.yml` lấy `env_file: .env`, không đặt hai biến tên cookie. `config/.env.example` để `sessionid`/`csrftoken`. Tên `knjsc_session_v2` / `knjsc_csrf_v2` (ADR-030) chỉ có khi `.env` của VPS đặt; trong kho chỉ thấy ở bài `core/tests/test_shared_login.py`, `test_shared_login_browser.py`. Luôn có `HttpOnly` (session), `SameSite=Lax`. core.E001 chỉ kiểm **domain** cookie, không kiểm **tên** |
| Hết phiên, đổi quyền | `core/middleware.py SessionTimeoutMiddleware`, `_ve_dang_nhap` | `SESSION_IDLE_TIMEOUT_SECONDS=3600`; so `auth_epoch` với `profile.session_epoch`. Yêu cầu HTMX nhận `HX-Redirect` (đã đọc lại `middleware.py:28-35`), yêu cầu thường nhận 302 `?het_phien=1` / `?doi_quyen=1` |
| Mất hiệu lực phiên | `org/models.py UserProfile.invalidate_sessions`, `SESSION_SENSITIVE_FIELDS` (rank, department_id, team_id); `forms_builder/services/grant_service.py _mat_hieu_luc_phien` (gọi trong `grant` và `revoke`) | Đổi cấp bậc, bộ phận, team, khoá, đặt lại mật khẩu, xoá mềm, cấp hoặc thu quyền → tăng `session_epoch` |
| Buộc đổi mật khẩu | `ForcePasswordChangeMiddleware` | 302 về `/doi-mat-khau/`. Miễn `/dang-nhap`, `/dang-xuat`, `/doi-mat-khau`, `/static`, `/media` |
| Phía trình duyệt | `templates/base.html` dòng 135–143 (ERP: `htmx:beforeSwap` bắt `/dang-nhap/`); `templates/crm/base_crm.html` dòng 137, `crm/base_bang_tinh.html` dòng 103 (CRM: **không** có bộ chặn); `static/js/master-grid.js` hàm `json()` dòng 54–62 | Ở lưới CRM, `response.redirected` hoặc phản hồi không phải JSON → lỗi "Phiên đăng nhập hoặc phản hồi không hợp lệ…". Gặp `/dang-nhap/` thì `status=403`. Poll `moi-nhat/` mỗi 8 giây (`master-grid.js` dòng 1359), dừng khi `document.hidden` |

#### 3.2.2 Mức phủ hiện tại

| Tình huống | Bài hiện có | ERP | CRM | Khoảng trống |
|---|---|---|---|---|
| Đăng nhập một lần, dùng hai dịch vụ | `core/tests/test_shared_login.py::test_login_identity_and_logout_across_apps` (4 vai × 2 chiều; kiểm domain, Secure, HttpOnly, SameSite, path của cookie) | ✔ | ✔ | Chưa có CEO, KT, CSKH. Bài trình duyệt `core/tests/test_shared_login_browser.py` bị skip trong CI (cần `SHARED_LOGIN_BROWSER=1`) |
| Cookie cũ `sessionid`, `next` ngoài host | `test_shared_login.py::test_old_cookie_and_unsafe_redirect_are_not_used` | — | ✔ | `next` ngoài host ở ERP chưa xác minh. Bài tự gán `SESSION_COOKIE_NAME='knjsc_session_v2'` trong `settings`, nên chỉ chứng minh logic khi tên đã đổi, không chứng minh cấu hình triển khai có đổi tên |
| Tên cookie ở production | `test_shared_login.py` (dòng 14–18) chỉ kiểm settings đọc đúng biến khi bài tự đặt biến | ✘ | ✘ | Chưa có gì bắt được việc `.env` VPS thiếu `SESSION_COOKIE_NAME`/`CSRF_COOKIE_NAME`. Khi thiếu, `base.py` rơi về `sessionid`/`csrftoken`, cookie cũ được dùng lại, lệch ADR-030 mà không có cảnh báo. `config/.env.example` còn mặc định `sessionid`. core.E001 và `check --deploy` không kiểm tên |
| CSRF đăng nhập, đăng xuất | `test_shared_login.py::test_csrf_and_first_password_change_still_required` (đăng nhập thiếu CSRF 403 ở ERP; đăng xuất khác origin 403 ở CRM) | ✔ | ✔ | — |
| Đăng xuất | như dòng đầu (POST 302, bên kia mất phiên) | ✔ | ✔ | Chưa khẳng định nhật ký LOGOUT; GET `/dang-xuat/` → 405 và phiên còn |
| Khoá tạm sau 5 lần sai | `org/tests/test_account.py`, `org/tests/test_do_mat_khau.py` (đồng thời) | ✔ | ✘ | CRM chưa có bài sai mật khẩu hay khoá tạm. `/quan-tri/login/` đi vòng qua khoá tạm, nhật ký và `auth_epoch` (chưa chạy xác minh) |
| Hết phiên 60 phút, yêu cầu thường | `core/tests/test_ra_soat.py::test_het_phien_sau_60_phut_khong_thao_tac`; `test_shared_login.py::test_shared_session_invalidated[timeout]` (đăng nhập ERP, hết hạn thấy ở CRM) | ✔ | ✔ | — |
| Hết phiên, yêu cầu HTMX | `test_ra_soat.py::test_het_phien_khi_bam_htmx_thi_bao_trinh_duyet_chuyen_trang` (`HX-Redirect`) | ✔ | ✘ | Chưa có bài HTMX dưới URLconf CRM (`waybill_detail`, `waybill_create`, `bang_tinh_loc_cot`) |
| Hết phiên giữa lúc ghi lưới (fetch JSON) | `scripts/kiem-thu-optimization-unit.cjs` dòng 6 (hàm `parse` gặp `redirected` + `/dang-nhap/` → status 403); chạy tay, **không có trong CI** | — | ◐ | Chưa có pytest hay e2e cho ca: ghi `luu-json` khi hết phiên → không báo "Đã lưu", DB không đổi, bản nháp còn |
| Poll lưới giữ phiên sống | không có | — | ✘ | Poll 8 giây ghi `last_seen_at` → tab còn hiện thì phiên không bao giờ hết hạn (FR-1.3, AC-1.4). Trong `docs/quyet-dinh/` không có ADR nào nói poll được tính là thao tác |
| TL-02 / TL-18 | `docs/test-log.md` vẫn ghi "Mới" | — | — | TL-02 trỏ tới `static/js/bang-tinh-o.js`, tệp này **không còn** trong `app/static/js/`. Lưới hiện là `master-grid.js`, đã có nhánh `redirected`. Cần kiểm lại và cập nhật trạng thái TL-02. TL-18 vẫn đúng ở CRM với trường hợp khoá, xoá, đặt lại (dòng PH-06) |
| Đổi cấp bậc → phiên mất | `org/tests/test_account.py::test_doi_cap_bac_lam_phien_dang_mo_mat_hieu_luc` (`doi_quyen=1`); `test_account_management.py::test_promoting_admin_to_ceo_removes_technical_privileges` (epoch tăng) | ✔ | — | — |
| Đổi team → phiên mất | `org/tests/test_org_scope.py::test_gan_nguoi_vao_team_lam_mat_phien` | ✔ | — | — |
| Đổi epoch, thấy ở dịch vụ kia | `test_shared_login.py::test_shared_session_invalidated[epoch]` | ✔ | ✔ | — |
| Khoá tài khoản | `test_account.py::test_khoa_tai_khoan_lam_phien_dang_mo_mat_hieu_luc` (gọi `lock_account` ở tầng dịch vụ); `test_shared_session_invalidated[disabled]` | ✔ | ✔ | Chưa đi qua view `nhan_su_doi_trang_thai`. Bài chỉ khẳng định 302, không kiểm có lời giải thích hay không |
| Đặt lại mật khẩu (quản lý làm) | `test_account_management.py::test_reset_invalidates_erp_crm_sessions_without_forcing_change`; `app/tests/e2e/test_dat_lai_mat_khau.py` (chạy trong CI); `test_shared_session_invalidated[password]` | ✔ | ✔ | Bài dùng `force_login`, nên không kiểm nhánh `auth_epoch` |
| Đổi mật khẩu cá nhân (POST) | không có (chỉ GET, và kiểm chuyển hướng buộc đổi) | ✘ | ✘ | Chưa kiểm: xoá `must_change_password`, giữ phiên hiện tại, huỷ phiên khác, validator, không ghi nhật ký (BR-5) |
| Chưa đăng nhập vào `/doi-mat-khau/` | không có (`test_khoi` bỏ qua) | ✘ | ✘ | — |
| Xoá mềm tài khoản | `test_account_management.py::test_deleted_account_cannot_authenticate_even_reactivated`, `::test_deleted_user_never_authenticates_with_valid_hash` | ◐ | ✘ | Chưa kiểm việc **phiên đang mở** của người bị xoá bị đẩy ra ở ERP và CRM |
| Cấp quyền bảng → phiên mất | `forms_builder/tests/test_bieu_mau.py::test_cap_quyen_lam_mat_hieu_luc_phien_dang_mo` (đăng nhập thật, ERP) | ✔ | ✘ | Chưa có: thu quyền (`revoke`) → phiên mất; cấp cho team → mọi thành viên mất phiên; các ca này ở CRM |
| HTMX gặp buộc đổi mật khẩu | không có | ✘ | ✘ | `ForcePasswordChangeMiddleware` trả 302; `base.html` chỉ bắt `/dang-nhap/` |
| Không lưu đệm trang khi đã đăng nhập | chỉ view riêng có `@never_cache` | ✘ | ✘ | `NoCacheForAuthenticatedMiddleware` chưa có bài trực tiếp |
| Cấu hình triển khai | `core/tests/test_kiem_cau_hinh.py` (core.E001, thiếu `BANGTINH_GOC`) | ✔ | ✔ | `prod.py` thiếu khoá bí mật, header bảo mật: chỉ có biên bản kiểm tay `docs/kiem-chung-dien-tap-phat-hanh-staging-20261008.md` mục 11. Tên cookie: xem dòng "Tên cookie ở production" |

Ký hiệu: ✔ có bài; ◐ có một phần; ✘ không có; — không áp dụng.

#### 3.2.3 Ca cần thêm

| ID | Ca kiểm | Bước / khẳng định chính | Góc nhìn | Loại | Mức | Ưu tiên | Tham chiếu |
|---|---|---|---|---|---|---|---|
| PH-01 | `/quan-tri/login/` phải chịu khoá tạm | POST `/quan-tri/login/` 6 lần sai với `quan_tri`, rồi 1 lần đúng. Khẳng định `locked_until` khác None; lần đúng không vào được (hoặc `/quan-tri/login/` 302 về `/dang-nhap/`); có 5 dòng LOGIN_FAILED | QA | Bảo mật HTTP | Tự động | P0 | FR-1.2, AC-1.2, AC-1.9 |
| PH-02 | Phiên tạo từ `/quan-tri/login/` vẫn chịu P4 | Admin B đăng nhập qua `/quan-tri/login/`; hạ B xuống Staff; B GET `/` → 302 `doi_quyen=1`. Hoặc chứng minh `/quan-tri/login/` không tạo được phiên | QA | Phân quyền phiên | Tự động | P0 | P4, AC-1.6 |
| PH-03 | Ghi lưới khi đã hết phiên không báo "Đã lưu" | Playwright: `vd.staff` mở lưới; xoá cookie (hoặc đặt `SESSION_IDLE_TIMEOUT_SECONDS=5`); dán 500 ô. Khẳng định không hiện "✓ Đã lưu"; có lời báo hết phiên tiếng Việt; ô giữ bản nháp; DB không đổi. Đăng nhập lại ở tab khác rồi thử lại thì lưu được | Người dùng | E2E trình duyệt | Bán tự động | P0 | TL-02, TL-18, AC-1.4 |
| PH-04 | pytest cho `luu-json` khi hết phiên | URLconf CRM, `last_seen_at` lùi 3.700 giây, POST `/bang-tinh/<vận đơn>/luu-json/`. Khẳng định 302 về `/dang-nhap/?het_phien=1`, DataRecord không đổi, phản hồi không phải JSON 200. Đưa `scripts/kiem-thu-optimization-unit.cjs` vào CI hoặc viết lại bằng bài tương đương | QA | Tích hợp HTTP | Tự động | P0 | AC-1.4, TL-02 |
| PH-05 | Poll lưới không giữ phiên sống quá 60 phút | (a) `last_seen_at` lùi 3.700 giây → GET `/bang-tinh/<vận đơn>/moi-nhat/` → 302 về đăng nhập. (b) Cần chốt chính sách trước: chuỗi poll 8 giây suốt 61 phút giả lập (patch `time.time`) không gia hạn `last_seen_at`, còn thao tác thật thì có | Người dùng | Tích hợp HTTP | Tự động | P1 | FR-1.3, AC-1.4, ADR-030 |
| PH-06 | HTMX ở CRM sau khoá, xoá hoặc đặt lại mật khẩu | URLconf CRM; `staff_vd` đăng nhập qua `/dang-nhap/`; Admin gọi `lock_account` (lặp lại với `delete_account`, `reset_password`); `staff_vd` POST `waybill_detail` kèm `HTTP_HX_REQUEST=true`. Mong đợi `HX-Redirect` chứa `/dang-nhap/`. Playwright: khung `#vd-detail-body` không chứa form đăng nhập | Người dùng | HTTP + E2E | Bán tự động | P1 | TL-18, AC-1.6 |
| PH-07 | HTMX gặp buộc đổi mật khẩu hoặc đổi quyền | (a) `must_change_password=True`, GET `/bang-tin/` kèm `HX-Request` → mong đợi `HX-Redirect=/doi-mat-khau/` (hiện là 302). (b) Tăng `session_epoch`, gửi yêu cầu HTMX → `HX-Redirect` chứa `doi_quyen=1`. Chạy ở cả hai URLconf | QA | HTTP | Tự động | P2 | AC-1.5, TL-18 |
| PH-08 | Đổi mật khẩu cá nhân | Tài khoản `must_change_password=True` đăng nhập ở client A và B. A POST `/doi-mat-khau/` hợp lệ → 302 `/`; A GET `/` 200; cờ False; B bị đẩy ra; mật khẩu cũ không đăng nhập được. Ca từ chối: `old_password` sai, mật khẩu toàn số, giống tên đăng nhập, hai ô khác nhau → hash và cờ không đổi. Lặp lại ở URLconf CRM | Người dùng | HTTP | Tự động | P1 | FR-1.4, AC-1.5, ADR-030 |
| PH-09 | Khoá và mở khoá qua view | Staff đăng nhập ở client S; Admin POST `/nhan-su/<pk>/doi-trang-thai/` → `is_active=False`, S bị đẩy ra ở ERP **và** CRM, có PERMISSION. POST lần nữa → mở, `failed_login_count=0`, `locked_until=None`. Admin tự khoá mình → có lời báo, không đổi gì. GET → 302, không đổi gì | Người dùng | HTTP | Tự động | P1 | FR-1.5, AC-1.6 |
| PH-10 | Xoá mềm đẩy phiên đang mở ra ở hai dịch vụ | `staff_sale_1` đăng nhập thật ở client ERP và CRM; Admin POST `/nhan-su/<pk>/xoa/` `confirm=yes`. Khẳng định GET `/` (ERP) và `/thu-muc/` (CRM) → 302 `/dang-nhap/`; đăng nhập lại thất bại | QA | HTTP | Tự động | P1 | BR-4, ADR-044, AC-1.6 |
| PH-11 | Thu quyền và cấp cho team làm mất phiên | (a) Cấp VIEW cho `staff_sale_1`, đăng nhập lại, `revoke` → GET kế tiếp 302 `doi_quyen=1`. (b) Cấp cho team Sale 1 → cả `staff_sale_1` và `staff_sale_1b` bị đẩy ra; `staff_sale_2` không bị. Chạy cả dưới URLconf CRM | QA | Phân quyền phiên | Tự động | P1 | P4, FR-1.5, AC-1.6 |
| PH-12 | Hai tab: bị hạ quyền giữa lúc đang gõ form | Tab 1: `sale.leader` mở `/nhan-su/<staff>/sua/`, gõ mật khẩu mới. Tab 2: `quantri` hạ `sale.leader` xuống Staff. Tab 1 bấm Đặt lại → về đăng nhập kèm "Quyền của bạn vừa thay đổi"; mật khẩu của Staff không đổi; không hiện lại chuỗi đã gõ | Người dùng | E2E | Bán tự động | P1 | P4, ADR-044 |
| PH-13 | Đăng xuất: nhật ký và phương thức | Ở cả hai URLconf: POST `/dang-xuat/` kèm CSRF → 302, có AuditLog LOGOUT đúng người; GET → 405 và phiên còn; POST khi chưa đăng nhập không ghi LOGOUT | QA | HTTP | Tự động | P2 | ADR-030, BR-5 |
| PH-14 | Khoá tạm và sai mật khẩu ở CRM | URLconf CRM: sai 5 lần → khoá; lần 6 đúng vẫn bị từ chối với cùng một lời báo; thiếu CSRF → 403 | QA | HTTP | Tự động | P2 | FR-1.2, AC-1.2 |
| PH-15 | `/doi-mat-khau/` khi chưa đăng nhập | Ở cả hai URLconf: GET → 302 `/dang-nhap/?next=/doi-mat-khau/` | QA | HTTP | Tự động | P1 | AC-1.1 |
| PH-16 | Mở rộng vai cho đăng nhập chung | Thêm CEO, `staff_kt`, CSKH vào tham số `role` của `test_login_identity_and_logout_across_apps` | QA | HTTP | Tự động | P2 | ADR-030, ADR-044 |
| PH-17 | Không lưu đệm trang khi đã đăng nhập | `force_login`, GET `/` và `/nhan-su/` (ERP), `/thu-muc/` (CRM) → `Cache-Control` có no-cache, no-store, must-revalidate, max-age=0; `/static/` không bị gắn header này | Người dùng | HTTP | Tự động | P2 | NFR-4 |
| PH-18 | Bật bài trình duyệt đăng nhập chung trong CI | Đặt `SHARED_LOGIN_BROWSER=1`, `ACCOUNT_BROWSER=1` và thư mục `/evidence` trong job e2e của `.github/workflows/ci.yml`, hoặc ghi lý do không bật | QA | E2E | Tự động | P2 | ADR-030 |
| PH-19 | Kiểm tay trên Staging hai tên miền | Đăng nhập ở ERP, bấm KN CRM thì không phải đăng nhập lại. Đăng xuất ở CRM, F5 ở ERP thì về trang đăng nhập. DevTools: cookie phiên tên đúng `knjsc_session_v2`, cookie CSRF tên `knjsc_csrf_v2` (ADR-030; nếu thấy `sessionid`/`csrftoken` thì `.env` thiếu biến → ghi lỗi, xem PH-21), Domain là tên miền cha, Secure, HttpOnly, Lax. Back rồi Submit form cũ sau khi đăng nhập lại → 403 CSRF, không ghi gì. Để yên 61 phút rồi bấm đúp một ô lưới và bấm Lưu khung chi tiết → về trang đăng nhập, không nhét trang đăng nhập vào ô | Người dùng | E2E thủ công | Thủ công | P1 | ADR-030, AC-1.10, AC-1.11, TL-02, TL-18 |
| PH-20 | Kiểm tay `/quan-tri/` trên Staging | CEO và `sale.manager` mở `/quan-tri/` → trang đăng nhập quản trị, không thấy model. Cửa sổ ẩn danh: 6 lần sai với `quantri` tại `/quan-tri/login/`, xem `/nhat-ky/?hanh_dong=login_failed`. Ghi kết quả vào biên bản `docs/kiem-chung-dien-tap-phat-hanh-staging-20261008.md` mục 11 (hiện chỉ có Staff) | Người dùng | E2E thủ công | Thủ công | P1 | Điều cấm 12, FR-1.2 |
| PH-21 | Tên cookie phiên ở production không rơi về mặc định | (a) Tự động: với `knjsc.settings.prod` (và `bangtinh` khi `BANGTINH_GOC=prod`), khi ERP và CRM ở hai tên miền mà `SESSION_COOKIE_NAME == 'sessionid'` hoặc `CSRF_COOKIE_NAME == 'csrftoken'` thì `check --deploy` phải báo lỗi. Hiện core.E001 chỉ kiểm domain, nên đây là kiểm tra cần thêm, viết bài đỏ trước theo TDD. Mở rộng `core/tests/test_kiem_cau_hinh.py`. (b) Bán tự động trước phát hành: đọc `.env` VPS (không in giá trị bí mật), xác nhận có `SESSION_COOKIE_NAME=knjsc_session_v2`, `CSRF_COOKIE_NAME=knjsc_csrf_v2`. Bổ sung vào bước 0 của `deploy/production/README.md` (hiện chỉ ghi "đủ hai cookie domain"). Đối chiếu với các ca cấu hình nền tảng PLAT-03, PLAT-34 ở phần khác (chưa xác minh nội dung hai mã này trong phần này) | QA | Cấu hình triển khai | Tự động + Bán tự động | P1 | ADR-030, AC-1.11, `app/knjsc/settings/base.py:187-189`, `app/knjsc/settings/prod.py`, `deploy/production/compose.yml`, `config/.env.example` |

---

### 3.3 Tiền và tính toán: kiểm chứng độc lập (oracle)

**Nguyên tắc.** Một bài kiểm số liệu chỉ có giá trị khi con số kỳ vọng được tính bằng một **đường thứ hai, độc lập** với mã đang kiểm. Có ba cách lấy con số kỳ vọng:

- Hằng số viết tay, do người nghiệp vụ xác nhận.
- SQL thô dùng `::numeric` không giới hạn số lẻ.
- Python thuần, dùng `Decimal` hoặc `fractions.Fraction`.

Nhiều bài hiện có đang tự so với chính mình, nên chưa đạt chuẩn này:

- `test_tong_cong_bang_tong_cac_dong_nhom` so tổng của `summarize` với tổng các dòng nhóm của chính `summarize`.
- `test_cot_tinh_san_tinh_lai_tren_tong` dựng kỳ vọng bằng đúng phép `Decimal.quantize` mà mã dùng.
- `integrity_service.lech_cot_tach` tính lại bằng chính `apply_computed_columns` và `sync_indexed_columns`.
- Các oracle hiệu năng có sẵn ở `app/tests/perf/` (`optimization_oracle.py`, `optimization_bulk_oracle.py`) lấy kỳ vọng qua chính `build_grid` hoặc `DataRecord.objects.in_scope` (xem mục 3.3.3).

Ngược lại, `scripts/crm-update-perf/oracle.py` đã gần đạt chuẩn: kỳ vọng tính bằng Python thuần trong bài tải, đọc lại DB không qua `in_scope`, so bằng `Decimal`. Đây là mẫu "đường thứ hai" nên tái dùng thay vì dựng từ đầu (mục 3.3.3).

Mọi ca dưới đây phải tuân thủ điều cấm ở mục 3.3.3.

#### 3.3.1 Kiểm kê các phép tính

Thang rủi ro: Cao / Vừa / Thấp, lấy theo dữ liệu đã được kiểm chứng đối kháng.

| # | Phép tính | Vị trí | Quy tắc cốt lõi | Bài kiểm hiện có | Oracle đề xuất | Rủi ro |
|---|---|---|---|---|---|---|
| T1 | Đọc số người dùng gõ | `app/core/money.py:parse_money`. Được gọi từ `record_service.parse_value`, `order_service._tien`, `waybill_service.money`, `threshold_service.parse` | Bỏ dấu cách và NBSP, bỏ ký hiệu tiền. Có cả chấm lẫn phẩy thì dấu đứng sau là dấu thập phân. Chỉ có phẩy thì phẩy là thập phân. Chỉ có chấm: đúng một chấm và 1–2 chữ số sau thì là thập phân, còn lại là ngăn nghìn. Sau đó khớp regex `\d+(\.\d+)?`, rồi qua `check_amount` | `app/tests/test_hop_trang.py` (vòng `format_money`→`parse_money`, BR-8); `app/core/tests/test_so_va_gio_bien.py` (AC-9.7); `app/forms_builder/tests/test_nhap_hang_loat.py` dòng 110. **Không** có bài cho `0.125`, `12.345`, `'12,345'`, U+202F | CSV bảng chân lý viết tay. Thêm một bộ đọc tham chiếu tối giản viết trong bài kiểm, và kiểm vòng tròn với hàm định dạng độc lập (OR-01, OR-02) | Cao |
| T2 | Chặn số không ghi được | `money.py:check_amount` | Không hữu hạn → `InvalidOperation`. `adjusted() ≥ 16` → `BusinessError`. **Không** giới hạn số chữ số lẻ | `test_so_va_gio_bien.py::test_o_so_qua_dai_bao_loi_tieng_viet` | Đếm chữ số phần nguyên bằng Python thuần. Đối chiếu `SELECT '<v>'::numeric(18,2)` trong giao dịch huỷ | Vừa |
| T3 | Hiển thị tiền theo loại tiền | `money.py:format_money`; `CURRENCY_DECIMALS`, `CURRENCY_SYMBOL` ở `app/core/constants.py` | VND/JPY/KRW không số lẻ, loại khác 2 số lẻ. `quantize` không chỉ định cách làm tròn nên mặc định ROUND_HALF_EVEN. USD đặt ký hiệu trước, loại khác đặt sau | `test_hop_trang.py::test_hien_tien_theo_tung_loai` (AC-9.5) | Bảng kỳ vọng viết tay. Chuỗi kỳ vọng dựng bằng số nguyên (`divmod`), không gọi `format_*` | Vừa |
| T4 | Viết số máy thành số Việt | `money.py:format_decimal`, `threshold_service.hien_so`, bộ lọc `so` ở `app/core/templatetags/knjsc.py`, `forms_builder/styling.py:list_value` | `format_decimal` giữ nguyên số lẻ. `so` làm tròn 2 số lẻ ROUND_HALF_UP (AC-22.27) | `app/reports/tests/test_che_do_so_lieu.py` (AC-46.8); `app/crm/tests/test_thong_ke_cach_viet_so.py` (chưa đọc nội dung) | Vòng tròn: `Decimal` ngẫu nhiên → chuỗi → bộ đọc tham chiếu. Với `so`: `quantize(0.01, ROUND_HALF_UP)` viết tay | Thấp |
| T5 | Quy đổi VND | `money.py:to_vnd`, `vnd_rate`; `settings/base.py:env_rates` | Nhân tỉ giá, `quantize(1, ROUND_HALF_UP)`. Thiếu tỉ giá (KRW) → `BusinessError` | `app/tests/test_ti_gia.py`; `culture/tests/test_van_hoa.py` (chưa đọc chi tiết) | Đặt tỉ giá cố định bằng `override_settings`, kỳ vọng tính tay | Vừa |
| T6 | Ô MONEY/DECIMAL | `forms_builder/services/record_service.py:parse_value` | Số thật: `str(check_amount(Decimal(str(raw))))`. Chuỗi: `parse_money` | `test_hop_trang.py`; `test_nhap_hang_loat.py`; `test_ngay_so_excel.py` (chưa đọc) | Năm đường ghi cùng một giá trị, đọc lại bằng SQL thô `data->>'<mã>'` (OR-03) | Cao |
| T7 | Ô INTEGER | `parse_value` nhánh INTEGER; `app/static/js/report-entry.js:docSo` | Chuỗi: xoá mọi `.`, `,`, dấu cách rồi `int()`. Nhận số âm | Chưa thấy bài cho `'1,5'`, `'1.5'` (đã grep, chưa xác minh hết) | Bảng kỳ vọng tay; `jsonb_typeof(...)='number'` | Cao |
| T8 | Cột tính sẵn theo dòng | `forms_builder/models.py:ColumnDef.compute`, `_to_decimal`; `DataRecord.apply_computed_columns` (ADR-006, ADR-016) | Thiếu toán hạng hoặc chia 0 → None. `quantize` HALF_EVEN nằm **ngoài** `try` | `reports/tests/test_aggregations.py::test_cot_tinh_san_tinh_lai_tren_tong` (tự so với chính công thức); `test_xem_truoc_chi_so.py` (AC-43.6) | Tính bằng `Fraction`. SQL `round(a/NULLIF(b,0), n)` (Postgres làm tròn xa số 0) | Cao |
| T9 | Tính lại cả bảng | `table_service.py:schedule_resync`, `resync_table`, `_giong`; `forms_builder/tasks.py:chay_tac_vu_tinh_lai`; `RECOMPUTE_SYNC_MAX_ROWS=2000` | Tối đa 2000 dòng tính tại chỗ, nhiều hơn chạy nền (`crm_heavy`). Tính cả dòng đã xoá mềm | `orders/tests/test_nang_cap_tinh_lai.py` và `crm/tests/test_bang_tinh_luu_o.py` (cả hai có nhắc TL-22, chưa đọc chi tiết). **TL-23 chưa có bài hồi quy**: grep `TL-23` trong mọi `test_*.py` ra 0 kết quả (khớp mục 8.5). `crm/tests/test_hang_doi_chet.py` chỉ kiểm AC-10.13 (Redis tắt) và AC-10.14 (đĩa đầy), không kiểm job RUNNING bị kẹt | SQL đếm số dòng có cột tính ≠ `round(a/b,n)`, kỳ vọng 0. Thêm bài hồi quy TL-23 (OR-09) | Vừa |
| T10 | Đổi kiểu cột | `table_service.py:_chuyen_kieu` (AC-8.11) | Đưa giá trị đã lưu qua `parse_value` của kiểu mới | `forms_builder/tests/test_doi_kieu_cot.py` (chỉ Chữ→Số nguyên) | Chụp SQL trước khi đổi, rồi `Decimal(chuỗi máy)` từng dòng sau khi đổi: phải bằng nhau hoặc bị từ chối | Cao |
| T11 | Chép sang cột tách `val_revenue` | `models.py:DataRecord.sync_indexed_columns`, `_normalise`; `val_revenue` DecimalField(18,2) | Postgres làm tròn về 2 số lẻ khi lưu, trong khi `data` giữ nguyên | `test_aggregations.py::test_cong_dung_cot_json_va_cot_tach` (chỉ số tròn) | INV-03 | Vừa |
| T12 | Cộng tổng báo cáo theo nhóm | `app/reports/aggregations.py:summarize`, `_sum_exprs`, `totals_from_rows`, `totals_only`, `summarize_in_memory`, `currency_sums_from_rows` | `SUM(Cast(... AS numeric(18,2)))`: làm tròn **từng dòng** rồi mới cộng. Nhóm theo `loai_tien` (ADR-046). `MAX_GROUPS=2000` | `test_aggregations.py` (FR-5.1–5.4, BR-4, AC-5.4, nhưng tự so); `test_che_do_so_lieu.py` (AC-46.9); `test_quy_vnd_va_tt.py`; `test_summary_scope.py` | SQL thô `GROUP BY` với `::numeric`, chạy hai đường (mặc định và ép `MAX_GROUPS=2`) (OR-10) | Cao |
| T13 | Dòng TỔNG CỘNG theo loại tiền | `aggregations.py:with_currency_totals`, `total_rows`, `_total_by_code`; `marketing.py:with_totals` | Mỗi loại tiền một dòng. Có 2 loại tiền trở lên thì tổng chung xoá cột tiền. Nguồn MKT nhiều loại tiền → `mot_tien=''` | `test_che_do_so_lieu.py`, `test_mkt_tien_viet.py` (AC-47.4), `test_mkt_derived_revenue.py` | Hằng số tính tay trên bộ dữ liệu ORACLE-1 (mục 3.3.3) | Cao |
| T14 | Tổng ngày và khối toàn kỳ | `aggregations.py:subtotals`; `layout.py:period_block`, `day_blocks`, `days_block`, `_by_currency` | Cộng `c_*` theo nhóm cha. Mỗi khoá đối soát cộng một lần (`da_cong`). CPO ngày = ΣCPQC ÷ Σđơn | `test_bo_cuc_khoi.py`, `test_tung_lan_nop_mac_dinh.py`, `test_bang_du_lieu_chi_tiet.py` (chưa đọc chi tiết) | SQL `GROUP BY val_date` / người; CPO tính bằng `Fraction` | Cao |
| T15 | Chỉ tiêu công thức BC SALE/MKT | `activity_service.py:FORMULAS`, `project_metrics`, `_formula_format`; `marketing.py:Metric.compute`, `divide` | Mẫu số None hoặc 0 → None. Không `quantize`; làm tròn lúc hiện bằng `format_number` (HALF_EVEN) | `test_activity.py`, `test_mkt_bo_bon_o.py`, `test_mkt_excel.py`, `test_xem_truoc_chi_so.py` | Bảng tay (mess 270, đơn 24, CPQC 500000, DS 3280000) (OR-15) | Cao |
| T16 | Cột (TT) đối soát từ vận đơn | `activity_service.py:marketing_actuals`, `attach_derived`, `_shared_keys` | Đếm `COUNT(DISTINCT vận đơn)`, cộng `SUM(paid_amount)` của chi tiết còn sống. Nguồn MKT bỏ phần tiền (ADR-047). Chỉ gắn vào khoá có dòng báo cáo | `test_mkt_derived_revenue.py`, `test_mkt_tien_viet.py`, `test_quy_vnd_va_tt.py`, `test_nguong_va_loc_san_pham.py` (AC-42.11) | SQL JOIN bảng phân công `orders_waybillassignment` (model `WaybillAssignment`, `app/orders/models.py:28`; nối `record_id` một-một với dòng vận đơn, người MKT ở FK `marketing`) rồi giao với tập (ngày, người) bằng Python | Cao |
| T17 | Báo cáo Vận đơn theo trạng thái | `activity_service.py:delivery`, `shipping_status`, `status_expression` | `COUNT(DISTINCT pk)`; `SUM(quantity)` của chi tiết còn sống | `test_delivery_daily.py` (AC-22.14) | SQL `GROUP BY COALESCE(NULLIF(trang_thai_vc,''),'Chưa xác định')` | Vừa |
| T18 | Tính chỉ số khi nộp/sửa báo cáo ngày | `daily_service.py:compute_report`, `amend`, `preview_columns`; `views.py:_gia_tri_dang_luu` | MKT ghi đè bằng `Metric`, HALF_EVEN chỉ ở kết quả cuối. `amend` giữ ô không gửi dưới dạng `Decimal` | `test_report_amendments.py`, `test_admin_sua_tong_hop.py` (ADR-050), `test_o_nhap_so_e2e.py` (AC-46.10) | SQL so chuỗi `data->>…` trước và sau khi sửa | Vừa |
| T19 | Loại tiền theo quốc gia | `orders/services/currency_service.py:report_currency`, `for_market`, `change`; `daily_service.protected_values` | MKT luôn VND (ADR-047). Sale theo `MARKET_CURRENCIES` (ADR-031). Đổi quốc gia giữ nguyên số (ADR-046) | `test_markets_currencies.py`, `test_mkt_tien_viet.py` (AC-47.1–47.3), `crm/tests/test_market_currency*.py` | Bảng tay 7 thị trường; SQL so từng ký tự trước và sau | Vừa |
| T20 | Ô số trên form (JS) | `report-entry.js: docSo, vietSo, chuanHoa, lamTron, tinh, xemTruoc` | Mô phỏng `parse_money`. Xem trước tính bằng `Number`, nửa về chẵn với dung sai 1e-9 | `test_o_nhap_so_e2e.py` (AC-46.10), `test_xem_truoc_chi_so.py` (AC-43.6) | Playwright gõ theo bảng chân lý, so `input.value` với SQL thô (OR-31) | Vừa |
| T21 | Tiền vận đơn | `waybill_service.py:money`, `validate_items`, `totals`, `prepare_values`, `update_items` | Tiền ≥0, tối đa 2 số lẻ. `gia_tien = Σ quantity×unit_price`, `so_tien_tt = Σ paid_amount`. Trạng thái: Chưa TT / TT một phần / Đã TT | `crm/tests/test_waybill_new.py`, `test_xoa_chi_tiet_san_pham.py`; `orders/tests/test_nap_du_lieu_van_don.py`, `test_len_don.py` | INV-04 | Cao |
| T22 | Thống kê vận đơn CRM theo loại tiền | `waybill_service.py:statistics*`, `executive_snapshot`; `crm/services/statistics_profiles.py:build_waybill` | `GROUPING SETS` trong một CTE, trần 2000 nhóm | `test_executive_statistics*.py`, `test_thong_ke_lien_ket_nguon.py` | SQL đơn giản, mỗi chiều một truy vấn | Vừa |
| T23 | Thống kê CRM Marketing/Sale/chung | `statistics_profiles.py:build_*`, `_decimal_expr`, `previous_range`, `period_granularity`; `statistics_insights.py`; `statistics_service.py:chart`, `build_overview` | Cast `numeric(18,2)`. Kỳ trước cùng độ dài. Đến 45 ngày xem theo ngày, đến 180 theo tuần, còn lại theo tháng. Có tính % | `test_thong_ke_cach_viet_so.py`, `test_thong_ke_mkt_bo_san_pham.py`, `test_statistics_labels_browser.py` | SQL `::numeric`; % tính bằng `Fraction` | Vừa |
| T24 | Đơn hàng | `order_service.py:_tien`, `create_order`; `orders/models.py:OrderLine.line_total`, `Order.recalculate_total` (BR-3) | `total = Σ unit_price×quantity` | `test_len_don.py`, `test_order_code_concurrency.py`, `crm/tests/test_len_don_mot_lan.py` | INV-05 | Vừa |
| T25 | Bảng xếp hạng và sao | `culture/services/leaderboard_service.py:sales_leaderboard`, `month_range`, `award_monthly_stars`; `recognition_service.competition_rank` (ADR-017) | Nhóm (người bán, loại tiền) → `to_vnd` (HALF_UP) → cộng theo người. Đồng hạng xếp 1,1,3. Sao 5/3/1 | `culture/tests/test_van_hoa.py` (chưa đọc chi tiết) | SQL theo mốc tháng giờ Asia/Ho_Chi_Minh tính tay, xếp hạng bằng `sorted()` | Vừa |
| T26 | Nhập/xuất Excel và CSV | `core/excel.py:coerce_cell`, `_doc_xlsx`, `_doc_csv`, `_o_csv`; `export_service.cell_value`; `reports/excel.py:build_workbook` | Ô CSV và ô chữ của xlsx đi qua `parse_money`. Xuất ra số thô của `Metric` (28 chữ số) | `core/tests/test_excel.py`; `test_nhap_xuat.py`, `test_ngay_so_excel.py`, `test_xuat_khong_cong_thuc.py`; `test_mkt_excel.py` | Tệp mẫu cam kết vào kho, `openpyxl` đọc lại rồi so SQL (OR-26) | Cao |
| T27 | Ngưỡng màu | `threshold_service.parse`; `aggregations.py:cell_class`, `_format_cells`, `_moc` | Ba bậc màu. Ngưỡng tiền chỉ áp cho dòng VND. Không có ngưỡng thì so ±10 % với dòng Tổng | `test_nguong_va_loc_san_pham.py` (AC-42.8), `test_che_do_so_lieu.py` (AC-46.6) | Bảng quyết định viết tay | Vừa |
| T28 | Tỉ trọng, `format_number`, đường cũ | `aggregations.py:_cell_values`, `format_number`; `summary_service.py:_headline`, `_compare`, `build_context`; `dashboard_service.py:_marketing` | Tỉ trọng `quantize` 1 số lẻ HALF_EVEN. `build_context` cộng không tách loại tiền | `test_aggregations.py::test_nhom_theo_san_pham_co_ti_trong`, `test_dinh_dang_so_kieu_viet_nam` | `Fraction`; SQL `GROUP BY loai_tien` để chứng minh có cộng lẫn | Thấp |
| T29 | Lọc khoảng số | `forms_builder/query.py:build`, `_ep_kieu_json`, `read_filters`; `JSON_RANGE_TYPES` | Cột tiền nằm trong JSON bị đổi thành so bằng. `val_revenue` sai kiểu thì bộ lọc bị bỏ lặng lẽ | `test_loc_sai_kieu.py` (AC-10.16, chưa đọc chi tiết) | SQL `WHERE (data->>'cpqc')::numeric >= 100` | Vừa |
| T30 | Rà toàn vẹn số liệu, cột `sl_*` | `orders/services/integrity_service.py`; lệnh `kiem_tra_du_lieu`; `crm/services/grid_service.py:product_any_of` | Tính lại bằng chính hàm của hệ thống, không độc lập | `orders/tests/test_kiem_tra_du_lieu.py` | INV-08, INV-03 | Thấp |

#### 3.3.2 Bộ giá trị biên dùng chung

Đặt một tệp CSV duy nhất trong thư mục oracle (mục 3.3.3). Mọi ca OR-xx đọc lại từ tệp này. Cột "Hiện tại" lấy từ việc đọc mã, **chưa chạy**. Cột "Kỳ vọng" ghi "Chốt Dx" nghĩa là chờ chủ dự án quyết định (mục 3.3.7).

| Giá trị vào | Áp cho | Hiện tại (đọc mã) | Kỳ vọng |
|---|---|---|---|
| `''`, `'   '` | T1, T6, T7 | None | None |
| `'0'`, `'-0'` | T1 | 0; `'-0'` → `Decimal('-0')` (đã đọc `parse_money`: `-so`) | 0, phải bằng 0 về giá trị |
| `'-500'`, `'-5'` | T1, T6, T7, T18 | Nhận | Chốt D4 |
| `'0.125'` (chuỗi máy) | T1, T6, T10, T21, T24, T26, T20 | 125 (TL-03) | Chốt D1: 0,125 hoặc từ chối |
| `'12.345'`, `'1.2345'`, `'1.234.5'` | T1 | 12345 | Chốt D1 |
| `'1.234'` | T1 | 1234 (chủ ý, đã chốt trong `test_so_va_gio_bien.py`) | 1234 |
| `'1.234,56'`, `'1.234,56 ₫'` | T1 | 1234.56 | 1234.56 |
| `'12,345'` (CSV từ Excel tiếng Anh) | T1, T26 | 12.345 (chia 1000) | Chốt D9 |
| `'13 250 000'` (dấu cách / NBSP) | T1, T20 | 13250000 | 13250000 |
| `'13 250 000'` với U+202F hoặc tab | T1, T20 | Máy chủ từ chối, JS nhận | Hai phía phải xử lý giống nhau |
| `'150.00'` | T1 | 150.00 | 150.00 |
| `'1,5'`, `'1.5'` vào ô INTEGER | T7, T20 | 15 | Chốt D5 |
| xlsx 3.0 / 3.5 vào ô INTEGER | T7 | 3 / lỗi | 3 / lỗi |
| `9999999999999999.99` | T2, T21 | Nhận | Nhận |
| `9999999999999999.995` | T2, T11 | Python nhận, Postgres tràn `numeric(18,2)` | Bị chặn trước khi lưu |
| `10000000000000000` | T2 | `BusinessError` | `BusinessError` |
| `'1e5'`, `'NaN'`, `'Infinity'`, `'0x10'`, `'A$100'` | T1 | `InvalidOperation` | Từ chối bằng lời báo tiếng Việt |
| xlsx `1e-07` / `'0,0000001'` | T6, T18 | Lưu `'1E-7'` | Chốt D3 |
| xlsx `0.1+0.2` | T6 | `'0.30000000000000004'` | Chốt D3 |
| 0,005 × 3 dòng | T12, T23 | Tổng 0,03 | 0,015 hoặc từ chối 3 số lẻ (Chốt D3) |
| 0,125 hiển thị 2 số lẻ | T3, T4, T15, T28 | `'0,12'` ở ERP, `'0,13'` ở `so` / Excel | Chốt D2 |
| 2,5 VND / 0,5 VND / -0,4 VND | T3 | `'2 ₫'` / `'0 ₫'` / `'0 ₫'` (đã đọc: không có dấu âm) | Chốt D2 |
| 1234.56 CAD | T3 | `'1.234,56 '` (dấu cách thừa) | `'1.234,56'` hoặc kèm mã CAD |
| 1500,50 JPY/KRW | T3, T24 | Lưu có phần lẻ, hiện `'1.500 ¥'` | Chốt D6 |
| Mẫu số 0 hoặc trống | T8, T15, T23, T27 | None / để trống | None / để trống |
| 1e15 × 1e15; `compute_decimals=30` | T8 | `InvalidOperation` không bắt (500) | Báo lỗi tiếng Việt, không 500 |
| Đúng 2000 / 2001 dòng hoặc nhóm | T9, T12, T22 | Tại chỗ / chạy nền; trần | Hai đường cho cùng số |
| 45/46 và 180/181 ngày | T23 | Đổi độ hạt | Theo quy tắc |
| 23:59 ngày 30.09 giờ VN (16:59 UTC) và 00:00 ngày 01.10 | T25 | Chưa có bài | Rơi đúng tháng |
| paid = 0, paid < price, paid = price, paid > price | T21 | Chưa TT / TT một phần / Đã TT / Đã TT | Bốn trạng thái đúng; trả thừa: chưa chốt |
| Một đơn KRW trong tháng | T5, T25 | Cả bảng xếp hạng lỗi | Chốt D7 |

#### 3.3.3 Thiết kế khung oracle

**Oracle đã có trong kho (tái dùng, mở rộng).** Kho đã có hai nhóm oracle và cổng đối chiếu: ở `app/tests/perf/` và ở `scripts/crm-update-perf/`, `scripts/grid-flags-check/`. Tất cả phục vụ đo hiệu năng, chạy tay trên DB riêng, **không có trong CI** (grep `crm-update-perf`, `grid-flags-check` trong `.github/workflows/ci.yml` ra 0 kết quả). Mức độc lập khác nhau:

| Tệp | Đang làm gì | Mức độc lập | Cách tái dùng |
|---|---|---|---|
| `app/tests/perf/optimization_oracle.py` | Trước mỗi lượt đo, đóng băng bằng ORM vào manifest JSON: `total` (= `qs.count()`, là **số dòng**, không phải tổng tiền), ID các trang 100 dòng, 2000 ID cho sửa hàng loạt, tập lọc `f_quoc_gia=USA`. Có chặn nhầm DB (`assert manifest['database']==os.environ['POSTGRES_DB']`) | Chưa độc lập: lấy kỳ vọng qua chính `crm.services.grid_service.build_grid`, tức mã đang kiểm. Chỉ bắt được thay đổi hồi quy *trước/sau tối ưu*, không bắt được lỗi có sẵn trong `build_grid` (sai phạm vi, sai lọc). Không có số tiền | Giữ mẫu "đóng băng manifest rồi so". Thêm đường thứ hai bằng SQL thô (`deleted_at IS NULL`, điều kiện phạm vi viết tay) chạy song song với `build_grid`; hai đường phải ra cùng tập ID và cùng số dòng |
| `app/tests/perf/optimization_bulk_oracle.py` | Chọn 2000 ID cuối bảng (`offset=298000`) không trùng ô đang sửa, ghi vào manifest. Chặn DB bằng `assert connection.settings_dict['NAME']=='test_knjsc_opt_after300'` | Chưa độc lập: lấy ID qua `DataRecord.objects.in_scope`, tức Custom Manager phạm vi đang kiểm. Chỉ chọn đích, không tính số liệu | Giữ cách chặn tên DB cho oracle chạy trên bản sao DB (mục 3.3.4). Không dùng làm nguồn kỳ vọng |
| `app/tests/perf/erp_integrity.py` | Đối chiếu số lần nộp của Locust với DB `knjsc_erp_verify`; khẳng định hằng số 100000 dòng, 60000 báo cáo, 80000 chi tiết, ΣSL = 120000 | Gần độc lập (hằng số viết tay), nhưng tổng lấy bằng ORM `Sum('quantity')`, không có tiền | Mẫu hằng số viết tay cho bộ dữ liệu lớn; chuyển `Sum` sang SQL thô khi đưa vào oracle |
| `scripts/crm-update-perf/oracle.py` | Docstring "Đối chiếu độc lập xác nhận HTTP với PostgreSQL của bài tải". Đọc `expected` trong tệp `LOAD_RESULT` do `locustfile.py` ghi (dòng sửa, dòng tạo mới, `ghi_chu`; CPO kỳ vọng tính bằng `str(Decimal(cost)/5)` ngay trong Python). Đọc lại `DataRecord.objects.filter(pk__in=…)` (không qua `in_scope`), so `table.code`, `created_by_id`, và so `cpqc`/`cpo`/`so_don` bằng `Decimal`. Chặn nhầm DB: `assert HOST=='knjsc-crm-update-db'`, `NAME.startswith('test_crm_update_load_')`. Ghi kết quả ra `.oracle.json` | **Gần đạt chuẩn**: kỳ vọng tính bằng Python thuần, độc lập với `ColumnDef.compute`. Hạn chế: CPQC chỉ là số nguyên kèm `.00` (`random.randrange(1,10000)`), công thức chia 5 cố định, đọc DB qua ORM chứ không SQL thô | Mẫu gốc cho "đường thứ hai" (luồng ở dưới). Mở rộng: CPQC có số lẻ khó (0,125; 1/3), đọc bằng SQL thô `data->>'cpo'` (OR-38) |
| `scripts/crm-update-perf/check_matrix.py` | Cổng tổng hợp: ghi `storage/crm-update/matrix-gate.json` với `passed: False` trước, rồi duyệt 100000/300000 dòng × 10/20 người. Khẳng định `measured==300`, `warmup==60`, `integrity_errors` và `oracle['errors']` rỗng, `oracle['checked']==users`, mọi mẫu HTTP 200, đủ mẫu cho từng nhóm (marketing, sale, van-don) × thao tác, kèm p95 | Không tự tính số liệu, chỉ gom bằng chứng của `oracle.py` | Mẫu cổng "đặt trượt trước, chỉ đạt khi mọi bằng chứng đạt" cho OR-33 |
| `scripts/crm-update-perf/check_endurance.py` | Như trên cho bài bền: `final-endurance-after-300000-20.json` cùng `.oracle.json`, `measured==1800`, cộng bằng chứng Chrome (`endurance-browser.json`) và Celery (`background.json`); ghi `endurance-gate.json` | Như trên | Như trên |
| `scripts/grid-flags-check/contract.py` | So JSON `/bang-tinh/van_don/du-lieu/` giữa các cờ `CRM_OPT_*` (off/render/read/sync) với bản tham chiếu khi tắt cờ: `capabilities`, `schema_version`, `total`, `columns`, thứ tự ID; với `sync` thì thêm POST `dong-bo/` không được `reset`. Vai admin và Vận đơn. Chặn DB `NAME=='test_knjsc_gridflags_load'`, `HOST=='knjsc-gridflags-db'` | Đối chiếu chéo giữa hai đường của cùng một view; chuẩn so là chính lưới khi tắt cờ, không độc lập về phạm vi | Mẫu "hai đường cùng ra một tập ID" cho OR-37 |
| `scripts/grid-flags-check/invalidation_audit.py` | Tạo đơn mới bằng `order_service.create_order` ngoài phạm vi một nhân viên Vận đơn, rồi kiểm token cũ (protocol 1 và 2) và `total`, ID khối đầu không đổi. Chặn DB như trên | Dùng `in_scope` để khẳng định đơn nằm ngoài phạm vi, nên không độc lập về phạm vi | Mẫu ca "thay đổi ngoài phạm vi không làm đổi tập" cho OR-37 |
| `scripts/grid-flags-check/acceptance.py` | Chỉ là kịch bản điều phối: chờ `results/final-before-delivery-integrity.json`, khẳng định `errors` rỗng, `measured_seconds >= 300`, không `abort`, rồi chạy các lượt after/mixed/sync. Tệp integrity sinh ở đâu: chưa xác minh | Không tính kỳ vọng | Mẫu cổng tuần tự |

**Cấu trúc mới đề xuất** (thư mục `app/tests/oracle/` chưa tồn tại, cần tạo khi thực hiện; dùng lại mẫu manifest, cách chặn tên DB và cách tính kỳ vọng thuần Python của `scripts/crm-update-perf/oracle.py` ở trên):

| Thành phần | Đường dẫn đề xuất | Nội dung |
|---|---|---|
| Bảng chân lý | `app/tests/oracle/du_lieu/bang_chan_ly_so.csv` | Các cột `chuoi_vao, kieu_cot, ky_vong, nguon_xac_nhan`. Người nghiệp vụ điền và xác nhận, **không sinh bằng code** |
| Bộ dữ liệu biết trước | `app/tests/oracle/du_lieu/oracle1.py` (dựng bằng ORM) + `ky_vong_oracle1.py` (hằng số viết tay) | Xem bảng ngay dưới |
| Tệp mẫu nhập | `app/tests/oracle/du_lieu/mau_tien.xlsx`, `mau_tien.csv` | Cùng giá trị, có cả ô số và ô chữ |
| Đường thứ hai | `app/tests/oracle/sql_tho.py`, `tham_chieu.py` | SQL thô qua `connection.cursor()`; bộ đọc và bộ viết số Việt tối giản; làm tròn bằng `Fraction` |
| Bất biến | `app/tests/oracle/test_bat_bien.py` (dấu `cham`) + một tệp SQL chỉ đọc dùng cho bản sao DB | INV-01…INV-13 |
| Đối chiếu lưới | Mở rộng `optimization_oracle.py` hoặc thêm `app/tests/oracle/test_luoi_sql_tho.py` | Tập ID và số dòng của `build_grid` so với SQL thô viết tay, theo từng vai |
| Kiểm meta | `app/tests/oracle/test_khong_dung_lai.py` | OR-34 |

**Bộ dữ liệu ORACLE-1.** Nhỏ, đủ để tính tay; mọi giá trị kỳ vọng ghi thành hằng số.

| Chiều | Thành phần |
|---|---|
| Tổ chức | 2 team MKT (A, B), 1 team Sale, 1 nhân sự "Chưa có team"; Leader và Manager mỗi bộ phận, Kế toán, CEO, Admin. Có thể dùng fixture `teams` ở `app/conftest.py` (lưu ý mỗi Leader chỉ một team) |
| Thời gian | Kỳ 28.09–03.10.2026, cắt qua cuối tháng 30.09→01.10. Riêng T25 thêm cặp 31.12→01.01. Có một ngày chỉ có vận đơn mà không có báo cáo |
| Loại tiền | VND, USD, CAD, EUR, KRW, JPY và `''` (Chưa rõ). Một người có dòng ở hai loại tiền trong cùng một ngày |
| Xoá mềm | Mỗi ngày ít nhất một dòng xoá mềm, mang giá trị dễ nhận (999.999.999) để nếu lọt vào tổng thì lộ ngay. Có chi tiết vận đơn xoá mềm, Order xoá mềm |
| Giá trị khó | 0,005 × 3; 0,125; 1/8; 500000/24; CPQC âm; Số đơn 0; Mess 0; số đơn lớn hơn số mess |
| Vận đơn | Có và không có chi tiết (ADR-036); chưa phân công MKT (không có dòng `WaybillAssignment` hoặc `marketing` trống); đơn USD của marketer MKT; đơn có 2 sản phẩm được lọc; trạng thái trống |
| Nộp báo cáo | Một người nộp 3 lần một ngày (`derived_shared`) |
| Quy mô lớn | Biến thể ORACLE-1L: 2001 dòng (đường nền T9) và ép `MAX_GROUPS=2` như AC-46.9, thay vì dựng 2001 nhóm thật |

**Luồng mỗi ca:**

1. Dựng dữ liệu.
2. Lấy kỳ vọng từ hằng số viết tay, hoặc từ SQL thô / Decimal thuần.
3. Lấy đầu ra qua ba kênh:
   - HTML: client test + `html.parser` có sẵn trong Python, đọc chuỗi rồi chuyển về số bằng bộ đọc tham chiếu.
   - JSON của lưới và Thống kê CRM.
   - Excel: `openpyxl`, thư viện đã có trong dự án.
4. So sánh theo luật trong bảng dưới.

| Loại số | Luật so |
|---|---|
| Tổng cộng, số đếm, tiền lưu | Bằng tuyệt đối, so `Decimal`; không có dung sai |
| Chỉ tiêu đã làm tròn trên màn hình | `Fraction` → làm tròn theo luật đã chốt (D2) → so chuỗi |
| Excel ghi số thô của `Metric` | Làm tròn ROUND_HALF_EVEN tay phải ra đúng chữ trên màn hình. Excel chỉ giữ 15 chữ số có nghĩa, nên cần so riêng các số trên 15 chữ số |
| % biểu đồ, tỉ trọng | Từng mục bằng kỳ vọng; tổng các mục = 100 ± 0,1 × số nhóm |

**Điều cấm (bắt buộc).** Mã tính kỳ vọng trong `app/tests/oracle/` không được import hoặc gọi các thành phần sau:

- `parse_money`, `format_money`, `format_decimal`, `format_number`, `to_vnd`, bộ lọc `so`, `hien_so`
- `ColumnDef.compute`, `apply_computed_columns`, `sync_indexed_columns`
- `summarize`, `totals_*`, `with_currency_totals`, `subtotals`, `Metric`, `divide`
- `integrity_service.*`, `statistics_*`
- `build_grid`, `in_scope` (chỉ được gọi ở phía "đầu ra cần kiểm", không được dùng để dựng kỳ vọng; đây là lý do các oracle ở `app/tests/perf/` và `scripts/grid-flags-check/invalidation_audit.py` chưa đạt chuẩn)
- Biểu thức Cast `numeric(18,2)`

SQL của oracle phải dùng `::numeric` không giới hạn số lẻ và luôn có `deleted_at IS NULL`. Tên bảng mặc định là `forms_builder_datarecord`, `orders_order`, `orders_orderline`, `orders_waybillitem`, và bảng phân công `orders_waybillassignment` (model `WaybillAssignment`, `app/orders/models.py:28`, đã đọc model: `record` một-một, FK `delivery`, `care`, `marketing`, cột `version`). Tên cột (`created_by_id`, `record_id`, `seller_id`, `marketing_id`…) suy theo quy ước Django, phải kiểm lại bằng `sqlmigrate` hoặc đọc model trước khi chạy.

#### 3.3.4 Khẳng định bất biến chạy định kỳ

Chạy ở ba nơi:

- **CI:** trên ORACLE-1, dấu `cham`.
- **Hằng đêm hoặc trước phát hành:** trên bản sao DB Staging, chỉ đọc qua `psql`. Script phải chặn nhầm DB theo kiểu `optimization_bulk_oracle.py` hoặc `scripts/crm-update-perf/oracle.py` (khẳng định tên DB, và cả HOST, trước khi chạy). Cổng tổng hợp theo mẫu `check_matrix.py`: ghi trạng thái trượt trước, chỉ chuyển đạt khi mọi bất biến đạt.
- **Lệnh vận hành:** có thể bổ sung vào `kiem_tra_du_lieu`. Lệnh này là cổng phát hành (thoát mã 1), nên INV-03 và INV-12 sẽ đỏ mãi cho tới khi chốt D1/D3. Vì vậy hai bất biến này chỉ nên báo cáo, chưa nên chặn phát hành.

| Mã | Khẳng định | Cách đo độc lập | Kỳ vọng |
|---|---|---|---|
| INV-01 | Tổng mỗi loại tiền ở Báo cáo tổng hợp bằng tổng thô trong DB cùng kỳ | `SELECT COALESCE(data->>'loai_tien',''), COUNT(*), SUM((data->>'<cột>')::numeric) FROM forms_builder_datarecord WHERE table_id=%s AND deleted_at IS NULL AND val_date BETWEEN %s AND %s GROUP BY 1`, so với dòng TỔNG CỘNG | Bằng tuyệt đối. Nếu lệch, liệt kê các dòng có hơn 2 số lẻ (nguồn chênh từ T12) |
| INV-02 | Số dòng của báo cáo bằng `COUNT(*)` các dòng còn sống | Như trên | Bằng nhau |
| INV-03 | `val_revenue` khớp cột mang nhãn Doanh thu | `WHERE (data->>'<cột>')::numeric IS DISTINCT FROM val_revenue AND deleted_at IS NULL` | Rỗng |
| INV-04 | Tiền vận đơn khớp chi tiết | JOIN `orders_waybillitem` (còn sống), `GROUP BY r.id HAVING (data->>'gia_tien')::numeric <> SUM(quantity*unit_price) OR (data->>'so_tien_tt')::numeric <> SUM(paid_amount)` | Rỗng |
| INV-05 | Order.total bằng tổng các dòng đơn | `orders_order` JOIN `orders_orderline`, `HAVING o.total <> SUM(l.quantity*l.unit_price)` | Rỗng |
| INV-06 | Cột tính sẵn đúng công thức | Số dòng có `data->>'cpo'` ≠ `round((data->>'cpqc')::numeric/NULLIF((data->>'so_don')::numeric,0),4)` | 0, trừ chênh do làm tròn (liệt kê riêng tới khi chốt D2) |
| INV-07 | Không cộng lẫn loại tiền | Số dòng TỔNG CỘNG bằng số loại tiền phân biệt (INV-01). Tổng chung có cột tiền None khi có 2 loại tiền trở lên | Đúng |
| INV-08 | `sl_*` khớp chi tiết | `(data->>'sl_X')::int` so với `SUM(i.quantity)` theo record và mã sản phẩm | Hiện chỉ báo cáo vì `sl_*` không được giữ theo Chi tiết (theo `integrity_service`) |
| INV-09 | Tổng Số đơn (TT) bằng số vận đơn đã gắn | SQL `COUNT(DISTINCT r.id)` từ `forms_builder_datarecord` JOIN `orders_waybillassignment` (theo `marketing_id`), giao với tập (ngày, người) có báo cáo | Bằng nhau |
| INV-10 | Thống kê vận đơn CRM khớp SQL | Mỗi chiều một `GROUP BY NULLIF(data->>'loai_tien','')` | Bằng nhau |
| INV-11 | Ô tiền JSON đều là số máy hợp lệ | `WHERE data->>'<cột>' !~ '^-?\d+(\.\d+)?$'`: bắt `'1E-7'` và chuỗi rác (gây `DataError` ở Cast) | Rỗng |
| INV-12 | Không có tiền hơn 2 số lẻ | `WHERE data->>'<cột tiền>' ~ '\.\d{3,}$'` | Rỗng (nguồn của T11, T12) |
| INV-13 | Ô INTEGER là số nguyên | `jsonb_typeof(data->'so_mess')<>'number' OR (data->>'so_mess')::numeric % 1 <> 0` | Rỗng |

#### 3.3.5 Kiểm thử dựa thuộc tính

- **Tuỳ chọn có thư viện:** `hypothesis` là thư viện mới. Theo quy tắc 8, cần chủ dự án duyệt trước khi thêm vào `requirements`. Chưa được duyệt thì không dùng.
- **Cách không cần thư viện mới (mặc định):** dùng `random.Random(seed)` với seed cố định ghi trong bài, lặp khoảng 2.000 vòng, và in seed cùng giá trị khi hỏng để chạy lại được. Ba thuộc tính:
  1. Lấy `d` ngẫu nhiên (0–16 chữ số phần nguyên, 0–2 số lẻ). Viết `d` bằng hàm viết số Việt trong `tham_chieu.py`. `parse_money(chuỗi) == d`.
  2. `format_decimal(d)` đọc lại bằng bộ đọc tham chiếu phải ra `d` (0–6 số lẻ).
  3. Tổng `Decimal` trên danh sách dòng ngẫu nhiên phải bằng tổng của báo cáo.
- Bổ sung bằng **sinh tổ hợp có hệ thống**: lấy tích Descartes của {dấu, nhóm nghìn, dấu thập phân, số chữ số lẻ, ký hiệu tiền, loại khoảng trắng}, dùng `itertools.product`.

#### 3.3.6 Ca kiểm

Viết tắt: Tự = Tự động (CI); Bán = Bán tự động (chạy tay qua script hoặc lệnh); Tay = Thủ công (Chặng 2). Các ca phụ thuộc quyết định Dx dùng `pytest.mark.xfail(strict=True)` cho tới khi chốt.

| Mã | Ca kiểm | Góc nhìn | Loại | Cách chạy | Ưu tiên | Truy vết |
|---|---|---|---|---|---|---|
| OR-01 | `parse_money` theo bảng chân lý CSV (mục 3.3.2) | QA | Đơn vị | Tự | P0 | BR-8, AC-9.7, TL-03 |
| OR-02 | Vòng tròn Decimal → chuỗi Việt → `parse_money` (mục 3.3.5) | QA | Thuộc tính | Tự | P1 | BR-8 |
| OR-03 | Cùng giá trị 0,125 / 1234,5678 qua năm đường ghi (lưu ô lưới CRM, nộp form, xlsx ô số, xlsx ô chữ, CSV), đọc lại bằng SQL thô | QA | Tích hợp | Tự | P0 | TL-03, D1, D3 |
| OR-04 | Lưới CRM: ô tiền chứa `'0.125'` → Enter không sửa, dán, kéo điền, hoàn tác → giá trị và nhật ký không đổi | Người dùng | E2E `trinh_duyet` | Tự + Tay | P0 | TL-03, BR-6 |
| OR-05 | Đổi kiểu DECIMAL→MONEY, MONEY→INTEGER, TEXT→MONEY, INTEGER→MONEY, kể cả dòng xoá mềm: so từng dòng | QA | Tích hợp | Tự | P0 | AC-8.11, BR-4 |
| OR-06 | Ô INTEGER `'1,5'`, `'1.5'`, `'-5'` trên form, lưới, CSV và JS | Người dùng | Tích hợp + E2E | Tự | P1 | D4, D5 |
| OR-07 | Cột tính sẵn so với `Fraction`: chia 0, toán hạng trống, 1/8, -1/3, percent 24/270 | QA | Đơn vị | Tự | P1 | ADR-006, ADR-016, D2 |
| OR-08 | Cột tính sẵn tràn (1e15×1e15, `compute_decimals=30`, `'Infinity'` trong JSON cũ) không ra 500 | QA | Đơn vị + HTTP | Tự | P1 | ADR-016 |
| OR-09 | Tính lại 2000/2001 dòng (đường nền chạy eager), đổi `compute_decimals` 4→2, đổi nhãn Doanh thu → INV-06 = 0. Đây sẽ là bài hồi quy đầu tiên cho TL-23 (hiện chưa có) | QA | Tích hợp | Tự (`cham`) | P1 | TL-22, TL-23 |
| OR-10 | Báo cáo tổng hợp trên ORACLE-1: tổng theo loại tiền khớp SQL thô, cả đường mặc định lẫn đường `MAX_GROUPS=2` | QA | Tích hợp | Tự | P0 | ADR-046, AC-5.4, AC-46.9, BR-4 |
| OR-11 | Ba dòng 0,005: tổng báo cáo so với tổng thô | QA | Tích hợp | Tự (xfail) | P1 | D3 |
| OR-12 | Dòng TỔNG CỘNG với USD+EUR, VND+Chưa rõ, KRW/JPY: tổng chung có cột tiền None, cột đếm bằng `COUNT(*)` | QA | Tích hợp | Tự | P0 | ADR-046, BR-8 |
| OR-13 | MKT lẫn loại tiền: (TT) không biến mất, không dồn vào Chưa rõ, không đếm đôi ở khối toàn kỳ | QA | Tích hợp | Tự | P1 | ADR-047, AC-47.4 |
| OR-14 | Tổng ngày và khối toàn kỳ: CPO = ΣCPQC÷Σđơn; nộp 3 lần một ngày; "Chưa có team"; Số đơn 0 | QA | Tích hợp | Tự | P1 | — |
| OR-15 | Chỉ tiêu công thức trên bộ tay (Tỉ lệ chốt 8,89 %, CPO 20.833,33, Giá Mess 1.851,85, CPQC/DS 0,1524, AOV 136.666,67) ở màn hình và Excel | Người dùng | Tích hợp + Excel | Tự | P0 | AC-43.6, D2 |
| OR-16 | (TT) từ vận đơn: chưa phân công, xoá mềm, chi tiết xoá mềm, đơn không có chi tiết, đơn USD của MKT, lọc 2 sản phẩm; kỳ vọng từ SQL JOIN `orders_waybillassignment` | QA | Tích hợp | Tự | P0 | ADR-036, ADR-047, AC-42.11 |
| OR-17 | Báo cáo Vận đơn: số đơn và số lượng theo trạng thái, trạng thái trống | QA | Tích hợp | Tự | P1 | AC-22.14 |
| OR-18 | Tiền vận đơn: 4 trạng thái thanh toán; 200/201 chi tiết; đơn giá `'0.125'`; vòng xuất/nhập 12,50 | Người dùng + QA | Tích hợp HTTP | Tự | P0 | TL-03 |
| OR-19 | Thống kê vận đơn CRM khớp SQL từng chiều; `loai_tien` `''` và thiếu khoá vào cùng nhóm | QA | Tích hợp | Tự | P1 | ADR-046 |
| OR-20 | Thống kê CRM: kỳ trước bằng 0, độ hạt 45/46 và 180/181 ngày, % biểu đồ, chữ "Chênh lệch … đơn" | Người dùng | Đơn vị + Tích hợp | Tự | P2 | AC-22.27 |
| OR-21 | Đơn hàng: INV-05; đơn giá `'1,255'`, số lượng `'1.5'` không ra 500; 1000 dòng × 0,01 | QA | Tích hợp HTTP | Tự | P1 | BR-3, AC-9.5 |
| OR-22 | Bảng xếp hạng: mốc tháng giờ VN, tổng .5 làm tròn HALF_UP, đồng hạng 1,1,3, đơn KRW, chạy thưởng 2 lần, người bị khoá | QA | Tích hợp | Tự | P1 | ADR-017, D7 |
| OR-23 | `to_vnd` theo bảng tỉ giá cố định; `env_rates` sai định dạng | QA | Đơn vị | Tự | P2 | — |
| OR-24 | `format_money` theo bảng tay 8 loại tiền (dấu cách thừa ở CAD/PHP/AUD, HALF_EVEN) | Người dùng | Đơn vị | Tự | P2 | AC-9.5, D2 |
| OR-25 | Vòng tròn `format_decimal` / `so` / `hien_so` | QA | Thuộc tính | Tự | P2 | AC-46.8, AC-22.27 |
| OR-26 | Nhập tệp mẫu xlsx/csv → SQL → xuất → `openpyxl` đọc lại; số trên 15 chữ số | QA | Tích hợp | Tự | P0 | TL-03, D9 |
| OR-27 | Ngưỡng màu theo bảng quyết định (bằng Tốt, bằng Kém, 90 %/110 %, dòng USD, Tổng = 0, mốc `'0.345'`) | QA | Đơn vị | Tự | P2 | AC-42.8, AC-46.6 |
| OR-28 | Lọc khoảng cột tiền JSON và `val_revenue` với `'1.000.000'`: không được bỏ lọc lặng lẽ | Người dùng | Tích hợp HTTP | Tự | P1 | AC-10.16, TL-04 |
| OR-29 | Đường cũ `build_context` / thẻ Tổng quan với 2 loại tiền: chứng minh cộng lẫn | QA | Tích hợp | Tự (xfail) | P1 | ADR-046 |
| OR-30 | Sửa báo cáo Sale đổi Thị trường (trang `/sua/` và `?khung=1`): số giữ nguyên từng ký tự, loại tiền đổi, có hỏi xác nhận | Người dùng | HTTP | Tự | P1 | ADR-046, D8 |
| OR-31 | `report-entry.js` (`docSo`, `lamTron`, `tinh`) theo bảng chân lý, nạp qua `vm` như `scripts/kiem-thu-date-inputs.cjs` | QA | Đơn vị JS | Bán | P2 | AC-43.6, AC-46.10 |
| OR-32 | Kế toán và Manager đối chiếu Báo cáo tổng hợp, Excel với bảng tính tay ORACLE-1 trên local | Người dùng | Nghiệm thu | Tay | P1 | docs/07 |
| OR-33 | Chạy INV-01…INV-13 trên bản sao DB Staging trước mỗi lần phát hành; cổng theo mẫu `scripts/crm-update-perf/check_matrix.py` (trượt trước, đạt khi mọi bất biến đạt) | QA | Giám sát dữ liệu | Bán | P0 | BR-8, ADR-046 |
| OR-34 | Kiểm meta: `app/tests/oracle/` không import danh sách cấm (mục 3.3.3) | QA | Meta | Tự | P1 | — |
| OR-35 | `compute_report` của MKT và `resync_table` cho cùng CPO / Giá Mess / AOV | QA | Tích hợp | Tự | P2 | — |
| OR-36 | Sửa một ô báo cáo: các ô tiền khác giữ nguyên chuỗi; giá trị lưu `'1E-7'` | QA | Tích hợp HTTP | Tự | P2 | ADR-050 |
| OR-37 | Lưới vận đơn theo từng vai: tập ID và số dòng của `build_grid` (cả có lọc `f_quoc_gia=USA`) bằng SQL thô viết tay. Mở rộng `app/tests/perf/optimization_oracle.py` thêm đường thứ hai; tái dùng kiểu so của `scripts/grid-flags-check/contract.py` và ca "đơn ngoài phạm vi" của `invalidation_audit.py`, nhưng thay `in_scope` bằng điều kiện phạm vi viết tay | QA | Tích hợp | Tự | P1 | ADR-040 |
| OR-38 | Mở rộng bài tải `scripts/crm-update-perf/`: `locustfile.py` dùng CPQC có số lẻ khó (0,125; 1/3) thay vì chỉ số nguyên `.00`; `oracle.py` đọc `data->>'cpqc'`, `data->>'cpo'` bằng SQL thô thay cho ORM | QA | Tải + đối chiếu | Bán | P2 | TL-03, D1, D2 |

#### 3.3.7 Quyết định cần chủ dự án chốt trước khi viết kỳ vọng

| Mã | Câu hỏi | Ảnh hưởng tới |
|---|---|---|
| D1 | Chuỗi máy `'0.125'` / `'12.345'` phải đọc ra số nào? Có tách đường đọc chuỗi máy khỏi đường đọc chữ người gõ không? | TL-03, OR-03/04/05/18/26/38 |
| D2 | Dùng một luật làm tròn chung (HALF_EVEN hay HALF_UP) cho màn hình, cột tính, Excel, thống kê CRM? | T3, T4, T8, T15, T28 |
| D3 | Cột tiền có giới hạn số lẻ không (chặn ở `check_amount`)? | T2, T6, T11, T12 |
| D4 | Báo cáo ngày có cho số âm không? | T6, T7, T18 |
| D5 | Gõ `'1,5'` vào ô số nguyên thì báo lỗi hay nhận? | T7, T20 |
| D6 | JPY/KRW có được lưu phần lẻ không? | T3, T24 |
| D7 | Bảng xếp hạng lấy nguồn từ Order hay vận đơn? Xử lý KRW thế nào? | T25 |
| D8 | Đổi thị trường khi sửa báo cáo có bắt xác nhận không? | T19, OR-30 |
| D9 | Có hỗ trợ CSV kiểu `'12,345'` (Excel tiếng Anh) không? | T1, T26 |

#### 3.3.8 Phát hiện đáng lo

| # | Phát hiện | Vị trí | Trạng thái xác minh | Mức | Ca |
|---|---|---|---|---|---|
| F1 | TL-03 vẫn còn: `'0.125'` → 125, `'12.345'` → 12345. Các đường còn gửi chuỗi máy vào: CSV (`_o_csv`), ô chữ xlsx, ô sửa lưới (`master-grid.js` dòng 524), ô ngưỡng màu, đơn giá lúc lên đơn. Hộp sửa báo cáo thì an toàn (`_gia_tri_dang_luu`) | `money.py:parse_money`; `docs/test-log.md` dòng 1201 vẫn "Mới" | Đã đọc mã, chưa chạy. Chưa xác minh: Enter không sửa có bị `working.stage` bỏ qua không; dán và kéo điền lấy value hay display | Cao | OR-01/03/04 |
| F2 | Đổi kiểu cột làm hỏng số âm thầm: DECIMAL→MONEY `'0.125'`→`'125'`; MONEY→INTEGER `'1234.56'`→123456; áp cả cho dòng đã xoá | `table_service._chuyen_kieu` | Đã đọc mã | Cao | OR-05 |
| F3 | Ô INTEGER xoá mọi dấu: `'1,5'` → 15, JS cũng làm vậy. Báo cáo ngày nhận số âm; chỉ `waybill_service.money` và `threshold_service.parse` chặn âm | `record_service.parse_value`; `report-entry.js` | Đã đọc mã | Cao | OR-06 |
| F4 | Bốn cách làm tròn khác nhau: HALF_EVEN (`compute`, `format_number`, `format_money`, JS `lamTron`), HALF_UP (`to_vnd`, `so`), Postgres (xa số 0). Excel Báo cáo tổng hợp ghi `Metric` chưa làm tròn | Nhiều nơi | Đã đọc mã | Cao | OR-15/24/25 |
| F5 | Cast `numeric(18,2)` làm tròn từng dòng trước khi SUM (3×0,005 → 0,03). `val_revenue` lệch `data` nên `lech_cot_tach` báo lệch mãi; `--sua` có lẽ không chữa được | `aggregations._sum_exprs`; `statistics_profiles._decimal_expr`; `integrity_service` | Đã đọc mã. Cơ chế Postgres theo hiểu biết chung, chưa chạy. `--sua`: chưa xác minh | Cao | OR-11, INV-03/12 |
| F6 | `ColumnDef.compute` đặt `quantize` ngoài `try` → 500 khi tràn | `forms_builder/models.py` | Đã đọc mã. Validator ở form: chưa xác minh | Vừa | OR-08 |
| F7 | Nguồn MKT nhiều loại tiền: (TT) dồn vào Chưa rõ hoặc biến mất; nghi đếm đôi ở `subtotals` | `aggregations.with_currency_totals`, `subtotals` | Đã đọc mã, chưa dựng dữ liệu | Vừa | OR-13 |
| F8 | Lọc khoảng cột tiền JSON bị đổi thành so bằng; trên `val_revenue`, giá trị `'1.000.000'` làm bộ lọc bị bỏ lặng lẽ | `forms_builder/query.py:build` | Đã đọc mã | Vừa | OR-28 |
| F9 | Một đơn KRW làm hỏng cả Bảng xếp hạng và việc thưởng sao. `Order.total` không theo kịp khi sửa trên lưới; dòng nhập từ tệp không được tính | `leaderboard_service` | Đã đọc mã | Vừa | OR-22 |
| F10 | `'12,345'` → 12,345; `'1.234.5'` → 12345. U+202F và tab không bị bỏ ở máy chủ nhưng JS thì bỏ | `parse_money` (đã đọc lại: chỉ bỏ dấu cách và NBSP) | Đã đọc mã | Vừa | OR-01/31 |
| F11 | Đường cũ `build_context` / thẻ Tổng quan cộng lẫn loại tiền, trái ADR-046 | `summary_service.build_context`; `dashboard_service._marketing` | Đã đọc mã | Vừa | OR-29 |
| F12 | Sửa báo cáo Sale đổi Thị trường: Loại tiền tự đổi, số giữ nguyên, không có bước xác nhận | `daily_service.amend`, `protected_values` | Đã đọc mã. Chủ dự án muốn hành vi nào: chưa xác minh | Vừa | OR-30 |
| F13 | `format_money` có dấu cách thừa với CAD/PHP/AUD; 2,5 VND hiện `'2 ₫'` | `format_money` | Đã đọc mã | Thấp | OR-24 |
| F14 | Có thể hiện "Chênh lệch 2.00 đơn" | `statistics_service._overview_chart` | Đã đọc mã, chưa chạy | Thấp | OR-20 |
| F15 | Lưu `'1E-7'` khiến lần sửa ô khác sau đó bị báo lỗi kiểu | `parse_value`, `report-entry.js` | Đã đọc mã | Thấp | OR-36 |
| F16 | `parse_money('-0')` trả `Decimal('-0')` và lưu chuỗi `'-0'` (bằng 0 về giá trị) | `parse_money` | Đã đọc mã | Thấp | OR-01 |
| F17 | Lọc sản phẩm trên lưới dựa vào `sl_*`, mà `sl_*` không được giữ theo Chi tiết | `grid_service.product_any_of` | Chưa xác minh | Thấp | INV-08 |
| F18 | (TT) lọc theo `product__name`, Vận đơn lọc theo `product__code`; nếu trùng tên khác mã thì (TT) cộng cả hai | `marketing_actuals`, `delivery` | Chưa xác minh (`Product.name` có unique không) | Thấp | OR-16 |
| F19 | `create_order`: đơn giá 3 số lẻ gây `ValidationError`, số lượng `'1.5'` gây `ValueError`; chưa rõ view có bắt không | `order_service.create_order` | Chưa xác minh | Vừa | OR-21 |
| F20 | Bài kiểm số liệu hiện có tự đối chiếu với chính mình; chưa có bài cho `0.125`, `'12,345'`, U+202F, đổi kiểu tiền, lọc khoảng cột tiền | Mục đầu 3.3 | Đã đọc mã | Cao | OR-34, toàn bộ |
| F21 | Oracle lưới ở `app/tests/perf/` (`optimization_oracle.py`, `optimization_bulk_oracle.py`) và `scripts/grid-flags-check/` (`contract.py`, `invalidation_audit.py`) lấy kỳ vọng qua `build_grid` / `in_scope` hoặc qua chính view lưới khi tắt cờ, chỉ chạy khi đo hiệu năng, không có trong CI. Lỗi phạm vi có sẵn trong `build_grid` sẽ được "đóng băng" thành kỳ vọng. Riêng `scripts/crm-update-perf/oracle.py` tính kỳ vọng độc lập nhưng chỉ với CPQC số nguyên | `app/tests/perf/`; `scripts/grid-flags-check/`; `scripts/crm-update-perf/` | Đã đọc mã | Vừa | OR-37, OR-38 |
| F22 | TL-23 chưa có bài hồi quy (grep `TL-23` trong `test_*.py` ra 0). `test_hang_doi_chet.py` chỉ phủ AC-10.13/AC-10.14 | `app/crm/tests/test_hang_doi_chet.py` | Đã grep | Vừa | OR-09 |

### Critical Files for Implementation
- /home/user/KNJSC/app/core/money.py
- /home/user/KNJSC/app/forms_builder/services/record_service.py
- /home/user/KNJSC/app/reports/aggregations.py
- /home/user/KNJSC/scripts/crm-update-perf/oracle.py
- /home/user/KNJSC/app/tests/perf/optimization_oracle.py
