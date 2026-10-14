> Phần của [Kế hoạch kiểm thử toàn diện KNJSC](../08-ke-hoach-kiem-thu-toan-dien.md) — mục lục, lộ trình P0/P1/P2 và rủi ro còn lại nằm ở tệp đó.

### 3.4 Đồng thời và CAS

**Phạm vi.** Mục này gồm mọi chỗ hai yêu cầu có thể chạm cùng một dữ liệu:
- ghi lưới CRM qua `luu-json/`;
- biên nhận chống gửi lặp: lưới, Lên đơn, nộp báo cáo, chứng từ;
- các khoá: khoá vòng đời bảng, khoá cấp mã đơn, khoá dòng;
- tính lại cột nền chạy song song với ghi;
- các màn ERP chưa có so phiên bản;
- các cờ tối ưu `CRM_OPT_*` (ADR-024), vì các cờ này đổi giao thức đọc, ghi và biên nhận của lưới.

**Hiện có**

| Cơ chế | Mã nguồn | Bài đang giữ |
|---|---|---|
| CAS từng ô. Lệch giá trị thì trả 409 cho cả lượt và không ghi lịch sử (AC-21.3, AC-21.9) | `crm/services/master_grid_service.py::save` (`@transaction.atomic`, `lifecycle_service.lock`) | `crm/tests/test_master_grid.py::test_same_cell_conflict_but_other_cell_survives`, `test_master_nine.py::test_conflict_rolls_back_whole_batch_and_no_history`, `::test_one_error_in_two_thousand_cells_rolls_back_everything` |
| CAS riêng từng thuộc tính định dạng | `record_service.normalise_style` | `test_master_nine.py::test_style_cas_merges_properties_and_preserves_value` |
| Biên nhận `GridMutationReceipt` (unique actor+operation, fingerprint sha256). Gửi lại thì trả `replayed`; khác nội dung thì 409; mỗi lần gửi lại vẫn kiểm quyền hiện hành | `crm/models.py` | `test_master_grid.py::test_replay_and_changed_payload`, `::test_replay_revoked_scope_denied`, `::test_concurrent_replay_applies_once` (Barrier), `::test_concurrent_cells_and_receipt`; `test_shared_integrity.py::test_replay_checks_current_grant`; `test_receipt_schema.py::test_committed_create_retry_after_schema_change_does_not_create_twice` |
| Các đường ghi cũ (`o/`, `luu-o/`, `dinh-dang/`, `dong-moi/`, `xoa-dong/`, `khoi-phuc-dong/`) trả 409 | `_master_upgrade_required` | `test_master_grid.py::test_legacy_writers_cannot_bypass_master_cas`, `test_shared_integrity.py::test_retired_writes_cannot_bypass_cas` |
| Hoàn tác (undo) khi ô đã bị người khác đổi | `master-working-copy.js`, `save` kind `undo` | `test_master_grid.py::test_undo_rejects_changed_cell_and_limits`, `test_shared_integrity.py::test_undo_creation_conflict_rolls_back_other_cells` |
| Tính cột công thức từ dòng đã khoá | `record_service._update_locked_cells` | `test_shared_integrity.py::test_concurrent_inputs_recompute_from_locked_row` |
| Lịch sử ô: chỉ ghi thêm, 50 mục/trang, có con trỏ (AC-21.10, AC-21.13) | `GridCellHistory`, `master_grid_service.history` | `test_lich_su_o.py` (2 bài), `test_master_nine.py::test_history_replay_and_scope`, `::test_history_cursor_is_bounded_and_append_only` |
| Chống gửi lặp bằng `core/submission.run_once` (AC-4.12, AC-6.11) | `SubmissionReceipt` | `reports/tests/test_nop_mot_lan.py`, `crm/tests/test_len_don_mot_lan.py` (đều có luồng song song) |
| Khoá cấp mã đơn (`pg_advisory_xact_lock`, lock_timeout 5s) | `order_service._lock_order_code` | `orders/tests/test_order_code_concurrency.py`; `scripts/order-code-check/` (chạy tay) |
| Ghép phân công theo CAS `version` (AC-20.1–20.3) | `assignment_service.assign` | `test_waybill_feedback.py` (có luồng song song) |
| CAS chứng từ theo `version`, replay theo `operation` (AC-26.3) | `payment_service` | `test_payment_documents.py` |
| Deadlock khi tính lại nền: worker nhường, thử lại tối đa 3 lần (RECOMPUTE_RETRIES); `bulk_save` sắp theo pk (K27) | `forms_builder/services/table_service.py::resync_table` dòng ~380; `forms_builder/models.py` dòng ~602 | Không có bài ép deadlock |
| Đơn vị JS: hàng đợi lưu, xung đột, tự lưu | `scripts/kiem-thu-master-conflict-unit.cjs`, `-queue-unit`, `-autosave-unit`, `kiem-thu-master-working-copy.cjs` | Chạy tay, **không có trong CI** (`.github/workflows/ci.yml` dòng 139-142) |

**Cờ tối ưu `CRM_OPT_*`.** Có tám cờ, khai ở `knjsc/settings/base.py` dòng 125-136 và đọc qua `crm/services/optimization.enabled(name)`. Tất cả mặc định tắt. `deploy/production/compose.yml` dòng 16-22 đặt `${CRM_OPT_*:-0}`. Riêng `CRM_REQUEST_METRICS` được đặt `'1'` ở dòng 14.

| Cờ | Tác động trong mã | Bài đang giữ | Ghi chú |
|---|---|---|---|
| `CRM_OPT_READ` | Đọc giao thức 2 cho bảng vận đơn (`master_grid_service.py` dòng 156; `master_views.py` dòng 218) | `crm/tests/test_optimization_contract.py::test_read_metadata_matches_current_grid`, `::test_read_refreshes_dynamic_choices_without_column_change`; `test_optimization.py::test_v2_repeat_block_has_no_count`, `::test_v2_value_change_keeps_query_and_rollback_does_not_publish` | CLAUDE.md: gây lỗi mở editor |
| `CRM_OPT_SYNC` | Đồng bộ dòng đổi (`master_grid_service.py` dòng 344). `master_sync` trả `unsupported` khi cờ tắt (`master_views.py` dòng 132). `syncUrl` chỉ có khi bật **cả READ lẫn SYNC** (dòng 221) | `test_optimization.py::test_sync_only_changed_visible_rows_and_no_scope_count`, `::test_warm_cache_loses_assignment_immediately` | CLAUDE.md: gây lỗi mở editor |
| `CRM_OPT_RECEIPTS` | Biên nhận gọn khi `protocol==2` (`master_grid_service.py` dòng 231). Fingerprint không phụ thuộc cờ | `test_optimization.py::test_v2_receipt_is_compact_and_replay_does_not_duplicate_history`, `::test_compact_receipt_survives_flag_rollback`; `test_market_currency.py` (nhánh compact, dòng 127) | Có bài tắt cờ khi đang có biên nhận gọn |
| `CRM_OPT_STATS` | Cache thống kê, bỏ qua khi đang trong giao dịch (`statistics_cache.py` dòng 16, 36) | `test_optimization.py::test_statistics_cache_expiry_refresh_and_access`, `::test_statistics_concurrent_miss_reuses_first_calculation`, `::test_redis_failure_reads_authoritative_data`; `test_thong_ke_lien_ket_nguon.py` | — |
| `CRM_OPT_RENDER` | Chỉ truyền `renderOptimized` sang JS (`master_views.py` dòng 220) | `test_scroll_fixture.py::test_export_scroll_fixture` đặt cờ False. Bài cho nhánh True ở JS: chưa xác minh | CLAUDE.md: chưa thấy lợi |
| `CRM_OPT_EXPORT` | Ghi Excel `write_only` (`export_service.py` dòng 122) | xem mục 3.5 | — |
| `CRM_OPT_QUEUES` | Định tuyến ba task `forms_builder` sang `crm_heavy` (`base.py` dòng 136+) | xem mục 3.6 | — |
| `CRM_REQUEST_METRICS` | `core.request_metrics.RequestMetricsMiddleware` | xem C37-17 | Đã bật trên production |

> **Điều cấm 15 (CLAUDE.md, ADR-024, ADR-029).** Chỉ được bật một cờ `CRM_OPT_*` ở môi trường dùng chung khi có **cả hai**: biên bản kiểm chứng `docs/kiem-chung-*.md` và lệnh của chủ dự án. Lưu ý này áp cho mọi ca đề xuất bật cờ trên Staging, gồm C36-04 và các ca PLAT-20, FB-21 ở phần khác. Ca nào thiếu hai điều kiện này thì chỉ được chạy ở local hoặc trong pytest bằng fixture `settings` (đổi cờ trong bài kiểm, không đổi môi trường).

**Thiếu**

