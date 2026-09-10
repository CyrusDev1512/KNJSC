# Số đo Vận đơn mới — 10.09.2026

Được tạo từ artifact đã kết thúc. File này không tự xác nhận toàn bộ nghiệm thu.
HTTP bỏ 60 giây làm nóng; percentile nearest rank, đơn vị ms. 409 dự kiến được đếm riêng; bộ đếm này có thể gồm cả làm nóng. Không cộng chúng lần hai vào request/giây.
Baseline có nhiễu từ công việc khác trên cùng máy; không diễn giải thành tỷ lệ tăng tốc tuyệt đối.

| Lượt | Request | Request/s | Lỗi | 409 dự kiến |
|---|---:|---:|---:|---:|
| before-100000-10 | 1.938 | 6,47 | 1 (0,05%) | 0 |
| before-100000-20 | 3.764 | 12,56 | 3 (0,08%) | 1 |
| before-300000-10 | 1.560 | 5,21 | 0 (0%) | 0 |
| before-300000-20 | 2.513 | 8,39 | 2 (0,08%) | 3 |
| after-100000-10 | 2.052 | 6,85 | 0 (0%) | 0 |
| after-100000-20 | 4.094 | 13,66 | 2 (0,05%) | 3 |
| after-300000-10 | 1.918 | 6,4 | 2 (0,1%) | 0 |
| after-300000-20 | 3.751 | 12,52 | 2 (0,05%) | 3 |

Chạy bền: Dừng theo yêu cầu chủ dự án, mẫu Chrome cuối ở phút 15. Chưa đủ 30 phút; không có tổng HTTP chạy dài. Chạy lại trong phiên sau.

| Lượt | Endpoint | Mẫu | p50 | p95 | p99 | Lỗi |
|---|---|---:|---:|---:|---:|---:|
| before-100000-10 | read:block | 814 | 166,27 | 484,77 | 556,06 | 1 |
| before-100000-10 | read:filter | 174 | 184,62 | 499,32 | 548,83 | 0 |
| before-100000-10 | poll | 272 | 70,38 | 347,03 | 412,66 | 0 |
| before-100000-10 | read:write-target | 339 | 178,21 | 441,65 | 490,96 | 0 |
| before-100000-10 | write:cell | 339 | 50,54 | 314,71 | 357,16 | 0 |
| before-100000-20 | read:block | 1.615 | 200 | 583,56 | 707,51 | 0 |
| before-100000-20 | poll | 548 | 84 | 412,29 | 519,58 | 0 |
| before-100000-20 | read:write-target | 637 | 211,46 | 540,48 | 697,17 | 2 |
| before-100000-20 | read:filter | 329 | 214,29 | 547,23 | 684,17 | 1 |
| before-100000-20 | write:cell | 635 | 56,15 | 368,66 | 476,33 | 0 |
| before-300000-10 | read:write-target | 267 | 652,69 | 1.774,83 | 2.066,13 | 0 |
| before-300000-10 | write:cell | 267 | 68,03 | 1.108,84 | 1.277,9 | 0 |
| before-300000-10 | read:block | 650 | 584,68 | 1.872,15 | 2.113,2 | 0 |
| before-300000-10 | poll | 255 | 251,54 | 1.411,6 | 1.498,46 | 0 |
| before-300000-10 | read:filter | 121 | 501,93 | 1.802,65 | 2.044,07 | 0 |
| before-300000-20 | read:block | 1.033 | 1.000,92 | 2.891,28 | 3.751,78 | 2 |
| before-300000-20 | poll | 468 | 542,46 | 2.488,08 | 3.046,63 | 0 |
| before-300000-20 | read:write-target | 400 | 1.064,87 | 2.944,88 | 3.627,59 | 0 |
| before-300000-20 | write:cell | 400 | 163,25 | 1.804,09 | 2.471,33 | 0 |
| before-300000-20 | read:filter | 212 | 983,81 | 2.873,08 | 3.382,47 | 0 |
| after-100000-10 | read:block | 871 | 84,27 | 163,87 | 214,8 | 0 |
| after-100000-10 | poll | 290 | 56,57 | 83,61 | 103,51 | 0 |
| after-100000-10 | read:write-target | 358 | 45,62 | 88,76 | 117,04 | 0 |
| after-100000-10 | write:cell | 358 | 42,91 | 86,18 | 102,35 | 0 |
| after-100000-10 | read:filter | 175 | 271,86 | 386,71 | 436,46 | 0 |
| after-100000-20 | read:filter | 346 | 264,98 | 365,28 | 397,68 | 0 |
| after-100000-20 | read:block | 1.800 | 86,93 | 167,16 | 201,77 | 2 |
| after-100000-20 | read:write-target | 684 | 44 | 79,78 | 109,75 | 0 |
| after-100000-20 | write:cell | 684 | 40,52 | 96,82 | 116,86 | 0 |
| after-100000-20 | poll | 580 | 56,46 | 89,14 | 124,9 | 0 |
| after-300000-10 | read:write-target | 326 | 74,74 | 222,74 | 277,4 | 0 |
| after-300000-10 | read:filter | 163 | 843,16 | 1.134,89 | 1.253,8 | 0 |
| after-300000-10 | read:block | 824 | 150,13 | 540,48 | 653,06 | 2 |
| after-300000-10 | write:cell | 326 | 58,57 | 106,47 | 120,85 | 0 |
| after-300000-10 | poll | 279 | 179,86 | 267,32 | 309,44 | 0 |
| after-300000-20 | read:block | 1.525 | 183,8 | 663,7 | 898,15 | 1 |
| after-300000-20 | read:write-target | 668 | 88,54 | 317,96 | 480,28 | 0 |
| after-300000-20 | write:cell | 668 | 51,48 | 123,73 | 275,05 | 0 |
| after-300000-20 | poll | 552 | 200,87 | 358,65 | 496,95 | 0 |
| after-300000-20 | read:filter | 338 | 895,67 | 1.340,38 | 1.501,56 | 1 |

