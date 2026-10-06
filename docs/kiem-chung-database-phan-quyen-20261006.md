# Biên bản — Dữ liệu đi từ A sang B, bảo mật, đổi URL là mất quyền (06.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án: tập trung vào cơ sở dữ liệu, dữ liệu từ A sang B (hệ thống cũ → DB mới, nâng cấp phiên bản, ERP ↔ CRM), bảo mật, "vào URL khác là mất quyền" |
| Đã chốt | Chặn trùng mã đơn ở tầng DB, trừ dòng đã xoá; xoá dòng vận đơn thì bỏ luôn đơn gốc |
| Nhánh | `claude/database-phan-quyen` từ `Staging` `b19b109`, PR nháp về `Staging` |
| Tiêu chí | AC-1.10, 1.11, 1.12; AC-6.12; AC-7.16; AC-8.11; AC-36.11 → 36.14 |
| Môi trường | Máy ảo; Postgres 16; hệ thống thật ERP 8020 / CRM 8021 (`runserver`) trên DB thử 10.033 vận đơn + 2.291 báo cáo MKT; Playwright Chromium |

## 1. Đổi URL là mất quyền

| Tình huống | Trước | Sau |
|---|---|---|
| Mở ERP bằng `127.0.0.1:8020` (đúng địa chỉ `KN JSC.bat` mở), bấm KN CRM | Sang `localhost:8021` — trình duyệt coi là host khác, không gửi cookie phiên → trang đăng nhập | Liên kết giữ host đang mở, chỉ đổi cổng; còn đăng nhập. Chiều CRM → ERP và đường dẫn Lên đơn cũ cũng vậy (AC-1.10). Đã đi thử bằng trình duyệt cả hai chiều |
| VPS: ERP, CRM hai tên miền mà chưa đặt `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` | Không ai báo; sang dịch vụ kia phải đăng nhập lại | `manage.py check --deploy` dừng với `core.E001` nói rõ phải đặt tên miền cha (AC-1.11). `deploy/production/README.md` ghi hai biến |
| Dịch vụ CRM thiếu `BANGTINH_GOC=prod` | Lặng lẽ chạy cấu hình dev (DEBUG bật, cookie không Secure) | Chạy ở tên miền thật mà thiếu biến → dừng khởi động với lời rõ; máy local vẫn chạy dev (AC-1.11) |
| Cùng đường dẫn ở ERP và CRM, từng vai | Chưa có bảng nào khoá | Đã dò **mọi** đường dẫn GET × 8 vai × 2 dịch vụ (105 dòng). Khác biệt giữa hai dịch vụ đều có chủ ý: quản lý bảng ở ERP chỉ Manager (ADR-045), ở CRM Leader như Manager (ADR-015); CEO chỉ xem. Bảng thành bài kiểm AC-1.12; đường dẫn chung mới mọc ra thì bài đỏ |
| Đổi cấp bậc, bộ phận, team, quyền riêng | — | Đã có: mọi phiên đang mở ở cả hai dịch vụ mất hiệu lực (`session_epoch`, bài `test_shared_login`). Không phải lỗi; là "bị đăng xuất" có chủ ý |

Ghi nhận, chưa sửa (ảnh hưởng thấp): trang `/bang-da-xoa/` của CRM trả danh sách rỗng cho Staff thay vì 403 (quy tắc 8);
`/van-don/thong-ke/` trả 403 cho Sale trong khi `/thong-ke/` mở cho mọi vai.

## 2. Dữ liệu

| Vấn đề | Trước | Sau |
|---|---|---|
| Mã đơn trùng | Chỉ bước kiểm tệp nhập so mã; lưới, Lên đơn, khôi phục dòng, hai lượt nhập cùng lúc đều để lọt hai dòng cùng mã | Cột `val_order_code` (mã đã cắt khoảng trắng, chỉ bảng vận đơn) + ràng buộc duy nhất một phần `record_ma_don_unique` (dòng chưa xoá, mã khác rỗng). Lỗi trùng thành lời tiếng Việt nêu mã ở mọi đường ghi; ghi trong điểm lưu nên lượt nhập nhiều dòng vẫn đi tiếp (AC-36.11) |
| Lên đơn khi bảng đã giữ mã cùng tiền tố (dòng nhập từ hệ thống cũ) | — (trước đây ra hai dòng cùng mã) | Bộ sinh mã nhảy qua mã đã có trên bảng, dò đúng mã qua chỉ mục: 4,0 ms/lần (cách quét theo tiền tố đo được 23 ms ở 10.033 dòng, tăng theo số dòng) |
| Migration 0017 trên dữ liệu đang có mã trùng | — | Dừng, liệt kê mã trùng, quay lui cả migration (AC-36.12) |
| Xoá dòng vận đơn | Đơn gốc còn sống, mồ côi | Bỏ luôn đơn (xoá mềm, nhật ký); khôi phục dòng thì khôi phục đơn (AC-6.12). Lưới hiện không có nút xoá dòng có sẵn; đường duy nhất trong giao diện là Bỏ đơn, vốn đã xoá cả hai — phần sửa này chặn hở ở tầng dịch vụ |
| Đổi kiểu cột | Giá trị cũ nằm nguyên: "1.500" trong cột Số nguyên, "abc" lọt vào cột số | Thử chuyển mọi giá trị (kể cả dòng đã xoá): hỏng thì từ chối, nêu số dòng và ví dụ; được thì ghi lại theo kiểu mới (AC-8.11) |
| Lệnh nâng cấp cấu trúc (`tao_bang_van_don`, `configure_erp_reports`) | Tạo, sửa cột thẳng trong DB, không tính lại dòng cũ | Chụp cấu trúc trước và sau; đổi thì `schedule_resync`, không đổi thì không đụng dòng nào (AC-36.13). Bằng chứng thật: 5 dòng báo cáo MKT mẫu thiếu cột `cpqc_doanh_so` và lệch số làm tròn ở `aov`, `cpo`, `gia_mess` — đúng loại lỗi này |
| Không có cách biết dữ liệu lệch | — | Lệnh chỉ đọc `kiem_tra_du_lieu` (AC-36.14), mục 3 |
| Tệp Excel có ô ngày dạng số (45000) | Cả dòng bị từ chối "không đúng kiểu Ngày" | Đổi thành 15/03/2023; chỉ số thật của ô Excel, chữ "45000" vẫn bị từ chối (AC-7.16) |
| `resync_table` | So lệch không gồm khoá số điện thoại | So đủ mọi cột tách (`DERIVED_FIELDS`, dùng chung cho `bulk_save` và lệnh kiểm) |

