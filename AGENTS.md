# Hướng dẫn Codex — Kim Ngân JSC

Áp dụng cho toàn bộ repository. File này chứa quy tắc làm việc cốt lõi;
tài liệu được liên kết bên dưới cung cấp chi tiết theo từng tác vụ.

## 1. Phối hợp với chủ dự án

- Tự đọc tài liệu, khảo sát code và kiểm tra trạng thái Git trước khi đề xuất sửa.
- **Mỗi tác vụ sửa code, kể cả lỗi nhỏ, phải được chủ dự án duyệt cách làm trước.**
  Trình bày ngắn gọn mục tiêu, phạm vi tác động, cách sửa và cách kiểm chứng.
  Yêu cầu triển khai một kế hoạch đã duyệt là đủ quyền thực hiện; không hỏi lại.
- Sau khi được duyệt, tự hoàn tất sửa code, kiểm thử và cập nhật tài liệu liên quan
  trong phạm vi đó. Không dừng xin xác nhận ở từng bước hoặc từng giai đoạn.
- **Không tự ý thay đổi nghiệp vụ hoặc luồng UI/UX của người dùng cuối.** Nếu cần
  thay đổi, mô tả hành vi trước/sau, tác động và hỏi riêng trước khi sửa. Duyệt một
  tác vụ không mặc nhiên cho phép đổi quy tắc tính toán, quyền, điều hướng hoặc
  các bước thao tác ngoài phạm vi đã chốt.
- Không tự đổi kiến trúc nền tảng hoặc thêm dependency. Nêu nhu cầu và chốt trước
  nếu phương án đã duyệt chưa bao gồm những thay đổi này.
- Tra cứu quyết định đã có trước khi hỏi. Nếu gặp mâu thuẫn ảnh hưởng nghiệp vụ,
  quyền hoặc UI/UX mà chưa có quyết định thay thế rõ ràng, trình bày và hỏi;
  không tự chọn theo suy đoán.
- Giao tiếp và báo cáo bằng tiếng Việt. Bàn giao kết quả cùng diff để chủ dự án xem;
  chỉ commit, push, tạo PR hoặc merge khi được yêu cầu.

## 2. Đọc context theo tác vụ

Hướng dẫn và skill dùng chung được quản lý trong repository; xem
[đồng bộ AI nhiều máy](docs/dong-bo-ai-nhieu-may.md). Chỉ đọc hướng dẫn đồng bộ
khi thiết lập/cập nhật máy hoặc sửa skill, không nạp lại ở mọi tác vụ.
Quy tắc phối hợp ở file này áp dụng chung cho Codex và Claude; CLAUDE.md bổ sung
ngữ cảnh và hướng dẫn riêng của Claude, không thay thế quy tắc phối hợp chung.

Đầu phiên, đọc [README](README.md), [CLAUDE.md](CLAUDE.md) và các mục dưới đây.
Dùng quy trình phối hợp ở mục 1 cho Codex; không mặc định các lệnh skill/hook
riêng của Claude có sẵn trong môi trường Codex.

| Cần hiểu | Nguồn cần đọc |
|---|---|
| Việc còn nợ và quyết định đã chốt | [Backlog](docs/backlog.md), mục 0 và mục 2 |
| Trạng thái công việc, lỗi và kiểm chứng | [Kanban](docs/backlog-kanban.md), [test-log](docs/test-log.md), [dashboard](docs/dashboard-tien-do.html) |
| Mục tiêu, người dùng, yêu cầu | [PRODUCT.md](PRODUCT.md), [tổng quan](docs/01-tong-quan-san-pham.md), [yêu cầu sản phẩm](docs/02-yeu-cau-san-pham.md) |
| Kiến trúc và dữ liệu | [Thiết kế kỹ thuật](docs/03-thiet-ke-ky-thuat.md), [kiến trúc](docs/kien-truc.md), [quyết định kiến trúc](docs/quyet-dinh/README.md) và ADR liên quan trong thư mục đó |
| Giao diện và thao tác | [DESIGN.md](DESIGN.md), [hồ sơ thiết kế](.agents/design-state/design.json), template/CSS/JS của màn hình và ADR liên quan |
| Thế nào là xong | [Tiêu chí nghiệm thu](docs/04-tieu-chi-nghiem-thu.md), [kế hoạch kiểm thử](docs/06-ke-hoach-kiem-thu.md), [kịch bản nghiệm thu](docs/07-kich-ban-nghiem-thu.md) |
| Chạy và vận hành | [Hướng dẫn vận hành](docs/05-huong-dan-va-van-hanh.md), cấu hình thực tế trong `deploy/` và `app/knjsc/settings/` |

- Đọc sâu phần liên quan thay vì chép toàn bộ tài liệu vào hướng dẫn hoặc đọc lại
  mọi tài liệu ở mỗi lần sửa nhỏ. Danh mục ADR có thể chậm cập nhật: kiểm tra cả
  các file hiện có trong `docs/quyet-dinh/`.
