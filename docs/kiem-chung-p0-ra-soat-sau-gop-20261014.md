# Biên bản kiểm chứng — Rà sau khi gộp đợt P0: cây gộp thử, rà ngữ nghĩa giữa các PR, diễn tập chặng 2 bằng máy (14.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 14.10: "kiểm tiếp đi, chưa xong đâu đúng không". Trước đó mới kiểm từng PR so với `Staging`, chưa kiểm các PR với nhau và chưa ai dùng thử hệ thống thật |
| Cây kiểm | Cây gộp thử `0c5f25c` = `Staging` `b2b0198` + 16 PR đợt P0, gộp tuần tự theo thứ tự ghi ở #130. Sau khi chủ dự án gộp xong, `Staging` `03e5d99` trùng **từng tệp** với cây này (`git diff` rỗng), nên mọi kết quả dưới đây áp dụng cho `Staging` hiện tại |
| Liên quan | #131 (phiên khác) ghi lại chính lần gộp: thứ tự, cách gộp #127/#129/#130, quét liên kết 424 trang, lệnh xoá nhánh. Biên bản này không lặp phần đó, chỉ ghi phần rà ngữ nghĩa và diễn tập |
| Môi trường | Máy ảo Claude Code trên web: Python 3.11, Django 5.2.17, PostgreSQL 16, `pg_restore` 16.15, Chromium của Playwright 1.56, Node 22 |
| Kết luận | **Đạt.** Không lỗi mã nào chỉ lộ khi gộp. Mọi bước của đợt P0 đạt khi dùng thử trên máy chủ thật. Lộ thêm 7 lỗi, ghi TL-105 → TL-111 (`docs/test-log.md`): 3 lỗi do đợt P0, đều mức S3, không chặn; 4 lỗi có từ trước. Chưa sửa mã, chờ duyệt cách sửa |

## 1. Kiểm tự động trên cây gộp thử

