# Kiểm chứng — Ghi chú tự giãn dòng, xuống dòng và ngắt dòng đúng (AC-11.44)

| Mục | Nội dung |
|---|---|
| Ngày | 23.09.2026, hai lượt trong ngày |
| Nhánh | `claude/ghi-chu-tu-gian-dong`, tách từ `b43b20e` |
| Yêu cầu | Bộ phận Vận đơn báo ghi chú bị ẩn, phải bấm mở hộp đọc mới xem được — bất tiện |
| Phạm vi lượt 1 | chỉ cột `ghi_chu` của bảng `van_don`; rộng 400 px; dòng tự giãn, trần 2000 px, kéo tay thắng |
| Phạm vi lượt 2 | chủ dự án hỏi *"ghi chú đã xuống dòng, cách dòng được chưa — phải confirm lại"*; chốt thêm: ô Ghi chú ở Lên đơn thành nhiều dòng, tệp Excel xuất ra bật Wrap Text |

---

## Câu trả lời cho "phải confirm lại"

Rà mã trước khi sửa (đường dẫn dưới `app/`): **ký tự xuống dòng đi qua hệ thống nguyên vẹn
nhưng người xem hầu như không thấy.**

| Khâu | Trước lượt 2 |
|---|---|
| Lưu & truyền | `\n` giữ nguyên (`record_service.parse_value` chỉ `strip()` hai đầu; `master_grid_service` trả chuỗi thô) |
| Gõ trong lưới | ô văn bản dài mở `<textarea>`; Enter xuống dòng, Ctrl+Enter xong — đúng docs/02:328 |
| Hiện trong ô | `.mg-cell` là `white-space:nowrap!important` → `\n` dồn thành dấu cách; chỉ dòng cao hơn 28 px mới được gắn `.mg-wrap` (`pre-wrap`). Lượt 1 chỉ giãn dòng khi ghi chú dài hơn 60 ký tự, không nhìn `\n` |
| Hộp đọc | giữ `\n` nhưng chỉ mở khi ô tràn — ghi chú ngắn nhiều dòng không có cách nào thấy ngắt dòng |
| Lên đơn | ô Ghi chú là `<input>` một dòng — không gõ được xuống dòng |
| Xuất Excel | ghi `\n` vào ô nhưng không đặt Wrap Text — Excel hiện một dòng |

Kịch bản có sẵn `docs/07:136` (AC-11.3, "gõ hai dòng → hiện hai dòng trong ô") đang sai mà
không bài kiểm nào bắt được. Dữ liệu giả đã có ca lỗi: `seed_perf.py:97`
`"Gọi trước khi giao\nKhách hay vắng"` (33 ký tự).

Lượt 1 còn 13 lỗ hổng khác được rà ra (đệm chiều cao khoá theo `id|rộng` không bao giờ cũ đi,
không đo lại sau khi sửa ô/dán/hoàn tác/lưu về/người khác sửa, nút đo gắn ngoài lưới nên không ăn
`line-height:1.45` và cỡ chữ `dd-co-*`, thu tay về 28 px bị chiều cao tự tính đè, poll cũ làm mọi
dòng co về 28 rồi bật lại, JS nhận diện theo mã cột `'ghi_chu'` trái CLAUDE.md, `aria-valuemax`
còn 400…). Lượt 2 bịt hết, danh sách đầy đủ ở kế hoạch đã duyệt.

---

## Đã sửa gì

