// Records the real web app against the real PayPal sandbox, reusing the buyer session the
// person signed into with login.js. Usage: node record_live.js approve|nudge|ledger
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");

const APP = "http://localhost:8000";
const OUT = path.join(__dirname, "raw");
const which = process.argv[2];

async function send(page, text) {
  const before = await page.locator("#messages .row.assistant").count();
  await page.locator("#chat-input").click();
  await page.locator("#chat-input").pressSequentially(text, { delay: 35 });
  await page.keyboard.press("Enter");
  await page.waitForFunction((n) => document.querySelectorAll("#messages .row.assistant:not(.typing)").length > n, before, { timeout: 90000 });
}

async function approveInPayPal(page) {
  const approve = page.locator("#messages a", { hasText: "Approve in PayPal" }).last();
  await approve.waitFor({ timeout: 90000 });
  await approve.scrollIntoViewIfNeeded();
  await page.waitForTimeout(2500);
  await approve.click();
  await page.waitForURL(/paypal\.com/, { timeout: 60000 });
  await page.waitForLoadState("networkidle", { timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(2000);
  // Never type credentials or solve challenges: stop and let the person handle it.
  if (await page.locator('input[type="password"], #email, iframe[title*="captcha" i]').count()) {
    console.log(`WAITING ${new Date().toISOString()}: sign in on PayPal in the window yourself (the script never types it)`);
    await page.locator('input[type="password"], #email').first().waitFor({ state: "detached", timeout: 300000 });
    await page.waitForLoadState("networkidle", { timeout: 60000 }).catch(() => {});
    await page.waitForTimeout(2000);
    console.log(`SIGNED IN ${new Date().toISOString()}`);
  }
  const labels = await page.locator("button").evaluateAll((bs) => bs.map((b) => [b.id, b.getAttribute("data-testid"), b.innerText.trim()].join(" | ")));
  console.log("PAYPAL BUTTONS: " + labels.join(" || "));
  // PayPal's main submit button, never an offer like "Pay in 4".
  const pay = page.locator("#one-time-cta, #payment-submit-btn, [data-testid='submit-button-initial']")
    .or(page.getByRole("button", { name: /^(complete purchase|continue to review order|pay now|agree & continue)$/i })).first();
  await pay.waitFor({ timeout: 60000 });
  await page.waitForTimeout(1500);
  await pay.click();
  await page.waitForURL(/localhost:8000\/(#demo)?(\?.*)?$|status=/, { timeout: 90000 });
  await page.waitForSelector("#messages .decision.approved, #messages .decision.blocked", { timeout: 60000 });
  await page.waitForTimeout(500);
  await page.evaluate(() => document.querySelector("#demo .card").scrollIntoView({ block: "start" }));
  await page.waitForTimeout(600);
  // Bring the guard's final decision into view inside the chat.
  await page.evaluate(() => { const m = document.getElementById("messages"); m.scrollTop = m.scrollHeight; });
  await page.waitForTimeout(4500);
}

(async () => {
  const context = await chromium.launchPersistentContext(path.join(__dirname, "profile"), {
    headless: false,
    // The screen is 1536x864 at 125% scaling, so a visible window fits 1280x720 (1600x900 real pixels).
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: OUT, size: { width: 1600, height: 900 } },
  });
  // 200% zoom on the app only, so its text records large; PayPal's own page is left as is.
  await context.addInitScript(() => {
    if (location.host === "localhost:8000") {
      document.addEventListener("DOMContentLoaded", () => {
        document.documentElement.style.zoom = "1.3333";
        // Recording only: the page's own single-column (narrow-window) layout, with the chat card sized to the screen.
        const css = document.createElement("style");
        css.textContent = ".hero{grid-template-columns:minmax(0,1fr)!important}.demo{height:500px!important;min-height:0!important}";
        document.head.appendChild(css);
      });
    }
  });
  const page = await context.newPage();
  for (const p of context.pages()) if (p !== page) await p.close();
  try {
    // Let the headed window settle before the take, so the first frames record at the right scale.
    await page.goto("about:blank");
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.waitForTimeout(1500);
    await page.goto(`${APP}/`);
    await page.reload();
    await page.waitForTimeout(800);
    await page.evaluate((w) => document.querySelector(w === "ledger" ? "#ledger" : "#demo .card").scrollIntoView({ block: "start" }), which);
    await page.waitForTimeout(1200);
    if (which === "probe") {
      await page.locator("#new-request").click();
      await page.locator("#chat-input").pressSequentially("Grab a bottle of cabernet for dinner", { delay: 35 });
      await page.keyboard.press("Enter");
      await page.waitForSelector("#messages .decision.blocked", { timeout: 90000 });
      await page.waitForTimeout(3000);
    } else if (which === "ledger") {
      await page.evaluate(() => document.getElementById("ledger").scrollIntoView({ behavior: "smooth", block: "start" }));
      await page.waitForTimeout(9000);
    } else {
      await page.locator("#new-request").click();
      await page.waitForTimeout(800);
      if (which === "approve") {
        await send(page, "Get me an unscented moisturiser under $25");
      } else {
        await send(page, "Buy me the Studio Pro noise-cancelling headphones");
        await page.waitForSelector("#messages .decision.nudge", { timeout: 60000 });
        await page.waitForTimeout(3500);
        await send(page, "Yes, buy the earbuds instead");
      }
      await approveInPayPal(page);
    }
  } catch (e) {
    console.error("STOPPED:", e.message);
    await page.screenshot({ path: path.join(OUT, `${which}-stopped.png`) });
  }
  const video = page.video();
  await context.close();
  const file = await video.path();
  fs.renameSync(file, path.join(OUT, `${which}.webm`));
  console.log("saved", `${which}.webm`);
})();
