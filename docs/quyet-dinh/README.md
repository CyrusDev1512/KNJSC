# Nhật ký quyết định kiến trúc

Mới 18.09.2026: [ADR-038 — Hoàn thiện báo cáo Marketing: nộp tự do, Tệp khách hàng, Doanh thu suy ra từ vận đơn, Kế toán sửa, Chọn nhanh](038-bao-cao-marketing-hoan-thien.md), thay khoá một bản/ngày của BR-2 và công thức K/J 09.09; ADR-031 có mục bổ sung bảy thị trường.

Mới 18.09.2026: [ADR-037 — Mã nhân sự theo quy ước THUANLT, cố định, là tên đăng nhập của tài khoản mới](037-ma-nhan-su.md), bổ sung ADR-013 và ADR-035.

Mới 18.09.2026: [ADR-036 — Một bảng vận đơn duy nhất "Vận đơn mới" (`van_don`)](036-mot-bang-van-don-duy-nhat.md), thay ADR-029/034 và phần hai bảng của ADR-018; xoá cứng crmThuận và Vận đơn DB theo quyết định chủ dự án.

Mới 18.09.2026: [ADR-035 — Báo cáo tổng hợp theo ngày × nhân sự, cột Leader, 100 dòng mỗi trang](035-bao-cao-tong-hop-theo-ngay-va-nhan-su.md), bổ sung ADR-022.

Mới 18.09.2026: [ADR-034 — Bảng nhận đơn liệt kê mọi bảng vận đơn đang có](034-bang-nhan-don-liet-ke-moi-bang-van-don.md), sửa điều "bảng cũ không làm đích" của ADR-029.

Mới 17.09.2026: [ADR-033 — Nhân viên Vận đơn xem và sửa toàn bảng; nút Tôi / Toàn bộ thay Chế độ xem](033-pham-vi-toi-toan-bo-va-quyen-sua-van-don.md), thay toàn bộ ADR-026.

Mới: [ADR-027 — Lưới chung và vòng đời bảng](027-crm-update-luoi-chung-va-vong-doi-bang.md), đang kiểm local.

- [ADR-028 — Solarpunk Office và chế độ tập trung lưới](028-solarpunk-office.md): duyệt 14.09.2026, đang hợp nhất với CRM-UPDATE.

Mới: [ADR-026 — Chế độ xem Vận đơn mới](026-che-do-xem-van-don.md) (12.09.2026) — đã bị ADR-033 thay thế.

Mới 12.09.2026: [ADR-025 — Trạng thái và chứng từ thanh toán](025-trang-thai-va-chung-tu-thanh-toan.md).

Thư mục này ghi lại các quyết định kỹ thuật quan trọng kèm lý do.

Đang triển khai: [ADR-024 — CRM-Optimization](024-crm-optimization.md), chưa nghiệm thu hiệu năng/chạy bền.

Mới: [ADR-023 — Điều hướng ERP và Lên đơn CRM](023-dieu-huong-erp-va-len-don-crm.md) (11.09.2026).

---

## Vì sao cần

Mã nguồn cho biết **đã làm gì**. Thư mục này cho biết **vì sao không làm cách khác**.

Sáu tháng sau, khi có người hỏi *"sao không dùng thư viện X cho nhanh"*, câu trả lời
nằm ở đây thay vì phải nhớ lại hoặc tranh luận lại từ đầu.

---

## Quy tắc

| # | Quy tắc |
|---|---|
| 1 | **Không sửa mục đã ghi.** Đổi ý thì ghi mục mới, đánh dấu mục cũ là đã được thay thế |
| 2 | Mỗi mục một tệp, đánh số tăng dần |
| 3 | Tên tệp: `số-thứ-tự-mô-tả-ngắn.md`, ví dụ `001-chon-co-so-du-lieu.md` |
| 4 | Ghi ngay khi quyết định, không để sau |

Giá trị của tài liệu này nằm ở chỗ nó cho thấy **suy nghĩ tại thời điểm quyết định**,
không phải ở chỗ nó luôn đúng.

---

## Khi nào cần ghi một quyết định

