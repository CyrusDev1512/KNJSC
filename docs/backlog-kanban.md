# Bảng việc — To do / In progress / Finished / Far Plan

## 16.09.2026 — Tối ưu cuộn và cờ: đã phát hành phần đã kiểm

Code/E2E/hồi quy và tải ngắn đã kiểm; đã dừng kiểm bền theo yêu cầu sau 14,71 phút đo; chưa đủ 60 phút. Bảy cờ tắt.
READ/SYNC chưa đạt thao tác dưới tải, RENDER chưa chứng minh lợi ích mới.
Đã push/phát hành VPS 0907cdd; giữ nợ 300k của task khác. [Chi tiết](kiem-chung-co-toi-uu-20260916.md).

VPS image `knjsc-app:0907cdd-grid`; Chrome 1440/390 và hash JS đạt, năm service
cùng image, giới hạn tài nguyên/CSS giữ nguyên. Không coi smoke là kiểm tải VPS.

## 16.09.2026 — Mốc thực tế: 300.000 dòng + tối đa 10 người

Chủ dự án xác nhận khoảng 100.000 đơn/năm, kiểm dự phòng 300.000 dòng và tối đa 10 người dùng file Vận đơn. Đã đo trên hai DB giả độc lập: 10 người, đọc toàn bảng p95 local/VPS 1,37/5,04 giây; lọc tháng 8.496 dòng 0,83/3,09 giây. Lưu tương ứng toàn bảng 0,49/2,34 giây, theo tháng 0,31/1,57 giây; không lỗi HTTP hoặc sai giá trị cuối ở 8 lượt chính. SQL phiên bản vẫn quét 300k dòng dù lọc tháng; CPU DB VPS gần hết hai core. Browser VPS nhảy dòng 150k vượt chờ 10 giây; chọn ô vẫn khoảng 36 ms. **Chưa đạt mục tiêu mượt**; cần duyệt tác vụ xử lý server/cache rồi đo lại đúng mốc này, không lấy khảo sát 20 người trước làm yêu cầu. Môi trường đo đã dừng, production giữ nguyên. [Bằng chứng và giới hạn](kiem-chung-300k-10-nguoi-20260916.md).


## 16.09.2026 — Đo đồng thời Vận đơn DB trên VPS và local

Đã đo 1/5/10/20 người trên 10.000 dòng giả, 26 cột, môi trường riêng. VPS 20 người: p95 đọc 965 ms, lưu 848 ms, poll 804 ms; vượt mục tiêu lưu/poll. Local tương ứng 288/272/199 ms. Các lượt hợp lệ không lỗi HTTP, kiểm lại giá trị cuối khớp. Browser 9 Locust + 1 Chrome: local cuộn p95 351 ms, VPS 245 ms; chưa chứng minh tối ưu local giữ lợi ích khi có ghi nền. Ghi nhận 409 đọc gây bỏ cache: cần chốt tác vụ riêng để xử lý, chưa sửa ứng dụng hoặc phát hành. [Phương pháp, số đo và giới hạn](kiem-chung-tai-dong-thoi-20260916.md).

## 16.09.2026 — Sửa riêng bố cục Tổng quan ERP

Đã sửa nhãn–giá trị cùng hàng, bỏ kéo cao thẻ theo Marketing, kiểm responsive và suite báo cáo; push/phát hành VPS commit `da6e2c0`. Không đưa thay đổi báo cáo/lưới chưa phát hành vào bản này. [Kiểm chứng và giới hạn](kiem-chung-tong-quan-20260916.md).

## 16/09/2026 — Chọn ô/nhập trong lúc lưu: đã tối ưu và đo local

