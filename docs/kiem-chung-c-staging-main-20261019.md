# Nhánh C — kiểm chứng trước khi đồng bộ Staging và main, 19.10.2026

## Phạm vi và mốc kiểm

- Nhánh kiểm chứng: `codex/kiem-chung-c-staging-main`, tách từ `origin/Staging` sau fetch.
- Staging: `ed7795b3e7f42233a1fbc4d3261c49d92faaf101`, đã gộp PR #137.
- Main trước lượt này: `3bfa9e61fa48c792a6350b8499a88b63622252fc`.
- Chủ dự án cho phép đồng bộ hai nhánh sau kiểm chứng, rồi xoá nhánh C; không phát hành VPS.
- Phần chênh Staging so với main gồm cả đợt P0 và hậu kiểm 14–15.10, KN OMS demo và PR #137; không chỉ riêng PR #137.
- Không có migration, requirements, Dockerfile hoặc entrypoint thay đổi trong phần chênh này.

## Bằng chứng đã có trên đúng mã ứng dụng

Tree của Staging `ed7795b` giống tree PR #137 tại `2a84147`; không suy kết quả từ một bản mã cũ hơn.
Mô phỏng `git merge-tree --write-tree origin/main HEAD` trước khi thêm biên bản này không xung đột và cho cùng tree với Staging.

| Kiểm | Kết quả |
|---|---|
| CI PR #137, run 39197889098, head `2a84147` | 3.926 test chính đạt; 91 + 30 test trình duyệt đạt |
| Kiểm lại local trước gộp #137 | 369 test server đạt (20 deselected), gồm báo cáo, phạm vi quyền, kiểu lọc, lưu lỗi và tính/xoá theo lô |
| Kiểm lại Chromium local | 10/10 đạt: dán vùng qua khối, đồng bộ, giữ nháp khi lỗi, đánh dấu ô sai, xoá thất bại, Manager desktop/390px |
| Cấu hình Django | `check`: không có vấn đề; `migrate --check` trên preview: không có migration chờ |
| Giao diện báo cáo mới | `activity.html` và `report-filters.js` không khác origin/main; PR #137 không sửa các tệp reports |

CI có 18 bài skip (fixture/môi trường kiểm riêng, kiểm tải và ca dòng trống không áp dụng) và một cảnh báo kết nối còn mở khi dọn database test.
Không gọi skip là đạt hoặc coi cảnh báo đã sửa. Không chạy lại tải 300k, không chứng nhận 10 người sửa + 5 Sale lên đơn.
TL-71, TL-83 và phần quyền Leader chưa chốt vẫn giữ trạng thái riêng; không tuyên bố toàn hệ thống không còn lỗi.
CI mới trên commit merge Staging và trên PR nhánh C phải được đọc kết quả thực tế trước khi gộp tiếp.

## Preview local đã chuẩn bị

- ERP `http://localhost:18062/`, CRM `http://localhost:18063/`, database fixture riêng.
- Đã sao lưu database fixture trước khi chạy `configure_erp_reports`; backup chỉ lưu local, ngoài Git.
- Đã cấu hình ba nguồn Marketing, Sale, Vận đơn; không seed hoặc đặt lại mật khẩu.
- Trước/sau: 1.005 DataRecord, 0 DailyReport, 0 Order. Metadata/cột tính báo cáo được cập nhật bằng lệnh chuẩn.
- Trình duyệt đã mở giao diện báo cáo mới, chuyển nguồn Sale/Marketing, mở bộ lọc, bật toàn màn hình và thoát bằng Esc.
- Năm dòng Marketing mẫu cũ chưa có loại tiền vẫn hiện cảnh báo; Sale chưa có dòng mẫu. Không dùng số liệu mẫu này nghiệm thu tiền thật.
- Preview chưa chạy worker/beat; kiểm browser không thay nghiệm thu tác vụ nền thực tế.
- VPS không được thay đổi; chưa đối chiếu trực tiếp lại giao diện VPS vì kết nối domain và SSH timeout trong lượt kiểm này.

## Chặng kiểm tay còn thiếu

Chủ dự án xác nhận ngày 19.10: mới lướt qua local, chưa biết nên kiểm gì. Đây **chưa phải xác nhận kiểm tay đạt**.

Kịch bản ngắn dùng dữ liệu mẫu local:

1. Báo cáo tổng hợp: mở/ẩn lọc; đổi Marketing/Sale; bật toàn màn hình và Esc; xác nhận bố cục mong muốn.
2. CRM: sửa ghi chú một dòng mẫu, chờ Đã lưu rồi tải lại; đối chiếu nội dung.
3. Dán vùng nhỏ từ Excel; lọc ngày/tiền rồi bỏ lọc; kiểm các dòng mong đợi.
4. Tài khoản mẫu Manager: đọc vận đơn người khác; không tự có quyền sửa hoặc menu Quản trị.

Máy kiểm các ca lỗi kỹ thuật; chủ dự án xác nhận trải nghiệm/luồng phù hợp. Nếu có lỗi thì ghi lại và kiểm lại sau sửa.

## Thứ tự gộp được phép

1. Nhánh C → PR nháp về Staging; chỉ gộp khi CI đạt theo phê duyệt có điều kiện của chủ dự án.
2. Chỉ sau xác nhận kiểm tay đạt: Staging → PR về main, kiểm CI và gộp.
3. Đồng bộ Staging tới commit đã gộp trên main theo fast-forward (không thêm mã, không force), để hai ref cùng commit theo yêu cầu chủ dự án; dừng nếu có thay đổi từ phiên khác.
4. Xoá nhánh C đã hoàn tất, giữ bốn nhánh nền. Không đụng PR #136 đang mở hoặc đưa nhánh chưa duyệt vào lượt này.

Biên bản này ghi tình trạng chuẩn bị, không chứng nhận các bước gộp ở trên đã xảy ra. Kết quả thực tế phải đối chiếu ref/PR khi thực hiện.