| Tệp | Thay đổi |
|---|---|
| `app/orders/services/waybill_service.py` | `grid_column` trả `width: 400` **và cờ `auto_height: True`** cho riêng cột `ghi_chu`; lưới đọc cờ, không đọc mã cột |
| `app/static/js/master-grid.js` | thay bộ hàm đo: `cotTuGian`, `rongCot`, `noiDungO`, `vuaMotDong`, `doChieuCaoTheoLo`, `caoTuDong`, `caoDong`, `apLaiChieuCao(ids)`, `ketThucKeoCot`; đo khi có `\n` hoặc chữ không chắc vừa một dòng (1 em/ký tự theo cỡ chữ thật); đệm khoá `rộng|lớp CSS|chữ`, giữ 4000 mục; nút đo nằm trong `#master-grid` mang `data-code` và lớp thật của ô; đo lại sau `finishEditor`, `submit` (dán/xoá/định dạng), `undo/redo`, `updateRows` (lưu về, người khác sửa), xung đột, đổi rộng/ẩn hiện cột có cờ, phông tải xong (`document.fonts` `loadingdone`); `invalidate(false)`, `loadBlock`, `paste` dùng `geometry.resize` thay `reset`; `rememberHeight` so với chiều cao tự tính nên 28 px kéo tay được nhớ; loader nhận `h>=28`; Home về chiều cao tự tính; `aria-valuemax` lấy từ trần; ô nhập textarea của cột có cờ cao theo chữ đang gõ (`positionEditor` + sự kiện `input`); mốc `performance.measure('mg-auto-height')` cho bài đo |
| `app/static/js/master-row-geometry.js` | trần chiều cao một dòng ở một chỗ: `static MAX=2000` |
| `app/templates/crm/master_grid.html` | chân lưới thêm "Ô văn bản dài: Enter xuống dòng, Ctrl+Enter xong" |
| `app/crm/waybill_forms.py` | `note` dùng `Textarea(rows=3)`; `clean_note` gom CRLF về `\n` |
| `app/core/excel.py`, `app/forms_builder/services/export_service.py` | `write_table(..., wrap_columns=)` bật `Alignment(wrap_text, vertical=top)` và rộng 60 cho cột văn bản dài, cả chế độ thường và ghi liền (`WriteOnlyCell`); `build_workbook` truyền chỉ số cột LONG_TEXT |
| `docs/04` AC-11.44, AC-21.1; `docs/05:803`; `docs/07:136` | viết lại tiêu chí; trần 400 → 2000; kịch bản hai dòng trỏ thêm AC-11.44. Không thêm AC mới, docs/06 giữ 240 |
| `app/crm/tests/test_master_browser_server.py` | ghi chú dài chỉ ở hai dòng cuối MASTER-01298/01299 để 1298 dòng đầu giữ 28 px cho các script Chrome |
| `scripts/kiem-thu-master-row-height.cjs`, `kiem-thu-master-ui.cjs` | sửa kỳ vọng theo trần 2000 và dòng tự giãn — **sửa theo suy luận, chưa chạy** (xem Chưa kiểm) |

Bài kiểm: `crm/tests/test_ghi_chu_tu_gian_dong.py` (9 bài máy chủ), `core/tests/test_excel.py`
(+2), `tests/e2e/test_ghi_chu_tu_gian_dong.py` (8 bài trình duyệt gồm bài đo hiệu năng và hai ảnh).

### Cách đo chiều cao

Đo **theo lô** đúng lúc khối 100 dòng vừa về (và theo đúng những dòng vừa đổi khi sửa/lưu/poll):
dựng cả lô ô ẩn mang lớp `.mg-cell.mg-wrap` + lớp thật của ô + `data-code`, đặt **trong**
`#master-grid` để mọi luật CSS theo bảng áp y như ô sẽ vẽ, rồi đọc `offsetHeight` một lượt —
trình duyệt tính bố cục **một lần cho cả lô**.

Bỏ qua không đo: ghi chú rỗng, và ghi chú **không có `\n`** mà dù mỗi ký tự rộng trọn 1 em (cỡ
chữ theo `dd-co-*`, mặc định 13 px) vẫn nằm trong bề rộng chữ của ô. Mọi trường hợp khác đo
thật. Kết quả đệm theo `(rộng cột, lớp CSS, chữ)` — sửa chữ là khoá đổi, không bao giờ dùng số
đo cũ; ghi chú trùng nhau đo một lần.

**Thứ tự ưu tiên:** chiều cao người dùng tự kéo — kể cả kéo về 28 px — thắng chiều cao tự tính;
Home trả về chiều cao tự tính.

---

## Đã đo được gì

Chạy trong container `web` (Chromium cài qua `playwright install`), Playwright headless, khung
1366×800, tài khoản `staff_vd`, cột Ghi chú 400 px, `line-height` thật 18,85 px:

