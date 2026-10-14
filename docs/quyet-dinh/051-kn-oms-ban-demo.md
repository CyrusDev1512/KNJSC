# ADR-051 — KN OMS: bản demo dữ liệu giả trong KN CRM, chỉ Admin

| Mục | Nội dung |
|---|---|
| Ngày | 13.10.2026 |
| Trạng thái | Xong trên máy ảo 13.10.2026, PR nháp về `Staging`. Chưa gộp, chưa phát hành VPS. Bổ sung cùng ngày: thiết kế lại theo Solarpunk Office và làm sâu sáu màn (mục cuối), PR nháp riêng |
| Thay thế / bổ sung | Không thay ADR nào. Không đổi phạm vi giai đoạn 1: kho, công nợ, khách rủi ro, lãi theo page vẫn chưa làm thật; câu hỏi H7 (ai ghi nhận tiền) vẫn mở |

## Bối cảnh

Chủ dự án 13.10.2026 đã xem [mockup tương tác](https://claude.ai/artifact/PtHzbv73q4kdaQrJSijEWk) gồm Báo đơn, Kho,
Kênh bán & Page. Sau đó chủ dự án xem danh sách đề xuất tính năng cùng hệ sinh thái. Ba đề xuất được chọn:

1. Công nợ & đối soát tiền.
2. Cảnh báo khách rủi ro khi lên đơn.
3. Lãi thật theo page và sản phẩm.

Yêu cầu nguyên văn: "mockup + 1 2 3 làm sang một site khác từ KN CRM có thể mở KN OMS để có mockup + 1 2 3".

Mockup lúc đó chỉ là một trang artifact, chưa nằm trong hệ thống. Chủ dự án chốt ba câu hỏi:

| Câu hỏi | Chốt |
|---|---|
| KN OMS chạy ở đâu | Đường dẫn riêng `/oms/` trong KN CRM (cổng 8021), có khung và tên riêng. Không thêm container, không thêm tên miền |
| Ai thấy | Chỉ Admin. Mục "KN OMS" ở thanh bên KN CRM mở tab mới. Vai khác gọi thẳng đường dẫn thì nhận 403 và có nhật ký từ chối |
| Dữ liệu | Toàn bộ giả, sinh ngay trong trình duyệt. Không đọc, không ghi bảng Vận đơn; không model, không migration |

## Quyết định

1. **Một view, một đường dẫn, chỉ ở KN CRM.**
   - View `crm/oms_views.kn_oms` chạy theo thứ tự:
     - `@login_required`, `@require_GET`;
     - `assert_admin`: không phải Admin thì 403 và một dòng nhật ký `DENIED`, đích `path` `/oms/`;
     - render `crm/kn_oms.html`, không truy vấn dữ liệu nghiệp vụ.
   - Đường dẫn khai ở `crm/urls.py`: `path("oms/", …, name="kn_oms")`.
     - Chỉ có ở URLconf KN CRM `knjsc.urls_bangtinh`; KN ERP trả 404.
     - Lý do: AC-1.12 cấm một đường dẫn nằm ở cả hai dịch vụ.
   - Mục ở thanh bên khai trong `crm/navigation.py`, đứng cuối sau Nhật ký.
     - Điều kiện `is_admin`, giống hệt view.
     - `new_tab=True`: `target="_blank" rel="noopener"`, title "Mở trong tab mới".
2. **Trang đứng riêng, không kế thừa khung KN CRM.** (Bổ sung 13.10: nay nạp CSS và dùng markup khung của KN CRM, xem mục cuối.)
   - `templates/crm/kn_oms.html` không `extends`. Trang có:
     - thanh bên KN OMS, ba nhóm: Đơn hàng · Hàng hoá · Kinh doanh;
     - dải "Dữ liệu giả";
     - ba nút "← Về KN CRM", "Đổi nền", "Đặt lại demo".
   - Hai tệp tĩnh, JS thuần, không thư viện (ADR-005):
     - `static/css/oms.css`: CSS của mockup, bỏ khối `prefers-color-scheme`;
     - `static/js/oms.js`: một IIFE.
   - **Nền** dùng chung khoá `localStorage["knjsc-nen"]` với KN CRM.
     - Đổi ở KN OMS thì KN CRM theo khi tải lại.
     - Đổi ở KN CRM thì KN OMS theo ngay, qua sự kiện `storage`.
   - **Địa chỉ:** mỗi màn một địa chỉ riêng, nút Lùi của trình duyệt dùng được:
     `#bao-don`, `#cong-no`, `#khach-rui-ro`, `#kho`, `#kenh-ban`, `#lai-theo-page`.
   - **Soát lớp CSS:** `core/tests/test_giao_dien.py` soát template này theo đúng `oms.css`, qua bảng `CSS_RIENG`.
     `oms.css` không vào bộ CSS dùng chung `CAC_TEP_CSS`. Vào đó thì lớp của trang này "khai hộ" cho mọi template khác.
3. **Dữ liệu giả cố định.**
   - Dữ liệu sinh từ hạt giống (mulberry32).
     - Dòng số chính giữ đúng thứ tự gọi của mockup, nên Báo đơn, Kho, Kênh ra y như mockup.
     - Ba màn mới dùng ba dòng số riêng, nên không làm lệch dữ liệu cũ.
   - "Đặt lại demo" và tải lại trang đều sinh lại đúng bộ dữ liệu ban đầu.
   - Không lưu gì ở máy chủ. Trình duyệt chỉ nhớ lựa chọn nền.
   - Ba khách mẫu cố định: KH-90001, KH-90002, KH-90003. SĐT của họ thuộc dải 555-01xx, dải số giả quy ước của Bắc Mỹ,
     không thuộc ai.
   - Thêm 10 đơn page cũ, giao 16–58 ngày trước, để bốn nhóm tuổi nợ đều có dữ liệu.
4. **Ba màn mới.** Ngưỡng, phí sàn, giá vốn, cước và tiền quảng cáo đều là số minh hoạ, chưa chốt.
   - **Công nợ & đối soát.**
     - Chỉ đơn page Facebook đã giao mới là tiền phải thu.
     - Đơn sàn do sàn thu hộ, theo dõi riêng ở "Tiền sàn chờ về". Đơn website trả trước.
     - Dùng đúng 3 nhãn thanh toán, 7 PTTT và nhãn "Đã về TK" của bảng Vận đơn (`orders/constants.py`).
     - Mọi tổng tách theo loại tiền, không quy ₫.
     - Khớp tiền về: theo mã đơn, theo tên người gửi, khách trả một phần, hoặc chọn tay khi không khớp đơn nào.
     - Màn ghi rõ: ai ghi nhận tiền, ai xác nhận "Đã về TK" chưa chốt (H7).
   - **Khách rủi ro.**
     - Gõ SĐT là ra mức Thấp, Cần chú ý hoặc Cao, kèm lý do và việc nên làm.
     - Luật chấm điểm hiện ngay trên màn, ở khối "Cách tính".
     - SĐT vẫn che ở mọi bảng.
   - **Lãi theo page.**
     - Lãi = doanh số đơn đã giao − phí sàn − giá vốn − cước − quảng cáo − chi phí hoàn.
     - Ba cách xem: theo page, theo sản phẩm (lãi gộp, chưa trừ quảng cáo), theo thị trường. Hai kỳ: 7 và 30 ngày.
     - Quảng cáo tính bằng tiền Việt như báo cáo Marketing (ADR-047), tỉ lệ với doanh số từng page (ROAS khoảng 3–10).
     - Cố ý cho hai page lỗ: KN Beauty Japan và KN Beauty LazMall.
5. **Tỉ giá chỉ ở màn Lãi, chỉ để minh hoạ.**
   - Doanh số ngoại tệ quy VND theo bảng "Tỉ giá tạm (chỉ để minh hoạ)".
     - Bảng sửa được ngay trên màn, khởi đầu bằng `settings.EXCHANGE_RATES_VND`.
     - KRW để trống như settings, nên page Hàn báo "Thiếu tỉ giá KRW".
   - Không trái AGENTS.md §4 (không quy đổi tự động trên dữ liệu thật): đây là số giả, chỉ nằm trong trình duyệt.
   - Bản thật cần một nguồn tỉ giá được duyệt.
6. **An toàn.**
   - Tệp ở `/static/` ai cũng tải được, vì nginx phục vụ công khai. Hai tệp này chỉ chứa mã giao diện và dữ liệu giả,
     không có số liệu thật hay khoá bí mật.
   - Trang không gọi `fetch` hay XHR:
     - AC-51.1 soát mã nguồn;
     - AC-51.5 soát request thật trong trình duyệt.

## Hệ quả

- Admin mở KN OMS từ KN CRM để trình bày. Dữ liệu thật không bị đụng.
- Không thêm model, migration, settings, container hay cấu hình nginx. Phát hành VPS chỉ cần `collectstatic` như mọi lần.
- **Gỡ bỏ:** xoá các phần sau.
  - Mã: mục trong `crm/navigation.py`, đường dẫn trong `crm/urls.py`, `crm/oms_views.py`.
  - Giao diện: `templates/crm/kn_oms.html`, `static/css/oms.css`, `static/js/oms.js`.
  - Kiểm thử: mục `CSS_RIENG`, hai tệp bài kiểm.
  - Tài liệu: mục 51 ở docs/04.
- **Làm thật** bất kỳ màn nào cũng cần ADR riêng, nói rõ:
  - model và quyền;
  - nguồn dữ liệu: Pancake, hãng vận chuyển, ngân hàng, sàn;
  - lời đáp H7.
- **Bộ đếm và bài kiểm:**
  - Bộ đếm: AC-51.1 → AC-51.8.
  - Bài kiểm: `crm/tests/test_kn_oms.py`, `tests/e2e/test_kn_oms_e2e.py`.
  - Biên bản: `docs/kiem-chung-kn-oms-demo-20261013.md`.

## Bổ sung 13.10.2026 — thiết kế lại theo Solarpunk Office, làm sâu sáu màn (AC-51.9 → 51.14)

Chủ dự án: "dùng impeccable để design lại UI, sau đó nâng cấp tính năng". Chủ dự án chốt bốn câu hỏi:

| Câu hỏi | Chốt |
|---|---|
| Phạm vi | Chỉ KN OMS. KN CRM và KN ERP giữ nguyên |
| Diện mạo | Theo Solarpunk Office như KN CRM (ADR-028) |
| Tính năng | Làm sâu sáu màn đang có |
| Dữ liệu | Vẫn dữ liệu giả; mục 3 và 6 ở trên giữ nguyên |

Impeccable dùng đúng cách dự án cho phép: chỉ hướng dẫn thủ công (`operate`, `craft-floor`), không chạy engine, hook hay
agent. Hồ sơ mặt ở `.agents/design-state/surfaces/app-templates-crm-kn-oms-html.md`.

1. **Mượn nguyên diện mạo KN CRM, không chép giá trị.**
   - `kn_oms.html` nạp đúng bốn tệp của `crm/base_crm.html`, cùng thứ tự: `tokens.css`, `main.css`, `crm-frame.css`,
     `solarpunk.css`. Sau cùng mới tới `oms.css`.
   - `oms.css` bỏ bảng màu chép tay. Chỉ còn biến KN CRM chưa có: màu thông tin, màu năm nền tảng, chữ trên nền đậm,
     lớp phủ. Đổi màu ở `solarpunk.css` thì KN OMS đổi theo.
   - Khung theo markup KN CRM: `body.sp-crm`, thanh bên kính `crm-nav`, thanh trên có đường dẫn, mặt đọc `noi-dung`,
     ảnh nền `solarpunk-office.webp`. Thanh bên là sáu màn OMS, không phải thanh bên KN CRM (`#thanh-ben` vẫn không có).
   - Thành phần chung dùng kiểu KN CRM: `.nut`, `.o-nhap`, `.truong`, `.loc`, `.the`, `.bang-hop`, `table.bang`,
     `.chip`, `.bao`, `.phan-trang`. Lớp riêng của OMS mà trùng tên với lớp chung thì đổi sang tiền tố `oms-`
     (vd `.mo` của KN CRM là "thanh bên đang mở").
   - `CSS_RIENG` của bài soát lớp nay là danh sách năm tệp trang này nạp.
2. **Sửa sáu lỗi của bản đầu** (rà theo `craft-floor`):
   - dải "DEMO" thành nhãn "Dữ liệu giả" trên thanh trên;
   - 22 ô KPI số to ở năm màn thành một dải phẳng ngăn vạch mảnh như trang chủ KN CRM, vẫn bấm để lọc;
   - đoạn giới thiệu 182–290 ký tự thành một câu; phần giải thích dài vào khối "Cách tính";
   - bỏ viền trái 3–4 px ở thẻ rủi ro và khoản tiền về;
   - Ghi nhận tiền, Phiếu kho, Thêm kênh rời hộp thoại, vào ngăn kéo bên phải;
   - bảng trống chỉ cách gỡ lọc; chữ phụ trên nền đang chọn đủ tương phản 4,5:1.
3. **Làm sâu sáu màn**, vẫn sinh trong trình duyệt:
   - **Báo đơn:** lọc ngày lên đơn (Hôm nay, 7, 30 ngày, Tất cả; ô Từ–Đến DD/MM/YYYY qua `date-inputs.js` dùng chung).
     "Xuất danh sách" ra CSV các dòng đang lọc.
   - **Công nợ:** lọc ngày giao; chọn nhiều đơn rồi "Nhắc N đơn", "Xuất N đơn"; xuất danh sách.
   - **CSV:** cho Excel tiếng Việt. UTF-8 có BOM, phân cách `;`, CRLF. Tiền một cột kèm cột loại tiền. Ô mở đầu bằng
     `= + - @` hay dãy số từ 12 chữ số có dấu `'`. Tạo bằng Blob, không gọi máy chủ.
   - **Khách rủi ro:** ngăn kéo khách có dòng thời gian gộp mọi đơn và mọi lần đánh dấu. Chặn lên đơn phải ghi lý do.
   - **Kho:** đủ bán và gợi ý nhập đủ 30 ngày, theo số xuất cho đơn 7 ngày, tính riêng từng kho. Phiếu kho điền sẵn.
   - **Kênh:** thẻ so với 7 ngày trước. Biểu đồ 14 ngày dừng được bằng Tab, có bảng số đối chiếu.
   - **Lãi theo page:** biểu đồ lãi theo ngày (khuôn SVG của màn Thống kê, thêm đường 0), chọn page, phím mũi tên, bảng
     số. Ô Lãi của kỳ bằng đúng tổng các ngày.
4. **"7 ngày" là 7 ngày lịch giờ Việt Nam** (hôm nay và 6 ngày trước) ở Báo đơn, Kênh và kỳ của Lãi theo page. Trước đây
   Kênh và Lãi tính lùi 7 × 24 giờ từ lúc mở trang. Đổi để số đơn của thẻ kênh khớp chip "7 ngày" ở Báo đơn, và để lãi
   từng ngày cộng lại đúng bằng lãi cả kỳ. Tốc độ xuất ở Kho vẫn là 7 × 24 giờ.
5. **Dữ liệu giả thêm một chỗ cố ý:** mã xuất cho đơn nhiều nhất 7 ngày qua (trừ ba chỗ thiếu, sắp hết đã có và hàng
   đang về) chỉ còn khoảng 5 ngày bán, để Kho có gợi ý nhập thật. Không rút số ngẫu nhiên nên dữ liệu khác không lệch.
6. **Bộ đếm:** AC-51.9 → 51.14. Biên bản: `docs/kiem-chung-kn-oms-thiet-ke-lai-20261013.md`.
