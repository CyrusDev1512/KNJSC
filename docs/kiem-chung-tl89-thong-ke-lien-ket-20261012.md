# Biên bản kiểm chứng — Sửa TL-89: nút của Thống kê KN CRM (12.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 12.10: "sửa TL-89 đi", chọn đích **Báo cáo tổng hợp KN ERP** |
| Lỗi | Thống kê KN CRM, nguồn Sale/MKT: nút "Mở dữ liệu" và "Mở bảng nguồn" mở `/bang-tinh/bao_cao_*/`. Từ ADR-040 lưới đó luôn 404, với mọi vai, kể cả Admin |
| Phạm vi | 4 tệp mã (`statistics_profiles.source_url`, `statistics_service`, `statistics_views`, `crm/statistics.html`) và 1 tệp bài kiểm. Không có migration, không đổi quyền, không đổi số liệu |
| Môi trường | Máy ảo Claude Code trên web: Python 3.11.15 (CI 3.12), Django 5.2.17, PostgreSQL 16, Redis, Chromium Playwright. Hệ thống thật: ERP `runserver` 8020 và CRM 8021 chạy mã nhánh trên DB `knjsc_nc12` (dữ liệu như máy chủ dự án sau launcher: 10.000 vận đơn, 845 dòng `bao_cao_mkt`, `bao_cao_sale` chưa có dòng nào) |
| Kết luận | **Đạt.** Không còn nút nào ở Thống kê dẫn tới 404. Chặng 2 (người thử ở máy mình) chưa làm |

## 1. Đã đổi

| Nguồn ở Thống kê | Trước | Sau |
|---|---|---|
| Sale, MKT (bảng có nguồn báo cáo ERP) | `/bang-tinh/bao_cao_*/?f_ngay__…` ở KN CRM → 404 | Báo cáo tổng hợp KN ERP của đúng nguồn, cùng kỳ: `/bao-cao/tong-hop/?nguon=<mã>&tu=…&den=…` |
| Vận đơn | Lưới KN CRM lọc đúng kỳ | Như cũ |
| Bảng khác (vd. Báo cáo công việc Vận đơn) | Lưới KN CRM → 404 | Không có nút; nhận định vẫn hiện |
| Phần số liệu tạm lỗi ("Mở bảng nguồn") | Lưới, không lọc → 404 với bảng thường | Cùng luật trên; Báo cáo tổng hợp mở đúng kỳ |

- **Không dùng Bảng dữ liệu ERP:** trang đó chỉ Manager trở lên mở được, Staff và Leader sẽ gặp 403.
- **Báo cáo tổng hợp lọc nguồn theo cùng phạm vi với Thống kê** (`TableDef.objects.in_scope`, bảng đang dùng). Vì vậy vai
  nào thấy nguồn ở Thống kê thì mở được.
- **Liên kết sang ERP giữ host đang mở** (AC-1.10). Mở bằng 127.0.0.1 thì sang 127.0.0.1:8020; trên VPS thì đúng
  `MAIN_APP_URL`.
- **Số liệu có thể lấy từ bộ nhớ đệm Thống kê** (`CRM_OPT_STATS`), mà khoá đệm không theo host. Vì vậy dịch vụ lưu địa chỉ
  theo cấu hình, còn view đổi host trên bản sao của mỗi lần trả lời.

## 2. Bài kiểm tự động

| Kiểm | Kết quả |
|---|---|
| `crm/tests/test_thong_ke_lien_ket_nguon.py` (AC-40.9) trước khi sửa | 14 đỏ, đúng chỗ lỗi (liên kết lưới bảng báo cáo). 2 xanh: hai bài giữ hành vi Vận đơn |
| Cùng tệp sau khi sửa | **16/16 đạt** |
| Nội dung tệp | Sale/MKT × 7 vai, mở thật ở URLconf ERP (200, đúng nguồn, đúng kỳ); tổng quan × 4 vai; Vận đơn; bảng khác; số liệu lỗi; host 127.0.0.1 so với localhost khi lấy từ bộ nhớ đệm; tên miền thật |
| Thống kê và liên kết có sẵn: `test_executive_statistics*`, `test_thong_ke_*`, `test_lien_ket_khong_cut`, `test_optimization`, `test_crm_chi_van_don`, `core/tests/test_lien_ket_dich_vu` | 53 đạt, 1 bỏ qua (bài kiểm tải) |
| `tests/test_truy_vet.py` | 36/36 sau khi thêm AC-40.9 (docs/06: 384 tiêu chí, 348 trên 371) |
| Toàn bộ trừ trình duyệt, có Redis: `pytest -m "not trinh_duyet" -rs` | **3.177 đạt, 7 bỏ qua, 0 đỏ**, 8 phút 39 giây. Bằng 3.161 của lượt 12.10 cộng 16 bài mới; 7 bài bỏ qua là bài kiểm tải như mọi lượt |

## 3. Hệ thống thật, qua HTTP

