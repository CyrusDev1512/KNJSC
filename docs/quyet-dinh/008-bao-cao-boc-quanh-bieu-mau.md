# ADR-008 — Báo cáo hằng ngày bọc quanh biểu mẫu, không tự giữ nội dung

| | |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | 29.08.2026 |
| Liên quan | FR-4.1 → FR-4.5 · BR-2 · ADR-001 · ADR-007 |

---

## Bối cảnh

Giai đoạn 3 đã dựng xong bộ máy biểu mẫu và bảng động: quản lý tự tạo biểu mẫu,
nối vào bảng đích, nhân viên điền và dữ liệu chảy vào `DataRecord`.

Giai đoạn 4 cần báo cáo hằng ngày. `docs/03` mục 2.2 liệt kê một bảng
*Báo cáo hằng ngày — người nộp, thời điểm nộp, nội dung*. Câu hỏi là chữ
**nội dung** đó lưu ở đâu.

---

## Các cách đã cân nhắc

| | Cách | Nội dung lưu ở đâu |
|---|---|---|
| A | Báo cáo tự giữ nội dung | Một cột JSON riêng trên `DailyReport` |
| B | Báo cáo bọc quanh biểu mẫu | `DataRecord` như mọi dòng dữ liệu khác |
| C | Model cố định cho từng bộ phận | Ba bảng vật lý, mỗi bộ phận một bảng |

---

## Quyết định

**Chọn cách B.** `DailyReport` chỉ giữ bốn thứ mà bảng động không có:

```
ai nộp  ·  báo cáo cho ngày nào  ·  nộp lúc mấy giờ  ·  đã khoá chưa
```

Nội dung nằm trong `DataRecord` do biểu mẫu sinh ra.

---

## Vì sao

**FR-4.1 chính là `FormDef.department`.** Yêu cầu *"mỗi bộ phận phải có biểu mẫu
báo cáo riêng"* đã được Giai đoạn 3 giải xong. Viết lại nó lần nữa là làm hai
lần một việc.

**Báo cáo tự vào được báo cáo tổng hợp.** Giai đoạn 6 cộng số liệu dựa trên
nhãn ý nghĩa của cột (ADR-001). Nội dung nằm trong `DataRecord` thì báo cáo
hằng ngày tự động vào được thống kê, không phải viết đường ống thứ hai.

**Cách A tạo chỗ thứ hai lưu dữ liệu người dùng nhập.** Sẽ có hai bộ quy tắc
kiểm kiểu, hai đường tính thống kê, hai chỗ áp phạm vi quyền — đúng thứ điều
cấm 1 và 11 muốn ngăn.

**Cách C chết ngay khi khách hàng đổi mẫu báo cáo.** Thêm một trường là phải
sửa mã nguồn và chạy tệp chuyển đổi cấu trúc — trái hẳn FR-8.1.

---

## Hệ quả

**Được gì**

- Cột tính sẵn chạy sẵn cho báo cáo: CPO, tỉ lệ chốt tự tính, không viết thêm dòng nào
- Báo cáo hiện luôn trên màn hình bảng dữ liệu, cùng chỗ với mọi dữ liệu khác
- Phạm vi quyền, xoá mềm, nhật ký đều dùng lại nguyên vẹn

**Mất gì**

- Bỏ một báo cáo phải xoá mềm **hai** bản ghi: `DailyReport` và `DataRecord`.
  Quên một cái là dòng mồ côi còn nằm trên bảng
- Báo cáo phụ thuộc vào biểu mẫu. Quản lý sửa biểu mẫu thì báo cáo **cũ vẫn
  nguyên** (dữ liệu khoá theo tên cột, không theo trường biểu mẫu — FR-8.5),
  nhưng báo cáo mới sẽ khác cấu trúc báo cáo cũ

**Phải giữ**

- **Nộp xong là khoá.** BR-2 và FR-4.4. Chặn ở ba tầng: không có view sửa,
  `DailyReport.save()` nổ khi sửa bản đã có, và ràng buộc duy nhất trong cơ sở
  dữ liệu chặn nộp đè
- Không thêm hàm sửa vào `daily_service`. Thiếu hàm là cách chặn chắc nhất
- Bỏ báo cáo phải xoá mềm cả `DataRecord` đi kèm