| Trường hợp | Ghi chú | Cao ô | Cao chữ | Số dòng | Kết luận |
|---|---|---|---|---|---|
| Ngắn một dòng | 26 ký tự | **28** | 27 | 1 | giữ nguyên như cũ |
| Ngắn có `\n` | `"Dòng 1\nDòng 2"` (13 ký tự) | **47** | 46 | **2** | ngắt dòng hiện đúng — trước lượt 2 là 28 px dồn một dòng |
| Dài một đoạn | 427 ký tự | **160** | 159 | 8 | không cắt chữ |
| Sửa ngay trong ô | gõ hai dòng, Enter + Ctrl+Enter | 28 → **47** | 46 | 2 | dòng giãn **không tải lại**; ô nhập cao **51 px** lúc đang gõ; DB nhận đúng `\n`; tải lại vẫn 47 |
| Kéo tay về 28 | ghi chú 427 ký tự | 160 → 28 → tải lại **28** → Home **160** | | | 28 px được nhớ trong `localStorage`; Home về tự tính |
| Quá trần | 12.600 ký tự | **2000** | 3777 | 200 | dừng ở trần, bấm ô mở hộp đọc |

Điều kiện bài kiểm khẳng định ở mọi ca: `cao_chu <= cao_o + 1` (không cắt một chữ nào) và
`so_dong` đúng.

### Hiệu năng (theo skill `web-perf`)

1.000 dòng, dòng nào cũng có ghi chú 400 ký tự **khác nhau** (không trùng khoá đệm), cuộn từ đầu
tới cuối bảng (211 bước, bảng cao 141.110 px, tổng 1.002 dòng):

| Số | Giá trị |
|---|---|
| Số lượt đo (mỗi khối 100 dòng một lượt, cộng lượt đo lại khi phông về) | 12 |
| Một lượt đo cả khối — p50 / p95 / max | **15,4 / 20,8 / 21,6 ms** |
| Long task ≥ 50 ms trong cả lần cuộn | **0** |

Ngưỡng đỏ của bài là p95 ≤ 100 ms; kết quả nằm quanh một khung hình 60 Hz (16,7 ms) và chạy
một lần mỗi khối tải về, không chạy theo từng khung cuộn.

## Lệnh đã chạy

```
docker compose -f deploy/docker-compose.yml run --rm -e RUN_MIGRATIONS=0 web pytest crm/tests/test_ghi_chu_tu_gian_dong.py core/tests/test_excel.py tests/test_truy_vet.py -p no:cacheprovider
docker compose -f deploy/docker-compose.yml exec -T -e RUN_MIGRATIONS=0 -e DJANGO_ALLOW_ASYNC_UNSAFE=true web pytest tests/e2e/test_ghi_chu_tu_gian_dong.py -s -p no:cacheprovider
docker compose -f deploy/docker-compose.yml exec -T -e RUN_MIGRATIONS=0 -e DJANGO_ALLOW_ASYNC_UNSAFE=true web pytest crm/tests/test_luoi_dong_trong_va_ghim_e2e.py tests/e2e/test_hanh_trinh_nhan_vien.py tests/e2e/test_dien_thoai.py --junitxml=/tmp/kq-hoi-quy.xml
docker compose -f deploy/docker-compose.yml exec -T -e RUN_MIGRATIONS=0 web pytest -m "not cham" -p no:cacheprovider --junitxml=/tmp/kq-day-du.xml
```

Cú pháp hai tệp JS kiểm bằng `new Function(src)` trong Chromium của container (không có Node
trên máy). **Bài học:** `pytest.ini` đã có `-q`, truyền thêm `-q` thành `-qq` là pytest bỏ dòng
tổng kết — đó là lý do lượt 1 "không lấy được con số tổng"; giờ lấy tổng qua `--junitxml`.

## Kết quả

| Bộ | Kết quả |
|---|---|
| `crm/tests/test_ghi_chu_tu_gian_dong.py` (9 bài máy chủ) | đạt |
| `core/tests/test_excel.py` (18 bài, 2 mới) | đạt |
| `tests/test_truy_vet.py` | đạt với docs/04 đã viết lại |
| `tests/e2e/test_ghi_chu_tu_gian_dong.py` (8 bài trình duyệt) | đạt, số đo ở trên |
| Ba tệp e2e hồi quy của lưới (8 bài) | `test_hanh_trinh_nhan_vien`, `test_dien_thoai` đạt; **3 bài đỏ đều trong `test_luoi_dong_trong_va_ghim_e2e.py`** — tệp CI đang loại có chủ ý (`ci.yml:164-173`), biên bản 18.09 đã ghi đỏ trên nền sạch. Đã `git stash` toàn bộ thay đổi rồi chạy lại đúng 3 bài trên mã gốc: **đỏ y hệt** (hai bài chờ "bấm ô là mở ô nhập" — trái ADR-033, bấm chỉ chọn ô; một bài chờ cột thứ tư không ghim — ADR-036 đã thêm cột Trùng). Không phải hồi quy của thay đổi này |
| Bộ đầy đủ `-m "not cham"` | **2536 đạt, 2 đỏ sẵn (`test_dong_bo_skill`, xem dưới), 9 bỏ qua, 39 bỏ chọn — 299,5 s** |

