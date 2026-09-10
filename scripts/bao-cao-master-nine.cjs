/* Xuất bằng chứng gọn để tài liệu có thể đi cùng repository. Không mang session. */
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..'),source=path.join(root,'.agents/design-state/review/master-nine-capacity');
const summary=JSON.parse(fs.readFileSync(path.join(source,'summary.json')));
const out=path.join(root,'docs/kiem-thu/master-nine-2026-09-10');fs.mkdirSync(out,{recursive:true});
const n=value=>Number(value).toLocaleString('vi-VN',{maximumFractionDigits:2});
const lines=['# Số đo Vận đơn mới — 10.09.2026','','Được tạo từ artifact đã kết thúc. File này không tự xác nhận toàn bộ nghiệm thu.',
  'HTTP bỏ 60 giây làm nóng; percentile nearest rank, đơn vị ms. 409 dự kiến được đếm riêng; bộ đếm này có thể gồm cả làm nóng. Không cộng chúng lần hai vào request/giây.',
  'Baseline có nhiễu từ công việc khác trên cùng máy; không diễn giải thành tỷ lệ tăng tốc tuyệt đối.','','| Lượt | Request | Request/s | Lỗi | 409 dự kiến |','|---|---:|---:|---:|---:|'];
for(const run of summary.http)lines.push(`| ${run.name} | ${n(run.requests)} | ${n(run.rps)} | ${run.errors} (${n(run.errors/run.requests*100)}%) | ${run.conflicts} |`);
if(summary.runState)lines.push('',`Chạy bền: ${summary.runState.note}`);
lines.push('','| Lượt | Endpoint | Mẫu | p50 | p95 | p99 | Lỗi |','|---|---|---:|---:|---:|---:|---:|');
for(const run of summary.http)for(const [key,s] of Object.entries(run.endpoints))lines.push(`| ${run.name} | ${key} | ${n(s.n)} | ${n(s.p50)} | ${n(s.p95)} | ${n(s.p99)} | ${s.errors} |`);
lines.push('','## Tài nguyên','','Mẫu mỗi khoảng 30 giây trong cửa sổ đo; không thể hiện mọi đỉnh tức thời. CPU theo docker stats: 100% tương ứng khoảng một lõi. Container kiểm tải gồm cả Gunicorn và Locust; PostgreSQL dùng chung với dịch vụ local khác.',
  '','| Lượt | Container | Mẫu | CPU p50/p95 (%) | RAM cao nhất (MiB) |','|---|---|---:|---:|---:|');
for(const run of summary.http)for(const [name,r] of Object.entries(run.resources||{}))lines.push(`| ${run.name} | ${name} | ${r.samples} | ${n(r.cpuPercent.p50)} / ${n(r.cpuPercent.p95)} | ${n(r.maxMemoryBytes/1024**2)} |`);
lines.push('','## Chrome','','Các phương pháp đo được ghi trong JSON; click/pointer tổng hợp và thời gian tới hai frame không phải INP hoặc bộ gõ thực tế.',
  '','| Lượt | Thao tác | Mẫu | p50 | p95 | p99 |','|---|---|---:|---:|---:|---:|');
for(const b of summary.browser)for(const [name,s] of Object.entries(b.operations||{}))lines.push(`| ${b.name} | ${name} | ${s.samples} | ${n(s.p50)} | ${n(s.p95)} | ${n(s.p99)} |`);
lines.push('','Xem [JSON đầy đủ](summary.json) để đối chiếu cache, DOM, heap, dung lượng lịch sử và trạng thái lượt kéo dài.');
fs.writeFileSync(path.join(out,'performance.md'),lines.join('\n')+'\n');
fs.writeFileSync(path.join(out,'summary.json'),JSON.stringify(summary,null,2));
for(const name of ['ui-result.json','grid-1440.png','grid-1280.png','grid-390.png','zoom125.png','history.png','row-selected.png']){
  const file=path.join(root,'.agents/design-state/review/master-nine',name);if(fs.existsSync(file))fs.copyFileSync(file,path.join(out,name));
}
console.log(out);
