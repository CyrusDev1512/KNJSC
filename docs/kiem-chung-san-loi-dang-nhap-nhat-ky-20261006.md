# Biên bản săn lỗi — Dò mật khẩu và dữ liệu nhạy cảm trong nhật ký (06.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Đợt săn lỗi, bước 9 (chủ dự án duyệt, làm trên nhánh `claude/san-loi-tiep`) |
| Tiêu chí | AC-1.9 |
| Môi trường | Máy ảo; hệ thống thật (ERP 8020 `runserver` có nhiều luồng, CRM 8021, gunicorn như VPS ở 8030); `requests` nhiều luồng chờ chung một hiệu lệnh |

## Dò mật khẩu

| Kịch bản | Kết quả trước khi sửa |
|---|---|
| 5 lần sai lần lượt, lần 6 đúng mật khẩu | **Đạt**: lần 6 bị từ chối "đang bị khoá tạm" (AC-1.2 đã có) |
| **40 lần sai gửi cùng lúc** vào `sale.leader2` | **LỖI NGHIÊM TRỌNG: cả 40 lần đều được thử mật khẩu**, không lần nào bị chặn. Gốc: mọi yêu cầu đọc "chưa bị khoá" trước khi yêu cầu nào kịp ghi khoá, và bộ đếm cộng kiểu đọc-rồi-ghi nên mất lượt (sau loạt 40 lần bộ đếm chỉ lên 0 kèm một mốc khoá). Kẻ dò có N luồng được N lần đoán mỗi 15 phút thay vì 5 |
| Thông báo lỗi có lộ tài khoản tồn tại | Gần đạt: sai tài khoản hay sai mật khẩu cùng một lời (AC-1.1). Riêng tài khoản có thật sau 5 lần sai thì báo "đang bị khoá tạm" — dò được tài khoản nào có thật. Hệ thống nội bộ, tên đăng nhập là mã nhân sự dễ đoán; **ghi lại, chưa sửa** |

Đã sửa: `auth_service.reserve_attempt` **giữ chỗ** lần thử trong bộ đếm (khoá dòng hồ sơ `select_for_update`) **trước**
khi kiểm mật khẩu; lần thứ 5 đặt khoá, các lần thử cùng lúc sau đó thấy khoá và không được kiểm mật khẩu. Đăng nhập
đúng xoá cả bộ đếm lẫn khoá, nên sai 4 lần rồi lần 5 đúng vẫn vào được như cũ. Nhật ký "Khoá tạm" chỉ ghi khi lần sai
thật sự làm khoá. Lời báo khoá nói đúng số phút còn lại.

Bắn lại trên hệ thống thật: 40 lần cùng lúc → **5 lần được thử, 35 lần bị chặn**; 10 lần sau đó → 10 lần bị chặn.

## Dữ liệu nhạy cảm trong nhật ký (điều cấm 6)

| Chỗ quét | Kết quả |
|---|---|
| Nhật ký ứng dụng của ERP, CRM, worker, gunicorn sau cả đợt thử (đăng nhập sai với mật khẩu riêng, lên đơn với số điện thoại, tên khách) | **Đạt**: không có mật khẩu, số điện thoại, tên khách, `csrfmiddlewaretoken`. Nhật ký đo yêu cầu chỉ ghi mẫu đường dẫn (`route`), không ghi đường dẫn thật hay tham số |
| nginx trên VPS (`deploy/production/nginx.conf.template`) | **Đạt**: định dạng `technical` chỉ có mã yêu cầu, mã trả về, thời gian; không ghi URL nên chuỗi tìm kiếm (`?q=` số điện thoại) không vào nhật ký |
| Nhật ký hoạt động (AuditLog) trong DB, 5.001 dòng | **Đạt**: 0 dòng chứa số điện thoại, 0 dòng chứa mật khẩu |
| `runserver` (chỉ máy phát triển) | Ghi cả đường dẫn kèm tham số — không chạy trên VPS |

Ghi lại, chưa sửa (nhẹ):
- Mỗi lần bị từ chối quyền (403) Django ghi **nguyên một traceback** mức WARNING: không lộ dữ liệu, nhưng nhật ký VPS phình nhanh nếu
  có ai dò đường dẫn.
- Người dùng gõ nhầm mật khẩu vào ô Tên đăng nhập thì chuỗi đó vào `actor_label` của dòng "Đăng nhập thất bại" (Admin
  xem được). Che đi thì mất dấu vết dò tài khoản — cần chủ dự án chọn.

## Bài kiểm

`org/tests/test_do_mat_khau.py`: 3 bài. Bài 20 luồng thật cùng gửi đỏ trên mã cũ (20/20 lần được thử), xanh sau khi
sửa; hai bài canh luật cũ (lần 5 đúng vẫn vào, số phút đúng).

## Chưa kiểm

- Dò rải nhiều tài khoản từ một địa chỉ (password spraying): khoá theo tài khoản không chặn được kiểu này. Chặn theo địa
  chỉ IP cần chủ dự án chốt (cả văn phòng chung một IP — lý do FR-1.2 chọn đếm theo tài khoản).
