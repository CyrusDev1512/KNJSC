# Kiểm chứng — Cuộn Báo cáo tổng hợp: lăn chuột trên bảng không kẹt, bớt giật (TL-63) — 28.09.2026

Nhánh `claude/cuon-bao-cao-tong-hop` tách từ `main` (`a0313be`), máy ảo Claude Code, PostgreSQL 16,
Chromium 141 không màn hình (vẽ bằng CPU, không GPU), DPR 1.

Chủ dự án báo: bấm qua lại Gộp/Không gộp rồi lăn chuột giữa thì "lag và chậm hơn rất nhiều"; con trỏ đặt
trên bảng thì không cuộn được.

## Dữ liệu và cách đo

- Cơ sở dữ liệu riêng: `du_lieu_mau`, `configure_erp_reports`, thêm 20 marketer (4 team, mỗi team 1 leader),
  718 báo cáo MKT nộp qua `daily_service.submit` trong 30 ngày (khoảng 20 % người–ngày nộp hai lần) và 1.819
  vận đơn gán Phụ trách Marketing. Kịch bản nạp và đo nằm ngoài kho (máy ảo), không commit.
- `runserver` settings dev, tài khoản `quantri`, Báo cáo Marketing kỳ 30 ngày, cỡ trang mặc định 100 nhóm
  (tối đa, nên Không gộp đang ở mức nặng nhất: 6 bảng, 133 dòng, 693 ô dính, khoảng 3.000 nút; Gộp: 2 bảng,
  55 dòng, 184 ô dính, khoảng 1.400 nút).
- Lăn bằng Playwright `mouse.wheel` (100 px một nấc), con trỏ ở giữa phần nhìn thấy của khung bảng. Khung
  hình đếm bằng trace Chrome (`PipelineReporter`: hiển thị / rớt), thời gian `BeginMainFrame`, `Paint`,
  `Layerize`, `RasterTask` trong cửa sổ cuộn.

## Nguyên nhân

1. **Kẹt.** Khung bảng `.report-table-scroll` (cao `100vh - 230px`, `overflow:auto`) nằm trong khung cuộn
   của trang (`main.noi-dung`) và có `overscroll-behavior: contain` — chép từ bản vẽ
   `docs/tham-khao/ban-ve-bao-cao-tong-hop-20260918.html`, không có ADR chốt. Quy tắc này chặn cuộn truyền
   từ bảng ra trang:
   - bảng vừa khung theo chiều dọc nhưng tràn ngang (bảng thật nhiều cột): lăn trên bảng không cuộn gì —
     bảng 0/0, trang 0/626 px; lăn ngoài bảng thì trang cuộn 400 px;
   - bảng dài: lăn trên bảng chỉ cuộn bên trong khe (lúc mở chỉ lộ 252 px ở đáy thẻ), hết bảng thì dừng —
     bảng 4.549/4.549 px, trang 0/626 px.

   Đối chứng trên trang tối giản (khung cuộn ngang được, dọc không, nằm trong khung cuộn dọc): có `contain`
   thì trang 0 px, bỏ thì 750 px; có hay không ô dính không đổi kết quả.
2. **Giật.** Khung bảng không có nền (trong suốt) trên thẻ nền 96 %: mỗi khung cuộn trình duyệt raster lại
   nội dung. Không gộp nặng hơn Gộp khoảng 2,7 lần việc luồng chính khi cuộn vì nhiều bảng và ô dính hơn.
3. **Bấm qua lại Gộp/Không gộp** là tải lại cả trang (0,4–0,55 s trên máy thử); trang cũ nằm chờ thu rác
   (sau 30 lần: 38 trang, 238.000 nút, 22 MB; ép thu rác về 3 trang, 1,6 MB — không rò rỉ). Đo cuộn ngay sau
   mỗi lần bấm, 30 lần liên tiếp: việc luồng chính ổn định (Không gộp 99–124 ms, Gộp 37–46 ms cho 15 nấc) —
   **không chậm dần**, nên không sửa phần này.

## Sửa

