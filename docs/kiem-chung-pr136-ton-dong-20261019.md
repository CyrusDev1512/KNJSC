# Kiểm chứng PR #136 và lỗi tồn đọng — 19.10.2026

## Phạm vi và quyết định

Chủ dự án duyệt sửa theo nhóm nguyên nhân; xác nhận Manager đọc **toàn bộ đơn hàng/vận đơn**,
không mở phạm vi báo cáo hay dữ liệu nghiệp vụ khác. Giữ quyền sửa, quyền Leader và Quản trị chỉ Admin.
PR #136 là biên bản rà soát, không phải bản sửa mã. Không làm lại TL đã có bản sửa còn hiệu lực.

Mốc đầu việc sau fetch: `Staging 2d5fb0465f46a94626ba52b651c0495adc4a0643`,
`main 3bfa9e61fa48c792a6350b8499a88b63622252fc`, PR #136 head `10b110fd`.
Đây là mốc kiểm chứng local, không khẳng định GitHub/VPS luôn ở các SHA này.

Bản kết hợp: `codex/tl136-kiem-thu-tong-hop`, từ cùng `Staging`, gom thay đổi chưa commit của
các nhánh A–F và Manager bên dưới. Checkout gốc của chủ dự án được giữ nguyên.
**Chủ dự án yêu cầu commit, push và mở PR nháp về Staging ngày 19.10.2026. Chờ kiểm tay và duyệt merge; không tự gộp hoặc cập nhật VPS.**

## Trước và sau theo nhóm

| Nhóm / TL | Trước | Sau ở bản local | Giới hạn kiểm chứng |
|---|---|---|---|
| A — 14, 113, 114, 08, 115 | ACK bỏ phiên khối, dán qua ranh giới có thể lưu 99/100; ACK riêng nuốt mốc của người khác; poll cũ làm mới sai lúc | Giữ phiên; kiểm đủ ID duy nhất trước khi tạo nháp; ACK yêu cầu đồng bộ kế tiếp; bỏ phản hồi poll lỗi thời. Trạng thái Trùng của dòng liên quan được làm mới qua đồng bộ | Playwright tái hiện 99/100 trước sửa; sau từ chối khối lệch, tải lại và lưu đủ 100. Đồng bộ qua chu kỳ poll hiện có, không phải realtime push |
| B — 04, 10, 09, 120, 32 | Tiền JSON so chuỗi; sai bộ lọc bị bỏ qua/500; ngày giờ gán nhãn Ngày lỗi; thứ tự cùng giá trị không ổn định | So numeric có kiểm tra ép kiểu; lọc số/ngày có kiểu, sai trả lỗi rõ; lấy ngày Việt Nam từ datetime; thêm PK làm khoá phụ | Kiểm chuỗi tiền khác độ dài/giá trị thập phân, số quá lớn, bộ lọc sai và ngày giờ. Không đổi tỷ giá/precision dữ liệu |
| C — 06, 19, 20, 24, 119 | Lỗi đọc lại quyền có thể xoá nháp; thao tác lỗi vẫn ghi Đã lưu; lỗi ô khó tìm; lỗi DB tạm thời trả HTML500 | Giữ nháp khi lỗi mạng/500; trạng thái Lỗi lưu bền; đánh dấu đúng ô và tên cột; 40P01/40001/55P03 trả JSON503 có thể thử lại sau rollback | Kiểm sự cố mạng, lỗi quyền, retry/biên nhận, ô lỗi và trạng thái điện thoại; lỗi DB khác vẫn báo lỗi thật |
| D — 11, 121 | Số dòng ERP và tiến độ tính lại có thể lộ số đếm toàn bảng | Đếm cùng phạm vi DataRecord; poll chỉ báo ID tác vụ tính lại | Không đổi watermark toàn bảng đã chốt, không trả dữ liệu qua mốc |
| E — 12, 25, 26, 118, 122, 123 | Xoá nhiều dòng tăng SQL theo dòng; tính lại N+1/cấu hình cũ; nộp trước mọi lô; xoá cột vô ích vẫn tính lại | Ghi trạng thái/audit/đơn gốc theo lô; khoá cấu hình và đọc lại mỗi lô; giới hạn lô đang xử lý; ngừng nộp thêm khi lỗi; gom PENDING và bỏ cột một lượt | 30 dòng xoá/khôi phục mỗi lượt <60 SQL (trước xoá 601); 180 dòng tính lại <30 SQL (trước191). Không suy p95/100k từ ngân sách SQL |
| F — 27, 29, 30, 33, 112, 124 | Công cụ dùng endpoint cũ, chọn nhầm dòng thật; static không phục vụ; chạy lại seed/mật khẩu; tính lại có thể đo no-op | Runner riêng có static; JSON/CAS; chỉ PERF-*; giữ dữ liệu không seed; mọi HTTP lỗi được tính; tính lại fixture có thay đổi thật và kiểm kết quả | Đã smoke 1.000 dòng/2 người/20s, không kiểm tải 300k hoặc chứng nhận 100 người |
| G — 28, 31 | Tài liệu còn mô tả mốc theo người và renderer HTML/HTMX cũ | Đồng bộ docstring/AC/ADR với watermark và lõi JSON; ghi rõ số đo cũ là lịch sử | `grid_service.cell_url` đã không còn ở baseline, không viết lại phần đã bỏ |
| Manager — 116 và phần Manager của117 | Manager có thể thấy ít vận đơn hơn Leader; không mở được bảng nếu chưa có dòng của mình | Manager mọi bộ phận đọc đơn gốc/vận đơn toàn công ty, kể cả chưa có đơn; xuất/thống kê theo cùng phạm vi | Không mở thêm quyền sửa/phân công/Quản trị. Phần Leader117 giữ nguyên để chủ dự án chốt riêng |