Đã tách cập nhật vùng chọn/mở/hủy editor khỏi dựng lại nội dung lưới.
40 lượt/10.000 dòng mô phỏng, trình duyệt Codex 1280×720, giữ request lưu:
p95 chọn/mở/nhập ~33–34 ms; baseline cũng ~34 ms nhưng một lượt chọn 58,1 ms.
Bản cuối max 34,2 ms; DOM tạo mới giảm 51.891 → 466. Đây là phép đo tới hai
rAF của fixture, không phải số đo API/VPS hoặc bảo đảm trên mọi máy.
Giữ nháp mới khi phản hồi cũ về; lỗi lưu và Undo/Redo đã kiểm; 48 test server
và nhóm Node liên quan đạt. Local, chưa push/VPS. Không đánh dấu toàn bộ bảy
hạng mục tối ưu hoàn thành hoặc coi kiểm này là kiểm bộ nhớ dài hạn.
[Chi tiết](kiem-chung-nhap-khi-luu-20260916.md).

## 16.09.2026 — Gom nhảy xa

**Finished local:** chỉ tải vùng đích sau 80 ms yên cuộn; tải trước phục hồi
khi cuộn ổn định. Chrome 1440/390, sở hữu request và E2E DB thật đạt.
48→1 request trong chuỗi nhảy mô phỏng; không gọi là tăng tốc lần nhảy đơn.
Chưa push/VPS. [Chi tiết](kiem-chung-cuon-luoi-20260916.md).

## 16.09.2026 — Cuộn cache và tải trước theo hướng

**Finished local trong phép đo kiểm soát:** giữ DOM khi chỉ cuộn, đón hai
khối, giữ trần cache và xử lý lỗi/quyền. Functional 110 đạt; Chrome 1440/390
và tương thích cờ renderer đạt. Chưa push/VPS; còn đo mạng/backend thật khi
phát hành. [Bằng chứng](kiem-chung-cuon-luoi-20260916.md).

## 16.09.2026 — Đổi tên Vận đơn thành crmThuận (local)

Theo yêu cầu chủ dự án, đổi tên hiển thị bảng `van_don_moi` thành `crmThuận`.
Đã cập nhật tên mặc định và chuyển tên cũ khi khởi tạo lại; không ghi đè tên
riêng khác. Local chỉ cập nhật name/updated_at và audit; kiểm trước/sau giữ
ID, code, cờ nhận đơn và số dòng. Chrome mục Bảng nhận đơn hiển thị crmThuận
là lựa chọn hiện tại. 11 test khởi tạo/bảng nhận đơn đạt. Chưa commit/push/VPS.


## 16.09.2026 — Ngày hệ thống và chỉnh sửa báo cáo (local)

Đã triển khai theo ADR-032: nhập ngày DD/MM/YYYY; báo cáo mới khóa ngày Việt
Nam và người nộp; Leader sửa trong team, Manager trong bộ phận, Admin toàn
hệ thống, có lịch sử và chống ghi đè bản cũ. Staff không sửa báo cáo đã nộp,
kể cả qua lưới. Marketing có Doanh thu/Hóa đơn và năm công thức đã chốt;
loại tiền lấy theo thị trường. Tổng tiền khác/thiếu đơn vị để trống có giải thích.
256 test nhóm cuối đạt; đã kiểm trình duyệt luồng sửa, ngày, lưới và mobile.
Lỗi nhập lại mã đơn trùng tái hiện cả ở HEAD 5ce53f3, không đổi nghiệp vụ nhập.
Phần báo cáo này chưa commit/push/VPS; lỗi thêm sản phẩm 404 trên domain thật
vẫn mở, không coi kết quả local là đã sửa 404.
[Chi tiết và giới hạn](kiem-chung-bao-cao-erp-20260916.md),
[quyết định thay thế](quyet-dinh/032-ngay-he-thong-va-sua-bao-cao.md).

## 16.09.2026 — Đã phát hành tiền/PTTT, bỏ Đơn vị phụ và sửa cột ghim