| Kiểm | Lệnh | Kết quả |
|---|---|---|
| Gộp | Gộp tuần tự 16 nhánh; thêm 120 cặp PR gộp thử với nhau (`git merge-tree`) | Không xung đột. Không PR nào thêm migration |
| Cấu hình | `check --settings=knjsc.settings.test`; `check --deploy --fail-level WARNING` cho ERP (`prod`) và CRM (`bangtinh`, `BANGTINH_GOC=prod`) với biến môi trường giả; `makemigrations --check --dry-run` | 0 vấn đề; "No changes detected" |
| Bộ chính | `pytest -m "not trinh_duyet" -rfEs` | **3.852 đạt**, 7 bỏ qua (các bài kiểm tải có sẵn), **0 đỏ**, 15 phút 56 giây |
| e2e lượt 1 | `pytest tests/e2e -m trinh_duyet -vv -o faulthandler_timeout=120` | **79 đạt**, 2 bỏ qua có sẵn, 0 đỏ, 8 phút 7 giây |
| e2e lượt 2 | `pytest -m trinh_duyet --ignore=tests/e2e -vv -o faulthandler_timeout=120` | **30 đạt**, 9 bỏ qua như CI, 0 đỏ, 4 phút 46 giây |
| Sao lưu, phục hồi thật | `pytest core/tests/test_sao_luu.py -m cham` | 3/3 đạt, chạy với `pg_restore` thật |
| Script Node đơn vị | 12 script `kiem-thu-*unit*`, `master-working-copy`, `master-row-geometry`, `date-inputs` | **12/12 đạt**, kể cả ba script đỏ sẵn trên `Staging` cũ (#129 và #130 đã sửa) |
| Truy vết TL | `grep` mỗi mã TL-01, 02, 03, 13, 18, 23, 90 → 99 trong bài kiểm | Mã nào cũng có ít nhất một tệp bài |

Lần chạy bộ chính đầu tiên ra toàn lỗi kết nối: máy ảo vừa khởi động lại nên Postgres tắt. Bật lại Postgres rồi chạy lại,
kết quả ở bảng là lần chạy lại.

## 2. Rà ngữ nghĩa giữa các PR

Hai PR có thể cùng sửa một luồng theo hai hướng. Khi đó git gộp không báo gì nhưng hành vi sai. Một workflow chỉ đọc
chia năm nhóm, mỗi nhóm một agent đọc diff của các PR liên quan trên cây gộp thử. Mỗi phát hiện có một người kiểm lại cố
bác, chạy bài thăm dò trên bản chép riêng, so cả với từng PR đứng riêng lẫn `Staging` cũ.

| Nhóm | PR | Phát hiện | Kết luận của người kiểm lại |
|---|---|---|---|
| Đăng nhập, phiên, middleware | #121, #129, #125, #118 | Không có | — |
| Quyền và nhật ký Từ chối | #127, #122, #120, #125, #126 | 403 ở kho chứng từ không ghi Từ chối | Bác: có từ trước, không PR nào đụng, gộp không đổi gì. Vẫn ghi TL-111 |
| | | Manager mất bộ phận: 403 không ghi Từ chối, `luu-json` nhận HTML | Bác như lỗi gộp: #127 đã chứa sẵn #125. Vẫn là lỗi thật của #125: TL-106 |
| Tiền và báo cáo | #124, #119, #129 | Hoàn tác một lượt dán có tạo dòng vẫn nhân nghìn | Bác: lưới CRM chỉ phục vụ bảng vận đơn, bảng này không cho tạo dòng (`protect_table`), nên không ai đi tới đoạn mã đó |
| | | `soViet` coi chữ người gõ chưa lưu là chuỗi máy | Bác: không chỉ lộ khi gộp; trên lưới vận đơn chỉ đi tới được nếu Manager tự thêm cột Tiền vào `van_don`. Ghi lại để làm khi lưới phục vụ bảng khác |
| Tác vụ nền, sao lưu | #117, #123, #116, #115 | Phục hồi xong thì lượt canh báo Kẹt nhầm cho tác vụ sao lưu trong bản chụp | **Đứng**: lỗi thật, một mình #117 gây ra. TL-105 |
| Dữ liệu mẫu, tài liệu | #118, #125, #121, #127, #126, #130, #113 | `docs/tai-khoan-mau.md` ghi `giamdoc` giao việc được cho mình | **Đứng**: lỗi tài liệu, đã sửa cùng PR này |
| | | Tài liệu ghi "chưa gộp / nháp, chờ gộp" cho các PR đã gộp | **Đứng**, chỉ sai khi gộp: đã sửa `docs/test-log.md` và `docs/08`. `CLAUDE.md` do #131 sửa |
| | | `docs/08` (01, 04, 06 và tệp chính) còn tả hành vi trước P0: fixture thiếu 4 vai, khoá DEBUG chưa có bài, `/quan-tri/login/` còn form, TL-01 còn cho qua, bộ đếm AC cũ | **Đứng**: đã sửa từng câu sau khi đối chiếu mã |

## 3. Diễn tập chặng 2 bằng máy

**Đây không thay chặng 2 của chủ dự án.** Chặng 2 vẫn phải bật bằng `KN JSC.bat` trên máy mình, vì #115 đổi launcher.

Cách dựng:
- Hai agent, mỗi agent một cặp máy chủ thật (`runserver` ERP với `knjsc.settings.dev`, CRM với `knjsc.settings.bangtinh`)
  và một DB riêng.
- Dữ liệu dựng đúng thứ tự launcher: `migrate` → `tao_bang_van_don` → `du_lieu_mau` → `configure_erp_reports` →
  `configure_delivery_daily_report`.
- Playwright đi các bước của `docs/08-ke-hoach-kiem-thu/06-kiem-tay-chang-2.md` mà đợt P0 đụng tới, cộng sáu bước P0-14
  ở mục 4 biên bản #129.
- Bắt mọi lỗi JS và mọi phản hồi 500, rồi đọc log máy chủ.

| Bước | Tài khoản | Kết quả |
|---|---|---|
| S1: đăng nhập ERP, sang CRM không hỏi lại; chiều ngược | `sale.staff`, `sale.staff2` | Đạt |
| Bốn tài khoản mới đăng nhập được ở cả hai cổng; menu đúng vai | `giamdoc`, `vd.leader`, `kt.staff`, `cskh.staff` | Đạt |
| Kế toán không có "Nộp báo cáo ngày"; gõ thẳng `/bao-cao/` thấy câu báo, mã 200; POST bằng biểu mẫu Sale 403; `sale.manager` vẫn thấy mục | `kt.staff`, `sale.manager` | Đạt |
| K1-8: Giám đốc không có Quản trị; `/nhat-ky/`, `/quan-tri/` bị chặn; `/bang/`, `/nhan-su/` mở được; `/tai-lieu/tai-len/`, `/tai-nguyen/moi/` 403; ô lưới chỉ đọc, POST `luu-json` 403; hộp Chi tiết không sửa được; sáu cửa ghi ở CRM 403, không 500; Nhật ký có đủ 6 dòng Từ chối | `giamdoc`, `quantri` | Đạt |
| K1-2: sai mật khẩu 5 lần, lần 6 đúng thì báo khoá tạm 15 phút, ở cả ERP lẫn CRM | `sale.staff` | Đạt. Nhưng dòng nhật ký khoá bị lược chữ và ghi lặp: **TL-108** |
| K1-13 / P0-8: `/quan-tri/` chưa đăng nhập về trang đăng nhập tiếng Việt; Admin sai 6 lần thì khoá; Manager mở `/quan-tri/` nhận 403 kèm Từ chối | admin phụ, `sale.manager` | Đạt |
| K2-8 / TL-01: `mkt.manager` tự cấp quyền Sửa bảng Sale | `mkt.manager` | Đạt: 403, Grant không tạo, có dòng Từ chối |
| P0-9: không hạ cấp hay khoá được Admin cuối; không chọn được trưởng nhóm khác bộ phận; bắt buộc bộ phận; Manager bị gỡ bộ phận nhận 403 với đúng câu ở 6 trang | `quantri`, `vd.manager` | Đạt. Nhưng log có `ERROR` kèm traceback, không có Từ chối, trang 403 không có lối ra: **TL-106** |
| K3-11: CSKH chỉ thấy 3 đơn được giao, ghi ô 403; Kế toán có Tôi/Toàn bộ, Thống kê tách CAD và USD khớp DB từng số | `cskh.staff`, `kt.staff` | Đạt. Nhưng link Thống kê mất `nguon` sau Tôi/Tìm (**TL-109**) và Áp dụng bỏ bộ lọc (**TL-110**) |
| K5-12: Giám đốc xem Tổng hợp (0 nút ✎), Lịch sử (0 Sửa, 0 Bỏ), `/bao-cao/` 403 | `giamdoc` | Đạt |
| S2: lên đơn Canada, Zelle, giá `10,50` | `sale.staff` | Đạt: "Đã lưu đơn DH-1410-0001…", giờ Việt Nam |
| S5 / K3-3: sửa Ghi chú, "Đã lưu", F5 còn, Lịch sử ô có mã và giờ Việt Nam | `vd.staff` | Đạt |
| P0-3: đổi nhãn cột Tiền ở ERP; giá trị `1234.567`, `250.75` giữ nguyên, Tổng hợp không đổi | `quantri` | Đạt. Bước gõ, hoàn tác, dán `0,125` trên lưới **không làm được** trên sản phẩm thật: lưới CRM chỉ có bảng vận đơn và ô tiền của nó là ô tổng của Chi tiết. Bài e2e `tests/e2e/test_tien_chuoi_may_e2e.py` đã phủ phần này bằng bảng giả |
| P0-7: bỏ cột khoá, vế công thức, cột nối biểu mẫu, cột chuẩn vận đơn | `quantri` | Đạt: 400 kèm lời đỏ, cột còn nguyên, không 500. Tải lại trang sau đó ra 405 trắng: **TL-107** |
| P0-4 / K5-8: Tổng hợp Sale có CAD và USD; Gộp/Không gộp; Xuất Excel | `sale.manager` | Đạt: mỗi loại tiền một dòng TỔNG CỘNG, không cộng lẫn; tệp có đủ sheet |
| P0-14 a: hai tab, tab 2 đăng xuất lúc tab 1 đang gõ ô lưới | `vd.staff` | Đạt: báo hết phiên sau 5,6 giây kèm liên kết, chữ còn, Enter thì "Lỗi lưu" |
| P0-14 b: đăng nhập lại đúng người, Thử lại | `vd.staff` | Đạt: "Đã lưu", lịch sử ô thêm đúng 1 dòng |
| P0-14 c: người khác đăng nhập, Thử lại | `vd.staff`, `vd.manager` | Đạt: 409 "Tài khoản vừa đăng nhập khác người mở trang…", lời dẫn có mã, không liên kết |
| P0-14 d: Lên đơn lúc hết phiên, đăng nhập lại rồi Lưu | `sale.staff` | Đạt: không dán trang đăng nhập, chữ còn, ra đúng một đơn |
| P0-14 e: hộp Chi tiết và ô phân công lúc hết phiên | `vd.staff` | Đạt: hộp không đóng, lời báo ở đầu, lưu được sau khi đăng nhập lại |
| P0-14 f: ERP, nút HTMX lúc hết phiên | `sale.manager` | Đạt: cả trang về đăng nhập, đăng nhập xong về đúng trang (giữ `?dang=tho`, `gop=1`) |
| K1-10: thời hạn phiên 60 giây và 120 giây | `vd.staff` | 60 giây: hết phiên đúng. 120 giây: lượt hỏi 8 giây giữ phiên sống mãi, đúng G6/P1-21 đã biết, ADR-053 ghi chưa đổi |

Log máy chủ:
- Không có phản hồi 5xx nào, không có lỗi JS nào.
- Mọi `WARNING` đều là 400, 403, 409 có chủ đích.
- Ngoại lệ duy nhất là 3 dòng `ERROR` của TL-106.

Ghi nhận nhẹ, không cấp mã:
- Tóm tắt Lên đơn in tiền dạng máy `10.50`. ADR-052 đã ghi phần hiển thị chưa làm.
- Ô Trưởng nhóm liệt kê leader mọi bộ phận. Sai bộ phận thì báo lỗi lúc lưu.
- Trang đăng nhập ERP sau `HX-Redirect` không có lời "phiên đã hết". ADR-053 giữ ERP như cũ.

## 4. Chưa kiểm

- Docker và `KN JSC.bat`: máy ảo không dựng được image.
- Firefox, Safari: máy ảo chỉ có Chromium.
- Chặng 2 của chủ dự án trên máy mình.
- VPS: kiểm cookie CSRF host-only trùng tên (ADR-053, Ràng buộc), các câu SQL chỉ đọc trước khi phát hành (`docs/08` mục 9).
- Ảnh chụp và kịch bản của buổi diễn tập chỉ nằm ở máy ảo, không đưa lên kho.
