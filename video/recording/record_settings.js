// Records the real settings section of the local SpendGuard app (no PayPal involved).
const { chromium } = require("playwright");
const path = require("path");

const OUT = path.join(__dirname, "raw");

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
    recordVideo: { dir: OUT, size: { width: 1920, height: 1080 } },
  });
  // 200% zoom: the page lays out as a 960 px window, captured at full 1920x1080 resolution.
  await context.addInitScript(() => { document.addEventListener("DOMContentLoaded", () => { document.documentElement.style.zoom = "2"; }); });
  const page = await context.newPage();
  await page.goto("http://localhost:8000/");
  await page.waitForTimeout(1500);

  // Glide down to "Your rules", then visit each rule the voiceover names.
  await page.evaluate(() => document.getElementById("rules").scrollIntoView({ behavior: "smooth", block: "start" }));
  await page.waitForTimeout(2200);
  for (const name of ["monthly_budget", "per_purchase_cap", "savings_goal_name", "blocked_categories"]) {
    const field = page.locator(`[name="${name}"]`);
    await field.scrollIntoViewIfNeeded();
    await field.click();
    await page.waitForTimeout(2300);
  }
  await page.waitForTimeout(1000);
  const video = page.video();
  await context.close();
  await browser.close();
  console.log(await video.path());
})();