Đã push mã `5ce53f3`, VPS chạy `knjsc-app:5ce53f3-market-20260916` trên
ERP/CRM và các worker. Hồi quy đúng bản phát hành: 535 đạt, 1 lỗi nền,
17 skip; E2E database test và Chrome VPS 1440/390 đạt. Giữ hotfix sidebar.
Đã xử lý 502 sau thay container bằng nạp lại proxy; không ghi thử dữ liệu VPS.
Mục này thay thế trạng thái chưa push/VPS của các mục cùng phạm vi bên dưới.
[Chi tiết phát hành và giới hạn](phat-hanh-tien-te-20260916.md).

## 16.09.2026 — Sửa màu cột ghim

**Finished VPS:** CSS vùng giấy thống nhất ở sáng/tối; Chrome thật 1440/390 đạt.
[Kiểm chứng](kiem-chung-mau-cot-ghim-20260916.md). Chưa commit/push.

## 16.09.2026 — Bỏ trường Đơn vị phụ

**Finished local:** bỏ trên Lên đơn/Xem đơn gốc; không xóa dữ liệu cũ.
36 test và Chrome 1440/390 đạt. Chưa commit/push/VPS.

## 16.09.2026 — Tiền theo quốc gia và PTTT

**Finished local:** cố định tiền theo quốc gia, xác nhận giữ số tiền khi đổi,
chọn Zelle/PayPal dùng chung form/lưới. 15 test mới và Chrome 1440/390 đạt;
hồi quy có ba lỗi nền được đối chứng riêng. Chưa commit/push/VPS.
[Kiểm chứng](kiem-chung-tien-theo-quoc-gia-20260916.md).

## 16.09.2026 — Báo cáo ERP

**Local đã có bản xem thử; toàn tác vụ In progress:** lọc nhân sự/team,
kèm nút ẩn/hiện bộ lọc và toàn màn hình bảng (đã kiểm desktop/mobile),
kẻ bảng, báo cáo ngày Vận đơn và 36 mẫu lịch sử đã kiểm. Còn tái hiện/sửa
404 thêm sản phẩm trên domain thật. Chưa commit/push/VPS.
[Bằng chứng](kiem-chung-bao-cao-erp-20260916.md).

## 15.09.2026 — Vận đơn DB bị vô hiệu trong chọn bảng

**Finished VPS cf51ad2:** command/service chuẩn bị bảng đã có placeholder; kiểm
local 87 test + Chrome hai kích thước đạt. [Chi tiết](kiem-chung-chuan-bi-bang-nhan-don-20260915.md).

## 15.09.2026 — Bàn giao tối ưu lưới cho PC nhà

**To do:** đã chọn phương án 1; chưa sửa lưới hoặc tạo “Vận đơn optimize”.
[Daily tasks](daily-tasks.md) là điểm đọc tiếp: 7 hạng mục, phạm vi local,
kiểm chứng, lỗi nhập 3.333 dòng và ranh giới đối soát đang tắt.
Các mục “chưa push” của mẫu Excel bên dưới là nhật ký tại thời điểm kiểm;
code mẫu Excel đã có trên GitHub qua `c41d8f0` và `f971683`.

## 15.09.2026 — Phiên đăng nhập chung

**Finished VPS — cdc1a45; 16 ca Chrome test và 4 ca domain thật đạt.** Không có thay đổi
quyền nghiệp vụ. Hồi quy có một lỗi CSS nền riêng; chưa sửa ở đợt này.
[Kiểm chứng](kiem-chung-dang-nhap-chung-20260915.md).

## 15.09.2026 — Báo cáo Marketing/Sale mẫu trên domain thật

**Finished VPS:** hai bảng mỗi bảng 50 dòng, phân đúng 5 team/10 nhân sự mẫu;
DB và giao diện đã kiểm. Không tạo DailyReport đã nộp, tài khoản mẫu khóa đăng
nhập; không restart dịch vụ. [Chi tiết](kiem-chung-bao-cao-mau-vps-20260915.md).

