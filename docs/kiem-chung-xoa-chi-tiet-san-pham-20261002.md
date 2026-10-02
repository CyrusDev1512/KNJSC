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
| Toàn bộ | `python -m pytest -m "not trinh_duyet and not cham"` | 2.872 bài: **0 đỏ, 0 lỗi** (thoát mã 0) |

## Chưa kiểm / để lại

- Chưa chạy trên máy chủ dự án và VPS (Claude Code trên web không tới được); chặng 2 là chủ dự án thử tay ở local.
- Cột số lượng theo sản phẩm `sl_*` (ẩn mặc định) vẫn chỉ ghi lúc lên đơn, như khi sửa Chi tiết; bỏ chi tiết
  không xoá nó.
- Bỏ chi tiết không vào lịch sử ô của lưới (`GridCellHistory`); dấu vết ở nhật ký hoạt động.