- Quyết định đã được chốt và văn bản thay thế rõ ràng giải thích yêu cầu hiện hành.
  Đối chiếu code, cấu hình và test để xác định trạng thái triển khai thực tế;
  code đang chạy không tự trở thành quyền thay đổi nghiệp vụ.
- Không coi “đã merge”, nhãn hoàn thành hoặc test-log cũ là bằng chứng lỗi đã hết.
  Không đóng băng số lượng test, số tiêu chí hay trạng thái PR trong file này.
- Không tự triển khai các mục chưa quyết, đang hoãn hoặc Far Plan.

## 3. Context và ranh giới hệ thống

- **Ưu tiên hiện tại (chủ dự án chốt 09.09.2026):** tập trung sửa feedback
  khách hàng trong KNJSC_PROBLEM.txt theo phạm vi đã xác nhận. “Việc cần làm
  của tôi”, nhắc việc chủ động và AI là giai đoạn sau; không đưa vào tác vụ
  sửa feedback hoặc lấy chúng làm điều kiện phải xây trước.

- **Mục tiêu dài hạn (chủ dự án xác nhận 09.09.2026):** hệ thống chủ động báo
  cho từng người dùng biết công việc còn phải làm, giảm việc quản lý liên tục
  kiểm tra/nhắc việc; tương lai tích hợp AI xuyên suốt CRM/ERP. Khi đề xuất
  tính năng, nêu rõ ai cần làm gì, vì sao cần làm và khi nào việc được coi là
  hoàn tất. Chưa tự quyết hạn xử lý, quy tắc nhắc việc hay quyền hành động
  của AI. Định hướng này không phải quyền tự triển khai AI hoặc đổi luồng UI/UX.
- Tài liệu KNJSC là ghi chép feedback buổi họp khách hàng;
  [KNJSC_PROBLEM.txt](KNJSC_PROBLEM.txt) là bản tổng hợp vấn đề. Phân biệt
  feedback với yêu cầu đã chốt. Câu hỏi nghiệp vụ cần xác nhận tập hợp tại
  [USER_INQUIRY.md](docs/USER_INQUIRY.md); xem [PRODUCT.md](PRODUCT.md) về mục tiêu.

- Hệ thống vận hành thương mại điện tử của Kim Ngân JSC: Marketing → Sale → Vận đơn,
  cùng các module nội bộ. Stack Django, PostgreSQL, HTMX, CSS/JavaScript thuần,
  Celery/Redis và Docker Compose; giữ kiến trúc modular monolith hiện có.
- **KNERP**: dịch vụ `web`, cổng local 8020; báo cáo, lên đơn và các chức năng ERP.
  **Bảng dữ liệu chỉ đọc với mọi bảng**, không mở sửa ô hoặc endpoint ghi lưới ở ERP
  ([ADR-014](docs/quyet-dinh/014-bang-du-lieu-chi-xem.md)).
- **KN CRM**: dịch vụ `bangtinh`, cổng local 8021, dùng chung code và database;
  bảng tính là nơi chỉnh sửa dữ liệu theo quyền. Giữ khung thư mục/sidebar và lưới
  toàn màn hình; nút quay lại của lưới về thư mục CRM, không về ERP
  ([ADR-012](docs/quyet-dinh/012-kn-crm-app-rieng-cay-thang.md),
  [ADR-015](docs/quyet-dinh/015-kn-crm-khung-sidebar-leader-nhu-manager.md)).
- Bảng động dùng `TableDef`, `ColumnDef`, `DataRecord`; tái sử dụng service chung.
  Tháng là góc nhìn lọc trên bảng, không tự tạo bảng vật lý riêng theo tháng.
  Không mở rộng công thức theo cột thành công thức Excel tự do từng ô khi chưa chốt.
- Với vận đơn, đọc [ADR-018](docs/quyet-dinh/018-van-don-moi-theo-crm-tan.md):
  `van_don` là bảng cũ, `van_don_moi` nhận đơn mới. Giữ ID và liên kết lịch sử;
  không áp hành vi riêng của bảng cũ sang bảng mới. ERP và CRM tạo đơn qua cùng
  service; quyền tạo đơn không đồng nghĩa quyền xem bảng.

## 4. Quy tắc dữ liệu và triển khai

- Cấp bậc tách khỏi bộ phận: Staff theo bản thân, Leader theo team, Manager theo
  bộ phận, Admin toàn hệ thống. Kiểm tra quyền phía server trên mọi đường đọc/ghi,
  nhập/xuất và thống kê; dùng manager/service phạm vi hiện có. Không chỉ ẩn nút UI.
- Giữ ngoại lệ đã chốt như bảng dùng chung và dữ liệu nội bộ toàn công ty;
  không siết hoặc mở quyền đồng loạt. Leader có một số thao tác như Manager ở CRM
  không có nghĩa được xem toàn bộ phận hoặc tự cấp quyền như Manager.
