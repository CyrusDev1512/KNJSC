# Biên bản săn lỗi — Đường truyền (06.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Đợt săn lỗi, bước 3 (chủ dự án duyệt, làm trên nhánh `claude/san-loi-tiep`) |
| Tiêu chí | AC-10.12 |
| Môi trường | Máy ảo; hệ thống thật (ERP 8020, CRM 8021) trên `Staging` `632506c`; Playwright Chromium: `set_offline`, CDP `Network.emulateNetworkConditions` |

## Đã thử

| Kịch bản | Kết quả trước khi sửa |
|---|---|
| Lưới Vận đơn: sửa ô rồi mất mạng đúng lúc tự lưu; 7,5 giây sau có mạng lại | Đúng về dữ liệu: "Lỗi lưu", ô giữ chữ, có mạng thì tự lưu, DB đúng giá trị, lịch sử ô 1 dòng. **Lỗi vừa: lời báo "Failed to fetch"** — chữ Anh thô |
| Lưới, mạng 3G (trễ 2 giây, 50 KB/s): gõ liên tiếp 5 ô, gõ đè ô đầu khi lượt trước còn đang bay | **Đạt**: 5 giây sau "Đã lưu", DB đúng cả 5 giá trị, ô gõ đè giữ giá trị sau cùng |
| Nộp báo cáo: máy chủ ghi xong nhưng phản hồi rớt (connection reset) | **Đạt**: chỉ 1 báo cáo. Người dùng thấy trang lỗi mạng của Chrome; mở lại form có dòng "Hôm nay bạn đã nộp biểu mẫu này N lần"; tải lại trang lỗi gửi lại đúng mã lần nộp nên không ghi đôi (AC-4.12) |
| Lên đơn: bấm Lưu đơn lúc mất mạng | **Lỗi vừa: không báo gì về việc lưu** (chỉ dòng "Không tải được tóm tắt"); người dùng có thể tưởng đã lưu. Dữ liệu còn nguyên, có mạng bấm lại ra đúng 1 đơn |
| Toàn hệ thống: yêu cầu HTMX gửi hỏng | **Lỗi vừa: im lặng ở mọi trang** — không có xử lý `htmx:sendError` / `htmx:responseError` nào |

## Đã sửa

`static/js/loi-mang.js` nạp đầu tiên ở cả bốn khung trang (`base.html`, `base_tran.html`, `crm/base_crm.html`,
`crm/base_bang_tinh.html`):
- `fetch` hỏng vì mạng đổi thành lời "Mất kết nối mạng — thay đổi chưa được gửi lên máy chủ. Dữ liệu trên màn hình vẫn
  giữ; kiểm tra mạng rồi thử lại." Mọi chỗ đang hiện `error.message` (lưới, chứng từ, phản hồi vận đơn, Lên đơn) tự có lời
  dễ hiểu; huỷ yêu cầu (AbortError) giữ nguyên.
- HTMX gửi hỏng, quá hạn hay máy chủ 5xx: ô báo ở đáy màn hình (role="alert"), không tự tắt khi có mạng lại (người dùng
  vẫn phải bấm lại); tắt khi bấm × hoặc một yêu cầu sau thành công.

Bài `tests/e2e/test_mat_mang_e2e.py`: 2 bài, đỏ trên mã cũ ("Failed to fetch"; không có ô báo), xanh sau khi sửa.

## Chưa kiểm

- Nhập tệp lớn trên mạng chậm (giới hạn thời gian của nginx trên VPS): cần đo trên VPS thật.
- Safari/Firefox: máy ảo chỉ có Chromium.