- **TL-22 (S1, còn "Mới")** mô tả lỗi trên đường `luu-o/`. Đường này nay đã trả 409 (`_master_upgrade_required`), nên TL-22 phải được kiểm lại trên `luu-json/`. Grep "deadlock" chỉ ra `table_service.py` và `models.py`, nghĩa là `master_grid_service.save` không có vòng làm lại. Vậy khi va với tính lại nền, phía web bị Postgres huỷ thì nhận 500 hay 409: chưa xác minh. TL-24 (các đường ghi khác bị 500 khi trùng lúc tính lại) và TL-25 (không gộp job tính lại) vẫn mở.
- `bo-chi-tiet/` thiếu hai thứ:
  - không có biên nhận, nên gửi lại sau khi mạng chập trả 409 "vừa được người khác sửa" dù chính mình đã làm xong;
  - không ghi `GridCellHistory`.
  Tham chiếu: `waybill_service.clear_items/_clear` dòng 409-441.
- Dòng nháp (id âm) bỏ qua CAS, nên lịch sử ghi `before=c['old']` do client gửi lên. Client gửi giá trị giả thì lịch sử ghi giá trị giả (`master_grid_service.py` dòng 279, 311-313).
- Admin xoá dòng trong lúc người khác đang sửa dòng đó: người sửa nhận 403 "không còn quyền", sai bản chất. Chưa có bài khẳng định nháp ở các dòng khác vẫn được giữ.
- Hết phiên hoặc đổi `session_epoch` khi đang có nháp: `clearAccess()` tạo working copy mới, chữ đã gõ bị mất, lời báo ở nhánh poll sai (`master-grid.js` dòng 54-62, 858-861, 1291-1303, 1357).
- Đổi `delivery_view_version` khi đang có nháp: `reloadForViewMode()` xoá sạch nháp. Chưa có bài.
- Các màn ERP **không có so phiên bản**, người lưu sau đè người lưu trước:
  - `task_service.update_task` và `change_status`: tab cũ bấm "Đang làm" mở lại việc đã Xong, mất `done_at`;
  - `resource_service.update_resource`;
  - `threshold_service.update` ghi đè cả dict.
- Báo cáo ngày: `daily_service.amend` dựa vào `select_for_update`, vì `lifecycle_service.lock` chỉ là khoá chia sẻ. Chưa có bài hai luồng sửa cùng một báo cáo.
- Kiểm tồn tại rồi mới tạo (`exists()` → `create`), không bắt `IntegrityError`, nên ra 500 khi hai người tạo cùng lúc:
  - `document_service.create_category`, `resource_service.create_category`;
  - `create_product` (Product.code unique);
  - `account_service.create_with_temporary_password` (trùng `staff_code`).
- `Grant` không có ràng buộc duy nhất: cấp hai lần thì có hai dòng.
- Nhập tệp giữ khoá độc quyền suốt lượt (`import_service.run` dòng 347-357), nên mọi ghi lưới phải chờ. `set_progress` nằm trong cùng giao dịch, nên phiên khác thấy tiến độ đứng 0% rồi nhảy thẳng 100%.
- `toggle_like` và `award_monthly_stars` chạy song song: chưa có bài.
- **Tổ hợp cờ `CRM_OPT_*`.** Các bài hiện có bật từng nhóm cờ riêng (ví dụ fixture `enabled` trong `test_optimization.py` dòng 17-20 bật READ+SYNC+RECEIPTS+STATS cùng lúc). Chưa có ma trận chạy cùng bộ khẳng định CAS và biên nhận qua các tổ hợp cờ. Chưa có bài cho các ca:
  - `SYNC` bật mà `READ` tắt;
  - `RENDER=True` ở phía JS;
  - tắt `READ` khi tab đang mở ở giao thức 2.

**Ca cần thêm**

| Mã | Ca kiểm | Góc nhìn | Loại | Mức tự động | Ưu tiên | Khẳng định chính | Tham chiếu |
|---|---|---|---|---|---|---|---|
| C34-01 | Dán 500 ô `luu-json/` trong lúc `resync_table` chạy cùng lô, có monkeypatch ép deadlock | QA | Đồng thời (transactional_db, 2 kết nối) | Bán tự động | P0 | Hoặc mọi ô mới được giữ và có đúng 1 biên nhận, hoặc trả 409/503 rõ ràng. Không bao giờ trả 200 mà không ghi; cột tính sẵn khớp | TL-22, TL-24, ADR-016 |
| C34-02 | Gửi lại cùng UUID sau khi phản hồi bị chặn (server đã ghi) | Người dùng | e2e (route fulfill lỗi) | Bán tự động | P0 | DB đổi đúng một lần, 1 mục `GridCellHistory`, `replayed=true`, hiện "Đã lưu" | AC-21.3, AC-10.12 |
| C34-03 | Hai tab cùng một người sửa cùng ô | Người dùng | e2e | Bán tự động | P1 | Tab 2 nhận 409, hộp đối chiếu hiện giá trị 'A'. Chọn gửi lại thì ô thành 'B', lịch sử có 2 mục | AC-21.3, AC-21.10 |
| C34-04 | Hết phiên hoặc đổi quyền (`session_epoch`) giữa lúc có nháp, ở cả nhánh lưu và nhánh poll | Người dùng | e2e | Tự động | P0 | Lời báo nói rõ hết phiên, chữ đã gõ còn, không hiện "Quyền xem đã thay đổi", DB không đổi | AC-21.4, TL-02, TL-18 |
| C34-05 | Admin `delete_rows` dòng 1 trong lúc vd.staff có nháp ở dòng 1 và dòng 2 | Người dùng | Tích hợp + e2e | Bán tự động | P1 | Nháp dòng 1 bị gỡ kèm lời đúng; dòng 2 lưu được khi Thử lại; dòng 1 không có lịch sử mới | AC-21.4, AC-21.18 |
| C34-06 | Gửi `bo-chi-tiet/` hai lần cùng thân | Người dùng | Tích hợp | Tự động | P2 | WaybillItem bị xoá đúng một lần; lần 2 có lời "đã bỏ" (hoặc thêm biên nhận); có dấu vết trong lịch sử ô | AC-36.9 |
| C34-07 | Dòng nháp id=-1 gửi `old='giả'` | QA | Tích hợp | Tự động | P2 | `GridCellHistory.before` là None, không phải 'giả' | AC-21.10, BR-6 |
| C34-08 | Đổi `delivery_view_version` khi đang có nháp | Người dùng | e2e | Bán tự động | P2 | Có hỏi lại hoặc giữ nháp, không xoá lặng lẽ | `dispatch_service.py` dòng 137 |
| C34-09 | Hai luồng `daily_service.amend` cùng version | QA | Đồng thời | Tự động | P0 | Đúng một lần thắng, lần kia `ReportConflict`, `ReportRevision.count()==1` | ADR-032, AC-50.7 |
| C34-10 | Tab cũ đổi trạng thái việc Xong → Đang làm | Người dùng | Tích hợp | Tự động | P1 | 409/400 "đã đổi trạng thái", `done_at` giữ nguyên. Hiện đang đỏ | AC-14.3 |
| C34-11 | Hai quản lý sửa cùng tài nguyên hoặc cùng việc | Người dùng | Đồng thời | Bán tự động | P1 | Người sau không đè lặng lẽ (bài đỏ để chốt cách so `updated_at`) | FR-13.3, FR-11.5 |
| C34-12 | Hai quản lý lưu ngưỡng màu cùng lúc | QA | Đồng thời | Tự động | P2 | Không mất mốc của người kia, hoặc có báo xung đột | AC-42.9 |
| C34-13 | Hai Leader tạo cùng tên sản phẩm; hai Admin tạo hai người trùng mã nhân sự; tạo mục tài liệu/tài nguyên trùng tên | QA | Đồng thời (Barrier) | Tự động | P1 | Một bên thành công, bên kia nhận lời tiếng Việt, không 500 | AC-6.9, ADR-037, AC-12.1, AC-16.1 |
| C34-14 | Bấm Cấp quyền hai lần (double-click) | QA | Tích hợp | Tự động | P1 | Chỉ một Grant còn sống, hoặc lần hai báo "đã có" | FR-8.4 |
| C34-15 | Hai tab cùng bấm Xác nhận nhập | Người dùng | HTTP | Tự động | P1 | Lần hai báo "đã được xác nhận"; số dòng bằng số dòng trong tệp | FR-7.5 |
| C34-16 | Nhập 10.000 dòng vận đơn trong lúc vd.staff sửa ô | Người dùng | Hiệu năng + đồng thời | Bán tự động | P1 | Không 500, lưới báo đang bận, thời gian chờ được đo và ghi vào `docs/kiem-chung-*` | AC-7.5, ADR-027 |
| C34-17 | Tiến độ nhập nhìn thấy từ phiên khác | Người dùng | Tác vụ nền | Bán tự động | P2 | Đọc được `0 < progress < total` trước khi DONE. Hiện đang đỏ | FR-7.5 |
| C34-18 | Hai tab lên đơn cho cùng một khách; 30 Sale cùng khách | QA | Đồng thời | Tự động | P1 | Mã đơn khác nhau, `mua_lai` liên tục {1..30}, chỉ đúng một nhật ký đổi tên | AC-6.3, AC-6.8, AC-6.10 |
| C34-19 | Lỗi bên trong lần nộp rồi gửi lại cùng `ma_lan_nop` (đơn và báo cáo) | QA | Tích hợp | Tự động | P1 | Lần lỗi không để lại biên nhận; lần sau tạo đúng một bản | AC-6.11, AC-4.12 |
| C34-20 | Gửi lại `ma_lan_nop` của báo cáo hoặc đơn đã bị bỏ | Người dùng | Tích hợp | Tự động | P1 | Không 500 (hiện `DailyReport.DoesNotExist`), lời báo nói rõ đã bị bỏ | NFR-6, AC-4.9, AC-6.13 |
| C34-21 | Hai luồng `toggle_like`; hai luồng `award_monthly_stars` | QA | Đồng thời | Tự động | P2 | Like: 1 dòng. Sao kỳ: đúng 3 dòng `xep_hang`. Không `IntegrityError` lọt ra | FR-10.2, AC-15.3 |
| C34-22 | VĐ gửi lại lượt tạo chứng từ sau khi Kế toán đã xoá | QA | Tích hợp | Tự động | P2 | Lời báo rõ, `PaymentDocument.count()==1`, không có tệp mới trên đĩa | AC-26.3 |
| C34-23 | Chạy 9 script Node đơn vị lõi lưới trong CI, có assert `indexOf(marker)>=0` | QA | Đơn vị JS | Tự động | P0 | Mã thoát 0. Cần hỏi chủ dự án vì đổi CI (quy tắc 8) | docs/06 tầng 8 |
| C34-24 | Ma trận cờ trong pytest (fixture `settings`, không đổi môi trường). Bộ khẳng định cố định: CAS 409, replay, đổi nội dung thì 409, kiểm quyền khi replay, lịch sử 1 mục. Các tổ hợp: (a) tắt hết; (b) bật riêng từng cờ READ, SYNC, RECEIPTS, STATS, RENDER, EXPORT; (c) READ+SYNC; (d) READ+SYNC+RECEIPTS; (e) bật cả sáu; (f) đang bật rồi tắt giữa hai lượt gửi | QA | Tích hợp (parametrize) | Tự động | P1 | Mọi tổ hợp cho cùng kết quả nghiệp vụ. Với (b) chỉ bật SYNC: `syncUrl` là None và `master_sync` trả `unsupported`. Với (f): replay vẫn hợp lệ (như `test_compact_receipt_survives_flag_rollback`) | ADR-024, AC-21.3, Điều cấm 15 |
| C34-25 | Lưới với `CRM_OPT_RENDER=1` ở local: cuộn, sửa ô, dán 500 ô, xung đột 409 | Người dùng | e2e | Bán tự động | P2 | Hành vi giống khi tắt cờ. Kết quả ghi vào biên bản `docs/kiem-chung-*` làm điều kiện cho mọi đề xuất bật cờ sau này | ADR-024, Điều cấm 15 |

