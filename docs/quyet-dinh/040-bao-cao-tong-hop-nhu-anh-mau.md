# ADR-040 — Báo cáo tổng hợp như ảnh mẫu: quy ₫ trước khi cộng, cột đối soát (TT), bố cục khối theo ngày, ngưỡng màu

| Mục | Nội dung |
|---|---|
| Ngày | 23.09.2026 (đợt 1); các đợt sau bổ sung ngay trong tệp này |
| Trạng thái | Đang làm theo đợt — đợt 1 và 2 xong local |
| Thay thế / bổ sung | **ADR-038** quyết định "lẫn loại tiền thì cảnh báo và để trống chỉ tiêu tiền" (bỏ); **ADR-031** câu "không quy đổi tỉ giá" chỉ còn đúng cho **lưu trữ**; **ADR-035** bố cục Tổng hợp (bổ sung đợt 2) |

## Bối cảnh

Chủ dự án gửi ảnh một hệ thống khác (LUMI OMS, tab "Báo cáo chi tiết") và chốt 23.09.2026:
Báo cáo tổng hợp là màn hình **đối tác thích nhất**, phải **giữ mọi chức năng đang có** và nâng
cấp cho **giống ảnh, toàn diện nhất có thể**; Bảng dữ liệu cập nhật theo sau. Ảnh có gì mà ta chưa
có: mọi tiền là **₫**; cặp cột **"(TT)"** (Số Đơn (TT), DS Chốt (TT), Tỉ lệ chốt (TT)) luôn nhỏ hơn
hoặc bằng cột thường; bảng đầu là **toàn kỳ theo từng người**, rồi **mỗi ngày một bảng riêng** có
TỔNG CỘNG đứng ngay dưới tiêu đề, STT đếm lại, cột Team, **không có cột Ngày**; ba cột chỉ số có nền
tiêu đề riêng và ô tô **xanh / vàng / đỏ** theo ngưỡng cố định; bộ lọc Sản phẩm **tick nhiều mục**.

Chỗ đối tác thấy sai trước tiên: dữ liệu thật lẫn USD/EUR/CAD/VND nên `currency_safe_result`
(ADR-038) **để trống mọi cột tiền** — CPQC, DS Chốt, CPO, Giá Mess đều "—" trong khi Bảng dữ liệu
(tính từng dòng, một loại tiền một dòng) vẫn hiện số. Chủ dự án không chấp nhận cách "để trống".

## Quyết định

1. **Quy về ₫ ngay trong truy vấn rồi mới cộng** (đợt 1). `aggregations.summarize(currency_code=…)`
   gắn `_ti_gia = Case/When` theo loại tiền **từng dòng** (`core.money.vnd_rate_expression`, tỉ giá
   `settings.EXCHANGE_RATES_VND`) và mọi cột kiểu **Tiền** cộng `giá trị × _ti_gia`; cột Số nguyên /
   Số thập phân giữ nguyên. SUM kết hợp được nên tổng nhóm, tổng ngày, tổng bộ lọc cùng một số. BR-8
   vẫn giữ: Decimal, quy đổi rồi mới cộng, **không bao giờ cộng lẫn**. Dòng thiếu tỉ giá (KRW) hoặc
   trống loại tiền: tiền **không vào tổng**, cột đếm vẫn tính, cảnh báo nêu số dòng và loại tiền
   thiếu (`currency_note`). Nguồn không ánh xạ cột Loại tiền cộng thô như trước. Tiền suy ra từ vận
   đơn quy ₫ trong Python bằng `core.money.to_vnd` (dời từ `culture.leaderboard_service`, Q71).
   Lưu trữ không đổi (ADR-031): quy đổi là việc của lúc lập báo cáo.
2. **Cột đối soát "(TT)" của BC MKT** (đợt 1) — chủ dự án chốt TT = đối soát từ vận đơn:
   **Số đơn (TT)** = số vận đơn có Phụ trách Marketing là marketer, theo ngày lên đơn, cùng bộ lọc
   sản phẩm/quốc gia, **kể cả đơn không có chi tiết sản phẩm** (ADR-036); **DS Chốt (TT)** = tiền đã
   thu (`WaybillItem.paid_amount`, chính là "Doanh thu suy ra" của ADR-038) quy ₫ — đơn không chi tiết
   không góp tiền, `so_tien_tt` gõ tay của nó **chưa** tính (xem Giới hạn); **Tỉ lệ chốt (TT)** =
   Số đơn (TT) ÷ Số Mess. `marketing_actuals` là **một truy vấn trên `DataRecord` vận đơn** (đếm
   trên đơn, không trên chi tiết), thay `marketing_revenue`. Không có đơn thì Số đơn (TT) là **0**.
