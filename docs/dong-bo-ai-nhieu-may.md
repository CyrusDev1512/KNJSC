# Một bộ skill dùng chung cho Codex và Claude Code

## Cấu trúc hiện tại

```text
.agents/
  skills/                 10 skill đầy đủ, mỗi skill một bản — NGUỒN DUY NHẤT
  skill-sources.json      Nguồn, commit, giấy phép và hash local
  NGUON-THIET-KE.md        Xuất xứ nhóm thiết kế đã có
  design-state/           Hồ sơ thiết kế và surfaces của KNJSC
.claude/
  skills/<tên>/SKILL.md   10 cầu nối SINH TỰ ĐỘNG cho Claude Code — không sửa tay
  agents/                 Bốn agent Impeccable, chỉ Claude dùng
```

**Vì sao cần cầu nối (17.09.2026).** Codex đọc `.agents/skills`. Claude Code chỉ
khám phá `.claude/skills/<tên>/SKILL.md` (và `~/.claude/skills`, plugin); tài liệu
Claude Code ghi rõ không hỗ trợ `.agents/skills`. Bản 09.09 bỏ `.claude/skills`
nên Claude mất cả 10 skill. Ba cách đã cân nhắc:

| Cách | Vì sao không / có |
|---|---|
| Symlink `.claude/skills/<tên>` → `.agents/skills/<tên>` | Windows checkout biến symlink thành tệp chữ; máy chủ dự án là Windows |
| Chép nguyên nội dung sang `.claude/skills` | Hai bản, lệch nhau sau vài lần sửa; impeccable có hơn 50 tệp |
| **Cầu nối** một tệp `SKILL.md` chép `name`/`description`, thân chỉ trỏ về nguồn | Claude tự chọn skill nhờ mô tả, đọc nội dung thật ở `.agents`; script sinh và kiểm nên không lệch |

Chỉ sửa nội dung tại `.agents/skills`. Không còn `ai`, `.impeccable` ở gốc. Giữ
nguyên năm skill cốt lõi và năm skill thiết kế; không bổ sung skill mới. Ảnh review
trong `.agents/design-state/review/` là dữ liệu local được Git bỏ qua.

AGENTS.md là quy tắc chung; PRODUCT.md, DESIGN.md và ADR lưu tầm nhìn, quyết định.
CLAUDE.md là ngữ cảnh riêng cho Claude, đứng dưới AGENTS.md.

## Chuyển máy và kiểm

Máy khác clone hoặc pull đúng nhánh rồi chạy:

```powershell
python scripts/dong-bo-skill.py --check
```

Windows có thể dùng `py -3`; macOS/Linux dùng `python3`. Cần Python 3.10 trở lên,
không cần package. `--check` chỉ đọc: kiểm danh mục, metadata, nguồn, hash chuẩn
hoá CRLF về LF, và **10 cầu nối khớp bản sinh từ nguồn** (thiếu, thừa, lệch mô tả
đều FAIL). Không tải mạng, chạy ứng dụng hay database. Bài `app/tests/test_dong_bo_skill.py`
chạy cùng kiểm tra đó trong pytest, nên suite đỏ khi ai sửa skill mà quên cầu nối.

Mở phiên mới để kiểm Codex nhận đủ 10 tên và Claude Code liệt kê đủ 10 skill.
File hợp lệ không chứng minh tự chọn skill đúng; năm tình huống trong
[bộ skill](bo-skill-knjsc.md) vẫn cần đánh giá qua tác vụ thực tế.
Cùng skill không bảo đảm kết quả giống hệt giữa model, công cụ và context khác nhau.

## Cập nhật và Impeccable

Sửa `.agents/skills/<tên>`, review rồi cập nhật hash local và ghi điều chỉnh trong
`.agents/skill-sources.json`. Giữ commit nguồn và giấy phép; không tự cập nhật
upstream. Rồi sinh lại cầu nối và kiểm:

```powershell
python scripts/dong-bo-skill.py --tao-cau-noi
```

Lệnh này ghi đè 10 tệp `.claude/skills/<tên>/SKILL.md` rồi chạy `--check`. Commit
cả `.agents` lẫn `.claude/skills` trong cùng một commit; chỉ commit/push khi được
yêu cầu.

Impeccable hiện dùng hướng dẫn thiết kế cùng hồ sơ ở `.agents/design-state`.
Entrypoint đã bỏ việc tự chạy engine/hook, tránh tạo lại `.impeccable` ở gốc.
Workflow engine gốc được giữ trong reference để bảo trì, không nạp mặc định.
Chưa xác minh engine hỗ trợ vị trí dữ liệu mới; di chuyển file không đồng nghĩa
cấu hình engine đã hoạt động. Không tự chạy hoặc cài engine trong lần gom này.
Credentials, session, .env, cache và cấu hình riêng từng máy không đồng bộ qua Git.