### 3.5 Nhập / xuất Excel

**Hiện có**

| Chủ đề | Bài (tệp::hàm) |
|---|---|
| Nhận diện loại tệp thật, tệp đổi đuôi, ≤10 MB, tiêu đề không ở hàng đầu, CSV `;` có BOM, tệp hỏng không nổ, ép kiểu ô | `core/tests/test_excel.py` (`test_tu_choi_tep_doi_duoi`, `test_excel_khai_la_csv_bi_tu_choi`, `test_kich_thuoc_qua_10mb`, `test_do_hang_tieu_de_khong_o_hang_dau`, `test_doc_csv_dau_cham_phay_va_bom`, `test_excel_hong_khong_no`, `test_ep_kieu_o_excel`, `test_ghi_bang_giu_decimal_va_ngay`…) |
| Bom giải nén (AC-7.15), không ô công thức (AC-7.14) | `forms_builder/tests/test_nhap_tep_bom.py`, `test_xuat_khong_cong_thuc.py` (chỉ đường kiểu cũ, fixture `marketing_scope`) |
| Bốn bước nhập: xem trước chưa ghi gì; dòng lỗi không chặn dòng đúng; giới hạn 10.000 dòng; 2.000 dòng < 60 giây; quyền hai chiều; tác vụ của người khác không thấy; tệp vận đơn thật có tiêu đề ở hàng 2 | `forms_builder/tests/test_nhap_xuat.py` (`test_xem_truoc_chua_ghi_gi`, `test_nhap_tep_co_dong_loi_van_nhap_dong_hop_le`, `test_tep_hon_10000_dong_bi_tu_choi`, `test_nhap_2000_dong_duoi_60_giay`, `test_nhap_tep_van_don_that_do_tieu_de_hang_2`, `test_tac_vu_nhap_cua_nguoi_khac_khong_thay`) |
| Ngày dạng số serial Excel (AC-7.16); nhập 1.000 dòng ít truy vấn, một nhật ký | `test_ngay_so_excel.py`, `test_nhap_hang_loat.py` |
| Chống trùng mã đơn khi nhập vận đơn | `test_import_checks.py` (có luồng song song) |
| Mẫu nhập (không có dữ liệu khách, DataValidation) | `test_import_template.py` |
| Xuất kèm lọc và sắp; xuất lớn chạy nền; vượt trần 50.000; chỉ dòng trong phạm vi; vòng xuất rồi nhập lại | `test_nhap_xuat.py::test_xuat_kem_bo_loc_va_sap_xep`, `::test_xuat_lon_chay_nen_va_tai_duoc`, `::test_xuat_vuot_tran_bi_tu_choi`, `::test_xuat_chi_ra_dong_trong_pham_vi`, `::test_xuat_roi_nhap_lai_khong_loi` |
| Hàng đợi chết (AC-10.13); đĩa đầy khi xuất nền (AC-10.14); tải tệp xuất sau khi bị thu quyền hoặc bảng đã xoá (ADR-027) | `crm/tests/test_hang_doi_chet.py` (gồm `::test_tac_vu_xuat_het_dia_noi_ro`), `test_shared_integrity.py::test_generic_export_revocation_and_deleted_table` |
| Cờ `CRM_OPT_EXPORT` (ghi `write_only`): tệp giống hệt khi tắt cờ, đường nền giống đường trực tiếp, kiểm lại quyền; giữ kiểu giá trị và hàng tiêu đề; ô ghi chú xuống dòng | `crm/tests/test_optimization.py::test_streaming_export_direct_background_equivalence_and_revocation`, `::test_streamed_excel_preserves_values_types_and_header`; `crm/tests/test_ghi_chu_tu_gian_dong.py::test_xuat_excel_cot_ghi_chu_xuong_dong` (tham số `ghi_lien`) |
| Excel Báo cáo tổng hợp | `reports/tests/test_mkt_excel.py` |

Ghi chú từ mã nguồn:
- `core/excel.py::coerce_cell` đổi chuỗi `DD/MM/YYYY` (có thể kèm giờ `H:MM`) thành `date`; số thực nguyên `7788599010.0` thành số nguyên; số thực có phần lẻ được giữ nguyên là float.
- `record_service.parse_value` với kiểu DATE dùng `date.fromisoformat`.
- Các trường hợp năm 2 chữ số, `31/02/2026` và chuỗi `M/D` kiểu Mỹ đi qua `coerce_cell` cho kết quả gì: **chưa xác minh**.

**Thiếu**

- **Số kiểu Việt và số lẻ.**
  - TL-03 (S1, còn "Mới"): `parse_money('0.125')` cho ra 125, áp cho cả nhập tệp và Lên đơn.
  - Ô Số nguyên: `'1,5'` và `'12.5'` thành 15 và 125 (`record_service.py` dòng 97-106).
  - Tiền hơn 2 chữ số lẻ từ ô số thật trong Excel làm JSON lệch `val_revenue numeric(18,2)`, và `kiem_tra_du_lieu` báo lệch mãi.
  - Ca phải có: `'1.234,567'`, `'12,345,678'`, `'1.2345'`.
- **Unicode.** Tệp `.xlsx`/`.csv` có giá trị dạng NFD, ô Đúng sai `'Có'` dạng NFD. Đã có chuẩn hoá ở `core/excel._o_nfc`/`_o_csv` nhưng chưa có bài khoá.
- **Cột thiếu hoặc thừa, nhãn lạ.** `import_service.map_columns`/`HEADER_ALIASES`/`QUANTITY_PREFIXES` chưa có bài cho các ca: cột thừa bị bỏ qua và có báo; cột bắt buộc thiếu thì báo trước khi xác nhận; trùng tên cột; tiêu đề NFD.
- **Trùng dữ liệu.** Bảng thường có cột khoá (ADR-010) không được kiểm trùng khi nhập: `import_check_service` chỉ bật cho `waybill`/`van_don`. Nhập lại cùng một tệp là nhân đôi doanh thu.
- **Bảng báo cáo Sale/MKT.** `create_records_bulk` → `report_input_values` gán Ngày = hôm nay, Người bán = người nhập, cho mọi dòng, không báo gì và không tạo `DailyReport`. Mẫu nhập lại hướng dẫn "Ngày: yyyy-mm-dd".
- **Nhánh phụ.**
  - Worker không kiểm lại `can_import` (`import_service.run` không gọi `grant_service`).
  - `don_tep_xuat_qua_han` xoá tệp theo mtime, kể cả tệp của job PENDING.
  - Xuất là GET (`bang_xuat` không có `require_POST`).
  - `check_download` gặp dòng đã bị xoá mềm thì báo "Quyền xem … đã thay đổi" (dòng 226-234), sai lý do.
