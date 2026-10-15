> Phần của [Kế hoạch kiểm thử toàn diện KNJSC](../08-ke-hoach-kiem-thu-toan-dien.md) — mục lục, lộ trình P0/P1/P2 và rủi ro còn lại nằm ở tệp đó.

## 6. Danh sách kiểm tay Chặng 2 theo vùng đụng tới

Chặng 2 là lúc người thật bật hệ thống trên máy local và dùng thử bằng tay. Nó không thay cho `pytest` (CLAUDE.md, mục quy trình). Một lượt kiểm gồm ba phần, làm theo thứ tự:
1. Khói 5 phút (6.2). Thay đổi nào cũng phải làm.
2. Các gói kiểm 10–15 phút (6.3) của mọi vùng mà thay đổi đụng tới (tra ở 6.1).
3. Ghi kết quả theo 6.4.

### 6.0 Chuẩn bị chung (làm một lần mỗi lượt)

| Việc | Cách làm | Ghi chú |
|---|---|---|
| Bật hệ thống | Windows: nháy đúp `KN JSC.bat`. Linux/Mac: `./scripts/cap-nhat-local.sh` | Mở KN ERP `http://127.0.0.1:8020` và KN CRM `http://127.0.0.1:8021` |
| Dữ liệu mẫu | `python manage.py du_lieu_mau`, sau đó `configure_erp_reports` và `configure_delivery_daily_report` | `du_lieu_mau` chỉ chạy khi DEBUG. Mỗi lần chạy, mật khẩu được đặt lại và phiên của 16 tài khoản mẫu bị huỷ (TL-30) |
| Mật khẩu chung | `matkhaucuatoi` (docs/tai-khoan-mau.md) | `sale.moi` dùng để thử buộc đổi mật khẩu |
| Bốn vai thêm từ #118 | `giamdoc` (CEO), `kt.staff` (Kế toán), `cskh.staff` (CSKH), `vd.leader` | Có sẵn trong `du_lieu_mau` từ 14.10.2026. Máy dựng trước đó thì chạy lại `du_lieu_mau` |
| Hai tài khoản cùng lúc | Mở hai trình duyệt khác nhau, hoặc hai hồ sơ trình duyệt | Trên 127.0.0.1, ERP 8020 và CRM 8021 **dùng chung cookie** (TL-86). Đăng nhập tài khoản khác ở một tab là tab kia đổi người theo |
| Theo dõi lỗi | Để mở `docker compose -f deploy/docker-compose.yml logs -f web bangtinh worker` và DevTools (Console, Network) | Thấy traceback hoặc lỗi JS đỏ thì ghi "không đạt", kể cả khi màn hình trông vẫn đúng |

### 6.1 Ánh xạ "thay đổi đụng tới đâu" → gói kiểm

| Thay đổi đụng tới (tệp / thư mục / màn hình) | Gói phải chạy | Lệnh tự động nên chạy trước (người duy trì) |
|---|---|---|
| `app/core/` (đăng nhập, `middleware.py`, `scope.py`, nhật ký), `app/org/`, `/dang-nhap/`, `/doi-mat-khau/`, `/nhan-su/`, `/bo-phan/…`, `/ma-tran-quyen/` | K1 | `pytest org/tests core/tests/test_shared_login.py core/tests/test_ma_tran_quyen_hai_dich_vu.py tests/test_khoi.py` |
| `app/core/money.py` (tiền) | K2 (dòng nhập tiền), K4, K5 | `pytest orders reports -m 'not trinh_duyet'` |
| `app/core/request_metrics.py`, `core/context_processors.py` | K1, K7 | `pytest tests/test_khoi.py tests/test_gom_p95.py` |
| `app/forms_builder/`, ERP `/bang/…`, `/bieu-mau/…`, nhập/xuất Excel, cấp quyền | K2 | `pytest forms_builder -m 'not trinh_duyet'`, `manage.py kiem_tra_du_lieu` |
| `app/crm/` (trừ phần đơn), `static/js/master-grid.js`, `master-working-copy.js`, `master-row-geometry.js`, `grid-focus.js`, `/bang-tinh/…`, `/thu-muc/`, `/thong-ke/`, trang chủ 8021 | K3 | `pytest crm/tests -m 'not trinh_duyet'`, `node scripts/kiem-thu-master-working-copy.cjs`, `node scripts/kiem-thu-master-queue-unit.cjs` |
| Template, CSS của trang lưới CRM, thanh công cụ, chân trang lưới | K3 (K3-14 đến K3-17 bắt buộc) | Không có bài tự động cho bố cục: AC-11.1, AC-11.11, AC-11.18, AC-11.27 là Thủ công trong docs/04 |
| `app/orders/`, `crm/*waybill*`, `order_views`, `payment_views`, `static/js/order-entry.js`, `waybill.js`, `waybill-feedback.js`, `payments.js`, `/van-don/…`, `/chung-tu-thanh-toan/` | K4 (và K3 nếu đụng lưới) | Bộ lệnh ở mục debug orders (7.3, dòng "Bài phân hệ đơn"); đụng Quốc gia / Loại tiền thì thêm `pytest crm/tests/test_market_currency.py` |
| `app/reports/`, `app/dashboard/`, `static/js/report-*.js`, `date-inputs.js`, `phan-trang.js`, `staff-code.js`, `/bao-cao/…`, `/` (Tổng quan) | K5 | `pytest reports dashboard -m 'not trinh_duyet'`, `node scripts/kiem-thu-date-inputs.cjs` |
| `app/documents/`, `feed/`, `taskboard/`, `culture/`, `resources/`, `/bang-tin/`, `/cong-viec/`, `/van-hoa/`, `/tai-nguyen/`, tab Tài liệu | K6 | `pytest documents feed taskboard culture resources -m "not trinh_duyet"` |
| `deploy/`, `knjsc/settings/`, `knjsc/celery*`, `requirements*`, `scripts/backup.sh`, `restore.sh`, `KN JSC.bat` | K7 | `manage.py check`, `check --deploy` (K7-12) |
| Migration của bất kỳ app nào | K7 (dòng 1, 2, 11), gói của app đó, `kiem_tra_du_lieu` | `pytest core/tests/test_chuyen_doi.py` |
| `templates/base.html`, CSS chung, `loi-mang.js`, `chon.js`, menu | Khói 5 phút, K1-13 (menu theo vai), K6-12 (390px) | `pytest core/tests/test_giao_dien.py core/tests/test_quyen_menu_erp.py` |
| `app/tests/`, `conftest.py`, `pytest.ini`, `.github/workflows/ci.yml`, `docs/04`, `docs/06`, `docs/07` | K8 | `pytest tests/test_truy_vet.py tests/test_live_server_requests.py tests/test_khoi.py` |
| Tài liệu thuần (không đụng mã) | Chỉ K8-9, K8-10 nếu đụng docs/07 | Không bắt buộc khói |

