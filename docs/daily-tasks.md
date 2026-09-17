# Daily tasks — KNJSC

## Bàn giao cho Claude Code CLI trên máy chủ dự án — 17.09.2026: phát hành VPS

Claude Code trên web **không tới được VPS** (mạng môi trường trả
`x-deny-reason: host_not_allowed`, cổng 22 không mở, không có `ssh`). Việc phát
hành làm từ máy có SSH vào VPS. Mở Claude Code CLI trong thư mục kho, dán:

> Đọc `docs/daily-tasks.md` mục "Bàn giao cho Claude Code CLI ... 17.09.2026" và
> làm theo. SSH tới VPS: `<điền>`. Đường dẫn kho trên VPS: `<điền>`. Cách dựng
> image: `<build tại VPS | build ở đây rồi đẩy>`.

### Bối cảnh — đã kiểm chứng, không kiểm lại

- Nhánh làm việc là `codex/crm-update-solar-ui`, **không phải** `main`. Đọc
  `CLAUDE.md` mục "Nhánh và nơi mã đang chạy" trước.
- VPS đang chạy `knjsc-app:0907cdd-grid` (16.09). Đầu nhánh gồm cả `9949062`
  (ADR-033, Codex đẩy chiều 17.09) — xác nhận HEAD bằng `git log -1`.
  **Hai migration mới**, cả hai đảo ngược được, đã thử xuôi ngược:
  `forms_builder.0013_remove_tabledef_delivery_view_all` (bỏ cột cấu hình
  ADR-026, quay lui thì cột về `false`) và `reports.0003_report_revision`.
- Đã diễn tập nâng cấp **hai lần** trên DB có dữ liệu ở trạng thái `0907cdd`
  (lần hai gồm `9949062`): 10.005 dòng trước/sau không đổi, quay lui được,
  `check --deploy` sạch, gunicorn prod khởi động được. Biên bản:
  `docs/kiem-chung-dien-tap-vps-20260917.md` — **đọc trước khi làm**.
- **ADR-033 là thay đổi nghiệp vụ nhìn thấy ngay**: nhân viên Vận đơn thấy và
  **sửa được mọi dòng** của bảng vận đơn (trước chỉ dòng được giao); nút
  "Chế độ: Xem" và trang "Chế độ xem bảng" bị bỏ; thay bằng nút **Tôi / Toàn
  bộ** trên thanh công cụ lưới. Đã kiểm trên DB nâng cấp bằng Chrome với
  `vd.staff`: thấy 10.000 dòng, "Tôi" còn 5.000, sửa dòng người khác ghi được.
  Báo nhân viên Vận đơn trước khi phát hành để họ không tưởng lỗi.
- Quy trình chuẩn ở `deploy/production/README.md`, **đã thêm** hai lệnh
  `configure_erp_reports` và `configure_delivery_daily_report` sau
  `tao_bang_van_don`. Thiếu chúng thì Báo cáo tổng hợp lặng lẽ hiện bản cũ.
  Production đặt `RUN_MIGRATIONS=0` nên entrypoint không chạy giúp — phải gọi tay.
- Khuôn phát hành các lần trước: các tệp `docs/kiem-chung-*-vps-*.md` và các
  commit "Ghi ket qua phat hanh ... tren VPS" — đọc để làm đúng khuôn tên tag
  image, backup, `nginx -t`, kiểm Chrome domain thật.

### Việc, theo thứ tự

1. Trên máy này: `git fetch`, checkout `codex/crm-update-solar-ui`, xác nhận
   HEAD chứa `9949062` (`git log --oneline | grep 9949062`). `pytest -m "not cham"` cho chắc (~2.500 đạt).
2. SSH vào VPS, **không đổi gì**, chỉ ghi nhận: `docker compose ps`, tag image
   đang chạy, dung lượng DB, `manage.py showmigrations reports`. Báo chủ dự án.