Giữ nguyên có chủ ý: bỏ cột thì giá trị cũ vẫn nằm trong `data`, tạo lại cột cùng mã thì dữ liệu hiện lại — docstring
`remove_column` ghi đây là tính năng (hoàn tác bỏ cột), không phải lỗi. Một lượt nhập tệp hỏng giữa chừng: bảng thường ghi
theo lô, mỗi lô một giao dịch; bảng vận đơn ghi từng dòng, dòng lỗi bị bỏ, dòng khác vào (AC-7.6).

## 3. `kiem_tra_du_lieu` trên DB thử

```
manage.py kiem_tra_du_lieu            # 4,5 giây cho 12.327 dòng
```

| Phép rà | Kết quả |
|---|---|
| Cột tách / cột tính sẵn lệch `data` | `bao_cao_mkt`: **5 dòng lệch** (dòng mẫu cũ, xem mục 2). `--sua` tính lại, rà lại ĐẠT. `van_don`: 0 |
| Giá trị ngoài danh sách chọn | 0 |
| Mã đơn trùng (dòng chưa xoá) | 0 — nên migration 0017 tạo được ràng buộc |
| Đơn mồ côi | 0 |
| `sl_*` lệch Chi tiết sản phẩm | 9.999 dòng: dữ liệu mẫu `MAU-*` nạp Chi tiết mà không ghi `sl_*`, và sửa Chi tiết trên lưới cũng không ghi. Cột ẩn mặc định, nên phép này chỉ để biết (nhãn BIẾT), không tính vào mã thoát |

## 4. Đi thử trên hệ thống thật

- Lưới Vận đơn (vd.manager): sửa ô Mã đơn dòng 2 thành mã dòng 1 → trạng thái "Lỗi lưu", thanh báo "Mã đơn
  MAU-20260910-0001 đã có ở một dòng khác trong bảng. Mỗi mã đơn chỉ một dòng." kèm Thử lại / Bỏ bản nháp; tải lại trang
  ô vẫn mã cũ. Thanh báo không chỉ đúng ô (máy chủ không biết ô nào gây trùng khi dán nhiều ô).
- Migration 0017 trên DB thử: xuôi 9,4 giây (gồm khởi động), ngược, xuôi lại; 10.033 dòng có khoá.

## 5. Bài kiểm

Bài mới (đều đỏ trên mã cũ, xanh sau khi sửa): `core/tests/test_lien_ket_dich_vu.py`, `test_kiem_cau_hinh.py`,
`test_ma_tran_quyen_hai_dich_vu.py`; `crm/tests/test_ma_don_khong_trung.py`; `orders/tests/test_xoa_dong_huy_don.py`,
`test_nang_cap_tinh_lai.py`, `test_kiem_tra_du_lieu.py`; `forms_builder/tests/test_doi_kieu_cot.py`, `test_ngay_so_excel.py`.

Ràng buộc mới làm đỏ 12 bài cũ có helper tự sinh mã đơn trùng (cùng tên khách → cùng mã) hay chép nguyên `data` của một
dòng sang dòng khác: đã sửa helper cho mỗi dòng một mã, không nới ràng buộc.

## Chưa kiểm

- Ràng buộc trên dữ liệu VPS thật: chạy `manage.py kiem_tra_du_lieu --bang van_don` trên VPS **trước** khi phát hành;
  còn mã trùng thì migration sẽ dừng và phải dọn trước.
- Tên miền cha thật cho `SESSION_COOKIE_DOMAIN`/`CSRF_COOKIE_DOMAIN` trong `.env` VPS: chủ dự án đặt, không ghi vào kho.
- Đổi kiểu cột trên bảng 100.000 dòng: chuyển trong cùng yêu cầu web, chưa đo thời gian.
