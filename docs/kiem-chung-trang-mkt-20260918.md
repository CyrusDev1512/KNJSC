# Kiểm chứng trang MKT hoàn thiện — 18.09.2026

Nền `d05293d`, nhánh `codex/crm-update-solar-ui`, máy ảo Claude Code (không tới được VPS). Trong lúc làm,
phiên khác đẩy ADR-036 (một bảng vận đơn, `84ee0f7`) nên hai quyết định của đợt này đánh số **037/038**
và commit được rebase lên `84ee0f7`; sau rebase chạy lại `pytest -m "not cham"` toàn bộ (xem bảng).
Quyết định: [ADR-037](quyet-dinh/037-ma-nhan-su.md), [ADR-038](quyet-dinh/038-bao-cao-marketing-hoan-thien.md),
[ADR-031 bổ sung](quyet-dinh/031-tien-theo-quoc-gia-va-pttt.md). Kế hoạch năm đợt đã được chủ dự án
duyệt trong phiên; bàn giao bằng diff (commit local, chưa push, chưa phát hành).

## Phạm vi

Mã nhân sự THUANLT xuyên hệ thống; bảy thị trường / tám loại tiền; nộp báo cáo không giới hạn
số lần trong ngày; Kế toán xem và sửa mọi báo cáo; Tệp khách hàng; Doanh thu Marketing suy ra
từ vận đơn và Hóa đơn/Doanh thu theo nhãn; Chọn nhanh kỳ. **Không** gồm Báo cáo Nội dung (D8),
hạn nộp (N1/H8), bố cục ba trạng thái của Việc A.

## Môi trường

PostgreSQL 16 cục bộ cổng 5434, Redis 6379, venv Python 3.11 + Django 5.2.6, Chromium của
Playwright. DB pytest `test_knjsc_db`; DB diễn tập `knjsc_mkt` dựng từ đầu; không đụng DB nào khác.

## Kiểm tự động

| Lượt | Lệnh | Kết quả |
|---|---|---|
| Sau Đợt 1 + 2 | `pytest -m "not cham"` toàn bộ | 2508 đạt, 12 bỏ qua, **2 đỏ** — hai bài còn so tên đăng nhập (`test_danh_sach_chon`, `test_delivery_daily`), đã đổi sang `employee_code` |
| Sau Đợt 3 + 4 + 5 | `pytest -m "not cham"` toàn bộ | **2518 đạt, 12 bỏ qua, 0 đỏ** (298 s) |
| Đợt cuối (trước rebase) | `pytest` đầy đủ gồm bài `cham` và `trinh_duyet` | **2536 đạt, 18 bỏ qua, 2 xfail, 3 lỗi** (392 s) — ba lỗi đều ở `crm/tests/test_luoi_dong_trong_va_ghim_e2e.py` ("Playwright Sync API inside the asyncio loop" khi chạy chung); chạy riêng: 2 đỏ vì `wait_for_function` quá 15 s, **đúng như trên nền `d05293d` chưa có thay đổi này** (worktree riêng) → lỗi môi trường máy ảo, không do đợt này |
| Sau rebase lên `84ee0f7` (commit `582aa66`) | `pytest -m "not cham"` toàn bộ | **2490 đạt, 9 bỏ qua, 0 đỏ** (260 s; ít bài hơn vì ADR-036 xoá 8 tệp kiểm cũ) |
| Truy vết | `tests/test_truy_vet.py` | đạt: `docs/04` 219 tiêu chí (206 tự động, 13 thủ công), 182/206 đã có bài kiểm, 24 hoãn không đổi |
| Migration | `makemigrations --check --dry-run` | "No changes detected" |

Bài kiểm mới: `org/tests/test_ma_nhan_su.py` (AC-37.1→36.6), `reports/tests/test_markets_currencies.py`
(AC-38.1), `reports/tests/test_ke_toan_bao_cao.py` (AC-4.7, 4.8), `reports/tests/test_mkt_derived_revenue.py`
(AC-38.2, 37.3), `reports/tests/test_customer_segment.py` (AC-38.4), `reports/tests/test_date_presets.py`
(AC-38.5). Phân quyền kiểm hai chiều ở mỗi bài (Staff/Manager bị từ chối, Kế toán không bỏ báo cáo
người khác, Staff không thấy tiền người khác, Staff không thêm tuỳ chọn). 20 bài cũ đổi kỳ vọng từ
tên đăng nhập sang mã, hoặc từ K/J sang Hóa đơn ÷ Doanh thu.

## Diễn tập máy sạch (`scratchpad/dien-tap-may-sach.sh`)

DB mới → `migrate` → `tao_bang_van_don` → `du_lieu_mau` → `configure_erp_reports` →
`configure_delivery_daily_report` → `gan_ma_nhan_su_cu` (xem trước, ghi, chạy lại) →
`configure_erp_reports` lần hai → `migrate` ngược/xuôi ba migration mới → `check`: **tất cả OK**, 20 s.

- 12 tài khoản mẫu tự nhận mã khi tạo: `quantri=VIENQT, sale.manager=BAOLQ, sale.leader=DUNGTV,
  sale.leader2=ANHPQ, sale.staff=HANT, sale.staff2=HANGLT, sale.moi=MOINV, mkt.manager=TRANGDT,
  mkt.leader=NAMVH, mkt.staff=ANHPM, vd.manager=CHIBK, vd.staff=TUHV` (đúng `docs/tai-khoan-mau.md`).