## Tài nguyên

Mẫu mỗi khoảng 30 giây trong cửa sổ đo; không thể hiện mọi đỉnh tức thời. CPU theo docker stats: 100% tương ứng khoảng một lõi. Container kiểm tải gồm cả Gunicorn và Locust; PostgreSQL dùng chung với dịch vụ local khác.

| Lượt | Container | Mẫu | CPU p50/p95 (%) | RAM cao nhất (MiB) |
|---|---|---:|---:|---:|
| before-100000-20 | knjsc-nine-capacity | 1 | 55,26 / 55,26 | 393,7 |
| before-100000-20 | knjsc-db-1 | 1 | 156,4 / 156,4 | 609,5 |
| before-300000-10 | knjsc-nine-capacity | 10 | 18,35 / 34,07 | 398,3 |
| before-300000-10 | knjsc-db-1 | 10 | 257,14 / 428,19 | 999,5 |
| before-300000-20 | knjsc-nine-capacity | 9 | 35,52 / 60,88 | 398,9 |
| before-300000-20 | knjsc-db-1 | 9 | 537,75 / 737,17 | 1.014 |
| after-100000-10 | knjsc-nine-capacity | 9 | 22,28 / 30,37 | 384 |
| after-100000-10 | knjsc-db-1 | 9 | 42,7 / 49,28 | 1.102,85 |
| after-100000-20 | knjsc-nine-capacity | 10 | 33,37 / 56,29 | 392 |
| after-100000-20 | knjsc-db-1 | 10 | 66,27 / 110,25 | 1.111,04 |
| after-300000-10 | knjsc-nine-capacity | 10 | 11,65 / 29,15 | 396,8 |
| after-300000-10 | knjsc-db-1 | 10 | 53,06 / 152,95 | 1.486,85 |
| after-300000-20 | knjsc-nine-capacity | 9 | 39,45 / 71,61 | 395,8 |
| after-300000-20 | knjsc-db-1 | 9 | 350,99 / 632,61 | 1.504,26 |

## Chrome

Các phương pháp đo được ghi trong JSON; click/pointer tổng hợp và thời gian tới hai frame không phải INP hoặc bộ gõ thực tế.

| Lượt | Thao tác | Mẫu | p50 | p95 | p99 |
|---|---|---:|---:|---:|---:|
| before-100000-browser.json | select | 100 | 31,8 | 32,2 | 41,6 |
| before-100000-browser.json | column | 100 | 48,5 | 65,2 | 91,6 |
| before-100000-browser.json | row | 100 | 48,5 | 48,9 | 50,1 |
| before-300000-browser.json | select | 100 | 31,7 | 32,1 | 32,3 |
| before-300000-browser.json | column | 100 | 48,4 | 64,3 | 65,3 |
| before-300000-browser.json | row | 100 | 48,4 | 48,9 | 50,5 |
| after-100000-browser.json | select | 100 | 31,8 | 32,2 | 43,7 |
| after-100000-browser.json | openAndTypeWhileSaving | 100 | 30 | 31 | 56 |
| after-100000-browser.json | reader | 100 | 29,5 | 31,1 | 32,4 |
| after-100000-browser.json | column | 100 | 47,9 | 49,2 | 51,2 |
| after-100000-browser.json | row | 100 | 48,6 | 49,2 | 53,2 |
| after-300000-browser.json | select | 100 | 31,8 | 32,4 | 40,6 |
| after-300000-browser.json | openAndTypeWhileSaving | 100 | 29 | 31 | 48 |
| after-300000-browser.json | reader | 100 | 28,6 | 30,1 | 42,3 |
| after-300000-browser.json | column | 100 | 47,6 | 49 | 49,3 |
| after-300000-browser.json | row | 100 | 48,5 | 48,9 | 57,1 |

Xem [JSON đầy đủ](summary.json) để đối chiếu cache, DOM, heap, dung lượng lịch sử và trạng thái lượt kéo dài.
