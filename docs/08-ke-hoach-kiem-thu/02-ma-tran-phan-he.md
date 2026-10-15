> Phần của [Kế hoạch kiểm thử toàn diện KNJSC](../08-ke-hoach-kiem-thu-toan-dien.md) — mục lục, lộ trình P0/P1/P2 và rủi ro còn lại nằm ở tệp đó.

## 2. Ma trận phân hệ × loại kiểm thử

Cách đọc:
- **Ký hiệu:** ✅ là có và đủ (chỉ còn lỗ hổng mức thấp). ⚠️ là có một phần (còn lỗ hổng mức cao hoặc vừa đã xác minh). ❌ là không có. — là không áp dụng cho phân hệ này.
- **Đường dẫn** tính từ gốc kho `/home/user/KNJSC`. Số trong ngoặc là số tệp, hoặc tên tệp dùng làm bằng chứng.
- **Ưu tiên** suy ra từ mức nghiêm trọng đã kiểm chứng: cao là P0, vừa là P1, thấp là P2.
- **Hình thức:**
  - *Tự động*: bài pytest chạy được trong CI.
  - *Bán tự động*: script Node, bài có `skipif` theo biến môi trường, hoặc diễn tập theo danh sách kiểm.
  - *Thủ công*: người kiểm làm tay.
- **Lỗ hổng chung của nhiều phân hệ** chỉ ghi đầy đủ một lần. Ở các phân hệ khác chỉ trỏ tới mã của nó (ví dụ "xem 2.1-C4").
- **ADR-022 có hai tệp trùng số:** docs/quyet-dinh/022-ban-dieu-hanh-kn-crm.md (Bàn điều hành `GET /thong-ke/` của KN CRM) và docs/quyet-dinh/022-bao-cao-hoat-dong-erp.md (ánh xạ báo cáo hoạt động KN ERP). Viết "ADR-022" trơn thì không rõ là tệp nào, nên khi dẫn phải ghi kèm tên tệp. Việc đánh số lại ghi ở 2.8, mức thấp.

| Phân hệ | Unit Python | Unit JS | Tích hợp/dịch vụ | Phân quyền hai chiều | HTTP chức năng | E2E trình duyệt | Giao diện/responsive | Hiệu năng | Migration/dữ liệu | Kiểm tay |
|---|---|---|---|---|---|---|---|---|---|---|
| **2.1 Xác thực, tổ chức, phân quyền nền và lõi (core, org)** — 39 tệp | ⚠️ test_permissions, test_audit, test_so_va_gio_bien, test_hop_trang; thiếu parse_money '1.2345', form bộ phận/team, RequestMetrics | — (JS dùng chung xem 2.9) | ⚠️ test_account, test_account_management, test_sao_luu; thiếu nhật ký của Django admin, trùng mã nhân sự | ⚠️ test_ma_tran_quyen_hai_dich_vu (8 vai × 2 URLconf), test_quyen_menu_erp; /quan-tri/ có bài từ #121, CEO ở endpoint ghi có bài quét từ #127; thiếu Leader chéo bộ phận | ⚠️ test_shared_login, test_temporary_password; thiếu POST /doi-mat-khau/, khoá/mở khoá | ⚠️ test_dat_lai_mat_khau chạy trong CI; 2 tệp Chrome bị `skipif` | ⚠️ test_mau_dung_chung, test_trang_loi; 'Mọi tác vụ' ở CRM dẫn tới 403 | ⚠️ test_do_mat_khau (20 luồng), ngân sách truy vấn trong test_account_management | ✅ test_chuyen_doi, test_account_concurrency | ⚠️ biên bản 08.10 mục 11 (chỉ Staff ở /quan-tri/); kiem-thu-quan-ly-tai-khoan.cjs |
| **2.2 Bảng động, biểu mẫu, Bảng dữ liệu ERP, nhập/xuất, cấp quyền (forms_builder)** — 34 tệp | ⚠️ test_ngay_so_excel, test_nhap_tep_bom; thiếu số nguyên '150.00', code chết trong ColumnForm | — (xem 2.9) | ⚠️ test_bang_dong, test_doi_kieu_cot (chỉ tầng dịch vụ), test_import_checks; thiếu val_revenue >2 số lẻ, danh sách quyền đã thu | ⚠️ test_known_table_scope, test_pham_vi_bang_nhanh; TL-01 có bài từ #122 | ⚠️ test_man_hinh_bang, test_nhap_xuat; thiếu luồng quản lý biểu mẫu, bỏ cột, đổi kiểu cột qua HTTP ra 500 (C18) | ⚠️ test_luong_nhap_xuat, test_sap_xep_khong_giat (CI) | ⚠️ test_mau_cot; Leader thấy '＋ Thêm mới' rồi nhận 403 | ⚠️ test_hieu_nang (chậm), ngân sách truy vấn; chưa đo khoá khi nhập | ⚠️ bài migration liên quan nằm ở crm (crm/tests/test_an_cot.py, crm/tests/test_khoa_trung_sdt.py); chưa có bài đổi kiểu trên dữ liệu cũ | ⚠️ kiem-thu-erp-*.cjs chạy tay; docs/07 lỗi thời |
| **2.3 KN CRM: lưới master, thư mục, cấp quyền, thống kê (crm + JS lưới)** — 50 tệp | ⚠️ test_grid_date_display, test_bang_tinh_dinh_dang; thiếu bài append-only cho GridCellHistory | ⚠️ 9 script Node, **không có trong CI** | ⚠️ test_master_grid, test_shared_integrity, test_khoi_luoi_dem, test_optimization | ⚠️ test_crm_chi_van_don, test_chi_admin_xoa_dong, test_ceo_chi_doc_luoi; xoá bảng thường qua CRM chưa bị chặn | ⚠️ thiếu các nhánh 400 của luu-json/, quyen-dong/, dong-bo/ | ⚠️ khoảng 10 tệp e2e trong CI; thiếu hết phiên khi còn nháp, nút Tôi/Toàn bộ | ⚠️ test_khung_crm, test_lien_ket_khong_cut; thiếu `?v=` ở 6 chỗ | ⚠️ 6 tệp *_capacity (chậm, bỏ qua khi thiếu biến), test_moc_moi_nhat_nhe | ⚠️ nhiều bài migration (gồm test_an_cot, test_khoa_trung_sdt); dữ liệu NFD cũ chưa được chuẩn hoá | ⚠️ tài khoản mẫu Kế toán/CSKH/CEO có từ #118; kiem-thu-solarpunk.cjs lỗi thời |
| **2.4 Lên đơn, khách hàng, sản phẩm, bảng vận đơn, phân công, thanh toán (orders)** — 38 tệp | ⚠️ test_hop_trang; thiếu hợp đồng create_order, trùng cột sl_* | — (xem 2.9) | ⚠️ test_len_don, test_waybill_new, test_payment_documents, test_xoa_dong_huy_don (ADR-049, AC-6.12); thiếu khoá SĐT, sản phẩm ngừng bán | ⚠️ test_bo_don_chi_admin, test_waybill_new; thiếu Kế toán/CSKH/CEO, phạm vi Leader/Manager Sale | ⚠️ test_len_don_mot_lan, test_order_consolidation; thiếu TL-03 3 số lẻ | ⚠️ test_tom_tat_len_don_e2e, test_phan_cong_o_chon (CI); thiếu hết phiên | ⚠️ 4 tệp *_browser* bị `skipif` | ⚠️ chỉ có test_order_code_concurrency | ⚠️ test_kiem_tra_du_lieu, test_mot_bang_van_don; ba lệnh còn vỡ với dữ liệu thật | ⚠️ 5 script kiem-thu-*.cjs; AC-26.6 thực chất là kiểm tay |
| **2.5 Báo cáo ngày, Báo cáo tổng hợp, Tổng quan (reports, dashboard)** — 40 tệp | ⚠️ test_aggregations, test_date_presets, test_activity (AC-22.10, AC-22.11, ADR-035); thiếu số âm | ❌ report-entry.js, staff-code.js, report-filters.js không có unit Node | ⚠️ test_che_do_so_lieu, test_quy_vnd_va_tt; **cộng lẫn tiền ở đường kiểu cũ**; biểu mẫu báo cáo điền thẳng không tạo DailyReport (ADR-008) | ⚠️ test_ma_tran_phan_quyen_bao_cao, test_report_amendments; thiếu POST của CEO, ngưỡng màu | ⚠️ test_bao_cao_ngay, test_admin_sua_tong_hop; nộp lại báo cáo đã bỏ ra 500 | ✅ test_bo_cuc_bao_cao_e2e, test_admin_sua_tong_hop_e2e, test_o_nhap_so_e2e (CI) | ✅ test_bo_cuc_bao_cao, test_bo_cuc_khoi, AC-42.19/42.20 | ⚠️ ngân sách truy vấn; locustfile_erp.py chạy tay | ✅ test_activity_migration, test_mkt_tien_viet (chỉ còn lỗ thấp) | ⚠️ kiem-thu-bao-cao-chi-ma.mjs, kiem-thu-erp-table-focus.cjs |
| **2.6 Nhóm Nội bộ: Tài liệu, Bảng tin, Công việc, Đánh giá nhân sự, Tài nguyên** — 54 bài | ⚠️ test_ghi_chu_khong_chua_mat_khau; thiếu ranh giới tháng, làm tròn | — (phan-trang.js xem 2.9) | ⚠️ thưởng sao, thiệp sinh nhật; thiếu chạy lại thưởng sao, KRW lẫn USD | ⚠️ test_giao_viec_theo_pham_vi, test_go_tai_lieu_theo_quyen; CEO có bài quét POST từ #127 | ⚠️ có bài HTTP ở cả 5 app; thiếu tab cũ, sửa đồng thời | ❌ không có e2e (chỉ kiem-thu-erp-hub.cjs chạy tay) | ⚠️ chỉ kiểm chuỗi HTML; thiếu 390px (AC-13.6) | ⚠️ ngân sách ≤10 truy vấn cho 5 màn; bảng xếp hạng chưa đo | ✅ test_chuyen_doi (CAC_APP gồm cả 5 app) | ⚠️ sao lưu tệp tài liệu chưa có; AC-13.6 làm tay |
| **2.7 Nền tảng, vận hành và phi chức năng** — 26 tệp | ⚠️ test_ti_gia, test_phien_ban_tinh; thiếu cờ prod, lịch beat | — | ⚠️ test_sao_luu (sao lưu: runner giả, cộng một bài pg_dump thật có dấu `cham`, bỏ qua khi máy không có pg_dump; phục hồi: chỉ runner giả), test_hang_doi_chet; **RUNNING kẹt, chưa phục hồi thật** | ⚠️ /quan-tri/ (xem 2.1-C1) | ⚠️ test_trang_loi (500/404/507), test_ky_tu_nul; thiếu 400/CSRF/413/502 | ⚠️ test_mat_mang_e2e; test_shared_login_browser luôn bị bỏ qua | ⚠️ thiếu 400.html, 403_csrf.html | ⚠️ test_hieu_nang, test_kiem_tai; VPS 300k vượt ngưỡng; gunicorn 30 s; NFR-18 (dung lượng/năm) chưa đo | ⚠️ test_chuyen_doi; do_hieu_nang chỉ ghi dòng PERF-* từ #116 | ⚠️ diễn tập 08.10; không có runbook phục hồi trên VPS; .bat Windows |
| **2.8 Hạ tầng kiểm thử, truy vết AC và tài liệu kiểm thử** — 22 tệp | ⚠️ test_live_server_requests, test_gom_p95, test_dong_bo_skill; hook TL-67 chưa có bài; **chưa có kiểm tĩnh kiến trúc** cho Cấm 1/11, Bắt buộc 9/12 | ❌ script Node không có trong CI (xem 2.3-C1) | ⚠️ thiếu Redis thật trong CI | ⚠️ **test_ma_tran_phan_quyen lệch docs/04**; test_khoi chấp nhận mã 200 | ⚠️ test_khoi chỉ gọi GET với pk giả | ⚠️ 19 tệp e2e trong CI, nhưng Chromium hỏng thì bỏ qua cả bộ mà CI vẫn xanh | ⚠️ test_giao_dien chỉ kiểm tĩnh | ⚠️ TL-71 (p95 ≤100 ms trên runner chung) | ✅ test_chuyen_doi | ⚠️ docs/06, docs/07 đã cũ |
| **2.9 JS phía trình duyệt** — 19 tệp trong app/static/js (gồm htmx.min.js là thư viện ngoài) | — | ⚠️ 9 script đơn vị + kiem-thu-date-inputs.cjs, đều chạy tay | — | ⚠️ waybill-feedback.js, payments.js không kiểm `redirected` khi hết phiên | — | ⚠️ e2e Playwright trong CI phủ lưới, Lên đơn, báo cáo | ⚠️ thiếu `?v=` ở 6 chỗ; test_dien_thoai chỉ có 4 màn; sáng/tối và tập trung lưới (ADR-028) chỉ có kiểm tĩnh và script tay | ⚠️ test_ghi_chu_tu_gian_dong (p95), test_luoi_hoi_nhe; poll 8 giây | — | ⚠️ 51 script .cjs chạy tay |

