# Biên bản kiểm chứng — P0-14: hết phiên giữ nháp, mã CSRF mới lúc gửi, chặn đổi người (TL-02, TL-18, ADR-053), 14.10.2026

| Mục | Nội dung |
|---|---|
| Yêu cầu | Lộ trình P0 (`docs/08` mục 9), việc P0-14. Chủ dự án chốt 14.10.2026: hết phiên không dán trang đăng nhập, không xoá nháp, không báo lưu giả; "Lưu lại được, sửa ADR-030"; người khác đăng nhập thì 409 `nguoi_dung_doi` |
| Phạm vi | `core/middleware.py`, `core/views.py`, `knjsc/settings/base.py`, `crm/context_processors.py`; JS `het-phien.js` (mới), `master-grid.js`, `waybill-feedback.js`, `payments.js`, `order-entry.js`; năm template KN CRM. Không model, không migration, không đổi quyền, không thêm thư viện |
| Nhánh | `claude/p0-tl18-het-phien-con-nhap`: tách từ `claude/p0-tl03-doc-tien` (#124), gộp `claude/p0-admin-cuoi-va-truong-nhom` (#125) và `Staging` (KN OMS) |
| Môi trường | Máy ảo Claude Code trên web: Python 3.11, Django 5.2.17, PostgreSQL 16, Chromium của Playwright 1.56, Node 22 |
| Kết luận | **Đạt** trên máy ảo. Còn chờ CI của PR, kết luận còn lại của người kiểm lại (mục 3) và chặng 2 ở máy chủ dự án |

## 1. Bài đỏ trước khi sửa

Bài viết trước, chạy trên mã chưa sửa để chắc là đỏ đúng vì lỗi.

| Bài | Đỏ trên | Kết quả | Lý do đỏ |
|---|---|---|---|
| `crm/tests/test_nguoi_mo_trang.py` B1–B8 (21 bài) | Mã trước C2 | **21 đỏ** | View chạy và ghi dưới tên người khác (200); mã CSRF lệch trả trang HTML; khung chưa nạp `het-phien.js`; Lên đơn, chứng từ thiếu `?v=` |
| `tests/test_khoi.py` quét 409 mọi đường dẫn (B9) | Mã trước C2 | **132 đỏ** | GET trả 200 (32), 302 (11), 403 (4), 404 (44), 405 (40); một đường nổ 500 (TL-104, ngoài phạm vi) |
| `core/tests/test_ra_soat.py` A1–A5, `tests/test_khoi.py` A6 | Mã sau C2, trước C3 | **140 đỏ** | HTMX chưa đăng nhập nhận 302 rồi dán trang đăng nhập; `next` mang `/\ngoai.example`, vòng về trang đăng nhập; phải đổi mật khẩu nhận 302 |
| `crm/tests/test_het_phien_e2e.py` E1–E8 | `70fd92b` | **8 đỏ** | Lưới báo "Quyền xem đã thay đổi" và xoá ô đang gõ; không có nút Thử lại; trang đăng nhập dán vào hộp Chi tiết; Ẩn cột tự tải lại trang; tóm tắt bảo "tải lại trang"; Lên đơn không có lời báo; ô phân công đóng; chứng từ mất form |
| `tests/e2e/test_tom_tat_len_don_e2e.py` (thêm hai bước) | `70fd92b` | **Đỏ** ở bước mã bảo mật | 403 nào cũng ra một lời chung |
| `scripts/kiem-thu-master-het-phien-unit.cjs` | `70fd92b` | **Đỏ** | `RangeError: Maximum call stack size exceeded`: `saveAll` ↔ `travel*` đệ quy khi còn lượt dòng chờ thử lại |
| `scripts/kiem-thu-optimization-unit.cjs` (bản sửa) | `70fd92b` | **Đỏ** | Bị chuyển về đăng nhập ra `status 403` (mất quyền) |
| `scripts/kiem-thu-het-phien-unit.cjs` | `70fd92b` | **Đỏ** | Chưa có `het-phien.js` |
| Bài thêm sau rà đối kháng (mục 3) | C4 | **Đỏ** | `test_ra_soat`: `HX-Current-URL` hỏng ném `ValueError` (500). `kiem-thu-master-het-phien-unit`: Thử lại sau lỗi phiên mang mã lượt mới. `kiem-thu-het-phien-unit`: phản hồi 200 có `code: "csrf"` bị coi là lỗi phiên. Đột biến bỏ từng nhánh `csrf_failure`, chốt 409 ở `loadBlock`, cắt đệ quy `travelCreated`, giữ lượt khi lỗi phiên, `retainReadableDrafts`, 403 thường của htmx: mỗi đột biến đều làm bài đỏ |

## 2. Xanh sau khi sửa

| Kiểm | Lệnh | Kết quả |
|---|---|---|
| Bài mới phía máy chủ | `pytest crm/tests/test_nguoi_mo_trang.py tests/test_khoi.py core/tests/test_ra_soat.py` | Xanh hết |
| Hồi quy gần | `pytest tests/test_khoi.py core/tests/test_ra_soat.py core/tests/test_shared_login.py core/tests/test_giao_dien.py tests/test_truy_vet.py crm/tests/test_master_grid.py crm/tests/test_waybill_new.py crm/tests/test_waybill_feedback.py crm/tests/test_payment_documents.py crm/tests/test_shared_integrity.py org/tests/test_account_management.py feed/tests/test_bang_tin.py` | **2.034 đạt**, 0 đỏ (sau C2) |
| `manage.py check` | | Không có vấn đề (`CSRF_FAILURE_VIEW` đúng chữ ký) |
| Bộ chính như CI | `pytest -m "not trinh_duyet" -rs` | **3.525 đạt** trên C4 (11 phút 13 giây); **3.527 đạt** sau khi sửa theo rà (`48fa53a`, thêm 2 tham số), 11 phút 5 giây. Cả hai 7 bỏ qua (các bài kiểm tải cần DB riêng, có sẵn), 0 đỏ |
| e2e lượt 1 như CI | `pytest tests/e2e -m trinh_duyet -vv -rs -o faulthandler_timeout=120` | **78 đạt**, 2 bỏ qua (có sẵn: 300.000 dòng cần cờ riêng, bảng không có dòng trống), 0 đỏ, 7 phút 34 giây (trên C2) |
| e2e lượt 2 như CI | `pytest -m trinh_duyet --ignore=tests/e2e -vv -rs -o faulthandler_timeout=120` | **30 đạt** (22 cũ, 8 mới), 9 bỏ qua (các tệp `*_browser*` cần máy riêng, như CI), 0 đỏ, 4 phút 31 giây trong lúc máy đang chạy rà đối kháng (trần CI 8 phút) |
| Bài e2e mới chạy lại | `pytest crm/tests/test_het_phien_e2e.py tests/e2e/test_tom_tat_len_don_e2e.py -m trinh_duyet` | 8/8 đạt **4 lượt liền** (64–71 giây/lượt), bài tóm tắt 3 lượt liền |
| Script node | `node scripts/kiem-thu-{optimization-unit,master-het-phien-unit,het-phien-unit,master-scope-unit,grid-jump-unit,grid-interaction-unit,master-autosave-unit,master-working-copy,master-row-geometry,date-inputs}.cjs` | Đạt hết. `master-queue-unit` (`1 !== 2`) và `master-conflict-unit` (`apLaiChieuCao is not defined`) đỏ y hệt trên `70fd92b`, có sẵn trên `Staging` |

Cảnh báo "Error when trying to teardown test databases … being accessed by other users" ở cuối lượt e2e có sẵn: chạy riêng
`crm/tests/test_luoi_dong_trong_va_ghim_e2e.py` trên cùng cây cũng ra y hệt.

## 3. Rà đối kháng

Workflow chỉ đọc, bốn hướng rà, mỗi hướng một người tìm, mỗi phát hiện một người kiểm lại cố bác. Ngoài ra tôi tự kiểm
từng phát hiện bằng một bài đỏ trên mã trước khi sửa: pytest, script node hay đột biến. Bảng ghi kết luận lúc đẩy.

| # | Hướng | Phát hiện | Mức | Kiểm | Xử lý |
|---|---|---|---|---|---|
| 1 | Máy chủ | `HX-Current-URL` hỏng (`http://[/`) làm `urlsplit` ném lỗi, yêu cầu HTMX chưa đăng nhập ra **500** | Vừa | Người kiểm lại **xác nhận**; pytest đỏ | Bắt `ValueError`, bỏ `next`; thêm hai tham số vào bài |
| 2 | Máy chủ | Lượt khôi phục lịch sử htmx nhận thân rỗng, trang trắng | Nhẹ | Người kiểm lại **bác**: trang duy nhất dùng `hx-push-url` có `phan-trang.js` tự chuyển về đăng nhập | Không sửa |
| 3 | Lưới | Thử lại xoá dòng hay bỏ chi tiết thành công sau lỗi phiên thì lưới **trống mãi** (cờ chặn tải khối không gỡ) | Vừa | Người kiểm lại **xác nhận**; script node đỏ | Phản hồi JSON hợp lệ gỡ chặn của `holdForSession` |
| 4 | Lưới | Lượt xoá dòng còn treo mà thanh trạng thái báo **"Đã lưu"**, nút Lưu khoá, nút Thử lại dễ mất | Vừa (người kiểm lại hạ xuống nhẹ) | Người kiểm lại **xác nhận**; script node đỏ | "Lỗi lưu"; nút Lưu thử lại được; mọi lời nhắc lượt dòng kèm nút Thử lại |
| 5 | Lưới | Lỗi phiên ở `loadBlock` qua `safe()` bị `message()` đè mất nút và liên kết | Nhẹ | Người kiểm lại **xác nhận**; script node đỏ | Lỗi đã báo mang `handled`; lỗi phiên không đè lời lưu đang chờ |
| 6 | Lưới | `holdForSession` bỏ cả khối có nháp đang nằm trong `stale` (tải lại mềm) | Nhẹ | Người kiểm lại **xác nhận**, và chỉ ra cách sửa đầu (đưa sang bộ đệm) sai vì `stale` có thể theo thứ tự cũ | Giữ ngay trong `stale` khối có nháp, bỏ khối khác; không đưa sang bộ đệm |
| 7 | Lưới | Hẹn tự thử lại 5xx còn chạy sau lỗi phiên: đăng nhập lại là **tự gửi lại** | Nhẹ | Script node đỏ | `sessionNotice` huỷ hẹn; vòng 5xx và sự kiện `online` không chạy khi mất phiên |
| 8 | Lưới (trong danh sách bỏ bớt, tôi tự kiểm) | Lỗi phiên nhả lượt lưu chưa rõ kết quả: Thử lại mang mã lượt mới, mất bảo đảm chống ghi đôi | Vừa | Script node đỏ | Lỗi phiên giữ lượt và mã lượt |
| 9 | het-phien.js | Phần tử gửi htmx đã bị tách khỏi trang thì không chặn được `HX-Redirect`: cả trang lưới chuyển sang đăng nhập | Nhẹ | Script node đỏ | Nghe thêm ngay trên phần tử gửi, mỗi sự kiện xử lý một lần |
| 10 | het-phien.js | Khối báo thiếu lớp `bao bao-xau`, khuất trong hộp Chi tiết dài | Nhẹ | Đọc mã | `div.bao.bao-xau.het-phien-o`, cuộn tới khi cần |
| 11 | het-phien.js | Phản hồi 200 có `code: "csrf"` (tạo sản phẩm tên "CSRF") bị coi là lỗi phiên | Nhẹ | Script node đỏ | Chỉ 403 `csrf`, 409 `nguoi_dung_doi` |
| 12 | Máy chủ (trong danh sách bỏ bớt) | `csrf_failure` trả JSON cho mọi htmx, kể cả ERP: `chon.js` in nguyên chuỗi JSON kèm lời "Bấm Thử lại" vô ích ở ERP | Nhẹ | Đọc mã | Chỉ yêu cầu mang mã người mở trang hay thân JSON; ERP giữ trang 403 của Django như cũ |
| 13 | Bài kiểm | B5/B6 luôn gửi cả header lẫn JSON: bỏ một nhánh của `csrf_failure` bài vẫn xanh | Vừa | Đột biến | B6 tách ca: JSON, form, FormData, htmx có header; JSON không header; ERP; đột biến từng nhánh đều đỏ |
| 14 | Bài kiểm | Script node chỉ chạy `travelDeleted`; hai sửa đối xứng ở `travelCreated` không có bài | Vừa | Đột biến | Thêm kịch bản `travelCreated`; đột biến đều đỏ |
| 15 | Bài kiểm | E4: lời nổi sau Lưu đơn được thoả bằng lời nổi còn lại từ bước tra khách | Nhẹ | Đọc mã | Rời ô điện thoại, gỡ lời nổi cũ rồi mới bấm Lưu đơn; E5 kiểm lời nổi đổi người |
| 16 | Bài kiểm | Bài tóm tắt chỉ kiểm "tải lại trang" ở ca hết phiên | Nhẹ | Đọc mã | Kiểm ở mọi ca |
| 17 | Bài kiểm | Chốt 409 `nguoi_dung_doi` ở `loadBlock` không có bài | Nhẹ | Đột biến | Thêm ca vào `optimization-unit`; đột biến đỏ |
| 18 | Bài kiểm | Bước form của B6 dùng Staff (403 vì không có quyền, không phải vì CSRF) | Nhẹ | Đọc mã | Dùng Admin, kiểm có chữ "CSRF" và cột không đổi |
| 19 | Bài kiểm (trong danh sách bỏ bớt) | E7 có thể chập chờn: đếm lượt hỏi từ trước khi đăng xuất | Nhẹ | Đọc mã | Đếm từ sau khi đăng xuất |
| 20 | Bài kiểm (trong danh sách bỏ bớt) | htmx 403 thường (không mã) không có bài; nhánh `retainReadableDrafts` gặp lỗi phiên, `clearDetails` không có bài | Nhẹ | Đột biến | Thêm ca vào hai script node; đột biến đều đỏ |

Kết luận của người kiểm lại cho các mục 7, 9–11, 13–18 về sau thì cập nhật vào PR.

Ghi lại, không sửa (ngoài phạm vi hay chấp nhận được):
- Lời nổi `.het-phien-noi` của htmx hỏng còn tới khi chính phần tử đó gửi lại thành công hay bấm ×, đúng khuôn `loi-mang.js`.
- Ô chọn phân công đóng khi cuộn nếu khối của dòng đó bị `holdForSession` bỏ (dòng không có nháp).
- `next` rất dài có thể vượt bộ đệm header của nginx (chỉ với URL trên khoảng 2 KB toàn ký tự mã hoá).
- Mã AC của E7 (AC-1.1) và B3 (AC-6.11) mượn gần nghĩa, vì đặc tả tránh AC-26.x đang hoãn.

## 4. Chưa kiểm, còn mở

- **Chặng 2** (máy chủ dự án, `KN JSC.bat`, CRM `127.0.0.1:8021`), theo đặc tả mục 7:
  1. Hai tab cùng người. Tab 1 đang gõ ô lưới, tab 2 Đăng xuất. Trong ≤ 8 giây tab 1 hiện "Phiên đăng nhập đã hết…" kèm
     liên kết, ô đang gõ còn; Enter thì "Lỗi lưu".
  2. Tab 2 đăng nhập lại đúng người, tab 1 bấm Thử lại: "Đã lưu".
  3. Tab 2 đăng xuất, đăng nhập người khác, tab 1 bấm Thử lại: thấy "Tài khoản vừa đăng nhập khác người mở trang…" và lời
     dẫn có mã, không có liên kết đăng nhập; lịch sử ô không đổi.
  4. Lên đơn, hộp Chi tiết, phân công, chứng từ (bật cờ): như E3–E7.
  5. Admin khoá tài khoản đang mở lưới: trong ≤ 8 giây dòng không có nháp biến mất, nháp còn và không lưu được.
  6. ERP: hết phiên khi bấm nút HTMX thì về trang đăng nhập rồi quay lại đúng trang.
- **VPS:** biên bản phát hành kiểm không còn cookie CSRF host-only trùng tên với cookie của domain mẹ trên hai hostname
  (ADR-053, Ràng buộc).
- **TL-104** (ngoài phạm vi, chưa sửa): POST `multipart/form-data` vào `/van-don/phan-cong/` ra 500. Lộ ra lúc bài B9 POST
  `{}` vào mọi đường dẫn; giao diện luôn gửi JSON nên người dùng không gặp.
- Form HTML thường ở tab cũ (Đăng xuất, Bỏ đơn, Xoá/Khôi phục bảng, Nhập tệp, Cấp quyền) sau khi đăng nhập lại vẫn thấy
  trang 403 CSRF của Django, chưa có lời tiếng Việt — đúng điều khoản ADR-030 được giữ.
