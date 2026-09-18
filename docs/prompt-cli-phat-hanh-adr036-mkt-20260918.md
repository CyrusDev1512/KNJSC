# Prompt dán vào Claude Code CLI (máy chủ dự án, có SSH tới VPS)

Toàn bộ phần dưới đây là **một prompt**, chép nguyên vào CLI. Kế hoạch năm đợt trang MKT đã làm
xong và đã push (`49068b7` trên `codex/crm-update-solar-ui`); máy khác đã chốt thêm bảy PTTT
(`3748ea9`, đóng TL-44). Việc "nốt" là phát hành VPS gộp ADR-036 + bảy PTTT + ADR-037/038 rồi
làm Việc A (bố cục Báo cáo tổng hợp).

---

Đọc `CLAUDE.md` và `AGENTS.md` trước. Nhánh làm việc là `codex/crm-update-solar-ui`; `git fetch`
rồi checkout, HEAD phải từ `3748ea9` trở lên ("Bay PTTT theo sheet Van don cua Quan tri noi bo";
trên đó chỉ còn commit tài liệu). Đây là máy có SSH tới VPS; Claude Code trên web không tới được
nên các đợt dưới đây đang chờ phát hành. Làm theo AGENTS.md: trình kế hoạch ngắn (mục tiêu, phạm vi, cách làm, cách
kiểm) để tôi gật rồi tự làm trọn; chỉ commit, push khi tôi bảo; không dán mật khẩu, khoá, IP vào
chat. Thông tin SSH và đường dẫn kho trên VPS: `<tôi điền>`.

## Đọc trước, không kiểm lại những gì biên bản đã ghi

- `docs/daily-tasks.md` hai mục đầu: "Bàn giao phát hành VPS — 18.09.2026 (tối): trang MKT hoàn
  thiện (ADR-037, ADR-038, ADR-031 bổ sung)" và "Bàn giao cho Claude Code CLI trên máy chủ dự án —
  18.09.2026 (chiều): phát hành ADR-036, một bảng vận đơn". Hai đợt này cùng bảy PTTT **phát hành
  chung một lần**.
- Bảy PTTT (`3748ea9`): mục "18.09.2026 (tối) — Bảy PTTT theo sheet Vận đơn" ở đầu `docs/backlog.md`,
  `docs/backlog-kanban.md`, `docs/test-log.md`. Migration `orders/0010` chỉ đổi choices;
  `tao_bang_van_don` bổ sung 5 lựa chọn cho cột `pttt`, `pttt_thuc_te` có sẵn; tệp thật vào đủ 221/221.
- `docs/quyet-dinh/036-mot-bang-van-don-duy-nhat.md`, `037-ma-nhan-su.md`,
  `038-bao-cao-marketing-hoan-thien.md`, mục "Bổ sung 18.09.2026" của `031-tien-theo-quoc-gia-va-pttt.md`.
- Biên bản: `docs/kiem-chung-mot-bang-van-don-20260918.md`, `docs/kiem-chung-trang-mkt-20260918.md`
  (ảnh ở `docs/kiem-thu/trang-mkt-2026-09-18/`). Khuôn phát hành các lần trước:
  `docs/kiem-chung-phat-hanh-vps-20260918-tl41.md`, `-excel.md`, `deploy/production/README.md`.
- `docs/backlog.md` ba mục 18.09 ở đầu tệp (Bảy PTTT, trang MKT, một bảng vận đơn) — phần "Còn nợ".

## Việc 1 — Kiểm trên máy này trước khi động vào VPS

1. `pytest -m "not cham"` từ `app/` (kỳ vọng ≈ 2.490 đạt, 0 đỏ; biên bản trang MKT đo trên
   `49068b7`, bảy PTTT chỉ sửa hai bài AC-11.9 và `test_market_currency`).
2. `pytest` đầy đủ gồm bài `cham` và `trinh_duyet`. Trên máy ảo web, ba bài của
   `crm/tests/test_luoi_dong_trong_va_ghim_e2e.py` đỏ **cả trên nền cũ lẫn mã mới** (lỗi môi
   trường: "Playwright Sync API inside the asyncio loop", `wait_for_function` quá 15 s). Chạy ở
   máy này để biết chúng có xanh không; đỏ thì ghi vào biên bản, **không sửa test để cho qua**.
