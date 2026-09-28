# Kiểm chứng — "Khách mua lại" theo bảng tính và ô ngày tự chèn "/" — 28.09.2026

Nhánh `claude/mua-lai-va-o-ngay` tách từ `main` (`a0313be`), máy ảo Claude Code, PostgreSQL 16.
Chủ dự án báo ba việc, chốt làm việc 2 và 3 trước; việc 1 (đảo thứ tự tải lại trang) ghi TL-62, để lượt sau.

## Việc 2 — Lên đơn báo "khách mua lại" dù số không còn trên bảng tính (TL-61)

**Nguyên nhân.** `order_service.customer_notice` đếm **đơn hàng** của khách (`Customer.order_count`).
Hai đường làm đơn "ma" vẫn bị đếm:

- Xoá dòng trên lưới chỉ xoá mềm dòng (`DataRecord`), đơn hàng gắn với dòng vẫn sống.
- Lệnh `xoa_bang_van_don_cu` (xoá cứng crmThuận, Vận đơn DB) giữ đơn hàng và chỉ cắt liên kết
  (`Order.record = None`), nên mọi khách của hai bảng đó vẫn bị báo mua lại.

Tái hiện trước khi sửa (bài tạm, đã xoá): xoá dòng duy nhất của số `0900000000` → lưới còn 0 dòng,
Lên đơn vẫn "mua_lai=True, so_don_cu=1".

**Sửa.** `dispatch_service.rows_with_phone(phone, before=None)` đếm dòng **đang sống** trên bảng vận đơn
cùng khoá 9 số cuối (`forms_builder.models.phone_key`) — cùng thước đo cột Trùng của lưới.
`customer_notice` và cột "Mua lại lần" (`_lan_mua`) dùng chung hàm này. Số chỉ có trên bảng (nhập
thẳng, chưa có hồ sơ khách) nay cũng được báo; template `_nhac_khach.html` không in dòng tên khi chưa
có hồ sơ. Không migration, không xoá dữ liệu; đơn hàng và hồ sơ khách giữ nguyên.

| Bài (AC-6.8) | Trước sửa | Sau sửa |
|---|---|---|
| `test_mua_lai_dem_theo_dong_con_tren_bang_van_don` | **đỏ**: xoá dòng xong vẫn "dòng đã xoá khỏi lưới vẫn bị tính" | xanh: xoá dòng → không báo; đơn bảng cũ mất liên kết → không báo; dòng nhập thẳng `+84 900 111 222` → báo, 1 dòng |
| `test_cot_mua_lai_lan_khong_tinh_dong_da_xoa` | **đỏ**: đơn sau khi đơn trước đã xoá ghi "Mua lại lần 2" | xanh: lần 1, rồi lần 2; dựng lại giá trị không tự đếm chính mình |
| `orders/tests/test_len_don.py`, `crm/tests/test_bang_tinh.py`, `crm/tests/test_waybill_new.py`, `orders/tests/test_nap_khach_mau.py` | — | **79 đạt, 0 đỏ** (gồm các bài AC-6.8, AC-6.10, Q25 cũ) |

## Việc 3 — Ô Từ ngày / Đến ngày tự chèn "/" (AC-32.1)

**Trước.** `date-inputs.js` chỉ nhận đúng `D/M/YYYY`; gõ `03 09 2026` hay `03092026` bị báo sai định dạng.

**Sửa.** Trong `date-inputs.js` (mọi ô ngày ERP/CRM và ô ngày trên lưới CRM đều dùng chung), với ô
ngày không kèm giờ: khi đang gõ ở cuối ô thì dấu cách/chấm/gạch ngang thành "/", đủ 2 số ngày và 2 số
tháng thì chèn "/", gõ liền 8 số thành `DD/MM/YYYY`; Backspace/Delete để yên; rời ô thì thêm số 0
(`3/9/2026` → `03/09/2026`). Ô ngày giờ không đổi. Giá trị gửi đi vẫn là ISO.

| Bài | Trước sửa | Sau sửa |
|---|---|---|
| `tests/e2e/test_o_ngay_tu_dinh_dang.py` (AC-32.1, Chromium thật, ô Từ ngày của Tổng quan, gõ phím thật) | **đỏ**: `03 09 2026` giữ nguyên, không hợp lệ | xanh: `03 09 2026`, `03092026`, `03.09.2026`, `03-09-2026` → `03/09/2026` (ISO `2026-09-03`); `03` → `03/`; `0309` → `03/09/`; Backspace sau `03/` còn `03`; `3/9/2026` + Tab → `03/09/2026`; `31022026` vẫn báo sai |
| `scripts/kiem-thu-date-inputs.cjs` (node) | — | đạt: ngày hợp lệ, năm nhuận, ngày sai, round-trip ISO, ô nháp lưới |
| `reports/tests/test_bo_cuc_bao_cao_e2e.py` | — | 2 đạt |

## Chung

| Bài | Kết quả |
|---|---|
| `tests/test_truy_vet.py` (docs/06 → 278 / 265 tự động / 242 có bài) | 36 đạt |
| Suite đầy đủ `-m "not trinh_duyet and not cham"` | **2.802 đạt, 1 bỏ qua, 0 đỏ** (365 s) |

**Đỏ do môi trường, không do nhánh:** 3 bài `crm/tests/test_luoi_dong_trong_va_ghim_e2e.py` đỏ trên máy ảo;
đối chứng `git stash` trên `main` chưa sửa đỏ y hệt (3/3) — lưới không tải trong máy ảo; trên CI bộ
e2e vẫn xanh. Gộp nhiều tệp trình duyệt vào một lượt pytest thì hai kiểu mở Playwright đụng nhau lúc
khởi tạo — chạy tách từng tệp.

## Chưa kiểm

- Ô ngày trên lưới CRM (cùng mã) chưa có bài trình duyệt riêng; kiểm bằng tay khi test local.
- TL-62 (đảo thứ tự tải lại trang) chưa làm.
- Chưa phát hành VPS.
