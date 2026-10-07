# Biên bản — ERP mở rộng mặc định, phân trang dùng chung, lưới CRM bớt việc thừa (07.10.2026)

| Mục | Nội dung |
|---|---|
| Yêu cầu | Chủ dự án 07.10.2026: (1) ERP mở lên ở chế độ "Mở rộng giao diện ERP", không ảnh nền, thích nền thì bấm; (2) ba vấn đề của thanh phân trang dùng chung; (3) bốn chỗ máy chủ làm thừa ở lưới CRM (a–d) |
| Nhánh | `claude/phan-trang-luoi-erp-mo-rong` từ `Staging` `6a266b2`, PR nháp về `Staging` |
| Tiêu chí | AC-10.17 → AC-10.22 |
| Môi trường | Máy ảo; Postgres 16; hệ thống thật ERP 8020 / CRM 8021 (`runserver`) trên DB thử **385.034 dòng Vận đơn** (10.034 mẫu + `nap_khach_mau --so-khach 300000`), 2.291 báo cáo MKT; Playwright Chromium |

## 1. ERP mở rộng mặc định (AC-10.17)

| | Trước | Sau |
|---|---|---|
| Máy chưa từng chọn | Khung bo góc trên ảnh nền | Chế độ mở rộng: không ảnh nền, không viền, không lề |
| Bấm nút "Mở rộng giao diện ERP" | Bật mở rộng | Tắt mở rộng, hiện ảnh nền; máy đó nhớ (`localStorage` = "0") |
| Fullscreen API (như F11) | Không dùng | Vẫn không dùng — trình duyệt không cho tự bật khi chưa có thao tác người dùng |

Sửa một dòng ở `templates/base.html` (thiếu khoá = bật) và một dòng đồng bộ giữa các tab ở `solarpunk-shell.js`. Trang đăng
nhập không đổi. Script kiểm tay `scripts/kiem-thu-erp-table-focus.cjs` cập nhật theo mặc định mới.

## 2. Thanh phân trang dùng chung (AC-10.18, AC-10.19)

| Vấn đề | Trước | Sau |
|---|---|---|
| #1 Mất bộ lọc khi sang trang | Liên kết chỉ gồm `?trang=…&moi_trang=…` + chuỗi lọc màn hình tự truyền; Nhân sự và Nhật ký quên truyền nên sang trang 2 là mất bộ lọc | Thẻ `{% trang_url %}` giữ **mọi** tham số của URL đang mở, chỉ thay số trang; đổi cỡ trang thì về trang 1 |
| #2 Hai bảng trên một trang giẫm nhau | Trang Bộ phận và team: chuyển trang bảng này thì bảng kia về trang 1 | Tự hết nhờ #1 |
| #3 Tải lại cả trang | Mỗi lần bấm số trang hay đổi "Mỗi trang" | `phan-trang.js` chỉ thay vùng `data-vung-trang` (tải trang mới bằng fetch), URL đổi theo, Back/Forward tại chỗ; Báo cáo tổng hợp dùng chung đường đổi bảng của nút Gộp. Lỗi mạng, hết phiên, trang lạ → tải cả trang như cũ |

Màn hình được đánh dấu vùng: Nhân sự, Bộ phận (hai vùng), Nhật ký, Tác vụ, Bảng dữ liệu (danh sách, bảng thô, báo cáo
theo ngày), Lịch sử báo cáo, Báo cáo đã bỏ, Báo cáo tổng hợp (cả bản cũ), Công việc, Tài nguyên, Tài liệu, Biểu mẫu, Bảng tin,
Đánh giá nhân sự (hai trang), Bảng đã xoá (CRM). Không dùng `hx-push-url` để không chép số liệu vào `localStorage`.

Ghi chú: máy chủ vẫn dựng cả trang mới (trình duyệt chỉ lấy phần danh sách), nên lợi ở phía người dùng — không nháy trắng,
đầu trang và bộ lọc giữ nguyên — chứ chưa giảm việc của máy chủ.

## 3. Lưới CRM: bốn chỗ máy chủ làm thừa (AC-10.20 → AC-10.22)

| # | Trước | Sau |
|---|---|---|
| a | Mở lưới là đếm sẵn số dòng theo sản phẩm, thị trường, marketer cho panel Bộ lọc đang ẩn | Panel tải khi người dùng mở lần đầu (mảnh `bo-loc/?panel=1`) |
| b | Đổi bộ lọc tải lại cả trang HTML lưới chỉ để chép panel và chip | Chỉ lấy mảnh `bo-loc/` (chip; cả panel nếu đã mở), dựng không qua context processor |
| c | `moi-nhat/` bảng Vận đơn: `MAX + COUNT` theo phạm vi (JOIN phân công) mỗi 8 giây mỗi tab | `MAX(updated_at)` cả bảng qua chỉ mục — mốc vẫn đổi khi sửa ô, xoá, đổi phân công; không lộ dữ liệu |
| d | Mỗi lượt hỏi 8 giây gửi tới ~1.000 mã dòng đi kiểm quyền | Chỉ khi mốc đổi, cộng một lượt dự phòng mỗi 10 lần hỏi; máy chủ vẫn chặn mọi lần đọc/ghi ngoài phạm vi |