3. **Dừng lại**, tóm tắt kế hoạch, hỏi chủ dự án xác nhận **một lần** trước khi
   động vào production. Dữ liệu thật ~1,25 GB, không hoàn tác được như máy ảo.
4. Sau khi được gật: backup DB theo cách các lần trước, **kiểm phục hồi được**.
   Không có backup kiểm được thì không đi tiếp.
5. Dựng/kéo image `knjsc-app:<commit>-<nhãn>` đúng khuôn cũ.
6. Tại `deploy/production`, chạy đúng dãy trong README: `config --quiet` →
   `up -d db broker cache` → `static-owner` → `migrate --noinput` →
   `tao_bang_van_don` → `configure_erp_reports` →
   `configure_delivery_daily_report` → `collectstatic --noinput` →
   `up -d crm erp worker heavy beat proxy`. Rồi `nginx -t` và reload.
7. Kiểm sau phát hành bằng Chrome trên domain thật:
   - ERP `/bao-cao/tong-hop/` phải là bản **mới**: có nút "Toàn màn hình".
   - CRM `/bang-tinh/van_don_moi/` mở được, chân trang "N dòng khớp bộ lọc",
     console không lỗi JS.
   - Đăng nhập chung ERP/CRM còn hoạt động.
8. Ghi một mục ngày vào đầu `docs/backlog.md` và một tệp
   `docs/kiem-chung-phat-hanh-vps-<ngày>.md`: tag image, lệnh đã chạy, số đo,
   phần chưa kiểm. Commit theo khuôn "Ghi ket qua phat hanh ... tren VPS", push
   lên `codex/crm-update-solar-ui` khi chủ dự án bảo.

### Hai thứ sẽ xảy ra sau phát hành — không phải lỗi, báo để chủ dự án quyết

- **Báo cáo Marketing: mọi cột tiền hiện `—` kèm dải vàng**, vì dòng cũ không
  có `loai_tien`; `currency_safe_result()` cố ý không cộng lẫn tiền tệ. Đếm số
  dòng `bao_cao_mkt` trên VPS thiếu `loai_tien` và báo. Điền `loai_tien` cho
  dòng cũ thì số hiện lại — đã kiểm. **Không tự điền**, hỏi loại tiền nào.
- **Hai bảng rỗng** `bao_cao_sale` và `bao_cao_van_don_ngay` sẽ xuất hiện nếu
  VPS chưa từng chạy `configure_*`. Chỉ báo, không xoá.

### Nếu hỏng

Quay lui bằng image `knjsc-app:0907cdd-grid`, rồi `migrate forms_builder 0012`
và `migrate reports 0002` (thứ tự này). Cột `delivery_view_all` về `false` cho
mọi bảng — chấp nhận được vì bản cũ mặc định cũng `false`.
**Không restore DB chỉ để lùi mã** (README production nói rõ).

### Quy tắc

- Không bật cờ `CRM_OPT_*`, không đổi đích nhận đơn, không đụng dữ liệu nghiệp vụ.
- Chỉ push khi được bảo. Không dán mật khẩu/khoá vào đâu; dùng `ssh` có sẵn.
- Báo kết quả thật: lệnh nào đỏ thì dán nguyên log, không tóm tắt cho đẹp.

## 16.09.2026 — Dừng phép đo hỗn hợp, đưa toàn bộ thay đổi lên GitHub

Theo yêu cầu chủ dự án, dừng kiểm tải 10 người Vận đơn + 5 Sale lên đơn. Mới chuẩn bị tài khoản/sản phẩm/bảng nhận đơn trong DB thử; chưa chạy kịch bản hỗn hợp, chưa có kết quả để kết luận. App/DB benchmark local và VPS đã dừng; giữ dữ liệu giả riêng để tái lập. Phạm vi bàn giao Git gồm toàn bộ thay đổi code, migration, kiểm thử và tài liệu hiện có; dữ liệu local/manifest phiên thử trong storage vẫn được gitignore.

