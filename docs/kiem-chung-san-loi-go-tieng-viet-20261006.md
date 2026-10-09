# Biên bản săn lỗi — Gõ tiếng Việt (06.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Đợt săn lỗi, bước 4 (chủ dự án duyệt, làm trên nhánh `claude/san-loi-tiep`) |
| Tiêu chí | AC-9.6 |
| Môi trường | Máy ảo; hệ thống thật (ERP 8020, CRM 8021) trên `Staging` `632506c`; Playwright Chromium (giả lập sự kiện ghép chữ của bộ gõ, gõ phím nhanh), `requests` cho dữ liệu dạng tổ hợp |

## Đã thử

| Kịch bản | Kết quả trước khi sửa |
|---|---|
| Lưới Vận đơn: gõ "Nguyễn Văn Ánh" bằng sự kiện ghép chữ của bộ gõ (IME), Enter giữa lúc đang ghép | **Đạt**: ô chỉ lưu chữ đã ghép xong, DB đúng (kiểm bằng id dòng) |
| Lưới: giả lập kiểu Unikey (gõ chữ, xoá lùi, thay bằng chữ có dấu), gõ nhanh liên tục | **Đạt**: không rớt chữ, không lặp chữ |
| Lên đơn với tên khách **dạng tổ hợp** (NFD — macOS và một số bộ gõ gửi "e" + dấu rời), rồi tìm bằng chữ gõ từ Windows (NFC) | **LỖI NGHIÊM TRỌNG**: đơn `DH-0610-0027` lưu nguyên dạng tổ hợp; tìm "Ngọc Ánh" ra **0 kết quả** cả khớp đúng lẫn `icontains`. Hệ quả: người Windows không tìm ra khách do người Mac nhập, tra trùng khách và gộp nhóm theo tên/sản phẩm trượt, Báo cáo tổng hợp có thể tách một người thành hai dòng |
| Ô tìm kiếm của lưới gõ từ Mac | Cùng lỗi theo chiều ngược: dữ liệu NFC, chữ tìm NFD → 0 kết quả |
| Tệp Excel/CSV soạn trên Mac | Cùng lỗi: ô chữ vào bảng nguyên dạng tổ hợp |

## Đã sửa

`core.middleware.UnicodeNFCMiddleware` (đăng ký ngay sau `SessionMiddleware`) đưa mọi chữ người dùng gửi lên về dạng
dựng sẵn NFC **ở cửa vào**, nên mọi tầng sau (ghi, tìm, lọc, tra trùng) chỉ thấy một dạng:
- tham số GET (tìm kiếm, lọc);
- form POST (urlencoded, multipart);
- thân JSON của lưới: đọc ra rồi chuẩn hoá từng chuỗi, vì JSON có thể mã hoá dấu thành `́` mà chuẩn hoá văn bản
  thô không thấy.

Ô mật khẩu và `csrfmiddlewaretoken` giữ nguyên từng byte: chuẩn hoá mật khẩu thì mật khẩu đặt từ máy này có thể không
đăng nhập được từ máy kia. Tệp tải lên: `core.excel` chuẩn hoá từng ô chữ khi đọc (.xlsx và .csv).

Bắn lại trên hệ thống thật sau khi sửa: Lên đơn với tên dạng tổ hợp → DB lưu dạng NFC, tìm khớp đúng 1, `icontains` 1,
không còn bản dạng tổ hợp.

## Bài kiểm

`crm/tests/test_chu_viet_mot_dang.py`: 4 bài (Lên đơn; lưới ghi JSON rồi tìm bằng chữ NFD; mật khẩu không đổi; ô CSV và
.xlsx). Đỏ trên mã cũ, xanh sau khi sửa.

## Dữ liệu đã có

Bản sửa không đụng dữ liệu cũ. Đếm số dòng còn chữ dạng tổ hợp (chỉ đọc, chạy được trên VPS):

```sql
SELECT count(*) FROM forms_builder_datarecord WHERE NOT (data::text IS NFC NORMALIZED);
```

Hệ thống thật trong máy ảo: 1 trên 12.090 dòng — chính đơn thử `DH-0610-0027`. VPS chưa có khách nên chưa viết lệnh
chuẩn hoá dữ liệu cũ; nếu câu trên ra số lớn thì làm thành một lệnh riêng (ghi qua tầng dịch vụ, có nhật ký).

## Chưa kiểm

- Unikey, EVKey thật trên Windows và bộ gõ Telex của macOS/Safari thật: máy ảo chỉ giả lập được sự kiện. Kịch bản tay:
  gõ "Nguyễn Ngọc Ánh" vào ô Tên khách của lưới bằng từng bộ gõ, Enter, tải lại trang, tìm "Ngọc Ánh" ở ô tìm kiếm
  từ một máy khác hệ điều hành — phải ra đúng dòng.
