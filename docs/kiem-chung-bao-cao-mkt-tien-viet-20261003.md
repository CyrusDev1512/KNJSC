# Biên bản kiểm chứng — Báo cáo Marketing nộp bằng tiền Việt (03.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ quản: mọi số trong báo cáo nộp là tiền Việt; chủ dự án: Báo cáo tổng hợp hiện tại đổi sang VND, không tỉ giá, làm Marketing trước |
| Quyết định | [ADR-047](quyet-dinh/047-bao-cao-mkt-tien-viet.md) |
| Tiêu chí | AC-47.1 → 47.5 (mới); AC-38.2, 38.3, 46.5 đổi chữ |
| Nhánh | `claude/bao-cao-mkt-vnd` từ `Staging` `fd08cb3`, PR nháp về `Staging` |
| Môi trường | Máy ảo Claude Code trên web: Python 3, PostgreSQL 16 cục bộ, Chromium Playwright có sẵn |

## Đã đo

| Kiểm | Lệnh (từ `app/`) | Kết quả |
|---|---|---|
| Bài mới trên mã cũ | `python -m pytest reports/tests/test_mkt_tien_viet.py` | 4/5 **đỏ** đúng chỗ: chưa có `report_currency`, nộp Canada ra CAD, chưa có tệp chuyển đổi, TỔNG CỘNG là CAD |
| Bài mới sau sửa | như trên | 5/5 đạt |
| Bài cũ theo luật cũ | `reports forms_builder dashboard core orders` | 18 bài đỏ đúng dự kiến (ghim MKT = CAD/USD và DS Chốt (TT) theo tiền); viết lại theo ADR-047; bài cơ chế nhiều loại tiền ghi nhãn thẳng vào dòng để vẫn kiểm cơ chế dùng cho Sale |
| Tệp chuyển đổi | CSDL nháp: `migrate`, `du_lieu_mau`, gán 5 dòng MKT CAD/USD/CAD/trống/AUD, rồi `migrate reports 0005` ↔ `0006` | Xuôi: 5 dòng VND, số giữ nguyên (CPQC 438.446.060…); ngược: CAD 2, USD 1, AUD 1, trống 1 như ban đầu; xuôi lại: 5 VND; Sale không đổi |
| Trình duyệt (bấm thật) | `runserver` trên CSDL nháp, Chromium | `mkt.staff`: chọn Canada rồi Hoa Kỳ → Loại tiền vẫn VND; nhãn "CPQC (₫)", "Doanh số (₫)"; xem trước CPO "1.000.000 VND"; nộp thật → lưu Canada / VND / 5000000. `mkt.manager`: Báo cáo tổng hợp một dòng TỔNG CỘNG · VND, mọi dòng VND; không lỗi JS |
| Trình duyệt (bài kiểm) | `reports/tests/test_bo_cuc_bao_cao_e2e.py`, `test_o_nhap_so_e2e.py` | 10/10 đạt (bài ô nhập số đổi hậu tố CAD/USD → VND) |
| Ẩn Hóa đơn, Hóa đơn/DS Chốt (TT) | `test_bao_cao_mkt_khong_con_cot_hoa_don` | Đỏ trên mã trước, đạt sau: màn hình và Excel không còn hai cột; cột dữ liệu `hoa_don` giữ; 6 bài cũ nhắc hai cột viết lại |
| Lỗi giật bảng ở mép phải (lộ ra khi bảng bớt hai cột) | `test_keo_ngang_khong_con_cot_bi_che` | Kéo tới gần mép phải: trình duyệt chỉ tới 569 khi đích là 570 → lần nhích sau tưởng kéo lùi, giật bảng về 551. Sửa `report-filters.js` (sai số 2 px). Ở đúng mép phải không nhích ngược nữa nên một cột có thể bị vùng đứng yên che một phần — bài kiểm chỉ nới điều kiện "không vắt" ở mép phải. Chạy 3 lần đều đạt |
| Toàn bộ | `python -m pytest -m "not trinh_duyet and not cham"` | **2.861 đạt, 1 bỏ qua, 0 đỏ** (sau khi ẩn hai cột) |

## Chưa kiểm / để lại

- Chưa chạy trên máy chủ dự án và VPS; lên VPS `migrate` tự đổi nhãn báo cáo MKT cũ.
- DS Chốt (TT) của báo cáo MKT trống cho tới khi có tỉ giá được duyệt.
- Báo cáo Sale chưa đổi (chủ dự án: làm Marketing trước).