## 16.09.2026 — Mốc thực tế: 300.000 dòng + tối đa 10 người

Chủ dự án xác nhận khoảng 100.000 đơn/năm, kiểm dự phòng 300.000 dòng và tối đa 10 người dùng file Vận đơn. Đã đo trên hai DB giả độc lập: 10 người, đọc toàn bảng p95 local/VPS 1,37/5,04 giây; lọc tháng 8.496 dòng 0,83/3,09 giây. Lưu tương ứng toàn bảng 0,49/2,34 giây, theo tháng 0,31/1,57 giây; không lỗi HTTP hoặc sai giá trị cuối ở 8 lượt chính. SQL phiên bản vẫn quét 300k dòng dù lọc tháng; CPU DB VPS gần hết hai core. Browser VPS nhảy dòng 150k vượt chờ 10 giây; chọn ô vẫn khoảng 36 ms. **Chưa đạt mục tiêu mượt**; cần duyệt tác vụ xử lý server/cache rồi đo lại đúng mốc này, không lấy khảo sát 20 người trước làm yêu cầu. Môi trường đo đã dừng, production giữ nguyên. [Bằng chứng và giới hạn](kiem-chung-300k-10-nguoi-20260916.md).


## 16.09.2026 — Đo đồng thời Vận đơn DB trên VPS và local

Đã đo 1/5/10/20 người trên 10.000 dòng giả, 26 cột, môi trường riêng. VPS 20 người: p95 đọc 965 ms, lưu 848 ms, poll 804 ms; vượt mục tiêu lưu/poll. Local tương ứng 288/272/199 ms. Các lượt hợp lệ không lỗi HTTP, kiểm lại giá trị cuối khớp. Browser 9 Locust + 1 Chrome: local cuộn p95 351 ms, VPS 245 ms; chưa chứng minh tối ưu local giữ lợi ích khi có ghi nền. Ghi nhận 409 đọc gây bỏ cache: cần chốt tác vụ riêng để xử lý, chưa sửa ứng dụng hoặc phát hành. [Phương pháp, số đo và giới hạn](kiem-chung-tai-dong-thoi-20260916.md).

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

Mở lại file này mỗi ngày để xem việc còn nợ. Thêm nhật ký theo ngày thực tế;
không tự chuyển việc chưa kiểm chứng sang hoàn thành. Đây là sổ công việc,
không phải lịch tự chạy hoặc nhắc việc tự động.

## Bàn giao cho Codex ở PC nhà — 15/09/2026

- Repository: `CyrusDev1512/KNJSC`, nhánh `codex/crm-update-solar-ui`.
  Pull nhánh này trước khi đọc; kiểm Git và giữ thay đổi riêng của máy đó.
- Ý định đã chọn: **phương án 1**, tải dữ liệu theo vùng nhìn/tải trước có
  giới hạn, kết hợp cải thiện vẽ lưới. Không tải toàn bảng vào RAM theo
  phương án 2/3, không thay framework hoặc viết lại bằng Canvas.
- Bước tiếp theo khi chủ dự án yêu cầu tiếp tục: đo baseline local, trình
  bày kế hoạch cụ thể theo AGENTS.md; sau khi duyệt thì tự hoàn tất sửa,
  kiểm thử và tài liệu. Việc chọn hướng không phải xác nhận mọi chi tiết
  nghiệp vụ hoặc quyền. Lệnh hiện tại chỉ yêu cầu ghi bàn giao và push
  những gì đang có, chưa yêu cầu bắt đầu viết tối ưu.
- Đợt đầu ưu tiên điều phối request, bỏ yêu cầu đọc lỗi thời, cache theo
  vùng thực dùng và giảm dựng/cập nhật DOM. Đo server/sync để quyết định
  phần cần làm tiếp trong 7 hạng mục; không tự bật tất cả cờ toàn hệ thống.
