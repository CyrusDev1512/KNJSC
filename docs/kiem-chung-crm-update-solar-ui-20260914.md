# Kiểm chứng hợp nhất CRM-UPDATE và Solar UI — 14.09.2026

## Phạm vi

Nhánh `codex/crm-update-solar-ui` hợp nhất lõi nghiệp vụ của `CRM-UPDATE` với
giao diện Solarpunk từ `origin/codex/ui-solarpunk`. CRM-UPDATE tiếp tục là
nguồn chuẩn cho dữ liệu, quyền, lưới JSON/cuộn ảo, tự lưu, CAS, Undo, phân công,
chi tiết sản phẩm, chứng từ và thống kê. Solar chỉ thay đổi trình bày, bố cục và
chế độ tập trung. Không thêm dependency, migration, model hoặc endpoint.

Preview dùng riêng ERP 18020, CRM 18021, database/volume/cookie riêng; không đổi
dịch vụ 8020/8021, database đang dùng hoặc dữ liệu thật.

## Kết quả tự động

- Nhóm giao diện tệp, khung ERP/CRM, lưới động, tạo/cấp quyền và báo cáo: đạt
  toàn bộ.
- `manage.py check` với URLconf ERP và KN CRM: không có vấn đề.
- Full suite: **2.329 passed, 15 failed, 31 skipped, 2 xfailed** trong 650,83
  giây. Mốc CRM-UPDATE trước hợp nhất là 2.327 passed, 17 failed, 31 skipped,
  2 xfailed; hai lỗi giảm đi là hai assertion cũ phụ thuộc renderer HTMX đã bị
  ADR-027 thay thế. Không phát sinh nhóm lỗi mới do merge.
- 15 lỗi còn lại trùng các nhóm nền đã ghi ở biên bản CRM-UPDATE: dữ liệu mẫu
  có bộ phận Kế toán (2), bài cũ còn đòi form Lên đơn tại ERP và ma trận quyền
  cũ (8), truy vết mã AC/tài liệu cũ (5). Không coi full suite là xanh.
- Kiểm tra migration ở chế độ dry-run: không có thay đổi schema ngoài migration
  đã có trong hai dòng lịch sử.

## Kết quả Chrome

- `kiem-thu-solarpunk.cjs`: đạt hợp đồng lưới master, dropdown trạng thái vận
  chuyển, trình chọn ngày thanh toán, chi tiết sản phẩm, phân công, liên kết chế
  độ xem, ERP → CRM, báo cáo HTMX và fallback không JavaScript.
- `kiem-thu-solarpunk-save.cjs`: đạt lưu nền, chuyển chế độ tập trung khi còn
  lượt lưu, Undo, lỗi mạng/thử lại, dán hai dòng và hoàn tác.
- `kiem-thu-solarpunk-conflict.cjs`: đạt xung đột CAS thật, hộp đối chiếu, thứ
  tự ưu tiên Esc, cột ghim và giữ vị trí cuộn.
- `kiem-thu-solarpunk-layout.cjs`: đạt bảy cấu hình viewport/mật độ, sáng/tối,
  báo cáo/lưới/tập trung; không tràn hoặc đè dock. Mức 125–200% là mô phỏng
  viewport/mật độ, chưa phải thao tác zoom thủ công trong Chrome.
- Audit vai trò chỉ ghi nhận các 404 dự kiến do seed/phạm vi quyền của Sale;
  không có lỗi JavaScript hoặc lỗi bố cục mới.

## Giới hạn và bàn giao

Không triển khai production, không thay runtime 8020/8021, không xóa nhánh cũ
và không đưa các thư mục cá nhân chưa theo dõi vào Git. Các bài bị skip chưa
được tính là đã kiểm chứng; phần browser trọng yếu đã được chạy bằng các script
Chrome riêng ở trên. Nhánh chỉ sẵn sàng để chủ dự án kiểm thử tiếp, chưa phải
quyết định merge vào `main`.