---

### 2.1 Xác thực, tổ chức, phân quyền nền và lõi (core, org) — 39 tệp kiểm

| Mã | Lỗ hổng và rủi ro | Bằng chứng | Góc nhìn | Loại | Hình thức | Ưu tiên |
|---|---|---|---|---|---|---|
| C1 | **Đã sửa ở #121 (TL-93).** Trước đó đăng nhập qua /quan-tri/login/ đi vòng qua khoá tạm, nhật ký LOGIN/LOGIN_FAILED/LOGOUT và auth_epoch (dò mật khẩu Admin không giới hạn). Nay /quan-tri/login/ chỉ chuyển về /dang-nhap/, không kiểm mật khẩu; vai khác Admin nhận 403 kèm DENIED. Gộp với lỗ hổng cùng tên ở 2.7 | app/knjsc/urls.py (`quan-tri/login/` → core.views.quan_tri_dang_nhap); app/core/tests/test_quan_tri_dang_nhap.py | QA | Bảo mật HTTP | Tự động | P0 |
| C2 | Admin duy nhất tự hạ cấp mình qua Sửa hồ sơ thì bị gỡ is_staff/is_superuser, hệ thống không còn ai quản trị. Nhánh "Admin hoạt động cuối" trong delete_account không chạm tới được qua HTTP | app/org/views.py nhan_su_sua; app/org/services/account_service.py update_profile; app/org/services/account_management.py delete_account; test_account_management.py::test_cannot_delete_last_admin_or_reuse_deleted_identifiers chỉ chạm tới nhánh tự xoá | Người dùng | Dịch vụ + HTTP | Tự động | P0 |
| C3 | Leader của bộ phận khác được chọn làm trưởng nhóm thì đọc được dữ liệu, đặt lại mật khẩu và xoá mềm Staff của bộ phận đó | app/org/forms.py TeamForm.__init__ (không lọc theo bộ phận); app/org/models.py UserProfile.scope_team_ids; AccountPolicy.can_manage nhánh LEADER; grep 'tm-leader' chỉ có trong test_ra_soat.py | QA | Phân quyền (cấu hình) | Tự động | P0 |
| C4 | **TL-03 (gốc chung):** parse_money đọc '1.2345' thành 12345 và '0.125' thành 125 mà không báo gì. Lưu ý: '1.234' → 1234 là quy ước cố ý (test_so_va_gio_bien), nên cần chủ dự án chốt cách đọc chuỗi máy trước khi viết bài. Đường đi qua lưới ở 2.2-C3, qua Lên đơn ở 2.4-C1 | app/core/money.py parse_money nhánh co_cham (dòng 86–90); app/reports/tests/test_nguong_va_loc_san_pham.py dòng 132–133; docs/test-log.md TL-03 'Mới'; docs/backlog-kanban.md P0 | Người dùng | Unit tiền | Tự động | P0 |
| C5 | Bài "CEO vào trang quản trị" là khẳng định rỗng: /admin/ luôn trả 404 | app/org/tests/test_account_management.py dòng 312; docs/kiem-chung-dien-tap-phat-hanh-staging-20261008.md mục 11 (chỉ Staff, làm tay) | QA | Phân quyền HTTP | Tự động | P1 |
| C6 | Chưa có bài quét mọi endpoint ghi với CEO (RANK_LEVEL 35 > Manager 30) và staff_kt. Hiện chỉ tầng dịch vụ chặn | documents/views.py dòng 36, 58; resources/views.py dòng 84, 106, 133, 144; app/tests/test_khoi.py CAC_VAI_TRO không có 'ceo', 'staff_kt' | QA | Phân quyền (quét URL) | Tự động | P1 |
| C7 | Lưới CRM poll moi-nhat/ mỗi 8 giây nên phiên không bao giờ hết hạn khi tab còn hiện. Trái FR-1.3, AC-1.4; không ADR nào cho phép | app/static/js/master-grid.js dòng 1312, 1359; app/core/middleware.py SessionTimeoutMiddleware | QA | Tích hợp + trình duyệt (giả giờ) | Tự động | P1 |
| C8 | POST /doi-mat-khau/ chưa có bài pytest: xoá must_change_password, huỷ phiên khác, từ chối mật khẩu cũ sai; không ghi nhật ký (BR-5) | app/core/views.py PasswordChangeView.form_valid; chỉ có scripts/kiem-thu-quan-ly-tai-khoan.cjs dòng 59–63 | Người dùng | HTTP | Tự động | P1 |
| C9 | nhan_su_doi_trang_thai: chưa có bài cho các chiều thuận. Tài khoản đang khoá tạm bấm nút lại bị KHOÁ HẲN; bộ lọc 'bi-khoa' bỏ sót khoá tạm | app/org/views.py nhan_su_doi_trang_thai, nhan_su | Người dùng | HTTP | Tự động | P1 |
| C10 | Form tạo/sửa hồ sơ không kiểm tổ hợp bộ phận và team. Manager không có bộ phận thì in_scope trả danh sách rỗng thay vì từ chối (FR-3.5) | app/org/forms.py TaoTaiKhoanForm.clean, SuaHoSoForm.clean; app/core/managers.py apply_scope | QA | Unit form | Tự động | P1 |
| C11 | Hai Admin tạo hai người trùng mã nhân sự (khác tên đăng nhập) thì ra trang 500 | account_service.create_with_temporary_password (except IntegrityError); app/org/views.py nhan_su_moi | QA | Đồng thời | Tự động | P1 |
| C12 | Liên kết "Mọi tác vụ" ở CRM dẫn tới trang 403. Trái AC-44.4, ADR-045 | app/core/context_processors.py khung_chung; app/templates/core/tac_vu_xem.html dòng 14 | Người dùng | Giao diện + phân quyền | Tự động | P1 |
| C13 | X-Forwarded-For không phải IP làm mọi lần ghi nhật ký trả 500, và giả được IP trong nhật ký. Production an toàn nhờ nginx; local và Staging thì bị. Cơ chế lỗi (ValueError ở Python hay DataError 22P02) chưa xác minh | app/core/audit.py _client_ip; AuditLog.ip_address là GenericIPAddressField; deploy/production/nginx.conf.template dòng 41 | QA | Unit + HTTP (fuzz header) | Tự động | P1 |
| C14 | Nhật ký đăng nhập sai lưu chuỗi thô, kể cả mật khẩu gõ nhầm ô. Tên đăng nhập rỗng thì gán nhầm cho người có email rỗng. Tên có khoảng trắng thì mất dòng "Khoá tạm" | app/core/views.py LoginView.form_invalid; auth_service.note_failed_login, find_user; app/templates/core/nhat_ky.html dòng 50 | QA | Unit nhật ký | Tự động | P1 |
| C15 | RequestMetricsMiddleware (bật trên production) chưa có bài kiểm: X-Request-ID xấu, log không có query string, ensure_connection, status 500. Với StreamingHttpResponse thì đếm thiếu db_ms (theo 2.7) | app/core/request_metrics.py; deploy/production/compose.yml CRM_REQUEST_METRICS '1' | QA | Unit middleware (caplog) | Tự động | P1 |
| C16 | E2E đăng nhập chung và quản lý tài khoản bằng Chrome không chạy trong CI | core/tests/test_shared_login_browser.py dòng 21 (SHARED_LOGIN_BROWSER); org/tests/test_account_browser_server.py dòng 25 (ACCOUNT_BROWSER) | QA | E2E | Bán tự động → đưa vào CI | P1 |
| C17 | Sửa qua Django admin không ghi AuditLog (BR-5). Tạo superuser không có hồ sơ thì thành Admin ngoài luồng, không bị buộc đổi mật khẩu | app/org/admin.py; app/core/permissions.py get_rank | QA | Tích hợp admin | Tự động | P1 |

Mức thấp (P2, chỉ liệt kê):
- Ma trận quyền hiển thị CEO "Nộp báo cáo ngày" (core/views.py ma_tran_quyen).
- NoCacheForAuthenticatedMiddleware chưa có bài trực tiếp.
- HTMX gặp buộc đổi mật khẩu thì trang bị nhét vào chỗ nút (base.html dòng 135–143).
- find_user tra theo email nên khoá được tài khoản người khác.
- Chọn bản sao lưu theo thứ tự tên tệp (backup_service.list_backups).
- ADR-044 không có mã AC; hai docstring sai nghĩa.

Bị bác bỏ (thật ra đã có bài):

| Tưởng là thiếu | Thật ra đã phủ bởi |
|---|---|
| Tải tệp tác vụ đã bị dọn | app/forms_builder/tests/test_nhap_xuat.py::test_xuat_lon_chay_nen_va_tai_duoc |
| Các hàm tiền phụ trợ (currency_rank, format_money JPY/AUD, check_amount) | reports/tests/test_markets_currencies.py, test_quy_vnd_va_tt.py, test_che_do_so_lieu.py (AC-46.10), core/tests/test_so_va_gio_bien.py |
| code_expression, bộ lọc ma/ma_ten | reports/tests/test_activity.py, test_bao_cao_ngay.py, org/tests/test_ma_nhan_su.py. label_expression là mã chết, cần gỡ chứ không cần bài |
| FR-1.1 đòi đăng nhập bằng email | docs/02 dòng 34 không nói tới email; FR-1.4, FR-1.7 chốt đăng nhập bằng mã nhân sự |

### 2.2 Bảng động, biểu mẫu, Bảng dữ liệu ERP, nhập/xuất, cấp quyền (forms_builder) — 34 tệp kiểm

