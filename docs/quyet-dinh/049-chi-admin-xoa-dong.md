# ADR-049 — Chỉ Admin xoá dòng

| Mục | Nội dung |
|---|---|
| Ngày | 08.10.2026 |
| Trạng thái | Xong trên máy ảo 08.10.2026, PR nháp về `Staging`; chờ chủ dự án thử local rồi gộp |
| Thay thế / bổ sung | Thay luật xoá dòng của ADR-011 và backlog Q52 ("xoá = quyền sửa"); AC-11.21 (menu chuột phải của bộ lưới cũ, đã bỏ theo ADR-021) và ý "xoá dòng của người khác" trong AC-11.33. Bổ sung AC-6.12 (xoá dòng vận đơn thì bỏ đơn gốc) |

## Bối cảnh

Chủ dự án 08.10.2026: "tôi muốn làm chỉ có quản trị mới có khả năng xóa dòng". Hiện trạng lúc đó:

- **Lưới KN CRM không có nút xoá dòng bất kỳ.** Bộ lưới cũ có "Xoá N hàng" theo quyền sửa (AC-11.21). Lưới JSON (ADR-021)
  thay nó và tắt hai đường `xoa-dong/`, `khoi-phuc-dong/`: gọi vào trả 409, có bài kiểm giữ.
- **Ctrl+Z gỡ dòng vừa gõ** có trong mã. Nhưng bảng vận đơn không cho tạo dòng trên lưới (`protect_table`), nên trên KN CRM
  đường này không xảy ra.
- **Bỏ đơn** ở trang đơn gốc: người lên đơn tự bỏ được đơn của mình. Bỏ đơn xoá mềm cả dòng vận đơn đang chạy (AC-6.12).
- `grant_service.can_delete_record` bằng quyền sửa. Leader và Manager xoá được dòng của người khác (AC-11.33).

Chủ dự án chọn hai điều:
- **Thêm nút Xoá dòng cho Admin**: xoá mềm, khôi phục được, áp cho dòng bất kỳ; người khác không xoá được dòng.
- **Giữ Ctrl+Z gỡ dòng vừa gõ, khoá Bỏ đơn** (chỉ Admin).

## Quyết định

1. **Quyền xoá và khôi phục dòng: chỉ Admin.**
   - `grant_service.can_delete_record` = `is_admin` và `can_edit_record`. Vẫn giữ phạm vi dòng, bảng chỉ xem và báo cáo đã khoá.
   - Ở cấp bảng: `row_mutations.can_delete`, dùng cho lưới biết có hiện nút hay không.
2. **Đường ghi là `luu-json/`** như mọi lần ghi lưới, không mở lại hai đường cũ.
   - Hai loại lượt mới: `delete_rows` và `restore_rows`, mang `row_changes=[{id, action, version}]` và không kèm sửa ô.
   - Cả lượt dùng chung biên nhận chống gửi lặp và khoá dòng.
   - So phiên bản từng dòng (`updated_at`): một dòng vừa đổi thì cả lượt trả 409.
   - Xoá và khôi phục đi qua `record_service`:
     - dòng vận đơn kéo theo đơn gốc, có nhật ký (AC-6.12);
     - khôi phục khi mã đơn đã có dòng sống khác thì bị chặn (AC-36.11);
     - lịch sử dòng ghi cột `__row__`.
   - Vai khác gửi thẳng yêu cầu thì nhận 403. Nhật ký từ chối được ghi sau khi giao dịch của lượt đã huỷ, nên không bị mất.
3. **Lưới**:
   - Mục "Xoá dòng đang chọn" trong menu "…" chỉ render cho Admin; khối dữ liệu báo `capabilities.delete`.
   - Mục này áp cho các dòng trong vùng đang chọn. Bấm số dòng ở cột trái là chọn cả dòng; từ đợt này, Shift + bấm số dòng chọn liền nhiều dòng như Excel.
   - Hộp xác nhận nêu số dòng và báo đơn gốc cũng bị bỏ. Con trỏ đứng sẵn ở Huỷ.
   - Xoá xong là một bước hoàn tác: Ctrl+Z khôi phục, Ctrl+Y xoá lại.
   - Không dùng phím Ctrl+− vì trùng phím thu nhỏ của trình duyệt.
4. **Bỏ đơn: chỉ Admin.**
   - Quy tắc nằm ở `order_service.cancel_order`.
   - Trang đơn gốc chỉ hiện nút cho Admin. Người khác gửi thẳng yêu cầu thì bị từ chối, có nhật ký.
5. **Không đổi:** Ctrl+Z gỡ dòng vừa tạo; xoá mềm, không xoá cứng (BR-4); xoá cả bảng theo `lifecycle_service.can_delete` (bảng vận đơn vốn không xoá được).

## Hệ quả

- Sale, CSKH, Vận đơn, Kế toán, Leader, Manager và CEO đều không xoá được dòng nào. Muốn bỏ một đơn hay một dòng thì báo Admin.
- Bộ đếm: AC-21.18, AC-21.19, AC-6.13. Bài kiểm ở `crm/tests/test_chi_admin_xoa_dong.py`,
  `orders/tests/test_bo_don_chi_admin.py` và `tests/e2e/test_admin_xoa_dong.py`.
