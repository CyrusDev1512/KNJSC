# Kiểm chứng hai lỗi chủ dự án báo — 19.09.2026

Nền `3c61e86`, nhánh `codex/crm-update-solar-ui`, máy ảo Claude Code trên web.
Chưa phát hành VPS.

## Lỗi 1 — đơn thứ hai của cùng số điện thoại lấy tên khách của đơn đầu

**Nguyên nhân.** `order_service.create_order` nhận diện khách bằng số điện thoại
(`Customer.phone` là duy nhất, FR-6.7) qua `get_or_create`. Số đã có thì `defaults`
bị bỏ qua, nên tên vừa gõ **không** được dùng; ô Tên khách của dòng vận đơn lấy từ
`order.customer.name`, tức tên của lần lên đơn đầu tiên. Gõ nhầm tên lần đầu là mọi
đơn sau đều mang tên sai đó.

Tái hiện trước khi sửa, trên DB dev:

| Lượt | Gõ vào | Đơn ghi |
|---|---|---|
| Đơn 3 — `0900000003` | "Ten Ban Dau" | Ten Ban Dau |
| Đơn 4 — `0900000003` | "Ten Moi Hoan Toan" | **Ten Ban Dau** ✗ |

**Cách sửa** (chủ dự án chọn): đơn ghi **tên vừa gõ**, và danh bạ đổi theo tên mới
nhất, có ghi nhật ký hoạt động. Đơn cũ không bị sửa ngược vì ô Tên khách của chúng
là chữ đã ghi lúc đó. Facebook và Email chỉ điền thêm khi đang trống — ô bỏ trống
không xoá dữ liệu cũ.

Sau khi sửa, cùng DB dev:

| Lượt | Gõ vào | Đơn ghi | Danh bạ |
|---|---|---|---|
| `0911000001` | "Ten Ban Dau" | Ten Ban Dau | Ten Ban Dau |
| `0911000001` | "Ten Sua Lai" + email | **Ten Sua Lai** | Ten Sua Lai, email điền thêm |
| `0911000001` | "Ten Sua Lai", email bỏ trống | Ten Sua Lai | email cũ **giữ nguyên** |
| `0911000002` | "Khach Khac" | Khach Khac | khách riêng |

Nhật ký: `Cập nhật khách 0911000001 khi lên đơn: tên Ten Ban Dau → Ten Sua Lai · email a@b.com`.

Chromium, qua đúng biểu mẫu Lên đơn với tài khoản Sale: hai đơn cùng số `0977000111`
ghi lần lượt "Khach Go Nham" và "Khach Ten Dung"; danh bạ về "Khach Ten Dung".

## Lỗi 2 — hộp lọc của từng cột trông hỏng (TL-46)

**Nguyên nhân.** `static/css/crm-frame.css` dòng 184 mở chú thích tiêu đề mục
`/* ── 3. Lưới: … ` nhưng **thiếu `*/`**. Chú thích chạy tiếp tới chú thích kế tiếp
ở dòng 219, nuốt **24 luật CSS** — toàn bộ nhóm `.loc-cot-*`. Tệp CSS vẫn hợp lệ nên
không có lỗi nào được báo. Lỗi có từ commit `9bac840` (14.09).

Hậu quả nhìn thấy: hộp lọc không nền, không khung, không giới hạn chiều cao, không
cuộn; 200 giá trị trải khắp màn hình và đè lên chữ của lưới, đọc không nổi.

**Cách sửa.** Đóng chú thích đó. 24 luật sống lại đều thuộc nhóm `.loc-cot-*`, không
luật nào đụng phần khác của trang — đã đối chiếu từng selector.

Đo sau khi sửa (Chromium, `getComputedStyle`):

| Thuộc tính | Trước | Sau |
|---|---|---|
| Nền hộp | không có | `rgb(255, 253, 247)` |
| Khung | không có | `1px solid rgb(158, 175, 154)` |
| Rộng | tràn màn hình | 256 px |
| Danh sách giá trị | không cuộn | cao tối đa 250 px, cuộn được |

**Vì sao bộ kiểm không bắt được.** `core/tests/test_giao_dien.py` quét tên lớp bằng
biểu thức chính quy trên **toàn bộ** tệp CSS, nên `.loc-cot-hop` nằm trong chú thích
vẫn bị tính là đã khai. Đã sửa: bỏ phần trong `/* … */` trước khi quét, thêm bài
khẳng định không chú thích nào chứa cả `{` lẫn `}` (dấu hiệu chắc chắn của chú thích
quên đóng), và bài kiểm hộp lọc có đủ nền, khung, cuộn.

Đã thử đưa lỗi trở lại: bốn bài chuyển đỏ đúng như mong đợi, khôi phục thì xanh lại.

## pytest

| Lượt | Kết quả |
|---|---|
| `orders/tests/test_len_don.py` (thêm AC-6.9, ba bài) | 33 đạt |
| `core/tests/test_giao_dien.py` (thêm AC-11.40) | 578 đạt |
| Toàn bộ `-m "not trinh_duyet and not cham"` | 2.428 đạt, 1 bỏ qua, 0 đỏ, mã thoát 0 |
| `tests/test_truy_vet.py` sau khi thêm AC | Đạt; docs/06 lên 234 AC, 221 tự động, 197 đã có bài |

## Chưa kiểm

- Bài `trinh_duyet` không chạy ở lượt này.
- Chưa phát hành VPS; cả hai lỗi vẫn còn trên domain thật cho tới khi phát hành.
- Hộp lọc trên bảng 100.522 dòng mở mất khoảng 5 giây và chỉ hiện 200 giá trị đầu.
  Đó là giới hạn cố ý (`GRID_FILTER_OPTIONS_MAX`), không phải lỗi vừa sửa, nhưng với
  cột nhiều giá trị như Tên khách thì danh sách gần như vô dụng — ghi vào backlog để
  chủ dự án chốt có đổi cách lọc cột đó không.
