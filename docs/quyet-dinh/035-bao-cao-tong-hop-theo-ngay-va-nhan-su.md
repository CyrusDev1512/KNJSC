# ADR-035 — Báo cáo tổng hợp thêm cột Nhân sự và Leader, 100 dòng mỗi trang, bảng gọn

| Mục | Nội dung |
|---|---|
| Trạng thái | Đã triển khai local, kiểm chứng ở `docs/kiem-chung-gop-y-sau-adr033-20260918.md` |
| Ngày | 18.09.2026 |
| Người quyết định | Chủ dự án (góp ý trên domain thật sau phát hành ADR-033; hai câu hỏi trả lời trong phiên Claude Code) |
| Bổ sung cho | ADR-022 (báo cáo hoạt động ERP), ADR-032; không đổi thang phạm vi Staff / Leader / Manager / Admin |

## Bối cảnh

Màn hình `/bao-cao/tong-hop/` với nguồn đã cấu hình (`ReportSource`, ADR-022) nhóm cách
xem "Tổng hợp" theo **ngày**: một dòng gộp mọi người trong ngày, không biết ai làm.
Danh tính chỉ có ở cách xem "Theo nhân viên" và không có khái niệm **leader của dòng**.
Phân trang mặc định 25 dòng, ô 14px đệm 12×14 px nên một màn hình thấy rất ít dòng.
Chủ dự án yêu cầu: thêm Nhân sự và Leader ngay sau Ngày, hiện theo bộ lọc; Staff chỉ
thấy của mình, Leader team mình, Manager cả bộ phận; nhiều dòng hơn; cột hẹp, bảng gọn.

## Quyết định

1. **Cách xem Tổng hợp giữ nguyên mỗi ngày một dòng** (chủ dự án 18.09: chỉ thêm hai cột,
   không đổi cấu trúc — bản nháp đầu nhóm theo ngày × nhân sự đã bị hoàn lại). Hai cột
   **Nhân sự** và **Leader** ngay sau Ngày gộp tên (`StringAgg` không trùng, thứ tự chữ) của
   những người có dòng trong ngày, theo đúng bộ lọc và phạm vi quyền: `person_name` =
   "username — họ tên" người lập dòng (Vận đơn: người được phân công, đúng ADR-022; chưa phân
   công → "Chưa phân công"), `leader_name` = họ tên (hoặc username) của `Team.leader` team
   người đó. Lọc một nhân sự thì cột chỉ còn người đó và leader; Staff chỉ có mình. Cùng một
   truy vấn GROUP BY (`with_day_people`), không N+1; ngân sách ≤ 10 truy vấn giữ nguyên.
2. **Cách xem Theo nhân viên thêm cột Leader** cạnh Team (`with_person_team`). Cách xem
   Sản phẩm, Thị trường, Phòng ban giữ nguyên vì dòng không thuộc về một người.
3. **Phạm vi quyền không viết lại**: vẫn `apply_scope` ở `activity_service.records`
   (Staff: `created_by`; Leader: team phụ trách + của mình; Manager: bộ phận; Admin: tất
   cả) và `filter_people` chặn lọc ra ngoài phạm vi (403). Nhân sự/Leader chỉ là cột hiển
   thị của dòng đã trong phạm vi; Staff thấy tên leader của chính mình, không thấy dòng ai khác.
4. **100 nhóm mỗi trang** cho báo cáo hoạt động (`pagination_context(default_size=100)`),
   vẫn nằm trong `PAGE_SIZES` 25/50/100 và vẫn phân trang (quy tắc bắt buộc 1 giữ). Dòng
   "Tổng trong bộ lọc" vẫn tính trên toàn bộ kết quả.
5. **Bảng gọn theo token `sheet-body` 13px** của DESIGN.md: chữ 13px, ô đệm 5×8 px, khung
   bảng cao `calc(100vh - 230px)`, panel lọc 224px, cột danh tính tối đa 220px có cắt
   chữ. Không đổi màu, không thêm thư viện; chế độ Toàn màn hình giữ nguyên.
   > **Bổ sung 19.09.2026 — đảo quyết định 1.** Chủ dự án gửi ảnh mẫu (một hệ thống khác)
   > và yêu cầu màn hình giống ảnh: trong một ngày **mỗi marketer là một hàng riêng**. Từ
   > 19.09 cách xem Tổng hợp nhóm theo **ngày × nhân sự** (`aggregations.summarize(extra_groups=…)`,
   > `derived_key=("nhom","person_name")`): ngày lặp lại ở từng hàng, mỗi hàng chỉ mang số của
   > người đó; Doanh thu suy ra (ADR-038) khoá theo cặp (ngày, marketer); dòng Tổng không đổi;
   > Excel cùng cấu trúc; Vận đơn nhóm theo ngày × người phụ trách. Bỏ `StringAgg` gộp tên và
   > bản trung gian `98d5c1e` (xuống dòng trong ô). Luật cắt chữ 220px của quyết định 5 đã bỏ
   > ở AC-22.13. Xem AC-22.10, AC-22.14 và [biên bản](../kiem-chung-o-danh-tinh-20260919.md).
6. **Excel** xuất đúng các cột đang hiện (Ngày, Nhân sự, Leader, chỉ tiêu; Theo nhân viên:
   Team, người, Leader, chỉ tiêu). Dòng tổng để trống ô danh tính.

## Hệ quả

- ~~Số dòng của Tổng hợp không đổi so với trước (mỗi ngày một dòng); chỉ thêm hai cột chữ.~~
  Từ 19.09 số hàng = số cặp (ngày, người) có dữ liệu — xem Bổ sung ở quyết định 5.
- Bài kiểm cũ so dòng tổng Excel theo vị trí cột phải trừ hai ô danh tính
  (`test_sale_scope_and_dashboard`, `test_delivery_filters_match_status_and_export`,
  `test_people_filters`) — đã cập nhật.
- Chưa làm: chọn cột hiển thị, gộp lại theo ngày không kèm người (nếu cần thì là một
  "Cách xem" mới, không phải đổi cách xem này).

## Kiểm chứng

`reports/tests/test_activity.py::test_day_view_shows_person_and_leader_in_scope` (AC-22.10,
bốn cấp bậc, lọc nhân sự, 403 ngoài phạm vi, Excel) và `test_day_view_pages_by_hundred`
(AC-22.11); `test_query_budget`, `test_delivery_query_budget` còn đạt. Chromium local 8020
chụp `sale.staff`, `sale.leader`, `sale.manager` ở 1440 và 390 px.