### Kiểm bằng cách phá — đỏ trước, xanh sau

Mọi bài mới viết trước khi sửa mã và đã đỏ đúng lý do:

```
máy chủ   KeyError: 'auto_height'                           ← chưa có cờ
          assert '<textarea name="note"' in '<!doctype…'    ← Lên đơn còn ô một dòng
          TypeError: write_table() got an unexpected keyword argument 'wrap_columns'
          AssertionError: assert (None is True)             ← ô Excel chưa Wrap Text
trình duyệt  assert 28 > 28   {'cao_o': 28, 'chu': 'Dòng 1\nDòng 2', ...}   ← ngắt dòng bị dồn
             ô nhập vẫn 28 px khi đã gõ hai dòng
             assert None == 28  where {} = _chieu_cao_da_nho(...)             ← 28 px không được nhớ
```

Sau khi sửa, cùng các bài đó xanh với số đo ở bảng trên.

### Hai bài đỏ sẵn, không phải do thay đổi này

`tests/test_dong_bo_skill.py` — hai bài đỏ `FileNotFoundError` vì `deploy/docker-compose.yml`
không gắn `.agents/` vào container. Đã kiểm ở lượt 1 bằng `git stash`: vẫn đỏ y hệt. Trên CI
(checkout cả kho) hai bài này xanh.

---

## Ảnh đối chiếu

`storage/e2e/` (không vào git), chụp sau lượt 2:

```
ghi-chu-tu-gian-dong-1440-sang.png   ghi-chu-tu-gian-dong-390-sang.png
ghi-chu-tu-gian-dong-1440-toi.png    ghi-chu-tu-gian-dong-390-toi.png
```

Dòng 1 ghi chú `"Dòng 1\nDòng 2"` hiện đúng hai dòng; dòng 2 ghi chú 427 ký tự hiện trọn 8 dòng
chữ; các dòng khác vẫn 28 px.

---

## Đợt thử phá 24.09 — đóng vai người dùng thật

Chủ dự án yêu cầu *"kiểm như một người dùng thật các trường hợp dễ xảy ra lỗi, vỡ view, vỡ
grid"*. Dựng `app/tests/e2e/test_pha_luoi_ghi_chu.py`: chín bài, mỗi bài làm một việc dễ làm
hỏng lưới rồi **soát hình học** — dòng có hở hay chồng lên nhau không, mọi ô có cao đúng bằng
dòng không (kể cả ô ghim), còn ô `…` không, chữ có bị cắt không, có lỗi JavaScript không.

**Kết quả cuối: 9/9 đạt, không lượt soát nào thấy vỡ lưới.** Chạy trên máy chủ dự án
(Chromium trong container `web`), 58 giây.

| Bài | Số đo được |
|---|---|
| Nội dung độc (9 kiểu) | một từ 3.000 ký tự không dấu cách → **1.498 px, bẻ được**; emoji ×60 → 160 px; chữ Nhật ×20 → 197 px; `\r\n` → 66 px đúng 3 dòng; chuỗi giống thẻ HTML **hiện thành chữ, không thành thẻ** |
| 40 dòng cao liền nhau (khung 34.390 px) | Ctrl+End 1,2 s; Ctrl+Home 1,2 s; **25 lần phím mũi tên, 0 lần ô chọn ra ngoài khung nhìn** |
| 12 lượt cuộn giật cục (150 dòng, khung 58.910 px) | **0/12 lượt có vấn đề** |
| Kéo đổi rộng cột | 400 px → dòng 160; kéo còn **72 px → dòng 1.177**; nới **640 px → dòng 103**. Đo lại đúng cả hai chiều |
| Ẩn / hiện cột | ẩn → mọi dòng 28 px; hiện lại → 160 px |
| Xoá + hoàn tác | 160 → 28 → 160, không tải lại trang |
| Dán từ Excel | ô có ngắt dòng bên trong → 66 px, giữ nguyên ngắt dòng |
| Điện thoại 390 px (cột 400 px) | **không tràn ngang trang** |
| Phóng 125 % rồi thu về | 160 → 160, không lệch |

### Một lỗi thật, đã sửa