## 15.09.2026 — Sửa lỗi mẫu nhập đã được duyệt

**Finished local, chờ đối chiếu file của chủ dự án:** preview đúng cột, mẫu bỏ
cột chỉ xuất và căn ô, báo lỗi sớm, chặn nhập trùng. 30 test đạt; UI ba mẫu,
tệp lỗi/trùng và 10.000 dòng đạt. Thay thế trạng thái “Còn việc” ngay bên dưới.
Chưa kiểm Microsoft Excel/chưa VPS. [Chi tiết](kiem-chung-mau-nhap-van-don-20260915.md).

## 15.09.2026 — Kiểm người dùng thật cho mẫu nhập

**Còn việc:** tải/nhập hợp lệ và 10.000 dòng đạt, nhưng preview lệch cột,
mẫu có cột không nhận nhập, báo lỗi muộn và nhập lại tạo trùng. Phát hiện
được ghi nhận, chưa thay đổi nghiệp vụ. [Chi tiết](kiem-chung-mau-nhap-van-don-20260915.md).

## 15.09.2026 — Tải mẫu Excel vận đơn

**Finished local:** nút Tải mẫu Excel đúng từng bảng, bỏ nhãn Sửa; kiểm nhập lại và quyền đạt. Chưa push/VPS. [Kiểm chứng](kiem-chung-mau-nhap-van-don-20260915.md).

## 15.09.2026 — Chọn bảng nhận đơn tại CRM (local)

Admin chọn đích nhận đơn mới; bảng/đơn cũ giữ nguyên. Đã áp migration 0012 local, chưa đổi đích mặc định, chưa commit/push/VPS. Sau sửa cuối 67 test liên quan đạt; Chrome 1440/390, hai ca 30 Sale đồng thời và migration xuôi/ngược đạt. [Kết quả và giới hạn](kiem-chung-bang-nhan-don-20260915.md) · [ADR-029](quyet-dinh/029-bang-nhan-don-crm.md).


## 15.09.2026 — Sửa sidebar CRM thu gọn

**Finished:** căn giữa logo và icon nhóm; Chrome local đạt, VPS đã nhận CSS
hotfix qua HTTPS. [Bằng chứng và giới hạn](kiem-chung-crm-sidebar-20260915.md).

## 15.09.2026 — Mở rộng giao diện KN ERP trong tab

**Finished local, chờ chủ dự án xem:** hai nút Nền/Mở rộng đã đổi thành icon có
nhãn hỗ trợ. ERP tràn sát viewport và không còn ảnh nền khi bật; trình duyệt vẫn
giữ thanh địa chỉ và các tab vì nút không gọi Fullscreen API. Esc, desktop 1440px
và mobile 390px đều đạt. Lựa chọn mở rộng được giữ qua tải lại, chuyển trang và
đồng bộ giữa các tab ERP cùng origin. Đã triển khai VPS; image hiện hành
`knjsc-app:8dead1b` chứa commit chức năng `2ea5ab2`. Không merge `main`.

## 14.09.2026 — Toàn màn hình ERP, sắp lại Vận đơn và tạm khóa Chứng từ

**Đã phát hành nhánh riêng lên VPS, chờ nghiệm thu người dùng:** chức năng, dữ liệu metadata và
Chrome 1440/390 sáng/tối đã áp dụng; database local và VPS được sao lưu trước. Hai bảng giữ
nguyên số dòng/ID/quyền; Chứng từ mặc định tắt nhưng kiểm thử cờ bật vẫn giữ luồng
cũ. VPS đang chạy image `knjsc-app:97741e4`; HTTPS/check/log sau triển khai đạt.
Không merge `main`. [Kiểm chứng](kiem-chung-erp-vandon-bill-20260914.md).
Full suite cuối: **2.332 passed, 15 failed nền, 31 skipped, 2 xfailed**.

## 14.09.2026 — Hợp nhất CRM-UPDATE và Solar UI