3. **Nhãn BC MKT theo ảnh**: "DS Chốt" (số marketer khai), "DS Chốt (TT)", "Số đơn (TT)", "Tỉ lệ
   chốt (TT)", "CPQC/DS Chốt", "Hóa đơn/DS Chốt (TT)". Sale giữ "Doanh số"/"Doanh thu" vì Doanh thu
   của Sale là cột nhập. **Tỉ lệ chốt** vào BC MKT (trước chỉ Sale có) và **hiện theo %** (6,18 %)
   ở cả hai nguồn, Excel ghi cùng số %. Chỉ số quan trọng và chiều tốt khoá theo **mã chỉ tiêu**
   (`reports/constants.py`), đường cũ `marketing.adapt` suy mã từ nhãn.
4. **Toàn bộ dòng nhóm vào bộ nhớ khi ≤ 2.000** (`summarize_in_memory`): tổng, khoá đối soát,
   tổng ngày, khối toàn kỳ và phân trang dùng chung một danh sách — bỏ được lệnh aggregate và lệnh tra
   khoá; nguồn MKT thật từ 12 xuống dưới 10 truy vấn (AC-40.4). Quá trần thì giữ queryset như cũ.
5. **Bố cục khối như ảnh** (đợt 2, `reports/layout.py` + `reports/_bang_khoi.html`): khối **toàn kỳ
   theo nhân sự** đứng đầu — cộng trong bộ nhớ từ các dòng ngày × người, cột STT · Team · Nhân sự ·
   Leader, TỔNG CỘNG ngay dưới hàng tiêu đề cột, sắp theo mã; rồi **mỗi ngày một bảng riêng** mới nhất
   trước, tiêu đề ngày đặt trên bảng, **không cột Ngày**, TỔNG CỘNG ngày bằng tổng dòng con (cột tính
   tính lại từ tổng), STT đếm lại từ 1; nhiều bảng trong **một** khung cuộn (thead và TỔNG CỘNG dính
   trong bảng của nó). Phân trang vẫn 100 dòng người; ngày bị tách trang ghi "(tiếp)" và lặp TỔNG
   CỘNG đủ cả ngày. Nút **Gộp / Không gộp** (`gop=1`): Gộp = mỗi ngày chỉ còn dòng TỔNG CỘNG, phân
   trang theo ngày — chính là bố cục trước 19.09. Excel hai sheet "Toan ky theo nhan su" và "Theo
   ngay" cùng khối, số thô. Các cách xem khác vẫn một bảng, cột định danh như ADR-035.
6. **Ngưỡng màu tuyệt đối ba bậc** — đợt 3: `ReportSource.thresholds` do Manager bộ phận sở hữu
   đặt; chưa đặt thì giữ cách tương đối ±10 % (AC-22.16); không bịa số mặc định. Lọc **nhiều sản
   phẩm** và mốc "Tuần này".
7. **Bảng dữ liệu** — đợt 4: bảng có nguồn báo cáo hiện thành báo cáo chi tiết theo ngày dùng chung
   động cơ (mỗi lần nộp một dòng), `?dang=tho` về liệt kê thô; bảng không có nguồn giữ nguyên.

## Hệ quả

- `currency_safe_result` bị xoá; `currency_warning` chỉ còn nghĩa "N dòng chưa quy đổi được".
  AC-38.2, AC-38.3 đổi chữ theo; AC-40.x là tiêu chí mới (`docs/04` mục 40).
- Ô tiền hiện "540.000 ₫" không phần lẻ; tỉ lệ hiện "6,18%". Cột đếm không hậu tố.
- Số đơn (TT) và DS Chốt (TT) chỉ có ở nguồn MKT (chỉ vận đơn có phân công Marketing).
- Hai lỗi thật sửa cùng đợt 1: liên kết phân trang kéo theo `trang` cũ (TL-53) và chip Kỳ có × ngay
  cả ở kỳ mặc định vì form luôn gửi `tu`/`den` (TL-52).

## Giới hạn và việc để lại

- KRW chưa có tỉ giá (ADR-031): dòng KRW không vào tổng tiền cho tới khi kế toán chốt.
- `so_tien_tt` gõ tay ở đơn không có chi tiết chưa vào DS Chốt (TT) — backlog, chờ chủ dự án.
- Người đổi team giữa kỳ sẽ thành hai dòng ở khối toàn kỳ (đợt 2).
- Ngưỡng màu mặc định không bịa; màn hình chỉ tô ba bậc sau khi Manager đặt (đợt 3).