Đo phía máy chủ (Django test client trên DB thử 385.034 dòng, p50 của 10 lần, `do_luoi.py` chạy trên mã trước
`e9e45d0` ở worktree riêng và mã sau):

| Thao tác | vd.manager | vd.staff | sale.staff |
|---|---|---|---|
| Mở lưới | 2.924 → **389 ms** | 1.268 → **417 ms** | 1.914 → **628 ms** |
| Đổi bộ lọc | 2.896 → **33 ms** | 1.282 → **29 ms** | 1.853 → **31 ms** |
| Hỏi "có gì mới" (mỗi 8 s/tab) | 608 → **34 ms** | 117 → **30 ms** | 485 → **35 ms** |
| Kiểm quyền 1.000 dòng (mỗi lần như cũ; nay chỉ chạy khi mốc đổi) | 38 → 46 ms | 45 → 39 ms | 50 → 43 ms |
| Mở panel Bộ lọc (chỉ khi người dùng bấm) | — | — | 2.636 / 917 / 1.263 ms |

Riêng truy vấn mốc: theo phạm vi kèm COUNT 418–595 ms, theo cả bảng 0,8 ms.

## 4. Đi thử trên hệ thống thật (385.034 dòng)

| Bước | Kết quả |
|---|---|
| ERP (mkt.manager) mở lên | Đạt: mở rộng, không ảnh nền (đã xem ảnh chụp) |
| Lịch sử báo cáo → trang 2 | Đạt: tại chỗ, trang không tải lại, URL `?trang=2` |
| Báo cáo tổng hợp → trang 2 | Đạt: tại chỗ |
| Lưới Vận đơn (vd.manager) mở | Đạt: không gọi `bo-loc/` |
| Mở panel Bộ lọc | Đạt: tải panel một lần |
| Áp dụng lọc Thị trường | Đạt: chip "Quốc gia thuộc Canada", trang không tải lại |

## 5. Phát hiện ngoài phạm vi — chưa sửa, cần chủ dự án quyết

| Chỗ | Đo ở 385.034 dòng | Gốc |
|---|---|---|
| **Trang chủ KN CRM** `/` (trang sau đăng nhập CRM), khối "Bảng gần đây" | **150–258 giây** (vd.manager) | `tong_quan_service._bang_gan_day`: `COUNT(DISTINCT)` + `MAX` theo phạm vi qua JOIN đơn hàng/phân công trên mọi dòng |
| Menu khung KN CRM (mọi trang CRM) | 0,4 s mỗi trang | `crm/navigation.build`: `TableDef.objects.in_scope` với EXISTS trên dòng |
| Thư mục `/thu-muc/` | 1,5 s | Đếm dòng từng bảng theo phạm vi |
| Đọc một khối 100 dòng `du-lieu/` | 222 ms (vd.manager) – 929 ms (sale.staff) | `master_grid_service.stamp`: COUNT + MAX theo phạm vi để kiểm phiên bản khối — đúng điểm nghẽn biên bản 16.09 |

VPS hiện ít dòng nên chưa lộ; tới mốc 100.000 đơn/năm thì trang chủ CRM sẽ không mở được.

**Đã sửa ở nhánh `claude/crm-nhanh-bang-lon`** — [biên bản](kiem-chung-crm-nhanh-bang-lon-20261007.md).

## Bài kiểm

Mới (đều đỏ trên mã trước, xanh sau): `tests/e2e/test_erp_mo_rong_mac_dinh.py`, `core/tests/test_phan_trang_giu_tham_so.py`,
`tests/e2e/test_phan_trang_khong_tai_lai.py`, `crm/tests/test_bo_loc_tai_khi_mo.py`, `crm/tests/test_moc_moi_nhat_nhe.py`,
`tests/e2e/test_luoi_hoi_nhe.py`. Bài cũ đọc định dạng liên kết trang cũ hay `context["ben"]` của trang lưới: đổi sang đọc
theo tham số và mảnh `bo-loc/`, giữ nguyên ý kiểm.

## Kiểm toàn phần

| Lượt | Kết quả |
|---|---|
| `pytest -m "not trinh_duyet"` | 3.088 đạt, 7 bỏ qua, 0 đỏ |
| Bài trình duyệt lượt 1 (`tests/e2e`) | 53 đạt, 9 đỏ — đúng 9 bài `test_pha_luoi_ghi_chu` lỗi chứng chỉ Google Fonts của máy ảo, như `Staging` |
| Bài trình duyệt lượt 2 | Lần đầu 2 đỏ ở `reports/tests/test_bo_cuc_bao_cao_e2e.py`; sau khi sửa 16 đạt |

Hai bài đỏ đó dựng tiền đề theo khung thường (trang cuộn được; bảng thử ít cột tràn ngang đủ xa để cột Loại tiền chạm chỗ
đứng yên). Mặc định mở rộng làm khung rộng hơn nên tiền đề hết đúng. Đo trên dữ liệu thật ở 1366×768 thì hai chế độ cùng
bề rộng cột (Nhân sự 130 px) — không phải lỗi bố cục. Hai bài chạy ở khung thường như máy đã tắt mở rộng (`khung_thuong`).

## Chưa kiểm

- Đo trên VPS thật (2 nhân, 4 GB).
- Nhiều người cùng lúc với cách hỏi mới (lượt hỏi nhẹ hơn nên dự kiến tốt hơn, chưa chạy locust).
