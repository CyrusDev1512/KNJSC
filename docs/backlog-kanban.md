# Bảng việc — To do / In progress / Finished / Far Plan

**In progress / chờ nghiệm thu — CRM-Optimization (11.09):** mã sau cờ tắt đã có;
đã đo đủ trước/sau 100k/300k × 10/20 và bài bền cấu hình 30 phút. Render/cold
Thống kê, backlog xuất và tăng RSS app còn cần cải thiện/điều tra. Không suy nguyên nhân toàn bộ
16 lỗi lịch sử; chưa kết luận năng lực VPS. [Kiểm chứng](kiem-chung-crm-optimization-20260911.md).

**11.09.2026 — Ba lựa chọn Lên đơn bắt buộc chọn rõ:** Quốc gia/Loại tiền/PTTT mặc định rỗng, chọn hợp lệ mới lưu; đơn kế tiếp trở lại rỗng. 105 test đạt, Chrome 1440/390 đạt, trần 10 truy vấn giữ đạt; không migration/dependency, chưa commit/push. [Bằng chứng bổ sung](kiem-chung-len-don-gio-admin-20260911.md).


**11.09 — Cột ghim Vận đơn mới:** triển khai và hồi quy tự động đã xong;
100k/300k lệch 0 px, cache 10, không tăng request. Còn nghiệm thu thủ công
zoom trình duyệt thật/trackpad; chi phí render tăng nhẹ được ghi rõ tại
[biên bản](kiem-chung-ghim-cot-20260911.md). Không gộp với lỗi API trước đó.

**11.09.2026 — Bổ sung giờ lưu và Admin tự đứng đơn (thay quyết định chọn Sale):** Ngày giờ cập nhật HH:mm trên form, thông báo lấy timestamp thực tế đã lưu; bỏ dropdown, Admin/Sale tự đứng bằng mã đăng nhập. Admin thử nghiệm chưa thuộc Sale dùng Sale/team trống, giữ hồ sơ. 117 test đạt; Chrome 1440/390 đạt; kiểm tải đọc 10/20 Admin: 4.782 request đo/0 lỗi, p95 cao nhất 76,38 ms trên fixture nhỏ. Không migration mới, chưa commit/push. [Kiểm chứng và giới hạn](kiem-chung-len-don-gio-admin-20260911.md).


**11.09.2026 — Ngày/đơn vị/mã nhân viên khi lên đơn:** đã kiểm chứng local: Ngày Việt Nam chỉ đọc; chọn hộp/cái/chiếc/túi từng sản phẩm, snapshot trên đơn/vận đơn; mã đăng nhập cho định danh nghiệp vụ và lịch sử. Migration 0006 đã kiểm xuôi/ngược DB test và áp dụng xuôi local. Hồi quy 984 đạt/2 lỗi giao diện thống kê có sẵn; lượt focused cuối 72 đạt; Chrome 1440/390 đạt; Locust đọc 10/20 đạt 4.618 request/0 lỗi. Chống lặp hoãn, không kết luận năng lực toàn CRM. [Bằng chứng và giới hạn](kiem-chung-len-don-20260911.md). Chưa commit/push.


**11.09.2026 — Điều hướng ERP/thư viện/Lên đơn CRM:** đã triển khai local theo ADR-023. Giữ Bảng dữ liệu ERP; sửa Biểu mẫu thiếu người tạo, gộp hai tab đúng quyền; chuyển nhập đơn và xem đơn gốc sang CRM. Kiểm thử, số đo và giới hạn tại [báo cáo bàn giao](kiem-chung-erp-hub-20260911.md). Chưa commit/push.

**11.09 — Lưới Vận đơn mới:** sửa Admin/nhập trong ô đã kiểm Chrome/E2E;
chạy bền snapshot 7449e73 đã đủ 30 phút; còn 16 lỗi đọc/22.460 request và
lọc Quốc gia p95 1,35s chưa đạt. Hai bài rà giao diện Thống kê
có lỗi từ trước, chưa xử lý trong tác vụ lưới. Chi tiết và giới hạn:
[kiểm chứng 11.09](kiem-chung-master-admin-20260911.md).

Bản nhìn theo cột của `backlog.md`. `backlog.md` vẫn là nơi ghi **vì sao** (quyết
định Q, lỗ hổng K, nhật ký); tệp này chỉ trả lời **đang ở cột nào**. Lỗi cụ thể
kèm mức nghiêm trọng, chỗ sai, blocker và ảnh hưởng nằm ở `test-log.md`; ở đây
chỉ tham chiếu mã `TL-xx`.