- **Xuất đúng thứ đang hiện.**
  - Sắp xếp không ổn định ở bảng thường (TL-09); cột tiền trong JSON sắp theo chuỗi (TL-10).
  - Lọc `f_cpqc=1.500` qua `data__contains` trả 0 dòng (`query.apply_filters` dòng 154-158).
  - Lọc trên dữ liệu NFD cũ ra 0 dòng.
  - Tìm chung quét cả cột ẩn (`ColumnMap.searchable_paths`).
  Cả bốn lỗi đi thẳng vào tệp xuất.
- **Bảo mật Excel.** Chèn công thức ở đường nguồn đã cấu hình (`screen.export_response` → `excel._khoi`; ô mã nhân sự, team, sản phẩm) chưa có bài.
- **Giới hạn proxy.** Nginx `client_max_body_size 11m` không có trang lỗi 413 tiếng Việt.

**Ca cần thêm**

| Mã | Ca kiểm | Góc nhìn | Loại | Mức tự động | Ưu tiên | Khẳng định chính | Tham chiếu |
|---|---|---|---|---|---|---|---|
| C35-01 | Ô tiền `'0.125'`, `'12.345'`, `'1.234,567'`, `'12,345,678'`, `'1.2345'` trong tệp nhập | QA | Đơn vị + nhập tệp | Tự động | P0 | Hoặc từ chối kèm số hàng Excel, hoặc làm tròn theo quy tắc đã chốt. Không được nhân 1000 lặng lẽ. Bài sẽ đỏ trên mã hiện tại | TL-03, BR-8, ADR-046 |
| C35-02 | Ô Số nguyên `'1,5'`, `'12.5'` | QA | Đơn vị + nhập tệp | Tự động | P1 | Báo lỗi đúng dòng và cột, không ra 15 hay 125 | BR-8, NFR-6 |
| C35-03 | Ô số thật 1234.5678 vào cột nhãn Doanh thu | QA | Tích hợp DB | Tự động | P0 | `integrity_service.lech_cot_tach(table)['so']==0`; `Sum(val_revenue)` khớp JSON theo cùng quy tắc làm tròn | BR-8, ADR-001, AC-36.14 |
| C35-04 | Ngày `13/10/2026`, `0:58 14/10/2023`, `31/02/2026`, `29/02/2028`, `03/04/26`, serial 45000.99, chuỗi `2026-10-13` | QA | Đơn vị (`coerce_cell` + `parse_value`) | Tự động | P1 | Ngày hợp lệ lưu đúng ISO; ngày vô lý báo lỗi tiếng Việt; ghi rõ cách đọc năm 2 chữ số (chưa xác minh) | AC-7.16, AC-32.1, AC-9.8 |
| C35-05 | Tệp có cột thiếu, cột thừa, tiêu đề NFD, hai cột cùng tên | QA | Tích hợp nhập tệp | Tự động | P1 | Bước xem trước báo cột thiếu hoặc thừa; không ghi gì trước khi xác nhận; tiêu đề NFD khớp đúng cột | FR-7.5, AC-7.6 |
| C35-06 | Giá trị và ô Boolean dạng NFD trong `.xlsx` và `.csv` | QA | Tích hợp nhập tệp | Tự động | P2 | Dữ liệu lưu ở dạng NFC; `?tim=` (NFC) ra dòng; 'Có' thành True. Sau khi nhập, câu `SELECT count(*) FROM forms_builder_datarecord WHERE NOT (data::text IS NFC NORMALIZED)` không tăng | AC-9.6, TL-79, `docs/kiem-chung-san-loi-go-tieng-viet-20261006.md` |
| C35-07 | Tệp vận đơn bẩn: SĐT `+1 (416)…`, ô Ghi chú có Alt+Enter, mã đơn trùng dòng sống, tiền `'1.234,5'` | Người dùng | Chức năng (KN CRM) | Tự động | P1 | Lỗi báo đúng dòng; cột Trùng đếm đúng sau khi nhập; dòng trùng mã bị từ chối | AC-11.9, AC-36.8, AC-11.44 |
| C35-08 | Nhập cùng một tệp hai lần vào bảng thường có cột khoá | Người dùng | Chức năng HTTP | Tự động | P1 | Bước xem trước cảnh báo số dòng trùng khoá (theo chốt); bảng vận đơn lần hai báo 10 dòng "Mã đơn đã tồn tại" | FR-7.5, ADR-010 |
| C35-09 | Nhập mẫu `bao_cao_mkt` ngày 2026-09-01, 3 Marketer khác nhau | Người dùng | HTTP + eager | Bán tự động | P1 | Không âm thầm đổi thành hôm nay và người nhập. Chủ dự án chốt giữ theo tệp hay chặn | ADR-032, ADR-043 |
| C35-10 | Thu quyền Sửa giữa lúc xác nhận và lúc worker chạy | QA | Tích hợp tác vụ | Tự động | P1 | Job FAILED "quyền đã thay đổi", hoặc ghi nhận hành vi để chốt | AC-3.6, ADR-027 |
| C35-11 | Tệp 10.000 dòng, 10.000 + 1 dòng, 10 MB + 1 byte, ZIP rác đổi đuôi `.xlsx` | QA | Biên | Tự động | P2 | Phần lớn đã có; bổ sung ca CSV lớn và `.xlsx` hỏng một phần | NFR-11, NFR-13, AC-7.8, AC-7.9 |
| C35-12 | Tệp 10,5 MB và 12 MB qua Nginx trên Staging | Người dùng | Proxy | Thủ công | P2 | 10,5 MB: lời tiếng Việt. 12 MB: ghi lại trang 413 hiện ra | NFR-6, NFR-11 |
| C35-13 | Xuất lưới đúng thứ đang hiện: `trung=1`, `sp`, `cua_toi=1`, cột ẩn cả công ty, chip lọc trên cột ẩn | Người dùng | HTTP | Tự động | P1 | Số dòng, thứ tự cột và cột ẩn trong tệp khớp lưới; cột ẩn không có trong tệp; AuditLog EXPORT ghi bộ lọc | ADR-002, AC-11.13, AC-33.4, AC-39.8 |
| C35-14 | Xuất bảng thường có 60 dòng cùng giá trị sắp; cột tiền không nhãn `['999','1234.50']` | QA | Tích hợp truy vấn | Tự động | P1 | Không lặp hoặc sót dòng qua các trang và trong tệp; 999 đứng trước 1234.50 | TL-09, TL-10 |
| C35-15 | Xuất kèm `f_cpqc=1.500`, `f_x__trong=<NFD>` | QA | Tích hợp truy vấn | Tự động | P2 | Khớp đúng dòng, hoặc giao diện báo không hỗ trợ; không trả 0 dòng lặng lẽ | AC-7.2, AC-9.6 |
| C35-16 | Xuất `?dang=tho` bảng báo cáo và Báo cáo tổng hợp (cả `gop=1`, nguồn Vận đơn) với team `'=1+1'`, mã `'=HYPERLINK(…)'` | QA | Bảo mật Excel | Tự động | P1 | Không ô nào có `data_type 'f'`; chữ giữ nguyên. Chạy cả khi `CRM_OPT_EXPORT` tắt và bật | AC-7.14, FR-5.6, ADR-024 |
| C35-17 | Tải tệp xuất nền sau khi Admin xoá mềm một dòng | Người dùng | Tích hợp | Tự động | P2 | Cho tải, hoặc báo đúng lý do "có dòng đã xoá" | ADR-027, ADR-049 |
| C35-18 | Tác vụ IMPORT PENDING có tệp lùi mtime 25 giờ, rồi chạy `core.don_tep_xuat_qua_han` | QA | Tác vụ định kỳ | Tự động | P2 | Tệp còn, hoặc job FAILED kèm lời rõ | NFR-16 |
| C35-19 | **Vòng tròn đầy đủ**: dữ liệu có tiền nhiều loại tiền, ngày, Chọn một, NFD, cột ẩn, ô ghi chú nhiều dòng. Xuất → nhập lại vào bảng trống cùng cấu trúc → xuất lần 2 | QA | Tích hợp | Tự động | P0 | Hai tệp xuất giống từng ô; Decimal không lệch; ngày không đảo ngày/tháng; cột ẩn không ra rồi không bị nhập thành rỗng; số dòng bằng nhau | ADR-002, BR-8, ADR-039 |
| C35-20 | Vòng tròn trên bảng vận đơn: xuất → nhập lại vào chính bảng đó | QA | Tích hợp | Tự động | P1 | Mọi dòng bị từ chối "Mã đơn đã tồn tại"; không tạo đơn mới; các cột tổng (`san_pham`, `so_luong`) và Bill `'REF-A; REF-B; Bill cũ'` xử lý ra sao: chưa xác minh, cần chốt | AC-36.4, AC-26.5, AC-11.9 |

