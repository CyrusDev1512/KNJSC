# Một bộ skill dùng chung cho KNJSC

## Cấu trúc hiện tại

```text
.agents/
  skills/                 10 skill đầy đủ, mỗi skill một bản
  skill-sources.json      Nguồn, commit, giấy phép và hash local
  NGUON-THIET-KE.md        Xuất xứ nhóm thiết kế đã có
  design-state/           Hồ sơ thiết kế và surfaces của KNJSC
```

Chỉ sửa nội dung tại `.agents/skills`. Không còn `ai`, `.impeccable` ở gốc,
`.claude/skills` hoặc file cầu nối. Giữ nguyên năm skill cốt lõi và năm skill
thiết kế; không bổ sung skill mới. Ảnh review trong `.agents/design-state/review/`
là dữ liệu local được Git bỏ qua; hồ sơ thiết kế và surfaces dùng chung qua Git.

AGENTS.md là quy tắc chung; PRODUCT.md, DESIGN.md và ADR lưu tầm nhìn, quyết định.
CLAUDE.md và `.claude/agents` là cấu hình cũ còn giữ để tham khảo, không chứa bộ
skill riêng. Cấu trúc skill không phụ thuộc việc tiếp tục dùng Claude Code.
Không mặc định Claude tự khám phá `.agents/skills`; nếu dùng lại, đọc skill từ
đường dẫn này theo AGENTS.md hoặc xác minh khả năng khám phá của client đó.

## Chuyển máy

Hiện chưa commit/push, nên máy khác chưa nhận thay đổi qua GitHub. Khi được phép,
đưa `.agents` (trừ dữ liệu local bị ignore), hướng dẫn, script và các thay đổi di
chuyển/xóa file cũ vào cùng commit. Máy khác clone/pull đúng nhánh/commit rồi chạy:

```powershell
python scripts/dong-bo-skill.py --check
```

Windows có thể dùng `py -3`; macOS/Linux dùng `python3`. Cần Python 3.10 trở lên,
không cần package. Script chỉ đọc, kiểm danh mục, metadata, nguồn, hash chuẩn hóa
CRLF về LF và thư mục cũ không còn. Không tải mạng, chạy ứng dụng hay database.
Không có chế độ tạo cầu nối hoặc sao chép skill.

Mở phiên mới để kiểm Codex nhận đủ 10 tên. Chỉ đọc skill và reference liên quan.
File hợp lệ không chứng minh tự chọn skill đúng; năm tình huống trong
[bộ skill](bo-skill-knjsc.md) vẫn cần đánh giá qua tác vụ thực tế.
Cùng skill không bảo đảm kết quả giống hệt giữa model, công cụ và context khác nhau.

## Cập nhật và Impeccable

Sửa `.agents/skills/<tên>`, review rồi cập nhật hash local và ghi điều chỉnh trong
`.agents/skill-sources.json`. Giữ commit nguồn và giấy phép; không tự cập nhật
upstream. Chạy check và kiểm diff; chỉ commit/push khi được yêu cầu.

Impeccable hiện dùng hướng dẫn thiết kế cùng hồ sơ ở `.agents/design-state`.
Entrypoint đã bỏ việc tự chạy engine/hook, tránh tạo lại `.impeccable` ở gốc.
Workflow engine gốc được giữ trong reference để bảo trì, không nạp mặc định.
Chưa xác minh engine hỗ trợ vị trí dữ liệu mới; di chuyển file không đồng nghĩa
cấu hình engine đã hoạt động. Không tự chạy hoặc cài engine trong lần gom này.
Credentials, session, .env, cache và cấu hình riêng từng máy không đồng bộ qua Git.