`app/static/css/solarpunk.css`, `.report-table-scroll`: bỏ `overscroll-behavior:contain`, thêm
`background:var(--surface)` — cùng màu nền thẻ kết quả ở cả nền sáng lẫn tối (`rgb(255,253,247)` /
`rgb(25,44,35)`), mắt không thấy khác; chế độ Toàn màn hình vốn đã đặt nền này. Giữ
`.bang-cuon{overscroll-behavior-x:contain}` (vuốt ngang trên bàn di chuột không làm trình duyệt lùi trang).
Khung dùng chung cho Báo cáo tổng hợp và Bảng dữ liệu dạng báo cáo (`bang_xem.html`) nên sửa cả hai. Không
đổi template, JS, số liệu hay phân quyền.

## Kết quả

Lăn 80 nấc với con trỏ trên bảng (cùng kết quả ở 1440×900 và 1920×960; số trong ngoặc là 1920×960):

| Trường hợp | Trước sửa | Sau sửa |
|---|---|---|
| Bảng ngắn — Gộp, 7 ngày, 1 người (dọc 625/625, ngang 1.007/1.695) | bảng 0, trang **0**/626 | sau 5 nấc trang 500 px; 80 nấc trang **626/626** (566/566) |
| Bảng dài — Không gộp, 30 ngày (bảng 4.549 px) | bảng 4.549/4.549, trang **0**/626 | 5 nấc đầu: bảng 500, trang 0 (bảng cuộn trước); 80 nấc: bảng 4.549/4.549, trang **626/626** (566/566) |

Chế độ Toàn màn hình sau sửa: lăn 80 nấc, bảng cuộn hết (4.613/4.613 px); khung trang vẫn
`overflow:hidden` nên đứng yên (0/0), thanh điều khiển giữ ở mép trên — bỏ `contain` không làm gì phía sau
trôi theo.

Trace 80 nấc, Không gộp, hai lần mỗi bản. Ba dòng đầu vá CSS ngay lúc tải (route) để cùng điều kiện; dòng
cuối là tệp đã sửa thật trên đĩa:

| Bản | Khung rớt | Raster | Layerize | BeginMainFrame |
|---|---|---|---|---|
| Trước sửa | 81 / 78 | 682 / 642 ms | 138 / 128 ms | 646 / 617 ms |
| Chỉ bỏ `contain` | 79 / 78 | 1.108 / 653 ms | 216 / 131 ms | 1.087 / 642 ms |
| Bỏ `contain` + nền đặc | **0 / 1** | **124 / 122 ms** | **60 / 59 ms** | **540 / 539 ms** |
| Tệp đã sửa (đo lại) | 4 / 1 | 127 / 123 ms | 60 / 61 ms | 538 / 553 ms |

Bỏ `contain` sửa lỗi kẹt; nền đặc là thứ làm hết rớt khung.

| Bài | Trước sửa | Sau sửa |
|---|---|---|
| `reports/tests/test_bo_cuc_bao_cao_e2e.py::test_lan_chuot_tren_bang_khong_ket` (AC-22.19, Chromium) | **đỏ**: bảng dài — hết bảng trang 0 px; bảng ngắn (1000 px, tràn ngang) — trang 0 px. Lần viết đầu dùng màn 1440 px, bảng thử không tràn ngang nên không tái hiện; đã đổi 1000 px và thêm tiền đề "tràn ngang" | xanh |
| Trọn tệp `test_bo_cuc_bao_cao_e2e.py` (AC-22.13, AC-22.17, AC-22.19) | — | 3 đạt |
| `tests/test_truy_vet.py` + `core/tests/test_giao_dien.py` (docs/06 → 278 / 265 / 242) | — | đạt |
| Suite đầy đủ `-m "not trinh_duyet and not cham"` | — | **2.799 đạt, 1 bỏ qua, 0 đỏ** (mã thoát 0) |

Lệnh (từ `app/`, Postgres đang chạy):

```
python -m pytest --ds=knjsc.settings.test reports/tests/test_bo_cuc_bao_cao_e2e.py
python -m pytest --ds=knjsc.settings.test tests/test_truy_vet.py core/tests/test_giao_dien.py
python -m pytest --ds=knjsc.settings.test -m "not trinh_duyet and not cham"
```

Cảnh báo `database "test_knjsc_db" is being accessed by other users` lúc dọn cơ sở dữ liệu kiểm thử có cả
khi chạy riêng hai bài trình duyệt cũ — có sẵn, không do bài mới.

## Kiểm kĩ trước khi gộp (28.09.2026, theo lệnh chủ dự án)

Cùng máy chủ thử và dữ liệu giả ở trên, tệp CSS đã sửa (commit `8072b8e`), Chromium 1440×900 trừ khi ghi khác.
**25/25 mục đạt.**

