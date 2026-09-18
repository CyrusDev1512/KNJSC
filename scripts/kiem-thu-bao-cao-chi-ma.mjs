// Đo Báo cáo tổng hợp trên KN ERP local (8020) bằng Chrome DevTools Protocol thuần — Node ≥ 22 có
// fetch + WebSocket sẵn, không cần cài Playwright; chỉ cần Chromium của Playwright đã có trên máy
// (%LOCALAPPDATA%\ms-playwright\chromium-<bản>\chrome-win64\chrome.exe, đổi bằng KN_CHROME).
// Chạy: node scripts/kiem-thu-bao-cao-chi-ma.mjs [thư mục ảnh, mặc định storage/e2e]
// In JSON: ô Nhân sự chỉ mã, ô chọn vẫn "MÃ · Họ tên", khung bảng ở Toàn màn hình nằm trong viewport.
import { spawn } from "node:child_process";
import { writeFileSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const CHROME = process.env.KN_CHROME || process.env.LOCALAPPDATA + "/ms-playwright/chromium-1234/chrome-win64/chrome.exe";
const BASE = process.env.KN_ERP_BASE || "http://127.0.0.1:8020";
const OUT = process.argv[2] || "storage/e2e";
const PORT = 9333;
mkdirSync(OUT, { recursive: true });

const chrome = spawn(CHROME, [
  `--remote-debugging-port=${PORT}`, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
  `--user-data-dir=${join(tmpdir(), "kn-cdp-profile-" + Date.now())}`, "--window-size=1440,900", "about:blank",
], { stdio: ["ignore", "ignore", "ignore"] });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws, id = 0; const pending = new Map(); const events = [];
async function connect() {
  for (let i = 0; i < 120; i++) {
    try {
      const list = await fetch(`http://127.0.0.1:${PORT}/json`).then((r) => r.json());
      const page = list.find((t) => t.type === "page");
      if (page) { ws = new WebSocket(page.webSocketDebuggerUrl); break; }
    } catch { }
    await sleep(250);
  }
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } else events.push(d); };
}
function send(method, params = {}) {
  return new Promise((res, rej) => { const i = ++id; pending.set(i, (d) => d.error ? rej(new Error(method + ": " + JSON.stringify(d.error))) : res(d.result)); ws.send(JSON.stringify({ id: i, method, params })); });
}
async function evaluate(expr) {
  const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
  return r.result.value;
}
async function goto(url) {
  await send("Page.navigate", { url });
  for (let i = 0; i < 80; i++) { await sleep(150); if (await evaluate("document.readyState") === "complete" && await evaluate("location.href") !== "about:blank") break; }
  await sleep(300);
}
async function viewport(w, h) { await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: false }); await sleep(250); }
async function shot(name) { const r = await send("Page.captureScreenshot", { format: "png" }); writeFileSync(join(OUT, name + ".png"), Buffer.from(r.data, "base64")); console.log("ảnh", join(OUT, name + ".png")); }

const KET_QUA = {};
try {
  await connect();
  await send("Page.enable"); await send("Runtime.enable");
  await viewport(1440, 900);
  await goto(`${BASE}/dang-nhap/`);
  const TK = JSON.stringify(process.env.KN_USER || "quantri"), MK = JSON.stringify(process.env.KN_PASSWORD || "matkhaucuatoi");
  await evaluate(`(()=>{const f=document.querySelector('form');f.querySelector('[name=username]').value=${TK};f.querySelector('[name=password]').value=${MK};f.querySelector('button[type=submit]').click();return 1})()`);
  for (let i = 0; i < 40; i++) { await sleep(250); if (!(await evaluate("location.pathname")).includes("dang-nhap")) break; }
  const url = `${BASE}/bao-cao/tong-hop/?nguon=bao_cao_mkt&nhom=day&tu=2026-09-01&den=2026-09-18`;
  await goto(url);
  KET_QUA.trang = await evaluate("location.pathname+location.search");
  KET_QUA.o_nhan_su = await evaluate(`[...document.querySelectorAll('tbody tr:not(.report-total) .id-nhan-su')].map(e=>e.textContent.trim())`);
  KET_QUA.o_chon = await evaluate(`[...document.querySelectorAll('#report-person option')].map(o=>o.textContent.trim())`);
  KET_QUA.rong_cot_nhan_su = await evaluate(`Math.round(document.querySelector('thead .id-nhan-su').getBoundingClientRect().width)`);
  KET_QUA.cao_dong = await evaluate(`Math.round(document.querySelector('tbody tr:not(.report-total)').getBoundingClientRect().height)`);
  KET_QUA.tran_ngang_trang = await evaluate(`document.documentElement.scrollWidth>document.documentElement.clientWidth`);
  await shot("bao-cao-chi-ma-1440-thuong");
  // Toàn màn hình ở 1440×900
  await evaluate(`document.getElementById('report-toggle-focus').click();1`);
  await sleep(400);
  const doKhung = `(()=>{const s=document.querySelector('.report-table-scroll'),p=document.querySelector('.report-results>.phan-trang'),r=s.getBoundingClientRect();
    return {focus:document.documentElement.classList.contains('sp-report-focus'),day_khung:Math.round(r.bottom),cao_cua_so:innerHeight,cuon_ngang:s.scrollWidth>s.clientWidth,
    cuon_doc:s.scrollHeight>s.clientHeight,day_phan_trang:p?Math.round(p.getBoundingClientRect().bottom):null,rong_bang:s.scrollWidth,rong_khung:s.clientWidth}})()`;
  KET_QUA.toan_man_hinh_900 = await evaluate(doKhung);
  await shot("bao-cao-chi-ma-1440-toan-man-hinh");
  // Cửa sổ thấp hơn bảng: khung phải co lại, thanh kéo ngang và phân trang vẫn trong viewport
  await viewport(1440, 300);
  KET_QUA.toan_man_hinh_300 = await evaluate(doKhung);
  await shot("bao-cao-chi-ma-1440x300-toan-man-hinh");
  // Nửa màn hình như ảnh chủ dự án (960 rộng)
  await viewport(960, 1000);
  KET_QUA.toan_man_hinh_960 = await evaluate(doKhung);
  await shot("bao-cao-chi-ma-960-toan-man-hinh");
  KET_QUA.loi_js = events.filter((e) => e.method === "Runtime.exceptionThrown").length;
} catch (e) { KET_QUA.loi = String(e); }
finally { try { ws?.close(); } catch { } chrome.kill(); }
console.log(JSON.stringify(KET_QUA, null, 1));