Cập nhật: 07.09.2026. Ai làm xong việc nào thì kéo dòng đó sang cột kế tiếp
trong cùng lượt sửa mã, không để dồn.

Mức ưu tiên: **P0** chặn nghiệm thu hoặc mất/lộ dữ liệu · **P1** người dùng
gặp hằng ngày · **P2** khó chịu, có đường vòng · **P3** khi rảnh.

---

## To do

Xếp theo thứ tự nên làm. Mỗi dòng một PR nhỏ, có ảnh trước/sau hoặc bài kiểm.

| Ưu tiên | Việc | Liên quan | Nhánh đích | Ghi chú |
|---|---|---|---|---|
| P0 | Chặn Manager bộ phận khác tự cấp quyền Sửa qua màn Cấp quyền / Thu quyền | TL-01 | `main` | Lộ quyền; bài kiểm phải có chiều bị từ chối |
| P0 | Hết phiên 60 phút: mọi yêu cầu HTMX/fetch phải về màn đăng nhập, không báo "Đã lưu" | TL-02, TL-18 | `main` | Mất dữ liệu âm thầm; cùng gốc với "trang đăng nhập rơi vào ô" |
| P0 | Số ≥ 3 chữ số lẻ bị nhân nghìn khi Enter, dán, kéo điền, hoàn tác | TL-03 | `main` | Sai dữ liệu tiền âm thầm |
| P0 | Lọc khoảng cột tiền/ngày với chuỗi lạ trả 500 | TL-04 | `main` | Trang trắng |
| P0 | Thanh trên báo "Đã lưu" khi máy chủ trả 400; lời báo lỗi bị CSS giấu | TL-19, TL-20 | `main` | K28 — anh/chị gặp trong video 07.09 |
| P0 | PR #21: làm lại giao dịch sau deadlock mất dữ liệu; job tính lại kẹt RUNNING làm lưới ngừng cập nhật | TL-22, TL-23 | `claude/kiem-tai-kn-crm` | **PR #21 không gộp cho tới khi xong hai dòng này** |
| P1 | Tiêu đề bảng ngoài vận đơn màu vàng → xanh; ô trắng; chỉ ô cảnh báo mới vàng/đỏ | TL-21 | `main` | K28; yêu cầu gốc của anh/chị |
| P1 | Khôi phục dòng bỏ qua phạm vi quyền | TL-05 | `main` | Quy tắc 11 |
| P1 | Dòng trống / ô sửa kẹt sau 403/500, tự cập nhật dừng | TL-06 | `main` | |
| P1 | Sau khi chính mình lưu, lưới tự nạp lại và báo "Có dữ liệu mới"; dòng mới không khớp bộ lọc biến mất | TL-08 | `main` | |
| P1 | Sắp xếp không ổn định giữa các trang | TL-09 | `main` | |
| P1 | Cột tiền không mang nhãn Doanh thu sắp xếp và lọc theo chuỗi | TL-10 | `main` | |
| P1 | Màn Sửa cột cho bỏ cột hệ thống của bảng vận đơn | TL-13 | `main` | |
| P1 | Nghiệm thu bấm tay theo `docs/07` một đợt (V4, V5) | — | — | Việc của anh/chị, sau khi các P0 xong |
| P2 | Hoàn tác ghi đè sửa đổi của người khác không cảnh báo | TL-07 | `main` | |
| P2 | Trang chủ và trang chọn bảng đếm cả dòng ngoài phạm vi và dòng đã xoá | TL-11 | `main` | |
| P2 | Xoá 2.000 dòng tốn ~6.000 truy vấn | TL-12 | `main` | |
| P2 | Dán vượt trang tạo dòng mới thay vì ghi tiếp | TL-14 | `main` | |
| P2 | Định dạng ô ngoài phạm vi bị bỏ qua lặng lẽ thay vì 403 | TL-15 | `main` | Quy tắc 8 |
| P2 | Sửa một ô ghi cả dòng; sửa một ô không vẽ lại cột tính sẵn | TL-16, TL-17 | `main` | |
| P2 | Thêm/sửa cột tính sẵn trên bảng lớn chặn request (153 s ở 100.000 dòng) | TL-34 | `main` | PR #21 đã sửa; chỉ còn nếu PR #21 không gộp |
| P2 | PR #21: chỉ luu-o có làm lại khi deadlock; không gộp job tính lại; lỗi một lô không dừng các lô còn lại; `do_hieu_nang` đo tính lại không ghi; docstring lệch mã | TL-24 → TL-28, TL-31, TL-32 | `claude/kiem-tai-kn-crm` | Sau TL-22/23 |
| P2 | Chạy `scripts/kiem-tai-kn-crm.*` trên máy anh/chị và máy chủ thật, ghi số vào `docs/06` | K27 | — | Sau khi PR #21 gộp |
| P3 | Tệp tĩnh không được phục vụ khi chạy gunicorn (không nginx, không whitenoise) | TL-29 | `main` | Giai đoạn 8 sẽ có nginx |
| P3 | Script kiểm tải chạy `du_lieu_mau` nên đặt lại mật khẩu 12 tài khoản mẫu | TL-30 | `claude/kiem-tai-kn-crm` | |
| P3 | `tests/test_hieu_nang.py` vẫn xfail vì ngân sách 10 truy vấn | K24, TL-33 | `main` | Sau K27 lưới còn 13 |

