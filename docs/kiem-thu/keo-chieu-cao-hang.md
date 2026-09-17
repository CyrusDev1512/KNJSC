# Kiểm chứng kéo chiều cao hàng — 10.09.2026

Chỉ Vận đơn mới, nhánh `codex/sua-feedback`. Đã triển khai theo kế hoạch duyệt:
28–400 px, xuống dòng khi hàng cao, ghi nhớ theo user/bảng/ID trong localStorage.
Không thêm API, migration hoặc dependency; không đổi dữ liệu/định dạng Excel.

## Kết quả

- Hồi quy Chrome ban đầu đỏ vì chưa có tay kéo. Bản cuối: **1 passed trong
  78,31 giây**, script Node PASS; kiểm chuột, cảm ứng qua CDP, 1440/1280/390 px,
  zoom 125%, hủy kéo, bàn phím, wrap/reader/editor, copy/dán/Delete/Undo,
  lọc/sắp xếp theo ID, polling, khối rời cache, đổi tài khoản và lỗi localStorage.
- Nhóm `crm/tests/test_master_grid.py core/tests/test_giao_dien.py tests/test_truy_vet.py`:
  **612 passed trong 13,50 giây** trên DB test riêng.
- `node scripts/kiem-thu-master-row-geometry.cjs`: PASS; đối chiếu 1.000 lần cập nhật
  với tổng tuyến tính, biên hàng và cấu trúc thưa cho 300.000 dòng.
- Kiểm local bằng tài khoản `quantri`: bấm đúp/F2, kéo cột, kéo hàng 28→108 px;
  không lỗi JavaScript. Chỉ mở/hủy ô nhập và đổi tùy chọn trong phiên browser test,
  không ghi vào 20 khách mẫu.

## Đo trình duyệt với dữ liệu lớn

Chrome headless Windows, viewport 1440×900; Django/Gunicorn 3 worker × 4 thread,
PostgreSQL test, cùng cấu hình máy trong báo cáo master. Fixture tổng hợp 25 cột,
mỗi dòng một chi tiết sản phẩm; hai mức 100.000 và 300.000 dòng. Một phiên trình
duyệt, không chạy tải HTTP nhiều người. Các container khác vẫn chạy trên máy.

Thời gian đo từ pointermove chuột thật do Playwright phát đến ba animation frame;
30 mẫu/mức, p95 nearest rank. Không phải INP thực địa hoặc kiểm endurance.
Thêm hàng cao ở nhiều khối, cuộn 35 lượt gồm cuối bảng rồi trở về đầu.

| Dòng | p95 kéo hàng | Mẫu | Cache tối đa | Ô DOM tối đa | Heap sau GC, lượt 16–34 |
|---:|---:|---:|---:|---:|---:|
| 100,000 | 33.6 ms | 30 | 10 | 470 | 5.41–5.48 MiB |
| 300,000 | 33.5 ms | 30 | 10 | 470 | 5.42–5.48 MiB |

Cả hai lượt đạt mục tiêu p95 ≤100 ms, không lỗi JS, không gọi `luu-json` khi kéo
hàng. 37 request dữ liệu mỗi mức cho toàn bộ quá trình mở/cuộn; không tải toàn bảng
để khôi phục chiều cao. Fixture capacity hoàn tất **1 passed trong 82,99 giây**.

## Giới hạn và bằng chứng

Chiều cao hàng chưa tải được ước lượng bằng 28 px; khôi phục khi khối chứa ID đó
xuất hiện, bù vị trí cuộn quanh hàng neo. Tùy chọn chỉ ở trình duyệt/máy hiện tại.
Đã kiểm cảm ứng giả lập Chrome, chưa kiểm thiết bị di động vật lý; dữ liệu lớn
là tổng hợp, chưa chứng minh mọi phân phối dữ liệu hoặc phiên làm việc nhiều giờ.

Lệnh chạy tại [kế hoạch kiểm thử](../06-ke-hoach-kiem-thu.md); hợp đồng tại
[ADR-021](../quyet-dinh/021-luoi-master-va-thong-ke-crm.md).
Raw JSON, ảnh và diff local: `.agents/design-state/review/master/row-height-*`.
Không commit/push. Không sử dụng các số renderer cũ thay số đo của bản này.