- Bàn giao mong muốn của đợt tối ưu: bản chạy local, so sánh trước/sau cùng
  dữ liệu, hồi quy thao tác ô và push GitHub khi được yêu cầu. Các khoảng
  ms bên dưới là kỳ vọng, không phải tốc độ đã đo hay điều kiện được phép
  bỏ kiểm thử. Không dùng ước lượng thời gian trong chat làm giới hạn công việc.
- Bảng thử “Vận đơn optimize” trên VPS là ý định trước đó, **chưa tạo**;
  tách khỏi bước tối ưu local, không tự deploy hoặc chạm bảng gốc. VPS có
  task từ máy khác đang làm; phải kiểm lại trạng thái trước thao tác.
- Lỗi thiếu 3.333 dòng là tác vụ nhập dữ liệu riêng. Chủ dự án nhắc đối
  soát đã tắt; không tự thêm lựa chọn, bật chức năng hay nhập bù.
- File Excel/video/ảnh trong Downloads, Videos, Temp và chứng cứ trong
  `storage/` ở PC hiện tại không đi theo Git. Nếu PC nhà không có, đọc
  các phát hiện đã ghi rồi chuẩn bị dữ liệu thử tương đương để đo; không
  tuyên bố đã xem lại video hoặc chạy lại test khi chưa có chứng cứ.
- Script báo cáo mẫu được lưu để truy vết việc đã làm; không tự chạy lại
  trên VPS. Không có mật khẩu/private key trong gói bàn giao này.

## 15/09/2026 — Tối ưu lưới CRM, phương án 1

**Trạng thái:** đã chọn hướng; đã khảo sát code/cấu hình VPS, chưa triển khai
các thay đổi dưới đây. Chưa tạo bảng thử “Vận đơn optimize”.

**Mục tiêu:** tải theo vùng nhìn, tải trước vùng lân cận có giới hạn và giảm
chi phí vẽ lưới. Giữ nghiệp vụ, quyền, nháp trong RAM, Undo, CAS và autosave.
Bảng thử dự kiến sao chép cấu trúc/dữ liệu Vận đơn DB; phải đối chiếu số dòng
thực tế và tách khỏi bảng gốc, không làm ảnh hưởng instance VPS khác.

| Trạng thái | Phần | Hiện trạng qua code | Hướng xử lý |
|---|---|---|---|
| Chưa làm | Điều phối tải | Yêu cầu dữ liệu khi vùng cần vẽ còn thiếu; chưa có ưu tiên theo hướng cuộn | Ưu tiên vùng đang nhìn, tải trước phía đang kéo; giới hạn yêu cầu đồng thời |
| Chưa làm | Yêu cầu lỗi thời | Đổi bộ lọc có hủy yêu cầu; cuộn sang vùng khác chưa có cơ chế tương đương | Hủy hoặc hạ ưu tiên yêu cầu đọc không còn cần, tránh vùng mới phải chờ |
| Chưa làm | Cache | Giới hạn 10 khối nhưng việc đọc ô không cập nhật mức độ sử dụng của khối | Giữ vùng đang nhìn và vùng vừa dùng; tránh phản hồi cũ về muộn đẩy vùng cần dùng ra khỏi cache |
| Chưa làm | Vẽ và chọn ô | Có tái sử dụng DOM; nhánh bỏ qua hàng không đổi đang tắt. Cuộn vẫn cập nhật cả trạng thái phụ | Kiểm chứng nhánh tối ưu có sẵn; giảm cập nhật ô, tiêu đề và thanh trạng thái khi không thay đổi |
| Chưa làm | Server và dữ liệu truyền | Đường đọc thông thường tính tổng, phiên bản và dựng metadata mỗi khối; trả nhiều thuộc tính cho từng ô | Đo SQL, thời gian dựng JSON, dung lượng truyền; giảm phần lặp lại có chi phí đáng kể |
| Chưa làm | Đồng bộ nền | Kiểm tra mỗi 8 giây; đường hiện tại có thể xóa cache khi bảng thay đổi | Cập nhật hoặc vô hiệu hóa đúng vùng bị ảnh hưởng, giữ kiểm quyền và nháp |
| Chưa làm | Bộ nhớ, lưu nền | Cache, nháp và Undo cùng tồn tại | Kiểm khi cuộn lâu và đang chờ lưu; tải trước không được gây mất nháp hoặc làm lưu chậm |