3. `python manage.py makemigrations --check --dry-run` phải "No changes detected".

## Việc 2 — Phát hành VPS gộp ADR-036 + bảy PTTT + ADR-037/038

Tuân đúng thứ tự, mỗi bước in kết quả thật; **dừng hỏi tôi ở hai chỗ đánh dấu DỪNG**.

1. SSH vào VPS, **chỉ ghi nhận**: `docker compose ps`, tag image đang chạy, dung lượng DB, số dòng
   ba bảng `van_don`, `van_don_moi`, `van_don_db`, `showmigrations forms_builder org orders reports`.
   Báo tôi.
2. Backup DB, **kiểm phục hồi** vào DB tạm, đếm dòng ba bảng khớp. Không khớp thì không đi tiếp.
   **DỪNG 1**: tóm tắt và hỏi tôi xác nhận lệnh xoá cứng crmThuận + Vận đơn DB (không hoàn tác;
   biên bản ADR-036 ghi 6.667 + 2 dòng trên VPS).
3. `.env` trên VPS: `EXCHANGE_RATES_VND` **không bắt buộc** (mặc định trong mã đã theo sheet:
   USD=25500, CAD=17500, PHP=440, EUR=28500, JPY=155, AUD=17000); **không thêm KRW** — kế toán chưa
   chốt, bảng xếp hạng sẽ báo "Chưa có tỉ giá cho KRW" nếu có đơn Hàn Quốc, đó là chủ ý.
4. Build image `knjsc-app:<hash HEAD ngắn>-mkt` theo cách máy này vẫn làm (HEAD là `3748ea9` cộng
   một commit chỉ tài liệu, mã chạy y hệt `3748ea9`).
5. Dãy lệnh `deploy/production/README.md`, đúng thứ tự:
   `config --quiet` → `up -d db broker cache` → `static-owner` →
   `migrate --noinput` (kỳ vọng **năm** migration mới: `forms_builder 0014`, `org 0005`,
   `orders 0009`, `orders 0010`, `reports 0004`; ghi lại output) →
   `tao_bang_van_don` (nâng cấp tại chỗ `van_don`, in một bảng; cột PTTT nhận thêm 5 lựa chọn) →
   `xoa_bang_van_don_cu --dong-y-xoa-cung --backup-da-lam` (**chỉ sau DỪNG 1 được gật**; in số
   lượng từng loại) →
   `configure_erp_reports` (thêm cột Tệp khách hàng, bổ sung 4 thị trường/4 loại tiền vào cột có
   sẵn, gỡ trường Doanh thu nhập tay khỏi biểu mẫu MKT, bỏ cột tính `hoa_don_doanh_thu`) →
   `configure_delivery_daily_report` → `collectstatic --noinput` →
   `gan_ma_nhan_su_cu` (xem trước, in bảng "tên đăng nhập → mã" và số dòng ô danh tính sẽ đổi).
   **DỪNG 2**: gửi tôi bảng mã. Ai cần mã khác thì tôi gán tay ở Nhân sự → Sửa hồ sơ (gán rồi
   là cố định) rồi bảo bạn chạy `gan_ma_nhan_su_cu --xac-nhan`. Chạy lại lần hai phải đổi 0 dòng.