**Finished trong phạm vi nhánh:** nghiệp vụ/quyền/lưới master của CRM-UPDATE đã
được hợp nhất với trình bày Solar. Chrome chức năng và bố cục đạt; full suite
2.329 passed, còn 15 lỗi nền đã đối chiếu. Chờ chủ dự án nghiệm thu trước mọi
quyết định với `main` hoặc nhánh cũ. [Bằng chứng](kiem-chung-crm-update-solar-ui-20260914.md).

## 14.09.2026 — Tích hợp phần local vào CRM-UPDATE

Đã khôi phục ERP từ stash, ghép sửa Thống kê và chế độ xem Vận đơn; Solarpunk giữ riêng. Functional toàn bộ: 2327 đạt, 17 lỗi đều tái hiện trên nền 9bac840, 31 skip/2 xfail. Chrome định danh, bốn cấp quyền, Thống kê và đổi chế độ xem đạt tại 1440/390. Không kích hoạt runtime chính hoặc chạy lại kiểm tải toàn CRM. [Bằng chứng và giới hạn](kiem-chung-tich-hop-local-20260914.md).


**Finished trong phạm vi kiểm chứng — 14.09, CRM-UPDATE:** lưới chung,
xóa/khôi phục bảng, tương phản và truy vấn phạm vi đã kiểm functional/Chrome;
ma trận tải và bài bền 30 phút đạt. Bốn lỗi kiểm thử nền/11 skip giữ riêng.
Chờ chủ dự án duyệt diff/kích hoạt; worktree riêng, local vẫn nhánh fix,
chưa commit/push. Tạo bảng trắng/duplicate tiếp tục hoãn.
[Bằng chứng](kiem-chung-crm-update-20260912.md).

**12.09, 17:20 — Chủ dự án yêu cầu test trước:** đã chuyển checkout chính sang `CRM-UPDATE`, cập nhật local 8020/8021 và worker cùng code; không seed/migrate, chưa commit/push. Marketing/Sale đã xác nhận dùng lưới mới. Functional 1.130 passed, 4 lỗi nền, 11 skipped; Chrome chức năng đạt. Kiểm tải tạm dừng: bản cuối mới đủ 100k/10, chưa nghiệm thu toàn chiến dịch. [Kết quả và phần còn lại](kiem-chung-crm-update-20260912.md).

**12.09 — CRM-UPDATE đang kiểm local:** lưới chung Marketing/Sale/Vận đơn cũ,
xóa mềm/khôi phục bảng; giữ Vận đơn mới, ERP và dữ liệu. Đang chạy ma trận tải,
chưa nghiệm thu toàn chiến dịch; tạo bảng trắng/duplicate cấu trúc hoãn.
[Biên bản](kiem-chung-crm-update-20260912.md) · [ADR-027](quyet-dinh/027-crm-update-luoi-chung-va-vong-doi-bang.md).


> Cập nhật 12.09.2026: theo yêu cầu chủ dự án, đã chuyển nhánh codex/chung-tu-thanh-toan về checkout chính C:/KNJSC/KNJSC và kích hoạt app local 8021. Đã áp dụng orders 0007, org 0004; không chạy seed. Các mô tả chưa kích hoạt bên dưới ghi trạng thái bàn giao trước bước này. Chưa commit/push; bản sao checkout cũ giữ nguyên nội dung, ở detached HEAD.

