# Biên bản kiểm chứng — Delete xoá được ô Sản phẩm, Bỏ dòng xoá được dòng cuối (02.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án: "ấn delete thì xoá được luôn ô sản phẩm + ấn bỏ dòng cũng xoá được"; duyệt mockup 02.10.2026 |
| Quyết định | [ADR-036 bổ sung 02.10](quyet-dinh/036-mot-bang-van-don-duy-nhat.md) |
| Tiêu chí | AC-36.9, AC-36.10 |
| Nhánh | `claude/xoa-o-san-pham-bo-dong` từ `Staging` `fd08cb3`, PR nháp về `Staging` |
| Môi trường | Máy ảo Claude Code trên web: Python 3, PostgreSQL 16 cục bộ, Chromium Playwright có sẵn |

## Đã đo

| Kiểm | Lệnh (từ `app/`) | Kết quả |
|---|---|---|
| Bài mới trên mã cũ | `python -m pytest crm/tests/test_xoa_chi_tiet_san_pham.py` | 9/9 **đỏ** đúng chỗ: chưa có `bo-chi-tiet/`, `update_items` từ chối danh sách rỗng ("Cần từ 1 đến 200 dòng"), Lên đơn chưa báo "ít nhất 1 sản phẩm" |
| Bài mới sau sửa | như trên | 9/9 đạt: Vận đơn Staff/Leader/Manager bỏ được; quyền Xem và Sale ngoài phạm vi 403, chưa đăng nhập 302, không đổi; giá trị cũ lệch 409; cột Ghi chú hay gói rỗng 400 |
| Trình duyệt | `python -m pytest tests/e2e/test_xoa_chi_tiet_san_pham_e2e.py` | 2/2 đạt, chạy 3 lần đều đạt: Delete ô Sản phẩm → hộp hỏi lại, Huỷ không đổi; bôi đen Sản phẩm → Số lượng (có Chi tiết số nhà) → "Bỏ chi tiết và xoá" → ô Sản phẩm trống, chi tiết 0, Chi tiết số nhà trống, thông báo "Đã bỏ chi tiết sản phẩm của 1 dòng"; hộp Chi tiết Bỏ dòng hai lần → không còn dòng, Thêm dòng thêm lại được, Lưu → đơn không còn sản phẩm, mở lại vẫn có một dòng chọn sản phẩm trống như cũ; không lỗi JS |
| Ảnh màn hình | `storage/e2e/xoa-chi-tiet-hoi-lai.png`, `bo-dong-cuoi.png` (1366×800) | Hộp hỏi lại và dòng trống đúng mockup |
| Toàn bộ | `python -m pytest -m "not trinh_duyet and not cham"` | **2.887 đạt, 1 bỏ qua, 0 đỏ** (sau lượt kiểm toàn diện) |

## Kiểm toàn diện — đóng vai người dùng (02.10.2026, trước khi gộp `Staging`)

Rà mã theo thao tác dễ sai, thấy và sửa hai lỗi trước khi gộp:

| Lỗi tìm thấy | Hậu quả nếu để | Sửa |
|---|---|---|
| Mở Chi tiết đơn nhập từ tệp (dòng chọn trống), lỡ bấm Lưu | Mất chữ sản phẩm và tổng tiền, không hỏi | Dòng chưa chọn sản phẩm → báo lỗi như bản cũ, không đổi gì |
| Hộp hỏi lại của Delete đặt con trỏ ở "Bỏ chi tiết và xoá" | Ấn Delete rồi Enter theo thói quen là mất chi tiết | Con trỏ đứng ở Huỷ |

Bài thêm, đều đạt:

| Tình huống | Bài |
|---|---|
| Delete rồi Enter / Esc / × → không mất gì | `test_delete_roi_enter_hay_esc_khong_mat_gi` |
| "Chỉ xoá ô thường" (vùng có Quốc gia, bấm OK hộp "Loại tiền sẽ trống") → sản phẩm giữ; Ctrl+Z trả ô thường | `test_chi_xoa_o_thuong_va_ctrl_z` |
| Bôi đen ba dòng, một dòng đã trống → hộp đếm 2, bỏ cả | `test_nhieu_dong_mot_lan_va_dong_da_trong` |
| Người khác sửa đơn khi đang mở hộp → báo, không bỏ | `test_nguoi_khac_vua_sua_thi_bao_khong_bo` |
| Bỏ xong mở Chi tiết, lỡ Lưu → báo; chọn lại sản phẩm → ô hiện lại | `test_bo_xong_mo_chi_tiet_chon_lai_san_pham` |
| Đơn nhập tệp lỡ bấm Lưu → giữ chữ và tiền; Bỏ dòng rồi Lưu → trống | `test_don_nhap_tep_lo_bam_luu_khong_mat_chu` |
| Lên đơn không đổi: Bỏ dòng ở dòng duy nhất không mất, lên đơn hai sản phẩm | `test_len_don_khong_doi` |
| Quyền bỏ chi tiết trùng quyền sửa ô thường ở 6 vai (Vận đơn, Sale lên đơn, Admin được; Sale khác, MKT, Manager Sale 403) | `test_quyen_bo_chi_tiet_trung_quyen_sua_o_thuong` |
| Sau khi bỏ: lưới, Thống kê, Excel, Báo cáo tổng hợp ERP và Bảng dữ liệu vẫn mở | `test_sau_khi_bo_luoi_thong_ke_excel_van_chay`, `test_bao_cao_tong_hop_erp_van_mo_sau_khi_bo` |

Bài trình duyệt của tác vụ: 9/9 đạt, chạy 3 lần liền đều đạt. Toàn bộ bài trình duyệt chạy chung một mạch: các bài
lưới, báo cáo, ô nhập số chạy lại riêng từng tệp đều đạt; ba bài `test_pha_luoi_ghi_chu.py` đỏ vì máy ảo không tải
được font ngoài (`ERR_CERT_AUTHORITY_INVALID`, chứng chỉ proxy của máy ảo), không do mã; CI GitHub chạy các bài này.

## Chưa kiểm / để lại

- Chưa chạy trên máy chủ dự án và VPS (Claude Code trên web không tới được); chặng 2 là chủ dự án thử tay ở local.
- Cột số lượng theo sản phẩm `sl_*` (ẩn mặc định) vẫn chỉ ghi lúc lên đơn, như khi sửa Chi tiết; bỏ chi tiết
  không xoá nó.
- Bỏ chi tiết không vào lịch sử ô của lưới (`GridCellHistory`); dấu vết ở nhật ký hoạt động.
