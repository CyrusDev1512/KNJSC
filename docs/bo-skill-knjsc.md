# Bộ 5 skill gọn cho KNJSC

Ngày thiết lập: 09.09.2026. Phạm vi: Codex trong repository KNJSC.

## Trạng thái và cách dùng

Năm skill cốt lõi bên dưới hiện ở `.agents/skills`, cùng năm skill thiết kế đã có:
`impeccable`, `design-taste-frontend`, `high-end-visual-design`, `minimalist-ui`,
`redesign-existing-projects`. Tổng **10 bản nội dung chung**, không thêm skill mới
ngoài hai nhóm này. Chỉ `.agents/skills` chứa nội dung; không còn cầu nối.
Xem [cấu trúc và đồng bộ nhiều máy](dong-bo-ai-nhieu-may.md).

Danh mục Codex ở đầu lượt đã hiển thị đủ 10 tên skill trước lần chuyển nội dung này.
Cấu trúc mới cần kiểm khám phá ở lượt/phiên tiếp theo; tự chọn qua 5 tác vụ vẫn chờ.

| Skill | Tác giả | Khi dùng | Dòng entrypoint: nguồn → bản local |
|---|---|---|---:|
| [verification-before-completion](../.agents/skills/verification-before-completion/SKILL.md) | Superpowers / Jesse Vincent | Bàn giao kết quả triển khai hoặc sửa lỗi | 120 → 73 |
| [test-driven-development](../.agents/skills/test-driven-development/SKILL.md) | Superpowers / Jesse Vincent | Hành vi mới hoặc lỗi cần hồi quy | 320 → 72 |
| [performance-optimization](../.agents/skills/performance-optimization/SKILL.md) | Addy Osmani | Thiết kế hoặc sửa code theo yêu cầu hiệu năng cụ thể | 496 → 69 |
| [web-perf](../.agents/skills/web-perf/SKILL.md) | Cloudflare | Đo/điều tra lag và rendering trình duyệt | 201 → 71 |
| [performance-testing-skill](../.agents/skills/performance-testing-skill/SKILL.md) | jovd83 | Kế hoạch, thực thi hoặc phân tích kiểm tải | 278 → 67 |

Tổng entrypoint: **1.415 → 352 dòng**. Đây là số dòng, không phải số token,
thời gian hay mức tăng chất lượng. Mỗi skill có một reference ngắn, chỉ đọc khi cần.
Tên/mô tả phục vụ khám phá; nội dung và reference không được yêu cầu đọc đồng loạt.
Thông thường chọn một skill chuyên môn, thêm TDD/verification nếu phù hợp;
không áp giới hạn cứng nếu công việc thực sự cần nhiều chuyên môn.

Quy tắc nghiệp vụ và lệnh kiểm thử lấy từ [AGENTS.md](../AGENTS.md) và ADR liên quan.
Không tải lại toàn bộ tài liệu hoặc chạy lại kiểm tra còn hợp lệ chỉ vì đổi skill.

## Nguồn, giấy phép và thay đổi

[Manifest nguồn](../.agents/skill-sources.json) lưu commit đầy đủ, đường dẫn nguồn,
SHA-256 bản gốc, SHA-256 các file local, giấy phép và mô tả biên tập.
Mỗi thư mục skill có bản LICENSE từ đúng commit nguồn. Không tự cập nhật upstream.

- Superpowers: giữ bằng chứng trước kết luận và chu trình red/green/refactor;
  bỏ yêu cầu nạp skill cho mọi phát biểu tích cực, bắt xóa code và lặp kiểm tra
  chỉ vì sang lượt mới. Không bắt TDD cho hỏi đáp/tài liệu.
- Addy Osmani: giữ xác định nút thắt, lựa chọn thay đổi và đo lại; bỏ ví dụ
  React/Node và tối ưu hình ảnh không liên quan; thêm reference về dữ liệu/lưới.
- Cloudflare: giữ điều tra dựa trên browser/network/trace; thu hẹp vào triệu chứng,
  bỏ công thức gọi MCP cố định và hướng dẫn tự cài công cụ.
- jovd83: giữ mô hình tải, baseline, tăng tải có giới hạn và phân tích percentile;
  dùng Locust/quy tắc KNJSC, không mang mặc định k6 hoặc ngưỡng lỗi 1% sang dự án.
- Tất cả: metadata ngắn, tự chọn bật, không thêm agent phụ hay quy trình phê duyệt
  lặp lại. Reference là hướng dẫn biên tập có chọn lọc, không là bản sao toàn manual.

Khi cập nhật: chọn commit mới, review thay đổi và giấy phép, biên tập lại phần liên
quan, kiểm cấu trúc/liên kết, cập nhật hash và đánh giá lại routing. Không ghi đè
bản local bằng upstream mà bỏ qua các điều chỉnh này.

## Danh mục để dành — chưa cài

- Đã được giữ trong danh mục: `property-based-testing`, `tanstack-virtual`, `ag-dev`.
  Chỉ bổ sung skill grid ứng với nền tảng được chốt; không mặc định dùng cả hai thư viện.
- Còn ở mức đề xuất: `systematic-debugging`, `supabase-postgres-best-practices`,
  `differential-review`.
- Chưa viết: `knjsc-data-performance`, `knjsc-permission-and-ui-verification`,
  `knjsc-concurrent-editing`. Chỉ tách khi có quy trình lặp lại đủ rõ.

## Kiểm tra tĩnh và đánh giá thực tế

Kiểm tra tĩnh ngày 09.09.2026: **ĐẠT** — 5/5 skill qua `quick_validate.py`;
đã đối chiếu 5 entrypoint cốt lõi (trước bước gom 10 skill), YAML hợp lệ, tên/mô tả, automatic invocation,
liên kết local, giấy phép, hash nguồn/local và kích thước. Kiểm diff/trailing whitespace.
Không chạy suite ứng dụng hoặc kiểm tải chỉ để kiểm tra tài liệu skill.

Bảng dưới là **kịch bản nghiệm thu routing**, chưa phải kết quả chạy agent.
Chạy như công việc bình thường, không gọi đích danh skill để kiểm tự chọn.
Không thực hiện thay đổi dữ liệu chỉ để lấp đầy bảng đánh giá.

| Tác vụ đại diện | Kỳ vọng | Trạng thái |
|---|---|---|
| Hỏi đáp hoặc chỉnh tài liệu | Không kéo theo TDD, kiểm tải hay tài liệu grid | Chờ tác vụ thực tế |
| Sửa lỗi lưu ô | TDD và verification; chỉ thêm chuyên môn khi có lý do | Chờ tác vụ thực tế |
| Điều tra lag cuộn | web-perf; performance-optimization khi chuyển sang phương án sửa | Chờ tác vụ thực tế |
| Tối ưu truy vấn | performance-optimization; không tự audit trình duyệt | Chờ tác vụ thực tế |
| Kiểm tải 10–20 người trên môi trường được phép | performance-testing và verification | Chờ tác vụ thực tế |

Mỗi lần ghi: tác vụ/ngày, skill và reference thực sự đọc, số byte hoặc token có
nguồn đo, số lần gọi công cụ của tác vụ, kết quả và phần chưa kiểm. Không đo được
token thì ghi “không có số đo”, không suy ra token từ số dòng.

Đạt khi skill được khám phá, không tự kích hoạt sai rõ ràng, không nạp tất cả
references, không mở rộng phạm vi và kết luận có bằng chứng. Sau đủ 5 tác vụ,
sửa mô tả hoặc nội dung trùng trước khi thêm skill. Mặc định vẫn giữ bộ 5.
