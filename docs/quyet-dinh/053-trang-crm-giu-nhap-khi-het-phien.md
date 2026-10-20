# ADR-053 — Trang KN CRM giữ nháp khi hết phiên, lấy mã CSRF mới lúc gửi, chặn đổi người

| Mục | Nội dung |
|---|---|
| Ngày | 14.10.2026 |
| Trạng thái | Chủ dự án đã duyệt (câu "Lưu lại được, sửa ADR-030"). Mở PR nháp về `Staging` (P0-14, TL-02, TL-18). Chưa gộp |
| Thay thế / bổ sung | Sửa một điều khoản của ADR-030 ("form cũ sau đăng nhập lại có CSRF cũ bị từ chối") cho trang KN CRM. Phần còn lại của ADR-030 giữ nguyên |

## Bối cảnh

Hết phiên giữa lúc làm việc ở KN CRM (hết 60 phút không thao tác, đăng xuất ở tab khác, bị khoá, phải đổi mật khẩu) làm
mất việc đang làm:

- **TL-02 (S1), lưới.** `fetch` đi theo 302 tới trang đăng nhập, `json()` gán `status=403`, lưới coi là mất quyền:
  `clearAccess` xoá bản đang làm, ô đang gõ và cả màn hình. Lượt hỏi 8 giây cũng đi đường đó ("Quyền xem đã thay đổi").
  Nút "Ẩn cho cả công ty" coi trang đăng nhập (200) là thành công rồi tải lại trang.
- **TL-18 (S2), htmx.** htmx đi theo 302 rồi dán cả trang đăng nhập vào hộp Chi tiết, hộp lọc, form Lên đơn (mất form).
  Ô phân công đọc trang đăng nhập ra `{}` rồi đóng như đã lưu. Lượt hỏi chứng từ ném `SyntaxError` tiếng Anh rồi xoá form
  đang gõ. Tạo sản phẩm in nguyên HTML trang 403.
- **ADR-030, dòng 25–27.** Đăng nhập lại ở tab khác thì Django đổi mã CSRF (`rotate_token`); trang cũ giữ mã cũ nên
  "đăng nhập lại rồi bấm Thử lại" luôn ra 403. Người dùng chỉ còn cách tải lại trang, tức là mất nháp.

Chủ dự án chốt 14.10.2026:

1. Hết phiên thì không dán trang đăng nhập, không xoá nháp (giữ trong bộ nhớ tab, không ghi localStorage), không báo lưu
   giả, lời báo tiếng Việt. Lượt hỏi 8 giây giữ nguyên chuyện gia hạn phiên.
2. Đăng nhập lại rồi bấm Thử lại/Lưu thì **lưu được**: trang lấy mã CSRF mới lúc gửi.
3. Người khác đăng nhập ở tab khác thì chặn: máy chủ trả 409, trang báo "Tài khoản vừa đăng nhập khác người mở trang —
   nháp không được lưu".
4. Ghi thành ADR này, sửa điều khoản của ADR-030.

## Quyết định

