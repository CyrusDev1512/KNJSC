# Biên bản săn lỗi — Giờ, tiền và số (06.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Đợt săn lỗi, bước 5 (chủ dự án duyệt, làm trên nhánh `claude/san-loi-tiep`) |
| Tiêu chí | AC-9.7 (ô số chỉ nhận số viết kiểu Việt Nam, số quá lớn báo lỗi), AC-9.8 (ngày "hôm nay" theo giờ Việt Nam) |
| Môi trường | Máy ảo, đồng hồ hệ thống giờ quốc tế như container; hệ thống thật (ERP 8020, CRM 8021) trên `Staging` `632506c`; `requests` gửi thẳng form |

## Số và tiền

| Kịch bản | Kết quả trước khi sửa |
|---|---|
| Nộp báo cáo Marketing, Doanh số `NaN` | **LỖI VỪA: trang lỗi 500.** `parse_money` nhận vì `Decimal("NaN")` hợp lệ trong Python; cơ sở dữ liệu từ chối lúc ghi |
| Doanh số `Infinity`, `1e400` | **Trang lỗi 500**, cùng gốc |
| Doanh số 24 chữ số | **Trang lỗi 500**: cột tiền giữ 18 chữ số (16 phần nguyên) |
| Doanh số `1e5` | Ghi thành 100.000 — chữ "e" lọt qua; không ai gõ số kiểu đó, có thể là gõ nhầm |
| `+-5` | Đọc thành 5 (mất dấu trừ); `--5` thành −5 |
| Lên đơn, Đơn giá `NaN`, `Infinity`, `1e30` | **Đạt**: form chặn, trả lại form (mã 400), không ghi đơn |
| Cột tiền của lưới Vận đơn | **Đạt**: `waybill_service.money` đã chặn số không hữu hạn, số âm |
| `1.234,5`, `1,234.5` (dán từ Excel kiểu Mỹ), `1.234`, `150.00`, `1 234 ₫`, `0` | **Đạt**: đọc đúng |
| Số đơn = 0, Số Mess = 0 (chia cho không ở CPQC/đơn, tỉ lệ chốt) | **Đạt**: Báo cáo tổng hợp (Từng lần nộp, Gộp), xuất Excel, Thống kê CRM đều 200, không hiện `NaN`/`Infinity`; cột tính sẵn để trống |
| Doanh số âm `-5000` | Nhận và ghi. Chưa sửa: có thể có nghiệp vụ hoàn tiền — **cần chủ dự án chốt** có cho số âm ở báo cáo ngày không |

## Giờ

| Kịch bản | Kết quả trước khi sửa |
|---|---|
| Chip "Hôm nay", "Tháng này", "Tháng trước" của lưới lúc 00:30 giờ Việt Nam (17:30 hôm trước giờ quốc tế) | **LỖI VỪA**: `sidebar_service.preset_range` dùng `date.today()` — đồng hồ container là giờ quốc tế, nên **từ 0 giờ tới 7 giờ sáng "Hôm nay" là hôm qua**, ngày 1 đầu tháng thì "Tháng này" là tháng trước. Người làm ca sớm lọc "Hôm nay" không thấy đơn mới |
| Tên tệp Excel xuất từ lưới | **Lỗi nhẹ**: `datetime.now()` mang giờ máy chủ, lệch 7 giờ |
| Ngày báo cáo, ngày đơn, tên tệp xuất Báo cáo tổng hợp, lọc `__date` | **Đạt**: đã dùng `timezone.localdate()`, Django đổi theo `TIME_ZONE` |
| Rà toàn bộ mã: `date.today()`, `datetime.now()`, `.date()` trên giờ quốc tế | Chỉ còn ở các lệnh dữ liệu giả và đo hiệu năng (không ảnh hưởng người dùng); ở JS `date-inputs.js` đổi giờ có `+07:00` rõ ràng |

## Đã sửa

1. **AC-9.7:** `core.money.parse_money` sau khi bỏ dấu ngăn nghìn chỉ nhận chữ số với một dấu thập phân, và một dấu
   `+`/`-` ở đầu. Hàm mới `check_amount` chặn số không hữu hạn và phần nguyên quá 16 chữ số, báo "Số … quá lớn: tối đa 16
   chữ số phần nguyên". Ô số thật của tệp Excel cũng qua `check_amount`. Mọi chỗ đọc tiền (form, lưới, Lên đơn, mốc màu)
   dùng chung hàm này nên cùng được chặn.
2. **AC-9.8:** `preset_range` dùng `timezone.localdate()`; tên tệp xuất lưới dùng `timezone.localtime()`.

## Bài kiểm

`core/tests/test_so_va_gio_bien.py`. Đỏ trên mã cũ: mọi ca chữ lạ, số quá dài, nộp báo cáo `NaN` (500), chip "Hôm
nay", tên tệp. Ca đọc đúng cách viết Việt Nam xanh cả trước lẫn sau (canh không siết quá tay).

## Chưa kiểm

- Đổi múi giờ máy người dùng (máy để giờ Mỹ): trình duyệt hiện ngày theo giờ máy, máy chủ theo giờ Việt Nam — cần
  máy thật.
- Số âm ở báo cáo ngày: chờ chủ dự án chốt.
