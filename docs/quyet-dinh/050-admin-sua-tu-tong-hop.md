# ADR-050 — Admin sửa lần nộp ngay trên Báo cáo tổng hợp

| Mục | Nội dung |
|---|---|
| Ngày | 10.10.2026 |
| Trạng thái | Kiểm kỹ xong 10.10.2026, chủ dự án bảo gộp vào `Staging`; sau đó thử local rồi mới gộp `main` |
| Thay thế / bổ sung | Bổ sung ADR-032 (luồng Sửa báo cáo có lịch sử) và ADR-042 (Báo cáo tổng hợp): thêm một lối vào luồng sửa đó ngay trên bảng. Không đổi quyền sửa |

## Bối cảnh

Chủ dự án 10.10.2026: "tôi muốn quản trị có chức năng khi vào báo cáo tổng hợp có thể sửa dữ liệu". Hiện trạng lúc đó:

- **Sửa báo cáo đã nộp** đi một đường duy nhất (ADR-032, BR-2): Lịch sử báo cáo → mở báo cáo → Sửa báo cáo → Lưu → về
  trang báo cáo. `daily_service.amend` kiểm quyền (`can_amend`: Admin, Kế toán, Manager bộ phận, Leader team), so phiên
  bản (409 khi bản đã cũ), ghi `ReportRevision` và nhật ký.
- **Báo cáo tổng hợp** của nguồn Sale/MKT luôn ở chế độ Từng lần nộp: mỗi dòng ở khối ngày (và ở khối Gộp) là đúng một
  lần nộp. Khối Toàn kỳ, dòng TỔNG CỘNG và nguồn Vận đơn là số gộp.
- **Bảng dữ liệu** dùng chung bảng khối với Báo cáo tổng hợp nhưng chỉ để xem (ADR-014).

Chủ dự án xem mockup tương tác rồi chốt:
- chỉ Admin thấy nút sửa;
- sửa trong một hộp mở đè lên bảng, lưu xong bảng đổi tại chỗ;
- dòng Toàn kỳ, TỔNG CỘNG, Vận đơn giữ nguyên, không thêm gì.

Mockup: https://claude.ai/artifact/AiyWUW9ycAGuRsdniXRWnN

## Quyết định

1. **Nút ✎ ở ô đầu mỗi dòng lần nộp, chỉ Admin thấy.**
   - Cờ `sua_bao_cao` chỉ đặt ở `reports/activity_views.report`, là `is_admin(user)` và nguồn sale/mkt.
   - Bảng dữ liệu không đặt cờ này, nên không bao giờ có nút (ADR-014).
   - Câu truy vấn số liệu không đổi. `layout._gan_lan_nop` gắn id dòng số liệu và số Lần cho dòng khối ngày và khối Gộp.
     Khối Toàn kỳ, TỔNG CỘNG, Vận đơn không gọi hàm này, nên không có nút.
   - Khi có cờ, `daily_service.attach_report_ids` tra id báo cáo ngày bằng **một truy vấn** theo đúng các dòng đang hiện,
     qua phạm vi quyền.
     - Kiểm kỹ trước khi gộp đã đo: LEFT JOIN trong câu số liệu làm chậm mọi người dùng thêm 4,7 → 21,8 ms (DB 2.400 lần
       nộp), vì phép nối chạy trên cả kỳ.
     - Tra theo dòng của trang thì Admin chỉ thêm một truy vấn nhỏ, còn vai khác và Bảng dữ liệu không đổi gì.
   - Mỗi dòng không dựng URL và SVG riêng. Dòng mang `data-lan-nop`, nút mang `data-lan`. URL ghép ở `report-sua.js` từ mẫu
     `data-sua-mau` của hộp; biểu tượng là `#report-but-sua`, khai một lần.
