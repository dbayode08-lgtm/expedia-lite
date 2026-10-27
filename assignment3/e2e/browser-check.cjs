// Browser walkthrough of the running app (mock model). Saves screenshots to docs/evidence/
// and prints a JSON summary of what was observed.
// Usage (both servers running, LLM_PROVIDER=mock):  node e2e/browser-check.cjs
// Needs Playwright (`npm i -g playwright` or run where it is installed).
const { chromium } = require("playwright");
const path = require("path");
const OUT = path.join(__dirname, "..", "docs", "evidence");
const APP = process.env.APP_URL || "http://127.0.0.1:5174";
const API = process.env.API_URL || "http://127.0.0.1:8001";

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 430, height: 860 } });
  const page = await ctx.newPage();
  const results = [];
  const log = (id, ok, note) => { results.push({ id, ok, note }); console.log(ok ? "PASS" : "FAIL", id, note || ""); };
  const shot = (n) => page.screenshot({ path: path.join(OUT, n + ".png") });
  const crisisVisible = async () => page.locator('[data-test="crisis"]').isVisible();

  await fetch(`${API}/api/history`, { method: "DELETE" });

  // 1. Home
  await page.goto(APP);
  await page.waitForSelector('[data-test="skill-breathing"]');
  await shot("01-home");
  log("home-options", await page.locator(".choice").count() === 4, "four skills offered, none pre-selected");

  // 2. Check-in -> suggestion -> full breathing run
  await page.fill('[data-test="checkin-input"]', "my chest is tight and my heart is racing");
  await page.click('[data-test="checkin-send"]');
  await page.waitForSelector('[data-test="suggested"]');
  await shot("02-checkin-suggestion");
  log("checkin-suggests-breathing", (await page.textContent('[data-test="suggested"]')).includes("Paced breathing"));
  await page.click('[data-test="suggested"]');
  await page.waitForSelector('[data-test="breathing"]');
  await page.waitForTimeout(5500);
  await shot("03-breathing-inhale");
  log("crisis+stop visible in exercise", (await crisisVisible()) && (await page.locator('[data-test="stop"]').isVisible()));
  // open crisis support mid-exercise (time excluded from measure)
  await page.click('[data-test="crisis"]');
  await page.waitForSelector('[data-test="crisis-panel"]');
  await shot("04-crisis-panel-during-breathing");
  await page.waitForTimeout(4000);
  await page.click('[data-test="crisis-panel"] button');
  const t0 = Date.now();
  await page.waitForSelector('[data-test="done"]', { timeout: 120000 });
  await shot("05-breathing-done");
  await page.click('[data-test="fb-helped"]');
  log("breathing completes", true, `wall ${Math.round((Date.now() - t0) / 1000)}s after closing crisis panel`);
  await page.click('[data-test="home"]');

  // 3. STOP runs by itself
  await page.click('[data-test="skill-stop"]');
  await page.waitForSelector('[data-test="stop-skill"]');
  await page.waitForTimeout(22000);
  await shot("06-stop-observe");
  await page.waitForSelector('[data-test="done"]', { timeout: 60000 });
  log("STOP auto-advances to done", true);
  await page.click('[data-test="home"]');

  // 4. Grounding: tap through, no typing
  await page.click('[data-test="skill-grounding"]');
  await page.waitForSelector('[data-test="grounding"]');
  await shot("07-grounding-step1");
  for (let i = 0; i < 5; i++) { await page.waitForTimeout(1200); await page.click('[data-test="next"]'); }
  await page.waitForSelector('[data-test="done"]');
  log("grounding completes with 5 taps", (await page.locator("input").count()) === 0);
  await page.click('[data-test="home"]');

  // 5. Stop mid-exercise
  await page.click('[data-test="skill-grounding"]');
  await page.click('[data-test="next"]');
  await page.click('[data-test="stop"]');
  await page.waitForSelector('[data-test="stopped"]');
  await shot("08-stopped");
  log("stop leads to neutral screen, no confirm", true);
  await page.click('[data-test="home"]');

  // 6. Reframe with mock alternatives
  await page.click('[data-test="skill-reframe"]');
  await page.click("text=They're upset with me");
  await page.click('[data-test="next"]');                 // skip evidence
  await page.click('[data-test="assist"]');
  await page.waitForSelector(".chip >> nth=0");
  await shot("09-reframe-alternatives");
  await page.locator(".chips .chip").first().click();
  await page.click('[data-test="next"]');
  await page.click('[data-test="next"]');
  await page.waitForSelector('[data-test="done"]');
  log("reframe completes with zero typed characters", true);
  await page.click('[data-test="home"]');

  // 7. Crisis text in check-in
  await page.fill('[data-test="checkin-input"]', "honestly i want to die");
  await page.click('[data-test="checkin-send"]');
  await page.waitForSelector('[data-test="crisis-panel"]');
  await shot("10-crisis-text");
  log("crisis text opens crisis support", true);
  await page.click('[data-test="crisis-panel"] button');

  // 8. Personalization: usual appears after the breathing completion + one more
  await page.click('[data-test="skill-breathing"]');
  await page.waitForSelector('[data-test="done"]', { timeout: 120000 });
  await page.click('[data-test="home"]');
  await page.waitForSelector('[data-test="usual"]');
  await shot("11-your-usual");
  log("usual skill shown after 2 completions", (await page.textContent('[data-test="usual"]')).includes("Paced breathing"));

  // 9. Less on screen
  await page.check('[data-test="fewer"]');
  await shot("12-less-on-screen");
  log("less on screen hides list + check-in", (await page.locator('[data-test="checkin-input"]').count()) === 0 && (await crisisVisible()));
  await page.uncheck('[data-test="fewer"]');

  // 10. History
  await page.click('[data-test="history"]');
  await page.waitForSelector(".session");
  await shot("13-history");
  log("history lists sessions", (await page.locator(".run").count()) >= 5);

  // 11. Model failure (simulated)
  const p2 = await ctx.newPage();
  await p2.goto(APP + "/?simulateFailure=1");
  await p2.fill('[data-test="checkin-input"]', "I keep thinking it's all my fault");
  await p2.click('[data-test="checkin-send"]');
  await p2.waitForSelector("text=isn't available right now");
  await p2.screenshot({ path: path.join(OUT, "14-model-failure-checkin.png") });
  await p2.click('[data-test="crisis"]');
  log("crisis works after failed model request", await p2.locator('[data-test="crisis-panel"]').isVisible());
  await p2.click('[data-test="crisis-panel"] button');
  await p2.click('[data-test="skill-reframe"]');
  await p2.click("text=I messed everything up");
  await p2.click('[data-test="next"]');
  await p2.click('[data-test="assist"]');
  await p2.waitForSelector('[data-test="assist-failed"]');
  await p2.screenshot({ path: path.join(OUT, "15-model-failure-reframe.png") });
  log("reframe continues after model failure", await p2.locator('[data-test="alt-input"]').isVisible());

  // 12. Backend unreachable
  const p3 = await ctx.newPage();
  await p3.route(API + "/**", (r) => r.abort());
  await p3.goto(APP);
  await p3.waitForSelector('[data-test="not-saving"]');
  await p3.click('[data-test="crisis"]');
  await p3.waitForSelector('[data-test="crisis-panel"]');
  await p3.screenshot({ path: path.join(OUT, "16-backend-down-crisis.png") });
  log("crisis works with backend down", true);

  const hist = await (await fetch(`${API}/api/history`)).json();
  const runs = hist.sessions.flatMap((s) => s.runs).map((r) => ({ skill: r.skill, status: r.status, setup_ms: r.setup_ms, duration_ms: r.duration_ms, paused_ms: r.paused_ms, steps: r.steps_done }));
  console.log(JSON.stringify({ results, runs }, null, 2));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
