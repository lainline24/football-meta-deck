// 덱 검증 루프: 모든 슬라이드를 렌더링해 스크린샷 + 자동 검사
// 사용: node scripts/verify.mjs <url> <screenshot_dir>
// 필요: puppeteer-core (PUPPETEER_DIR 환경변수로 node_modules 상위 폴더 지정 가능), 로컬 Chrome
import { createRequire } from "module";
import fs from "fs";
import path from "path";

const require = createRequire(process.env.PUPPETEER_DIR ? path.join(process.env.PUPPETEER_DIR, "x.js") : import.meta.url);
const puppeteer = require("puppeteer-core");
const URL = process.argv[2] || "http://localhost:8765/";
const OUT = process.argv[3] || "verify-shots";
const CHROME = process.env.CHROME || "C:/Program Files/Google/Chrome/Application/chrome.exe";
fs.mkdirSync(OUT, { recursive: true });

const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new", args: ["--autoplay-policy=no-user-gesture-required"] });
const page = await browser.newPage();
await page.setViewport({ width: 1600, height: 900 });
const problems = [];
page.on("console", m => { if (m.type() === "error") problems.push(`[console] ${m.text()}`); });
page.on("pageerror", e => problems.push(`[pageerror] ${e.message}`));
page.on("requestfailed", r => problems.push(`[requestfailed] ${r.url()} ${r.failure()?.errorText}`));
page.on("response", r => { if (r.status() >= 400) problems.push(`[http ${r.status()}] ${r.url()}`); });

await page.goto(URL, { waitUntil: "networkidle0", timeout: 60000 });
await page.waitForFunction(() => window.__deck && window.__deck.ready, { timeout: 20000 });
const count = await page.evaluate(() => window.__deck.count);

for (let i = 0; i < count; i++) {
  await page.evaluate(n => window.__deck.go(n), i);
  await new Promise(r => setTimeout(r, 3800)); // 진입 애니메이션 종료 대기
  // 영상이 있는 슬라이드는 재생이 끝난 마지막 장면까지 기다림 (최대 15초)
  await page.waitForFunction(() => [...document.querySelectorAll(".slide.active video")].every(v => v.ended), { timeout: 15000 }).catch(() => {});
  const res = await page.evaluate(() => {
    const issues = [];
    const stage = document.getElementById("stage").getBoundingClientRect();
    const s = document.querySelector(".slide.active");
    const vis = e => { const cs = getComputedStyle(e); return cs.display !== "none" && cs.visibility !== "hidden" && +cs.opacity > 0.05; };
    const label = e => (e.id ? "#" + e.id : e.tagName.toLowerCase() + (e.className && typeof e.className === "string" ? "." + e.className.split(" ")[0] : "")) +
      ` "${(e.textContent || "").trim().slice(0, 24)}"`;
    // 1) 캔버스 밖으로 넘친 요소
    s.querySelectorAll("*").forEach(e => {
      if (e.closest(".bgimg") || !vis(e)) return;
      const r = e.getBoundingClientRect(); if (!r.width || !r.height) return;
      if (r.left < stage.left - 2 || r.right > stage.right + 2 || r.top < stage.top - 2 || r.bottom > stage.bottom + 2)
        issues.push(`overflow ${label(e)} [${Math.round(r.left)},${Math.round(r.top)},${Math.round(r.right)},${Math.round(r.bottom)}]`);
    });
    // 2) 내용이 잘린 블록 (scroll > client)
    s.querySelectorAll("div,p,span,b,h1,h2").forEach(e => {
      if (!vis(e)) return; const cs = getComputedStyle(e);
      if (cs.overflow !== "visible" && (e.scrollWidth > e.clientWidth + 2 || e.scrollHeight > e.clientHeight + 2)) issues.push(`clipped ${label(e)}`);
    });
    // 3) 텍스트끼리 겹침 (텍스트를 직접 가진 리프 요소 기준)
    const leaves = [...s.querySelectorAll("*")].filter(e => vis(e) && !e.closest(".bgimg") &&
      [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()));
    const rects = leaves.map(e => [e, e.getBoundingClientRect()]);
    for (let a = 0; a < rects.length; a++) for (let b = a + 1; b < rects.length; b++) {
      const [ea, ra] = rects[a], [eb, rb] = rects[b];
      if (ea.contains(eb) || eb.contains(ea)) continue;
      const ox = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left), oy = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
      if (ox > 3 && oy > 3) issues.push(`text-overlap ${label(ea)} × ${label(eb)}`);
    }
    // 4) 이미지·영상 로드
    s.querySelectorAll("img").forEach(im => { if (!im.complete || !im.naturalWidth) issues.push(`img-not-loaded ${im.src}`); });
    s.querySelectorAll(".bgimg").forEach(b => { const u = getComputedStyle(b).backgroundImage; if (!u || u === "none") issues.push("bg-missing"); });
    s.querySelectorAll("video").forEach(v => { if (v.readyState < 2) issues.push(`video-not-ready ${v.src} rs=${v.readyState}`); if (v.paused && !v.ended) issues.push(`video-paused ${v.src}`); if (!v.ended) issues.push(`video-not-ended ${v.src}`); });
    return { id: s.id, title: s.dataset.title, issues };
  });
  const file = path.join(OUT, `slide-${String(i + 1).padStart(2, "0")}.png`);
  await page.screenshot({ path: file });
  console.log(`${String(i + 1).padStart(2)} ${res.title.padEnd(14)} ${res.issues.length ? "✗ " + res.issues.length + " issue(s)" : "✓"}`);
  res.issues.forEach(x => console.log("     - " + x));
}
console.log(problems.length ? `\n네트워크/콘솔 문제 ${problems.length}건:\n` + [...new Set(problems)].map(p => "  " + p).join("\n") : "\n네트워크/콘솔 문제 없음");
await browser.close();