Ghi khi có ít nhất một trong ba dấu hiệu:

| Dấu hiệu | Ví dụ |
|---|---|
| Khó đảo ngược | Chọn cơ sở dữ liệu, chọn cách tổ chức phân quyền |
| Có nhiều lựa chọn hợp lý | Tự viết hay dùng thư viện có sẵn |
| Sau này sẽ có người hỏi vì sao | Vì sao không dùng công cụ phổ biến hơn |

**Không cần ghi** những quyết định nhỏ, dễ đổi, hoặc chỉ có một cách làm.

---

## Mẫu

Sao chép nội dung dưới đây khi tạo mục mới.

```markdown
# ADR-00x — Tiêu đề ngắn nêu quyết định

| Mục | Nội dung |
|---|---|
| Trạng thái | Đề xuất / Đã áp dụng / Cần xem lại / Đã bị thay thế |
| Ngày | |
| Người quyết định | |
| Thay thế cho | ADR-00y (nếu có) |

## Bối cảnh

Tình huống dẫn tới việc phải quyết định. Nêu ràng buộc và thông tin
đã có tại thời điểm đó.

## Các lựa chọn đã cân nhắc

| Lựa chọn | Ưu | Nhược |
|---|---|---|
| A | | |
| B | | |
| C | | |

## Quyết định

Chọn phương án nào.

## Lý do

Vì sao chọn phương án đó, và vì sao loại các phương án khác.

## Hệ quả

**Được gì:**

**Mất gì:**

**Chỗ cần cẩn thận về sau:**

## Điều kiện xem lại

Trong tình huống nào thì nên xem lại quyết định này.
```

---

## Danh sách quyết định