### Bằng chứng và giới hạn

- Đọc cấu hình Django trong container CRM VPS ngày 15/09/2026:
  `CRM_OPT_READ`, `CRM_OPT_RENDER`, `CRM_OPT_SYNC` đều False.
- Code có tái sử dụng node qua `syncRow`/`updateBody`; không kết luận mọi lần
  cuộn đều thay toàn bộ DOM. Nhánh bỏ qua dựng lại hàng chưa đổi có cờ riêng.
- `van_don_db` không thuộc profile vận đơn mà đường đọc/sync tối ưu hiện tại
  yêu cầu. Chỉ bật cờ không đủ; không đổi workflow nghiệp vụ để lách điều kiện.
- Nguồn: `app/static/js/master-grid.js`,
  `app/crm/services/master_grid_service.py`, `app/crm/services/optimization.py`,
  `app/crm/master_views.py`; đối chiếu ADR-024 và ADR-027 trước triển khai.
- Video người dùng cho thấy khoảng trống/đợi thông tin cỡ 1–1,5 giây ở một
  đoạn kéo nhanh. Đây là quan sát video, chưa phải trace mạng/CPU hay p95.

### Dự đoán trước/sau — giả định kỹ thuật, chưa phải kết quả đo

Giả định: cùng PC, trình duyệt, mạng và bộ lọc; khoảng 6.667–10.000 dòng,
server không quá tải. Khoảng dự đoán dưới đây dùng để lập kế hoạch, sẽ thay
bằng số đo trên cùng dữ liệu. Không áp cho mọi thiết bị hoặc mọi lần thao tác.

| Tình huống | Trước, bằng chứng hiện có | Sau, khoảng kỳ vọng có điều kiện |
|---|---|---|
| Cuộn vào vùng đã có cache | Chưa đo riêng | Khoảng 16–50 ms từ thao tác đến khung có dữ liệu; không chờ request đọc |
| Cuộn đều cùng hướng | Có đoạn chờ cỡ 1–1,5 giây trong video kéo nhanh, chưa có baseline cuộn đều | Nếu tải trước kịp: khoảng 16–100 ms chờ hiển thị; giảm mạnh khoảng trống |
| Nhảy xa tới vùng chưa tải | Video có khoảng chờ; chưa tách chính xác loại thao tác | Khoảng 200–600 ms nếu request đọc hoàn tất trong 150–500 ms và xử lý/vẽ thêm 20–100 ms; mạng/server chậm vẫn có thể vượt 1 giây |
| Chọn ô, gõ khi đang lưu | Chưa đo trên dữ liệu đối chiếu | Mục tiêu phản hồi nhìn thấy dưới 50 ms; không đồng nghĩa đã lưu server trong 50 ms |
| RAM, CPU, dung lượng truyền | Chưa đo baseline | Cache có giới hạn; tải trước có thể tăng RAM và byte tải so với không tải trước. Chưa dự đoán phần trăm giảm |

Không hứa toàn hệ thống nhanh hơn một hệ số cố định; phương án 1 không đảm
bảo nhảy ngẫu nhiên tới vùng chưa tải sẽ tức thì. Giữ lịch gửi autosave
500 ms/tối đa 2 giây theo quyết định đã chốt.

### Kiểm chứng cần thực hiện

- [ ] Chụp baseline: cùng bộ dữ liệu/quyền, cuộn xuống/lên, kéo thanh cuộn
  nhảy xa, vùng có cache và chưa có cache, cuộn ngang, hàng cao/cột ghim.