**Chờ kiểm tra trên môi trường sử dụng — Chứng từ thanh toán (12.09):** có mã,
functional/migration và Chrome với fixture 10k; giữ bốn lỗi nền/skip riêng.
Chưa kích hoạt trên app 8021, chưa commit/push. H7 chỉ chốt phần chứng từ,
không đóng quyền nhập tiền và đối soát. [Biên bản](kiem-chung-chung-tu-thanh-toan-20260912.md).
**14.09 — Solarpunk Office (nhánh UI riêng):** đã triển khai khung xanh, báo cáo hai vùng, chế độ tập trung cả hai lưới; preview ERP 18020 / CRM 18021 và dữ liệu riêng. Đã kiểm Chrome hai lưới, lưu/hoàn tác/lỗi mạng/CAS và bố cục sáng/tối; full suite 2154 pass, 14 fail (1 bài nhận diện khung chạy lại đạt, còn 13 lỗi nền); chưa merge/commit/push, không đổi 8020/8021. [Hồ sơ](kiem-chung-solarpunk-20260914.md), [ADR-028](quyet-dinh/028-solarpunk-office.md).


**14.09 — Vận đơn DB:** đã tạo bảng động riêng `van_don_db`, 26 cột lấy từ định nghĩa hiện có, 0 dòng; sắp thứ tự theo file chủ dự án, không có Đơn vị phụ. Chưa nối Lên đơn; không đổi code ứng dụng hoặc bảng nguồn. Đã kiểm cấu hình lưu, tiêu đề HTML và thứ tự xuất. [Chi tiết](cau-hinh-van-don-db-20260914.md).

**12.09.2026, 17:28 — Đã bật nhánh fix để chủ dự án test nút:** checkout chính `C:/KNJSC/KNJSC` và local 8020/8021 hiện chạy `fix/trung-ma-don-dong-thoi`. Bản CRM-UPDATE được giữ nguyên tại `C:/KNJSC/worktrees/CRM-UPDATE`, chưa ghép. Đã sao lưu database, áp dụng riêng `forms_builder.0011_delivery_view_mode`; không seed hoặc đổi chế độ xem thay người dùng. 10 test chế độ xem đạt trên PostgreSQL test riêng; hai URLconf sạch. Đọc READ ONLY trên local xác nhận trang chế độ xem, liên kết từ lưới và Cột & cấp quyền đều 200; mặc định hiện là theo phân công. Chưa commit/push.

**12.09.2026 — Chế độ xem Vận đơn mới, đã kiểm chứng local:** Admin/Manager
Vận đơn đổi theo phân công/toàn bảng; quyền sửa vẫn theo phân công. Trang
lưới tự reload khi nhận phiên bản mới. 10 test mới, focused cuối 46 passed;
Chrome 1440/390 đạt, migration xuôi/ngược đạt. Hồi quy rộng 500 passed,
4 failed, 10 skipped; 2 lỗi mount fixture chạy lại đạt, còn 2 lỗi markup
nền. Không chạy kiểm tải lớn, không tuyên bố tăng tốc. Đã có diff trên nhánh
fix trong worktree riêng, chưa tích hợp checkout chính/chưa commit/push.
[Bằng chứng](kiem-chung-che-do-xem-van-don-20260912.md), [ADR-026](quyet-dinh/026-che-do-xem-van-don.md).

**Finished local — Trùng mã đơn khi nhiều Sale lưu (11.09):** nhánh
`fix/trung-ma-don-dong-thoi`/`a81decd`; service khóa PG theo DDMM, chờ tối đa
5s và giữ giao dịch đơn–Vận đơn. Functional/Chrome 1440/390 đạt; hỗn hợp
30 Sale + 10 Vận đơn đủ thời lượng, 361 đơn đúng; đợt dồn 30/30, không
timeout. Kiểm tương thích READ/SYNC/RECEIPTS/RENDER đạt. Chưa commit/push/merge;
các việc truy vấn/render lưới và lỗi nền vẫn giữ trạng thái riêng.
[Biên bản](kiem-chung-trung-ma-don-20260911.md).

**In progress / chờ nghiệm thu — CRM-Optimization (11.09):** mã sau cờ tắt đã có;
đã đo đủ trước/sau 100k/300k × 10/20 và bài bền cấu hình 30 phút. Render/cold
Thống kê, backlog xuất và tăng RSS app còn cần cải thiện/điều tra. Không suy nguyên nhân toàn bộ
16 lỗi lịch sử; chưa kết luận năng lực VPS. [Kiểm chứng](kiem-chung-crm-optimization-20260911.md).