- `bao_cao_mkt` sau cấu hình: cột `ngay, marketer, so_mess, cpqc, so_don, doanh_so, hoa_don, cpo,
  gia_mess, cpqc_doanh_so, aov, san_pham, tep_khach_hang, thi_truong, loai_tien, ti_le_chot`;
  không còn `doanh_thu` nhập tay và `hoa_don_doanh_thu`; Tệp khách hàng 9 giá trị mặc định;
  Thị trường 7, Loại tiền 7 (+VND khi cột có sẵn); `ReportSource.columns` có `invoice`, `segment`,
  `currency`, không có `revenue`. Biểu mẫu `bc_mkt_ngay` có 11 trường, không có Doanh thu.
- `gan_ma_nhan_su_cu` trên máy sạch: 0 hồ sơ thiếu mã (tự gán lúc tạo), 0 dòng đổi — đúng vì dữ liệu
  mẫu Marketing ghi họ tên tự nhập, không phải tên đăng nhập, nên giữ nguyên.
- **Lưu ý đã thấy khi diễn tập:** `migrate org 0004` (quay lui) xoá cột nên **mất mọi mã**; chạy
  xuôi lại thì hồ sơ rỗng mã cho tới lần lưu kế tiếp hoặc `gan_ma_nhan_su_cu`. Ở lượt Chrome đầu,
  người chưa đăng nhập lại (`mkt.leader`) hiện tạm tên đăng nhập ở cột Nhân sự cho tới khi chạy lại
  lệnh gán mã (9 hồ sơ, 3 dòng báo cáo đổi). Trên VPS không có bước quay lui này; thứ tự phát hành
  trong `daily-tasks.md` chạy `gan_ma_nhan_su_cu` ngay sau migrate.

## Chrome (server dev 8020 trên `knjsc_mkt`, Chromium 1440×900 và 390×844)

Ảnh ở `kiem-thu/trang-mkt-2026-09-18/`, ghi chép máy ở `ket-qua.json`.

| Bước | Kết quả |
|---|---|
| Admin tạo tài khoản: gõ họ tên "Lê Thưởng Thuận", rời ô | ô Mã tự điền **THUANLT** (`01`); lưu → mã THUANLT, tên đăng nhập THUANLT (`02`) |
| Đăng nhập `thuanlt` (chữ thường) | vào được, bị đưa tới đổi mật khẩu lần đầu (FR-1.4) (`03`) |
| `mkt.staff` nộp báo cáo ngày hai lần | ô Marketer chỉ đọc hiện `ANHPM`; có ô Tệp khách hàng; hai lần đều 302 về Lịch sử; banner "Hôm nay bạn đã nộp biểu mẫu này 2 lần… không đè bản cũ" (`04`); Lịch sử hiện `ANHPM · Phạm Minh Anh` (`05`) |
| Kế toán (`ketoan.kiem`, mã SOATTK) | Lịch sử thấy báo cáo của mọi bộ phận (`06`); mở Sửa báo cáo Marketing, đổi Số Mess, lưu → về trang báo cáo, có "Lịch sử chỉnh sửa" (`07`) |
| Báo cáo tổng hợp MKT (`mkt.manager`) | cột: Ngày, Nhân sự, Leader, Số Mess, CPQC, Số đơn, Doanh số, **Doanh thu**, Hóa đơn, CPO, Giá Mess, CPQC/Doanh số, Hóa đơn/Doanh thu, AOV (`08`). Tháng này có 5 dòng mẫu cũ **chưa có loại tiền** nên các chỉ tiêu tiền để trống kèm cảnh báo (đúng ADR-032); |
| Chọn nhanh | bấm "Hôm nay", "7 ngày" → hai ô ngày đổi và gửi ngay, nút được đánh dấu (`08b`, `09`) |
| Hôm nay + Thị trường Canada (chỉ dòng có loại tiền) | Đơn vị tiền CAD; **Doanh thu 100** = 60 + 40 của hai vận đơn CAD hôm nay phân công `mkt.staff` (đơn chưa phân công 999 và đơn của `mkt.leader` không có dòng báo cáo hôm nay không vào); Hóa đơn/Doanh thu = 45.298.000 ÷ 100 = 452.980 (`08c`); theo nhân viên chỉ `ANHPM · Phạm Minh Anh` với cùng số |
| Lọc Tệp khách hàng = Filipino | chỉ dòng có tệp; Doanh thu và Hóa đơn/Doanh thu để trống theo đúng ADR-038 (`10`) |
| Theo nhân viên | `ANHPM · Phạm Minh Anh`, `NAMVH · Vũ Hoài Nam` — mã trước, tên sau (`11`) |
| 390 px | trang tổng hợp hiện được, bộ lọc xếp dọc (`12`) |
| Lỗi JS | không có lỗi trang; console chỉ báo `ERR_CERT_AUTHORITY_INVALID` khi tải Google Fonts qua proxy của máy ảo (không phải lỗi ứng dụng) |

## Chưa kiểm / còn nợ

- Chưa chạy trên VPS và domain thật (không tới được từ máy ảo) — làm theo mục phát hành trong
  `daily-tasks.md`, gồm bước xem trước bảng mã.
- Bố cục ba trạng thái, chip bộ lọc (Việc A của bàn giao CLI) chưa làm; chip `tep` và nút Chọn nhanh
  phải được giữ khi làm.
- Báo cáo Nội dung (CTR/CPM/video) — đợt sau; tỉ giá KRW chờ kế toán; hạn nộp N1/H8 để mở.
- Dữ liệu mẫu Marketing (`du_lieu_mau`) ghi họ tên tự nhập vào ô Marketer và không có loại tiền —
  là dữ liệu giả từ trước, giữ nguyên để không đổi kịch bản mẫu.
