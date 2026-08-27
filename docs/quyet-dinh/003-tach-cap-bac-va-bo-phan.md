# ADR-003 — Cấp bậc và bộ phận là hai cột riêng

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã áp dụng |
| Ngày | (điền ngày) |
| Người quyết định | (điền tên) |

---

## Bối cảnh

Hệ thống có ba bộ phận — Sale, Marketing, Vận đơn — và ba cấp bậc — Staff, Leader, Manager.

Cách phổ biến là gộp thành một cột `role` với các giá trị như `sale_staff`, `sale_leader`, `marketing_manager`. Nhiều hệ thống làm vậy vì đơn giản lúc đầu.

Câu hỏi: gộp hay tách?

---

## Các lựa chọn đã cân nhắc

| Lựa chọn | Ưu | Nhược |
|---|---|---|
| **A — Một cột `role`** | Đơn giản · Một lần kiểm là biết người đó là ai | Số giá trị nhân lên theo tích: 3 bộ phận × 3 cấp = 9 giá trị · Thêm bộ phận thứ tư thành 12 · Không lọc được theo một chiều |
| **B — Hai cột riêng** | Thêm bộ phận chỉ là thêm một dòng dữ liệu · Lọc được theo từng chiều · Phân quyền diễn đạt tự nhiên | Phải kiểm hai cột thay vì một |

---

## Quyết định

**Chọn B — hai cột riêng.**

```
bo_phan   →  Sale · Marketing · Vận đơn
cap_bac   →  Staff · Leader · Manager
```

Hàm phạm vi dùng cả hai:

```
pham_vi(nguoi_dung):
    Staff    →  chỉ bản ghi do chính người đó tạo
    Leader   →  toàn bộ team người đó phụ trách
    Manager  →  toàn bộ bộ phận của người đó
```

Cấp bậc quyết định **phạm vi rộng bao nhiêu**. Bộ phận quyết định **phạm vi ở đâu**.

---

## Lý do

**Hai chiều độc lập nhau.** Một người có thể là Leader ở Sale hôm nay, Leader ở Marketing tháng sau. Cấp bậc không đổi, bộ phận đổi. Với một cột `role` thì phải đổi cả chuỗi và mọi chỗ kiểm quyền phải biết chuỗi mới.

**Số giá trị tăng theo tích, không theo tổng.** Ba bộ phận ba cấp là chín giá trị. Thêm bộ phận Kế toán thành mười hai. Thêm cấp bậc Phó phòng thành mười sáu. Với hai cột thì chỉ thêm một dòng dữ liệu.

**Lọc theo một chiều là nhu cầu thật.** Báo cáo tổng hợp cần nhóm theo bộ phận, không quan tâm cấp bậc. Danh sách phê duyệt cần lọc theo cấp bậc, không quan tâm bộ phận. Với một cột `role` thì phải phân tích chuỗi để lấy ra từng phần.

---

## Hệ quả

**Được gì**

- Thêm bộ phận mới không cần sửa mã nguồn
- Thêm cấp bậc mới không nhân số giá trị lên
- Lọc và thống kê theo từng chiều
- Phân quyền diễn đạt tự nhiên: cấp bậc quyết định phạm vi, bộ phận quyết định vị trí

**Mất gì**

- Mỗi lần kiểm quyền phải đọc hai trường thay vì một
- Cần một hàm phạm vi tập trung, không kiểm rải rác

**Chỗ cần cẩn thận về sau**

- Không được thêm trường thứ ba kiểu `is_admin` bên cạnh — nó phá vỡ mô hình hai chiều
- Người có quyền vượt bộ phận, ví dụ chủ doanh nghiệp, xử lý bằng cấp bậc riêng chứ không phải cột thứ ba
- Mọi truy vấn dữ liệu phải đi qua hàm phạm vi, không viết điều kiện lọc rải rác ở từng màn hình

---

## Điều kiện xem lại

Xem lại khi xuất hiện một trong hai tình huống:

- Có người thuộc nhiều bộ phận cùng lúc
- Có nhu cầu cấp quyền theo từng chức năng, không theo cấp bậc

Tình huống thứ hai đã được chuẩn bị sẵn: hàm phạm vi thiết kế để cộng thêm phần được cấp riêng, phase 1 phần đó luôn rỗng.
