# Bảng việc — To do / In progress / Finished / Far Plan

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