### 3.6 Tác vụ nền (Celery) và lệnh manage.py

**Tác vụ Celery** (tên lấy từ `@shared_task(name=…)`; lịch lấy từ `knjsc/settings/base.py` `CELERY_BEAT_SCHEDULE`, múi giờ Asia/Ho_Chi_Minh)

| Tác vụ | Lịch | Kiểm gì | Hiện có | Thiếu |
|---|---|---|---|---|
| `core.kiem_tra_hang_doi` | Gọi khi cần | Hàng đợi chết thì báo rõ, không 500 (AC-10.13) | `crm/tests/test_hang_doi_chet.py` | CI không có Redis (`ci.yml` dòng 49-52, 99-102) |
| `core.danh_dau_tac_vu_ket` | Mỗi 15 phút | PENDING quá 15 phút thành STALE, có nhật ký và thư (AC-9.2) | `core/tests/test_sao_luu.py` dòng 214-223 (chỉ PENDING) | **TL-23**: RUNNING kẹt mãi vì chỉ lọc `status=PENDING` (`core/tasks.py` dòng 35-36). Hậu quả: lưới hiện "đang tính lại" vĩnh viễn; `lifecycle_service.delete` bị chặn mãi vì còn IMPORT/RECOMPUTE RUNNING |
| `core.don_tep_xuat_qua_han` | 03:00 | Xoá tệp xuất/nhập quá 24 giờ, đóng DRAFT (NFR-16); không đụng `storage/tai-lieu` (AC-12.5) | Có bài AC-12.5 (theo dữ liệu) | Xoá theo mtime cả tệp của job PENDING |
| `core.sao_luu_hang_dem` | 02:00 | Thất bại thì FAILED, có nhật ký và thư (NFR-19); giữ 30 bản (NFR-15) | `core/tests/test_sao_luu.py` | Không sao lưu `storage/tai-lieu` (K30); `list_backups` sắp theo tên nên tệp sai khuôn bị chọn nhầm |
| `forms_builder.chay_tac_vu_nhap` | Theo yêu cầu | Chạy lại kiểm trùng; khoá bảng; tiến độ | `test_nhap_xuat.py`, `test_import_checks.py` | Không kiểm lại quyền; tiến độ không nhìn thấy từ phiên khác; worker chết thì job kẹt RUNNING |
| `forms_builder.chay_tac_vu_xuat` | Theo yêu cầu | ≤50.000 dòng; kiểm lại quyền khi tải; đĩa đầy giữa chừng thì FAILED, có lời "hết chỗ lưu tệp" và gửi thư cho người vận hành (AC-10.14) | `test_xuat_lon_chay_nen_va_tai_duoc`, `test_shared_integrity.py`, `crm/tests/test_hang_doi_chet.py::test_tac_vu_xuat_het_dia_noi_ro` (patch `build_workbook` ném ENOSPC, patch `core.alerts.mail_admins`), `test_optimization.py::test_streaming_export_direct_background_equivalence_and_revocation` | Ca ENOSPC chỉ phủ đường `build_workbook`. Ca đĩa đầy lúc ghi theo luồng khi bật `CRM_OPT_EXPORT`: chưa xác minh |
| `forms_builder.chay_tac_vu_tinh_lai` | Theo `schedule_resync` (>2.000 dòng) | Lô 1.000, 2 luồng, thử lại deadlock 3 lần | Không có bài ép deadlock hay giết worker | TL-23, TL-25 (mỗi lần đổi cột một job, không gộp). Định tuyến `crm_heavy` khi bật `CRM_OPT_QUEUES` mà không có worker `-Q crm_heavy` (`deploy/docker-compose.yml` dòng 94) thì job nằm PENDING rồi thành STALE |
| `feed.thiep_sinh_nhat` | 06:00 | Mỗi người mỗi ngày đúng một thiệp; bù tối đa 14 ngày | `feed/tests/test_bang_tin.py` | Không có nhánh báo lỗi (không nhật ký, không thư); mốc `Max(birthday_on)` bị dời khi chạy tay `--ngay`; không đóng băng giờ |
| `culture.thuong_sao_thang` | Ngày 1, 01:00 | Hạng 1/2/3 nhận 5/3/1 sao; chạy lại không nhân đôi | `culture/tests/test_van_hoa.py::test_thuong_sao_top_ba_thang_truoc_khong_nhan_doi` | Thứ hạng đổi sau khi đã thưởng (khoá tài khoản, bỏ đơn, khôi phục dòng) thì lần chạy sau thưởng thêm người; nhánh `bao_nguoi_van_hanh` khi thiếu tỉ giá KRW chưa có bài |

**Chạy bù khi bật máy.** `deploy/entrypoint.sh` chỉ chạy `thiep_sinh_nhat` và `thuong_sao_thang` khi `RUN_MIGRATIONS=1`.
- Local: `deploy/docker-compose.yml` dòng 57 bật cờ này, nên hai lệnh chạy **mỗi lần bật máy**.
- VPS: `deploy/production/compose.yml` dòng 12 đặt `'0'`, nên chỉ trông vào beat.
- Beat có chạy bù lần bị lỡ không: **chưa xác minh**.
- `configure_erp_reports` lỗi thì entrypoint dòng 49 chỉ in "CANH BAO".

**Lệnh manage.py quan trọng**

| Lệnh | Kiểm gì | Hiện có | Thiếu |
|---|---|---|---|
| `orders tao_bang_van_don` | Chạy lại không thêm gì, nâng cấp tại chỗ giữ ID; cấu trúc đổi thì tính lại (AC-36.1, 36.2, 36.13) | `crm/tests/test_mot_bang_van_don.py`, `orders/tests/test_nang_cap_tinh_lai.py` | — |
| `orders kiem_tra_du_lieu [--bang] [--sua]` | Năm phép rà, thoát mã 1 khi lệch, `--sua` mã trùng (AC-36.14–36.16) | `orders/tests/test_kiem_tra_du_lieu.py` | Nhánh "đơn đã bỏ, dòng còn sống"; đơn sống có `record=None` sau `xoa_bang_van_don_cu` bị báo lệch, chặn bước "Dữ liệu khớp"; tiền >2 chữ số lẻ lệch mãi |
| `orders xoa_bang_van_don_cu` | Hai cờ, không xoá `van_don`, từ chối khi còn FormDef/DailyReport (AC-36.5, ADR-036) | `test_mot_bang_van_don.py::test_hard_delete_command_removes_old_tables_only_with_flags` | Dùng `Order.objects` nên bỏ sót đơn đã bỏ, vỡ PROTECT; hai nhánh CommandError chưa có bài; tệp ảnh chứng từ mồ côi |
| `orders nap_du_lieu_van_don`, `nap_khach_mau`; `core seed_perf` | Chỉ chạy khi DEBUG, hoặc có `--dong-y-chay-that` (NFR-4); chạy lại không trùng; dọn dòng giả | `orders/tests/test_nap_du_lieu_van_don.py`, `test_nap_khach_mau.py`, `core/tests/test_seed_perf_xoa.py` | `delete_fake_records` vỡ `IntegrityError` khi dòng đã có `GridCellHistory`/`PaymentDocument` (PROTECT); hàng rào DEBUG của `seed_perf` chưa có bài |
| `core du_lieu_mau`, `cap_nhat_mat_khau_mau` | Hàng rào DEBUG; chạy lại thì đặt lại mật khẩu (TL-30) | `tests/test_du_lieu_mau.py`, `tests/test_cap_nhat_mat_khau_mau.py` | Không gieo Kế toán, CSKH, Leader VĐ, CEO |
| `core du_lieu_solarpunk` | Chỉ chạy trên DB preview | — | Chưa có bài hàng rào |
| `core sao_luu`, `phuc_hoi --toi-chac-chan` | Tệp `.part` rồi mới đổi tên, chữ ký PGDMP, mật khẩu qua PGPASSWORD | `core/tests/test_sao_luu.py` | Chọn bản theo tên tệp; không có `storage/tai-lieu` |
| `reports configure_erp_reports`, `configure_delivery_daily_report` | Chạy lại idempotent; CommandError khi cấu hình sai | `test_configure_currency_options`; `reports/tests/test_delivery_daily.py::test_delivery_daily_configure_submit_history` (gọi `configure_delivery_daily_report` hai lần); `reports/tests/test_local_report_samples.py::test_samples_are_submitted_idempotent_and_cannot_login` (gọi cả hai lệnh) | Nhánh thiếu cột và nhiều cột Doanh thu/Hóa đơn; `@transaction.atomic` làm mất cả ba nguồn khi một nguồn lỗi |
| `reports nap_bao_cao_mau --xoa-cu`, `seed_local_report_history` | Chỉ chạy trên máy dev; chạy lại không trùng; tài khoản mẫu không đăng nhập được | `test_nap_bao_cao_mau.py`; `reports/tests/test_local_report_samples.py::test_samples_are_submitted_idempotent_and_cannot_login` (chạy lệnh hai lần), `::test_samples_refuse_production` | `--xoa-cu` thực chất là xoá mềm (`SoftDeleteQuerySet.delete`), nên mẫu hiện ở trang Đã bỏ |
| `org gan_ma_nhan_su_cu --thu/--xac-nhan` | Xem trước (mặc định hoặc `--thu`) không ghi gì; `--xac-nhan` gán mã cho hồ sơ rỗng; chạy lại không đổi thêm và không thêm nhật ký (AC-37.6, ADR-037) | `org/tests/test_ma_nhan_su.py::test_lenh_gan_ma_nhan_su_cu` | Bài chưa gọi cờ `--thu` một cách tường minh |
| `feed thiep_sinh_nhat [--ngay]`, `culture thuong_sao_thang [--thang]` | Ngày tương lai thì CommandError; `"2026-9"` chuẩn hoá thành `"2026-09"` | `feed/tests`, `culture/tests` | Như bảng tác vụ phía trên |

