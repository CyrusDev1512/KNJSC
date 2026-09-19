# Xác nhận trạng thái VPS — 19.09.2026

**Biên bản này dựng lại từ quan sát, không phải từ nhật ký phát hành.** Lần phát hành nói
dưới đây **không để lại biên bản nào trong kho mã**, nên mọi tài liệu sau đó (kể cả runbook
19.09) đều viết như thể chưa chạy. Ghi lại ở đây để không ai kết luận sai thêm lần nữa.

## Đã có trên VPS

Chủ dự án kiểm trực tiếp trên domain thật chiều 19.09, ba phép thử đều dương:

| Phép thử | Kết quả | Kết luận |
|---|---|---|
| Mở `https://crm.thnsolution.io.vn/cau-hinh/nhan-don/` | 404 Not Found | Trang Bảng nhận đơn đã bỏ — **ADR-036 đã chạy** |
| Thư mục Vận đơn trong KN CRM | Không còn "crmThuận" lẫn "Vận đơn DB" | Lệnh `xoa_bang_van_don_cu` **đã chạy thật**, 6.667 + 2 dòng đã mất vĩnh viễn |
| Ô PTTT ở Lên đơn | Đủ bảy loại | **Bảy PTTT đã chạy** (bổ sung ADR-031, 18.09 tối) |

Suy ra các migration đã áp trên VPS: `forms_builder/0014`, `orders/0009` (Codex), `orders/0010`.

## Chưa xác nhận

Chưa có phép thử nào cho: ADR-037 (mã nhân sự), ADR-038 (trang Marketing), bố cục Báo cáo
tổng hợp 18.09 tối, ô Nhân sự chỉ mã, AC-22.14. Ba việc này nằm cùng dãy commit nên **có thể**
đã lên cùng lần, nhưng không được coi là chắc cho tới khi kiểm.

Cách kiểm nhanh trên domain thật:

- **ADR-037**: danh sách Nhân sự có cột **Mã**; hoặc đăng nhập bằng mã (ví dụ `THUANLT`) thay tên đăng nhập.
- **ADR-038**: Marketing nộp báo cáo **hai lần trong cùng một ngày** không bị chặn; bộ lọc Báo cáo tổng hợp có ô **Tệp khách hàng**.
- **AC-22.14**: ô Nhân sự ở Báo cáo tổng hợp, ngày có hai marketer thì hiện **hai dòng**, không phải một dòng gộp.

## Chưa có trên VPS

**ADR-039 — ẩn cột với cả công ty** (`1e09cfd`), đẩy lên GitHub 19.09 sau lần phát hành trên.
Migration kèm theo `forms_builder/0015`. Sau khi phát hành còn phải bấm ẩn nhóm cột sản phẩm
một lần thì cột mới tắt.

## Bài học cho phiên sau

Không suy "không có biên bản" thành "chưa phát hành". Kho mã chỉ cho biết **điều gì đã được
ghi lại**. Muốn biết VPS đang chạy gì thì hỏi chủ dự án hoặc kiểm bằng dấu hiệu quan sát
được trên domain thật — Claude Code trên web không tới được VPS, kể cả để đọc.