## Bằng chứng từng nhóm

Mọi database kiểm thử riêng; không dùng VPS hoặc dữ liệu khách. Các số dưới là các lượt kiểm khác nhau,
**không cộng lại thành tổng test duy nhất**.

| Lượt | Kết quả thực tế |
|---|---|
| A: backend trước sửa + browser khối/poll/tiền | 22 backend; 6 browser đạt (84,15s), ca Trùng thêm đạt riêng (17,03s) |
| Manager: hồi quy các module liên quan | 2.233 đạt, 1 skip fixture xuất, 61 deselected (344,11s); desktop/390px 2 browser đạt |
| B: forms_builder + lưới/báo cáo | 524 đạt, 21 deselected (114,49s); 4 browser đạt (20,22s) |
| C: CRM không browser/chậm | 590 đạt, 1 skip, 23 deselected (191,60s); 15 browser đạt (56,05s) |
| C: hết phiên/đổi tài khoản | 8 browser đạt (75,82s); 1 cảnh báo teardown DB vì kết nối test còn mở, không tính cảnh báo là đã xử lý |
| D: đếm/phạm vi/thư mục/poll | 37 đạt (14,22s) |
| E: core, tính lại, xoá dòng/cột | 1.018 đạt, 16 deselected (54,85s) |
| F: công cụ và fixture | 17 đạt (9,48s), kiểm Compose hợp lệ |
| B/F/audit bổ sung trên bản kết hợp | 32 đạt (10,90s); gồm lọc chỉ ký hiệu tiền, phép tính lại có ghi thật, audit theo lô |
| Browser bản kết hợp | 28 đạt (172,75s), 9 file liên quan |
| Hồi quy server bản kết hợp | 3.691 đạt, 5 lỗi kỳ vọng cũ, 1 skip, 368 deselected (466,78s); cả 5 đã có kết quả đạt ở lượt kiểm lại 58 ca bên dưới |
| Ma trận quyền + biên bộ lọc sau cập nhật kỳ vọng cũ | 58 đạt (23,24s); 2 kỳ vọng Manager và 3 kỳ vọng bỏ lọc sai được thay theo quyết định mới |
| Truy vết / chuyển đổi / đồng bộ skill | 47 đạt (28,61s) |
| Schema | `makemigrations --check --dry-run`: No changes detected |

Đã đối chiếu ID test trong XML: đủ 5 lỗi của lượt tổng xuất hiện và đạt ở lượt kiểm lại; không còn ca lỗi chưa xử lý trong nhóm đã chạy. Không gọi lượt tổng ban đầu là xanh, không sửa báo cáo XML gốc. Skip là fixture đo cuộn (`test_scroll_fixture.py`); marker `cham`/`trinh_duyet` được loại ở lượt server, browser chạy riêng. Lượt tổng trước đó gặp lỗi quyền ghi XML ở cuối; đã chạy lại bằng user container phù hợp và giữ báo cáo đầy đủ.

Bài hành vi chính được tái hiện đỏ trước sửa. Hai bài bổ sung audit/tính lại fixture viết sau triển khai
để kiểm trực tiếp kết quả; không gọi chúng là bằng chứng RED trước sửa.

## Smoke công cụ tải

