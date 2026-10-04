# ADR-047 — Báo cáo Marketing nộp bằng tiền Việt

| Mục | Nội dung |
|---|---|
| Ngày | 03.10.2026 |
| Trạng thái | Đã gộp `Staging` (#83) và `main` (#87); bổ sung 04.10.2026 (Sale ẩn cột Lần nộp) ở PR nháp về `Staging` |
| Thay thế / bổ sung | Bổ sung ADR-046 (không quy đổi — vẫn giữ); thay phần "Loại tiền tự theo Thị trường" của ADR-031 **cho báo cáo Marketing**; ADR-038 phần DS Chốt (TT) |

## Bối cảnh

Chủ quản yêu cầu (02.10.2026): **tất cả số trong báo cáo được nộp đều là tiền Việt**. Chủ dự án 03.10.2026: "cái bảng
báo cáo tổng hợp hiện tại đổi sang VND"; "tôi chưa từng duyệt bất cứ thông tin nào về tỉ giá, bỏ qua"; "làm
marketing trước"; duyệt mockup "Cách A".

Dữ liệu cho thấy nhân viên **vốn đã gõ số tiền Việt**: vụ 28.09 (ADR-046) CPQC 13.250.000 bị gắn CAD vì Loại tiền tự
theo Thị trường; dữ liệu mẫu MKT có CPQC 438.446.060 mang nhãn CAD. Nhãn sai, số đúng.

## Quyết định

1. **Một chỗ quyết định loại tiền của báo cáo ngày**: `orders.services.currency_service.report_currency(kind,
   market)` và `REPORT_CURRENCY = {"mkt": "VND"}`. Marketing luôn VND, không theo Thị trường; Sale vẫn theo Thị
   trường. Nộp (`daily_service.protected_values`), nhập bảng (`record_service.report_input_values`), đổi Thị trường
   trên dòng (`record_service._dat_o`) và form (bản đồ Thị trường → Loại tiền) cùng gọi hàm này.
2. **Form Nộp báo cáo MKT:** ô Loại tiền luôn "VND"; ô tiền ghi "(₫)" (CPQC, Doanh số); xem trước chỉ số hiện VND.
3. **Báo cáo cũ đổi nhãn sang VND, số giữ nguyên** — tệp chuyển đổi `reports/0006_bao_cao_mkt_tien_viet`: mọi dòng
   của nguồn `kind="mkt"` (kể cả dòng đã bỏ) mang Loại tiền VND; cột Loại tiền có lựa chọn VND. Chạy ngược: nhãn lấy
   lại theo Thị trường như trước (ADR-031). Bảng Sale không đụng.
4. **Không tỉ giá ở bất cứ đâu.**
5. **(TT) đối soát của báo cáo MKT không khoá theo loại tiền**: Số đơn (TT) đếm đơn mọi loại tiền của marketer vào dòng
   VND của người đó (`activity_service.build` → `by_currency=False`). **DS Chốt (TT)** (tiền khách trả trên vận đơn,
   bằng USD/CAD…) **để trống "—"** vì không quy đổi; Dòng TỔNG CỘNG · VND nhận đủ
   phần đối soát (`aggregations.with_currency_totals`: một loại tiền thì cả đối soát thuộc loại tiền đó).
6. Báo cáo tổng hợp MKT chỉ còn **một dòng TỔNG CỘNG · VND**; ngưỡng tiền (CPO, Giá Mess, AOV) đặt theo ₫ nay tô được
   dòng MKT.
7. **Ẩn hai cột Hóa đơn và Hóa đơn/DS Chốt (TT)** khỏi báo cáo MKT (màn hình, Excel, Tổng quan — `DISPLAY_ORDER`);
   cột dữ liệu Hóa đơn trong bảng giữ nguyên (chủ dự án 03.10.2026).

8. Sửa kèm lỗi giật bảng khi kéo ngang tới sát mép phải (`report-filters.js`, sai số đích nhích 2 px): lộ ra khi bảng
   MKT bớt hai cột.

9. **Ẩn hai cột Lần nộp và Loại tiền** khỏi báo cáo MKT (màn hình, Bảng dữ liệu, Excel) — một chỗ
   `layout.HIDDEN_IDENTITY`, `ActivityResult.source_kind`; chỉ đổi hiển thị, không đổi cách cộng tổng; Sale giữ
   (chủ dự án 03.10.2026). Từ 04.10.2026 Sale ẩn cột Lần nộp, giữ Loại tiền — xem bổ sung dưới.

## Bổ sung 04.10.2026 — báo cáo Sale ẩn cột Lần nộp

Chủ dự án thử Staging 04.10.2026, nhìn báo cáo Sale: "tôi nhớ là cái lần nộp này đã bỏ rồi mà"; được hỏi lại thì chọn
**bỏ cột Lần nộp ở Sale**. `layout.HIDDEN_IDENTITY` thêm `"sale": ("lan",)`: cột Lần nộp rời màn hình, Bảng dữ liệu
dạng báo cáo và Excel của báo cáo Sale, ở khối toàn kỳ, khối ngày và khối Gộp. **Sale giữ cột Loại tiền**, vì một người
nộp được nhiều loại tiền (Canada CAD, Hoa Kỳ USD…) và không cộng lẫn tiền tệ (ADR-046). Hai lần nộp cùng ngày vẫn là
hai dòng; chỉ đổi hiển thị, không đổi cách cộng tổng. AC-47.7.

## Hệ quả

- Sale giữ cơ chế nhiều loại tiền của ADR-046 (mỗi dòng một loại tiền, TỔNG CỘNG theo loại tiền).
- DS Chốt (TT) của báo cáo MKT trống cho tới khi chủ dự án duyệt một cách quy đổi tiền vận đơn (tỉ giá); trên VPS cột này
  vốn đang "—" (chủ dự án 03.10.2026) nên không mất số đang dùng.
- Bài kiểm ADR-038/042/046 dùng nguồn MKT viết lại theo luật mới; bài cơ chế nhiều loại tiền ghi nhãn thẳng vào dòng để
  vẫn kiểm cơ chế dùng cho Sale.

## Việc để lại

- Báo cáo Sale bằng tiền Việt — chủ dự án nói làm Marketing trước.
- DS Chốt (TT) bằng VND — cần tỉ giá được duyệt.