2. **Hộp sửa dùng đúng luồng Sửa báo cáo**, chế độ `?khung=1` của `bao_cao_sua`.
   - Quyền vẫn là `can_amend`, việc ghi vẫn là `amend` (so phiên bản, lịch sử, nhật ký).
   - Chỉ Admin thấy nút. Leader, Manager, Kế toán vẫn sửa qua Lịch sử báo cáo như cũ.
   - Mở hộp: trả phần form `_bao_cao_sua_hop.html`, gồm ô sửa và Xem trước chỉ số (include chung với trang Sửa báo cáo
     và form Nộp báo cáo) cùng danh sách lịch sử sửa (`daily_service.revision_changes`, 50 lần gần nhất). Nút ghi tổng
     số lần sửa.
   - "Lần N" ở đầu hộp lấy từ `lan` trên URL, tức đúng số của dòng bảng vừa bấm, nên không lệch với bảng khi bảng đang lọc
     hay có dòng nhập ngoài form.
   - Lưu được: 204, `X-Bao-Cao-Doi: 0|1` (`amend` gắn `da_doi`).
   - Thiếu ô bắt buộc: 400 kèm phần form.
   - **409:** trả phần form đã nạp số mới nhất và phiên bản mới. Câu báo (`conflict_note`) nêu mã người vừa sửa và giờ
     sửa. Điều kiện: lần ghi cuối của dòng phải chính là một lần sửa; dòng đổi theo đường khác thì dùng câu chung, không đổ
     cho người sửa từ trước.
     - Ô khác với số lúc mở hộp (ô ẩn `goc-…`) tô vàng.
     - Số vừa gõ chưa lưu thì bỏ: Admin xem lại rồi mới Lưu, không ghi đè ngầm (bắt buộc 13).
3. **Trình duyệt** (`static/js/report-sua.js`, chỉ nạp khi có cờ):
   - Lưu bằng fetch.
     - Đang gửi thì khoá Lưu, ✕ và Huỷ, và Escape không đóng hộp, để kết quả luôn có chỗ hiện.
     - Quá 30 giây không trả lời thì thôi chờ, báo trong hộp.
     - Kết quả của lượt lưu cũ không đụng vào hộp của lần mở sau.
   - Lưu xong phát `knjsc:bao-cao-da-sua`. `report-filters.js` thay bảng tại chỗ bằng đường Gộp / Không gộp đang có, giữ
     lọc, trang, ngày đang xem và vị trí kéo ngang; dòng vừa sửa sáng vàng vài giây.
   - Lỗi mạng, 5xx, 403 (phiên hay quyền đổi, kể cả CSRF), 404 (báo cáo vừa bị bỏ), hết phiên: báo đúng lý do trong hộp,
     giữ số đã gõ, không báo "Đã lưu".
   - Escape chỉ đóng hộp: chặn ở chính hộp, pha nổi bọt, không chặn toàn cửa sổ.
   - `report-entry.js` gắn ô số và Xem trước chỉ số theo vùng (`gan(vung)`, sự kiện `knjsc:form-moi`).
4. **Không đổi:**
   - quyền sửa;
   - ngày, nhân sự, team, giờ nộp bất biến (ADR-032, ADR-043);
   - Bảng dữ liệu chỉ để xem (ADR-014);
   - không sửa ô tại chỗ trên bảng, không có lưới thứ hai (ADR-021).

## Hệ quả

- Admin sửa số của một lần nộp mà không rời Báo cáo tổng hợp. Mọi lần sửa vẫn có lịch sử và nhật ký như sửa qua trang.
- Trang Sửa báo cáo cũng có Xem trước chỉ số, vì dùng chung phần ô sửa với hộp.
- Bộ đếm: AC-50.1 → AC-50.11.
- Bài kiểm ở `reports/tests/test_admin_sua_tong_hop.py` và `reports/tests/test_admin_sua_tong_hop_e2e.py`.
- Biên bản: `docs/kiem-chung-admin-sua-bao-cao-20261010.md`.
