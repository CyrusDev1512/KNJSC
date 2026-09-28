# ADR-042 — Báo cáo tổng hợp như ảnh mẫu: quy ₫ trước khi cộng, cột đối soát (TT), bố cục khối theo ngày, ngưỡng màu

| Mục | Nội dung |
|---|---|
| Ngày | 23.09.2026 (đợt 1); các đợt sau bổ sung ngay trong tệp này |
| Trạng thái | Năm đợt xong local 23.09.2026 (PR nháp #36 vào nhánh codex); chờ chủ dự án nghiệm thu và Codex phát hành VPS |
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
   khoá; nguồn MKT thật từ 12 xuống dưới 10 truy vấn (AC-42.4). Quá trần thì giữ queryset như cũ.
5. **Bố cục khối như ảnh** (đợt 2, `reports/layout.py` + `reports/_bang_khoi.html`): khối **toàn kỳ
   theo nhân sự** đứng đầu — cộng trong bộ nhớ từ các dòng ngày × người, cột STT · Team · Nhân sự ·
   Leader, TỔNG CỘNG ngay dưới hàng tiêu đề cột, sắp theo mã; rồi **mỗi ngày một bảng riêng** mới nhất
   trước, tiêu đề ngày đặt trên bảng, **không cột Ngày**, TỔNG CỘNG ngày bằng tổng dòng con (cột tính
   tính lại từ tổng), STT đếm lại từ 1; nhiều bảng trong **một** khung cuộn (thead và TỔNG CỘNG dính
   trong bảng của nó). Phân trang vẫn 100 dòng người; ngày bị tách trang ghi "(tiếp)" và lặp TỔNG
   CỘNG đủ cả ngày. Nút **Gộp / Không gộp** (`gop=1`): Gộp = mỗi ngày chỉ còn dòng TỔNG CỘNG, phân
   trang theo ngày — chính là bố cục trước 19.09. Excel hai sheet "Toan ky theo nhan su" và "Theo
   ngay" cùng khối, số thô. Các cách xem khác vẫn một bảng, cột định danh như ADR-035.
6. **Ngưỡng màu tuyệt đối ba bậc** (đợt 3): `ReportSource.thresholds` `{mã chỉ tiêu: {"tot", "kem"}}`
   (migration `reports/0005`), do quản lý của bộ phận sở hữu nguồn đặt ngay trên màn hình báo cáo (nút
   "Ngưỡng màu", POST `bao-cao/tong-hop/nguong/`, cùng luật `grant_service.can_manage_columns`, ghi nhật
   ký); chiều tốt theo `METRIC_DIRECTION`; ô đạt mốc Tốt xanh, qua mốc Kém đỏ (`o-xau`, token
   `--critical`), giữa vàng; dòng TỔNG CỘNG cũng tô; chỉ tiêu chưa đặt giữ cách tương đối ±10 %
   (AC-22.16); không bịa số mặc định. Form hiện mốc theo cách người Việt gõ (`7,32`, `84.526.646`) để
   `parse_money` đọc lại đúng. Bộ lọc **Sản phẩm tick nhiều mục** (`sp` lặp lại, URL cũ `sp=A` vẫn đúng;
   danh sách chỉ gồm sản phẩm có thật trong phạm vi quyền; (TT) cũng lọc theo) và mốc Chọn nhanh "Tuần
   này". Danh sách sản phẩm là một truy vấn thêm; bù bằng backend đăng nhập lấy người dùng kèm hồ sơ
   trong một lệnh (`core/auth_backends.py`), mọi màn hình đã đăng nhập bớt một truy vấn.
7. **Bảng dữ liệu** (đợt 4): bảng có nguồn báo cáo Sale/MKT mở ở `/bang/<mã>/` là **báo cáo chi tiết
   theo ngày** dùng chung động cơ (`activity_service.build(detail=True)` thêm `record_id` vào khoá nhóm):
   **mỗi lần nộp một dòng** — nộp nhiều lần/ngày (ADR-032) vẫn tách, STT riêng; cùng bố cục khối, Gộp,
   quy ₫, nhãn theo nguồn, ngưỡng màu và (TT); bộ lọc như Báo cáo tổng hợp trừ Nguồn và Cách xem; 25 dòng
   một trang (quy tắc 1); Xuất tệp ra Excel cùng khối. (TT) khoá theo (ngày, người) không chia được cho
   từng lần nộp: khoá có nhiều dòng (`SummaryResult.derived_shared`) thì dòng để "—", TỔNG CỘNG ngày và
   toàn kỳ cộng mỗi khoá một lần. `?dang=tho` về liệt kê thô từng dòng (mọi liên kết giữ `dang=tho`);
   bảng không có nguồn (vận đơn, bảng thường) giữ nguyên. Bối cảnh màn hình dùng chung ở
   `reports/screen.py`. Lỗi vặt của liệt kê thô sửa cùng đợt: phân trang và sắp xếp giữ bộ lọc
   (`filter_query`), `aria-sort`, Đúng/sai hiện Có/Không, "Sửa cột" theo `can_manage_columns`.

## Hệ quả

- `currency_safe_result` bị xoá; `currency_warning` chỉ còn nghĩa "N dòng chưa quy đổi được".
  AC-38.2, AC-38.3 đổi chữ theo; AC-42.x là tiêu chí mới (`docs/04` mục 40).
- Ô tiền hiện "540.000 ₫" không phần lẻ; tỉ lệ hiện "6,18%". Cột đếm không hậu tố.
- Số đơn (TT) và DS Chốt (TT) chỉ có ở nguồn MKT (chỉ vận đơn có phân công Marketing).
- Hai lỗi thật sửa cùng đợt 1: liên kết phân trang kéo theo `trang` cũ (TL-58) và chip Kỳ có × ngay
  cả ở kỳ mặc định vì form luôn gửi `tu`/`den` (TL-52).

## Giới hạn và việc để lại

- KRW chưa có tỉ giá (ADR-031): dòng KRW không vào tổng tiền cho tới khi kế toán chốt.
- `so_tien_tt` gõ tay ở đơn không có chi tiết chưa vào DS Chốt (TT) — backlog, chờ chủ dự án.
- Người đổi team giữa kỳ sẽ thành hai dòng ở khối toàn kỳ (đợt 2).
- Ngưỡng màu mặc định không bịa; màn hình chỉ tô ba bậc sau khi Manager đặt (đợt 3).
- Bảng dữ liệu dạng báo cáo chỉ hiện cột trong ánh xạ nguồn; cột khác (ghi chú, thị trường, loại tiền) xem
  bằng `?dang=tho` — chờ chủ dự án nói có cần thêm "cột xem thêm" không (đợt 4).

## Bổ sung 26.09.2026 — thẻ Tổng quan bỏ ô đơn vị và cảnh báo quy đổi

Chủ dự án yêu cầu xoá ô vàng trên các thẻ Báo cáo tổng hợp của **Tổng quan** ERP ("… dòng chưa quy
đổi được …" và dòng "VND (₫), quy đổi theo tỉ giá cố định …"). Thẻ Tổng quan chỉ còn nguồn và chỉ
tiêu. Cách tính **không đổi**: dòng thiếu tỉ giá hoặc trống loại tiền vẫn không vào tổng tiền; cảnh
báo vẫn hiện ở màn Báo cáo tổng hợp chi tiết, Bảng dữ liệu dạng báo cáo và tệp Excel (AC-22.18).
