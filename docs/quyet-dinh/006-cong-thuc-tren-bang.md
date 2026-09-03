# ADR-006 — Bảng dữ liệu chỉ có cột tính sẵn, công thức tự do tách sang Bảng tính

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | 29.08.2026 |
| Người quyết định | (điền tên) |
| Liên quan | FR-7.8 · ADR-001 · ADR-002 · backlog K1 |

---

## Bối cảnh

`FR-7.8` nói *"hệ thống phải hỗ trợ công thức tính toán trên bảng"* nhưng để ngỏ
phạm vi, chuyển sang mục 11 của `02-yeu-cau-san-pham.md`. Đây là điểm chặn Giai
đoạn 3 — giai đoạn nặng nhất, trọng số 20 trên 100.

Câu hỏi: người dùng được tính toán tới mức nào trên bảng do họ tự tạo.

---

## Các lựa chọn đã cân nhắc

| Lựa chọn | Người dùng làm gì | Hệ thống lưu gì |
|---|---|---|
| **A — Cột tính sẵn** | Chọn phép tính từ danh sách khi tạo cột | Cấu trúc: `{phép tính, toán hạng}` |
| **B — Gõ công thức tự do** | Gõ `=D2/E2` vào từng ô, như Excel | Chuỗi công thức gắn với ô |
| **C — Tách chỗ** | Bảng dữ liệu dùng A; ai cần gõ tự do thì sang màn hình Bảng tính riêng | Cả hai, ở hai nơi khác nhau |

---

## Quyết định

**Chọn C.**

- **Bảng dữ liệu** — chỉ có cột tính sẵn. Công thức thuộc về cột, áp cho mọi dòng.
- **Bảng tính** — màn hình riêng, gõ công thức tự do thoải mái. Đọc từ bảng cố
  định, **không ghi ngược** (ranh giới đã có trong `kien-truc.md`).

---

## Lý do

### Bảng động không có ô A1

Theo ADR-001, bảng do người dùng tạo không sinh bảng vật lý; dữ liệu lưu dạng
bản ghi khoá–giá trị trong JSON. **Địa chỉ ô chỉ tồn tại lúc vẽ ra màn hình.**

```
Người dùng gõ  =D2/E2  khi bảng chưa sắp xếp
       ↓
Người khác bấm sắp xếp theo Ngày
       ↓
Dòng 2 giờ là bản ghi khác  →  công thức trỏ nhầm
```

Lọc, phân trang, thêm dòng — mỗi thao tác đều làm địa chỉ ô trỏ sang chỗ khác.
Cột tính sẵn nói *"mọi dòng: CPQC chia Số đơn"*, đúng bất kể sắp xếp thế nào.

### Công thức tự do mở lỗ hổng phân quyền

Manager gõ `=B15` vào một ô. Staff mở bảng đó và thấy kết quả — tức là thấy giá
trị của dòng 15, dòng nằm ngoài phạm vi quyền của họ. Muốn chặn thì phải tính
lại công thức riêng cho từng người xem, vừa chậm vừa phức tạp.

`04-tieu-chi-nghiem-thu.md` mục 13: *"Không bỏ qua tiêu chí phân quyền với lý do
sẽ sửa sau — dữ liệu đã lộ thì không thu hồi được."*

### Báo cáo tổng hợp không đọc được công thức tự do

Cột tính sẵn mang **nhãn ý nghĩa**, nên hệ thống biết cột đó là Doanh thu hay
Trạng thái và cộng đúng cách. Công thức gõ tay chỉ là một chuỗi — hệ thống không
biết kết quả mang nghĩa gì, nên `FR-5.1` không bao phủ được dữ liệu đó.

### Dữ liệu thật chỉ cần cột tính sẵn

Đã đọc cả bảy công thức trong `CRM_ Tân.xlsx`:

```
CPO            = CPQC / Số đơn
Giá Mess       = CPQC / Số Mess
CPQC/Doanh số  = CPQC / Doanh số
AOV            = Doanh số / Số đơn
Tỉ lệ chốt     = Số đơn / Số Mess      (ở ba sheet)
```

Cả bảy đều là phép chia giữa hai cột, áp cho toàn bộ cột. **Không có công thức
nào chỉ dùng cho riêng một ô.** Cột tính sẵn phủ hết nhu cầu thật đang có.

### Cách C không đắt hơn cách A

Màn hình Bảng tính vốn đã nằm trong phạm vi phase 1 — `README.md` hạng mục 5 và
`01-tong-quan-san-pham.md` mục 3.5. Chọn C chỉ là quyết định **công thức tự do
sống ở đâu**, không phải thêm phạm vi mới.

---

## Hệ quả

**Được gì**

- Bảng dữ liệu giữ được cấu trúc, nên báo cáo tổng hợp và phân quyền chạy đúng
- Người quen Excel vẫn có chỗ gõ tự do
- Người dùng không gõ sai cú pháp được trên bảng dữ liệu
- Giai đoạn 3 giữ đúng trọng số 20, không phồng lên

**Mất gì**

- Hai nơi để học thay vì một
- Số liệu tính trong Bảng tính không vào được báo cáo tổng hợp — đây là chủ ý,
  không phải thiếu sót
- Không làm được ngoại lệ cho từng dòng trên bảng dữ liệu

**Chỗ cần cẩn thận về sau**

- Danh sách phép tính của cột tính sẵn phải khai ở một chỗ duy nhất
- Cột tính sẵn phải tính lại khi cột nguồn đổi, và phải phát hiện tham chiếu vòng
- Không được để Bảng tính ghi ngược về bảng cố định, dù chỉ một trường hợp

---

## Điều kiện xem lại

Xem lại khi có một trong hai tình huống:

- Người dùng thật xin gõ công thức tự do trên bảng dữ liệu nhiều hơn ba lần, và
  lý do không giải quyết được bằng cột tính sẵn
- Xuất hiện nhu cầu tính toán tham chiếu chéo giữa hai bảng động