- Từ chối truy cập ngoài quyền theo hợp đồng endpoint (403/404); không che lỗi
  phân quyền bằng kết quả trống hoặc thông báo lưu thành công.
- Tiền dùng `Decimal`/PostgreSQL numeric, giữ đơn vị và loại tiền. Không dùng float,
  tự đổi tỷ giá hoặc cộng lẫn tiền tệ. Thời gian lưu UTC, hiển thị theo giờ Việt Nam.
- Giữ cơ chế bất biến của báo cáo đã nộp và đơn hàng đã chốt. Tạo đơn và bản sao
  vận đơn trong giao dịch; sửa bản sao vận đơn/chi tiết không sửa `Order`/`OrderLine`.
- Dùng soft delete và audit theo khuôn hiện có; audit chỉ nối thêm, không sửa lịch sử.
  Không ghi mật khẩu, token hoặc dữ liệu khách hàng nhạy cảm vào log/audit.
- View mỏng, logic nghiệp vụ trong service; tái sử dụng tiện ích `core`, không nhân
  bản logic giữa ERP và CRM. Giữ phân trang, tránh N+1 và giữ tính toàn vẹn khi ghi
  đồng thời; lỗi mạng/xung đột phải hiện đúng, không báo đã lưu khi ghi thất bại.
- Không sửa migration đã áp dụng; thêm migration mới, có cách đảo ngược phù hợp.
  Tên code theo quy ước tiếng Anh hiện có; nhãn UI và chú thích giải thích bằng
  tiếng Việt. Nếu được yêu cầu commit, dùng thông điệp tiếng Việt không dấu.
- Giữ nguyên thay đổi và file chưa theo dõi sẵn có của người dùng. Không tự reset,
  clean, xoá dữ liệu, phục hồi database hay xoá Docker volume để làm test chạy được.
- Đọc script trước khi chạy. Launcher `KN JSC.bat` có kéo mã, migration và khởi tạo
  dữ liệu; script seed/kiểm tải có thể thay đổi dữ liệu và mật khẩu mẫu. Chỉ dùng
  khi tác động đó thuộc phạm vi được cho phép và trên môi trường phù hợp.

## 5. Kiểm thử và bàn giao

Chạy từ gốc repository, với Docker/Compose và môi trường kiểm thử đã sẵn sàng.
Lệnh chuẩn theo [Compose](deploy/docker-compose.yml) và [pytest.ini](app/pytest.ini):

```powershell
# Toàn bộ suite
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest

# Ví dụ chạy nhóm liên quan; thay crm/tests bằng đường dẫn trong app/
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest crm/tests

# Vòng lặp nhanh, chủ động bỏ bài chậm
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest -m "not cham"
```

- `pytest.ini` ép `knjsc.settings.test` bằng `--ds`; mặc định **không loại** marker
  `cham`. Giữ `RUN_MIGRATIONS=0` để bỏ khởi tạo dữ liệu dev ở entrypoint; pytest
  vẫn quản lý migration của database kiểm thử riêng.
- Chọn test theo tác động, thêm hồi quy có ý nghĩa cho lỗi hành vi. Với phân quyền,
  kiểm cả trường hợp được phép và bị từ chối, kể cả truy cập trực tiếp endpoint.
  Giữ truy vết mã AC trong test khi tác vụ có tiêu chí nghiệm thu tương ứng.
- Khi thay đổi hành vi UI/JavaScript, kiểm bằng trình duyệt/Playwright theo kế hoạch
  kiểm thử. Marker `trinh_duyet` có thể bị skip nếu thiếu Chromium; skip không phải
  đã kiểm chứng. Test HTML đơn thuần không chứng minh luồng thao tác hoạt động.
- Với thay đổi migration, kiểm xuôi/ngược trên database test riêng; không migrate
  về zero trên dữ liệu dev/thật. Thay đổi đường ghi hàng loạt hoặc tính toán lớn
  cần kiểm hiệu năng liên quan theo ADR-016 trong môi trường kiểm tải phù hợp.
- Với thay đổi chỉ tài liệu, kiểm nội dung, liên kết và diff là đủ; không bắt buộc
  chạy suite ứng dụng. Không tuyên bố đạt những kiểm tra chưa chạy.
- Trong phạm vi đã duyệt, cập nhật backlog/dashboard khi tiến độ thay đổi,
  kanban/test-log khi liên quan. Phát hiện mới ghi backlog trước khi đổi đặc tả;
  quyết định kiến trúc quan trọng cần ADR. Giữ lịch sử, ghi rõ văn bản thay thế.
  Không tiện tay xử lý toàn bộ lỗi hoặc tài liệu cũ ngoài tác vụ.
- Trước bàn giao, kiểm diff và trạng thái Git. Báo ngắn gọn: đã đổi gì, vì sao,
  lệnh kiểm tra và kết quả, phần skip/chưa kiểm chứng, cùng rủi ro còn lại nếu có.
