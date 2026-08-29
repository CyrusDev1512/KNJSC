# ADR-007 — Biểu mẫu luôn chọn bảng có sẵn, và chốt bảy nhãn ý nghĩa

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | 29.08.2026 |
| Người quyết định | (điền tên) |
| Liên quan | FR-8.3 · ADR-001 · ADR-006 · backlog K2, K3, N8 |

---

## Bối cảnh

Hai điểm còn treo, cùng chặn Giai đoạn 3 và cùng nói về cách bảng động hình thành.

**K2** — tạo biểu mẫu mới thì bảng đích ở đâu ra: tự sinh bảng mới, hay luôn phải
chọn bảng có sẵn.

**K3 và N8** — bảy nhãn ý nghĩa. `03-thiet-ke-ky-thuat.md` mục 2.5 ghi một danh
sách, bản dựng giao diện lại đề xuất một danh sách khác hẳn. Hai bên chưa thống nhất.

---

## Quyết định 1 — Biểu mẫu luôn chọn bảng có sẵn

Muốn có bảng thì tạo bảng trước, rồi mới tạo biểu mẫu ghi vào bảng đó. **Không
có đường tắt tự sinh bảng.**

### Lý do

**Một lối đi duy nhất.** Tự sinh bảng thêm một nhánh nữa vào màn hình vốn đã là
phần rủi ro nhất của dự án. Mỗi nhánh là một tổ hợp phải kiểm thử.

**Tránh bảng rác.** Tự sinh khiến mỗi lần thử tạo biểu mẫu lại đẻ ra một bảng.
Bảng động không xoá cứng được (BR-4), nên rác tích lại mãi.

**Ép người dùng nghĩ trước.** Bảng là nơi dữ liệu sống lâu dài, biểu mẫu chỉ là
cửa nhập. Tách hai bước làm rõ điều đó.

### Đánh đổi

Người dùng phải làm hai bước thay vì một. Chấp nhận được: Manager tạo bảng không
thường xuyên, và bước thêm này rẻ hơn nhiều so với dọn bảng rác về sau.

---

## Quyết định 2 — Bảy nhãn ý nghĩa theo `docs/03` mục 2.5

| Nhãn | Hệ thống dùng để |
|---|---|
| Ngày | Lọc theo khoảng thời gian |
| Khách hàng | Đếm khách mới, khách cũ |
| Số điện thoại | Phát hiện mua lại — FR-6.7 |
| Doanh thu | Cộng tổng, tính trung bình |
| Người bán | Thống kê theo nhân viên |
| Sản phẩm | Thống kê theo sản phẩm |
| Trạng thái | Lọc và đếm theo trạng thái |

### Lý do

**Nhãn nói về nghiệp vụ, không nói về kiểu dữ liệu.** Danh sách kia — Số lượng,
Tiền, Tỉ lệ, Người — mô tả *kiểu* của giá trị, mà kiểu đã có sẵn ở `FieldDef`.
Lặp lại là thừa. Danh sách này nói *giá trị đó đại diện cho cái gì trong nghiệp
vụ*, và đó mới là thứ báo cáo tổng hợp cần biết.

**Bám đúng yêu cầu đã có mã.** `Số điện thoại` phục vụ FR-6.7 nhận diện khách mua
lại. `Khách hàng` phục vụ đếm khách mới và cũ. Hai nhãn này không suy ra được từ
kiểu dữ liệu.

**Tài liệu thiết kế là nguồn chuẩn.** Bản dựng giao diện chỉ là bản vẽ; khi hai
bên vênh nhau thì lấy tài liệu.

### Đánh đổi

Bốn cách nhóm của báo cáo tổng hợp — tổng hợp, theo nhân viên, theo sản phẩm,
theo thị trường — thì nhãn `Người bán` và `Sản phẩm` phủ được hai cách. **Cách
nhóm theo thị trường chưa có nhãn tương ứng.** Câu N5 trong backlog cũng chưa
chốt thị trường là Quốc gia hay Bang. Khi trả lời N5 sẽ biết cần thêm nhãn
`Thị trường` hay dùng lại `Trạng thái`.

---

## Hệ quả

**Được gì**

- Giai đoạn 3 hết bị chặn, bắt đầu được ngay
- Trình tạo biểu mẫu chỉ có một lối đi, ít tổ hợp phải kiểm thử
- Nhãn ý nghĩa nối thẳng được với bốn cách nhóm của FR-5.1

**Mất gì**

- Tạo bảng mới mất hai bước
- Chưa phủ được cách nhóm theo thị trường

**Chỗ cần cẩn thận về sau**

- Bảy nhãn khai ở một chỗ duy nhất, trong `forms_builder/meaning.py`
- Cột có nhãn phải tách ra cột riêng có chỉ mục, không nằm trong JSON — nếu không
  thì lọc và thống kê sẽ chậm (ADR-001)
- Thêm nhãn thứ tám phải kèm tệp chuyển đổi cấu trúc, không sửa nóng

---

## Điều kiện xem lại

- Sau khi chốt N5 về thị trường, xem có cần thêm nhãn `Thị trường` không
- Nếu người dùng thật phàn nàn về hai bước tạo bảng nhiều hơn ba lần
