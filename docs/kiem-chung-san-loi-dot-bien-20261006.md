# Biên bản săn lỗi — Chất lượng bộ kiểm bằng đột biến tay (06.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Đợt săn lỗi, bước 7 (chủ dự án duyệt, làm trên nhánh `claude/san-loi-tiep`) |
| Câu hỏi | Bộ kiểm 2.900+ bài xanh — nhưng nếu ai đó vô tình làm hỏng một quy tắc quan trọng, có bài nào đỏ không? |
| Cách làm | Mỗi lần cố ý làm hỏng **một** chỗ (một dòng) trong một worktree riêng, chạy các gói bài liên quan với `-x`, ghi bài đầu tiên đỏ; xong trả lại mã. Không thêm thư viện (không dùng mutmut): script `dot_bien.py` trong thư mục nháp, chỉ dùng `pytest` |
| Mã | Worktree tại commit bước 6 (`2e56865`), DB kiểm thử riêng `test_knjsc_mut` |

## Kết quả

| # | Đột biến (cố ý làm hỏng) | Quy tắc | Kết quả | Bài bắt được |
|---|---|---|---|---|
| M1 | Phạm vi của Staff trả cả bảng | Cấm 3, 11 | Bắt được | `core/tests/test_permissions.py::test_xem_ban_ghi_ngoai_pham_vi_bi_tu_choi` |
| M2 | Lưới bỏ so phiên bản ô (CAS) | Bắt buộc 13 | Bắt được | `crm/tests/test_master_grid.py::test_same_cell_conflict_but_other_cell_survives` |
| M3 | Lưới gửi lặp không trả kết quả cũ | ADR-021 | Bắt được | `crm/tests/test_market_currency.py::test_grid_confirmation_preserves_amount_and_order_and_history` |
| M4 | Lưới bỏ kiểm dòng ngoài phạm vi | Cấm 3 | Bắt được | `crm/tests/test_master_grid.py::test_replay_revoked_scope_denied` |
| M5 | Biên nhận nộp luôn tạo mới | AC-4.12 | Bắt được | `reports/tests/test_nop_mot_lan.py` (bài của bước 1) |
| M6 | Excel xuất để nguyên công thức | AC-7.14 | Bắt được | `forms_builder/tests/test_xuat_khong_cong_thuc.py` (bài của bước 2) |
| M7 | Khoá đăng nhập sau 6 lần thay vì 5 | FR-1.2 | Bắt được | `org/tests/test_account.py::test_khoa_tam_sau_nam_lan_dang_nhap_sai` |
| M8 | Bỏ lọc bản ghi đã xoá mềm (`AliveManager`) | BR-4 | Bắt được | `documents/tests/test_tai_lieu.py::test_go_tai_lieu_theo_quyen` |
| M9 | Nhật ký hoạt động sửa được | BR-6 | Bắt được | `core/tests/test_audit.py::test_khong_sua_duoc_ban_ghi_nhat_ky` |
| M10 | `1.234` đọc thành 1,234 (dấu chấm ba số lẻ thành thập phân) | `parse_money` | Bắt được — **nhưng chỉ nhờ bài mới của bước 5** | `core/tests/test_so_va_gio_bien.py` |
| M10b | Như M10, bỏ bài mới của bước 5, chạy `core` + `forms_builder` | | **LỌT** | — |
| M11 | Đổi quyền không đá phiên cũ | P4, AC-1.6 | Bắt được | `core/tests/test_shared_login.py::test_shared_session_invalidated[epoch]` |
| M12 | Tải tệp xuất không kiểm lại quyền từng dòng | ADR-020 | Bắt được | `crm/tests/test_shared_integrity.py::test_generic_export_revocation_and_deleted_table` |
| M13 | Báo cáo cộng lẫn loại tiền | Bắt buộc 6, ADR-046 | Bắt được | `reports/tests/test_activity.py::test_day_blocks_have_day_subtotal_and_stt` |
| M14 | Chuẩn hoá NFC cả mật khẩu | AC-9.6 | Bắt được | `crm/tests/test_chu_viet_mot_dang.py::test_mat_khau_khong_bi_doi` (bài bước 4) |
| M15 | Xoá là xoá cứng | BR-4, cấm 4 | Bắt được | `core/tests/test_scope.py::test_ban_ghi_da_xoa_khong_con_trong_pham_vi` |
| M16 | Người đọc toàn công ty (CEO) sửa được dòng | ADR-020 | **LỌT** lúc đầu; nay bắt được | `crm/tests/test_ceo_chi_doc_luoi.py` (bài mới, AC-21.17) |
| M17 | Xuất Excel không ghi nhật ký | P5 | Bắt được | `forms_builder/tests/test_nhap_xuat.py::test_xuat_kem_bo_loc_va_sap_xep` |

## Nhận xét

- **Bộ kiểm canh tốt các quy tắc nền**: phạm vi quyền, CAS, xoá mềm, nhật ký, khoá đăng nhập, phiên, tiền tệ đều có
  bài đỏ ngay khi bị làm hỏng.
- **Lỗ hổng tìm được (M10b):** quy tắc đọc số kiểu Việt Nam của `parse_money` — "dấu chấm với ba chữ số sau là ngăn
  nghìn" — không có bài nào trong `core` và `forms_builder` canh trước đợt này. Làm hỏng nó thì người dùng gõ `1.234`
  sẽ lưu thành 1,234 (lệch nghìn lần) mà bộ kiểm vẫn xanh. Đã được lấp bằng
  `test_o_so_van_doc_dung_cach_viet_viet_nam` của bước 5 (7 cách viết: `1.234,5`, `1,234.5`, `1.234`, `150.00`,
  `-5.000`, `0`, `1 234 ₫`). Không cần sửa thêm.
- **Lỗ hổng thứ hai (M16):** bỏ dòng chặn CEO trong `grant_service.can_edit_visible_record` mà không bài nào đỏ.
  Truy tiếp: CEO không thuộc bộ phận nào thì các lớp khác vẫn chặn (đột biến vô hại ở đó), nhưng **CEO có hồ sơ gắn
  vào bộ phận Vận đơn** sẽ được quy tắc "bảng dùng chung, ai trong bộ phận cũng sửa" cho sửa — lưới hiện ô sửa được
  và ghi thành công. Mã hiện tại vẫn đúng (dòng chặn còn đó); chỉ thiếu bài canh. Đã thêm
  `test_ceo_xem_duoc_nhung_khong_sua_duoc_o_luoi` (hai trường hợp: không bộ phận, trong bộ phận Vận đơn); chạy lại đột
  biến: bị bắt.
- Bốn trên mười bảy đột biến chỉ bị bắt bởi bài viết trong chính đợt săn lỗi này (M5, M6, M10, M14):
  đúng ý của đợt — mỗi lỗi tìm ra để lại một bài canh.

## Chưa làm

- Đột biến tự động trên toàn bộ mã (mutmut, cosmic-ray): cần thêm thư viện và hàng giờ máy; chưa hỏi chủ dự án.
- Đột biến ở JS của lưới (`master-grid.js`): bài trình duyệt chạy lâu; để lượt sau.