| Mục | Kết quả |
|---|---|
| Mặc định Không gộp: khối toàn kỳ + mỗi ngày một bảng; bấm Gộp: khối toàn kỳ + một bảng mỗi ngày một dòng, URL có `gop=1` | đạt |
| Dòng TỔNG CỘNG toàn kỳ giống hệt ở Gộp và Không gộp (80.855 Mess, 7.690 đơn, 1.819 đơn TT…) | đạt |
| Đang ở trang 2 có lọc Team, bấm Gộp: giữ nguồn/kỳ/Team, về trang 1, chip Team còn | đạt |
| Bấm qua lại 20 lần: lần nào cũng đúng chế độ, 0 lỗi JavaScript, mỗi lần tải 0,43–0,64 s | đạt |
| Sau 20 lần bấm, lăn trên bảng: bảng cuộn trước (500 px sau 5 nấc, trang 0), hết bảng (4.549) thì trang tới cuối (626) | đạt |
| Lăn ngược lên: bảng về đầu trước (trang giữ 626), rồi trang về 0 | đạt |
| Tiêu đề cột vẫn dính đầu khung khi đã cuộn 1.500 px | đạt |
| Lăn ngang: bảng cuộn hết 782 px, cột tên ghim trái đứng yên, trang không trôi ngang lẫn dọc | đạt |
| Bàn phím sau khi bấm vào bảng: PageDown 585 px, End xuống cuối, Home về đầu | đạt |
| Toàn màn hình: bảng cuộn hết 4.613 px, khung trang đứng yên, Escape thoát | đạt |
| Cách xem Theo nhân viên / sản phẩm / thị trường / phòng ban: lăn trên bảng cuộn bảng rồi tới trang | đạt (4/4) |
| Bảng ngắn (Gộp, 7 ngày, 1 người; tràn ngang 688 px): lăn trên bảng thì trang cuộn hết 626 px | đạt |
| Màn hẹp 390×844: không tràn ngang; bảng cuộn trước, hết bảng (4.361) thì trang tới cuối (813) | đạt |
| Nền tối và nền sáng: nền khung bảng trùng nền thẻ kết quả | đạt |
| Bảng dữ liệu `bao_cao_mkt`: bảng cuộn trước (trang giữ nguyên), hết bảng thì trang tới cuối | đạt |
| Không lỗi JavaScript cả lượt; yêu cầu hỏng duy nhất là phông Google bị proxy máy ảo chặn | đạt |

Khung hình (trace, lăn 40 nấc xuống + 40 nấc lên): Không gộp mở mới rớt 0/199, sau 20 lần bấm rớt 5/185; Gộp
lăn **trên bảng** rớt 10/116 (bảng Gộp chỉ cuộn 1.469 px, phần còn lại chuyển sang cuộn trang — trước khi sửa
phần đó không cuộn gì). Cuộn trang với con trỏ **ngoài bảng** (Gộp, hai lần mỗi bản): CSS cũ rớt 23 và 29
khung, CSS mới rớt 1 và 0 — nền đặc của khung bảng làm mượt cả việc cuộn trang.

Hai lần viết đầu của kịch bản trượt vì cách đo, không vì mã: lỗi console `ERR_CERT_AUTHORITY_INVALID` là phông
Google bị chặn (yêu cầu hỏng duy nhất `fonts.googleapis.com`); ở màn 390 px và Bảng dữ liệu, lúc mở trang khung
bảng nằm dưới đáy khung nhìn nên con trỏ rơi vào thanh dock — đã sửa kịch bản cuộn trang cho bảng hiện ra
trước như người dùng.

## Chưa kiểm

- Máy thật của chủ dự án (Windows, GPU, tỉ lệ màn hình): số trên là Chromium không màn hình vẽ bằng CPU;
  cảm nhận thật cần thử trên máy. Nếu Chrome tắt "Dùng tính năng tăng tốc đồ hoạ khi có sẵn" thì bảng nhiều
  ô dính vẫn nặng hơn.
- Chưa đổi (đổi giao diện, chờ chủ dự án chốt): lúc mở trang khung bảng chỉ lộ khoảng 250 px ở đáy thẻ; bốn
  cột ghim trái; bấm Gộp/Không gộp vẫn tải lại cả trang.
- Firefox, Safari chưa thử.
- Chưa phát hành VPS.