**11.09.2026 — Ba lựa chọn Lên đơn bắt buộc chọn rõ:** Quốc gia/Loại tiền/PTTT mặc định rỗng, chọn hợp lệ mới lưu; đơn kế tiếp trở lại rỗng. 105 test đạt, Chrome 1440/390 đạt, trần 10 truy vấn giữ đạt; không migration/dependency, chưa commit/push. [Bằng chứng bổ sung](kiem-chung-len-don-gio-admin-20260911.md).


**11.09 — Cột ghim Vận đơn mới:** triển khai và hồi quy tự động đã xong;
100k/300k lệch 0 px, cache 10, không tăng request. Còn nghiệm thu thủ công
zoom trình duyệt thật/trackpad; chi phí render tăng nhẹ được ghi rõ tại
[biên bản](kiem-chung-ghim-cot-20260911.md). Không gộp với lỗi API trước đó.

**11.09.2026 — Bổ sung giờ lưu và Admin tự đứng đơn (thay quyết định chọn Sale):** Ngày giờ cập nhật HH:mm trên form, thông báo lấy timestamp thực tế đã lưu; bỏ dropdown, Admin/Sale tự đứng bằng mã đăng nhập. Admin thử nghiệm chưa thuộc Sale dùng Sale/team trống, giữ hồ sơ. 117 test đạt; Chrome 1440/390 đạt; kiểm tải đọc 10/20 Admin: 4.782 request đo/0 lỗi, p95 cao nhất 76,38 ms trên fixture nhỏ. Không migration mới, chưa commit/push. [Kiểm chứng và giới hạn](kiem-chung-len-don-gio-admin-20260911.md).


**11.09.2026 — Ngày/đơn vị/mã nhân viên khi lên đơn:** đã kiểm chứng local: Ngày Việt Nam chỉ đọc; chọn hộp/cái/chiếc/túi từng sản phẩm, snapshot trên đơn/vận đơn; mã đăng nhập cho định danh nghiệp vụ và lịch sử. Migration 0006 đã kiểm xuôi/ngược DB test và áp dụng xuôi local. Hồi quy 984 đạt/2 lỗi giao diện thống kê có sẵn; lượt focused cuối 72 đạt; Chrome 1440/390 đạt; Locust đọc 10/20 đạt 4.618 request/0 lỗi. Chống lặp hoãn, không kết luận năng lực toàn CRM. [Bằng chứng và giới hạn](kiem-chung-len-don-20260911.md). Chưa commit/push.


**11.09.2026 — Điều hướng ERP/thư viện/Lên đơn CRM:** đã triển khai local theo ADR-023. Giữ Bảng dữ liệu ERP; sửa Biểu mẫu thiếu người tạo, gộp hai tab đúng quyền; chuyển nhập đơn và xem đơn gốc sang CRM. Kiểm thử, số đo và giới hạn tại [báo cáo bàn giao](kiem-chung-erp-hub-20260911.md). Chưa commit/push.

**11.09 — Lưới Vận đơn mới:** sửa Admin/nhập trong ô đã kiểm Chrome/E2E;
chạy bền snapshot 7449e73 đã đủ 30 phút; còn 16 lỗi đọc/22.460 request và
lọc Quốc gia p95 1,35s chưa đạt. Hai bài rà giao diện Thống kê
có lỗi từ trước, chưa xử lý trong tác vụ lưới. Chi tiết và giới hạn:
[kiểm chứng 11.09](kiem-chung-master-admin-20260911.md).

Bản nhìn theo cột của `backlog.md`. `backlog.md` vẫn là nơi ghi **vì sao** (quyết
định Q, lỗ hổng K, nhật ký); tệp này chỉ trả lời **đang ở cột nào**. Lỗi cụ thể
kèm mức nghiêm trọng, chỗ sai, blocker và ảnh hưởng nằm ở `test-log.md`; ở đây
chỉ tham chiếu mã `TL-xx`.