1. **Hết phiên (Phần A).**
   - Máy chủ: yêu cầu HTMX bị `login_required` hay `ForcePasswordChangeMiddleware` trả 302 thì `SessionTimeoutMiddleware`
     đổi thành `200 + HX-Redirect`, thân rỗng. Với trang đăng nhập, `next` là trang đang xem (`HX-Current-URL`), lọc bằng
     `url_has_allowed_host_and_scheme` và bỏ khi chính nó là trang đăng nhập hay không phân tích được. Yêu cầu thường và
     `fetch` JSON vẫn 302: lưới dựa vào `response.redirected`.
   - Trình duyệt: `static/js/het-phien.js` (nạp ở hai khung KN CRM ngay sau `loi-mang.js`) chặn `htmx:beforeOnLoad` khi
     gặp `HX-Redirect`/trang đăng nhập, trang đổi mật khẩu, 409 `nguoi_dung_doi`, 403 `code: csrf` hay 403 khác: không
     chuyển trang, không dán. Lời báo ghi ngay vào chỗ đích; đích có ô nhập thì chèn ở đầu, không đụng chữ đang gõ. Lời nổi
     chỉ hiện khi đích không nằm trong hộp thoại đang mở. Không chặn 400 (`waybill.js` tự dán lỗi nhập liệu).
   - Lưới: lỗi phiên (`het_phien`, `doi_mat_khau`, `csrf`, `nguoi_dung_doi`) không phải mất quyền. Lưới giữ bản đang làm,
     ô đang mở, lượt chưa xác nhận và các khối 100 dòng có nháp; bỏ các khối khác khỏi bộ đệm và màn hình như khi mất
     quyền; dừng lượt hỏi tới khi có phản hồi hợp lệ hay người dùng bấm Thử lại/Tiếp tục. Không ghi localStorage.
   - **Không bao giờ tự gửi lại:** lỗi phiên không vào vòng tự thử lại 5xx và huỷ hẹn tự thử lại đang chờ, sự kiện
     `online` không gửi khi đang mất phiên, tự lưu không gửi lại lượt xoá/khôi phục dòng đang chờ, `travel*` đang thử lại
     không lưu ô chờ trước. Lỗi phiên giữ nguyên lượt lưu chưa rõ kết quả cùng mã lượt, nên Thử lại dùng lại biên nhận
     chống ghi đôi.
   - Lượt dòng chưa xác nhận làm thanh trạng thái hiện "Lỗi lưu" (không phải "Đã lưu"), nút Lưu thử lại được lượt đó.
     Phản hồi JSON hợp lệ đầu tiên sau khi đăng nhập lại gỡ chặn tải khối, lưới tải tiếp.
   - Ô phân công, chứng từ, Lên đơn: lời báo tiếng Việt kèm cách làm tiếp, không đóng ô chọn, không xoá form đang gõ,
     không in trang HTML.
   - Cách làm tiếp: hết phiên hay mã bảo mật lệch thì liên kết "Đăng nhập lại (tab mới)"; phải đổi mật khẩu thì "Đổi mật
     khẩu (tab mới)"; đổi người thì lời dẫn "Đăng xuất tài khoản đang dùng ở tab khác, đăng nhập lại bằng tài khoản <MÃ>
     rồi bấm Thử lại", không đưa liên kết: trang đăng nhập không cho người đang đăng nhập đăng nhập lại mà đưa thẳng vào
     trang (ADR-030: đổi tài khoản phải đăng xuất trước).
2. **Sửa ADR-030 dòng 25–27.** Trang KN CRM (lưới, Lên đơn, hộp Chi tiết, phân công, chứng từ) lấy mã CSRF mới trong
   cookie lúc gửi, cả header `X-CSRFToken` lẫn tham số `csrfmiddlewaretoken` (Django đọc tham số trước header). Cookie trùng
   tên thì lấy cái sau cùng, như Django. Vẫn **không tự gửi lại**: người dùng phải bấm Thử lại/Lưu. Form HTML thường (Đăng
   xuất, Bỏ đơn, Xoá/Khôi phục bảng, Nhập tệp, Cấp quyền) vẫn giữ mã trong trang và bị từ chối như ADR-030.
3. **Chặn đổi người.** Mọi `fetch` và htmx cùng nguồn của trang KN CRM mang `X-KNJSC-User: <pk người mở trang>`.
   `core.middleware.PageOwnerMiddleware` trả 409 `{"error": "Tài khoản vừa đăng nhập khác người mở trang — nháp không
   được lưu", "code": "nguoi_dung_doi"}` khi người đang đăng nhập khác người đó; header rỗng hay sai dạng cũng 409.
   - View không chạy, không ghi gì, không thêm truy vấn. HTMX nhận thêm `HX-Reswap: none`.
   - Áp cho **mọi phương thức**, kể cả GET: không thì lượt hỏi và kiểm quyền dòng của trang A chạy dưới phiên B sẽ gỡ nháp
     của A theo phạm vi của B, và đổ dữ liệu của B vào trang mang tên A.
   - Đứng trước `SessionTimeoutMiddleware`: 409 không ghi `last_seen_at`, không gia hạn phiên của B.
   - Ẩn danh cho qua để `login_required` xử lý.
