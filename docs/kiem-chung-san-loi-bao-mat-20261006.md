# Biên bản săn lỗi — Bảo mật (06.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Đợt săn lỗi nghiêm trọng chủ dự án duyệt, bước 2 |
| Tiêu chí | AC-7.14 (xuất Excel không chạy công thức), AC-7.15 (chặn tệp nhập "bom nén") |
| Nhánh | `claude/san-loi-bao-mat` từ `Staging` (sau #91) |
| Môi trường | Máy ảo; hệ thống thật chạy thẳng (ERP 8020, CRM 8021) trên dữ liệu lượt 04.10 |

## Kết quả từng mục

| Mục | Cách thử | Kết quả |
|---|---|---|
| **Chèn công thức vào tệp Excel xuất** | Ô chữ `=HYPERLINK("http://…","Bấm")`, `=1+1` qua `excel.write_table` (thường và ghi liền), xuất Bảng dữ liệu, xuất Báo cáo tổng hợp | **LỖI NGHIÊM TRỌNG**: openpyxl ghi mọi chuỗi bắt đầu bằng `=` thành **công thức chạy được**. Bất kỳ Sale nào gõ tên khách hay ghi chú như vậy là người mở tệp xuất bị dẫn tới trang lạ. **Đã sửa** |
| **Tệp nhập "bom nén"** | .xlsx 220 KB, một dòng 2 triệu ô (giải nén 76 MB) | **LỖI NGHIÊM TRỌNG**: qua mọi kiểm tra cũ rồi khi đọc ăn **1,85 GB RAM, 68 giây CPU**. Ai có quyền nhập (Leader trở lên) đủ làm sập VPS 4 GB. **Đã sửa**: 68 MB, 0,01 giây, từ chối có lời tiếng Việt |
| **Thư viện có lỗ hổng đã công bố** | `pip-audit -r requirements.txt` (chạy ngoài dự án) | **Django 5.2.6: 62 mục**, sửa ở bản vá 5.2.17 cùng dòng 5.2 LTS; **python-dotenv 1.0.1: 1 mục** (1.2.2). **Đã nâng** hai bản vá này; `pip-audit` sau khi nâng: "No known vulnerabilities found" |
| Vượt quyền bằng id của người khác (IDOR) | `sale.staff`, `mkt.staff`, `vd.staff` gọi thẳng GET/POST 28 mẫu đường dẫn có id (báo cáo bộ phận khác, đơn của Sale khác, dòng vận đơn, việc, tài liệu, hồ sơ nhân sự, biểu mẫu, thư mục, tác vụ nền của Admin) | **Đạt**: mọi truy cập bị chặn; riêng nhân viên Vận đơn mở chi tiết mọi dòng vận đơn — đúng quyền ADR-033 |
| Phiên sau khi khoá, đặt lại mật khẩu, xoá tài khoản | Đăng nhập ERP + CRM, Admin làm thao tác, gọi lại bằng phiên cũ | **Đạt**: cả ba trường hợp phiên cũ bị đá về trang đăng nhập ở cả hai dịch vụ |
| Tệp giả đuôi | .exe đổi đuôi .xlsx | **Đạt**: từ chối. Chữ hay HTML đổi đuôi .csv thì đọc như CSV — chỉ là chữ, không chạy |
| Cấu hình triển khai | `manage.py check --deploy --settings=knjsc.settings.prod` | **Đạt**: 0 cảnh báo (HSTS, cookie Secure/HttpOnly, nosniff, X-Frame-Options DENY) |
| Header nginx | Đọc `deploy/production/nginx.conf.template` | Nhẹ: chưa `server_tokens off` (lộ phiên bản nginx), chưa có Content-Security-Policy. Ghi lại, chưa sửa: CSP cần rà mọi script nội dòng trước |

## Đã sửa

1. **AC-7.14:** `core/excel.neutralise_formulas(wb)` đổi mọi ô công thức thành ô chữ, giữ nguyên nội dung.
   - Gọi trong `write_table` (chế độ thường) và cuối `reports/excel.build_workbook`.
   - Chế độ ghi liền (tệp lớn, xuất nền) đặt kiểu chữ ngay lúc tạo ô.
   - Hệ thống không xuất công thức có chủ ý nào. Tệp mẫu nhập vốn đã an toàn.
2. **AC-7.15:** `core/excel._kiem_bom_xlsx` chạy trước openpyxl.
   - Tổng giải nén ≤ 200 MB.
   - Đếm ô từng dòng của mọi sheet bằng `iterparse` dòng chảy; dòng nào vượt 500 ô thì từ chối ngay.
   - CSV cũng có trần 500 cột.
   - Trần khai một chỗ ở `core/constants.py` (`IMPORT_MAX_COLUMNS`, `XLSX_MAX_UNCOMPRESSED_BYTES`).
   - Cái giá: tệp nhập lớn nhất cho phép (10.000 dòng × 45 cột, 2 MB) đọc chậm thêm 2,8 giây (+23 %), vẫn xa mốc
     NFR-3.
3. **Bản vá thư viện:** `Django==5.2.17`, `python-dotenv==1.2.2` trong `app/requirements.txt`. Toàn bộ
   `-m "not trinh_duyet"` chạy trên bản mới: 2.940 đạt; 3 bài truy vết đỏ lúc đó chỉ vì docs/04 chưa kịp ghi, sau đó
   đã xanh. Launcher và VPS phải **dựng lại image** vì requirements đổi.

## Bài kiểm mới

- `forms_builder/tests/test_xuat_khong_cong_thuc.py`: 5 bài, 4 bài đỏ trên mã cũ.
- `forms_builder/tests/test_nhap_tep_bom.py`: 4 bài; trên mã cũ không chạy được vì chưa có trần.

## Chưa kiểm

- CSP và `server_tokens off` ở nginx: chưa sửa, cần chủ dự án duyệt vì đụng cấu hình VPS.
- Chưa chạy công cụ quét lỗ hổng web tự động (ZAP…). Đó là thêm công cụ; cần hỏi trước.