| Số | Tiêu đề | Trạng thái | Ngày |
|---|---|---|---|
| 001 | Bảng động lưu dạng JSON, cộng cột tách cho nhãn ý nghĩa | Đã áp dụng | (điền) |
| 002 | Không nhúng thư viện bảng tính bên ngoài | Đã áp dụng | (điền) |
| 003 | Cấp bậc và bộ phận là hai cột riêng | Đã áp dụng | (điền) |
| 004 | CRM là module trong monolith, tách thành ứng dụng riêng khi đạt điều kiện | Đã áp dụng | (điền) |
| 005 | Chọn Django làm khung ứng dụng | Đã áp dụng | (điền) |
| 006 | Bảng dữ liệu chỉ có cột tính sẵn, công thức tự do tách sang Bảng tính | Đã áp dụng | 29.08.2026 |
| 007 | Biểu mẫu luôn chọn bảng có sẵn, và chốt bảy nhãn ý nghĩa | Đã áp dụng | 29.08.2026 |
| 008 | Báo cáo hằng ngày bọc quanh biểu mẫu, không tự giữ nội dung | Đã áp dụng | 29.08.2026 |
| 009 | Bảng tính là lưới làm việc của bộ phận Vận đơn, chạy thành dịch vụ riêng | Đã áp dụng | 03.09.2026 |
| 010 | Bảng tính cho mọi bảng, có định dạng ô, cột khoá và thư mục | Đã áp dụng | 04.09.2026 |
| 011 | Bảng tính nhìn và thao tác theo bảng tính KN Demo | Đã áp dụng | 04.09.2026 |
| 012 | KN CRM là app riêng, trang chủ là cây Bộ phận ▸ Quý ▸ Tháng ▸ bảng | Đã áp dụng | 06.09.2026 |
| 013 | Danh sách chọn và màu cột là thuộc tính của cột, Manager quản lý; danh tính người điền do hệ thống ghi | Đã áp dụng | 06.09.2026 |
| 014 | Bảng dữ liệu ở KN ERP chỉ để xem với mọi bảng; sửa số liệu là việc của KN CRM | Đã áp dụng | 06.09.2026 |
| 015 | KN CRM có khung sidebar theo Teeze, trang chủ là tổng quan, Leader như Manager trong bộ phận; tạo bảng, nhập tệp, cấp quyền ngay trong KN CRM | Đã áp dụng | 07.09.2026 |
| 016 | KN CRM chịu được 100 nghìn khách và 100 người cùng lúc: đo trước, sửa đúng chỗ đo được — ô lưới dựng bằng Python, cột Trùng theo trang, `moi-nhat/` không đếm dòng, `bulk_save` bằng VALUES, tính lại cột chạy nền, compose có chế độ gunicorn | Đã áp dụng | 07.09.2026 |
| 017 | Năm tính năng nội bộ (Bảng tin, Tài liệu, Công việc, Văn hoá, Tài nguyên) là năm app riêng, làm MVP trước | Đã áp dụng | 06.09.2026 |
| 018 | Vận đơn mới theo CRM Tân, hai bảng độc lập, chi tiết sản phẩm và tiền thu, thống kê theo bản sao | Đã áp dụng | 08.09.2026 |
| 019 | [Gỡ Lên đơn nhúng khỏi bảng Vận đơn](019-tach-len-don-khoi-bang-van-don.md), giữ trang riêng và thống kê | Đã áp dụng | 09.09.2026 |
| 020 | [Phân công, lọc và xuất Vận đơn mới](020-phan-cong-loc-xuat-van-don-moi.md), phạm vi theo tài khoản và kiểm lại quyền file nền | Đã áp dụng | 09.09.2026 |
| 021 | [Lưới master và Thống kê KN CRM](021-luoi-master-va-thong-ke-crm.md), tải khối/ảo hóa, CAS và biên nhận, biểu đồ riêng | Đã triển khai, kiểm chứng local; xem test-log | 10.09.2026 |
| 022 | [Bàn điều hành KN CRM theo nguồn dữ liệu](022-ban-dieu-hanh-kn-crm.md), tổng hợp Marketing–Sale–Vận đơn và phân tích từng bảng | Đã triển khai và kiểm chứng local; xem test-log | 11.09.2026 |
| 022b | [Báo cáo hoạt động ERP](022-bao-cao-hoat-dong-erp.md) — hai tệp cùng số 022, khôi phục 14.09 | Đã triển khai | 14.09.2026 |
| 023 | [Điều hướng ERP, thư viện hai tab và một nơi lên đơn tại CRM](023-dieu-huong-erp-va-len-don-crm.md) | Đã triển khai | 11.09.2026 |
| 024 | [Tối ưu KN CRM theo số đo](024-crm-optimization.md) — cờ `CRM_OPT_*` | Đang kiểm chứng, cờ tắt | 11.09.2026 |
| 025 | [Trạng thái và chứng từ thanh toán](025-trang-thai-va-chung-tu-thanh-toan.md) | Đã triển khai; kho chứng từ tắt bằng cờ | 12.09.2026 |
| 026 | [Chế độ xem Vận đơn mới](026-che-do-xem-van-don.md) | **Đã bị thay thế** bởi 033 | 12.09.2026 |
| 027 | [Bộ lưới chung và vòng đời bảng CRM](027-crm-update-luoi-chung-va-vong-doi-bang.md) | Đã triển khai | 12.09.2026 |
| 028 | [Solarpunk Office và chế độ tập trung lưới](028-solarpunk-office.md) | Đã áp dụng | 14.09.2026 |
| 029 | [Bảng nhận đơn cấu hình tại CRM](029-bang-nhan-don-crm.md) | Đã triển khai | 15.09.2026 |
| 030 | [Phiên đăng nhập chung ERP/CRM](030-dang-nhap-chung-erp-crm.md) | Đã triển khai | 15.09.2026 |
| 031 | [Loại tiền theo quốc gia và phương thức thanh toán](031-tien-theo-quoc-gia-va-pttt.md) | Đã triển khai | 16.09.2026 |
| 032 | [Ngày hệ thống, sửa báo cáo và mẫu Marketing](032-ngay-he-thong-va-sua-bao-cao.md) | Đã triển khai | 16.09.2026 |
| 033 | [Nhân viên Vận đơn xem và sửa toàn bảng; nút Tôi / Toàn bộ thay Chế độ xem](033-pham-vi-toi-toan-bo-va-quyen-sua-van-don.md) | Đã triển khai VPS 17.09 | 17.09.2026 |
| 034 | [Bảng nhận đơn liệt kê mọi bảng vận đơn đang có](034-bang-nhan-don-liet-ke-moi-bang-van-don.md) | Đã triển khai local | 18.09.2026 |
| 035 | [Báo cáo tổng hợp theo ngày × nhân sự, cột Leader, 100 dòng mỗi trang](035-bao-cao-tong-hop-theo-ngay-va-nhan-su.md) | Đã triển khai local | 18.09.2026 |
| 036 | [Một bảng vận đơn duy nhất "Vận đơn mới" (`van_don`)](036-mot-bang-van-don-duy-nhat.md) — xoá cứng crmThuận, Vận đơn DB; bỏ Bảng nhận đơn | Đã triển khai local | 18.09.2026 |
| 037 | [Mã nhân sự theo quy ước THUANLT, cố định, là tên đăng nhập của tài khoản mới](037-ma-nhan-su.md) | Đã áp dụng local | 18.09.2026 |
| 038 | [Hoàn thiện báo cáo Marketing: nộp tự do, Tệp khách hàng, Doanh thu suy ra, Kế toán sửa, Chọn nhanh](038-bao-cao-marketing-hoan-thien.md) | Đã áp dụng local | 18.09.2026 |