### 6.2 Khói 5 phút (bắt buộc với mọi thay đổi)

Đi theo thứ tự dưới đây. Mỗi bước để lại dữ liệu cho bước sau. Dùng một trình duyệt, đổi tài khoản bằng Đăng xuất.

| # | Tài khoản | Thao tác | Kết quả mong đợi | Góc nhìn · Loại · Cách · Ưu tiên |
|---|---|---|---|---|
| S1 | `sale.staff` | Đăng nhập ở `127.0.0.1:8020/dang-nhap/`, bấm nút KN CRM | Vào Tổng quan ERP, sang 8021 mà không phải đăng nhập lại | Người dùng · Khói/đăng nhập chung · Thủ công · P0 |
| S2 | `sale.staff` | 8021 `/van-don/len-don/`: chọn Canada, PTTT Zelle, một dòng sản phẩm giá `10,50`, Lưu đơn | Báo "Đã lưu đơn DH-ddmm-NNNN vào Vận đơn mới lúc HH:MM" (giờ VN), có nút Xem đơn gốc | Người dùng · Khói chức năng · Thủ công · P0 |
| S3 | `mkt.staff` | 8020 `/bao-cao/`: điền các trường bắt buộc (CPQC `13250000`), Nộp | Về Lịch sử, có dòng mới; Doanh số dạng `xx.xxx.xxx VND` | Người dùng · Khói chức năng · Thủ công · P0 |
| S4 | `mkt.manager` | 8020 `/bao-cao/tong-hop/?nguon=bao_cao_mkt` | Thấy báo cáo vừa nộp; thanh trên có "· Tiền: ₫"; **không** có tab "Theo sản phẩm" (nếu có tab này là đang rơi về bản kiểu cũ, xem 7.3) | Người dùng · Khói chức năng · Thủ công · P0 |
| S5 | `vd.staff` | 8021 Bảng tính → thư mục Vận đơn → lưới `van_don`: tìm đơn của S2, sửa ô Ghi chú, F5 | Dòng S2 có "Đã lên đơn", "Chưa thanh toán", CAD. Thanh trạng thái báo "Đã lưu", F5 vẫn còn giá trị | Người dùng · Khói lưới · Thủ công · P0 |
| S6 | Người vận hành | Xem log `web`, `bangtinh`, `worker` và Console DevTools | Không có traceback, không có "CANH BAO", không lỗi JS đỏ, không request 500 trong Network | QA · Khói vận hành · Thủ công · P0 |

Một bước S1–S6 không đạt thì **dừng lượt kiểm**: không gộp `main` và giữ lại ở `Staging` (CLAUDE.md, Chặng 3).

### 6.3 Gói kiểm theo phân hệ (mỗi gói 10–15 phút)

Gói nào cũng ngầm hiểu: góc nhìn **Người dùng**, cách **Thủ công**, trừ khi cột cuối ghi khác. Dòng "ghi nhận" là lỗ hổng đã biết (G-xx, TL-xx). Gặp lại thì ghi kết quả, không cần sửa ngay trong lượt.

#### K1. Xác thực, tổ chức, phân quyền nền (core, org)