Lệnh: `python scripts/kiem-tai-kn-crm.py --rows 1000 --users 2 --seconds 20`.
Lượt đầu HTTP không lỗi nhưng runner lỗi in Unicode trên Windows; đã sửa stdout UTF-8.
Lượt lại: `python scripts/kiem-tai-kn-crm.py --giu-du-lieu --users 2 --seconds 20 --smoke`, exit0:
22 HTTP, 0 lỗi; 13 đọc, 1 ghi, 4 poll và 4 đăng nhập. p95 quan sát: đọc360ms, ghi170ms, poll13ms.
**Mẫu quá ít, không nghiệm thu SLA hoặc khả năng chịu tải**. Báo cáo ở `storage/perf/kn-crm.html`
trong worktree công cụ (không đưa dữ liệu/báo cáo chạy vào Git).

Không đo trong lượt này: 300.000 dòng, 100 người/5 phút, 10 người dùng +5 Sale lên đơn,
50k-marked-slow, p95 VPS, tác vụ tính lại song song dưới tải. Không gọi các mục đó là đã đạt.

## Nhánh và kiểm tay còn cần

Nhánh nguồn local: `codex/tl136-dong-bo-luoi`, `codex/tl136-kieu-du-lieu`,
`codex/tl136-loi-luu-nhap`, `codex/tl136-dem-pham-vi`, `codex/tl136-tinh-lai-hang-loat`,
`codex/tl136-cong-cu-kiem-tai`, `codex/manager-xem-toan-bo-don`.
Bản kết hợp là bản bàn giao, chứa tất cả thay đổi và tài liệu thống nhất. Nhánh nguồn chỉ lưu từng nhóm trước khi đối chiếu kết hợp.

Chủ dự án kiểm local: dán qua khối/lọc, sửa và tải lại, 2 tab đồng bộ, mất mạng rồi Thử lại,
xoá/khôi phục bằng Admin, bộ lọc tiền/ngày; Manager nhìn đơn ngoài bộ phận nhưng không được sửa thêm.
Bàn giao theo yêu cầu commit/push: nhánh việc → PR nháp Staging → kiểm tay local → main → VPS.
Không đóng phần Leader117, TL71 hoặc TL83 trong đợt này.

## Mở bản local

- ERP: http://localhost:18062/ ; CRM: http://localhost:18063/ .
- Hai container xem thử `knjsc-tl136-preview-erp`/`knjsc-tl136-preview-crm` mount mã bản kết hợp,
  database fixture riêng `knjsc_loadtest` (1.000 dòng PERF và mẫu), không phải dữ liệu local nghiệp vụ.
- Cookie riêng `tl136_session`/`tl136_csrf`, không thay phiên của cổng 8020/8021.
- Có các tài khoản mẫu của `du_lieu_mau`: `sale.manager`, `vd.staff`, `quantri`; mật khẩu mẫu theo lệnh seed.
  Không có tài khoản hoặc mật khẩu thật được sao chép.
- Chưa chạy worker/beat cho preview; không coi luồng background thật là đã nghiệm thu trên preview này.
- Đã dừng container chạy tải sau smoke; database/Redis fixture giữ lại cho preview, không xoá volume.

## Lệnh và tệp bằng chứng

- Server: `pytest -m "not cham and not trinh_duyet" -vv --tb=short --show-capture=no -rs -p no:cacheprovider`.
- Kiểm lại kỳ vọng: `pytest crm/tests/test_o_chu_bien.py tests/test_ma_tran_phan_quyen.py`.
- Browser: `test_phien_khoi_va_dong_bo`, `test_loc_so_co_kieu`, `test_loi_luu_giu_nhap`,
  `test_manager_doc_don_cong_ty`, `test_sap_xep_khong_giat`, `test_luoi_hoi_nhe`,
  `test_tien_chuoi_may_e2e`, `test_admin_xoa_dong`, `test_xoa_chi_tiet_san_pham_e2e` trong `tests/e2e/`.
- Docker test image/runtime riêng, mount worktree; PostgreSQL riêng, `RUN_MIGRATIONS=0`.
- Kết quả local (bị Git ignore): `storage/test-results/tl136-integration.xml`,
  `tl136-updated-expectations.xml`, `tl136-browser.xml`, `full.log`.
- `git diff --check` đạt; không có thay đổi schema cần migration. Checkout gốc giữ nguyên file chưa theo dõi.

Kiểm sẵn sàng preview qua HTTP thực: đăng nhập fixture `sale.manager` thành công, JSON lưới trả 200 và đủ 1.000 dòng. Đây là kiểm endpoint, không thay kiểm tay của chủ dự án.