Ghi chú **chỉ gồm khoảng trắng và ký tự xuống dòng** làm dòng cao 197 px mà không hiện chữ
nào: điều kiện đo chỉ kiểm chuỗi rỗng, không kiểm chuỗi toàn khoảng trắng. Qua đường người
dùng thì không gặp (`parse_value` cắt hai đầu, nhập Excel strip, ô Lên đơn là `CharField`
cũng strip), nhưng dữ liệu ghi thẳng vào cơ sở dữ liệu thì còn — **đúng loại dữ liệu đang
nằm trên VPS** — và lúc đang gõ trong ô thì giá trị chưa lưu vẫn được đo. Sửa một dòng ở
`vuaMotDong`: không có chữ nào đọc được thì coi như vừa một dòng.

### Ba lần đỏ còn lại là lỗi bài kiểm, không phải lỗi sản phẩm

Bài kéo cột đỏ bốn lượt liền. Tôi đoán sai ba lần (tay kéo ngoài khung nhìn → nút lọc che →
nút chữ cái che) trước khi hỏi thẳng `elementsFromPoint` và thấy chồng phần tử thật:

```
BUTTON.mg-column-name                      ← trên cùng
DIV.mg-heading mg-pinned mg-pinned-edge
DIV.mg-pin-region                          ← z-index 10
SPAN.mg-resize                             ← tay kéo, z-index 9, bị đè
```

**Vùng cột ghim đè lên tay kéo.** Bài kiểm cuộn sao cho mép phải cột Ghi chú nằm ở x = 477,
trong khi dải ghim chiếm x = 0…526. Đây là hành vi đúng của lưới — cột ghim vốn nổi trên nội
dung cuộn qua dưới nó. Sửa bài kiểm: đẩy cột ra ngoài dải ghim rồi mới kéo, đúng như người
dùng phải làm.

**Bài học ghi lại:** chẩn đoán phải tự khai báo. Ba lượt đầu chỉ báo "kéo không ăn" nên chỉ
còn cách đoán; lượt in ra cả chồng phần tử thì trả lời ngay. Bộ bài giữ lại phần chẩn đoán đó.

## Quy mô lớn — trần khung vẽ và hình học 300.000 dòng (24.09)

Trước AC-11.44 mọi dòng đều 28 px nên tổng chiều cao khung vẽ luôn nhỏ. Dòng cao lên thì tổng
cao lên theo, mà **trình duyệt có trần cứng cho chiều cao một phần tử**: vượt trần là nó cắt
cụt, dòng nằm dưới điểm cắt không cuộn tới được và **không báo lỗi gì**. Bài
`tests/e2e/test_hieu_nang_ghi_chu_lon.py` đo đúng chỗ đó.

**Trần đo được trên Chromium trong container: 30.677.722 px** (dò nhị phân, không lấy theo số
tài liệu — trần thật thấp hơn con số 33,5 triệu thường thấy).

| Mốc | Cần | So với trần |
|---|---|---|
| 300k dòng × 28 px (như trước AC-11.44) | 8.400.000 px | 27,4 % — vừa |
| **100k dòng × 160 px** (đơn một năm, **mọi** dòng ghi chú dài) | 16.000.000 px | **52,2 % — vừa** |
| 300k dòng × 160 px (mức kiểm dự phòng) | 48.000.000 px | **156,5 % — VƯỢT** |
| 300k dòng × 2000 px (mọi dòng chạm trần) | 600.000.000 px | 1.955,8 % — vượt xa |

Hai giới hạn rút ra: ở **300.000 dòng**, chiều cao trung bình không được quá **102 px**; nếu
**mọi** dòng đều cao 160 px thì lưới chỉ chứa được **191.735 dòng**.

**Mức vận hành thật an toàn.** Công ty khoảng 100.000 đơn một năm; kể cả khi mọi đơn đều có ghi
chú dài thì mới dùng 52 % trần. Chỉ mức kiểm dự phòng 300.000 mới chạm trần, và chỉ khi phần
lớn dòng có ghi chú dài — thực tế phần lớn ghi chú ngắn hoặc trống.

### Hiệu năng hình học ở 300.000 dòng

Cây Fenwick với 300.000 dòng, 150.000 dòng cao 160 px (tổng 28.200.000 px, 300.000 nút):