**Ca cần thêm**

| Mã | Ca kiểm | Góc nhìn | Loại | Mức tự động | Ưu tiên | Khẳng định chính | Tham chiếu |
|---|---|---|---|---|---|---|---|
| C36-01 | Job RECOMPUTE, IMPORT, EXPORT ở trạng thái RUNNING, `updated_at` cũ hơn ngưỡng, rồi chạy `danh_dau_tac_vu_ket` | Người dùng | Tác vụ định kỳ | Tự động | P0 | Thành STALE/FAILED kèm thư; `recompute_job_of` là None; xoá bảng không còn bị chặn. Job vừa cập nhật 1 phút trước thì giữ nguyên | TL-23, ADR-016, ADR-027 |
| C36-02 | Giết worker giữa lượt tính lại 100.000 dòng (`docker compose restart worker`) trên Staging | QA | Vận hành | Thủ công | P1 | Sau ngưỡng job được giải phóng; lưới lại tự cập nhật; chạy lại thì dữ liệu cột tính khớp | TL-23 |
| C36-03 | Bỏ 5 cột liên tiếp | QA | Tích hợp | Tự động | P2 | Số job RECOMPUTE PENDING ≤1 sau khi sửa TL-25; giá trị cuối khớp công thức cuối | TL-25 |
| C36-04 | Bật `CRM_OPT_QUEUES=1`: route ba task `forms_builder` sang `crm_heavy`, compose đích có worker `-Q crm_heavy`. **Điều kiện trước (Điều cấm 15):** chạy ở local trước, lập biên bản `docs/kiem-chung-*`, có lệnh của chủ dự án rồi mới bật trên Staging | QA | Khói triển khai | Bán tự động | P2 | Một lượt nhập nhỏ thành DONE; tắt cờ thì job lại chạy ở hàng `celery` | ADR-024, ADR-016, ADR-029, `deploy/production/README.md` dòng 58 |
| C36-05 | `thuong_sao_thang` chạy lại sau khi người hạng 1 bị khoá hoặc bỏ đơn tháng trước | Người dùng | Tích hợp | Tự động | P1 | Số dòng `xep_hang` của kỳ vẫn là 3. Hiện đang đỏ | FR-12.4, Q72, AC-15.3 |
| C36-06 | Đơn KRW tháng trước, chạy tác vụ và lệnh `thuong_sao_thang` | Người dùng | Tích hợp + vận hành | Tự động | P1 | Tác vụ: trả 0, gửi 1 thư, có nhật ký "thất bại". Lệnh: CommandError nêu KRW | AC-15.3, BR-8 |
| C36-07 | `thiep_sinh_nhat --ngay hôm nay` rồi `catch_up` | Người dùng | Tích hợp (giờ) | Tự động | P1 | Người sinh vào ngày ở giữa vẫn có thiệp. Hiện đang đỏ | FR-10.4, AC-13.4 |
| C36-08 | `feed.thiep_sinh_nhat` gặp DatabaseError | QA | Vận hành | Tự động | P2 | Có nhật ký và thư như `culture/tasks.py` | FR-10.4 |
| C36-09 | Lịch beat khớp tên tác vụ, giờ và `CELERY_TIMEZONE` | QA | Cấu hình | Tự động | P1 | 5 mục lịch trỏ đúng task đã đăng ký trong `app.tasks` | ADR-017 |
| C36-10 | Dừng beat trước 06:00, bật lại lúc 06:10 trên compose production | QA | Vận hành | Thủ công | P1 | Ghi nhận có chạy bù không; nếu không thì ghi bước chạy tay vào `docs/05` | FR-10.4, FR-12.4 |
| C36-11 | `xoa_bang_van_don_cu` khi bảng cũ còn đơn đã bỏ; còn FormDef hoặc DailyReport; còn PaymentImage | QA | Lệnh quản trị | Tự động | P1 | Không `IntegrityError`; đơn đã bỏ có `record_id=None`; CommandError khi còn biểu mẫu hoặc báo cáo; ghi nhận tệp ảnh mồ côi | AC-36.5, ADR-036 |
| C36-12 | `kiem_tra_du_lieu` sau khi xoá cứng bảng cũ; khi có đơn đã bỏ mà dòng còn sống; khi `--bang` lặp | QA | Lệnh quản trị | Tự động | P1 | Mã thoát và câu báo đúng quy tắc đã chốt cho `record=None` | AC-36.14, TL-76 |
| C36-13 | `nap_khach_mau --xoa-cu` và `seed_perf --xoa-cu` sau khi dòng KH-* đã có lịch sử ô hoặc chứng từ | Người dùng | Lệnh quản trị | Tự động | P1 | Xoá sạch, hoặc báo rõ dòng nào chặn; không vỡ giữa chừng | TL-43, AC-10.9 |
| C36-14 | Hàng rào `seed_perf` và `du_lieu_solarpunk` khi `DEBUG=False` | QA | Lệnh | Tự động | P2 | CommandError; không bảng nào đổi số dòng | NFR-4 |
| C36-15 | `configure_erp_reports` với bảng MKT thiếu `cpqc`; hai cột "Hóa đơn"; `thi_truong` không phải choice; chạy lại trên bảng có dữ liệu | QA | Tích hợp lệnh | Tự động | P1 | CommandError nêu rõ lỗi; không còn ReportSource dở dang; CPO, Giá Mess, AOV không đổi sau `resync_if_changed` | ADR-043, ADR-048 |
| C36-16 | `phuc_hoi` mặc định khi thư mục có `knjsc-ban-sao.dump` | QA | Đơn vị | Tự động | P2 | Chọn đúng bản có ngày mới nhất; `rotate` xoá đúng bản cũ | NFR-10, NFR-15 |
| C36-17 | Một lượt CI có service `redis:7` chạy `test_khoi_luoi_dem.py`, `test_optimization.py` không override LocMem | QA | Tích hợp hạ tầng | Tự động | P2 | Hit/miss và mất phân công đúng như với LocMem. Chỉ đổi CI, không thêm thư viện | AC-10.26 |
| C36-18 | `chay_tac_vu_xuat` với `CRM_OPT_EXPORT=True` (fixture `settings`), patch thao tác ghi tệp ném ENOSPC | QA | Tích hợp tác vụ | Tự động | P2 | Như `test_tac_vu_xuat_het_dia_noi_ro`: job FAILED, có lời "hết chỗ lưu tệp", gửi thư, không để lại tệp dở | AC-10.14, ADR-024 |

### 3.7 Migration, toàn vẹn dữ liệu, xoá mềm và nhật ký

**Tệp chuyển đổi cấu trúc: hiện có**