| Mã | Lỗ hổng và rủi ro | Bằng chứng | Góc nhìn | Loại | Hình thức | Ưu tiên |
|---|---|---|---|---|---|---|
| C1 | **TL-01 (đã sửa ở #122):** trước đó mọi Manager thấy được bảng (kể cả Manager Sale, Manager Kế toán với bảng vận đơn) đều tự cấp được quyền EDIT, mở toàn bộ dòng vận đơn, và thu được quyền do Vận đơn cấp. Lỗ hổng có ở cả ERP lẫn CRM | app/forms_builder/views.py bang_cap_quyen (486–507), bang_thu_quyen (510–520); managers.py TableDefQuerySet.in_scope (54–63); test_ma_tran_quyen_hai_dich_vu.py dòng 36–39 đặt hai URL này vào CHUNG_KHONG_GET; crm/tests/test_quyen_leader.py:72 gửi form rỗng. Bài từ #122: forms_builder/tests/test_man_hinh_bang.py, core/tests/test_ma_tran_quyen_hai_dich_vu.py | QA | Phân quyền HTTP (chiều bị từ chối) | Tự động | P0 |
| C2 | Manager được cấp quyền FILL thì sửa được biểu mẫu của bộ phận khác: thêm/bỏ trường, nối lại cột đích, cấp và thu quyền | views.bieu_mau_sua, bieu_mau_bo_truong, bieu_mau_cap_quyen, bieu_mau_thu_quyen (606–729); FormDefQuerySet.in_scope (134–153) | QA | Phân quyền HTTP | Tự động | P0 |
| C3 | TL-03 trên lưới: chuỗi '0.125' khi Enter, dán, kéo điền, hoàn tác bị nhân nghìn, nhật ký lại ghi như người dùng cố ý sửa (gốc ở 2.1-C4) | test_nguong_va_loc_san_pham.py:133 né lỗi bằng cách gửi '0,345'; không bài nào đi qua update_cells | Người dùng | Unit + tích hợp + e2e lưới | Tự động | P0 |
| C4 | Đổi kiểu Tiền/Thập phân sang Số nguyên biến '150.00' thành 15000 và '12.5' thành 125, kể cả trên dòng đã xoá. Lưu ý: gõ dấu phẩy ở ô số nguyên (ví dụ '12,5' → 125) đã được chốt là chủ ý (xem 2.5, mục bác bỏ). Rủi ro chính nằm ở việc đổi kiểu. Đường HTTP của đổi kiểu xem C18 | app/forms_builder/services/record_service.py dòng 97–106; table_service._chuyen_kieu (157–189); app/static/js/report-entry.js dòng 34–36 | Người dùng | Unit + tích hợp | Tự động | P0 |
| C5 | Tiền có hơn 2 chữ số lẻ: JSON giữ '1234.5678' còn val_revenue là numeric(18,2), nên lệnh kiem_tra_du_lieu (cổng phát hành) đỏ mãi, và `--sua` cũng không chữa được | record_service.parse_value (107–115); DataRecord.val_revenue; app/orders/services/integrity_service.py lech_cot_tach (50–64); table_service.resync_table (367–377), _giong (411–419) | Người dùng / QA | Tích hợp DB + lệnh | Tự động | P0 |
| C6 | Danh sách quyền hiện cả quyền đã thu; thu lần hai ghi đè dấu vết lần đầu; cấp trùng tạo hai dòng Grant | grant_service.py dòng 318–327 (không lọc deleted_at); views.py dòng 517, 726; bang_cot.html dòng 126–145 | QA | Tích hợp + HTTP | Tự động | P1 |
| C7 | Bỏ cột ra 500: cột đang nối biểu mẫu (ProtectedError), cột chuẩn vận đơn (TL-13, BusinessError không được bắt). Cột là vế công thức thì không bị chặn. Nút "Bỏ" không hỏi xác nhận | views.bang_xoa_cot (191–202); table_service.remove_column (194–211) so với removable_reason (309–326); waybill_service.py:313–318; bang_cot.html:51 | Người dùng | Tích hợp + HTTP | Tự động | P1 |
| C8 | ColumnForm có code chết sau `return ket_qua`, nên toán hạng cột tính sẵn không bị ràng buộc (trỏ tới cột không có, phụ thuộc vòng) | app/forms_builder/forms.py dòng 96, 98–123; models.py ColumnDef.clean (375–390) | QA | Unit form | Tự động | P1 |
| C9 | Leader thấy nút "＋ Thêm mới…" nhưng bấm thì 403, mỗi lần bấm ghi một dòng DENIED | forms_builder/urls.py dòng 33–34; form_service.widgets (333, 347); choice_service.can_manage_options (20–24) | Người dùng | HTTP phân quyền | Tự động | P1 |
| C10 | Tham số bẩn ra 500: ?truong=abc; ?ve=<không phải slug> còn tạo FieldDef trước khi lỗi | views.bieu_mau_sua (614–620), truong_moi (684–686) | QA | HTTP biên | Tự động | P1 |
| C11 | Luồng HTTP quản lý biểu mẫu (tạo, thêm/sửa/bỏ trường, cấp/thu FILL) chưa có bài nào. AC-8.1 bị gắn nhầm vào bài tạo bảng | test_man_hinh_bang.py:122; chỉ có test_bieu_mau.py:243 (GET 403) | QA | Chức năng HTTP | Tự động | P1 |
| C12 | TL-25: mỗi lần đổi cột sinh một job tính lại, không gộp. Job RUNNING kẹt chặn xoá bảng vĩnh viễn (TL-23 xem 2.7-C1) | table_service.schedule_resync (443–462); lifecycle_service.delete (73–75) | QA | Tác vụ nền | Tự động | P1 |
| C13 | TL-09: sắp xếp không ổn định, lật trang thì sót hoặc lặp dòng. TL-10: cột tiền trong JSON sắp theo chuỗi | app/forms_builder/query.py apply_sort (225–233), build (248–252), JSON_RANGE_TYPES (46) | Người dùng | Tích hợp truy vấn | Tự động | P1 |
| C14 | Nhập lại cùng một tệp vào bảng thường thì nhân đôi dòng, dù bảng có cột khoá (ADR-010) | import_check_service.py dòng 13–15 | Người dùng | Chức năng | Tự động | P1 |
| C15 | Vòng đời bảng: không có cách ngừng dùng biểu mẫu, nên bảng đã có biểu mẫu không bao giờ xoá được. Leader và Manager chỉ có Grant chưa có bài chiều bị từ chối | crm/tests/test_table_lifecycle.py dòng 27–30; lifecycle_service.manageable (48–55) | QA | HTTP + phân quyền | Tự động | P1 |
| C16 | Thu quyền và cấp quyền cho team phải làm mất hiệu lực phiên, nhưng chưa bài nào đăng nhập thật để kiểm | test_bieu_mau.py:361–381, 300–312, 386–396 | QA | Phân quyền + phiên | Tự động | P1 |
| C17 | Nhập Excel giữ khoá độc quyền suốt lượt, chặn mọi lần ghi lưới. Tiến độ nhảy từ 0% lên thẳng 100% | import_service.run (347–357); BackgroundJob.set_progress (213–218) | Người dùng | Hiệu năng + đồng thời | Tự động | P1 |
| C18 | Đổi kiểu cột qua màn Cột (`/bang/<code>/cot/?cot=<pk>`, POST) ra trang 500 khi bảng còn giá trị không chuyển được sang kiểu mới. View bang_cot gọi table_service.update_column mà không bắt BusinessError. _chuyen_kieu ném BusinessError kèm lời tiếng Việt ("Không đổi được kiểu cột… Sửa các ô đó (kể cả dòng đã xoá) rồi đổi lại"), nhưng lời này không tới người dùng: không middleware nào chuyển BusinessError thành phản hồi (core/middleware.py chỉ có process_exception cho hết đĩa và DataError). Ca kiểm: tạo bảng có cột Chữ chứa 'abc', POST đổi sang Số nguyên; mong đợi trả lại form với lỗi tiếng Việt, cột giữ kiểu cũ, không 500 (NFR-6) | app/forms_builder/views.py bang_cot (142–179, gọi update_column dòng 165–166); app/forms_builder/services/table_service.py update_column (118), _chuyen_kieu (157–189, raise dòng 177); app/forms_builder/tests/test_doi_kieu_cot.py chỉ kiểm tầng dịch vụ, không gọi client | Người dùng | HTTP chức năng + xử lý lỗi | Tự động | P1 |

Mức thấp (P2):
- record_policies chưa có bài trực tiếp.
- Cột đang ẩn vẫn đánh dấu bắt buộc/khoá được; ô tìm chung quét cả cột ẩn.
- Nhánh lỗi nhập/xuất phụ: xác nhận hai lần; worker không kiểm lại can_import; tệp nhập bị dọn theo mtime kể cả job PENDING; xuất dùng GET.
- docs/07 lỗi thời (xem 2.8-C8).

Bị bác bỏ:

| Tưởng là thiếu | Thật ra đã phủ bởi |
|---|---|
| Chữ NFD từ tệp nhập không được chuẩn hoá NFC | app/core/excel.py _o_nfc, _o_csv; UnicodeNFCMiddleware; core/tests/test_excel.py::test_chuan_hoa_ten_cot; crm/tests/test_chu_viet_mot_dang.py (AC-9.6). Chỉ còn lỗ thấp: chưa kiểm *giá trị ô* NFD trong tệp |
| TL-22: thử lại sau deadlock mất ghi mà vẫn trả 200 | Lỗi này không có trên main, chỉ có ở PR #21 chưa gộp (backlog-kanban:716). Trên main, deadlock chỉ gây 500 rời rạc |

### 2.3 KN CRM: lưới master, thư mục, cấp quyền, thống kê (crm + JS lưới) — 50 tệp kiểm

| Mã | Lỗ hổng và rủi ro | Bằng chứng | Góc nhìn | Loại | Hình thức | Ưu tiên |
|---|---|---|---|---|---|---|
| C1 | 9 script đơn vị JS của lưới không chạy trong CI. Script cắt mã bằng `indexOf` mà không assert mốc có tồn tại, nên đổi tên hàm là cắt sai đoạn mà vẫn chạy | .github/workflows/ci.yml dòng 139–142 (không có setup-node); scripts/kiem-thu-master-*-unit.cjs, kiem-thu-grid-*-unit.cjs, kiem-thu-optimization-unit.cjs, kiem-thu-master-working-copy.cjs, kiem-thu-master-row-geometry.cjs | QA | Unit JS | Tự động (thêm bước Node vào CI) | P0 |
| C2 | xoa-bang/, khoi-phuc-bang/, bang-da-xoa/ ở CRM không lọc chỉ vận đơn, nên Manager xoá mềm được bảng thường của ERP qua cổng 8021. Trái AC-40.2. Cần chủ dự án chốt | app/crm/lifecycle_views.py; crm/services/catalog.py; test_table_lifecycle.py::test_delete_and_restore_preserve_identity lại KHẲNG ĐỊNH mã 302 trên bảng thường | QA | Phân quyền HTTP | Tự động | P1 |
| C3 | Hết phiên hoặc bị đổi quyền khi còn nháp: nháp bị xoá (clearAccess), lời báo sai ở nhánh poll. TL-02, TL-18 vẫn mô tả bang-tinh-o.js, tệp không còn | app/static/js/master-grid.js dòng 54–62, 858–861, 878–898, 1291–1303, 1357. Suy từ đọc mã | Người dùng | E2E trình duyệt | Tự động | P1 |
| C4 | CEO ở các cửa ghi CRM còn thiếu bài: an-cot/, them-cot/, xoa-cot/, thư mục, chuyen-thu-muc/, bo-chi-tiet/, xoa-bang/… Ngoài ra nhap_tep và cap_quyen trả 403 mà không ghi DENIED | app/crm/views.py dòng 149–175; app/core/permissions.py dòng 47–49; không có handler403 | QA | Phân quyền HTTP | Tự động | P1 |
| C5 | Ô NFD cũ (trước TL-79): lọc theo giá trị thì ra 0 dòng, tìm NFC không thấy, hộp lọc và Thống kê tách thành hai mục | forms_builder/query.py, crm/services/grid_service.py không chuẩn hoá. Chưa chạy | Người dùng | Chức năng + dữ liệu | Tự động | P1 |
| C6 | Các nhánh 400 của luu-json/ chưa bị khoá: payload là list, operation không phải UUID, ô trùng, kind lạ, JSON hỏng | crm/services/master_grid_service.py save (198–229); grep các chuỗi lỗi trong tests: 0 kết quả | QA | Tích hợp HTTP biên | Tự động | P1 |
| C7 | Nút Tôi/Toàn bộ và hộp Cột "Hiện lại" chưa có e2e. kiem-thu-solarpunk.cjs dòng 38 còn assert ngược với luật mới | master-grid.js dòng 1141–1152, 1363–1364; test_pham_vi_toi_toan_bo.py dòng 145; commit 3f32a92 (10.10.2026) | Người dùng | E2E | Tự động | P1 |
| C8 | Admin xoá dòng trong lúc người khác đang sửa dòng đó: người sửa nhận 403 "không còn quyền", sai bản chất; chưa ai kiểm nháp của dòng khác có được giữ | master_grid_service.save (OutOfScopeError); test_chi_admin_xoa_dong.py | Người dùng | Tích hợp + e2e | Tự động | P1 |
| C9 | Tài khoản mẫu Kế toán, CSKH, Leader Vận đơn, CEO: có từ #118, chặng 2 chưa bấm thử (xem 2.8-C6) | core/management/commands/du_lieu_mau.py dòng 64–68; docs/tai-khoan-mau.md | Người dùng | Kiểm tay | Thủ công | P1 |
| C10 | Tệp tĩnh thiếu `?v=` nên sau phát hành trình duyệt có thể giữ JS/CSS cũ (cùng gốc TL-80, AC-10.11) | crm/master_grid.html dòng 62–63; crm/payments.html dòng 4, 39; crm/waybill_entry.html dòng 5, 7; core/tests/test_phien_ban_tinh.py không quét template | QA | Giao diện / cấu hình | Tự động (quét template) | P1 |
| C11 | Poll 8 giây giữ phiên sống mãi (xem 2.1-C7) | — | — | — | — | P1 |
| C12 | Bảng vận đơn ngừng dùng (is_active=False) vẫn hiện ở sidebar và /thu-muc/, bấm Mở thì 404. Trái AC-40.6 | crm/navigation.py dòng 63–73; crm/services/tree_service.py dòng 61–70, 98; crm/views.py dòng 38–43 | Người dùng | Giao diện + phân quyền HTTP | Tự động | P1 |
| C13 | Bài AC-40.2 chỉ thử 10 cửa. Nên duyệt resolver mọi pattern có `<slug:code>` trong urls_bangtinh | test_crm_chi_van_don.py dòng 36–53 | QA | Phân quyền (liệt kê resolver) | Tự động | P1 |

Mức thấp (P2):
- AC-11.15/11.23 lệch ADR-021; display_value với 'NaN' và fmt usd có thể ra 500 (chưa chạy).
- Bộ đệm sau khi thu Grant chưa có bài `transaction=True`.
- Lịch sử ô và hộp lọc lộ cột đang ẩn (AC-39.6).
- Nhánh 400 của quyen-dong/, dong-bo/.
- check_ids là mã chết mang ngữ nghĩa quyền.
- Thống kê với group lạ và nguồn ngoài phạm vi (Bàn điều hành `/thong-ke/`, docs/quyet-dinh/022-ban-dieu-hanh-kn-crm.md).
- Ranh giới giờ VN ở trang chủ, previous_range, recent_edits.
- bo-chi-tiet/ không chống lặp, không ghi lịch sử ô.
- Bài trùng thân trong test_bang_tinh_dong_cot.py; save/delete của GridCellHistory chưa có bài.
- thu_muc ?bp không kiểm DENIED.
- chuyen-thu-muc/ với folder không phải số ra 500.
- bang-da-xoa/ trả danh sách rỗng thay vì từ chối.
- Khối Trang chủ lỗi phải được cô lập, chưa có bài.
- GridCellHistory.before của dòng mới lấy theo giá trị client gửi.
- CI không có Redis.

Bị bác bỏ:

| Tưởng là thiếu | Thật ra đã phủ bởi |
|---|---|
| chon.js không nạp ở KN CRM | Không trang CRM nào cần chon.js: components/o_chon.html chỉ dùng ở các route ERP |
| CEO ở cửa ghi CRM (phần đã có) | core/tests/test_ma_tran_quyen_hai_dich_vu.py::test_quyen_tung_vai_o_hai_dich_vu; crm/tests/test_chi_admin_xoa_dong.py::test_vai_khac_bi_tu_choi_co_nhat_ky; test_ceo_chi_doc_luoi.py |
| schema_changed của luu-json/ | crm/tests/test_shared_integrity.py::test_schema_change_keeps_all_values (tầng dịch vụ) |
| delete_rows sai dạng | test_chi_admin_xoa_dong.py::test_goi_xoa_dong_sai_dang_bi_tu_choi; test_master_grid.py::test_undo_rejects_changed_cell_and_limits |
| Ranh giới ngày VN của preset_range | core/tests/test_so_va_gio_bien.py::test_chip_hom_nay_theo_gio_viet_nam |
| Dán số tiền kiểu Mỹ | test_so_va_gio_bien.py::test_o_so_tu_choi_chu_khong_phai_so_viet, test_o_so_van_doc_dung_cach_viet_viet_nam; crm/tests/test_o_chu_bien.py |
| json() coi chuyển hướng sang /dang-nhap/ là 403 | Hành vi chủ ý, có khẳng định ở scripts/kiem-thu-optimization-unit.cjs dòng 6 (chạy tay) |
| Bộ đệm sau khi thu Grant (về thiết kế) | crm/migrations/0004_grid_change_triggers.py (TABLES có forms_builder_grant); views._bang kiểm in_scope trước khi đọc đệm |

### 2.4 Lên đơn, khách hàng, sản phẩm, bảng vận đơn, phân công, thanh toán (orders) — 38 tệp kiểm

| Mã | Lỗ hổng và rủi ro | Bằng chứng | Góc nhìn | Loại | Hình thức | Ưu tiên |
|---|---|---|---|---|---|---|
| C1 | TL-03 ở Lên đơn, Tóm tắt, hộp Chi tiết: giá '12.345' thành 12345, đơn USD/CAD có thể sai gấp nghìn lần. Hai ô nhập là ô chữ (inputmode=decimal) nên trình duyệt không chặn (gốc ở 2.1-C4) | waybill_service.money(); docs/test-log.md dòng 1201 (TL-03 S1 'Mới') | Người dùng | Tích hợp HTTP | Tự động (sau khi chủ dự án chốt) | P0 |
| C2 | Phạm vi dòng vận đơn của Leader/Manager Sale lệch với phạm vi đơn gốc. Với Manager Sale, hai nút Tôi và Toàn bộ cho cùng một tập dòng, trái giả định của ADR-033 (bổ sung 10.10.2026). Chưa xác minh bằng chạy | record_service.create_record; forms_builder/managers.py DataRecordQuerySet.in_scope; test_waybill_new.py::test_direct_routes_permissions_both_directions so với test_order_consolidation.py::test_original_order_scope | QA | Phân quyền (ma trận) | Tự động | P0 |
| C3 | Kho chứng từ chưa có bài cho các nhánh từ chối, lỗi và replay: CEO, Sale/CSKH/MKT nhận 403; replay khác nội dung phải ra 409; khôi phục khi trùng Ref; gỡ hết ảnh; remove=id ngoài chứng từ; file_path đi ra ngoài thư mục | crm/tests/test_payment_documents.py; payment_service.can_create/can_manage; image_for (is_relative_to) | QA | Phân quyền + tích hợp | Tự động | P0 |
| C4 | Chiều bị từ chối của Lên đơn, Tóm tắt, kiem-khach với Kế toán, CSKH, và CEO có gắn bộ phận Sale (ADR-044). kiem-khach trả về tên, email, lý do danh sách đen | waybill_views preview_order, kiem_khach không gọi assert_business_write | QA | Phân quyền HTTP | Tự động | P1 |
| C5 | AC-26.1–26.6 vẫn nằm trong HOAN của test_truy_vet dù đã có bài thật | app/tests/test_truy_vet.py; test_payment_documents.py chỉ ghi mã AC ở docstring module | QA | Truy vết | Tự động | P1 |
| C6 | Khách được định danh bằng SĐT đúng như gõ, còn "mua lại" dùng phone_key: gõ khác định dạng thì không báo danh sách đen và sinh thêm Customer thứ hai | order_service find_customer, customer_notice, create_order; forms_builder.models.phone_key | Người dùng | Tích hợp service + HTTP | Tự động | P1 |
| C7 | Hết phiên khi phân công trong ô: người dùng tưởng đã lưu. Với chứng từ thì hiện lỗi SyntaxError tiếng Anh (xem 2.9) | app/static/js/waybill-feedback.js responseJSON(); app/static/js/payments.js json() | Người dùng | E2E trình duyệt | Tự động | P1 |
| C8 | Hết phiên khi bấm Lưu đơn hoặc Lưu trong hộp Chi tiết (HMTX nhận HX-Redirect) làm mất đơn đang gõ. Chưa xác minh trình duyệt có giữ nháp không | core/middleware._ve_dang_nhap; waybill.js htmx.ajax | Người dùng | E2E trình duyệt | Tự động | P1 |
| C9 | seed_perf delete_fake_records vỡ IntegrityError khi dòng giả đã có lịch sử ô hoặc chứng từ (khoá PROTECT) | core/management/commands/seed_perf.py; crm/models.py dòng 59; orders/payment_models.py dòng 9. Chưa chạy | QA | Lệnh quản trị | Tự động | P1 |
| C10 | xoa_bang_van_don_cu vỡ khi bảng cũ còn đơn đã bỏ (Order.objects lọc sẵn đơn xoá mềm) | orders/management/commands/xoa_bang_van_don_cu.py; orders/models.py dòng 164, 214–216. Chưa chạy | QA | Lệnh quản trị | Tự động | P1 |
| C11 | kiem_tra_du_lieu: nhánh "đơn đã bỏ, dòng còn sống" chưa có bài; đơn có record=None (đúng AC-36.5) bị báo lệch | integrity_service.don_mo_coi (78–87) | QA | Lệnh quản trị | Tự động | P1 |
| C12 | Sản phẩm ngừng bán: Tóm tắt vẫn tính tổng, bấm Lưu thì báo "không tìm thấy sản phẩm" | product_service.entry_products; waybill_service.validate_items; order_service.create_order (lọc is_active) | Người dùng | Tích hợp HTTP | Tự động | P1 |
| C13 | Nhật ký "Cập nhật khách" ghi SĐT và email, trái AC-18.3, AC-20.3 | order_service.create_order; test_len_don.py::test_len_don_sinh_dong_nhat_ky chỉ soi dòng CREATE mới nhất | QA | Tích hợp service | Tự động | P1 |
| C14 | Đường thêm sản phẩm qua cột Chọn không theo luật TL-72: Manager bộ phận khác thêm được, Leader Sale lại bị chặn | choice_service.add_option → product_service.add_from_label; test_danh_sach_chon.py | QA | Phân quyền HTTP | Tự động | P1 |
| C15 | JPY/KRW nhận phần lẻ: số lưu 1500.50 hiện ra '1.500 ¥'. Cần chủ dự án chốt câu chữ của ADR-031 | core/money.py format_money, CURRENCY_DECIMALS | Người dùng | Tích hợp service | Tự động | P1 |
| C16 | Bài giao diện trình duyệt của Lên đơn, chứng từ (AC-26.6), tiền theo quốc gia chỉ chạy khi bật biến KN_FEEDBACK_BROWSER, KN_PAYMENT_BROWSER, MARKET_CURRENCY_BROWSER, KN_ORDER_HUB_BROWSER | .github/workflows/ci.yml; 4 tệp crm/tests/*_browser* | QA | Giao diện/e2e | Bán tự động | P1 |

Mức thấp (P2):
- create_order biến số lượng/giá rỗng hoặc 0 thành 1 và 0.
- Hai sản phẩm dùng chung cột sl_* do '-' và '_' (dispatch_service.product_column_code_of).
- Ba nhánh lỗi còn lại của create_order.
- URL chuyển tiếp còn lại (BANGTINH_URL rỗng → 503).
- Gửi lại ma_lan_nop khi lỗi xảy ra bên trong create().
- xoa_bang_van_don_cu: nhánh CommandError, tệp ảnh chứng từ mồ côi.
- Khoảng trắng giữa tên khách.
- Mã đơn và ô Ngày quanh nửa đêm.
- 7 thị trường × 7 PTTT chưa tạo thành đơn thật.
- Hai thước đo "số đơn" của khách.
- kiem_khach lộ khách của team khác (cần chủ dự án xác nhận).

Bị bác bỏ:

| Tưởng là thiếu | Thật ra đã phủ bởi |
|---|---|
| Tạo đơn với seller (Admin chọn Sale, Sale bị khoá hoặc khác bộ phận) | crm/tests/test_master_nine.py::test_rejects_unavailable_seller, ::test_admin_selects_seller_without_changing_profile (AC-21.11), ::test_admin_form_uses_actor_and_rejects_forgery |
| URL chuyển tiếp ERP (giữ host, ngoài phạm vi, POST 405) | core/tests/test_lien_ket_dich_vu.py (AC-1.10); orders/tests/test_len_don.py::test_goi_thang_don_ngoai_pham_vi_bi_chan (AC-3.7); test_order_consolidation.py::test_erp_navigation_and_legacy_posts; tests/test_khoi.py |
| Gửi lại mã lần nộp sau lỗi (cơ chế) | reports/tests/test_nop_mot_lan.py; core/submission.py run_once (dùng chung) |
| Từ chối Vận đơn và Marketing ở Lên đơn | test_waybill_new.py::test_direct_routes_permissions_both_directions, ::test_view_grant_cannot_edit_or_enter_orders; test_san_pham_moi.py; tests/test_luong_ba_bo_phan.py |
| Phạm vi dòng của Sale staff, CSKH, VĐ, Kế toán, MKT, Admin, CEO | test_pham_vi_toi_toan_bo.py (AC-33.1–33.3); test_chi_admin_xoa_dong.py; test_ceo_chi_doc_luoi.py (AC-21.17); test_waybill_feedback.py |
| Xoá dòng vận đơn để lại đơn gốc mồ côi; khôi phục dòng không khôi phục đơn (ADR-049, AC-6.12) | app/orders/tests/test_xoa_dong_huy_don.py (chốt 06.10.2026: xoá dòng qua record_service.delete_record thì bỏ đơn, có nhật ký nêu mã đơn); test_bo_don_chi_admin.py, test_len_don.py (chiều Bỏ đơn) |

### 2.5 Báo cáo ngày, Báo cáo tổng hợp, Tổng quan (reports, dashboard) — 40 tệp kiểm

| Mã | Lỗ hổng và rủi ro | Bằng chứng | Góc nhìn | Loại | Hình thức | Ưu tiên |
|---|---|---|---|---|---|---|
| C1 | Báo cáo tổng hợp kiểu cũ cộng CAD với USD thành một số (trái ADR-046, BR-8). Khi không có ?nguon, trang mặc định có thể rơi vào bản kiểu cũ (pick_table lấy tables[0]) | reports/services/summary_service.py build_context (184–189), build_export (256–260), _compare, pick_table (77–78); dashboard_service._marketing (155); aggregations.summarize (208–257); deploy/entrypoint.sh dòng 49 | Người dùng | Tích hợp + HTTP | Tự động | P0 |
| C2 | Sửa báo cáo Sale và đổi Thị trường thì Loại tiền tự đổi còn số tiền giữ nguyên (1.000.000 CAD thành 1.000.000 USD), không có bước xác nhận. Chưa xác minh chủ dự án muốn hành vi nào | daily_service.amend (dòng 284), protected_values (56–63) | Người dùng | Tích hợp + HTTP | Tự động | P0 |
| C3 | Nộp/sửa báo cáo nhận số âm, nên CPO, Giá Mess âm lọt vào Báo cáo tổng hợp; trong khi threshold_service lại chặn âm. docs/04 không có AC nào về việc này, cần chủ dự án chốt | record_service.parse_value (105); threshold_service.parse | Người dùng | Unit + HTTP | Tự động | P1 |
| C4 | Bộ phận/Team của DailyReport lệch với dòng số liệu khi người nộp thuộc bộ phận khác (Admin có hồ sơ bộ phận, hoặc người được cấp FILL chéo), làm lộ quyền sửa | daily_service.submit (418–422); record_service.create_record (210–216); views.bao_cao_ngay (76); grant_service.can_fill (128) | QA | Phân quyền + tích hợp | Tự động | P1 |
| C5 | Hai người sửa cùng một báo cáo: tuần tự hoá chỉ dựa vào select_for_update, chưa có bài 2 luồng | lifecycle_service.lock (khoá chia sẻ); amend (271–276) | QA | Đồng thời | Tự động | P1 |
| C6 | Ngưỡng màu: next trỏ ra ngoài ('https://evil.test', '//evil.test'), Leader POST, CEO POST, hai người lưu cùng lúc thì mất phần sửa của một người | activity_views.thresholds (91–93); threshold_service.update (93) | QA | Bảo mật + phân quyền HTTP | Tự động | P1 |
| C7 | Thẻ Tổng quan với nguồn ngoài phạm vi: lỗi bị nuốt vào logger.exception, không có DENIED. tu>den cũng bị nuốt | activity_service.select_source (107–114); dashboard_service._khoi (20–28) | QA | Phân quyền + HTTP | Tự động | P1 |
| C8 | Nhánh lỗi của configure_erp_reports và configure_delivery_daily_report chưa có bài. Lệnh chạy trong một atomic nên một nguồn lỗi làm mất cả ba; entrypoint nuốt lỗi | configure_source (105, 131), configure_marketing (175); configure_delivery_daily_report (24/29/33/38); deploy/entrypoint.sh 49–50 | QA | Tích hợp lệnh | Tự động | P1 |
| C9 | CEO gọi thẳng POST /bo/, /khoi-phuc/, GET /da-bo/, POST /tong-hop/nguong/, xuất Excel. Đường ngưỡng màu chỉ dựa vào rank in QUAN_LY_BO_PHAN | grant_service._quan_ly_bo_phan; core/tests/test_quyen_ceo_erp.py chỉ kiểm /bao-cao/ và Lịch sử | QA | Phân quyền HTTP | Tự động | P1 |
| C10 | Gửi lại mã lần nộp của một báo cáo đã bị bỏ thì ra 500 (DoesNotExist), trái NFR-6. Kịch bản: nộp, tự bỏ, bấm Back rồi nộp lại | daily_service.submit_current (dòng 82); core/submission.py run_once | Người dùng | Tích hợp + HTTP | Tự động | P1 |
| C11 | **ADR-008 (báo cáo bọc quanh biểu mẫu):** biểu mẫu nguồn của báo cáo ngày vẫn điền thẳng được qua `/bieu-mau/<code>/dien/`. View bieu_mau_dien gọi form_service.fill → record_service.create_record, ghi dòng vào bảng đích mà không tạo DailyReport. Dòng đó vì vậy không có "Lần nộp", không đi qua daily_service (sửa, bỏ, khôi phục, mã lần nộp). Bài hiện có lại chấp nhận đường này: test_team_he_thong.py dòng 78–84 khẳng định 302 và chỉ soi dòng dữ liệu. grant_service.py dòng 244–251 có phân biệt dòng có và không có DailyReport, nên đây có thể là chủ ý. Chủ ý hay lỗ hổng: chưa xác minh. Cần chủ dự án chốt (chặn, chuyển hướng sang /bao-cao/, hay giữ nguyên) rồi viết bài khẳng định | app/forms_builder/views.py bieu_mau_dien (735–762); app/forms_builder/services/form_service.py fill (292–315); docs/quyet-dinh/008-bao-cao-boc-quanh-bieu-mau.md; app/reports/tests/test_team_he_thong.py dòng 78–84 (CEO thì 403 ở dòng 100–102, AC-44.6) | QA | Phân quyền + tích hợp HTTP | Tự động | P1 |

Mức thấp (P2):
- Kế toán: tổng số, tệp Excel, nhật ký EXPORT.
- Ranh giới nửa đêm khi nộp (chỉ lệch hiển thị).
- Hộp ?khung=1 với dữ liệu biên (ra 403 thay vì 404).
- Chèn công thức Excel ở đường nguồn đã cấu hình (excel.py dòng 113).
- Nút ✎ ở dòng không có DailyReport.
- Lịch sử: tu/den hỏng lặng lẽ thành "hôm nay".
- resync_table so với compute_report của MKT.
- Migration 0006 với hơn 500 dòng.
- app/dashboard không có thư mục tests.
- Unit Node cho report-entry.js, staff-code.js và report-filters.js (xem 2.9).
- nap_bao_cao_mau --xoa-cu thực chất chỉ xoá mềm.
- "Lần N" bị đánh số lại theo bộ lọc.

Bị bác bỏ:

| Tưởng là thiếu | Thật ra đã phủ bởi |
|---|---|
| Liên kết nhom=person/department trên Tổng quan | reports/tests/test_tung_lan_nop_mac_dinh.py::test_khong_con_cach_xem_va_che_do (AC-22.23); test_bao_cao_theo_team.py (AC-22.20). Hai liên kết thừa là nợ giao diện, không phải thiếu bài |
| erp-table-focus.js, Toàn màn hình, phím Escape | reports/tests/test_bo_cuc_bao_cao_e2e.py (AC-42.19, AC-42.20, TL-75), chạy trong CI |
| Công thức Excel ở đường kiểu cũ | forms_builder/tests/test_xuat_khong_cong_thuc.py::test_xuat_bao_cao_tong_hop_khong_co_cong_thuc (AC-7.14) |
| Ô số nguyên gõ '12,5' thành 125 | Hành vi chủ ý: reports/tests/test_o_nhap_so_e2e.py::test_o_so_tu_chen_dau_cham_va_may_chu_nhan_dung |
| Cột loai_tien/thi_truong không phải choice | test_configure_currency_options.py::test_existing_vnd_currency_column_gets_market_currencies (AC-22.12) |
| Kế toán có mở được Báo cáo tổng hợp không | test_admin_sua_tong_hop.py::test_vai_khac_khong_thay_nut_sua (AC-50.2) |
| Cột Nhân sự và Leader, nhóm theo ngày × nhân sự; 100 nhóm mỗi trang (ADR-035) | reports/tests/test_activity.py dòng 268 (AC-22.10), dòng 437 (AC-22.11: mặc định 100 nhóm, dòng "Tổng trong bộ lọc" tính trên toàn bộ kết quả) |

### 2.6 Nhóm Nội bộ: Tài liệu, Bảng tin, Công việc, Đánh giá nhân sự, Tài nguyên — 54 bài kiểm

Con số 54 lấy từ dữ liệu và được tính theo từng bài, trải trên app/{documents,feed,taskboard,culture,resources}/tests/ cùng các tệp xuyên module.

| Mã | Lỗ hổng và rủi ro | Bằng chứng | Góc nhìn | Loại | Hình thức | Ưu tiên |
|---|---|---|---|---|---|---|
| C1 | CEO (ADR-044) chưa có bài HTTP nào ở 5 app. CEO GET form ghi được 200; POST bị 403 mà không ghi DENIED; POST /tai-lieu/muc-moi/ trả 302. Chỉ một lớp dịch vụ đang chặn | core/permissions.py dòng 28–30, 76–80; core/constants.py dòng 19–25; resources/views.py; documents/views.py::tai_lieu_muc_moi; tests/test_khoi.py dòng 90 | QA | Phân quyền HTTP | Tự động | P0 |
| C2 | Sao lưu chỉ là pg_dump, không chép storage/tai-lieu. Khôi phục xong thì tải tài liệu báo "Tệp không còn trên máy chủ" | scripts/backup.sh; core/services/backup_service.py; docs/backlog.md dòng 2373, 2419 (K30); deploy/production/compose.yml dòng 24, 104 | Người dùng | Sao lưu – khôi phục | Bán tự động (diễn tập) | P0 |
| C3 | Bảng xếp hạng chỉ đọc Order tạo qua Lên đơn, lệch với lưới vận đơn: dòng nhập từ tệp không được tính; sửa Chi tiết không cập nhật Order.total; khôi phục dòng làm đổi bảng của tháng đã thưởng. Cần chủ dự án chốt | orders/models.py dòng 232–249; waybill_service.after_create (264), after_restore (93); leaderboard_service.sales_leaderboard | Người dùng | Tích hợp nghiệp vụ | Tự động | P1 |
| C4 | Thưởng sao chạy lại sau khi thứ hạng đổi thì sinh thêm dòng sao. Ở local, lệnh chạy mỗi lần bật máy | culture/services/leaderboard_service.py award_monthly_stars; deploy/entrypoint.sh; deploy/docker-compose.yml dòng 57 | QA | Tích hợp | Tự động | P1 |
| C5 | Đổi trạng thái việc từ tab cũ: việc đã Xong bị mở lại và mất done_at mà không ai biết | taskboard/views.py::cong_viec_trang_thai; task_service.change_status; STATUS_TRANSITIONS | Người dùng | Tích hợp nhiều tab | Tự động | P1 |
| C6 | Hai người sửa cùng một tài nguyên hoặc một việc: người lưu trước bị đè lặng lẽ | resource_service.update_resource; task_service.update_task (không so phiên bản) | Người dùng | Đồng thời | Tự động | P1 |
| C7 | Một đơn KRW lẫn giữa đơn USD làm cả bảng rỗng và thưởng sao tháng đó hỏng. Nhánh báo người vận hành chưa có bài | core/money.py::to_vnd; culture/tasks.py (bao_nguoi_van_hanh); deploy/production/README.md dòng 118–120 | QA | Tích hợp + vận hành | Tự động | P1 |
| C8 | Ranh giới tháng giờ Việt Nam và làm tròn ROUND_HALF_UP theo từng nhóm chưa có bài | leaderboard_service.month_range; to_vnd (187–192) | Người dùng | Unit tiền/thời gian | Tự động | P1 |
| C9 | CEO không có bộ phận thì không tạo được việc của chính mình | task_service._bo_phan_cua; docs/quyet-dinh/044 dòng 18–25 | Người dùng | Tích hợp | Tự động | P1 |
| C10 | Lọc Công việc theo người ngoài phạm vi trả danh sách rỗng thay vì từ chối (Tài nguyên trả 404 trong cùng tình huống) | taskboard/views.py::cong_viec; resources/views.py::tai_nguyen | QA | Phân quyền HTTP | Tự động | P1 |
| C11 | VPS đặt RUN_MIGRATIONS '0' nên không chạy bù thiệp sinh nhật và thưởng sao lúc bật máy. Celery beat có chạy bù hay không: chưa xác minh | deploy/production/compose.yml dòng 12; deploy/entrypoint.sh; README dòng 127–128 | QA | Vận hành / cấu hình | Bán tự động | P1 |
| C12 | HTMX của 5 màn chưa được kiểm trên trình duyệt thật (OOB, hx-sync, hộp lỗi 400, phan-trang.js) | không có tệp e2e; scripts/kiem-thu-erp-hub.cjs chỉ đi tab Tài liệu | Người dùng | E2E | Tự động | P1 |

Mức thấp (P2):
- XSS nội dung người dùng: chỉ là rủi ro hồi quy, autoescape đã bật.
- Tài liệu: JPG/PNG được nhận; tên tệp bị cắt [:200]; tên NFD.
- Tạo mục trùng tên đồng thời ra 500.
- Thiệp sinh nhật với múi giờ, chạy tay `--ngay`.
- Màn 390px (AC-13.6).
- recipients() so với can_recognize_user().
- Leader sửa việc và đổi người làm.
- Bộ lọc bí mật Tài nguyên báo nhầm và để lọt.
- Hiệu năng bảng xếp hạng (không có chỉ mục created_at; bài canh chỉ mục chung ở 2.8-C14).
- Chiều phụ thuộc import giữa các app (các kiểm tĩnh kiến trúc khác ở 2.8-C13, C14).
- Tệp trên 11 MB bị Nginx trả 413.
- feed.thiep_sinh_nhat không có nhánh báo lỗi.
- Lịch beat không có bài canh (xem 2.7-C10).

Bị bác bỏ:

| Tưởng là thiếu | Thật ra đã phủ bởi |
|---|---|
| Migration của 5 app chạy ngược rồi chạy xuôi | app/core/tests/test_chuyen_doi.py::test_chay_nguoc_roi_chay_xuoi_lai_duoc (CAC_APP dòng 26–27, chạy trong CI) |
| Quy đổi KRW khi thiếu tỉ giá (đơn lẻ) | reports/tests/test_markets_currencies.py dòng 108–112; culture/tests/test_van_hoa.py::test_bang_xep_hang_doanh_so_thang_nay |
| Nhận diện tệp XLSX/CSV | core/tests/test_excel.py::test_word_va_pdf_nhan_theo_chu_ky_va_duoi và các bài dòng 33–69 |

### 2.7 Nền tảng, vận hành và phi chức năng — 26 tệp kiểm

| Mã | Lỗ hổng và rủi ro | Bằng chứng | Góc nhìn | Loại | Hình thức | Ưu tiên |
|---|---|---|---|---|---|---|
| C1 | **TL-23:** job RUNNING kẹt mãi khi worker chết, lưới báo "đang tính lại" vô hạn. Sao lưu cũng kẹt RUNNING khi gặp lỗi lạ. Không có acks_late. Gộp từ 2.1 và 2.2 | app/core/tasks.py danh_dau_tac_vu_ket (chỉ lọc PENDING); backup_service.run_backup (except BackupError, OSError); core/tests/test_sao_luu.py dòng 214–223; docs/test-log.md dòng 1204 | Người dùng | Tích hợp Celery | Tự động | P0 |
| C2 | cap-nhat-local.bat ghi dấu vết storage/.kn-jsc-lan-truoc dù migrate hỏng; KN JSC.bat ghi dấu vết dù tao_bang_van_don hỏng. Lặp lại sự cố 06.09.2026 | scripts/cap-nhat-local.bat nhãn :web_ok; KN JSC.bat khối `if defined MA_DOI` | QA | Kiểm tĩnh script + Windows | Thủ công | P0 |
| C3 | **Đã sửa ở #116 (TL-98).** Trước đó do_hieu_nang không có khoá DEBUG và ghi vào dòng THẬT; khoá DEBUG của seed_perf và nap_du_lieu_van_don chưa có bài. Nay do_hieu_nang có khoá DEBUG và chỉ ghi dòng PERF-*; cả ba khoá có bài. Gộp với 2.8 | core/tests/test_do_hieu_nang.py; core/tests/test_seed_perf_xoa.py; orders/tests/test_nap_du_lieu_van_don.py::test_tu_choi_khi_debug_tat_khong_ghi_gi | QA | Unit lệnh quản trị | Tự động | P0 |
| C4 | Chưa từng phục hồi thật (round-trip). Phía sao lưu đã có core/tests/test_sao_luu.py::test_pg_dump_that_ra_tep_hop_le (dấu `cham`, `skipif` khi máy không có pg_dump): pg_dump thật ra tệp có chữ ký PGDMP và lớn hơn 1 KB (NFR-19). Bài này có chạy trong CI hay không thì chưa xác minh (tuỳ runner có pg_dump và bộ lọc dấu `cham`). Phía phục hồi (run_restore) chỉ có bài dùng runner giả. run_restore không bắt TimeoutExpired; pg_restore chạy không có --exit-on-error/--single-transaction; client 17 so với db 16 (chưa xác minh) | backup_service.run_restore; core/tests/test_sao_luu.py (dòng 290–297 pg_dump thật; phần phục hồi dùng runner giả); docs/04 AC-10.5 'Thủ công'; deploy/Dockerfile | QA | Tích hợp DB + diễn tập | Bán tự động | P0 |
| C5 | NFR-20: bản sao lưu nằm cùng VPS. backup.sh/restore.sh gọi dịch vụ 'web' mà production không có, nên không có quy trình NFR-10 nào đã được thử | knjsc/settings/base.py BACKUP_DIR; deploy/production/compose.yml; diễn tập 08.10 dòng 285 | QA | Vận hành | Thủ công | P0 |
| C6 | /quan-tri/ không khoá, không ghi nhật ký: đã sửa ở #121 (xem 2.1-C1) | — | — | — | — | P0 |
| C7 | TL-85: BANGTINH_GOC gõ sai thì CRM chạy dev (DEBUG=True). Giảm nhẹ: compose.yml đặt cứng giá trị prod | app/knjsc/settings/bangtinh.py; test_kiem_cau_hinh.py; core/checks.py kiem_phien_chung | QA | Unit cấu hình (tiến trình con) | Tự động | P1 |
| C8 | Cờ bảo mật của knjsc.settings.prod (SSL redirect, cookie Secure, HSTS, X_FRAME_OPTIONS) không có bài kiểm | ci.yml chỉ chạy check với settings.test | QA | Unit cấu hình | Tự động | P1 |
| C9 | TL-82/D7: Postgres ghi nguyên câu UPDATE có dữ liệu ô vào log | deploy/production/compose.yml (thiếu log_min_error_statement); compose.vps.yml chưa xác minh | QA | Kiểm tĩnh + dò log | Bán tự động | P1 |
| C10 | Lịch CELERY_BEAT_SCHEDULE và định tuyến crm_heavy không có bài canh | knjsc/settings/base.py dòng 263–285 | QA | Unit cấu hình Celery | Tự động | P1 |
| C11 | Worker chung concurrency 1: một job dài hơn 15 phút làm job PENDING phía sau bị đánh STALE nhầm | deploy/production/compose.yml; core/tasks.py; import_service.run; BACKUP_TIMEOUT_SECONDS | Người dùng | Tích hợp Celery + diễn tập | Bán tự động | P1 |
| C12 | gunicorn production dùng timeout mặc định 30 s, trong khi công cụ đo dùng 60 s: quá hạn là giết cả tiến trình gthread, người dùng nhận 502 | deploy/Dockerfile CMD; scripts/order-code-check/start_app.py dòng 18; scripts/grid-flags-check/run.py dòng 72 | Người dùng | Hiệu năng / sự cố | Bán tự động | P1 |
| C13 | X-Forwarded-For (xem 2.1-C13) và RequestMetricsMiddleware (xem 2.1-C15) | — | — | — | — | P1 |
| C14 | entrypoint.sh, Dockerfile, compose, template nginx không được kiểm tự động | ci.yml không có docker build, compose config, nginx -t | QA | Kiểm tĩnh / smoke container | Tự động | P1 |
| C15 | CI thiếu check --deploy, pip-audit, --cov, khối permissions; bài HTTPS hai tên miền luôn bị bỏ qua | .github/workflows/ci.yml; core/tests/test_shared_login_browser.py | QA | CI | Tự động | P1 |
| C16 | Trang lỗi 413/502/504 của nginx, 400 và CSRF của Django không phải tiếng Việt (thiếu 400.html, 403_csrf.html), trái NFR-6. Header Server lộ phiên bản nginx (D18) | nginx.conf.template; app/templates (chỉ có 403/404/500); docs/kiem-chung-phat-hanh-vps-20260918-excel.md dòng 34 | Người dùng | HTTP + thủ công qua proxy | Bán tự động | P1 |
| C17 | Thư lỗi 500 mặc định kèm GET/POST chứa dữ liệu khách. EMAIL_HOST… không đọc từ biến môi trường (NFR-8). Nội dung thư chưa chạy thử | knjsc/settings/base.py LOGGING, EMAIL_*; D12 | QA | Unit (caplog, mail.outbox) | Tự động | P1 |
| C18 | Local và production lệch nhau ở cache Redis 'crm', nên kiểm tay ở Chặng 2 không chạm tới đường làm mất hiệu lực cache (AC-10.26) | deploy/docker-compose.yml (không đặt CRM_CACHE_URL); compose.yml production; master_grid_service.py, grid_service.py dòng 474, sidebar_service.py dòng 100 | QA | Thủ công Chặng 2 | Bán tự động | P1 |
| C19 | KN JSC.bat không dựng lại image khi commit cũ không còn hoặc mất tệp dấu vết | KN JSC.bat bước 4 | QA | Windows | Thủ công | P1 |
| C20 | Dịch vụ ứng dụng không có healthcheck; log json-file không giới hạn | compose.yml; Dockerfile; README "compose.yml chưa đặt logging:" | QA | Vận hành | Bán tự động | P1 |
| C21 | VPS 300k dòng, 10 người vượt cả ba ngưỡng (đọc 5.043 ms, lưu 2.341 ms, hỏi thăm 3.868 ms). p95 sau phát hành chỉ có 7–52 mẫu | docs/kiem-chung-300k-10-nguoi-20260916.md; docs/kiem-chung-phat-hanh-vps-20260929.md | Người dùng | Hiệu năng | Bán tự động | P1 |
| C22 | Quay lui/tiến lại: scripts/grid-flags-check/deploy.sh vẫn dùng collectstatic không --clear (TL-80/D1), không migrate, chỉ chạy `check` | deploy.sh dòng 37, 61 | QA | Diễn tập / kiểm tĩnh | Bán tự động | P1 |

Mức thấp (P2):
- .env cạnh compose chưa nằm trong .gitignore; kho không có .dockerignore.
- Giữ nhật ký hoạt động 24 tháng (NFR-17).
- NFR-18 (mức tăng dung lượng lưu trữ dưới 5 GB mỗi năm, docs/02 dòng 269): chưa có ca đo toàn cơ sở dữ liệu. Chỉ có crm/tests/test_master_nine_storage.py (dấu `cham`, `skipif` KN_NINE_STORAGE) đo pg_table_size và pg_indexes_size của hai bảng crm_gridcellhistory, crm_gridmutationreceipt trên DB test riêng. Cần một phép đo bán tự động: chụp pg_database_size cùng thư mục storage/ trên VPS theo tháng rồi ngoại suy theo năm. Góc nhìn QA, loại Hiệu năng/dung lượng.
- Ghim phiên bản phụ thuộc (playwright 1.56.0 so với 1.56.1; python-dotenv không ai dùng).
- Script kiểm tải (TL-29, TL-30; `set -uo pipefail` thiếu -e).
- Xoay vòng sao lưu theo số bản; tên trùng giây; tệp .part bỏ lại.
- Tài liệu lệch: AC-10.3 vẫn ghi "Chưa làm"; AC-10.6 bị nhầm với AC-10.8.

Bị bác bỏ:

| Tưởng là thiếu | Thật ra đã phủ bởi |
|---|---|
| Trang Tác vụ nền: quyền chéo vai | core/tests/test_ma_tran_quyen_hai_dich_vu.py; forms_builder/tests/test_nhap_xuat.py::test_tac_vu_nhap_cua_nguoi_khac_khong_thay; crm/tests/test_dich_vu_bangtinh.py dòng 63 |
| Dọn tệp xuất quá 24 giờ | core/tests/test_sao_luu.py::test_don_tep_qua_24_gio; test_nhap_xuat.py (unlink rồi tải) |
| Biến tỉ giá sai định dạng | app/tests/test_ti_gia.py::test_ti_gia_doc_tu_moi_truong (chỉ còn thiếu ca VND=2) |
| Mã đơn trùng chặn migrate | crm/tests/test_ma_don_khong_trung.py (AC-36.12, AC-36.15, TL-76); test_chu_viet_mot_dang.py (TL-79/D5) |
| Lọc mật khẩu khỏi AuditLog | core/tests/test_audit.py::test_khong_ghi_du_lieu_nhay_cam_vao_nhat_ky, ::test_luoc_bo_theo_ranh_gioi_tu |
| Cache CRM ở local chờ 0,2 s | Kết nối bị từ chối ngay (chưa đo). Vấn đề thật là local khác production, đã ghi ở C18 |
| dashboard vắng trong CAC_APP | app/dashboard/models.py không có Model nào nên không cần migration |
| pg_dump chưa từng chạy thật trong bài kiểm | core/tests/test_sao_luu.py::test_pg_dump_that_ra_tep_hop_le (dấu `cham`, `skipif` khi không có pg_dump). Chỉ phần phục hồi còn thiếu (C4) |

### 2.8 Hạ tầng kiểm thử, truy vết AC và tài liệu kiểm thử — 22 tệp kiểm

| Mã | Lỗ hổng và rủi ro | Bằng chứng | Góc nhìn | Loại | Hình thức | Ưu tiên |
|---|---|---|---|---|---|---|
| C1 | Ma trận phân quyền chép tay lệch docs/04 mục 3 ở 2/50 ô: Bảng vận đơn × Staff VĐ và Nhập tệp Sale × Leader Sale. Hệ thống thật (ADR-045) từ chối cả hai, nhưng docs/04 vẫn ghi "Vào được". Docstring dẫn "Mục 13 điều 2", đúng ra là mục 18 điều 2 | commit 5e710ed; docs/04-tieu-chi-nghiem-thu.md dòng 120, 122; app/tests/test_ma_tran_phan_quyen.py; forms_builder/tests/test_nhap_xuat.py::test_quyen_nhap_hai_chieu (docstring mâu thuẫn với assert) | QA | Phân quyền / truy vết | Tự động + sửa tài liệu | P0 |
| C2 | Chromium hỏng thì cả bộ trinh_duyet bị bỏ qua mà CI vẫn xanh. Có 24 AC chỉ có bài trình duyệt: AC-6.14, 10.4, 10.12, 10.17, 10.19, 10.22, 11.38, 11.40, 20.6, 21.12, 21.14, 21.20, 22.19, 22.21, 32.1, 42.15, 42.17, 42.19, 42.20, 42.21, 48.5, 50.9, 50.10, 50.11 | tests/e2e/conftest.py dòng 33–39; reports/tests/test_bo_cuc_bao_cao_e2e.py:26, 31; crm/tests/test_luoi_dong_trong_va_ghim_e2e.py:25, 30; ci.yml chỉ có -rs | QA | Hạ tầng CI | Tự động (chặn khi số bài bỏ qua > 0) | P0 |
| C3 | test_truy_vet tính là "đã có bài" cả bài luôn bị bỏ qua (AC-20.6) và docstring cấp module (AC-20.6, 21.1, 24.1, 27.3) | app/tests/test_truy_vet.py _ma_trong_bai_kiem; crm/tests/test_feedback_browser_server.py; docs/06 dòng 256 | QA | Meta / truy vết | Tự động | P1 |
| C4 | test_khoi chấp nhận mã 200, dùng pk=999999 và code='khong-ton-tai', thiếu staff_kt, ceo, leader_vd, manager_vd, chỉ gọi GET, chạy với GRID_ONLY_TABLES của ERP | app/tests/test_khoi.py MA_CHAP_NHAN, CAC_VAI_TRO, _tham_so_mau | QA | Phân quyền / khói | Tự động | P1 |
| C5 | Settings thật của dịch vụ 8021 (GRID_ONLY_TABLES = set(), ROOT_URLCONF) không bài nào khẳng định; nhánh BANGTINH_GOC=prod chưa từng được nạp | knjsc/settings/bangtinh.py; core/tests/test_kiem_cau_hinh.py::_nap_bangtinh; deploy/production/compose.yml dòng 67–68 | QA | Cấu hình | Tự động | P1 |
| C6 | **Đã sửa ở #118 (TL-90):** fixture có `ceo`, `cskh`, `leader_vd`, `manager_vd` và bộ phận cskh; du_lieu_mau có `giamdoc`, `kt.staff`, `cskh.staff`, `vd.leader`. Còn thiếu Leader MKT, Leader/Manager Kế toán (gộp 2.3-C9) | app/conftest.py nguoi_dung (15 tài khoản); du_lieu_mau.py dòng 64–68; docs/tai-khoan-mau.md | QA / Người dùng | Fixture + dữ liệu mẫu | Tự động | P1 |
| C7 | docs/06 đã cũ: ghi chưa có CI, còn xfail, AC-10.3 chưa làm, thiếu AC-10.8 | docs/06 dòng 80, 142, 184–197, 189, 212, 247, 249, 251, 373 | Người dùng | Tài liệu | Thủ công | P1 |
| C8 | docs/07 không khớp hệ thống: chuột phải giờ mở Lịch sử ô (AC-21.13), Báo cáo MKT trong CRM trái ADR-040, nhập tệp/cấp quyền Sale trong CRM ra 404; không có bước cho CEO, Kế toán, CSKH, ADR-049, ADR-050 | docs/07 dòng 31, mục 3.2–3.4, dòng 129–131; master-grid.js:1228; urls_bangtinh.py _chi_bang_van_don | Người dùng | Tài liệu / kiểm tay | Thủ công | P1 |
| C9 | 23 tệp test dùng đồng hồ thật, không có cơ chế giả ngày. TL-70 đã đỏ đúng ngày 01.10 | grep freezegun/time_machine: 0 kết quả; docs/test-log.md:349–363 | QA | Hồi quy thời gian | Tự động | P1 |
| C10 | Khoá DEBUG của seed_perf: có bài từ #116 (xem 2.7-C3) | — | — | — | — | P1 |
| C11 | TL-71 còn mở: e2e khẳng định p95 ≤100 ms trên runner dùng chung | tests/e2e/test_ghi_chu_tu_gian_dong.py:63, 659; docs/test-log.md:274 | QA | Độ ổn định CI | Tự động | P1 |
| C12 | AC-11.10/11.20 chỉ được phủ lẻ tẻ: phím mũi tên chỉ được nhấn 2 lần, chưa ai kiểm nút ↶ và giới hạn 100 bước. Script unit không có trong CI (xem 2.3-C1) | tests/test_truy_vet.py HOAN; scripts/kiem-thu-grid-jump-unit.cjs:9 | QA | E2E / unit JS | Tự động | P1 |
| C13 | **Kiểm tĩnh kiến trúc, phạm vi quyền:** chưa có bài quét mã nguồn cho Cấm 1, Cấm 11 và Bắt buộc 11 của CLAUDE.md (truy vấn dữ liệu có phạm vi phải qua Custom Manager `in_scope`, view không gọi `.objects.filter()` trực tiếp). Một view mới gọi thẳng `Model.objects.filter/get` trên model có phạm vi sẽ lọt qua mà CI vẫn xanh. Grep các tệp kiểm có dùng `ast`/`rglob`/`os.walk` chỉ ra test_giao_dien.py (kiểm giao diện tĩnh), test_truy_vet.py, test_payment_browser_server.py, e2e/test_dat_lai_mat_khau.py. Không tệp nào quét views.py. Đề xuất: bài dùng `ast` của thư viện chuẩn (không thêm thư viện, quy tắc 8), duyệt `app/*/views*.py` và `*_views.py`, lấy danh sách model có phạm vi từ các QuerySet có `in_scope` (ví dụ forms_builder/managers.py TableDefQuerySet, FormDefQuerySet, DataRecordQuerySet), kèm danh sách ngoại lệ ghi rõ lý do | CLAUDE.md "Không được làm" #1, #11; "Bắt buộc làm" #11; app/core/managers.py apply_scope | QA | Kiểm tĩnh kiến trúc | Tự động | P1 |
| C14 | **Kiểm tĩnh kiến trúc, chỉ mục:** chưa có bài canh Bắt buộc 9 (cột lọc hoặc tìm phải có chỉ mục) và Bắt buộc 12 (cột JSON dùng để lọc phải có GIN). GinIndex hiện có ở app/org/models.py dòng 144, app/forms_builder/models.py dòng 531 (`record_data_gin`) và app/resources/models.py, nhưng thêm bộ lọc mới mà quên chỉ mục thì không bài nào bắt. Một ví dụ đã thấy: bảng xếp hạng không có chỉ mục created_at (2.6, mức thấp). Đề xuất: bài đọc `Model._meta.indexes` và `db_index` qua `django.apps`, đối chiếu với danh sách trường được dùng trong bộ lọc và ô tìm (forms_builder/query.py, các view danh sách); hoặc quét migration tìm GinIndex cho mọi JSONField có lọc | CLAUDE.md "Bắt buộc làm" #9, #12; docs/kiem-chung-300k-10-nguoi-20260916.md (2.7-C21) | QA | Kiểm tĩnh kiến trúc + migration | Tự động | P1 |

Mức thấp (P2):
- Regex truy vết lỏng; bộ đếm docs/06 so bằng chuỗi con.
- TL-67: quá 5 giây chỉ cảnh báo.
- docs/backlog.md mục 0 còn liệt kê nợ đã đóng (dòng 207–241).
- Chú thích trong ci.yml sai số liệu.
- Cache 'crm' chưa kiểm với Redis thật; grid-options/grid-products.
- Không đo bao phủ (pytest-cov và app/.coveragerc có sẵn; K5 cố ý không đặt ngưỡng).
- 3 script không ai nhắc tới: kiem-thu-erp-export.py, kiem-thu-optimization-browser.cjs, kiem-thu-optimization-e2e.cjs.
- testpaths không có bài canh.
- Lệnh du_lieu_solarpunk không có bài.
- Bắt buộc 1 (danh sách mặc định 25 dòng): app/core/pagination.py (PAGE_SIZES = (25, 50, 100)) đã có core/tests/test_phan_trang.py, test_phan_trang_giu_tham_so.py. Chưa có bài quét mọi view danh sách xem có dùng hàm phân trang này không. Ngoại lệ đã chốt: lưới vận đơn GRID_PAGE_SIZE = 100 (core/constants.py dòng 105) và Báo cáo hoạt động 100 nhóm (AC-22.11, ADR-035).
- Bắt buộc 7 (hằng số chỉ khai một chỗ): chưa có bài canh. Ví dụ đã thấy: số 25 khai ở knjsc/settings/base.py dòng 197 (PAGE_SIZE_DEFAULT) và lặp lại làm giá trị dự phòng ở core/pagination.py dòng 17, 65.
- Đồng bộ skill: app/tests/test_dong_bo_skill.py gọi scripts/dong-bo-skill.py `run()` để khẳng định `.claude/skills` khớp nguồn `.agents/skills` (docs/dong-bo-ai-nhieu-may.md). Bài này và test_gom_p95.py đọc tệp nằm ngoài app/, nên container phải mount ../scripts, ../.agents, ../.claude cùng bốn tệp ngữ cảnh ở gốc kho (deploy/docker-compose.yml dòng 64–78). deploy/docker-compose.solarpunk.yml chỉ mount ../docs (dòng 36), nên chạy pytest trong compose đó sẽ gặp FileNotFoundError (suy từ đọc cấu hình, chưa chạy). CI lấy cả kho nên vẫn xanh.
- Công cụ của ADR-028 không có trong CI và không có bài: knjsc/settings/solarpunk_preview.py (cookie riêng `kn_solarpunk_session`), deploy/docker-compose.solarpunk.yml, scripts/audit-solarpunk.cjs, scripts/solarpunk-diff.py, kiem-thu-solarpunk*.cjs, profile-solarpunk.cjs, solarpunk-browser.cjs (xem 2.9-J7).
- Hai tệp trùng số ADR-022 (022-ban-dieu-hanh-kn-crm.md, 022-bao-cao-hoat-dong-erp.md), xem phần Cách đọc. Cần đánh số lại một tệp và sửa các chỗ dẫn.

Bị bác bỏ:

| Tưởng là thiếu | Thật ra đã phủ bởi |
|---|---|
| Đường dẫn chung ERP/CRM và guard _chi_bang_van_don không được quét | core/tests/test_ma_tran_quyen_hai_dich_vu.py::test_duong_dan_chung_deu_da_ra_quyen (AC-1.12), ::test_quyen_tung_vai_o_hai_dich_vu (8 vai × 2 URLconf); crm/tests/test_crm_chi_van_don.py (AC-40.2) |
| test_khoi bỏ qua tham số lạ mà không báo | Hiện có 0 route bị bỏ qua: chỉ dùng `<slug:code>`, `<int:pk>`, `<slug:ma_cot>` |
| AC-11.10/11.20 hoàn toàn không có hồi quy trong CI | test_master_grid.py::test_undo_rejects_changed_cell_and_limits; test_shared_grid.py; test_shared_integrity.py; tests/e2e/test_ghi_chu_tu_gian_dong.py (Ctrl+Z/Y, AC-11.44); tests/e2e/test_admin_xoa_dong.py |
| Không có Redis nên nhánh trúng cache không được kiểm | crm/tests/test_khoi_luoi_dem.py (AC-10.26); test_optimization.py; test_thong_ke_lien_ket_nguon.py (AC-40.9, TL-89); CRM_OPT_STATS mặc định là 0 |
| AC-3.6 (ngoài phạm vi phải từ chối) không có bài canh | Có ở 8 tệp: org/tests/test_org_scope.py, forms_builder/tests/test_nhap_xuat.py, test_man_hinh_bang.py, reports/tests/test_summary_scope.py, test_ma_tran_phan_quyen_bao_cao.py, core/tests/test_ra_soat.py, test_scope.py, test_permissions.py |
| 5 script Node không ai nhắc tới | Chỉ đúng với 3 tệp; kiem-thu-shared-advanced.cjs và optimization-unit có người nhắc |

### 2.9 JS phía trình duyệt — 19 tệp trong app/static/js

Phần này chủ yếu gom lại các lỗ hổng phía trình duyệt đã ghi ở trên. Riêng J7 (ADR-028) là dữ kiện mới, chưa có ở các mục trước.

Bài kiểm hiện có:
- 10 script đơn vị Node, đều chạy tay và không có trong CI: 9 script của lưới kể ở 2.3-C1, cộng scripts/kiem-thu-date-inputs.cjs.
- E2E Playwright chạy trong CI: 19 tệp trong app/tests/e2e, cộng các tệp e2e trong crm/tests và reports/tests.

| Tệp JS | Bài kiểm hiện có (theo dữ liệu) | Chỗ thiếu |
|---|---|---|
| master-grid.js, master-working-copy.js, master-row-geometry.js | 9 script đơn vị Node; e2e test_luoi_hoi_nhe, test_mat_mang_e2e, test_ghi_chu_tu_gian_dong… | 2.3-C1, 2.3-C3, 2.3-C7, 2.1-C7 |
| date-inputs.js | kiem-thu-date-inputs.cjs; tests/e2e/test_o_ngay_tu_dinh_dang.py | — |
| erp-table-focus.js | reports/tests/test_bo_cuc_bao_cao_e2e.py; kiem-thu-erp-table-focus.cjs | — |
| report-entry.js | reports/tests/test_o_nhap_so_e2e.py | Chưa có unit Node cho docSo, lamTron, tinh (2.5, mức thấp); bỏ dấu ở ô integer (2.2-C4) |
| order-entry.js, waybill.js | test_tom_tat_len_don_e2e.py; kiem-thu-order-entry.cjs | Hết phiên với HTMX (2.4-C8) |
| waybill-feedback.js | tests/e2e/test_phan_cong_o_chon.py; kiem-thu-feedback-ui.cjs | Không kiểm `redirected` (2.4-C7) |
| payments.js | kiem-thu-payment-ui.cjs; test_payment_browser_server.py (`skipif`) | Không kiểm `redirected` (2.4-C7); thiếu `?v=` (2.3-C10) |
| phan-trang.js | test_phan_trang_khong_tai_lai.py (chỉ /nhan-su/) | 5 màn Nội bộ (2.6-C12) |
| staff-code.js | Phía máy chủ có org/tests/test_ma_nhan_su.py | Chưa có unit JS (2.5, mức thấp) |
| loi-mang.js | test_mat_mang_e2e.py (mất mạng) | Chỉ bọc TypeError, không xử lý chuyển hướng |
| grid-focus.js (chế độ tập trung lưới CRM, ADR-028) | Nạp ở app/templates/crm/base_bang_tinh.html dòng 105 (có `?v=`); chỉ có kiem-thu-solarpunk.cjs, kiem-thu-solarpunk-save.cjs, kiem-thu-solarpunk-conflict.cjs chạy tay | Không có pytest hay e2e trong CI (J7) |
| solarpunk-shell.js (khung, sáng/tối, Thu gọn/Mở rộng, ADR-028) | core/tests/test_giao_dien.py dòng 146, 170–174 (đọc chuỗi tệp JS và base.html, kiểm `id="nut-nen"`, `sp-theme-icon`) | Lựa chọn lưu localStorage, phục hồi trước khi CSS vẽ, đồng bộ giữa các tab và thứ tự Esc chưa có e2e (J7) |
| report-sua.js (hộp sửa Báo cáo tổng hợp) | reports/tests/test_admin_sua_tong_hop_e2e.py (e2e, CI); mã đã kiểm `tra.redirected` ở report-sua.js dòng 81, 173, 179 (dòng 179 báo "Phiên đăng nhập đã hết… số vừa gõ chưa được lưu") | Nhánh hết phiên (dòng 179) chưa có ca e2e khẳng định (chưa xác minh trong tệp e2e) |
| report-filters.js (chip ngày, bộ lọc Báo cáo tổng hợp) | Chỉ có reports/tests/test_date_presets.py dòng 58 khẳng định trang có nạp `report-filters.js`, cộng thuộc tính data-tu/data-den do máy chủ dựng; mã có kiểm `tra.redirected` ở dòng 420 | Không có bài chạy JS (unit Node hay e2e) cho chính logic lọc (2.5, mức thấp) |
| chon.js (ô Chọn, components/o_chon.html, chỉ ở ERP) | Không có e2e; chỉ có bài HTTP phía máy chủ: forms_builder/tests/test_danh_sach_chon.py, orders/tests/test_san_pham_moi.py | Chưa có e2e cho hành vi phía trình duyệt của ô Chọn và nút "＋ Thêm mới…" (liên quan 2.2-C9, 2.4-C14) |
| htmx.min.js | Thư viện ngoài | — |

| Mã | Lỗ hổng phía trình duyệt | Trỏ tới | Ưu tiên |
|---|---|---|---|
| J1 | Unit JS của lưới không chạy trong CI; mốc `indexOf` không được assert | 2.3-C1 | P0 |
| J2 | Hết phiên khi còn nháp trên lưới, ô phân công, chứng từ, Lưu đơn | 2.3-C3, 2.4-C7, 2.4-C8 | P1 |
| J3 | Thiếu `?v=` ở 6 chỗ trong template CRM | 2.3-C10 | P1 |
| J4 | Poll 8 giây giữ phiên | 2.1-C7 | P1 |
| J5 | Ngưỡng p95 ≤100 ms của e2e trên runner chung (TL-71) | 2.8-C11 | P1 |
| J6 | htmx:beforeSwap trong base.html chỉ nhận ra '/dang-nhap/' | 2.1 (mức thấp) | P2 |
| J7 | **ADR-028 (Solarpunk Office):** cần các ca e2e sau. (1) Lựa chọn sáng/tối và Thu gọn/Mở rộng được lưu trong localStorage, phục hồi sau khi tải lại, đồng bộ giữa hai tab cùng origin, và không lưu dữ liệu nghiệp vụ. (2) Chế độ Tập trung của lưới CRM (grid-focus.js) giữ nguyên DOM lưới và nháp đang gõ. (3) Esc đóng lần lượt: lớp đang mở, rồi Công cụ, rồi toàn màn hình, cuối cùng mới thoát Tập trung. Góc nhìn Người dùng; loại E2E/giao diện; Tự động. Kèm một việc tài liệu: ADR-028 dòng 4 ghi "nhánh thử nghiệm `codex/ui-solarpunk`, chưa đưa vào bản đang vận hành", nhưng khung đã có trên main (crm/tests/test_nhap_tao_cap_quyen_crm.py dòng 19 `KHUNG_ERP = 'class="sp-erp"'`; crm/tests/test_dich_vu_bangtinh.py dòng 69, AC-11.31). Trạng thái ADR cần cập nhật; thời điểm gộp vào main: chưa xác minh. Công cụ đi kèm xem 2.8, mức thấp | docs/quyet-dinh/028-solarpunk-office.md; app/static/js/grid-focus.js, solarpunk-shell.js; scripts/kiem-thu-solarpunk.cjs (lỗi thời, 2.3-C7) | P2 |
| J8 | chon.js và report-filters.js chưa có bài nào chạy JS; report-sua.js có e2e nhưng nhánh hết phiên chưa được khẳng định | Bảng tệp JS ở trên; 2.2-C9, 2.4-C14 | P2 |

### Critical Files for Implementation
- /home/user/KNJSC/app/forms_builder/views.py
- /home/user/KNJSC/app/forms_builder/services/table_service.py
- /home/user/KNJSC/app/forms_builder/tests/test_doi_kieu_cot.py
- /home/user/KNJSC/app/core/tests/test_sao_luu.py
- /home/user/KNJSC/app/static/js/report-sua.js
