# Biên bản săn lỗi — Đối soát số liệu giữa các màn hình (06.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Đợt săn lỗi, bước 8 (chủ dự án duyệt, làm trên nhánh `claude/san-loi-tiep`) |
| Tiêu chí | AC-22.27 |
| Câu hỏi | Một con số hiện ở nhiều chỗ (Báo cáo tổng hợp, Excel, Bảng dữ liệu, Thống kê CRM) có phải là một không, và có đúng bằng dữ liệu gốc không |
| Môi trường | Máy ảo; hệ thống thật trên dữ liệu lượt 04.10: Báo cáo Marketing tháng 9/2026 (1.801 lần nộp, 21 người, VND), Vận đơn mới cả năm (10.032 đơn, CAD và USD, 19.968 dòng chi tiết). Người xem `mkt.manager`, `vd.manager`. Số gốc tính thẳng từ cơ sở dữ liệu qua `in_scope` của từng người |

## Báo cáo Marketing, 01/09 → 30/09/2026

| Chỉ tiêu | Cơ sở dữ liệu | Báo cáo tổng hợp | Cộng 21 dòng nhân sự | Excel: toàn kỳ | Excel: cộng 30 dòng tổng ngày | Thống kê CRM |
|---|---|---|---|---|---|---|
| Số Mess | 387.581 | 387.581 | 387.581 | 387.581 | 387.581 | 387581 |
| CPQC | 18.828.012.000 | 18.828.012.000 | 18.828.012.000 | 18.828.012.000 | 18.828.012.000 | (không hiện) |
| Số đơn | 24.683 | 24.683 | 24.683 | 24.683 | 24.683 | 24683 |
| DS Chốt | 48.311.822.000 | 48.311.822.000 | 48.311.822.000 | 48.311.822.000 | 48.311.822.000 | 48311822000 |

- Tỉ số tính lại bằng tay từ tổng đều khớp màn hình: tỉ lệ chốt 6,37 %, Giá Mess 48.578,26, CPO 762.792,69, CPQC/DS
  0,3897, AOV 1.957.291,33 (Thống kê CRM cùng 6,37 %, 762792,69, 1957291,33).
- Một ngày (01/09): Báo cáo tổng hợp và Bảng dữ liệu (`?tu=&den=`) cùng 13.026 Mess, 578.978.000 CPQC, 931 đơn,
  1.763.816.000 DS; điểm biểu đồ Thống kê CRM cùng 13.026 Mess.
- Số liệu sống: trong lúc đo có người nộp báo cáo mỗi 30 giây (bài chạy dài); tổng tháng 10 ở Bảng dữ liệu tăng đúng
  theo từng lần nộp.

## Vận đơn mới, 01/01 → 06/10/2026

| Chỉ tiêu | Cơ sở dữ liệu | Thống kê CRM |
|---|---|---|
| Số đơn | 10.032 (CAD 10.000, USD 32) | 10032 |
| Giá trị CAD (chi tiết sản phẩm còn hiệu lực) | 3.581.831,97 | 3581831,97 |
| Giá trị USD | 448,50 | 448,50 |
| Đã thanh toán CAD | 1.409.551,75 | 1409551,75 |
| Sản phẩm (tổng số lượng) | 49.844 | 49844 |

Lúc đầu tôi tự cộng ra CAD 3.582.165,51 — lệch 333,54. Truy ra là 3 dòng chi tiết **đã xoá mềm** mà câu cộng của tôi
quên loại; Thống kê loại đúng. Rà mọi chỗ đọc `WaybillItem`: chỗ nào cũng lọc `deleted_at` (qua `in_scope`,
`for_records` hay lọc thẳng). Không phải lỗi.

## Lỗi tìm được

**Lỗi nhẹ (đã sửa): Thống kê CRM viết số khác ERP.** Cùng một số mà ERP viết `48.311.822.000`, Thống kê CRM viết
`48311822000`; nhãn điểm biểu đồ viết số Mess là `13026,00`. Người đối chiếu hai màn hình phải đếm chữ số. Gốc:
template dùng `floatformat`, mà locale `vi` của Django không khai `NUMBER_GROUPING` nên không nhóm nghìn được.

Đã sửa: bộ lọc mẫu `so` (`core/templatetags/knjsc.py`) dùng lại `core.money.format_decimal`: tối đa hai số lẻ, số
nguyên không kèm `,00`. `crm/statistics.html` thay cả 11 chỗ `floatformat` và hai chú thích biểu đồ. Đo lại: Thống kê
CRM hiện `387.581`, `24.683`, `48.311.822.000`, `762.792,69`, điểm biểu đồ `13.026`.

## Ghi lại, chưa sửa

- Excel Báo cáo tổng hợp ghi tỉ lệ chốt là số thực đủ chữ số (`6.368475234854134`): ô hiện theo định dạng của Excel nên
  người xem có thể thấy dài. Là tỉ số, không phải tiền (BR-8 không áp); cần chủ dự án xem có muốn làm tròn trong tệp không.
- Báo cáo Sale chỉ có 3 lần nộp trên hệ thống thử: chưa đủ để đối soát nhiều loại tiền ở Sale; phần nhiều loại tiền đã
  đối soát ở Vận đơn (CAD, USD tách riêng, không cộng lẫn).

## Bài kiểm

`crm/tests/test_thong_ke_cach_viet_so.py` (AC-22.27): đỏ trên mã cũ (`48314322001`), xanh sau khi sửa. Các bài Thống kê
có sẵn (`test_executive_statistics*.py`) vẫn xanh.