## In progress

| Việc | Ở đâu | Trạng thái | Chặn bởi |
|---|---|---|---|
| Kiểm tải KN CRM 100 nghìn khách / 100 người (ADR-016) | PR #21 nháp, nhánh `claude/kiem-tai-kn-crm`, 5 commit | Đo xong, số ĐẠT trên máy ảo; **rà lại phát hiện TL-22 (mất dữ liệu) và TL-23** | Không gộp cho tới khi TL-22, TL-23 xong; anh/chị chốt Q67 "giờ chưa phải lúc tối ưu" |
| Bảng việc và nhật ký kiểm thử này | nhánh `claude/backlog-testlog` | Tạo 07.09 | — |

## Finished

- **11.09.2026 — Bàn điều hành KN CRM:** tổng hợp tối đa ba nguồn và chuyên sâu
  mọi bảng theo profile Marketing/Sale/Vận đơn/Chung; insight có bằng chứng và
  link xử lý, biểu đồ SVG, tách tiền tệ, giữ scope và tương thích thống kê cũ.
  [ADR-022](quyet-dinh/022-ban-dieu-hanh-kn-crm.md), AC-22.1–22.9. Hồi quy 159
  bài đạt; p95 20k Sale/100k Vận đơn/300k Vận đơn/tổng hợp lần lượt
  89,07/333,72/893,26/733,64ms; kiểm trình duyệt đủ ma trận trong test-log.

- **11.09.2026 — `vandonmoi`:** hoàn thiện đúng 10.000 dòng mẫu
  `MAU-20260910-*` trong Vận đơn mới bằng management command tái lập theo seed;
  giữ 500 danh tính cũ, thêm 9.500 dòng, chi tiết sản phẩm và phân công. Sửa ghi
  chú lỗi `?`, làm rõ ba cột ghim và toolbar theo phạm vi riêng của bảng mới.

- **09.09.2026 — `codex/sua-feedback`:** phân công Vận đơn mới và phạm vi theo
  tài khoản; bộ lọc nhanh/sản phẩm/thị trường/Marketing; xuất ngày/bộ lọc có
  mã nhân viên và kiểm quyền file nền. [ADR-020](quyet-dinh/020-phan-cong-loc-xuat-van-don-moi.md),
  AC-20.1 đến AC-20.7. H7 chưa làm; chưa commit/push trong tác vụ này.

Mọi thứ đã vào `main` (ở `3ab19a5`) hoặc đã xong trên nhánh. Số giai đoạn theo
`dashboard-tien-do.html`.

