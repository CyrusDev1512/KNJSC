# ADR-051 — KN OMS: bản demo dữ liệu giả trong KN CRM, chỉ Admin

| Mục | Nội dung |
|---|---|
| Ngày | 13.10.2026 |
| Trạng thái | Xong trên máy ảo 13.10.2026, PR nháp về `Staging`. Chưa gộp, chưa phát hành VPS |
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
2. **Trang đứng riêng, không kế thừa khung KN CRM.**
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
