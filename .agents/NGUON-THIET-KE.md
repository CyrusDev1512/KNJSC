# Nguồn nhóm skill thiết kế

Chép tay từ kho mã nguồn mở, không qua trình cài đặt, vì phiên Claude Code trên
web không ra được `impeccable.style` và lệnh `npx skills add` bị chặn. Cập nhật
bằng cách chép lại từ kho gốc theo đúng bảng dưới, hoặc trên máy cá nhân chạy
`npx impeccable update` và `npx skills add https://github.com/Leonxlnx/taste-skill --skill <tên>`.

| Thư mục | Nguồn | Phiên bản, commit | Giấy phép |
|---|---|---|---|
| `impeccable/` và `../agents/impeccable-*.md` | https://github.com/pbakaus/impeccable, thư mục `.claude/` của kho | skill 4.2.1, commit `831cabe` ngày 05.09.2026 | Apache-2.0, xem `impeccable/LICENSE` và `impeccable/NOTICE.md` |
| `design-taste-frontend/` | https://github.com/Leonxlnx/taste-skill, `skills/taste-skill/` | commit `ccbc156` ngày 24.08.2026 | MIT, xem `design-taste-frontend/LICENSE` |
| `redesign-existing-projects/` | cùng kho, `skills/redesign-skill/` | cùng commit | MIT |
| `high-end-visual-design/` | cùng kho, `skills/soft-skill/` | cùng commit | MIT |
| `minimalist-ui/` | cùng kho, `skills/minimalist-skill/` | cùng commit | MIT |

Tên thư mục lấy theo trường `name` trong đầu tệp `SKILL.md`, không theo tên thư
mục của kho gốc, vì Claude Code gọi skill bằng tên đó.

Chưa chép từ taste-skill, thêm được bằng cách chép cùng kiểu: `design-taste-frontend-v1`,
`gpt-taste` (cho Codex), `image-to-code`, `imagegen-frontend-web`,
`imagegen-frontend-mobile`, `brandkit` (ba cái này cần mô hình sinh ảnh),
`industrial-brutalist-ui`, `stitch-design-taste` (cho Google Stitch), `full-output-enforcement`.

Engine của Impeccable là tệp nhị phân, không nằm trong kho: `impeccable/scripts/impeccable`
tự tải từ GitHub Releases về `~/.impeccable/bin/` lần đầu chạy. Hook tự kiểm thiết kế
sau mỗi lần sửa tệp cũng không commit; bật trên máy mình bằng `/impeccable hooks on`.


09.09.2026: nội dung nằm duy nhất tại `.agents/skills/<tên>`, không còn cầu nối.
Các đường dẫn ở bảng trên mô tả nguồn nhập lịch sử. Manifest hiện hành:
[skill-sources.json](skill-sources.json). Hướng dẫn cập nhật bằng npx/hook phía
trên là lịch sử upstream, không áp dụng tự động cho bản KNJSC đã chuẩn hóa.
Impeccable dùng entrypoint thủ công; engine workflow lưu trong reference để bảo trì.
Hồ sơ thiết kế chuyển về `.agents/design-state`; chưa kiểm engine với vị trí mới.
