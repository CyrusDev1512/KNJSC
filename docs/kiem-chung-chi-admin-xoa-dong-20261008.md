# Biên bản — Chỉ Admin xoá dòng (08.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 08.10.2026: "tôi muốn làm chỉ có quản trị mới có khả năng xóa dòng". Hai lựa chọn: thêm nút Xoá dòng cho Admin (xoá mềm, khôi phục được, dòng bất kỳ); giữ Ctrl+Z gỡ dòng vừa gõ, khoá Bỏ đơn |
| Quyết định | [ADR-049](quyet-dinh/049-chi-admin-xoa-dong.md) |
| Nhánh | `claude/chi-admin-xoa-dong` từ `Staging` `4419643`, PR nháp về `Staging` |
| Tiêu chí | AC-21.18, AC-21.19, AC-6.13; sửa câu chữ AC-11.21, AC-11.33, AC-6.12 |
| Môi trường | Máy ảo; Postgres 16; Redis; Playwright Chromium; hệ thống thật `runserver` 8020/8021 trên DB thử 385.034 dòng Vận đơn |

## 1. Đã đổi

| Chỗ | Trước | Sau |
|---|---|---|
| Nút xoá dòng trên lưới | Không có (hai đường cũ `xoa-dong/`, `khoi-phuc-dong/` đã tắt, trả 409) | Admin có "Xoá dòng đang chọn" trong menu "…": hộp xác nhận, con trỏ đứng ở Huỷ, Ctrl+Z khôi phục, Ctrl+Y xoá lại |
| Quyền xoá dòng (`can_delete_record`) | Bằng quyền sửa: Leader, Manager xoá được dòng người khác | Chỉ Admin |
| Đường ghi | — | `luu-json/` với lượt `delete_rows`/`restore_rows`: biên nhận chống gửi lặp, so phiên bản từng dòng, cả lượt cùng thành công hoặc cùng huỷ |
| Vai khác gửi thẳng lượt xoá | — | 403, có nhật ký từ chối |
| Bỏ đơn | Người lên đơn tự bỏ đơn mình | Chỉ Admin, quy tắc nằm ở `order_service.cancel_order`; trang đơn chỉ hiện nút cho Admin; người khác gửi thẳng yêu cầu thì bị từ chối, có nhật ký |
| Shift + bấm số dòng | Chỉ chọn một dòng | Chọn liền nhiều dòng như Excel |

Hai chỗ khác với kế hoạch:
- **Ctrl+Z gỡ dòng vừa gõ không đổi gì.** Bảng vận đơn vốn không cho tạo dòng trên lưới (`protect_table`), nên trên KN CRM đường này không xảy ra.
- **Không làm phím Ctrl+−** như Excel, vì trùng phím thu nhỏ trang của trình duyệt.

## 2. Bài kiểm

| Bài | Kiểm gì |
|---|---|
| `crm/tests/test_chi_admin_xoa_dong.py` (15 bài) | Admin xoá: dòng xoá mềm, ghi người xoá, đơn gốc bị bỏ, có nhật ký, lịch sử `__row__`, tổng giảm. Khôi phục bằng phiên bản trả về thì dòng và đơn sống lại. Chín vai bị 403 có nhật ký, cả xoá lẫn khôi phục: Staff, Leader, Manager Vận đơn; người lên đơn; Leader, Manager Sale; CSKH phụ trách; Kế toán; CEO. `capabilities.delete` chỉ đúng với Admin. Một dòng lệch phiên bản thì 409 và không dòng nào bị xoá. Gửi lại cùng mã thao tác thì không xoá lần hai. Khôi phục khi mã đơn đã có dòng sống thì 400 nêu mã. Lượt kèm sửa ô hay sai hành động thì 400 |
| `orders/tests/test_bo_don_chi_admin.py` | Người lên đơn và Manager Sale không thấy nút; gửi thẳng thì bị từ chối có nhật ký, đơn và dòng còn nguyên. Tầng dịch vụ từ chối. Admin thấy nút và bỏ được |
| `tests/e2e/test_admin_xoa_dong.py` (2 bài) | Admin: chọn 2 dòng, Shift+bấm, Xoá dòng; hộp báo "2", con trỏ ở Huỷ; tổng 3 → 1; Ctrl+Z về 3. Staff Vận đơn không có mục, không có hộp |
| Sáu bài cũ đổi theo luật mới | `test_len_don` (AC-9.1, Manager không bỏ được đơn), `test_xoa_dong_huy_don`, `test_order_code_concurrency`, `test_van_hoa`, `test_order_consolidation`. Các bài này dùng Bỏ đơn để dựng tiền đề, nay bỏ bằng Admin |

## 3. Kiểm toàn phần

| Lượt | Kết quả |
|---|---|
| `pytest -m "not trinh_duyet"`, **tắt Redis** (như CI) | 3.124 đạt, 7 bỏ qua, 0 đỏ |
| Bài trình duyệt lượt 1 (`tests/e2e`) | 55 đạt, 9 đỏ — đúng 9 bài `test_pha_luoi_ghi_chu` lỗi chứng chỉ Google Fonts của máy ảo (`ERR_CERT_AUTHORITY_INVALID`), như `Staging` |
| Bài trình duyệt lượt 2 | 19 đạt, 9 bỏ qua |
| `tests/test_truy_vet.py` | 36 đạt; bộ đếm docs/06: 367 tiêu chí, 331 trên 354 tự động có bài |

## 4. Đi thử trên hệ thống thật (385.034 dòng)

| Bước | Kết quả |
|---|---|
| `quantri` chọn 2 dòng → Xoá dòng | Đạt: hộp báo 2 dòng; tổng 385.034 → 385.032; thông báo "Đã xoá 2 dòng. Ctrl+Z để khôi phục." |
| Ctrl+Z | Đạt: tổng về 385.034; DB: hai dòng `MAU-20260910-0001`, `-0002` sống lại; nhật ký có hai dòng xoá và hai dòng khôi phục |
| `vd.staff` mở menu "…" | Đạt: không có mục Xoá dòng |

## Chưa kiểm

- Hai dòng thử trên DB 385k là dòng mẫu, không có đơn gốc. Phần đơn gốc bị bỏ và sống lại mới kiểm bằng bài tự động và bài trình duyệt, chưa đi tay.
- Chưa thử trên máy Windows của chủ dự án và trên VPS.