| Hạng mục | Tệp | Bài |
|---|---|---|
| Model lệch tệp chuyển đổi; mỗi app có tệp chuyển đổi; chạy ngược rồi chạy xuôi lại được; không có hai nhánh lá. Áp cho 11 app trong `CAC_APP` | — | `core/tests/test_chuyen_doi.py` (`test_model_va_tep_chuyen_doi_khong_lech`, `test_khong_co_hai_nhanh_la_trong_mot_app`, `test_moi_app_deu_co_tep_chuyen_doi`, `test_chay_nguoc_roi_chay_xuoi_lai_duoc`; dấu `cham`). **Đã chạy trong CI**: job `kiem-thu` chạy `pytest -m "not trinh_duyet"`, có cả bài `cham`, cho mọi PR và mọi lần đẩy lên `Staging` và `main` (`.github/workflows/ci.yml` dòng 1-24, 91) |
| `core 0002_pg_trgm` (`TrigramExtension`, chạy ngược thì gỡ extension) | `core/migrations/0002_pg_trgm.py` | CI chạy bằng tài khoản superuser của image Postgres. Chú thích `ci.yml` dòng 58-60 ghi rằng extension này cần đúng quyền đó. CI chưa kiểm với role có quyền như trên VPS |
| `crm 0004_grid_change_triggers` (RunSQL kèm REVERSE; trigger DEFERRABLE, giữ 10.000 phiên bản) | `crm/migrations/0004_grid_change_triggers.py` | Gián tiếp qua `test_optimization.py` (`::test_revision_migration_forward_backward_preserves_business`, `::test_journal_retention_and_large_statement_reset`), `test_khoi_luoi_dem.py` |
| Lịch sử ô và chỉ mục phủ: xuôi/ngược giữ dòng | crm | `test_master_nine.py::test_history_migration_roundtrip_keeps_rows`, `::test_cover_index_migration_roundtrip_keeps_rows` |
| `forms_builder 0016` (backfill `val_phone_key` bằng một UPDATE, chạy ngược là noop) | `0016_datarecord_val_phone_key.py` | `crm/tests/test_khoa_trung_sdt.py` (MigrationExecutor 0015→0016) |
| `forms_builder 0017` (backfill `val_order_code`, `dung_neu_con_trung`) và pre_migrate `chan_migrate_khi_trung_ma` (AC-36.15, AC-36.16) | `0017_datarecord_val_order_code.py`, `integrity_service.chan_migrate_khi_trung_ma` | `crm/tests/test_ma_don_khong_trung.py` |
| `forms_builder 0015` (`is_hidden`, AC-39.7) | — | Chưa xác minh tên bài |
| `orders 0011` ẩn cột `sl_*` cũ, chạy ngược là noop (AC-39.9) | — | Theo dữ liệu đã có bài; chưa xác minh tên |
| `reports 0006` đổi dòng MKT sang VND, chạy ngược lấy lại theo Thị trường (AC-47.3) | `0006_bao_cao_mkt_tien_viet.py` | `reports/tests/test_mkt_tien_viet.py` (3 dòng còn sống) |
| Các RunPython xuôi/ngược khác: `orders 0002` (xuoi/nguoc), `orders 0005`, `crm 0005` (forward/backward), `org 0004` (thêm bộ phận `ke-toan`, ngược là noop) | — | Bài round-trip có dữ liệu riêng: chưa xác minh |

**Thiếu (migration)**
- `reports 0006` với hơn 500 dòng (nhánh `bulk_update` theo lô) và dòng đã xoá mềm.
- Round-trip có dữ liệu cho `orders 0002`, `orders 0005`, `crm 0005`.
- Đo thời gian backfill 0016/0017 trên bản sao dữ liệu cỡ thật. Docstring 0016 ghi 120 nghìn dòng đi trong một lượt UPDATE.
- Chạy `migrate` trên bản sao DB production ở Staging trước mỗi lần phát hành, kèm `kiem_tra_du_lieu` trước và sau (Chặng 2).
- **Quyền của role Postgres với extension.** `core/0002_pg_trgm` cần tạo extension `pg_trgm`. CI tạo được vì chạy bằng superuser. Chưa có ca xác nhận role mà ứng dụng dùng trên VPS tạo được extension, hoặc extension đã có sẵn trong DB đích. Chạy ngược `0002` sẽ gỡ extension, kéo theo các chỉ mục `gin_trgm_ops` (ví dụ `core 0003_auditlog_audit_actor_label_trgm`). Hai điểm này trên VPS: chưa xác minh.
- Không có migration chuẩn hoá dữ liệu NFD cũ (TL-79). Đã có câu SQL chỉ đọc để đếm: `SELECT count(*) FROM forms_builder_datarecord WHERE NOT (data::text IS NFC NORMALIZED);` (`docs/kiem-chung-san-loi-go-tieng-viet-20261006.md` dòng 44; cũng dùng ở `docs/kiem-chung-dien-tap-phat-hanh-staging-20261008.md` dòng 276).

**Bất biến toàn vẹn nên kiểm định kỳ.** Đề xuất mở rộng `kiem_tra_du_lieu`, hoặc thêm một lệnh rà chỉ đọc, chạy trước và sau phát hành.

| Bất biến | Hiện có | Nguồn |
|---|---|---|
| Cột tách `val_*` khớp JSON | Có (`lech_cot_tach`) | AC-36.14 |
| Một mã đơn chỉ có một dòng sống | Có (`ma_don_trung`, ràng buộc `record_ma_don_unique`) | AC-36.11 |
| Đơn gốc ↔ dòng vận đơn (sống/bỏ) | Có (`don_mo_coi`), nhưng báo nhầm khi `record=None` | AC-6.12, AC-36.5 |
| `sl_*` khớp chi tiết; giá trị ngoài danh sách chọn | Có (`so_luong_lech` chỉ ở mức "BIẾT", `ngoai_danh_sach`) | AC-36.14 |
| Tiền trong JSON tối đa 2 chữ số lẻ, khớp `val_revenue` | Thiếu | BR-8 |
| `DailyReport.department` bằng `DataRecord.department` của dòng số liệu | Thiếu | ADR-043, ADR-045 |
| Không có hai Grant sống trùng (đối tượng, người nhận, hành động) | Thiếu | FR-8.4 |
| Không trùng `lower(username)`; `username` không trùng `staff_code` của người khác | Thiếu | ADR-037 |
| Trưởng nhóm cùng bộ phận với team | Thiếu | ADR-003 |
| Không job RUNNING quá ngưỡng | Thiếu | TL-23 |
| Mọi `PaymentImage.file_path` và `Document.file_path` sống có tệp trên đĩa; đếm tệp mồ côi trong `storage/tai-lieu`, `chung-tu-thanh-toan` | Thiếu | K30, AC-26.4 |
| Hai sản phẩm không chung một cột `sl_*` | Thiếu | AC-11.8 |
| Đếm dòng `DataRecord` còn chữ dạng NFD | Thiếu trong lệnh rà. Đã có câu SQL chỉ đọc `SELECT count(*) FROM forms_builder_datarecord WHERE NOT (data::text IS NFC NORMALIZED)`, dùng lại nguyên câu này | TL-79, `docs/kiem-chung-san-loi-go-tieng-viet-20261006.md` |
| Số dòng `AuditLog`, `GridCellHistory`, `ReportRevision` không giảm giữa hai lần rà (trừ khi `xoa_bang_van_don_cu` có cờ) | Thiếu | BR-6, ADR-036 |

**Xoá mềm (BR-4): hiện có và thiếu**
- **Cơ chế.**
  - `SoftDeleteQuerySet.delete` chỉ đánh dấu (`core/managers.py` dòng 24-30).
  - `ProfileQuerySet.delete` ném RuntimeError.
  - `PreservedUserAdmin` không cho xoá cứng.
- **Xoá cứng có chủ đích:**
  - `xoa_bang_van_don_cu` (có cờ, ADR-036);
  - `seed_perf.delete_fake_records` và `nap_khach_mau --xoa-cu` (`_raw_delete`).
- **Khôi phục đã có bài:**
  - báo cáo (AC-4.10);
  - dòng (AC-21.18/19, AC-36.11; `test_chi_admin_xoa_dong.py`);
  - bảng (`test_table_lifecycle.py`, `test_shared_integrity.py::test_restore_detaches_deleted_folder`);
  - chứng từ (đường thuận).
- **Thiếu:**
  - Tạo lại bộ phận hoặc team trùng tên với bản đã xoá mềm: ModelForm kiểm trùng qua `AliveManager` nên lọt kiểm tra, rồi ra 500.
  - Xoá team hoặc bộ phận qua `/quan-tri/` không có `deleted_by`, không có nhật ký.
  - Thu một quyền đã thu thì ghi đè `deleted_at`/`deleted_by` của lần thu đầu (`views.py` dòng 517, 726).
  - `grants_of_table` liệt kê cả quyền đã thu.
  - Khôi phục dòng vận đơn làm Order sống lại, đổi bảng xếp hạng của tháng đã thưởng.
  - Khôi phục chứng từ khi Ref đã có lại: chưa có bài.
  - `nap_bao_cao_mau --xoa-cu` thực chất là xoá mềm.
  - Cửa xoá/khôi phục bảng thường ở 8021 không qua `catalog.chi_van_don` (AC-40.2).

**Nhật ký (BR-6): hiện có và thiếu**
- **Hiện có:**
  - `AuditLog.save` (khi đã có pk) và `delete` ném RuntimeError; `AuditQuerySet.update/delete` ném RuntimeError; `AuditLogAdmin` không cho thêm, sửa, xoá. Bài: `core/tests/test_audit.py`.
  - `GridCellHistory` (`HistoryQuerySet.update/delete`): `test_master_nine.py::test_history_cursor_is_bounded_and_append_only`.
  - `ReportRevision` (RevisionQuerySet), `DailyReport.save`, `Order.save` chặn sửa.
  - `Recognition`/`StarAward` không có view sửa hay xoá.
