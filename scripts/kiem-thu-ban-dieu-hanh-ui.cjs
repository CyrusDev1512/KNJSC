/* Kiểm tra đọc-only Bàn điều hành trên dịch vụ KN CRM đang chạy local. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const base = process.env.KN_EXECUTIVE_BASE || "http://127.0.0.1:8021";
const username = process.env.KN_EXECUTIVE_USER || "quantri";
const password = process.env.KN_EXECUTIVE_PASSWORD || "matkhaucuatoi";
const output = path.resolve(__dirname, "../storage/e2e/executive-statistics");

async function login(page) {
  await page.goto(`${base}/dang-nhap/`);
  await page.locator("[name=username]").fill(username);
  await page.locator("[name=password]").fill(password);
  await Promise.all([
    page.waitForURL((url) => !url.pathname.includes("dang-nhap")),
    page.locator("button[type=submit]").click(),
  ]);
}

async function inspect(browser, sample) {
  const context = await browser.newContext({
    viewport: sample.viewport,
    locale: "vi-VN",
    colorScheme: sample.colorScheme,
    reducedMotion: sample.reducedMotion || "no-preference",
    isMobile: sample.mobile || false,
    hasTouch: sample.mobile || false,
  });
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  await login(page);
  await page.evaluate((theme) => localStorage.setItem("knjsc-nen", theme), sample.colorScheme);
  await page.goto(`${base}/thong-ke/`);
  await page.locator("main.exec-page").waitFor();
  if (sample.zoom) {
    await page.evaluate((zoom) => {
      document.documentElement.style.zoom = zoom;
    }, sample.zoom);
  }
  const facts = await page.evaluate(() => {
    const svgs = [...document.querySelectorAll(".exec-chart svg")];
    const chartArticles = [...document.querySelectorAll(".exec-chart")];
    const chartDetails = [...document.querySelectorAll(".exec-chart details")];
    return {
      title: document.querySelector("h1")?.textContent.trim(),
      theme: document.documentElement.dataset.theme,
      insights: document.querySelectorAll(".exec-briefing li").length,
      charts: chartArticles.length,
      svgs: svgs.length,
      titledCharts: svgs.filter((svg) => svg.querySelector(":scope > title")).length,
      focusableCharts: svgs.filter((svg) => svg.tabIndex === 0).length,
      alternativeTables: chartDetails.filter((item) => item.querySelector("table")).length,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      motion: getComputedStyle(document.querySelector(".exec-line-wrap polyline") || document.body).transitionDuration,
    };
  });
  assert.match(facts.title || "", /Bàn điều hành/);
  assert.equal(facts.theme, sample.colorScheme);
  assert(facts.insights <= 3, `Có ${facts.insights} insight, vượt giới hạn 3`);
  assert.equal(facts.titledCharts, facts.svgs, "SVG thiếu title");
  assert.equal(facts.focusableCharts, facts.svgs, "SVG chưa nhận focus bàn phím");
  assert.equal(facts.alternativeTables, facts.charts, "Biểu đồ thiếu bảng thay thế");
  assert(facts.overflow <= 1, `Trang tràn ngang ${facts.overflow}px`);
  if (sample.reducedMotion === "reduce") {
    assert(["0s", "0ms"].includes(facts.motion), "Reduced motion vẫn còn transition");
  }
  await page.locator("select[name=nguon]").focus();
  await page.keyboard.press("Tab");
  assert(await page.evaluate(() => document.activeElement?.matches("input[name=tu]")));
  await page.screenshot({ path: path.join(output, `${sample.name}.png`), fullPage: true });
  if (sample.name === "light-1440") {
    await page.goto(`${base}/thong-ke/?nguon=van_don_moi&tu=2026-09-01&den=2026-09-11`);
    await page.locator(".exec-kpis").waitFor();
    const direct = await page.evaluate(() => {
      const insightLinks = [...document.querySelectorAll(".exec-briefing a")];
      return {
        charts: document.querySelectorAll(".exec-chart").length,
        kpis: [...document.querySelectorAll(".exec-kpis span")].map((node) => node.textContent.trim()),
        datedInsightLinks: insightLinks.filter((link) => {
          const url = new URL(link.href);
          return [...url.searchParams.keys()].some((key) => key.endsWith("__lon_bang"))
            && [...url.searchParams.keys()].some((key) => key.endsWith("__nho_bang"));
        }).length,
        stateInsightLinks: insightLinks.filter((link) => {
          const keys = [...new URL(link.href).searchParams.keys()];
          return keys.some((key) => key.includes("trang_thai_vc") || key.includes("trang_thai_tt"));
        }).length,
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      };
    });
    assert(direct.charts >= 5, "Góc Vận đơn thiếu bộ biểu đồ chuyên sâu");
    assert(direct.kpis.some((label) => label.startsWith("Giá trị ·")));
    assert(direct.kpis.some((label) => label.startsWith("Đã thanh toán ·")));
    assert(direct.datedInsightLinks >= 1, "Insight thiếu bộ lọc ngày");
    assert(direct.stateInsightLinks >= 1, "Insight trạng thái thiếu bộ lọc tương ứng");
    assert(direct.overflow <= 1, `Trang chuyên sâu tràn ngang ${direct.overflow}px`);
    facts.direct = direct;
    await page.screenshot({ path: path.join(output, "waybill-detail-1440.png"), fullPage: true });
  }
  await context.close();
  return { name: sample.name, ...facts, errors };
}

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  try {
    const samples = [
      { name: "light-1440", viewport: { width: 1440, height: 900 }, colorScheme: "light" },
      { name: "light-1280", viewport: { width: 1280, height: 800 }, colorScheme: "light" },
      { name: "light-390", viewport: { width: 390, height: 844 }, colorScheme: "light", mobile: true },
      { name: "dark-reduced-1440", viewport: { width: 1440, height: 900 }, colorScheme: "dark", reducedMotion: "reduce" },
      { name: "light-125pct", viewport: { width: 1280, height: 800 }, colorScheme: "light", zoom: "1.25" },
    ];
    const results = [];
    for (const sample of samples) results.push(await inspect(browser, sample));
    const errors = results.flatMap((result) => result.errors);
    assert.deepEqual(errors, [], `Console/page errors: ${errors.join(" | ")}`);
    process.stdout.write(`${JSON.stringify(results, null, 2)}\n`);
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
