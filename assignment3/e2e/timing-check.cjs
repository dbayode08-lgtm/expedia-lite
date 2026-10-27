// Runs grounding and reframe at the ASSUMED human pace from shared/skills.json
// (waiting each step's planned seconds before tapping) and reads the measured
// duration back from the API. Usage: node e2e/timing-check.cjs
const { chromium } = require("playwright");
const skills = require("../shared/skills.json").skills;
const APP = process.env.APP_URL || "http://127.0.0.1:5174";
const API = process.env.API_URL || "http://127.0.0.1:8001";
const sec = (id) => skills.find((s) => s.id === id).steps.map((s) => s.seconds);

(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto(APP);
  await p.waitForSelector('[data-test="skill-grounding"]');

  // grounding: wait planned seconds, tap Next
  await p.click('[data-test="skill-grounding"]');
  for (const s of sec("grounding")) { await p.waitForTimeout(s * 1000); await p.click('[data-test="next"]'); }
  await p.waitForSelector('[data-test="done"]');
  await p.click('[data-test="home"]');

  // reframe: type thought, type evidence, use model assist, read close
  const [t1, t2, t3, t4] = sec("reframe");
  await p.click('[data-test="skill-reframe"]');
  await p.click('[data-test="type-own"]');
  await p.waitForTimeout((t1 - 4) * 1000);
  await p.type('[data-test="thought-input"]', "I bombed the presentation", { delay: 120 });
  await p.keyboard.press("Enter");
  await p.waitForTimeout((t2 - 3) * 1000);
  await p.type('[data-test="evidence-input"]', "I froze once", { delay: 150 });
  await p.click('[data-test="next"]');
  await p.click('[data-test="assist"]');
  await p.waitForSelector(".chips .chip");
  await p.waitForTimeout((t3 - 1) * 1000);
  await p.locator(".chips .chip").first().click();
  await p.click('[data-test="next"]');
  await p.waitForTimeout(t4 * 1000);
  await p.click('[data-test="next"]');
  await p.waitForSelector('[data-test="done"]');

  const runs = (await (await fetch(`${API}/api/history`)).json()).sessions.flatMap((s) => s.runs).sort((a, b) => a.id - b.id).slice(-2);
  for (const r of runs) {
    const planned = skills.find((s) => s.id === r.skill).planned_seconds;
    console.log(`${r.skill}: measured ${(r.duration_ms / 1000).toFixed(1)} s, planned ${planned} s, setup ${r.setup_ms} ms, status ${r.status}`);
  }
  await b.close();
})().catch((e) => { console.error(e); process.exit(1); });
