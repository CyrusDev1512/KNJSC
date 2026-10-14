---
version: 1
slug: "app-templates-crm-kn-oms-html"
primary_target: "app/templates/crm/kn_oms.html"
related_targets: ["app/static/css/oms.css","app/static/js/oms.js","app/templates/crm/base_crm.html","app/static/css/solarpunk.css"]
---

# KN OMS — bản demo dữ liệu giả trong KN CRM, Operate

ADR-051 và mục bổ sung 13.10.2026. Chỉ Admin, mở tab mới từ thanh bên KN CRM. Người dùng: chủ dự án trình bày cho
Vận đơn, CSKH, Kế toán, Marketing; ngồi bàn văn phòng, ánh sáng ban ngày, màn 1366–1920 px; điện thoại phụ.

## Direction contract

THESIS: KN OMS là một phòng nữa trong cùng toà nhà Solarpunk Office của KN CRM: cùng ảnh nền kiến trúc–cây xanh, cùng
khung kính sage, cùng mặt đọc kem. Khác ở chỗ đây là bàn điều hành đơn: dày số, phẳng, vào việc ngay.

OWN-WORLD: kế thừa, không phát minh. Nạp đúng bốn tệp CSS của `crm/base_crm.html` (tokens, main, crm-frame, solarpunk)
rồi mới tới `oms.css`. Màu, chữ (Be Vietnam Pro; IBM Plex Mono cho mã, số, nhãn nhóm), bo góc (khung 20–28 px, điều
khiển 8–12 px, ô bảng 0), kính mờ chỉ ở thanh bên và thanh trên, nút, ô nhập, chip, bảng `table.bang` đều là của KN
CRM. `oms.css` chỉ thêm: màu thông tin (xanh dương) và năm màu nền tảng bán hàng, dải chỉ số phẳng, nút lọc dạng chip,
ngăn kéo bên phải, dòng thời gian, biểu đồ đường lãi.

STORY: mở màn là thấy dải chỉ số một hàng (bấm để lọc), dải lọc có nhãn, bảng. Bấm một dòng là ngăn kéo bên phải mở chi
tiết; ghi nhận tiền, lập phiếu kho, thêm kênh cũng làm trong ngăn kéo đó, không hộp thoại. Huỷ hay Esc ở biểu mẫu mở từ
ngăn kéo đơn thì quay về ngăn kéo đơn.

FIRST VIEWPORT: thanh bên kính (KN OMS · Bản demo, ba nhóm, sáu màn có số đếm), thanh trên (KN OMS / tên màn, nhãn
"Dữ liệu giả", Đặt lại demo, Nền), mặt đọc kem bo 26 px: tiêu đề 28 px một câu dưới, dải chỉ số, bảng.

FORM: Operate, Restrained: một màu nhấn (xanh rêu của KN CRM) cho hành động chính và mục đang chọn; vàng nhạt
`--sp-selected` cho chip lọc, ô chỉ số, dòng đang mở; màu trạng thái chỉ cho trạng thái.

FINISH: rà bằng tay theo `craft-floor` (không engine). Bằng chứng ở biên bản `docs/kiem-chung-kn-oms-thiet-ke-lai-20261013.md`:
ảnh trước/sau 6 màn × sáng/tối × 1366/390, tương phản chữ, quét tràn ngang 320–1440 px, trạng thái trống/lỗi/focus.

## Critique bản đầu (13.10, trước khi sửa)

| # | Thấy | Sửa |
|---|---|---|
| C1 | Không ảnh nền, không kính, không thanh trên như KN CRM | Khung và CSS của KN CRM |
| C2 | 22 ô KPI số to (mẫu hero-metric) | Dải chỉ số phẳng ngăn vạch mảnh, số 21 px |
| C3 | Đoạn giới thiệu 182–290 ký tự | Một câu dưới 90 ký tự; giải thích dài vào "Cách tính" |
| C4 | Viền trái 3–4 px ở thẻ rủi ro, khoản tiền về | Nền nhạt theo mức, viền 1 px, chip trạng thái |
| C5 | Ba hộp thoại | Ba biểu mẫu trong ngăn kéo bên phải |
| C6 | Dải "DEMO" chiếm một hàng | Nhãn "Dữ liệu giả" trên thanh trên |

## Còn để ý

- Nhãn nhóm thanh bên và đường dẫn dùng `--ink-3` trên kính sáng: 4,48:1 theo phép đo bỏ qua ảnh nền, bằng đúng trang
  chủ KN CRM. Là token chung của KN CRM, chưa sửa trong việc này.
- `table.bang` của KN CRM có tiêu đề cột mono chữ hoa (`main.css` thắng `solarpunk.css` về độ cụ thể). KN OMS giữ y
  như KN CRM cho nhất quán.