| Kiểm | Kết quả |
|---|---|
| 12 tài khoản mẫu, mỗi người: Thống kê tổng quan và từng nguồn trong ô "Nguồn phân tích", hai kỳ (mặc định và 01/09–12/10). Gom mọi nút "Mở dữ liệu" / "Mở bảng nguồn", mở ở đúng dịch vụ bằng phiên của chính người đó | **66 trang Thống kê, 114 nút.** 20 đích ERP khác nhau đều trả 200, chọn đúng nguồn, đúng kỳ (8 `bao_cao_mkt`, 12 `bao_cao_sale`). 32 đích lưới `van_don` đều 200. Không nút nào trỏ lưới bảng thường. `sale.moi` không có nguồn nào: trang trống, không nút. **0 hỏng** |
| Quét liên kết như lượt kiểm 12.10 (12 tài khoản × ERP và CRM, tối đa 60 trang mỗi dịch vụ mỗi người) | **937 lượt mở trang, 0 trả lời 4xx hay 5xx.** Lượt 12.10 trên mã cũ có 404 ở Thống kê với 9 tài khoản |

## 4. Đóng vai bằng trình duyệt

Chromium, 1366 × 768, ngôn ngữ vi-VN, đăng nhập ở KN CRM 127.0.0.1:8021 rồi bấm sang ERP. Mọi bước không có lỗi JS.

| Vai | Thao tác | Kết quả |
|---|---|---|
| `sale.staff`, `sale.leader`, `sale.manager`, `quantri` | Thống kê `bao_cao_sale`, bấm "Mở dữ liệu" | Sang 127.0.0.1:8020 Báo cáo Sale, vẫn đăng nhập, ô nguồn `bao_cao_sale`, ô ngày 01/09/2026 – 12/10/2026. Bảng trống vì DB thử chưa có dòng Sale, khớp Thống kê |
| `mkt.staff`, `mkt.leader`, `mkt.manager`, `quantri` | Thống kê `bao_cao_mkt`, bấm "Mở dữ liệu" | Sang Báo cáo Marketing đúng nguồn, đúng kỳ, có số liệu (`mkt.staff`: 5 lần nộp của mình) |
| `quantri`, `sale.manager`, `mkt.manager`, `vd.staff` | Tổng quan, bấm lần lượt từng nút "Mở dữ liệu" (1 → 3 nút) | Mọi nút tới trang 200: Báo cáo tổng hợp ERP hoặc lưới `van_don` |
| `vd.staff` | Thống kê `van_don`, bấm "Mở dữ liệu" | Lưới KN CRM lọc đúng kỳ và các trạng thái cần kiểm, như trước |
| `vd.staff` | Thống kê "Báo cáo công việc Vận đơn" (bảng khác) | Có nhận định "Bảng chưa có dữ liệu", không có nút, không liên kết lưới |
| `quantri` | Thống kê MKT, bảng khác, tổng quan × 1366, 768, 390 px | Không tràn ngang. Thẻ nhận định không nút vẫn gọn |

**26/26 đạt.** Lượt đầu ra 18/26: kịch bản so ô ngày dạng `2026-09-01`, nhưng ERP hiện `01/09/2026` khi trình duyệt
tiếng Việt (ADR-032). Cùng ngày, chỉ khác cách viết. Sửa kịch bản, không sửa mã.

## 5. Hiệu năng

Trang `/thong-ke/` đo bằng `django.test.Client` trên DB `knjsc_nc12`, mã `Staging` `110dbaa` so với mã nhánh. 3 vai × 5 trang,
mỗi trang 6 lần (bỏ lần đầu), 2 lượt.

| Vai · trang | Số truy vấn trước → sau | Trung vị ms, lượt 1 · lượt 2, trước → sau |
|---|---|---|
| `quantri` · tổng quan | 17 → 17 | 56,5 → 50,7 · 59,8 → 48,5 |
| `quantri` · MKT | 13 → 13 | 50,0 → 41,0 · 58,4 → 47,0 |
| `quantri` · Sale / Vận đơn / bảng khác | 11 / 13 / 10, không đổi | trong dao động |
| `mkt.staff` · tổng quan, MKT | 13, 14, không đổi | trong dao động |
| `sale.manager` · tổng quan, Sale, Vận đơn | 12, 12, 14, không đổi | trong dao động |

- **Không thêm truy vấn nào:** nguồn báo cáo được lấy sẵn cùng danh sách bảng (`select_related("erp_report")`).
- **Trang ngoài phạm vi vẫn 403 như cũ:** `mkt.staff` mở Sale, Vận đơn; `sale.manager` mở MKT, bảng khác.

## 6. Chưa kiểm

- **Chặng 2:** chủ dự án thử ở máy mình. Bật hệ thống, vào KN CRM → Bàn điều hành, chọn nguồn Báo cáo Marketing hoặc
  Báo cáo Sale, bấm "Mở dữ liệu". Phải sang KN ERP, vẫn đăng nhập, đúng báo cáo, đúng khoảng ngày.
  - 13.10 chủ dự án bảo gộp `main` khi chưa thử, nên thay bằng mục 3 và 4.
  - Thử mà thấy sai thì sửa ở một nhánh mới, đi qua `Staging` như mọi thay đổi khác.
- **Safari, Firefox, máy Windows thật:** máy ảo chỉ có Chromium.
- **Hai tên miền thật trên VPS:** chỉ kiểm bằng bài kiểm (`MAIN_APP_URL` tên miền thật). Chưa phát hành.
