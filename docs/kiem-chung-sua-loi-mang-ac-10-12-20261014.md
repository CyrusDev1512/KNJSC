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

## 5. Kiểm trước khi gộp (chủ dự án: "test kĩ rồi gộp #128 vào staging")

Kiểm trên đầu nhánh `09f3559`. Gộp thử `Staging` `f5c888e` với #128 bằng `--no-ff` thì ra cây `e967a34`, trùng đúng cây
của #128.

`loi-mang.js` được nạp ở cả bốn khung trang của KN ERP và KN CRM, nên phần kiểm không chỉ dừng ở Lên đơn.

| Kiểm | Kết quả |
|---|---|
| `node --check`, `git diff --check`, `check` với settings test, dev, bangtinh, `makemigrations --check`; rà diff | 0 lỗi; "No changes detected". Không có khoá, IP, thư viện mới hay migration |
| `test_mat_mang_e2e.py` 10 lần liền | **4/4 cả 10 lần** (28–35 giây mỗi lần) |
| Cùng tệp đó, 5 lần trong lúc máy bận: 3 tiến trình vòng lặp chiếm 3/4 nhân, tải trung bình 4,1. Đây là cách giả máy CI chậm, nơi bài cũ từng đỏ | **4/4 cả 5 lần** |
| Nhánh lỗi 5xx trên hệ thống thật (`page.route` trả mã 500): Lưu đơn 500, sau đó tra khách 500, rồi tra khách thành công | Lời báo "Máy chủ đang gặp lỗi (mã 500)" **còn** |
| Chỉ tra khách 500, rồi tra khách thành công | Lời báo **tắt**, như trước |
| Luồng thường trên hệ thống thật (`sale.staff`, `vd.staff`) | Đạt cả 5 ca: dựng lại cuộc đua thì lời báo còn; mất mạng bấm Lưu thì có lời báo, có mạng lại bấm Lưu thì lời báo tắt và thêm đúng 1 đơn; nút × đóng được; lưới mất mạng báo "Lỗi lưu" bằng tiếng Việt, có mạng lại thì tự lưu "Đã lưu", 0 lỗi JS |
| Quét liên kết KN CRM và KN ERP × `quantri`, `sale.manager`, `sale.staff`, `vd.staff` | 35 và 174 trang: 0 lỗi JS, 0 trả lời 5xx, nhật ký máy chủ 0 traceback. Sáu lượt mở không phải trang (tệp mẫu tải về, liên kết Google Docs của tài liệu mẫu) giống lượt 14.10 trước |
| `pytest -m "not trinh_duyet"` | **3.207 đạt, 7 bỏ qua, 0 đỏ** |
| e2e hai lượt như CI | 69 đạt và 22 đạt. 9 bài đỏ đúng là 9 bài font Google có sẵn của máy ảo, không có lỗi nào khác |
| CI của #128 trên `09f3559` | Xanh cả hai việc |

**Kết luận:** đạt, gộp.
