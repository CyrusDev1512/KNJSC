# Biên bản kiểm chứng — Lời báo mất mạng không còn bị tra khách xoá oan (AC-10.12, TL-100), 14.10.2026

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 14.10: "sửa luôn lỗi AC-10.12 đi". Lỗi lộ ra khi CI `Staging` `f5c888e` đỏ sau lúc gộp KN OMS ([comment trên #114](https://github.com/CyrusDev1512/KNJSC/pull/114#issuecomment-6160951331)) |
| Phạm vi | `static/js/loi-mang.js`: thêm một hàm, đổi ba chỗ gọi. `tests/e2e/test_mat_mang_e2e.py`: thêm một bài, sửa một chú thích sai. Thêm tài liệu. Không model, không migration, không đổi quyền hay luồng thao tác |
| Nhánh | `claude/sua-loi-mang-ac-10-12`, tách từ `Staging` `f5c888e` |
| Môi trường | Máy ảo Claude Code trên web: Python 3.11.15 (CI 3.12), Django 5.2.17, PostgreSQL 16.13, Chromium của Playwright 1.56. Hệ thống thật: CRM `runserver` 8021 trên DB `knjsc_ht` |
| Kết luận | **Đạt.** Còn chờ CI của PR và chặng 2 ở máy chủ dự án |

## 1. Lỗi và gốc

- **Lỗi:** bấm Lưu đơn lúc mất mạng có khi mất lời báo "Mất kết nối mạng…", dù đơn chưa lưu. Người dùng tưởng đơn đã
  lưu, đúng điều AC-10.12 muốn chặn.
- **Gốc:**
  - Ô `phone` và `customer_name` của Lên đơn tra khách bằng `hx-get` với `hx-trigger="change, keyup changed delay:600ms"`
    (`crm/waybill_forms.py`).
  - Bấm nút thì ô điện thoại mất focus, nên `change` chạy tra khách (GET) cùng lúc với Lưu đơn (POST). Mất mạng thì cả
    hai cùng hỏng.
  - `loi-mang.js` chỉ nhớ phần tử hỏng **sau cùng** (`hong`) và tắt lời báo khi chính phần tử đó gửi lại thành công. Nếu
    tra khách hỏng tới sau, `hong` là ô điện thoại, và lần tra khách thành công kế tiếp tắt lời báo.
- **Vì sao lúc đỏ lúc không:** thứ tự hai lỗi mạng không cố định. Trên máy ảo và ở CI của #114, Lưu đơn thường hỏng sau.
  Ở lượt chạy lại trên CI `Staging`, thứ tự đảo.
- **Chú thích sai ở bài cũ:** chú thích ghi "tra khách lần đầu chạy xong lúc còn mạng". Thực ra `fill` không phát `change`,
  nên lần tra theo số chỉ chạy khi bấm nút, lúc đã mất mạng.

## 2. Sửa

- **`loi-mang.js`:** thêm hàm `nhoHong(e)`.
  - Một yêu cầu GET hỏng **không** giành chỗ của phần tử đang hỏng, nếu phần tử đó còn trên trang.
  - Các trường hợp khác như cũ: yêu cầu ghi hỏng luôn được nhớ; chưa có gì hỏng thì yêu cầu nào hỏng cũng được nhớ.
  - Dùng ở `htmx:sendError`, `htmx:timeout`, `htmx:responseError` (mã ≥ 500).
- **Luật tắt lời báo không đổi:** người dùng đóng, phần tử đó gửi lại thành công, hoặc phần tử đó không còn trên trang.
- **Bài mới `test_loi_bao_con_khi_tra_khach_hong_sau_luu_don`:**
  - Ghi thứ tự các lần `htmx:sendError` bằng một init script.
  - Ép thứ tự xấu: mất mạng, Lưu đơn hỏng; rồi còn mất mạng thì phát `change` ở ô điện thoại để tra khách hỏng **sau**.
  - Có mạng lại, tra khách số mới thành công: lời báo phải còn, chưa có đơn.
  - Lưu đơn thành công: lời báo tắt, ra đúng một đơn.

## 3. Kiểm

| Kiểm | Kết quả |
|---|---|
| Bài mới trên mã cũ (bài đỏ trước) | **Đỏ** đúng chỗ: lời báo biến mất. Thứ tự lỗi ghi được: `phone, form, phone` |
| `tests/e2e/test_mat_mang_e2e.py` sau khi vá (4 bài), 5 lần liền | **4/4 đạt cả 5 lần** (23–25 giây mỗi lần) |
| Dựng lại trên hệ thống thật (`sale.staff`, CRM 8021): Lưu đơn hỏng, tra khách hỏng sau, có mạng lại rồi tra khách thành công | Mã `Staging`: lời báo **mất** (False). Nhánh này: lời báo **còn** (True) |
| `node --check static/js/loi-mang.js` | Đạt |
| Bộ chính như CI: `pytest -m "not trinh_duyet" -rs` | **3.207 đạt, 7 bỏ qua, 0 đỏ** (111 bài trình duyệt tách riêng, thêm đúng bài mới), 8 phút 21 giây |
| e2e lượt 1 như CI: `pytest tests/e2e -m trinh_duyet -vv -rs -o faulthandler_timeout=120` | 69 đạt (thêm bài mới), 2 bỏ qua, 9 đỏ, 6 phút 33 giây. 9 bài đỏ đúng là 9 bài của `test_pha_luoi_ghi_chu.py`: font Google qua proxy máy ảo, đỏ y hệt trên `Staging` gốc (biên bản gộp KN OMS 14.10). Không có lỗi nào khác. Bốn bài mất mạng đạt |
| e2e lượt 2 như CI: `pytest -m trinh_duyet --ignore=tests/e2e -vv -rs -o faulthandler_timeout=120` | **22 đạt, 9 bỏ qua, 0 đỏ**, 3 phút 9 giây |

## 4. Chưa kiểm, còn mở

- **Máy CI chậm:** đó là nơi bài cũ đỏ. Kết quả xem ở CI của PR này.
- **TL-71:** bài đo lưới 1000 dòng treo ở lượt 1 của cùng CI `Staging`. Chưa sửa, gốc chưa rõ; số chẩn đoán ghi ở
  `docs/test-log.md`.
- **Chặng 2:** chủ dự án thử ở máy mình. Cách thử: bấm Lưu đơn lúc tắt mạng, bật lại mạng rồi sửa số điện thoại. Lời báo
  phải còn tới khi Lưu đơn thành công.
