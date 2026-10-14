> Phần của [Kế hoạch kiểm thử toàn diện KNJSC](../08-ke-hoach-kiem-thu-toan-dien.md) — mục lục, lộ trình P0/P1/P2 và rủi ro còn lại nằm ở tệp đó.

## 4. Góc nhìn người dùng thật: hành trình theo vai

Cách đọc bảng:
- Mọi ca trong mục này nhìn từ phía **người dùng**. Loại kiểm thử mặc định là e2e hành trình; ca nào khác loại thì ghi rõ trong cột.
- Cột "Tự động hoá" ghi hai thứ: hiện đã có tệp kiểm nào, và mức nên đạt (**Tự động / Bán tự động / Thủ công**).
- Tài khoản kiểm tay lấy từ `docs/tai-khoan-mau.md` (`du_lieu_mau`, 16 tài khoản từ 14.10.2026, mật khẩu `matkhaucuatoi`). Tài khoản cho bài máy lấy từ fixture `nguoi_dung` trong `app/conftest.py`.
- ERP chạy ở cổng 8020, CRM ở cổng 8021.

**Chuẩn bị chung.** Từ #118 (14.10.2026) `du_lieu_mau` tạo đủ bốn vai từng thiếu: `giamdoc` (CEO), `kt.staff` (Kế toán), `cskh.staff` (CSKH), `vd.leader`. Fixture `nguoi_dung` có thêm `ceo`, `cskh`, `leader_vd`, `manager_vd`. Máy dựng trước 14.10 thì chạy lại `du_lieu_mau` (xem `docs/tai-khoan-mau.md`).
- Bộ phận `ke-toan` có sẵn từ migration `org/0004`.
- Bộ phận `cskh` do `du_lieu_mau` và fixture `departments` tạo (#118).

### 4.1. Sale Staff (`sale.staff`; bài máy dùng `staff_sale_1`)

| # | Bước | Màn hình / URL | Kết quả mong đợi | Dữ liệu bẩn / thao tác sai | Sự cố | Tự động hoá | Ưu tiên |
|---|---|---|---|---|---|---|---|
| 1 | Đăng nhập ERP | `/dang-nhap/` (8020) | Vào Tổng quan. Thanh bên không có Nhân sự, Bảng dữ liệu (`NavItem bang` cần Rank.MANAGER), Nhật ký | Gõ tên đăng nhập HOA vẫn vào (`CaseInsensitiveModelBackend`). Sai 5 lần thì bị khoá tạm (AC-1.3). Gõ email (FR-1.1): **cần chốt**. Mật khẩu gõ nhầm vào ô tên không được lọt vào nhật ký LOGIN_FAILED (cần chốt) | Bấm Đăng nhập 3 lần liền: cả 3 đều 302, không 500 (AC-1.9). `sale.moi` bị buộc đổi mật khẩu (AC-1.5) | Có bài HTTP ở core. Chưa có e2e riêng. Mức: Tự động | P0 |
| 2 | Bấm **KN CRM** | Tab mới tới 8021 `/` | Không phải đăng nhập lại; thấy trang chủ `tong_quan` của CRM | — | Đăng xuất ở 8021 rồi F5 ở 8020 thì về trang đăng nhập. Trên Staging cookie `knjsc_session_v2` phải có Domain cha, Secure, HttpOnly, Lax (AC-1.10, AC-1.11) | `core/tests/test_shared_login_browser.py` (chạy khi có env SHARED_LOGIN_BROWSER). Phần Staging: Thủ công | P0 |
| 3 | Lên đơn khách mới: Canada, 2 sản phẩm | `/van-don/len-don/` (8021). `/len-don/` của ERP chỉ chuyển tiếp bằng GET (`orders/handoff.py`) | Có mã `DH-…`. Dòng `van_don` có số lượng ở cột `sl_*`, loại tiền CAD. Tóm tắt cập nhật khi gõ (AC-6.1, AC-6.2, AC-6.14) | SĐT `+1 (416)…` vẫn nhận ra khách theo 9 số cuối (`phone_key`). Tên dạng NFD. Gửi kèm trường `seller` trong POST thì bị từ chối (`WaybillOrderForm.clean`). Chưa chọn quốc gia thì tóm tắt báo "Chọn quốc gia hợp lệ…". Đổi quốc gia rồi bấm Huỷ thì giữ USD. Sản phẩm ngừng bán: tóm tắt và nút Lưu phải cùng một kết luận (AC-6.9) | Mất mạng: báo "chưa lưu", có mạng lại thì lưu đúng 1 đơn. Mạng chập rồi bấm lại cùng `ma_lan_nop`: báo "đã lưu từ lần bấm trước" (AC-6.11). Hết phiên khi Lưu: báo rõ và giữ dữ liệu (cần chốt). Máy chậm và đổi quốc gia: tóm tắt cuối cùng phải đúng nhờ AbortController | `tests/e2e/test_tom_tat_len_don_e2e.py`, `test_mat_mang_e2e.py::test_len_don_mat_mang_bao_chua_luu_roi_luu_mot_don`. Hết phiên, mạng chập và máy chậm: chưa có. Mức: Tự động | P0 |
| 4 | Lên đơn lần hai cùng SĐT | Ô SĐT gọi `kiem_khach` (HTMX) | Có lời nhắc khách cũ, tên tự điền khi ô trống. "Mua lại lần" = 2 (AC-11.8) | Khách bị đánh dấu danh sách đen: ô đỏ kèm lý do, vẫn lưu được. Không có màn ghi danh sách đen, phải đặt qua `manage.py shell` (Q25) | Hai tab lưu cùng một khách: hai mã khác nhau, "Mua lại lần" là 1 và 2, nhật ký đổi tên đúng 1 dòng (AC-6.3, AC-6.8) | `tests/e2e/test_hanh_trinh_nhan_vien.py` (khách cũ). Hai tab: Bán tự động. Danh sách đen: Thủ công | P1 |
| 5 | Mở lưới vận đơn | `/bang-tinh/van_don/` | Chỉ thấy dòng của mình. **Không** có nút Tôi/Toàn bộ (`only_own_rows`, AC-33.6), không có nút Xoá dòng (ADR-049) | Dán tiền `12.500`, `1.234,567`, `1e3` theo luật `parse_money` (AC-9.7). Cột Trùng đang đếm cả dòng ngoài phạm vi (`grid_service.duplicate_phones` không qua `in_scope`): ghi thành lỗi | Hết phiên khi đang có nháp: báo rõ, giữ nháp, không hiện "Đã lưu" (TL-86, TL-02). Hai tab cùng sửa một ô thì tab sau nhận 409 kèm hộp đối chiếu (AC-21.3) | `tests/e2e/test_admin_xoa_dong.py::test_staff_khong_co_nut_xoa_dong`. Hết phiên kèm nháp: chưa có. Mức: Tự động | P0 |
| 6 | Xem đơn gốc, thử Bỏ đơn | `/van-don/don-goc/<code>/`, POST `…/bo/` | Xem được. Bỏ đơn bị từ chối với lời "Chỉ Quản trị mới bỏ được đơn." (AC-6.13) | — | Khi bị từ chối, `don_bo` chuyển về `thu_muc`, mà người không có bảng vận đơn trong phạm vi sẽ gặp 404 | Bài HTTP: Tự động | P2 |
| 7 | Nộp báo cáo ngày | `/bao-cao/` (ERP) | Lưu được. Thị trường quyết định loại tiền. Mỗi lần nộp là một bản riêng | Gõ `abc` vào ô số thì báo lỗi tại ô. Ô số nguyên gõ `1,5` không được thành 15 | Bấm Nộp 2 lần, mạng chập, Back rồi nộp lại: chỉ 1 bản (AC-4.12). Nộp vắt qua nửa đêm: thông báo phải ghi đúng ngày đã lưu (BR-7). Gửi lại mã của báo cáo đã bỏ: không được 500 (nghi `DailyReport.DoesNotExist`) | `reports/tests/test_o_nhap_so_e2e.py` (dùng form MKT). Nộp 2 lần: Bán tự động | P0 |
| 8 | Lịch sử, bỏ báo cáo của mình | `/bao-cao/lich-su/`, POST `/bao-cao/<pk>/bo/` | Khung đọc nạp bằng HTMX. Bỏ được bản của mình (ADR-041). `/bao-cao/<pk>/sua/` trả 404 với Staff | Mở pk của người khác: 404, thân trang không lộ số | — | Có bài HTTP. Khung đọc: Bán tự động | P1 |
| 9 | Nội bộ: Bảng tin, Quản lý task, Tài liệu, Đánh giá nhân sự, Tài nguyên | `/bang-tin/`, `/cong-viec/`, `/bieu-mau/?tab=documents`, `/van-hoa/`, `/tai-nguyen/` | Đăng bài, Thích, bình luận. Bấm **Xong** trên việc thì dòng đổi tại chỗ. Tài liệu chỉ thấy mục chung và mục Sale. Đánh giá nhân sự không có ô ghi nhận | Ô Hạn gõ `13102026` thành 13/10/2026; gõ `31/02/2026` thì báo lỗi, không mất tiêu đề (AC-32.1) | Hai tab cùng Thích: chỉ 1 Like. Tab cũ bấm "Đang làm" trên việc đã Xong không được âm thầm mở lại việc (P1). Mất mạng khi bấm Thích thì báo bằng loi-mang. Hết phiên khi bấm Xong thì về `/dang-nhap/?next=…` | `test_o_ngay_tu_dinh_dang.py`. Còn lại chưa có e2e. Mức: Tự động | P1 |
| 10 | Đổi mật khẩu, đăng xuất | `/doi-mat-khau/`, POST `/dang-xuat/` | Phiên đang dùng được giữ, phiên ở máy khác bị huỷ (ADR-030) | Mật khẩu toàn số, giống tên đăng nhập, hai ô lệch nhau: bị từ chối, hash không đổi | Đăng xuất rồi bấm Lùi: không hiện trang cũ (no-store, NFR-4) | Bài HTTP: Tự động | P1 |

### 4.2. Sale Leader / Manager (`sale.leader`, `sale.manager`; bài máy dùng `leader_sale_1`, `manager_sale`)

| # | Bước | Màn hình / URL | Kết quả mong đợi | Dữ liệu bẩn / thao tác sai | Sự cố | Tự động hoá | Ưu tiên |
|---|---|---|---|---|---|---|---|
| 1 | Danh sách nhân sự, đặt lại mật khẩu cho Staff | `/nhan-su/`, POST `/nhan-su/<pk>/dat-lai-mat-khau/` | Leader thấy team mình, Manager thấy cả bộ phận (ADR-044). Sau khi gửi, mật khẩu không còn hiện rõ | Mật khẩu NFD: Staff phải gõ đúng từng byte (AC-9.6) | Tab 1 đang gõ mật khẩu, tab 2 `quantri` hạ Leader xuống Staff. Tab 1 bấm thì về đăng nhập kèm "Quyền của bạn vừa thay đổi", mật khẩu Staff không đổi | `tests/e2e/test_dat_lai_mat_khau.py`, `test_phan_trang_khong_tai_lai.py`. Hai tab: Bán tự động | P1 |
| 2 | Lưới vận đơn: Tôi / Toàn bộ | `/bang-tinh/van_don/?cua_toi=1` | Nút hiện. Leader thấy dòng của `staff_sale_1b`, không thấy dòng của `staff_sale_2`. "Toàn bộ" của Manager rộng hơn "Tôi" (AC-33.1) | — | Đang có nháp thì bấm Toàn bộ không đổi trang. Tải lại vẫn nhớ lựa chọn theo khoá `kn-master:<user>:<bảng>` | Chưa có e2e. Mức: Tự động. Bảng mong đợi **cần chốt** | P0 |
| 3 | Thêm sản phẩm mới khi đang lên đơn | POST `/van-don/len-don/san-pham-moi/` | Mọi ô chọn có ngay sản phẩm mới, lựa chọn đã chọn không mất. Cột `sl_*` ẩn được tạo (TL-72) | `kem TEST` khi đã có "Kem test" thì báo "đã có trong danh mục" | Hết phiên thì báo "Phiên đăng nhập đã hết." | Chưa có e2e. Mức: Tự động | P2 |
| 4 | Sửa báo cáo của Staff | `/bao-cao/<pk>/sua/` | Lưu được, có `ReportRevision` (chỉ ghi thêm) | Đổi Thị trường từ Canada sang Hoa Kỳ: loại tiền xử lý thế nào **cần chốt** (ADR-046, P0) | Mở trang sửa, trong lúc đó Staff bỏ báo cáo, rồi bấm Lưu: 404, không có bản sửa. Hai người cùng sửa: CAS trả `ReportConflict` | Bài HTTP: Tự động | P0 |
| 5 | Manager: Đã bỏ và Khôi phục | `/bao-cao/da-bo/`, POST `/bao-cao/<pk>/khoi-phuc/` | Khôi phục xong thì số trên Báo cáo tổng hợp về đúng như cũ. Leader nhận 403 kèm nhật ký | — | — | Tự động | P1 |
| 6 | Báo cáo tổng hợp, Gộp/Không gộp, Xuất, Ngưỡng màu | `/bao-cao/tong-hop/?nguon=bao_cao_sale`, `/xuat/`, POST `/bao-cao/tong-hop/nguong/` | Tổng cộng tách theo loại tiền. Excel khớp màn hình. Ngưỡng lưu được | Mốc sai thứ tự quay về `?nguong=1` (chỉ một lần). Mốc `-1` báo "không âm" | Máy chậm, bấm Gộp/Không gộp liên tục rồi Back: bảng khớp URL. Hết phiên khi bấm Gộp thì tải lại cả trang về đăng nhập | `reports/tests/test_bo_cuc_bao_cao_e2e.py`. Máy chậm: Bán tự động | P1 |
| 7 | Manager: Bảng dữ liệu ERP chỉ đọc | `/bang/`, `/bang/van_don/`, `/bang/<code>/xuat/` | Không sửa được ô. Bảng vận đơn có nút sang CRM (AC-40.7). Leader nhận 403 ở ERP | — | — | `test_sap_xep_khong_giat.py::test_bang_du_lieu_sap_xep_khong_tai_lai_trang`, `test_dien_thoai.py` (bang-du-lieu) | P1 |
| 8 | CRM: Nhập tệp và Cấp quyền | `/nhap-tep/`, `/cap-quyen/` (8021) | Chỉ làm được với bảng vận đơn (`_chi_bang_van_don`, ADR-040) | Cấp riêng quyền "Sửa" mà không "Xem": người nhận không thấy bảng (lệch `in_scope`, P1) | — | Bài HTTP: Tự động | P1 |
| 9 | Leader thử tạo bảng ở CRM | `/bang/moi/` (8021) | Hiện tạo xong thì sang `/bang/<code>/cot/` và gặp 404. Đây là ngõ cụt, cần ẩn hoặc báo trước | — | — | Thủ công (đã có bài `crm/tests/test_nhap_tao_cap_quyen_crm.py` khoá hiện trạng) | P2 |
| 10 | Thống kê CRM rồi "Mở dữ liệu" | `/thong-ke/?nguon=bao_cao_sale` | Đường dẫn sang ERP `/bao-cao/tong-hop/?nguon=…` (AC-40.9) | — | — | `crm/tests/test_statistics_labels_browser.py` (chạy khi có env) | P2 |
| 11 | Nội bộ: ghi nhận, ghim bài, giao việc | `/van-hoa/ghi-nhan/`, POST `/bang-tin/<pk>/ghim/`, `/cong-viec/moi/` | Leader chỉ ghi nhận được team mình. Chỉ Manager ghim bài. Ô Người làm chỉ có người trong phạm vi | Tiêu đề việc có chữ "mật khẩu" làm cả dòng nhật ký bị lược bỏ (AC-14.5) | Hai quản lý cùng sửa một việc hoặc tài nguyên: người sau đè người trước mà không biết (mất cập nhật, P1) | Bài HTTP. Đồng thời: Bán tự động | P1 |

### 4.3. MKT Staff (`mkt.staff`; bài máy dùng `staff_mkt`)

| # | Bước | Màn hình / URL | Kết quả mong đợi | Dữ liệu bẩn / thao tác sai | Sự cố | Tự động hoá | Ưu tiên |
|---|---|---|---|---|---|---|---|
| 1 | Nộp báo cáo ngày MKT | `/bao-cao/?bieu_mau=bc_mkt_ngay` | Ô Marketer chỉ đọc, mang tên mình. Ô số tự chèn dấu chấm. Loại tiền cố định VND (`REPORT_CURRENCY={'mkt':'VND'}`). Thẻ xem trước chỉ số cập nhật khi gõ | Gửi kèm `marketer` giả trong POST: dòng vẫn ghi người gửi (AC-8.2). Ô số gõ `abc` | Bấm Nộp lần 1 bị treo 3 giây rồi đứt, bấm lại, Back rồi nộp lần nữa: chỉ 1 bản (AC-4.12) | `reports/tests/test_o_nhap_so_e2e.py` (3 bài). Mạng chập: Bán tự động | P0 |
| 2 | Nộp thêm lần 2 trong ngày | `/bao-cao/` | Có thêm một bản riêng, hiện "Lần 2" trên tổng hợp (reports/0004 bỏ ràng buộc một bản mỗi ngày) | — | — | Tự động | P1 |
| 3 | Đi đường vòng qua biểu mẫu | `/bieu-mau/<bc_mkt_ngay>/dien/` | Mong muốn: chuyển sang `/bao-cao/` hoặc cũng chống gửi trùng. Hiện tại gửi 2 lần ra 2 dòng và không có `DailyReport` (P1) | — | Gửi lặp | Bài HTTP đỏ | P1 |
| 4 | Lịch sử, bỏ báo cáo của mình | `/bao-cao/lich-su/` | Chuyển trang tại chỗ, giữ bộ lọc (AC-10.19) | — | — | Bán tự động | P2 |
| 5 | Mở KN CRM | `/thu-muc/`, `/thong-ke/` | Theo `scope_condition`, nhánh MKT rơi vào `original`: chỉ thấy dòng vận đơn do mình tạo. Không có dòng nào thì `/thu-muc/` trả 404. Được phân công Marketing có mở thêm dòng không: **chưa xác minh** (mã không thêm `marketing` vào nhánh này) | — | — | Thủ công cho tới khi chốt | P1 |
| 6 | Nội bộ | `/bieu-mau/?tab=documents`, `/tai-nguyen/`, `/van-hoa/` | Thấy mục MKT và mục chung, không thấy mục Sale. Tài nguyên chỉ xem. Không có ô ghi nhận | — | Mất mạng khi bấm Thích thì có lời báo tiếng Việt | Chưa có e2e. Mức: Tự động | P2 |
| 7 | Gõ ô ngày ở các bộ lọc | Lịch sử, Tổng quan | Gõ `03092026` thành 03/09/2026 | Gõ ngày sai thì báo tại ô | — | `test_o_ngay_tu_dinh_dang.py` | P2 |

### 4.4. MKT Manager (`mkt.manager`; bài máy dùng `manager_mkt`)

| # | Bước | Màn hình / URL | Kết quả mong đợi | Dữ liệu bẩn / thao tác sai | Sự cố | Tự động hoá | Ưu tiên |
|---|---|---|---|---|---|---|---|
| 1 | "＋ Thêm mới…" sản phẩm trên form nộp | POST `/bang/<code>/cot/<ma_cot>/lua-chon/` | Chọn được ngay, không tải lại trang. Có dòng nhật ký. Leader có được làm như vậy không phải khớp giữa giao diện và máy chủ (AC-8.8) | Nhãn trùng, nhãn NFD | — | Bài HTTP. Mức: Tự động | P1 |
| 2 | Bảng dữ liệu báo cáo, sửa màu cột và ngưỡng | `/bang/bao_cao_mkt/?dang=tho`, `/bang/<code>/cot/?cot=<pk>` | Cột tô màu, ô vượt ngưỡng tô đỏ (AC-8.9) | Đổi kiểu cột Chữ sang Số khi có giá trị `abc`: hiện ra **500** (AC-8.11, P0). Thêm cột trùng tên kỹ thuật: có thể 500 (chưa chạy) | — | Bài HTTP đỏ. Mức: Tự động | P0 |
| 3 | Nhập tệp vào bảng báo cáo MKT | `/bang/bao_cao_mkt/mau-nhap.xlsx`, `/nhap/`, `/nhap/<pk>/xac-nhan/` | Hiện tại mọi dòng nhận Ngày = hôm nay và Người bán = người nhập (`report_input_values`). Phải chốt: giữ theo tệp, hoặc chặn hẳn (P1) | Tệp `.exe` đổi đuôi thì bị từ chối (AC-7.9). Tệp 10,5 MB báo tiếng Việt. Tệp 12 MB qua nginx: hiện là trang 413 tiếng Anh | Hai tab cùng bấm Xác nhận: không nhân đôi dòng. Worker bị diệt giữa chừng: tác vụ không treo mãi (TL-23) | `tests/e2e/test_luong_nhap_xuat.py` (bảng Sale). Phần qua nginx: Thủ công | P1 |
| 4 | Báo cáo tổng hợp MKT, Xuất Excel | `/bao-cao/tong-hop/?nguon=bao_cao_mkt` | Số (TT) đúng. Bỏ một lần nộp thì TỔNG CỘNG giảm đúng, khôi phục thì về như cũ (AC-4.9, AC-4.10). Excel có tiền là số thật (AC-5.6). Không thấy nút ✎ (chỉ Admin, ADR-050) | — | — | `reports/tests/test_bo_cuc_bao_cao_e2e.py` | P1 |
| 5 | Ngưỡng màu từ Bảng dữ liệu dạng báo cáo | POST `/bao-cao/tong-hop/nguong/` kèm `next=/bang/bao_cao_mkt/…` | 302 về đúng `next` (AC-42.9, AC-42.13) | Mốc sai thứ tự | — | Tự động | P2 |
| 6 | Sửa báo cáo khi bảng nguồn đã ngừng dùng | `/bao-cao/<pk>/sua/` | Nhận 403, không có bản sửa, thông báo dễ hiểu (cần chốt câu chữ) | — | — | Tự động | P2 |
| 7 | Tạo biểu mẫu, trường, cấp quyền điền | `/bieu-mau/truong-moi/`, `/bieu-mau/moi/`, `/bieu-mau/<code>/sua/`, `/cap-quyen/` | Làm trọn vòng, người được cấp FILL điền được (AC-8.1) | Giá trị mặc định sai kiểu thì báo lỗi rõ, không 500 | — | Tự động | P1 |
| 8 | Tài liệu, tài nguyên, giao việc, ghi nhận | `/tai-lieu/tai-len/`, `/tai-nguyen/moi/`, `/cong-viec/moi/`, `/van-hoa/ghi-nhan/` | Tải đủ 6 loại tệp, tên tệp NFD tải về đúng. Ghi chú có "mật khẩu: 123" bị từ chối (FR-13.4). Không giao việc được cho `sale.staff` | Thư mục lưu không ghi được (PermissionError) đang ra 500 | Sửa tài nguyên ở hai tab gây mất cập nhật (P1) | Bài HTTP. Kiểm qua nginx: Thủ công | P1 |

### 4.5. Vận đơn Staff (`vd.staff`; bài máy dùng `staff_vd`)

| # | Bước | Màn hình / URL | Kết quả mong đợi | Dữ liệu bẩn / thao tác sai | Sự cố | Tự động hoá | Ưu tiên |
|---|---|---|---|---|---|---|---|
| 1 | Vào CRM, mở bảng | 8021 `/`, `/thu-muc/`, `/bang-tinh/van_don/` | Cây thư mục phẳng Bộ phận ▸ thư mục ▸ bảng (`tree_service`). Thấy toàn bộ dòng (ADR-033) | — | Máy chậm: ô `…` phải được thay bằng dữ liệu | `tests/e2e/test_hanh_trinh_nhan_vien.py` | P0 |
| 2 | Sửa ô Trạng thái vận chuyển và Ghi chú | Lưới (`luu-json/`) | Tự lưu sau 500 ms, hiện "✓ Đã lưu". Ghi chú hai dòng làm dòng giãn cao ngay (AC-11.44) | Bấm Enter trên ô tiền `0.125` mà không sửa: giá trị không đổi, không sinh nhật ký (TL-03, P0). Dán 500 ô TSV. Dán ô NFD | Mất mạng: báo tiếng Việt, có mạng lại tự lưu. Phản hồi bị mất: gửi lại cùng UUID, server trả `replayed=true`, lịch sử chỉ 1 mục (P0). Hết phiên hoặc `session_epoch` đổi khi đang có nháp: không được hiện "Quyền xem đã thay đổi" hay "Đã lưu" (P0) | `test_mat_mang_e2e.py`, `test_ghi_chu_tu_gian_dong.py`, `test_pha_luoi_ghi_chu.py`. UUID, hết phiên, epoch: chưa có. Mức: Tự động | P0 |
| 3 | Hai tab hoặc hai người cùng sửa một ô | Lưới | Người lưu sau nhận 409 kèm hộp Đối chiếu, "Gửi lại giá trị của tôi" hoạt động (AC-21.3, AC-21.10) | — | Manager chèn hoặc ẩn cột ở tab khác: lần lưu kế nhận 400 `schema_changed`, nút "Tải lại cấu trúc, giữ nháp" giữ chữ đã gõ (AC-27.6) | Chưa có fixture hai trang (đề xuất `hai_trang`). Mức: Bán tự động | P1 |
| 4 | Lọc cột, panel Bộ lọc, Trùng, ⌕ Mã đơn, sắp xếp | `/loc/<ma_cot>/`, `/bo-loc/?panel=1`, `?trung=1` | Đổi lọc không tải lại trang. Chip lọc nằm trên thanh công cụ. Sắp xếp không giật | Gõ chữ NFD vào ô tìm | Hỏi lại mỗi 8 giây, tab ẩn thì ngừng hỏi (AC-10.22) | `test_luoi_hoi_nhe.py`, `test_nhan_loc_tren_thanh_cong_cu.py`, `test_sap_xep_khong_giat.py` | P1 |
| 5 | Tôi / Toàn bộ | `#mg-pham-vi` | Bấm Tôi thì URL có `cua_toi=1`. Tải lại vẫn nhớ. Đăng nhập người khác trên cùng máy thì không áp theo (AC-33.3) | — | Đang có nháp thì không đổi trang | Chưa có e2e. Assert trong `scripts/kiem-thu-solarpunk.cjs` dòng 38 đã lỗi thời. Mức: Tự động | P1 |
| 6 | Hộp Chi tiết sản phẩm, Bỏ chi tiết | `/van-don/chi-tiet/<pk>/`, `/bang-tinh/van_don/bo-chi-tiet/` | Delete trên ô Sản phẩm thì hỏi lại 3 lựa chọn. Bỏ được dòng cuối | — | Người khác vừa sửa: 400 "vừa được người khác sửa", form giữ chữ đã gõ. Hết phiên khi Lưu: hiện cả trang chuyển sang đăng nhập (CRM không có `htmx:beforeSwap`, TL-18). Bấm Bỏ chi tiết 2 lần thì lần sau nhận 409, phải báo rõ | `test_xoa_chi_tiet_san_pham_e2e.py` (8 bài). Hết phiên: chưa có | P1 |
| 7 | Lịch sử ô bằng chuột phải | Lưới (`lich-su/`) | Khung lịch sử hiện cạnh ô. Ô vừa bị sửa trong 24 giờ có dấu góc | Đang gõ dở thì hiện menu thường của trình duyệt | — | `test_lich_su_o_tren_luoi.py` | P2 |
| 8 | Ẩn cột riêng máy, ghim cột | Hộp Cột, cuộn ngang | Tải lại vẫn ẩn. 4 cột ghim lệch không quá 1 px | — | Viewport 390 px hoặc zoom 125% thì bỏ ghim, không chồng ô | `crm/tests/test_luoi_dong_trong_va_ghim_e2e.py`, `test_pha_luoi_ghi_chu.py::test_dien_thoai_390` | P2 |
| 9 | Nhập `vandon-mau.xlsx` | ⋯ → Nhập tệp → `/tac-vu/<pk>/` | Báo nhập xong, số dòng lỗi đúng | Mã đơn trùng dòng đang sống. Tiền `1.234,5`. Ô có Alt+Enter | Nhập 10.000 dòng trong khi người khác sửa lưới: không 500. Worker bị diệt: tác vụ chuyển STALE hoặc FAILED (TL-23) | Đo tải: Bán tự động. Diệt worker: Thủ công | P1 |
| 10 | Xuất Excel lưới | `/bang-tinh/van_don/xuat/` | Chỉ các dòng đang lọc. Tệp lớn thì chạy nền qua `/tac-vu/<pk>/tai/` | — | Tệp quá 24 giờ đã bị dọn: báo "Hãy xuất lại", không 500 | Tự động | P2 |
| 11 | Chứng từ thanh toán (khi bật `PAYMENT_DOCUMENTS_ENABLED`) | `/chung-tu-thanh-toan/tao/` | VĐ tạo được, không sửa hay xoá được | Mã tham chiếu trùng (không phân biệt hoa thường) trên cùng dòng | Hết phiên khi Lưu: payments.js phải báo tiếng Việt, không hiện "Unexpected token" | `crm/tests/test_payment_browser_server.py` (chạy khi có env). Mức: Tự động | P2 |
| 12 | Gõ tiếng Việt bằng bộ gõ thật trên lưới (loại: kiểm tay tương thích trình duyệt và hệ điều hành) | Lưới, ô Tên khách và ô tìm kiếm | Gõ "Nguyễn Ngọc Ánh" bằng **Unikey** và **EVKey** (Windows, Chrome/Edge) và **Telex của macOS** (Safari), bấm Enter, tải lại: ô lưu đúng chữ đã ghép xong, không rớt hay lặp chữ. Từ máy khác hệ điều hành gõ "Ngọc Ánh" vào ô tìm kiếm thì ra đúng dòng (AC-9.6) | Bấm Enter, Tab hoặc Ctrl+S **giữa lúc đang ghép chữ**: lưới không được chốt ô hay chuyển ô. `master-grid.js` bỏ qua phím khi `isComposing` hoặc `keyCode===229` (dòng 995, 1006, 1283) và đặt `state.composing` ở `compositionstart` (dòng 984). Gõ nhanh kiểu Unikey (xoá lùi rồi thay chữ có dấu) | — | Hồi quy giả lập đã có: `crm/tests/test_chu_viet_mot_dang.py` (NFD/NFC, 4 bài), `scripts/kiem-thu-shared-grid.cjs` dòng 50 và `scripts/kiem-thu-master-ui.cjs` dòng 65 (giả lập sự kiện, chạy tay). Bộ gõ thật: **Chưa kiểm** theo `docs/kiem-chung-san-loi-go-tieng-viet-20261006.md` mục "Chưa kiểm" và `docs/kiem-chung-master-nine.md`. Mức: Thủ công | P0 |
| 13 | Rời trang khi còn nháp | Lưới: đóng tab, F5, bấm liên kết thanh bên, gõ URL khác | Trình duyệt hiện hộp hỏi "Rời trang?" khi còn ô đang gõ dở khác giá trị cũ, còn lượt đang gửi, còn lượt chờ thử lại (`state.retry`, `state.rowRetry`) hoặc lưới đang bận (listener `beforeunload` ở `master-grid.js` dòng 1261). Không có nháp thì rời trang không bị hỏi. Đòi hỏi của docs/07 mục "Nghiệm thu chín hạng mục" | Mở ô rồi gõ lại đúng giá trị cũ: không hỏi | Mất mạng, sửa 1 ô (lượt chờ thử lại), bấm F5: phải bị hỏi. Chọn "Ở lại" thì nháp còn nguyên | Chưa có bài nào kiểm `beforeunload`. Playwright bắt được qua sự kiện `dialog` loại `beforeunload` (đóng trang với `run_before_unload=True`). Mức: Tự động | P1 |

### 4.6. Vận đơn Leader (`vd.leader`; bài máy: `leader_vd` từ #118, xem ghi chú dưới bảng)

Ghi chú tài khoản bài máy: `app/crm/tests/conftest.py` chỉ có fixture `dich_vu_kn_crm` (autouse, đặt URLconf 8021). Fixture `nguoi_dung` trong `app/conftest.py` không có VĐ Leader. Người dùng VĐ cấp Leader/Manager được dựng riêng trong từng tệp:

| Tên biến | Tệp dựng riêng |
|---|---|
| `leader_vd` | `core/tests/test_ma_tran_quyen_hai_dich_vu.py`, `crm/tests/test_chi_admin_xoa_dong.py`, `forms_builder/tests/test_pham_vi_bang_nhanh.py` |
| `manager_vd` | `core/tests/test_ma_tran_quyen_hai_dich_vu.py`, `crm/tests/test_chi_admin_xoa_dong.py`, `crm/tests/test_lien_ket_khong_cut.py`, `tests/test_hieu_nang.py`, `tests/e2e/test_dien_thoai.py` |

Khi viết bài mới cho vai này, nên gom thành một fixture dùng chung (ví dụ trong `app/conftest.py`) để khỏi dựng lại lần thứ bảy.

| # | Bước | Màn hình / URL | Kết quả mong đợi | Dữ liệu bẩn / thao tác sai | Sự cố | Tự động hoá | Ưu tiên |
|---|---|---|---|---|---|---|---|
| 1 | Phân công ngay trong ô Phụ trách VĐ / CSKH / MKT | Lưới, POST `/van-don/phan-cong/` | Chọn người ngay trong ô. Danh sách không có người bị khoá hoặc đã xoá (`candidates`) | Gửi `versions` cũ thì bị CAS từ chối | Hết phiên khi chọn: ô không được đóng như đã lưu (P1). Phân công xen giữa lúc người khác mở hộp Chi tiết: người đó bị chặn, lời báo dễ hiểu (AC-20.3) | `tests/e2e/test_phan_cong_o_chon.py`. Hết phiên: chưa có | P1 |
| 2 | Ẩn cột với cả công ty, rồi hiện lại | POST `/bang-tinh/van_don/an-cot/` | `vd.staff` không thấy cột đó. Hiện lại thì cột về đúng chỗ (AC-39.1, AC-39.6) | — | Staff đang có nháp nhận `schema_changed` | Chưa có e2e. Mức: Tự động | P1 |
| 3 | Chèn hoặc bỏ cột | `/them-cot/`, `/xoa-cot/` | Đúng quyền Leader thuộc bộ phận sở hữu bảng. Gặp `removable_reason` thì báo lý do | Bỏ cột đang được dùng: BusinessError cần được báo rõ, không 500 | — | Bài HTTP | P2 |
| 4 | Thư mục | POST `/bang-tinh/thu-muc/moi/`, `…/sua/`, `…/xoa/` | Tạo, đổi tên, xoá được. Staff và CEO bị từ chối | — | — | Tự động | P2 |
| 5 | Nộp báo cáo Vận đơn ngày | `/bao-cao/?bieu_mau=bc_van_don_ngay` | Lưu được (`configure_delivery_daily_report`) | — | — | Thủ công. Bài riêng **chưa xác minh** | P2 |
| 6 | Đặt lại mật khẩu cho `vd.staff` | `/nhan-su/` | Leader chỉ quản lý Staff trong team mình, mà `vd.staff` mẫu có team = None, nên Leader **không** thấy. Cần gán team trước khi kiểm | — | — | Thủ công | P2 |
| 7 | Thử xoá bảng | `/bang-tinh/van_don/xoa-bang/` | Bị từ chối (chỉ Manager của bộ phận sở hữu hoặc Admin, ADR-027) | — | — | Tự động | P2 |

### 4.7. CSKH (`cskh.staff`; bài máy: `cskh`)

| # | Bước | Màn hình / URL | Kết quả mong đợi | Dữ liệu bẩn / thao tác sai | Sự cố | Tự động hoá | Ưu tiên |
|---|---|---|---|---|---|---|---|
| 1 | Mở lưới khi đã được giao chăm sóc | `/bang-tinh/van_don/` | Chỉ thấy dòng có `care` = mình (`_cham_soc`). Không có nút Tôi/Toàn bộ (AC-33.6). Gõ vào ô thì bị chặn, `luu-json/` trả 403 | Gọi thẳng POST `luu-json/` vẫn nhận 403 | — | Chưa có e2e. Mức: Tự động | P0 |
| 2 | Chưa được giao dòng nào | `/thu-muc/` | Trả 404 (không có bảng vận đơn trong phạm vi). Cần chốt câu hướng dẫn | — | — | Tự động | P2 |
| 3 | Hộp Chi tiết | `/van-don/chi-tiet/<pk>/` | Fieldset bị khoá, POST trả 403 | — | — | Tự động | P1 |
| 4 | Bị gỡ phân công khi đang mở lưới | Hỏi lại `moi-nhat/`, `quyen-dong/` | Dòng biến mất hoặc bị khoá, có lời báo | — | Hai tab | Bán tự động | P1 |
| 5 | Cột Trùng và Xuất Excel | Lưới | Excel chỉ có dòng được giao. Cột Trùng **không** được đếm dòng ngoài phạm vi (hiện đang đếm cả, nên lộ số) | — | — | Bài HTTP đỏ | P1 |
| 6 | Chứng từ thanh toán | `/chung-tu-thanh-toan/` | Chỉ xem chứng từ của dòng được giao | — | — | Tự động | P2 |
| 7 | Báo cáo ngày, Nội bộ | `/bao-cao/`, nhóm Nội bộ | Có biểu mẫu báo cáo cho CSKH hay không: **chưa xác minh** | — | — | Thủ công | P2 |

### 4.8. Kế toán (tài khoản thuộc bộ phận `ke-toan`; bài máy dùng `staff_kt`)

| # | Bước | Màn hình / URL | Kết quả mong đợi | Dữ liệu bẩn / thao tác sai | Sự cố | Tự động hoá | Ưu tiên |
|---|---|---|---|---|---|---|---|
| 1 | Lưới vận đơn | `/bang-tinh/van_don/` | Thấy mọi dòng (`is_accountant`). Có nút Tôi/Toàn bộ. Hộp Chi tiết chỉ xem. Quyền sửa ô thường: **chưa xác minh** | — | — | Chưa có e2e | P1 |
| 2 | Kho chứng từ: tạo, sửa, xoá mềm, khôi phục | `/chung-tu-thanh-toan/…` | `payment_service.can_manage` cho phép. Có nhật ký và `GridPendingChange` | Mã tham chiếu trùng. Tệp ảnh sai loại | Hai tab cùng sửa một chứng từ: **chưa xác minh** có CAS hay không | `crm/tests/test_payment_documents.py`, `test_payment_browser_server.py` | P1 |
| 3 | Lịch sử báo cáo và sửa báo cáo của bộ phận khác | `/bao-cao/lich-su/`, `/bao-cao/<pk>/sua/` | Thấy mọi báo cáo. Sửa được, có Nhật ký (ADR-038). Bỏ báo cáo và Khôi phục đều bị từ chối | — | CAS 409 | Tự động | P1 |
| 4 | Báo cáo tổng hợp và Xuất Excel nguồn Sale | `/bao-cao/tong-hop/?nguon=bao_cao_sale`, `/xuat/` | Ghi lại thực tế (200 hay 403). Nếu 200 thì tổng phải bằng của Admin và có `AuditLog EXPORT` | — | — | Tự động | P1 |
| 5 | Tổng quan | `/` | Thẻ Sale và MKT bằng số của Admin, không khối nào báo lỗi (AC-44.6) | — | — | Tự động | P1 |
| 6 | Bảng dữ liệu ERP | `/bang/` | Kế toán Staff nhận 403 (`assert_rank MANAGER`) | — | — | Tự động | P2 |

### 4.9. Admin (`quantri`; bài máy dùng `admin`)

| # | Bước | Màn hình / URL | Kết quả mong đợi | Dữ liệu bẩn / thao tác sai | Sự cố | Tự động hoá | Ưu tiên |
|---|---|---|---|---|---|---|---|
| 1 | Tạo bộ phận và team | `/bo-phan/` | Team mới có ngay trong ô chọn (AC-2.4) | Trùng tên với bản đã xoá mềm: báo lỗi tiếng Việt, không 500 (P1) | — | Bài HTTP | P1 |
| 2 | Tạo tài khoản | `/nhan-su/moi/`, `/nhan-su/goi-y-ma/` | Ra mật khẩu tạm. Người mới bị buộc đổi mật khẩu khi đăng nhập | Hai Admin tạo hai người trùng họ tên cùng lúc: không IntegrityError (AC-37.2). Tên đăng nhập trùng mã nhân sự của người khác | — | `org/tests/test_account_browser_server.py` (chạy khi có env). Đồng thời: Tự động | P1 |
| 3 | Sửa hồ sơ, đổi cấp bậc hoặc bộ phận | `/nhan-su/<pk>/sua/` | Phiên của người bị đổi bị huỷ, lần sau thấy `?doi_quyen=1` | Admin cuối cùng tự hạ cấp: phải bị chặn (**cần chốt**, P0). Admin tự đổi bộ phận của mình thì bị đẩy ra ngay (P2) | — | Tự động | P0 |
| 4 | Khoá, mở khoá, xoá mềm | `/nhan-su/<pk>/doi-trang-thai/`, `/nhan-su/<pk>/xoa/` | Phiên của người đó mất. Không tự khoá được mình, không xoá được Admin cuối | Gỡ khoá tạm mà không khoá hẳn tài khoản (P2, cần chốt) | Người bị khoá đang mở CRM và bấm Lưu trong khung HTMX: form đăng nhập không được nhét vào `#vd-detail-body` (TL-18) | Bán tự động | P1 |
| 5 | Nhật ký, Ma trận quyền, Tác vụ nền | `/nhat-ky/`, `/ma-tran-quyen/`, `/tac-vu/` | Đủ 50 ô trong ma trận. Tác vụ RUNNING bị treo phải được phát hiện (P1) | — | — | Tự động | P1 |
| 6 | Xoá dòng trên lưới rồi hoàn tác | ⋯ → Xoá dòng (`delete_rows`) | Hoàn tác thì dòng về đúng chỗ (AC-21.18, AC-21.19) | — | Xoá dòng mà `vd.staff` đang có nháp: nháp dòng đó bị gỡ kèm lời báo, nháp các dòng khác vẫn lưu | `tests/e2e/test_admin_xoa_dong.py`. Xung đột nháp: Bán tự động | P1 |
| 7 | Bỏ đơn | POST `/van-don/don-goc/<code>/bo/` | Dòng vận đơn bị xoá mềm theo (ADR-049) | Sale gửi lại `ma_lan_nop` của đơn đã bỏ: báo rõ "đơn đã bị bỏ" | — | Tự động | P2 |
| 8 | Sửa ✎ ngay trên Báo cáo tổng hợp | `/bao-cao/<pk>/sua/?khung=1&lan=N` | Trả 204, bảng đổi tại chỗ | Ô số gõ `abc` thì 400 trong hộp. Thiếu version thì 409 | Hai tab: tab sau nhận 409, ô đổi tô vàng (AC-50.9). Lưu hỏng thì báo lỗi trong hộp | `reports/tests/test_admin_sua_tong_hop_e2e.py` (3 bài). Hai tab: Bán tự động | P1 |
| 9 | Nộp báo cáo thay team | `/bao-cao/` (có dropdown Team) | `DailyReport.department` khớp với form. Manager Sale thấy, sửa được (ADR-043) | — | — | Tự động | P1 |
| 10 | Tạo bảng hoặc trường ở ERP | `/bang/moi/`, `/bieu-mau/truong-moi/` | Không 500. Hiện tại `quantri` có department=None nên `full_clean` lỗi (P1) | — | — | Bài HTTP đỏ | P1 |
| 11 | Vòng đời bảng | `/bang-da-xoa/`, `…/xoa-bang/`, `…/khoi-phuc-bang/` | Xoá và khôi phục được. Bảng còn biểu mẫu thì lời báo phải chỉ ra lối thoát (AC-27.5) | — | — | Bán tự động | P2 |
| 12 | Trang quản trị Django | `/quan-tri/` | Admin vào được. Sai 6 lần ở `/quan-tri/login/`: ghi lại có nhật ký và có bị khoá hay không | — | — | Thủ công | P1 |
| 13 | Để yên quá 60 phút rồi bấm Thích | `/bang-tin/` | Trình duyệt chuyển hẳn về trang đăng nhập (AC-1.4) | — | Hết phiên | `core/tests/test_ra_soat.py` (HTTP). E2E: chưa có | P1 |

### 4.10. CEO (`giamdoc`; bài máy: `ceo`)

| # | Bước | Màn hình / URL | Kết quả mong đợi | Dữ liệu bẩn / thao tác sai | Sự cố | Tự động hoá | Ưu tiên |
|---|---|---|---|---|---|---|---|
| 1 | Đăng nhập, nhìn thanh bên | `/` | Không có "Nộp báo cáo ngày" (`visible_navigation`). Lịch sử không có nút Nộp (`can_submit_reports`) | — | — | Tự động | P1 |
| 2 | Tổng quan | `/` | Ba thẻ có số toàn công ty. `sao_luu` là None (AC-44.6) | — | — | Tự động | P1 |
| 3 | Lưới CRM chỉ đọc | `/bang-tinh/van_don/` | Gõ vào ô bị chặn, `luu-json/` trả 403, không có nút Xoá dòng (AC-21.17). Xuất Excel được | — | — | Chưa có e2e. Mức: Tự động | P0 |
| 4 | Thử Lên đơn, tạo bảng, cấp quyền | `/van-don/len-don/`, `/bang/moi/`, `/cap-quyen/` | 403 (`assert_business_write`) | — | — | Tự động | P1 |
| 5 | Nhân sự, đặt lại mật khẩu | `/nhan-su/` | Thấy toàn công ty. Đặt lại được cho Manager, Leader, Staff, không được cho Admin (ADR-044) | — | — | Tự động | P1 |
| 6 | Báo cáo | `/bao-cao/<pk>/`, `/sua/`, `/bo/`, `/tong-hop/` | Xem được. Sửa trả 404, bỏ bị từ chối. Tổng hợp toàn công ty | — | — | Tự động | P1 |
| 7 | Nội bộ | `/bang-tin/`, `/cong-viec/`, `/van-hoa/`, `/tai-lieu/tai-len/`, `/tai-nguyen/moi/` | Đăng bài được. Ghim và ghi nhận trả 403. Việc chỉ giao cho mình. Tải tài liệu lên: GET mở được form nhưng POST trả 403 không ghi DENIED. Tài nguyên cũng vậy | CEO không có bộ phận tạo việc: hiện báo lỗi "phải thuộc một bộ phận" (P2). Lọc việc theo người không có ô chọn mà trả danh sách rỗng (P2) | — | Tự động | P2 |
| 8 | Bảng dữ liệu ERP | `/bang/` | Theo RANK_LEVEL CEO=35 thì vượt `assert_rank(MANAGER)`, nhưng **chưa xác minh** bằng bài kiểm | — | — | Tự động | P2 |
| 9 | Trang quản trị Django | `/quan-tri/` (Staging) | Bị chuyển sang trang đăng nhập quản trị, không thấy model nào | — | — | Thủ công | P1 |

### 4.11. Đối chiếu `docs/07-kich-ban-nghiem-thu.md` (bản ngày 03.09.2026)

**Bước đã lỗi thời**

| Mục docs/07 | Dòng đang ghi | Thực tế trong mã / quyết định | Việc cần làm |
|---|---|---|---|
| 3.1 | Thanh bên của `sale.staff` có "Lên đơn, Đơn hàng, Bảng dữ liệu" | `core/navigation.py`: ERP không có mục Lên đơn. `bang` cần Rank.MANAGER. `/len-don/` chỉ chuyển tiếp GET sang CRM (`orders/handoff.py`) | Viết lại theo 4.1 bước 1 và 3 |
| 3.1 | `sale.staff` mở Bảng dữ liệu → Bảng vận đơn | Staff nhận 403 ở ERP (`erp_table_view`) | Thay bằng bước xem trên lưới 8021 |
| 3.1 | Nhóm Nội bộ có "Bảng tin, Tài liệu, Công việc, Văn hoá, Tài nguyên" | Bảng tin nằm ở nhóm Tổng quan. Tài liệu nằm trong "Biểu mẫu & tài liệu". "Quản lý task". "Đánh giá nhân sự" nằm ở Tổ chức | Đổi tên và vị trí |
| 3.2 | Nộp lại cùng ngày thì ghi đè (AC-4.2) | Migration `reports/0004` bỏ ràng buộc một bản mỗi ngày. Mỗi lần nộp là một bản ("Lần N", AC-4.12). AC-4.2 nay nói về thời điểm nộp | Viết lại theo 4.3 bước 1 và 2 |
| 3.2 | `mkt.manager` mở Báo cáo Marketing trong CRM: cây Quý ▸ Tháng, thư mục, chèn và xoá cột bằng chuột phải, xoá hàng bằng chuột phải, kéo điền | CRM chỉ phục vụ bảng vận đơn (ADR-040, `catalog.chi_van_don`). Chuột phải mở Lịch sử ô (AC-21.13, `master-grid.js:1228`). Xoá dòng chỉ Admin làm, qua menu ⋯ (ADR-049). AC-11.20 và AC-11.21 đang nằm trong HOAN | Bỏ các bước đó, chuyển phần lưới sang 4.5 |
| 3.2 | Báo cáo tổng hợp "nhóm theo ngày rồi theo nhân viên" | Nguồn đã cấu hình dùng Gộp/Không gộp (`reports/screen.py`). Các tab nhóm chỉ còn ở bản cũ | Viết lại theo 4.4 bước 4 |
| 3.3 | Thanh bên ERP của `vd.staff` có Tác vụ nền, không có Báo cáo | Tác vụ nền cần Rank.ADMIN. Nhóm Báo cáo hiện với mọi người | Sửa lại |
| 3.3 | Cây Vận đơn ▸ Quý ▸ Tháng | Thư mục phẳng (`crm/services/tree_service.py`) | Sửa lại |
| 3.3 | `sale.leader` nhập tệp vào bảng Sale, + Tạo bảng. `sale.manager` cấp quyền bảng Sale | Chỉ làm được với bảng vận đơn (`_chi_bang_van_don`). Tạo bảng là ngõ cụt 404 | Thay bằng 4.2 bước 8 và 9 |
| 3.3 | Ở 8021 menu chuột phải có Dán, Chèn hàng, Xoá hàng | Chuột phải mở Lịch sử ô | Sửa lại |
| 3.3 | Gõ vào dòng trống cuối lưới | `master-grid.js` vẫn có `DRAFT_BATCH` khi `config.canCreate`. Bước này còn đúng hay không: **chưa xác minh** | Kiểm tay rồi chốt |
| 3.4 | Đường dẫn sai: "chưa làm 404 tiếng Việt (K9)" | Đã có `templates/404.html` | Đổi điều kiện đạt |

**Mục docs/07 còn hiệu lực nhưng các bảng 4.1–4.10 chưa phủ**

Mục 4 "Vận hành" nhìn từ phía **người vận hành** (chủ dự án chạy máy), không thuộc vai nghiệp vụ nào. Hai mục bổ sung ở cuối docs/07 là ca lưới của `vd.staff` và `vd.leader`.

| # | Mục docs/07 | Ca kiểm | Kết quả mong đợi | Căn cứ trong mã | Loại / Tự động hoá | Ưu tiên |
|---|---|---|---|---|---|---|
| V1 | 4 Vận hành | Chạy `scripts/backup.sh` | In "Đã sao lưu: knjsc-….dump", tệp có trong `storage/backups/` (AC-10.6) | `backup.sh` gọi `manage.py sao_luu` | Vận hành. Thủ công | P0 |
| V2 | 4 Vận hành | Chép tệp thành 35 bản (hoặc chạy thêm 30 lần) rồi chạy `backup.sh` lại | Thư mục còn đúng 30 bản mới nhất (AC-10.6) | `core/management/commands/sao_luu.py` ("giữ tối đa 30 bản gần nhất") | Vận hành. Phần xoay vòng đã có bài máy: `core/tests/test_sao_luu.py::test_chi_giu_30_ban_gan_nhat` và `::test_sao_luu_xong_thi_xoay_vong_luon` (docstring AC-10.6), mức Tự động. Chạy thật qua `backup.sh` trên máy vận hành: Thủ công | P1 |
| V3 | 4 Vận hành | Sửa một ô trên lưới, rồi `scripts/restore.sh --toi-chac-chan` với bản sao lưu trước khi sửa | Đăng nhập lại: ô về giá trị cũ, phần khác còn nguyên (AC-10.5) | `scripts/restore.sh` | Vận hành, khôi phục thảm hoạ. Thủ công | P0 |
| V4 | 4 Vận hành | Tắt Docker Desktop, mở lại, chờ 1 phút | `localhost:8020` và `8021` tự lên, không cần gõ lệnh (docs/05 B5) | `deploy/docker-compose.yml`: các dịch vụ đặt `restart: unless-stopped` | Vận hành, khởi động lại. Thủ công | P1 |
| V5 | 4 Vận hành | `manage.py seed_perf` rồi Locust 50 người trong 1 phút | Kịch bản in **ĐẠT**, p99 dưới 3 giây (AC-10.1) | `app/tests/perf/README.md`, `app/tests/perf/locustfile.py` | Hiệu năng. Bán tự động | P1 |
| V6 | 4 Vận hành | Trong lúc Locust chạy, mở lưới bằng tay | Vẫn dùng được, không chờ quá vài giây (NFR-2) | — | Hiệu năng cảm nhận. Thủ công | P1 |
| V7 | 4 Vận hành | Cài từ đầu trên máy sạch theo docs/05 B2 | Tới màn hình đăng nhập không cần hỏi ai (mục 17.1) | — | Cài đặt. Thủ công | P1 |
| V8 | 4 Vận hành | Chạy `scripts/kiem-tai-kn-crm.bat` (Mac/Linux: `.sh`), chờ khoảng 15 phút | In **KẾT QUẢ: ĐẠT**, `storage/perf` có `-don-le.md` và `-tai-100.md` của hôm nay; trong lúc chạy CRM vẫn dùng được (AC-10.8, ADR-016) | `app/tests/perf/locustfile_kn_crm.py` | Hiệu năng. Bán tự động | P1 |
| V9 | 4 Vận hành | `quantri` thêm cột tính sẵn `Giá × Số lượng` ở bảng vận đơn | Màn Sửa cột báo "đang được tính lại ở tác vụ nền #…", lưới hiện "Đang tính lại cột… n%" rồi tự nạp giá trị đúng; Tác vụ nền có dòng "Tính lại cột" (AC-11.35) | — | E2e + tác vụ nền. Bán tự động | P2 |
| A1 | Bổ sung Vận đơn mới (ADR-021) | Cuộn sâu, kéo cột đang ghim; bấm ô chữ dài, Escape, F2 | Không tải vô hạn, header và ô không lệch, giữ vị trí cuộn; đọc đủ chữ, popup nằm trong màn hình | — | E2e. Một phần có ở 4.5 bước 8. Mức: Tự động | P1 |
| A2 | Bổ sung ADR-021 | Ctrl+A rồi Copy/Delete trên tập lớn | Chọn toàn kết quả; vượt 2.000 ô thì báo lọc hoặc xuất, không cắt hay ghi âm thầm | — | E2e. Chưa có bài riêng (**chưa xác minh**). Mức: Tự động | P1 |
| A3 | Bổ sung ADR-021 | Shift chọn qua biên 100 dòng; dán từ Excel có số 0 đầu và nhiều dòng | Đúng ID dòng, giữ tiếng Việt và chuỗi mã; ô sai hoặc bị khoá thì từ chối cả lượt | — | E2e. Mức: Tự động | P1 |
| A4 | Bổ sung ADR-021 | Undo sau khi người khác vừa sửa ô khác | Undo không đè sửa của đồng nghiệp | — | E2e hai trang. Bán tự động (cùng fixture `hai_trang` ở 4.5 bước 3) | P1 |
| A5 | Bổ sung ADR-021 | Chuyển giao dòng khi người cũ đang sửa | Người cũ mất quyền ở request tiếp theo, không ghi nháp lên dòng đó | — | E2e hai trang. Bán tự động | P1 |
| A6 | Bổ sung ADR-021 | Mở Thống kê với bộ lọc, chọn nhóm, đối chiếu bảng rồi về lưới | Hai chiều giữ điều kiện; biểu đồ tính trên toàn tập; tiền tách loại; thiếu chi tiết có cảnh báo | — | E2e. Mức: Tự động | P2 |
| A7 | Bổ sung ADR-021 | Desktop 1440, laptop 1280, mobile 390, zoom 125% | Không tràn trang hay vỡ cấu trúc; mobile cuộn trong lưới | — | Giao diện đáp ứng. `test_pha_luoi_ghi_chu.py::test_dien_thoai_390` phủ 390. Mức: Tự động | P2 |
| N1 | Chín hạng mục 10.09.2026 | Admin không có bộ phận chọn Sale và tạo đơn | Đơn mới nằm cuối, hàng đầu là số 1 | `docs/kiem-chung-master-nine.md`, `app/crm/tests/test_master_nine.py` | E2e. Tự động | P1 |
| N2 | Chín hạng mục | Sale đứng đơn xem dữ liệu và lịch sử | Xem được, không tự có quyền sửa mới | `test_master_nine.py` | E2e. Tự động | P1 |
| N3 | Chín hạng mục | Tab/Enter/IME, vùng chọn xanh, định dạng fs/c/bg, Undo/Redo, kéo hàng và cột, popup nội dung dài có nút X | Hoạt động đúng; IME thật xem 4.5 bước 12 | `master-grid.js` | E2e + Thủ công (IME thật) | P1 |
| N4 | Chín hạng mục | Rời trang khi còn nháp | Có cảnh báo (xem 4.5 bước 13) | `master-grid.js:1261` | E2e. Tự động | P1 |
| N5 | Chín hạng mục | Đối chiếu tệp xuất với dữ liệu đã lưu | Khớp từng ô | — | E2e. Tự động | P2 |
| N6 | Chín hạng mục | Thu quyền một dòng trong lượt dán hai dòng đang gửi | Server không ghi cả lượt; lưới gỡ dòng mất quyền, giữ nháp dòng còn quyền; không tự gửi phần còn lại; chỉ bấm Thử lại mới tạo lượt mới và kiểm quyền/CAS lần nữa | `test_master_nine.py` (phần quyền và CAS) | E2e hai trang. Bán tự động | P0 |

**Vai và tính năng docs/07 chưa có**

| Thiếu | Căn cứ | Mục trong kế hoạch này |
|---|---|---|
| Vai CEO (chỉ đọc toàn công ty) | ADR-044, AC-21.17, AC-44.6 | 4.10 |
| Vai Kế toán (sửa báo cáo mọi bộ phận, kho chứng từ) | ADR-038 | 4.8 |
| Vai CSKH (chỉ dòng được giao, không có Tôi/Toàn bộ) | ADR-033, AC-33.6 | 4.7 |
| Vận đơn Leader (phân công trong ô) và tài khoản mẫu `vd.leader` | AC-21.15 | 4.6 |
| Lên đơn ở CRM, tóm tắt, chống gửi trùng `ma_lan_nop` | AC-6.11, AC-6.14 | 4.1 bước 3 |
| Hộp Chi tiết sản phẩm, Bỏ chi tiết | AC-18.3, AC-36.9 | 4.5 bước 6 |
| Tôi / Toàn bộ | ADR-033, AC-33.3 | 4.2 bước 2, 4.5 bước 5 |
| Admin xoá dòng và bỏ đơn | ADR-049 | 4.9 bước 6 và 7 |
| Sửa, bỏ, khôi phục báo cáo; Admin sửa ✎ trên tổng hợp | ADR-041, ADR-050 | 4.2 bước 4 và 5, 4.9 bước 8 |
| Thống kê `/thong-ke/` và lối sang ERP | AC-40.9 | 4.2 bước 10 |
| Kho chứng từ thanh toán (theo cờ) | `PAYMENT_DOCUMENTS_ENABLED` | 4.5 bước 11, 4.8 bước 2 |
| Đặt lại mật khẩu theo ma trận ADR-044 | ADR-044 | 4.2 bước 1, 4.10 bước 5 |
| Sự cố khi có nháp: hết phiên, đổi quyền, hai tab 409, `schema_changed`, gửi lại cùng UUID | TL-02, TL-18, TL-86, AC-21.3, AC-27.6 | 4.5 bước 2 và 3 |
| Bộ gõ tiếng Việt thật (Unikey, EVKey, Telex macOS) trên lưới và tìm khác hệ điều hành | AC-9.6, `docs/kiem-chung-san-loi-go-tieng-viet-20261006.md` mục "Chưa kiểm" | 4.5 bước 12 |
| Tài khoản mẫu cho CEO, Kế toán, CSKH, VĐ Leader trong `du_lieu_mau` và `docs/tai-khoan-mau.md` | `du_lieu_mau.py` dòng 48–60 | Chuẩn bị chung (cần chủ dự án chốt) |
| Fixture dùng chung cho VĐ Leader/Manager (hiện dựng riêng ở 6 tệp) | `app/crm/tests/conftest.py` chỉ có `dich_vu_kn_crm` | 4.6 (ghi chú tài khoản bài máy) |

### Các tệp quan trọng để thực hiện
- /home/user/KNJSC/docs/07-kich-ban-nghiem-thu.md
- /home/user/KNJSC/app/tests/e2e/conftest.py
- /home/user/KNJSC/app/conftest.py
- /home/user/KNJSC/app/core/management/commands/du_lieu_mau.py
- /home/user/KNJSC/app/orders/services/assignment_service.py
- /home/user/KNJSC/app/static/js/master-grid.js
- /home/user/KNJSC/docs/kiem-chung-san-loi-go-tieng-viet-20261006.md
- /home/user/KNJSC/app/core/management/commands/sao_luu.py
- /home/user/KNJSC/app/core/tests/test_sao_luu.py