4. **`CSRF_FAILURE_VIEW = "core.views.csrf_failure"`.** Yêu cầu mang `X-KNJSC-User` (mọi fetch và htmx của trang KN
   CRM) hay thân JSON nhận 403 JSON `{"code": "csrf"}` để trang giữ nháp và báo đúng thay vì coi là mất quyền. Form HTML
   thường và htmx của KN ERP (không lấy mã mới, bấm Thử lại cũng vô ích) vẫn nhận trang 403 của Django như ADR-030.
5. **Ba chỗ khác ADR-030 dòng 30–31** ("không thêm middleware/truy vấn"), có chủ ý:
   - (a) điều khoản CSRF ở mục 2;
   - (b) thêm đúng một middleware không truy vấn (`PageOwnerMiddleware`), `SessionTimeoutMiddleware` thêm bước đổi 302 thành
     `HX-Redirect` cho HTMX, thêm `CSRF_FAILURE_VIEW`;
   - (c) 409 áp cả GET từ trang KN CRM.

   Không đổi quyền nghiệp vụ, URL, form đăng nhập, schema, dependency; không truyền phiên qua URL hay localStorage.
6. **AC-6.14 đổi câu chữ, giữ mã:** 403 còn lại nghĩa là tài khoản không lên đơn được; trang do tài khoản khác mở và mã
   bảo mật lệch có lời riêng; không lời nào bảo tải lại trang.

## Ràng buộc

- `CSRF_COOKIE_HTTPONLY` phải để False (mặc định): `het-phien.js` đọc mã mới trong cookie. Biên bản phát hành kiểm không
  còn cookie CSRF host-only trùng tên với cookie của domain mẹ trên hai hostname.
- `X-KNJSC-User` là chốt toàn vẹn do trang tự nguyện gửi, **không phải kiểm quyền**: quyền vẫn theo `request.user`. Trang
  khác nguồn không đặt được header này (không mở CORS; header lạ cần preflight).
- Header không phủ tải tài nguyên thường: ảnh chứng từ, Tải Excel, liên kết GET. Khi người khác đã đăng nhập, các lần tải
  đó chạy theo quyền của người đó, như mọi trang khác.
- Màn hình mới dùng `fetch`/htmx ngoài hai khung KN CRM phải nạp `het-phien.js`.
- Tài khoản bị khoá: các khối có nháp còn trên màn hình tới khi đóng tab; lưu không được.
- ERP không đổi: HTMX hết phiên ở ERP vẫn chuyển cả trang về đăng nhập (nay qua `HX-Redirect`, quay lại đúng trang), form
  ERP đang gõ dở vẫn mất như trước.

## Hệ quả

- Cùng một lời "Phiên đăng nhập đã hết" cho hết giờ, đăng xuất ở tab khác, bị khoá và đổi quyền: máy chủ chỉ chuyển về
  trang đăng nhập nên trang không biết lý do.
- Lượt hỏi 8 giây dừng khi mất phiên hay đổi người, chạy lại khi có phản hồi JSON hợp lệ hoặc khi người dùng bấm. Trong
  lúc dừng, tab cũ không gia hạn phiên; tab vừa đăng nhập lại gia hạn như cũ (G6/P1-21 chưa đổi).
- Khi một lượt xoá hay khôi phục dòng chưa được xác nhận, ô sửa thêm không tự lưu ("Chưa lưu") tới khi người dùng bấm Thử
  lại lượt đó hoặc Lưu — đúng nguyên tắc không tự gửi lại.

## Quay lui

Revert PR. Không có migration, không đổi dữ liệu.

## Kiểm chứng

[Biên bản P0-14](../kiem-chung-p0-14-het-phien-20261014.md).