Cập nhật: 16.09.2026. Ai làm xong việc nào thì kéo dòng đó sang cột kế tiếp
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
| P1 | Cột Trùng có tác dụng: có ở Vận đơn DB, chuẩn hoá số điện thoại, đếm cả lịch sử, bấm để xem, lọc và tô màu | TL-35, TL-36 | `main` | Chờ anh/chị chốt 1 trong các ý ở backlog 16.09 |
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

- **11.09.2026 — Bàn điều hành KN CRM:** tổng hợp tối đa ba nguồn và chuyên sâu
  mọi bảng theo profile Marketing/Sale/Vận đơn/Chung; insight có bằng chứng và
  link xử lý, biểu đồ SVG, tách tiền tệ, giữ scope và tương thích thống kê cũ.
  [ADR-022](quyet-dinh/022-ban-dieu-hanh-kn-crm.md), AC-22.1–22.9. Hồi quy 159
  bài đạt; p95 20k Sale/100k Vận đơn/300k Vận đơn/tổng hợp lần lượt
  89,07/333,72/893,26/733,64ms; kiểm trình duyệt đủ ma trận trong test-log.

- **11.09.2026 — `vandonmoi`:** hoàn thiện đúng 10.000 dòng mẫu
  `MAU-20260910-*` trong Vận đơn mới bằng management command tái lập theo seed;
  giữ 500 danh tính cũ, thêm 9.500 dòng, chi tiết sản phẩm và phân công. Sửa ghi
  chú lỗi `?`, làm rõ ba cột ghim và toolbar theo phạm vi riêng của bảng mới.

- **09.09.2026 — `codex/sua-feedback`:** phân công Vận đơn mới và phạm vi theo
  tài khoản; bộ lọc nhanh/sản phẩm/thị trường/Marketing; xuất ngày/bộ lọc có
  mã nhân viên và kiểm quyền file nền. [ADR-020](quyet-dinh/020-phan-cong-loc-xuat-van-don-moi.md),
  AC-20.1 đến AC-20.7. H7 chưa làm; chưa commit/push trong tác vụ này.

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
| 7L | Vận đơn mới theo CRM Tân: hai bảng độc lập, ERP/CRM cùng luồng, chi tiết tiền từng sản phẩm, thống kê; 25 bài mới, toàn bộ hồi quy, migration hai chiều và giao diện desktop/mobile đều đạt | — | ADR-018 |
| 7L.1 | 10.000 vận đơn mẫu Canada/CAD có chi tiết, thanh toán, phân công; vùng ba cột nhận diện ghim rõ trên lưới | — | Nhánh `vandonmoi` · 11.09.2026 |
| 7M | Bàn điều hành KN CRM theo nguồn Marketing/Sale/Vận đơn/Chung; KNERP giữ báo cáo và thêm liên kết | — | ADR-022 |
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

### 10.09.2026 — Chín hạng mục lưới mới, thay quyết định lưu thủ công

Đã duyệt autosave, chọn hàng/màu xanh, hai chế độ, fs/c/bg, lịch sử và
đối chiếu conflict, Admin chọn Sale, thứ tự tạo tăng dần và số hàng từ 1.
Đã triển khai và kiểm chức năng trên database test: suite rộng 1.049 pass,
6 fixture skip được tách kiểm; 90 test tác động và E2E cuối đạt. Hiệu năng
lọc 300k còn chưa đạt; chạy bền dừng theo yêu cầu chủ dự án, để phiên sau
chạy lại đủ 30 phút. Không đổi H7/lưới cũ.
Xem [quyết định ADR-021](quyet-dinh/021-luoi-master-va-thong-ke-crm.md) và
[báo cáo chín hạng mục](kiem-chung-master-nine.md).
