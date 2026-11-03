// Opens a visible browser on the PayPal sandbox sign-in page. The person signs in as their
// sandbox buyer themselves; the session is saved in ./profile for the recording script.
const { chromium } = require("playwright");
const path = require("path");

(async () => {
  const context = await chromium.launchPersistentContext(path.join(__dirname, "profile"), {
    headless: false,
    viewport: null,
  });
  const page = context.pages()[0] || (await context.newPage());
  await page.goto("https://www.sandbox.paypal.com/signin");
  console.log("Waiting for the window to be closed...");
  await new Promise((resolve) => context.on("close", resolve));
  console.log("closed");
})();