6. `up -d crm erp worker heavy beat proxy` → `nginx -t` → reload. Hai domain 200, log sạch.
7. Kiểm Chrome trên domain thật (ghi ảnh vào biên bản):
   - Thư mục Vận đơn chỉ còn một bảng "Vận đơn mới"; sidebar Admin không còn Bảng nhận đơn;
     `/bang-tinh/van_don/` mở được, có cột Trùng và nút Tôi/Toàn bộ; Lên đơn: ô PTTT có đúng bảy
     lựa chọn (Zelle, PayPal, Visa/Website, Cheque, Western Union, RIA, Money Gram), thử một đơn
     Western Union → dòng mới có chi tiết và lưới hiện "Western Union", rồi đánh dấu xoá; lưới
     `pttt`/`pttt_thuc_te` cũng có bảy lựa chọn; Thống kê `nguon=van_don`.
   - Tài khoản cũ đăng nhập như thường; cột Nhân sự/Leader và Lịch sử báo cáo hiện `MÃ · Họ tên`.
   - Admin tạo một tài khoản thử: ô Mã tự gợi ý từ họ tên (THUANLT), đăng nhập bằng mã gõ thường
     vẫn vào; khoá tài khoản thử sau khi kiểm.
   - Marketing nộp báo cáo ngày **hai lần** cùng ngày, có Tệp khách hàng; banner "đã nộp 2 lần".
   - Kế toán mở Lịch sử → Sửa một báo cáo Marketing → có Lịch sử chỉnh sửa.
   - ERP `/bao-cao/tong-hop/` nguồn Marketing: cột Doanh thu (chỉ có số khi vận đơn đã phân công
     Marketing và đã thu tiền, theo ngày lên đơn), Hóa đơn/Doanh thu, ô lọc Tệp khách hàng, hàng
     nút Chọn nhanh; dòng cũ chưa có loại tiền vẫn hiện cảnh báo lẫn tiền — đúng ADR-032.
8. Báo nhân viên trước hoặc ngay sau phát hành: định danh hiện mã · họ tên; Marketing nộp bao
   nhiêu lần cũng được và không nhập Doanh thu nữa; Kế toán sửa được số liệu mọi bộ phận; crmThuận
   và Vận đơn DB không còn; Bảng nhận đơn không còn; PTTT có bảy lựa chọn theo sheet Vận đơn.
9. Quay lui nếu hỏng: image cũ + backup. Lưu ý `reports/0004` không quay lui bằng `migrate` nếu đã
   có người nộp nhiều lần/ngày; `org/0005` quay lui thì mất mã đã gán; `orders/0009`, `orders/0010`
   chỉ đổi choices, quay lui không đụng dữ liệu.
10. Ghi `docs/kiem-chung-phat-hanh-vps-20260918-adr036-mkt.md` theo khuôn, một mục ngày ở đầu
    `docs/backlog.md`, cập nhật `docs/backlog-kanban.md`; commit "Ghi ket qua phat hanh <hash>
    (ADR-036, bay PTTT, 037, 038) tren VPS", **push khi tôi bảo**.

## Việc 3 — Việc A: bố cục Báo cáo tổng hợp theo bản vẽ

Mục "Bàn giao cho Claude Code CLI — 18.09.2026: bố cục Báo cáo tổng hợp + mã nhân sự" trong
`docs/daily-tasks.md`, **chỉ phần Việc A** (Việc B đã làm xong ở ADR-037), cùng bản vẽ
`docs/tham-khao/ban-ve-bao-cao-tong-hop-20260918.html`. Ba điểm phải giữ khi viết lại
`templates/reports/activity.html`, `static/css/solarpunk.css`, `static/js/report-filters.js`:
ô lọc **Tệp khách hàng** (`name="tep"`) và chip `tep`; hàng nút **Chọn nhanh**
(`.report-presets`, `.report-preset[data-tu][data-den]`, JS gửi form ngay); ô Nhân sự/Leader
đã là `MÃ · Họ tên`, không cắt chữ. Kiểm: `pytest -m "not cham"`, `core/tests/test_giao_dien.py`,
Chrome 1440/900/390 sáng-tối, biên bản `docs/kiem-chung-bo-cuc-bao-cao-tong-hop-<ngày>.md`.
Bàn giao bằng diff; commit/push khi tôi bảo.

## Không làm trong đợt này, chỉ hỏi tôi khi tới lượt

- TL-44 đã đóng ở `3748ea9` (bảy PTTT), không hỏi lại. Các bảng đặc tả khác của "Quản trị nội bộ"
  (trạng thái thanh toán "Thanh toán lỗi", 7 trạng thái vận chuyển, Đối soát kế toán) vẫn chờ tôi
  chốt — không tự làm.
- Tỉ giá KRW: chờ kế toán. Báo cáo Nội dung (CTR/CPM/video) và hạn nộp giữa ca/9h: đợt sau.
- TL-43 (lệnh xoá 50.000 dòng treo một lần) chưa tái hiện — chỉ ghi nếu gặp lại khi phát hành.