- **Thiếu:**
  - `GridCellHistory` ở mức đối tượng: `save()` bản ghi cũ, `delete()`, `bulk_create(update_conflicts=True)` (`crm/models.py` dòng 44-77) chưa có bài.
  - Không ghi nhật ký: sửa qua Django admin (`UserProfileAdmin.save_model`, đổi mật khẩu qua `/quan-tri/auth/user/<id>/password/`), `PasswordChangeView.form_valid`.
  - `bo-chi-tiet/` không ghi `GridCellHistory`.

**Dữ liệu nhạy cảm trong log: hiện có và thiếu**
- **Hiện có:**
  - `core/audit._scrub` (SENSITIVE_KEYS, so theo ranh giới từ).
  - Mật khẩu tạm không lưu vào session, nhật ký hay URL (`org/tests/test_temporary_password.py`).
  - Sao lưu truyền mật khẩu qua PGPASSWORD.
  - Ghi chú tài nguyên không chép vào nhật ký (AC-16.3).
  - Nhật ký ghi nhận dùng mã nhân sự, không dùng tên.
- **Thiếu:**
  - `note_failed_login` lưu nguyên chuỗi người gõ vào `actor_label`, kể cả mật khẩu gõ nhầm ô.
  - `find_user('')` gán LOGIN_FAILED cho một người có email rỗng.
  - Nhật ký "Cập nhật khách {phone} … email" khi lên đơn (`order_service.create_order`).
  - `_client_ip` với X-Forwarded-For không phải IP thì ra 500.
  - `RequestMetricsMiddleware` (bật trên production: `CRM_REQUEST_METRICS: '1'`, `deploy/production/compose.yml` dòng 14) chưa có bài khẳng định không ghi query, SQL hay cookie.
  - `_scrub` thay **cả dòng** khi tiêu đề việc có từ "mật khẩu" hay "token", làm mất thông tin mà AC-14.5 đòi.
  - Tên mục tài nguyên không đi qua `check_text`.

**Ca cần thêm**

| Mã | Ca kiểm | Góc nhìn | Loại | Mức tự động | Ưu tiên | Khẳng định chính | Tham chiếu |
|---|---|---|---|---|---|---|---|
| C37-01 | Trước khi phát hành, kiểm trên bản sao DB production bằng đúng role ứng dụng dùng trên VPS: `SELECT extname FROM pg_extension WHERE extname='pg_trgm'`. Nếu chưa có extension: thử `migrate core 0002` bằng role đó. Ghi rõ ai tạo extension (superuser tạo trước hay role tự tạo) | QA | Migration / vận hành | Thủ công | P0 | `migrate` không dừng ở `core 0002_pg_trgm`. Có ghi lại cách tạo extension trong `docs/kiem-chung-*`. Không chạy ngược `0002` trên DB thật. (`test_chuyen_doi.py` đã chạy trong CI nên không cần ca riêng) | `core/migrations/0002_pg_trgm.py`, `.github/workflows/ci.yml` dòng 58-60, CLAUDE.md "Định nghĩa hoàn thành" điều 3 |
| C37-02 | `reports 0006` với 1.201 dòng MKT, một số đã xoá mềm | QA | Migration | Tự động | P2 | Mọi dòng thành VND, số giữ nguyên; chạy ngược lấy lại theo Thị trường | ADR-047, AC-47.3 |
| C37-03 | Round-trip có dữ liệu cho `orders 0002`, `orders 0005`, `crm 0005` | QA | Migration | Tự động | P2 | Xuôi, ngược, xuôi lại không mất hay đổi giá trị | BR-4 |
| C37-04 | Diễn tập `migrate` trên bản sao DB production ở Staging, kèm `kiem_tra_du_lieu` trước và sau, đo thời gian 0016/0017, chạy câu SQL đếm NFD trước và sau | QA | Vận hành | Thủ công | P0 | Mã thoát 0 ở cả hai lần; số dòng NFD không tăng; thời gian được ghi vào `docs/kiem-chung-*` | AC-36.14–36.16, TL-79 |
| C37-05 | Lệnh rà bất biến mở rộng (bảng bất biến phía trên), chỉ đọc, thoát mã 1 khi lệch | QA | Toàn vẹn | Tự động | P1 | Mỗi bất biến có một bài dựng ca lệch rồi bắt được. Bất biến NFD dùng nguyên câu `NOT (data::text IS NFC NORMALIZED)` | BR-8, ADR-037, K30, TL-79 |
| C37-06 | Tạo lại bộ phận hoặc team trùng tên với bản đã xoá mềm | Người dùng | HTTP | Tự động | P1 | Không 500; có lời báo, hoặc cho dùng lại tên (cần chốt) | BR-4, NFR-6, AC-2.1 |
| C37-07 | Thu lại một quyền đã thu; danh sách quyền sau khi thu | QA | HTTP | Tự động | P0 | 404; `deleted_at`/`deleted_by` giữ giá trị của lần đầu; không thêm dòng PERMISSION; danh sách chỉ có quyền còn hiệu lực | BR-4, BR-6, FR-8.4 |
| C37-08 | Xoá team qua `/quan-tri/org/team/` | QA | Tích hợp admin | Tự động | P2 | Có `deleted_by` và AuditLog DELETE. Hiện đang đỏ | BR-4, BR-5 |
| C37-09 | Bỏ rồi khôi phục: báo cáo MKT 2 lần nộp, dòng vận đơn có đơn gốc, chứng từ có Ref đã bị dùng lại | Người dùng | Tích hợp | Tự động | P1 | Số liệu tổng hợp trở về như trước; đơn sống lại; khôi phục chứng từ trùng Ref trả 400 | AC-4.10, AC-6.12, AC-26.3 |
| C37-10 | Không có đường xoá cứng nghiệp vụ: duyệt mọi URL POST, đếm `Model.all_objects` trước và sau | QA | Toàn vẹn | Tự động | P1 | Không bảng nghiệp vụ nào giảm số dòng `all_objects` | BR-4 |
| C37-11 | `GridCellHistory`: `h.save()`, `h.delete()`, `bulk_create(update_conflicts=True)`; xoá cứng DataRecord | QA | Đơn vị | Tự động | P2 | Ba thao tác đầu ném RuntimeError; xoá cứng DataRecord bị PROTECT | BR-6, AC-21.10 |
| C37-12 | `AuditLog`, `ReportRevision`: `update()`/`delete()` theo lô, `save()` bản ghi cũ, thao tác qua admin | QA | Đơn vị + admin | Tự động | P2 | Mọi đường đều bị chặn | BR-6, AC-9.3 |
| C37-13 | Sửa qua Django admin (rank, mật khẩu người khác); `POST /doi-mat-khau/` | QA | Tích hợp | Tự động | P2 | Có dòng nhật ký, không chứa mật khẩu. Hiện đang đỏ | BR-5, điều cấm 6 |
| C37-14 | Gõ mật khẩu vào ô tên đăng nhập; POST thiếu `username` | Người dùng | Đơn vị nhật ký | Tự động | P1 | `actor_label` bị che khi không khớp tài khoản nào; LOGIN_FAILED không gắn với người có email rỗng | điều cấm 6, BR-6 |
| C37-15 | Lên đơn lần 2 cùng SĐT, tên khác, email mới | QA | Tích hợp | Tự động | P1 | Nhật ký cập nhật khách không chứa SĐT hay email (hoặc chủ dự án chốt và sửa docstring bài) | AC-9.2, AC-18.3 |
| C37-16 | X-Forwarded-For là `'khong-phai-ip'`, `'1.2.3.4:5678'`, chuỗi 300 ký tự | QA | Fuzz header | Tự động | P1 | Không 500; `ip_address` là None hoặc IP hợp lệ | NFR-6 |
| C37-17 | `RequestMetricsMiddleware` bật: request ID xấu, query `?tim=khách`, view ném lỗi | QA | Đơn vị | Tự động | P2 | Log không có query hay SQL; request ID xấu được thay bằng uuid; status 500 được ghi; `ensure_connection` được trả về hàm gốc | ADR-024 |
| C37-18 | Sửa việc tên "Đổi mật khẩu email"; tạo mục tài nguyên "Token QC" | Người dùng | Tích hợp nhật ký | Tự động | P2 | Nhật ký vẫn ghi trường nào đổi, chỉ che phần nhạy cảm; tên mục qua `check_text` | AC-14.5, AC-16.3, BR-5 |
| C37-19 | `localStorage` sau khi gõ "KH-XYZ-123" vào ô Tên khách | QA | e2e | Tự động | P2 | `JSON.stringify(localStorage)` không chứa chuỗi đó | ADR-021 |
| C37-20 | Sao lưu rồi khôi phục trên máy sạch, có 2 tài liệu đã tải lên | Người dùng | Vận hành | Bán tự động | P0 | Tải về được đúng nội dung. Hiện đang đỏ (K30) | FR-9.5, K30, AC-12.5 |