- [ ] Đo riêng thời gian server, truyền/đọc JSON, cập nhật DOM và khung hiện dữ liệu.
- [ ] Thử phản hồi về sai thứ tự, đổi lọc khi đang tải, lỗi mạng, đồng bộ từ
  người khác và thay đổi quyền; không hiển thị dữ liệu cũ dưới số dòng mới.
- [ ] Kiểm sửa ô tiếng Việt, dán vùng, Undo/Redo, lỗi lưu/xung đột và cuộn
  trong khi chờ lưu; chỉ ghi vào dữ liệu thử được phép.
- [ ] So sánh trước/sau và kiểm bộ nhớ sau nhiều lần cuộn. Cập nhật kết quả,
  chưa kiểm chứng và diff; không tự bật toàn hệ thống hoặc deploy.

## 15/09/2026 — Vì sao nhập 10.000 dòng chỉ có 6.667

**Trạng thái:** đã xác định nguyên nhân bằng đọc dữ liệu; chưa sửa cấu hình,
chưa nhập bù, không chỉnh bảng gốc.

- File `C:/Users/PC/Downloads/mau-import-van-don-db-10000.xlsx`, sheet
  `Du lieu Van don DB`, tiêu đề hàng 3, có đúng 10.000 hàng dữ liệu.
- Cột 26 “Đối soát kế toán”: 6.667 ô trống, 3.333 ô có `Đã về TK`.
- VPS: BackgroundJob #3, target `van_don_db`, tạo lúc **08:23:18 ngày
  15/09/2026 giờ Việt Nam**, đã xử lý 10.000, tạo 6.667, lỗi 3.333.
- Job giữ 200 lỗi đầu; tất cả cùng thông báo giá trị `Đã về TK` không có
  trong danh sách cột “Đối soát kế toán”, cột chưa có danh sách chọn.
  Hàng lỗi đầu trong Excel: 6, 9, 12, 15, 18, 21…
- Cấu hình hiện tại `doi_soat` là kiểu choice, nguồn lựa chọn rỗng.
  Tổng DataRecord còn hoạt động của bảng trên VPS là 6.667.
- `preview_error_count=0` nhưng worker ghi lỗi: lần nhập đó không báo được
  lỗi này ở bước xem trước. `status=done` nghĩa là xử lý xong, không có nghĩa
  tất cả dòng nhập thành công.

Kết luận: 3.333 dòng bị từ chối lúc nhập do danh sách lựa chọn, không phải
3.333 dòng đã lưu nhưng renderer không vẽ được. Tối ưu cuộn không phục hồi
các dòng này. Cần duyệt riêng cách khắc phục nhập dữ liệu, đối chiếu cấu hình
và quy tắc đã chốt, rồi chỉ nhập phần thiếu sau kiểm trùng; không nhập lại
toàn bộ 10.000 dòng một cách mù quáng.

### Nhật ký lần mở tiếp theo

**Bổ sung 15/09/2026 — Chủ dự án nhắc chức năng đối soát đã bị tắt:**
không coi đề xuất thêm lựa chọn `Đã về TK` là phương án được duyệt. ADR-025
ghi quyết định ngày 14/09 tạm khóa kho chứng từ bằng
`PAYMENT_DOCUMENTS_ENABLED=0`, giữ Bill dạng text; quyền xác nhận đối soát
không được mở. Cột dữ liệu `doi_soat` vẫn tồn tại độc lập và đang được
validator nhập file kiểm tra. Nguyên nhân từ chối 3.333 dòng đã xác định,
nhưng cách xử lý giá trị của cột đang ngừng dùng chưa chốt; không bật lại
chức năng, tự bỏ dữ liệu đối soát hoặc nhập bù trước khi chốt phạm vi.

Thêm mục ngày mới cùng việc đã làm, bằng chứng, việc còn nợ và bước tiếp theo;
giữ nguyên các phát hiện ngày 15/09/2026 để truy vết.
