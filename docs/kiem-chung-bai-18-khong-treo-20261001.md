# Kiểm chứng — Bài đo hiệu năng 1000 dòng ghi chú không còn treo được (TL-71) — 01.10.2026

Nhánh `claude/sua-bai-18-khong-treo` tách từ `main` (`9a2722c`). Chỉ sửa bài kiểm
`app/tests/e2e/test_ghi_chu_tu_gian_dong.py`, không đụng mã ứng dụng, không thêm thư viện, không migration.
Chạy trên máy ảo Claude Code: PostgreSQL 16 cục bộ dựng như dịch vụ CI, Chromium không màn hình (Playwright
1.56), Python 3.12 như CI.

## Vì sao

Chẩn đoán ở PR #74 (biên bản `kiem-chung-e2e-treo-20261001.md`) khoanh hai lần CI treo 20 phút (lượt #107 ngày
29.09, #120 ngày 01.10) và một lần treo tại máy vào bài 18 `test_do_hieu_nang_1000_dong_ghi_chu_400`. Lúc treo,
luồng chính đứng chờ Playwright, máy chủ thử rảnh, không ai chờ khoá Postgres. Bài 18 có hai lời gọi
`page.evaluate` không giới hạn thời gian (Playwright không cho đặt timeout cho `evaluate`):

- Vòng cuộn hết 1000 dòng. Mỗi bước chờ hai khung vẽ bằng `requestAnimationFrame`, rồi chờ ô Mã đơn có dòng
  bằng rAF, hẹn 8 giây. Vòng có tối đa 600 bước. Nếu trang ngừng vẽ thì rAF không gọi lại và lời hứa treo mãi; nếu
  dữ liệu không về thì mỗi bước mất đủ 8 giây, cả vòng tới 80 phút.
- `_mo_luoi` chờ `document.fonts.ready` không có hẹn.

## Sửa

| Chỗ | Thay đổi |
|---|---|
| `CUON_HET_BANG`, `HAN_CUON_MS` (mới, đầu tệp) | Vòng cuộn tách thành hằng số, nhận hạn tổng 60 giây. Chờ khung vẽ đua với hẹn 1 giây; chờ dữ liệu bằng `setTimeout` 16 ms, hẹn 8 giây cho mỗi bước và không quá hạn tổng. Toàn bộ vòng còn đua với hẹn hạn tổng + 5 giây. Dừng thì trả trạng thái trang: số bước, đã tới cuối bảng chưa, vị trí cuộn, chiều cao bảng, số ô Mã đơn và số ô chưa có dòng, yêu cầu mạng (đang chờ, xong, lỗi; đếm bằng cách bọc `window.fetch` trong lúc cuộn rồi trả lại), rAF còn chạy không, thông báo của lưới |
| Bài 18 | Gọi `trang.evaluate(CUON_HET_BANG, HAN_CUON_MS)`, rồi kiểm đã cuộn tới cuối bảng: không tới thì đỏ, thông điệp kèm trạng thái trang. Phần đo p95 của AC-11.44 giữ nguyên |
| `_mo_luoi` | `document.fonts.ready` đua với hẹn 10 giây |

## Kiểm

**Ép tình huống bằng một bài tạm** (`tests/e2e/test_tam_bai18_treo.py`, đã xoá, không commit). Bài tạm nạp
1000 dòng như bài 18, mở lưới, rồi chạy `CUON_HET_BANG` với hạn 10 giây:

| Tình huống | Cách ép | Kết quả |
|---|---|---|
| Dữ liệu không về | `page.route("**/du-lieu/**")` không bao giờ trả lời | Dừng sau 10,0 giây: 69 bước, chưa tới cuối bảng, 2 ô Mã đơn chưa có dòng, 3 yêu cầu dữ liệu đang chờ |
| Trang ngừng vẽ | Thay `window.requestAnimationFrame` bằng hàm rỗng | Dừng sau 11,0 giây: `raf_chay: false` |
| Bình thường | — | Tới cuối bảng sau 8,0 giây: 240 bước, 10 yêu cầu, rAF chạy |

Với vòng cũ, hai tình huống đầu đều thành treo. Trang ngừng vẽ thì vòng cũ chờ rAF mãi. Dữ liệu không về thì mỗi
bước chờ đủ 8 giây; khoảng 240 bước tới cuối bảng là hơn 30 phút, vượt hạn 20 phút của job CI.

**pytest như CI:**

| Lệnh | Kết quả |
|---|---|
| `pytest tests/e2e -m trinh_duyet -vv -rs --durations=10 -o faulthandler_timeout=120` | 37 đạt, 2 bỏ qua, 4 phút 49. 9 đỏ đều ở `test_pha_luoi_ghi_chu.py` do proxy máy ảo chặn phông Google (đã biết, CI không gặp). Bài 18 đạt, thân bài 11,3 giây như trước. Mọi bài khác của tệp, đều qua `_mo_luoi` mới, đạt |
| `pytest -m trinh_duyet --ignore=tests/e2e -vv -rs --durations=10 -o faulthandler_timeout=120` | 8 đạt, 9 bỏ qua như CI, 1 phút 41. Cảnh báo cũ "database đang có phiên khác" lúc xoá CSDL cuối phiên (TL-67) |
| `pytest tests/test_truy_vet.py` | 36 đạt |

## Chưa làm / để lại

- Chưa biết vì sao trên CI dữ liệu không về hay trang ngừng vẽ. Từ nay nếu gặp lại, bài 18 đỏ sau khoảng 1 phút
  với trạng thái trang trong thông điệp; khi đó mới sửa gốc, có thể ở lưới.
- `_o_ghi_chu` và vài bài khác trong tệp vẫn chờ rAF không hẹn. Chưa thấy treo ở đó; sửa nếu treo lan sang.