| # | Tài khoản | Thao tác | Kết quả mong đợi | Loại · Ưu tiên |
|---|---|---|---|---|
| K1-1 | `sale.moi` | Gõ tên đăng nhập viết HOA `SALE.MOI`; mở `/bao-cao/`; đổi mật khẩu; mở 8021 | Vào được, bị chuyển về `/doi-mat-khau/` (kể cả khi mở `/bao-cao/`). Đổi xong thì vào Tổng quan, 8021 không hỏi đăng nhập | Chức năng · P0 |
| K1-2 | `sale.staff`, `quantri` | Gõ sai mật khẩu 5 lần, lần 6 gõ đúng. Sau đó `quantri` mở `/nhat-ky/?hanh_dong=login_failed` | Báo "Tài khoản đang bị khoá tạm. Vui lòng thử lại sau 15 phút."; nhật ký có 5 dòng và một dòng "Khoá tạm 15 phút" (hiện chưa đạt: TL-108) | Bảo mật · P0 |
| K1-3 | `sale.staff` (đang mở 8020 và 8021), `quantri` (trình duyệt khác) | `quantri` đổi Team của `sale.staff` sang Sale 2 rồi Lưu | Bấm bất kỳ đâu ở cả hai cổng đều về `/dang-nhap/?doi_quyen=1`, có lời "Quyền của bạn vừa thay đổi" | Bảo mật/phiên · P0 |
| K1-4 | `sale.leader` | Mở `/nhan-su/`; mở Sửa của `sale.staff`; gõ thẳng `/nhan-su/<pk sale.staff2>/sua/` | Chỉ thấy team Sale 1 và chính mình; có form Đặt lại mật khẩu, không có ô Cấp bậc; URL của `sale.staff2` trả 403 | Phân quyền · P0 |
| K1-5 | `sale.manager`, `sale.leader2` | Đặt lại mật khẩu cho `sale.leader2`: lần đầu gõ hai ô khác nhau, sau đó gõ đúng | Lần sai: báo lỗi, ô trống, không hiện lại mật khẩu. Lần đúng: báo "Đã đặt lại mật khẩu"; phiên của `sale.leader2` bị đẩy ra; đăng nhập mật khẩu mới không bị buộc đổi | Chức năng · P1 |
| K1-6 | `quantri` | Tạo "Lê Thưởng Thuận", để trống mã và tên đăng nhập; F5 trang kết quả; tạo thêm một người cùng tên | Ô Mã tự điền `THUANLT`, hiện mật khẩu tạm 16 ký tự, F5 không hiện lại mật khẩu; người thứ hai được mã `THUANLT2` | Chức năng · P1 |
| K1-7 | `quantri` | Xoá `sale.staff2`: bấm Xoá khi chưa tích ô, rồi tích ô và xác nhận | Chưa tích thì không xoá. Tích rồi thì biến khỏi Nhân sự; báo cáo và đơn cũ vẫn hiện `HANGLT`; đăng nhập `sale.staff2` báo lời chung (BR-4) | Chức năng · P1 |
| K1-8 | `giamdoc` (CEO) | Xem menu; mở `/nhat-ky/`, `/quan-tri/`, `/bang/`, `/nhan-su/`; gõ vào một ô lưới CRM | Không có nhóm Quản trị, không có "Nộp báo cáo ngày"; `/nhat-ky/` và `/quan-tri/` bị chặn; `/bang/` và `/nhan-su/` mở được; ô lưới bị từ chối (ADR-044) | Phân quyền · P0 |
| K1-9 | `quantri` | Tạo team "Sale 3" thuộc Sale ở Bộ phận và team | Team hiện ngay trong danh sách và trong ô Team của Sửa hồ sơ (AC-2.4). Thử chọn trưởng nhóm `mkt.leader`: **ghi nhận** có bị chặn không (G10) | Chức năng · P1 |
| K1-10 | `vd.staff` | Đặt `SESSION_IDLE_TIMEOUT_SECONDS=120` trong `.env`, chờ 3 phút rồi gõ một ô lưới | Báo hết phiên, không hiện "Đã lưu". **Ghi nhận** phiên có tự gia hạn nhờ poll 8 giây không (G6) | Phiên · P0 |
| K1-11 | `quantri`, `sale.manager` | `quantri` mở `/ma-tran-quyen/` và `/tac-vu/`; `sale.manager` gọi thẳng hai URL đó | `quantri` 200, `sale.manager` 403 tiếng Việt. **Ghi nhận** dòng "Nộp báo cáo ngày" cột Giám đốc đang hiện ✓ sai (G12) | Phân quyền · P1 |
| K1-12 | `sale.staff` | Đăng xuất, bấm nút Lùi | Không thấy dữ liệu trang trước | Bảo mật · P1 |
| K1-13 | `quantri` | `/quan-tri/login/` ở cửa sổ ẩn danh: trang chuyển về `/dang-nhap/` (#121); gõ sai 6 lần ở đó. Trên DB local có sao lưu: tự hạ cấp bậc của mình | Bị khoá tạm 15 phút như K1-2; tài khoản đang bị khoá không vào được `/quan-tri/`. **Ghi nhận** có chặn tự hạ cấp không (G2) | Bảo mật · P1 (QA) |

#### K2. Bảng dữ liệu ERP, biểu mẫu, nhập/xuất, cấp quyền (forms_builder)

| # | Tài khoản | Thao tác | Kết quả mong đợi | Loại · Ưu tiên |
|---|---|---|---|---|
| K2-1 | `mkt.manager` | ERP Bảng dữ liệu → `bao_cao_mkt`; bấm liệt kê thô (`?dang=tho`), sang trang 2, sắp xếp | Mặc định ra báo cáo chi tiết theo ngày; ở bản thô, phân trang và sắp xếp vẫn giữ `dang=tho`; không ô nào sửa được; không có nút sang KN CRM (AC-42.13, ADR-014, AC-40.7) | Chức năng · P0 |
| K2-2 | `mkt.manager` | Bấm tiêu đề cột CPQC hai lần, lật trang 2 | Chỉ khối bảng đổi (không tải lại trang), URL có `?sap=…&chieu=giam`, không có dòng lặp (AC-7.13) | Giao diện · P1 |
| K2-3 | `mkt.manager` | Cột CPQC: đặt màu vàng và ngưỡng "Đỏ khi lớn hơn 400000000"; thử đặt ngưỡng cho cột chữ | Bảng tô đúng; cột chữ báo lỗi rõ (AC-8.9) | Chức năng · P2 |
| K2-4 | `mkt.manager` | Bật bộ lọc, Xuất Excel; nhập lại chính tệp đó | Đúng số dòng và thứ tự, không có cột ẩn, ô bắt đầu `=` là chữ; xem trước đúng ánh xạ; tác vụ "không có dòng lỗi" (AC-7.7, AC-7.14) | Chức năng · P0 |
| K2-5 | `mkt.manager` | Nhập tệp có ô tiền `0.125` và `1.234,5` (định dạng chữ) | **Ghi nhận**, không chặn: #124 (ADR-052) mới sửa Bước 1 — số máy gửi lại (hoàn tác, dán từ lưới, ô sửa); ô chữ `0.125` trong tệp vẫn đọc theo luật người gõ ra 125 cho tới khi làm Bước 2 (chờ duyệt). `1.234,5` phải ra 1234,5 | Dữ liệu · P0 |
| K2-6 | `mkt.manager` | Nhập tệp `.exe` đổi đuôi `.xlsx`; tệp lớn hơn 10 MB; tệp thiếu cột bắt buộc | Hai tệp đầu bị từ chối; tệp thiếu cột báo tên cột (AC-7.8, AC-7.9) | Bảo mật · P1 |
| K2-7 | `sale.manager`, `mkt.manager` | `sale.manager` cấp quyền Xem bảng Sale cho `mkt.manager` | Phiên `mkt.manager` bị đăng xuất (AC-1.6); đăng nhập lại thấy bảng ở chế độ Xem | Phân quyền · P0 |
| K2-8 | `mkt.manager` | POST thẳng `/bang/<bảng Sale>/cap-quyen/`, tự cấp quyền Sửa cho mình (DevTools/curl có CSRF) | **Phải 403** (TL-01 đã sửa ở #122) | Bảo mật · P0 (QA, bán tự động) |
| K2-9 | `sale.manager`, `mkt.manager` | Thu quyền vừa cấp | `mkt.manager` không còn thấy bảng (404). **Ghi nhận**: "Ai xem được bảng này" có còn liệt kê quyền đã thu không | Phân quyền · P1 |
| K2-10 | `mkt.manager` | `/bieu-mau/?tab=forms` → `bc_mkt_ngay`: nối trường thư viện vào cột cùng kiểu; nối trường chữ vào cột số; bỏ trường | Cùng kiểu thì lưu được; trường chữ vào cột số báo "không ghi được vào cột … kiểu …" (AC-8.6); bỏ trường thì dữ liệu cũ còn (AC-8.5) | Chức năng · P1 |
| K2-11 | `mkt.staff` | `/bieu-mau/bc_mkt_ngay/dien/`; bỏ trống trường bắt buộc; gửi đúng; GET `/bieu-mau/?tab=forms` | Ô Marketer chỉ đọc, mang mã mình; thiếu trường thì không gửi được; gửi đúng thêm một dòng; `?tab=forms` trả 403 (AC-4.6, AC-8.2) | Phân quyền · P1 |
| K2-12 | `quantri` | 8021 `/bang-tinh/<bảng thử>/xoa-bang/`: nhập sai tên; bảng còn biểu mẫu; bảng không có biểu mẫu → khôi phục | Sai tên trả 400; còn biểu mẫu thì bị chặn kèm tên biểu mẫu; xoá được thì `/bang-da-xoa/` có bảng; khôi phục giữ dữ liệu (AC-27.4, AC-27.5) | Chức năng · P2 |
| K2-13 | `vd.staff`, người vận hành | ERP `/bang/`; sau cùng chạy `manage.py kiem_tra_du_lieu` | `/bang/` trả 403 với `vd.staff`; lệnh in "Dữ liệu khớp." | Phân quyền/dữ liệu · P0 (bán tự động) |

#### K3. Lưới KN CRM, thư mục, thống kê (crm, JS lưới)

| # | Tài khoản | Thao tác | Kết quả mong đợi | Loại · Ưu tiên |
|---|---|---|---|---|
| K3-1 | `quantri` | Trang chủ 8021 và sidebar | Có 4 ô số; "Bảng gần đây" chỉ có "Vận đơn mới"; Tác vụ nền và Nhật ký mở được, không 404 | Khói · P1 |
| K3-2 | `mkt.manager` | Xem sidebar; mở `/thu-muc/`, `/bang-tinh/van_don/`, `/thong-ke/`, bấm "Mở dữ liệu" nguồn MKT | Không có "Bảng tính"; `/thu-muc/` trả 404 có lời; `van_don` trả 403/404; `/thong-ke/` mở được; "Mở dữ liệu" sang Báo cáo tổng hợp ERP đúng kỳ (AC-40.9, TL-89) | Phân quyền · P0 |
| K3-3 | `vd.staff` | Sửa ô Ghi chú, F5; chuột phải vào ô | "Đã lưu", F5 vẫn còn; Lịch sử ô có mã VĐ và giờ VN | Chức năng · P0 |
| K3-4 | `vd.staff` (hai tab) | Tab 1 sửa ô Tên khách; tab 2 sửa cùng ô trước khi kịp cập nhật | Tab 2 hiện hộp Đối chiếu xung đột (409, CAS); chọn giữ giá trị hiện tại thì không ghi đè | Đồng thời · P0 |
| K3-5 | `vd.staff` | DevTools Offline, gõ 2 ô, sau đó bật mạng | Báo "Lỗi lưu" kèm lời "Mất kết nối mạng…", chữ còn nguyên; có mạng lại thì tự lưu đúng một lần | Chịu lỗi · P0 |
| K3-6 | `vd.staff` | Bấm Tôi, F5, bấm Toàn bộ; lọc cột Quốc gia, bấm × trên chip | URL có `cua_toi=1`; F5 vẫn ở Tôi; chip nằm giữa nút Cột và Định dạng, × bỏ được chip | Giao diện · P1 |
| K3-7 | `sale.staff` | Mở lưới; menu "…" | Không có Tôi/Toàn bộ, chỉ thấy đơn mình (TL-87); không có Xoá dòng; chưa có đơn thì chuyển sang Lên đơn | Phân quyền · P0 |
| K3-8 | `vd.manager`, `vd.staff` | `vd.manager` ẩn cột Ghi chú với cả công ty, sau đó Hiện lại; Xuất Excel khi đang ẩn | Đang ẩn: `vd.staff` F5 không thấy cột, không có mục "Đang ẩn", tệp xuất không có cột. Hiện lại: cột về chỗ cũ, đủ dữ liệu | Chức năng · P1 |
| K3-9 | `vd.manager`, `vd.staff` | Tạo thư mục "Thử", xếp bảng vào, đổi tên, xoá | Xoá thư mục thì bảng về "Không thư mục"; `vd.staff` không có ô tạo thư mục | Chức năng · P2 |
| K3-10 | `quantri` | Chọn 2 dòng (số dòng + Shift) → "…" → Xoá dòng đang chọn → xác nhận → Ctrl+Z | Hộp xác nhận đặt con trỏ ở Huỷ; số dòng giảm, đơn gốc bị bỏ; Ctrl+Z đưa dòng về ngay | Chức năng · P1 |
| K3-11 | CEO, CSKH, Kế toán | CEO gõ ô và gọi `/nhap-tep/`; CSKH ghi một ô; Kế toán mở Thống kê nguồn Vận đơn | CEO: ô chỉ đọc, `/nhap-tep/` trả 403. CSKH: thấy đúng đơn được giao, ghi trả 403. Kế toán: có Tôi/Toàn bộ, tiền tách USD/VND, không cộng lẫn (BR-8) | Phân quyền · P0 |
| K3-12 | `vd.staff` | Dán tên khách tiếng Việt dạng tổ hợp (NFD); tìm bằng chữ gõ thường; sửa một ô cũ dạng NFD | Tìm ra dòng; sửa không bị 409 (TL-79) | Dữ liệu · P1 |
| K3-13 | Bất kỳ | DevTools Network: tham số `master-grid.js?v=…`; mở panel Bộ lọc | Đúng phiên bản mới; panel không 404 (TL-80) | Phát hành · P1 |
| K3-14 | `vd.staff` | Mở lưới `van_don` có nhiều dòng; cuộn sang phải hết cỡ, rồi cuộn xuống cuối | Ngày (lên đơn) là cột dữ liệu đầu tiên; năm cột đầu (Trùng, Ngày, Mã đơn, Tên khách, SĐT) đứng yên khi cuộn ngang; hàng tiêu đề đứng yên khi cuộn dọc; đủ cột của bảng vận đơn (AC-11.1, docs/04 dòng 285) | Giao diện · P1 |
| K3-15 | `vd.manager` (hoặc `vd.staff`) | Mở lưới; kéo mép tiêu đề một cột rộng ra; kéo thả tiêu đề một cột sang chỗ khác; ẩn hai cột; thu gọn thanh bên; F5; bấm Đặt lại cột | Trang toàn màn hình riêng, không thanh bên hệ thống, lưới chiếm hết cửa sổ, menu ☰ dẫn về màn hình khác; mọi ô có viền; cột có chữ A B C đánh lại theo cột đang hiện; F5 vẫn giữ độ rộng, thứ tự, cột ẩn, thanh bên thu gọn; Đặt lại cột về mặc định (AC-11.18, docs/04 dòng 302). Thanh công cụ trong AC còn ghi "thêm dòng": **ghi nhận** nếu không có, vì ADR-040 và AC-11.14 đã bỏ đường thêm dòng trên lưới. docs/06 dòng 195 ghi tài khoản `mkt.manager`, nhưng tài khoản này không mở được lưới (K3-2), nên dùng tài khoản VĐ | Giao diện · P1 |
| K3-16 | `vd.staff` | Đặt lưới cạnh ảnh `docs/tham-khao/kn-demo/` (`02-sheet-van-don.png`, `03-chon-vung-tay-keo-dien.png`, `06-thanh-cong-thuc.png`, `07-nhieu-trang-them-dong.png`); kéo chuột chọn vùng; bấm ⛶ rồi Esc | Khung tối viền vàng; thanh công cụ đúng thứ tự demo; thanh công thức có ô địa chỉ; có cột số dòng; chữ cột A B C có nút ▼; hàng tên cột là hàng 1; ô 25px có viền; trạng thái lưu ở thanh trên; vùng chọn có viền vàng và tay kéo điền; ⛶ phóng toàn màn hình (AC-11.27, docs/04 dòng 311; docs/07 dòng 101). "Cột trống tới Z" và chân trang "+100 dòng": **ghi nhận** có hay không. Grep không thấy chuỗi "+100" trong `master-grid.js` và `templates/`, và K8-10 coi dòng trống cuối lưới là kiểu cũ. Còn chưa xác minh AC này đã lỗi thời theo ADR-040 hay chưa | Giao diện (đối chiếu ảnh) · P2 |
| K3-17 | `vd.staff`, màn 400px hoặc điện thoại | Mở lưới `van_don`, bấm một ô, mở hộp lọc cột | Cả trang không tràn ngang; lưới cuộn trong khung; bấm được ô; hộp lọc mở được (AC-11.11, docs/06 dòng 193, docs/07 dòng 143) | Giao diện · P2 |

#### K4. Lên đơn, khách, sản phẩm, vận đơn, phân công, thanh toán (orders)

| # | Tài khoản | Thao tác | Kết quả mong đợi | Loại · Ưu tiên |
|---|---|---|---|---|
| K4-1 | `sale.staff` | `/van-don/len-don/`: xem Quốc gia, PTTT, Loại tiền; chọn Canada | Quốc gia và PTTT trống; Loại tiền chỉ đọc, đổi thành CAD; PTTT đúng 7 mục (Zelle, PayPal, Visa/Website, Cheque, Western Union, RIA, Money Gram) | Chức năng · P0 |
| K4-2 | `sale.staff` | 2 dòng, giá `10,50` và `3`, Lưu; mở đơn gốc | Tóm tắt "2 dòng · N sản phẩm · Tổng … CAD"; đơn gốc chỉ đọc, **không** có "Bỏ đơn này" | Chức năng/tiền · P0 |
| K4-3 | `sale.staff` | Đơn mới, gõ lại SĐT vừa dùng, sửa tên khách | Hiện "Khách mua lại — đã có 1 đơn", tên tự điền; sửa tên thì cảnh báo "Lưu đơn sẽ đổi tên khách của số …" kèm cả hai tên | Chức năng · P1 |
| K4-4 | `sale.staff` | Có giá rồi đổi Quốc gia → Huỷ | Có hộp hỏi giữ số tiền; Huỷ thì giữ quốc gia và loại tiền cũ; không có hộp "Tạo sản phẩm" | Chức năng · P1 |
| K4-5 | `sale.leader` | Tạo sản phẩm "Đèn test", sau đó "đèn TEST" | Lần đầu có trong mọi ô chọn; lần hai báo đã có trong danh mục | Chức năng · P2 |
| K4-6 | `sale.staff2`, `sale.leader` | Mở URL đơn gốc của `sale.staff` | `sale.staff2` nhận 404 (ngoài phạm vi phải từ chối); `sale.leader` mở được | Phân quyền · P0 |
| K4-7 | `vd.staff` | Lưới: xem dòng mới; gõ Loại tiền, Giá tiền, Phụ trách; mở `/van-don/len-don/` | Có "Đã lên đơn", "Chưa thanh toán", CAD, cột `sl_*` không hiện; các ô bị từ chối; Lên đơn trả 403 | Phân quyền · P0 |
| K4-8 | `vd.staff` | Chi tiết sản phẩm: nhập "Đã thanh toán" từng dòng, Lưu; bỏ hết dòng, Lưu | Số tiền thanh toán đổi, Trạng thái thanh toán **không** tự đổi; bỏ hết thì bốn ô tổng trống | Chức năng · P1 |
| K4-9 | `vd.manager`, `quantri` (hai trình duyệt) | Cùng phân công một dòng (ô "Phụ trách Vận đơn" có "— Chưa gán —" và `TUHV`) | Bên lưu sau báo "Phân công vừa được thay đổi", không ghi đè | Đồng thời · P0 |
| K4-10 | `quantri` | Đổi Quốc gia một dòng có tiền sang Hoa Kỳ | Có hộp xác nhận; Loại tiền thành USD, số tiền giữ nguyên, đơn gốc vẫn CAD (ADR-046) | Tiền · P0 |
| K4-11 | `quantri` | Đơn gốc → "Bỏ đơn này"; khôi phục dòng trên lưới | Dòng biến khỏi lưới; khôi phục xong thì mở lại được đơn gốc | Chức năng · P1 |
| K4-12 | `mkt.staff`, `sale.staff` | `mkt.staff` mở `/van-don/len-don/`; `sale.staff` mở ERP `8020/len-don/` | `mkt.staff` trả 403; ERP chuyển sang Lên đơn ở 8021 (F1, không chuyển tiếp POST) | Phân quyền · P1 |
| K4-13 | `vd.staff`, Kế toán | Khi `PAYMENT_DOCUMENTS_ENABLED=1`: tạo chứng từ Ref `000123` kèm 1 ảnh PNG, thử xoá | Ô Bill hiện link; `vd.staff` bị chặn xoá; Kế toán xoá và khôi phục được | Chức năng · P1 (chỉ khi đụng chứng từ) |
| K4-14 | Người vận hành | `docker compose -f deploy/docker-compose.yml exec web python manage.py kiem_tra_du_lieu --bang van_don` | In "Dữ liệu khớp", mã thoát 0 | Dữ liệu · P0 (bán tự động) |
| K4-15 | `quantri` | Lưới `van_don`: (a) xoá trống ô Quốc gia của một dòng chưa có tiền; (b) chọn vùng Quốc gia, Bang, Thành phố của một dòng có tiền rồi bấm Delete, xác nhận, F5; (c) gõ lại Canada vào ô Quốc gia đó; (d) `sale.staff` lên đơn mà để trống Quốc gia | (a) Loại tiền trống theo, không hỏi. (b) Có hộp xác nhận như khi đổi quốc gia; xác nhận xong thì cả vùng (kể cả Quốc gia) và Loại tiền trống, ghi trong một lượt, số tiền giữ nguyên, F5 vẫn vậy. (c) Lại hỏi xác nhận vì dòng có tiền; xác nhận xong Loại tiền thành CAD. (d) Không lưu được đơn (Quốc gia vẫn bắt buộc khi lên đơn và nhập tệp). AC-33.8 (docs/04 dòng 575), ADR-033, ADR-031. Phía máy chủ đã có bài tự động `crm/tests/test_market_currency.py::test_clearing_country_clears_currency_and_asks_when_row_has_money`; ca tay này kiểm hộp xác nhận và hiển thị trên trình duyệt | Tiền · P0 (QA: chạy bài tự động trước) |

#### K5. Báo cáo ngày, Báo cáo tổng hợp, Tổng quan (reports, dashboard)

| # | Tài khoản | Thao tác | Kết quả mong đợi | Loại · Ưu tiên |
|---|---|---|---|---|
| K5-1 | `mkt.staff` | `/bao-cao/`: bấm Nộp hai lần liền (hoặc F5 gửi lại POST); bỏ trống CPQC | Chỉ có một báo cáo, lời "đã được ghi lúc HH:MM"; thiếu CPQC thì báo "Chưa điền các trường bắt buộc: CPQC", số đã gõ còn | Chức năng · P0 |
| K5-2 | `sale.staff` | Nộp Sale Canada; gõ `-5` vào Số Mess | Loại tiền tự CAD (chỉ đọc), không có ô Ngày ra đơn. **Ghi nhận** kết quả với `-5` (lỗ hổng chưa chốt) | Chức năng · P1 |
| K5-3 | `quantri`, `mkt.leader` | Form MKT có dropdown Team; nộp cho team khác | `mkt.leader` của đúng team đó thấy báo cáo ở Lịch sử | Phân quyền · P1 |
| K5-4 | `mkt.leader` | Sửa Số đơn của `mkt.staff`, Lưu; mở cùng màn ở tab khác, lưu tab cũ | Báo "Đã cập nhật"; có Lịch sử chỉnh sửa trước/sau; tab cũ nhận 409 "vừa được người khác sửa", số đang gõ còn | Đồng thời · P0 |
| K5-5 | `mkt.staff`, `mkt.manager`, `sale.manager` | `mkt.staff` mở `/bao-cao/<id>/sua/` của mình, bấm Bỏ; `mkt.manager` Khôi phục ở `/bao-cao/da-bo/`; `sale.manager` mở `/bao-cao/da-bo/` | Trang sửa trả 404; báo cáo bỏ biến khỏi Lịch sử; khôi phục thì số về lại Tổng hợp; `sale.manager` không thấy báo cáo MKT (BR-4) | Chức năng/phân quyền · P1 |
| K5-6 | `quantri` | Tổng hợp MKT → ✎ một lần nộp → sửa Số Mess → Lưu; lưu lại khi không đổi gì | Hộp đóng, bảng đổi tại chỗ, dòng sáng lên; TỔNG CỘNG ngày và toàn kỳ cộng đúng phần chênh; lưu không đổi gì thì báo "Không có số nào đổi" (ADR-050) | Chức năng · P0 |
| K5-7 | `quantri` | Ở hộp ✎, bật Offline rồi Lưu; bật mạng, Lưu lại | Báo lỗi trong hộp, số còn, không có "Đã lưu"; có mạng thì lưu được | Chịu lỗi · P1 |
| K5-8 | `sale.manager` | Tổng hợp Sale có cả CAD và USD; menu ⋯ Gộp/Không gộp; Xuất Excel | Mỗi loại tiền một dòng TỔNG CỘNG, không cộng lẫn (BR-8); đổi chế độ không tải lại trang, giữ ngày đang xem; tệp xuất khớp màn hình, có sheet theo nhân sự và theo ngày | Tiền · P0 |
| K5-9 | `sale.staff` | Sửa URL thành `&nhan_su=<id sale.staff2>`, rồi `&nguon=bao_cao_mkt` | Cả hai trả 403 (không trả danh sách rỗng); menu ⋯ không có Ngưỡng màu | Phân quyền · P0 |
| K5-10 | `mkt.manager` | Ngưỡng màu CPO: Tốt 900.000, Kém 800.000; sau đó nhập đúng | Báo lỗi "mốc Tốt phải nhỏ hơn mốc Kém", panel mở lại; nhập đúng thì ô tô xanh/vàng/đỏ, số hiện dạng VN | Chức năng · P2 |
| K5-11 | `mkt.manager`, `sale.manager`, `vd.manager` | Tổng quan `/`: đặt Từ ngày lớn hơn Đến ngày; gõ ngày `03092026` | Ba thẻ có số, mỗi loại tiền một cột; ngày sai thì chỉ thẻ đó báo lỗi, khối khác vẫn hiện; ô ngày tự thành 03/09/2026 | Chức năng · P1 |
| K5-12 | CEO, Kế toán | CEO mở Tổng hợp, Lịch sử, `/bao-cao/`; Kế toán mở Lịch sử | CEO: xem được mọi bộ phận, `/bao-cao/` trả 403, không có ✎/Sửa/Bỏ. Kế toán: thấy mọi bộ phận, sửa được, không có nút Bỏ | Phân quyền · P0 |

#### K6. Nội bộ: Tài liệu, Bảng tin, Công việc, Đánh giá nhân sự, Tài nguyên

| # | Tài khoản | Thao tác | Kết quả mong đợi | Loại · Ưu tiên |
|---|---|---|---|---|
| K6-1 | `sale.staff` | `/bang-tin/`: đăng bài có đường dẫn https | Thấy thiệp sinh nhật của mình, bài ghim ở đầu; bài mới lên đầu nhóm không ghim, link bấm được | Chức năng · P1 |
| K6-2 | `sale.staff` | Bấm Thích hai lần nhanh; gửi bình luận rỗng, rồi một bình luận thật | Số thích không nhảy hai; bình luận rỗng báo lỗi tiếng Việt; số bình luận cập nhật không tải lại trang | Chức năng · P1 |
| K6-3 | `sale.leader`, `mkt.manager` | `sale.leader` xem nút; `mkt.manager` ghim rồi gỡ ghim bài của `sale.staff`, gỡ bình luận của người khác | `sale.leader` không có Ghim, không có Gỡ ở bài người khác; `mkt.manager` làm được cả ba | Phân quyền · P1 |
| K6-4 | `sale.staff` | `/bieu-mau/?tab=documents`: tải về, mở liên kết; đổi `?muc=<mục MKT>` | Thấy mục toàn công ty và mục Sale, không thấy MKT; đổi `muc` thì 404 tiếng Việt | Phân quyền · P0 |
| K6-5 | `sale.manager` | Tải PDF thật; tải `.exe` đổi đuôi `.pdf`; thêm mục "quy trình sale" khi đã có "Quy trình Sale"; gỡ tài liệu | `.exe` bị từ chối, tiêu đề đã gõ còn; mục trùng (khác hoa thường) bị chặn; gỡ được | Bảo mật · P1 |
| K6-6 | `sale.staff` | `/cong-viec/moi/` không chọn người; Đang làm → Xong; tab thứ hai còn nút cũ, bấm Đang làm | Tự nhận việc; chip đổi tại chỗ (HTMX). **Ghi nhận** tab cũ có mở lại việc đã Xong không | Đồng thời · P1 |
| K6-7 | `sale.leader` | `/cong-viec/?tab=pham_vi`; đặt hạn sai `31/31/2026`; Gỡ việc không phải mình tạo | Thấy việc của `sale.staff`, không thấy của `sale.staff2`; hạn sai báo lỗi dưới ô, chữ còn; Gỡ trả 403 | Phân quyền · P1 |
| K6-8 | `vd.staff`, `sale.leader` | `/van-hoa/`: `vd.staff` xem; `sale.leader` ghi nhận `sale.staff` kèm lời nhắn, rồi gửi lời nhắn rỗng | `vd.staff` thấy bảng xếp hạng (tên, số đơn, tổng VND), không thấy mã đơn, không có form. `sale.leader` chỉ chọn được người team Sale 1; ghi nhận xong thì `/van-hoa/thanh-vien/<mã>/` thêm 1 sao; lời nhắn rỗng báo đúng ô | Chức năng · P1 |
| K6-9 | `mkt.manager`, `quantri` | `/tai-nguyen/moi/`: SIM ghi chú "OTP 483920"; sửa trạng thái sang Hỏng; `quantri` xem Nhật ký | OTP bị chặn; nhật ký có "Trạng thái: … → Hỏng" nhưng không có nội dung ghi chú (FR-13.4, `_scrub`) | Bảo mật · P0 |
| K6-10 | `sale.staff`, CEO | `sale.staff` lọc mục BM, tìm "via", gọi `/tai-nguyen/moi/`; CEO mở `/tai-nguyen/moi/`, `/tai-lieu/tai-len/` | `sale.staff` lọc và tìm được, `/moi/` trả 403. CEO: cả hai trang trả 403 ngay ở GET, không hiện form, mỗi lần một dòng DENIED (#127); `/cong-viec/` thấy mọi bộ phận nhưng không có nút đổi trạng thái; đăng được bài Bảng tin | Phân quyền · P1 |
| K6-11 | `quantri` (vận hành) | Chạy `thiep_sinh_nhat` và `thuong_sao_thang` hai lần liền | Lần hai in "0 thiep moi", "0 dong sao moi"; Nhật ký có dòng thưởng sao ghi tỉ giá | Tác vụ nền · P1 (bán tự động) |
| K6-12 | `sale.staff`, màn 390px | `/bang-tin/` (Thích, bình luận), lướt `/cong-viec/`, `/van-hoa/`, `/tai-nguyen/` | Thanh bên nằm dưới bài, không có thanh cuộn ngang (AC-13.6) | Giao diện · P1 |

#### K7. Nền tảng, vận hành (deploy, settings, Celery, sao lưu)

Góc nhìn: **QA/Người vận hành**, trừ dòng có ghi tài khoản người dùng.

| # | Tài khoản | Thao tác | Kết quả mong đợi | Loại · Ưu tiên |
|---|---|---|---|---|
| K7-1 | Người vận hành | Nháy đúp `KN JSC.bat` sau khi kéo nhánh có migration | In "Ma tren may khac lan chay truoc", migrate chạy, "restart worker beat", mở 8020; `storage/.kn-jsc-lan-truoc` bằng `git rev-parse HEAD` | Vận hành · P0 |
| K7-2 | Người vận hành | `docker compose -f deploy/docker-compose.yml ps`; `logs web --tail 50`; `logs beat --tail 20` | db, redis, web, worker, beat, bangtinh đều Up; không có "CANH BAO", không traceback; beat có dòng lịch | Vận hành · P0 |
| K7-3 | `quantri` | `./scripts/backup.sh`, tải lại Tổng quan, mở `/tac-vu/` | In "Đã sao lưu: knjsc-<giờ>.dump"; ô "Sao lưu đêm qua" đổi; tác vụ BACKUP "Xong" | Sao lưu · P0 |
| K7-4 | Người vận hành | `./scripts/restore.sh` không cờ | Chỉ liệt kê, mũi tên chỉ bản mới nhất, in "Chưa làm gì"; không container nào bị dừng | Sao lưu · P1 |
| K7-5 | `sale.staff`, `quantri` | GET `8020/tac-vu/` | `sale.staff` nhận 403 tiếng Việt; `quantri` 200 | Phân quyền · P1 |
| K7-6 | `sale.manager` | Nhập Excel nhỏ → `/tac-vu/<pk>/`; `docker compose stop redis` rồi xác nhận nhập lần nữa; `start redis` | Tiến độ tự cập nhật rồi "Xong". Redis tắt: vài giây sau báo "Không gửi được vào hàng đợi…", không trang 500 | Chịu lỗi · P0 |
| K7-7 | `mkt.manager` | Xuất Excel, tải tệp từ `/tac-vu/<pk>/tai/` | Số tiền đúng loại tiền; ô `=1+1` là chữ | Chức năng · P1 |
| K7-8 | Bất kỳ | `8020/khong-co-trang/` | Trang 404 tiếng Việt có nút về Tổng quan (AC-10.14) | Giao diện · P2 |
| K7-9 | Người vận hành | `exec -T web python manage.py check`; `showmigrations \| grep "\[ \]"` | Không lỗi, không migration chờ | Vận hành · P0 |
| K7-10 | Người vận hành (khi đụng settings/compose production) | `DJANGO_SETTINGS_MODULE=knjsc.settings.bangtinh BANGTINH_GOC=prod … python manage.py check --deploy --fail-level WARNING` (đủ biến như dữ liệu K7 nguồn); bỏ `SESSION_COOKIE_DOMAIN` | Thoát 0; bỏ biến thì báo `core.E001` | Cấu hình · P0 |
| K7-11 | Người vận hành (khi đụng JS/CSS) | `collectstatic --noinput --clear` trên bản sao; so sha256 `static/js/master-grid.js` với tệp nginx trả về | Khớp; mở panel Bộ lọc không lỗi JS (TL-80) | Phát hành · P1 |
| K7-12 | Người vận hành (khi có migration) | `run --rm -e RUN_MIGRATIONS=0 web python manage.py kiem_tra_du_lieu` | "Dữ liệu khớp", mã 0. Gặp "column val_order_code does not exist" là migration `forms_builder/0017` chưa áp (TL-76) | Dữ liệu · P0 |

#### K8. Hạ tầng kiểm thử, truy vết AC, tài liệu

Góc nhìn: **QA/Lập trình viên**, cách **Bán tự động** (chạy lệnh rồi đọc kết quả bằng mắt).

| # | Ai | Thao tác | Kết quả mong đợi | Ưu tiên |
|---|---|---|---|---|
| K8-1 | Lập trình viên | `docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest tests/test_truy_vet.py tests/test_live_server_requests.py tests/test_khoi.py tests/test_ma_tran_phan_quyen.py -rs` | 0 đỏ, không có SKIPPED ngoài lý do đã biết | P0 |
| K8-2 | Lập trình viên | `pytest -m "not trinh_duyet" -rs --durations=10` | Số bài bỏ qua bằng danh sách gắn biến môi trường đã biết (khoảng 17 tệp, chưa xác minh con số chính xác); bài chậm nhất không vượt nhiều so với CI | P1 |
| K8-3 | Lập trình viên (có Chromium) | `pytest tests/e2e -m trinh_duyet -vv -rs -o faulthandler_timeout=120` | Không bài nào SKIPPED vì "cần Playwright và Chromium"; không có cảnh báo TL-67 | P1 |
| K8-4 | Lập trình viên | `pytest -m trinh_duyet --ignore=tests/e2e -vv -rs` | 9 tệp `*_browser*.py` bỏ qua kèm lý do biến môi trường; `crm/tests/test_luoi_dong_trong_va_ghim_e2e.py` và 3 tệp `reports/*_e2e.py` đạt | P2 |
| K8-5 | Lập trình viên | Đổi AC trong docs/04 → cập nhật docs/06 (tổng, tự động, thủ công, "X trên Y", hoãn) → chạy `test_truy_vet` | Xanh mà không phải thêm mã vào `HOAN` (khi đã có bài) | P0 |
| K8-6 | Lập trình viên | Sửa `ci.yml` → PR vào `Staging` → tab Actions | Hai job xanh; bước e2e dưới 8 phút; log có dòng "N passed" (không thêm `-q`) | P1 |
| K8-7 | Lập trình viên | `node scripts/kiem-thu-master-working-copy.cjs`, `node scripts/kiem-thu-master-queue-unit.cjs` (khi đụng `master-grid.js`/`master-working-copy.js`) | Mã thoát 0 | P0 |
| K8-8 | Lập trình viên | Sau khi sửa `conftest.py` gốc: chạy `tests/e2e/test_sap_xep_khong_giat.py` 10 lần bằng vòng for | 0 lỗi "couldn't be flushed" hay "deadlock detected" | P1 |
| K8-9 | `vd.staff`, `mkt.manager` | 8021: thư mục của `vd.staff`; `mkt.manager` gõ `/bang-tinh/bao_cao_mkt/` | Cây phẳng, không có Quý/Tháng; `mkt.manager` nhận 404 (ADR-040). docs/07 mục 3.2 và 3.3 còn tả kiểu cũ thì ghi lỗi tài liệu | P2 |
| K8-10 | Chủ dự án | So mục docs/07 cần kiểm với ADR mới nhất (README trong `docs/quyet-dinh/`) | Không còn bước nhắc dòng trống cuối lưới, chuột phải xoá hàng, lưới MKT/Sale trong CRM. Kèm theo: docs/06 dòng 195, 197 và docs/07 dòng 94–101 (AC-11.18, AC-11.27) còn dùng `mkt.manager` và tả "+100 dòng", nhánh Marketing ▸ Quý ▸ Tháng. docs/07 mục 5 còn trỏ "Hỏng" vào `backlog.md` mục 1 (nay là "Chờ quyết định") và câu hỏi vào mục 5 (nay đã chuyển sang `docs/USER_INQUIRY.md`), xem 6.4. Nếu vẫn còn thì ghi lỗi tài liệu | P2 |

### 6.4 Cách ghi kết quả

| Việc | Quy ước |
|---|---|
| Ghi từng dòng | Mỗi mã (S1, K3-4…) nhận một trong năm kết quả: **Đạt**; **Không đạt**; **Ghi nhận** (lỗ hổng đã biết, gặp lại đúng như mô tả); **Không rõ đúng sai** (máy chạy được nhưng chưa chắc đó có phải hành vi nghiệp vụ mong muốn không); **Bỏ qua** (kèm lý do, ví dụ "thiếu tài khoản Kế toán"). Bỏ qua không có nghĩa là đã kiểm |
| Đầu biên bản | Ngày, nhánh, commit (`git rev-parse --short HEAD`), máy (Windows/Linux), các gói đã chạy. Ghi rõ loại lượt: **Chặng 2 thường** (theo 6.2–6.3) hay **nghiệm thu chính thức theo docs/07** (đợt V4) |
| Ảnh chụp | Dòng Không đạt nào cũng chụp cả trang, có thanh địa chỉ (URL, cổng 8020/8021) và tab DevTools liên quan (Console hoặc Network có mã trả về). Với K3-16 (AC-11.27), chụp lưới đặt cạnh ảnh `docs/tham-khao/kn-demo/` cùng số thứ tự. Chỉ chụp dữ liệu mẫu; không đưa ảnh dữ liệu thật vào kho (quy tắc 6) |
| Bằng chứng thêm | Ghi `X-Request-ID` của request lỗi (header phản hồi) và 20 dòng log quanh thời điểm đó (`logs bangtinh`/`web`) |
| Ghi TL mới (Không đạt) | Thêm vào đầu `docs/test-log.md` theo khuôn hiện có: tiêu đề `## dd.mm.yyyy — Kiểm Staging <commit> …`, mỗi lỗi một khối `**TL-NN (mở) — mức <nhẹ/nặng>, <phân hệ>:**` với các dòng **Lỗi**, **Nguồn** (tệp/hàm nếu biết), **Có từ trước?** (`main` có lỗi này không), **Đề xuất**. Số TL lớn nhất hiện tại là TL-89, nên số kế tiếp là TL-90. `docs/test-log.md` là **nơi duy nhất mô tả lỗi**, với cả hai loại lượt |
| Không rõ đúng sai | Đây là câu hỏi nghiệp vụ, không phải lỗi; không mở TL. Ghi vào `docs/USER_INQUIRY.md`: docs/07 mục 5 bảo ghi vào `backlog.md` mục 5, nhưng mục đó (`docs/backlog.md` dòng 2592) ghi các câu H1–H7 đã chuyển sang `USER_INQUIRY.md` từ 09.09.2026 để tránh lệch hai bản |
| Thống nhất với docs/07 mục 5 | Lượt **Chặng 2 thường**: chỉ ghi theo các dòng trên. Lượt **nghiệm thu chính thức theo docs/07**: vẫn mở TL như trên. Ngoài ra thêm một dòng ngắn vào `backlog.md` mục 1 theo docs/07 mục 5, gồm mã TL, mã AC và tên ảnh; không chép lại mô tả lỗi. Lưu ý: `backlog.md` mục 1 hiện có tên "Chờ quyết định" (1.1 Kỹ thuật, 1.2 Nghiệp vụ, 1.3 Vận hành), không phải danh sách lỗi. Vì vậy docs/07 mục 5 cần chủ dự án sửa lại cho khớp quy ước này (ghi lỗi tài liệu theo K8-10). Mọi ô của docs/07 đều ☑ thì chủ dự án ghi ngày nghiệm thu vào `backlog.md` mục 6 và đóng **V4**, **V5** (bảng 1.3, dòng 2446–2447). Agent không tự đóng V4, V5 |
| Biên bản dài | Lượt kiểm có nhiều phát hiện thì lập `docs/kiem-chung-<việc>-<ngày>.md` (như `kiem-chung-staging-len-main-20261012.md`) và liên kết từ TL |
| Quyết định | Một dòng P0 Không đạt → để lại `Staging`. Chỉ có P1/P2 Không đạt → chủ dự án quyết, ghi rõ quyết định trong biên bản. Dòng "Không rõ đúng sai" ở mã P0 thì chờ câu trả lời nghiệp vụ rồi mới gộp `main` |