| Việc | Đo được | Ngưỡng |
|---|---|---|
| Đặt 150.000 chiều cao | 50 ms | — |
| Đọc tổng chiều cao | 0 ms | — |
| Tra vị trí một dòng | **0,003 ms** | < 0,5 ms (chạy mỗi khung hình khi cuộn) |
| **Dựng lại cả cây** | **95 ms** | **< 1000 ms** |

Dòng cuối là quan trọng nhất: **mỗi lượt tải lại mềm đều dựng lại cả cây**, mà lưới hỏi mốc 8
giây một lần. 95 ms ở mức dự phòng 300.000 dòng nghĩa là việc đổi `geometry.reset` thành
`geometry.resize` (commit đầu) **an toàn ở quy mô lớn** — trước đó chưa có gì bảo đảm điều này.

### Bài 300.000 dòng thật

`test_300k_dong_ghi_chu_dai_khong_vo_view` dựng 300.000 dòng bằng SQL nhân bản rồi kiểm trình
duyệt có cắt cụt khung vẽ không và cuộn tới cuối có ra dòng cuối không. **Tự bỏ qua** khi thiếu
`KN_GHI_CHU_300K=1` vì nặng — tính tới 24.09 **chưa chạy lần nào**.

## Chưa kiểm — nợ ghi rõ

| Việc | Vì sao |
|---|---|
| **Chủ dự án nhìn tận mắt trên máy** | mở `http://127.0.0.1:8021/bang-tinh/van_don/`, cuộn tới cột Ghi chú, gõ thử một ghi chú hai dòng. Tính tới hết 24.09 vẫn chưa xem bằng mắt — mọi bằng chứng đều là máy đo |
| **Lưới vượt trần khung vẽ khi số dòng × chiều cao trung bình > 30,6 triệu px** | Chưa có gì chặn. Ở mức thật 100.000 đơn một năm thì còn xa trần (52 %), nhưng lưới không hề biết khi nào mình vượt: nó cứ đặt chiều cao, trình duyệt cắt lặng lẽ. Cần quyết định riêng — kẹp tổng chiều cao, hay giới hạn số dòng tự giãn, hay cảnh báo |
| **Dòng trống cuối bảng gõ ghi chú dài** | Bảng Vận đơn không mở dòng trống để nhập (đơn sinh ở Lên đơn, ADR-036) nên đường `absorbCreated` chưa thể gặp cột tự giãn. Bài kiểm giữ lại nhưng **tự bỏ qua** |
| **Tay kéo đổi rộng cột nằm dưới vùng cột ghim thì không bấm được** | phát hiện trong đợt thử phá. Đúng thiết kế (cột ghim nổi trên nội dung cuộn), nhưng dải ghim rộng 526 px nên trên màn hình hẹp nó chiếm gần nửa bề ngang — cột bị kéo vào dưới đó là mất luôn khả năng đổi rộng cho tới khi cuộn ra. Không sửa trong đợt này: đụng CSS đầu cột dùng chung cho mọi bảng, ngoài phạm vi đã duyệt |
| **Script Chrome `.cjs` chưa chạy** | máy không có Node. `kiem-thu-master-row-height.cjs`, `kiem-thu-master-ui.cjs` và fixture `test_master_browser_server.py` sửa theo suy luận; `kiem-thu-master-capacity.cjs`, `kiem-thu-master-row-capacity.cjs`, `kiem-thu-master-nine-capacity.cjs` **chắc chắn đỏ** vì fixture của chúng cho mọi dòng ghi chú dài và script nhảy tới dòng bằng `r*28` — cần làm lại trên máy có Node |
| **Ký tự rộng hơn 1 em** | `vuaMotDong` coi 1 em/ký tự là trần; emoji hay chữ toàn chiều rộng có thể vượt → dòng giữ 28 px kèm `…` như trước, không mất dữ liệu |
| **Trên VPS** | chưa phát hành; thứ tự cột trên VPS khác máy cá nhân, hình dáng thật có thể khác |
| **Trần 2000 px áp cho mọi bảng** | trần nằm trong `master-row-geometry.js` dùng chung; bảng khác không tự giãn nhưng kéo tay tới 2000 px được |

## Điểm lùi

Bỏ cờ `auto_height` trong `waybill_service.grid_column` là lưới về hành vi cũ (mọi dòng 28 px,
không đo) mà không cần gỡ JS; các thay đổi về `geometry.resize`, nhớ 28 px và ô nhập cao theo
chữ vẫn vô hại khi không có cột mang cờ.