| Giai đoạn | Việc | PR | Quyết định |
|---|---|---|---|
| 0 → 6 | Nền tảng: đăng nhập, phân quyền ba cấp, bảng động, biểu mẫu, báo cáo, lên đơn, nhập/xuất Excel | — | ADR-001 → 008 |
| 7A | Nhập tệp bốn bước có xem trước, xuất kèm bộ lọc, tệp lớn chạy nền giữ 24 giờ | — | |
| 7B | Sao lưu `pg_dump` 02:00, giữ 30 bản, phục hồi bằng `scripts/restore.sh` | — | |
| 7C | Bảng tính vận đơn theo tệp thật, dịch vụ `bangtinh` 8021 | — | ADR-009 |
| 7D | Kiểm thử chín tầng: Playwright, Locust 50 người, 50.000 dòng, ma trận 45 ô, `docs/07` | — | |
| 7E | Bảng tính cho mọi bảng, viền ô, dòng trống, định dạng ô, thư mục | #4 | ADR-010 |
| 7F | Lưới như KN Demo: chọn vùng, dán, kéo điền, hoàn tác, chuột phải, 40 màu, hộp lọc, tự cập nhật | #5 | ADR-011 |
| 7G | KN CRM là app riêng, cây Bộ phận ▸ Quý ▸ Tháng | #5 | ADR-012 |
| 7H | Ô chọn có "Thêm mới…", màu cột, ngưỡng cảnh báo | #11 | ADR-013 |
| 7I | Bảng dữ liệu KN ERP chỉ để xem | #15 → #18 | ADR-014 |
| 7J | KN CRM có sidebar theo Teeze, trang chủ tổng quan, Leader như Manager, tạo bảng/nhập tệp/cấp quyền trong KN CRM, logo tự vẽ | #19 | ADR-015 |
| — | `KN JSC.bat` tự kéo mã, migrate khi mã đổi, báo rõ khi kéo thất bại | #6 → #10, #12 | |
| 7K (đo) | `seed_perf` 100.000 dòng + bảng Sale có cột tính sẵn; `do_hieu_nang` 25 đường kèm EXPLAIN; Locust 100 người bốn vai tự chấm; `scripts/kiem-tai-kn-crm.*` | #21 (nháp) | ADR-016 |
| 7K (sửa) | Ô lưới dựng bằng Python 638 → 154 ms; cột Trùng theo trang; `moi-nhat` không đếm dòng; `bulk_save` bằng VALUES; tính lại cột chạy nền 153 s → 19,6 s; 100 người p95 11 s → 0,85 s | #21 (nháp) | ADR-016 — **chưa gộp**, xem In progress |
| 7L | Vận đơn mới theo CRM Tân: hai bảng độc lập, ERP/CRM cùng luồng, chi tiết tiền từng sản phẩm, thống kê; 25 bài mới, toàn bộ hồi quy, migration hai chiều và giao diện desktop/mobile đều đạt | — | ADR-018 |
| 7L.1 | 10.000 vận đơn mẫu Canada/CAD có chi tiết, thanh toán, phân công; vùng ba cột nhận diện ghim rõ trên lưới | — | Nhánh `vandonmoi` · 11.09.2026 |
| 7M | Bàn điều hành KN CRM theo nguồn Marketing/Sale/Vận đơn/Chung; KNERP giữ báo cáo và thêm liên kết | — | ADR-022 |
| — | Rà lại toàn bộ KN CRM trên `main` và trên PR #21, ghi thành `test-log.md` | nhánh này | |

## Far Plan

Chưa tới lượt, không làm khi chưa có quyết định mới của anh/chị.

| Mã | Ý tưởng | Điều kiện để bắt đầu |
|---|---|---|
| S13 | Lưới KN CRM trả JSON, JS thuần vẽ ô, cuộn ảo — trang 20 KB thay vì 300 KB | Q67: chỉ khi máy thật đo đỏ hoặc khi làm S10 |
| S14 | Máy chủ đẩy sự kiện (SSE) thay cho 100 tab hỏi mỗi 8 giây | Cùng lúc với S13 |
| S15 | Cột tính sẵn để Postgres tính, không đi qua Python và chỉ mục GIN | Đụng cấu trúc nền tảng, phải hỏi trước |
| S10 | Công thức gõ ở thanh công thức (`=SUM(A1:A5)`) | Chờ "cách thứ ba" anh/chị chốt; đo lại kiểm tải khi có |
| GĐ 8 | Máy chủ thật, tên miền con cho KN CRM, nginx phục vụ tệp tĩnh, đo tải trên máy chủ, KN ERP dùng tốt trên điện thoại | Chờ V1 |
| S1 → S9, S11, S12 | Đồng bộ hai chiều đơn ↔ vận đơn, chia sẻ quyền cho cấp dưới, thông báo chủ động, kênh báo sự cố, bảng xoay chiều, nhiều người cùng sửa thời gian thực, thư mục lồng nhau, xuất Excel mang định dạng, chiều cao dòng, quản lý sản phẩm | Xem `backlog.md` mục 3 |
| N9 | Thống kê theo thị trường trong báo cáo | Chờ nguồn số liệu (Q36) |

### 10.09.2026 — Chín hạng mục lưới mới, thay quyết định lưu thủ công

Đã duyệt autosave, chọn hàng/màu xanh, hai chế độ, fs/c/bg, lịch sử và
đối chiếu conflict, Admin chọn Sale, thứ tự tạo tăng dần và số hàng từ 1.
Đã triển khai và kiểm chức năng trên database test: suite rộng 1.049 pass,
6 fixture skip được tách kiểm; 90 test tác động và E2E cuối đạt. Hiệu năng
lọc 300k còn chưa đạt; chạy bền dừng theo yêu cầu chủ dự án, để phiên sau
chạy lại đủ 30 phút. Không đổi H7/lưới cũ.
Xem [quyết định ADR-021](quyet-dinh/021-luoi-master-va-thong-ke-crm.md) và
[báo cáo chín hạng mục](kiem-chung-master-nine.md).