---

## Quyết định đang chờ

Những điểm sẽ cần ghi lại khi chốt. Chi tiết ở `../backlog.md` **mục 0**.

Bốn điểm từng nằm ở đây đều đã chốt và đã có mục quyết định riêng:

| Nội dung cũ | Đã chốt ở |
|---|---|
| ~~Cách triển khai bảng dữ liệu và công thức~~ — K1 | ADR-006, backlog Q11 |
| ~~Tạo biểu mẫu thì tự sinh bảng hay chọn bảng có sẵn~~ — K2 | ADR-007, backlog Q12 |
| ~~Danh sách nhãn ý nghĩa cho cột~~ — K3 | ADR-007, backlog Q13 |
| ~~Khung ứng dụng~~ — K4 | ADR-005, backlog Q7 |

Hiện **không còn điểm nào chờ ghi thành mục quyết định**. Danh sách việc chưa
xong nằm ở `../backlog.md` mục 0.

## Khôi phục quyết định 14.09.2026

- [ADR-022: Báo cáo hoạt động ERP](022-bao-cao-hoat-dong-erp.md).
- [ADR-026: Chế độ xem Vận đơn](026-che-do-xem-van-don.md) — thay thế bởi ADR-033 ngày 17.09.2026.

- [ADR-029 — Bảng nhận đơn CRM](029-bang-nhan-don-crm.md): Admin chọn đích, giữ profile và dữ liệu đơn cũ.
- [ADR-031 — Tiền theo quốc gia và PTTT](031-tien-theo-quoc-gia-va-pttt.md): US/USD, CA/CAD, PH/PHP; xác nhận đổi tiền, chỉ chọn Zelle/PayPal.

- [ADR-032 — Ngày hệ thống và sửa báo cáo](032-ngay-he-thong-va-sua-bao-cao.md): DD/MM/YYYY, quyền sửa có lịch sử, mẫu Marketing và nguồn tiền.
- [ADR-039 — Ẩn cột với cả công ty](039-an-cot-voi-ca-cong-ty.md): quản lý bảng ẩn cột trong hộp "Cột"; cột biến khỏi lưới, tệp Excel và Bảng dữ liệu ERP, dữ liệu vẫn giữ.
- [ADR-040 — Báo cáo tổng hợp như ảnh mẫu](040-bao-cao-tong-hop-nhu-anh-mau.md): tiền quy ₫ ngay trong truy vấn rồi mới cộng (thay "để trống khi lẫn tiền" của ADR-038); cột đối soát (TT) từ vận đơn; nhãn MKT theo ảnh; bố cục khối theo ngày, Gộp, ngưỡng màu, Bảng dữ liệu chi tiết — làm theo đợt.
