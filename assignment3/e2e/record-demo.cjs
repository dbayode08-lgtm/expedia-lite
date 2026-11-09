// Records the captioned demo video (docs/recordings/demo.webm) of the running app.
// Mock model, fictional inputs only. Both servers must be running.
// Usage: node e2e/record-demo.cjs
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const ROOT = path.join(__dirname, "..");
const OUT = path.join(ROOT, "docs", "recordings");
const APP = process.env.APP_URL || "http://127.0.0.1:5174";
const API = process.env.API_URL || "http://127.0.0.1:8001";
const W = 1280, H = 800;

const CAPTION_JS = `
window.__cap = (text, section) => {
  let el = document.getElementById("__cap");
  if (!el) {
    el = document.createElement("div");
    el.id = "__cap";
    el.style.cssText = "position:fixed;left:0;right:0;bottom:0;z-index:99999;background:rgba(20,24,24,.92);color:#f3f1ec;font:500 20px/1.4 system-ui,sans-serif;padding:14px 28px;text-align:center;pointer-events:none";
    document.documentElement.appendChild(el);
    document.body.style.paddingBottom = "120px";
  }
  el.innerHTML = (section ? '<span style="display:block;font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#9fb7b3">' + section + '</span>' : '') + text;
};`;

function slide(title, body) {
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  body{margin:0;background:#f3f1ec;color:#2f3433;font:18px/1.55 system-ui,sans-serif;padding:36px 72px 130px}
  h1{font-size:30px;margin:0 0 18px} h2{font-size:18px;margin:14px 0 6px;color:#5d7774}
  code,pre{font:15px/1.5 ui-monospace,Menlo,monospace} pre{background:#fbfaf7;border:1px solid #d9d6cf;border-radius:10px;padding:14px 18px;white-space:pre-wrap}
  table{border-collapse:collapse;font-size:15px;background:#fbfaf7} td,th{border:1px solid #d9d6cf;padding:4px 9px;text-align:left}
  .bad{color:#7a3b33;font-weight:700} .good{color:#3f6b4f;font-weight:700}
  </style></head><body><h1>${title}</h1>${body}</body></html>`;
}

function esc(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;"); }

function rowFor(file, id) {
  const line = fs.readFileSync(file, "utf8").split("\n").find((l) => l.startsWith(`| ${id} `));
  return line ? line.split("|").slice(1, -1).map((c) => c.trim()) : [];
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  await fetch(`${API}/api/history`, { method: "DELETE" });

  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: W, height: H }, recordVideo: { dir: OUT, size: { width: W, height: H } } });
  await ctx.addInitScript(CAPTION_JS);
  const page = await ctx.newPage();
  const cap = (t, s) => page.evaluate(([t, s]) => window.__cap(t, s), [t, s]);
  const wait = (ms) => page.waitForTimeout(ms);

  // ---------------- PART 1: demo of the finished app
  await page.setContent(slide("Steady: IST 402 Assignment 3 demo", `
    <p>David Bayode · coursework skills prototype</p>
    <p>Not therapy, not a support service, not monitored. Every input in this video is <b>fictional</b>.</p>
    <p>Model: <b>mock (saved test responses)</b>, the default. This video was recorded automatically with Playwright by the coding agent (see AI-USE.md).</p>
    <h2>Sections</h2><p>1. Demo of the app &nbsp;·&nbsp; 2. Process: one failure → evidence → decision &nbsp;·&nbsp; 3. Saved data in SQLite</p>`));
  await cap("Steady demo: four brief skills, one at a time, with crisis support on every screen.", "Intro");
  await wait(6000);

  await page.goto(APP);
  await page.waitForSelector('[data-test="skill-breathing"]');
  await cap("Start screen: four skills offered as equal options, not a route (R4). Crisis support stays in the header on every screen (R2, D4).", "1 · Demo");
  await wait(6000);

  await page.click('[data-test="checkin-input"]');
  await page.type('[data-test="checkin-input"]', "my chest is tight and my heart is racing", { delay: 45 });
  await cap("Optional check-in. The text is checked for crisis language first, then the model (mock) replies in two short sentences.", "1 · Demo");
  await page.click('[data-test="checkin-send"]');
  await page.waitForSelector('[data-test="suggested"]');
  await wait(2000);
  await cap("The model only names a skill. It appears as one more button; the person still chooses. Steps come from skills.json, not the model.", "1 · Demo");
  await wait(6000);

  await page.locator('[data-test="suggested"]').scrollIntoViewIfNeeded();
  await wait(1500);
  await page.click('[data-test="suggested"]');
  await page.waitForSelector('[data-test="breathing"]');
  await cap("Paced breathing: the circle carries the pace, 4 s in, 6 s out, 6 breaths = 63 s (R1). Only Pause, Stop and Crisis support stay on screen (D1, D2).", "1 · Demo");
  await wait(14000);
  await cap("Opening Crisis support mid-exercise: static content, no backend or model needed. The exercise pauses and this time is excluded from the measured duration.", "1 · Demo");
  await page.click('[data-test="crisis"]');
  await page.waitForSelector('[data-test="crisis-panel"]');
  await wait(7000);
  await page.click('[data-test="crisis-panel"] button');
  await cap("Back to breathing. It resumes where it paused. Stop is always one tap with no confirmation (R3).", "1 · Demo");
  await page.waitForSelector('[data-test="done"]', { timeout: 90000 });
  await cap("Done. Feedback is optional, two taps or nothing. No streaks, no scores (D3, D6).", "1 · Demo");
  await wait(3000);
  await page.click('[data-test="fb-helped"]');
  await wait(2500);
  await page.click('[data-test="home"]');

  await page.click('[data-test="skill-grounding"]');
  await cap("5-4-3-2-1 grounding: notice silently, tap once per sense. No typing (D3).", "1 · Demo");
  await wait(4500);
  await page.click('[data-test="next"]');
  await wait(3500);
  await cap("Leaving mid-exercise: one tap on Stop.", "1 · Demo");
  await wait(2500);
  await page.click('[data-test="stop"]');
  await page.waitForSelector('[data-test="stopped"]');
  await cap("Stopped, with nothing lost. Stopping never lowers a skill in personalization (R3).", "1 · Demo");
  await wait(5000);
  await page.click('[data-test="home"]');

  await page.click('[data-test="skill-stop"]');
  await cap("STOP: one letter per screen; each step moves on by itself (42 s total), Next goes sooner.", "1 · Demo");
  await wait(7000);
  while (await page.locator('[data-test="next"]').count()) { await page.click('[data-test="next"]'); await wait(1500); }
  await page.waitForSelector('[data-test="done"]');
  await page.click('[data-test="home"]');

  await page.click('[data-test="skill-reframe"]');
  await cap("One-minute reframe: tap a common thought instead of typing.", "1 · Demo");
  await wait(4000);
  await page.click("text=They're upset with me");
  await cap("Evidence is optional. Skip.", "1 · Demo");
  await wait(3000);
  await page.click('[data-test="next"]');
  await cap("Opt-in: two possible alternative readings written by the model (validated in code). Pick one, write your own, or skip.", "1 · Demo");
  await wait(3500);
  await page.click('[data-test="assist"]');
  await page.waitForSelector(".chips .chip");
  await wait(4500);
  await page.locator(".chips .chip").first().click();
  await wait(2000);
  await page.click('[data-test="next"]');
  await cap("Finished with zero typed characters. Reframe text is not saved.", "1 · Demo");
  await wait(4000);
  await page.click('[data-test="next"]');
  await page.waitForSelector('[data-test="done"]');
  await page.click('[data-test="home"]');

  // second breathing completion -> "Your usual" (fast-forward for the video: recorded via API, labeled)
  const sid = (await (await fetch(`${API}/api/sessions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" })).json()).session_id;
  const rid = (await (await fetch(`${API}/api/runs`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ session_id: sid, skill: "breathing" }) })).json()).run_id;
  await fetch(`${API}/api/runs/${rid}/end`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: "completed", steps_done: 6, duration_ms: 63000 }) });
  await page.reload();
  await page.waitForSelector('[data-test="usual"]');
  await cap("After a second finished breathing run (added off-camera to save a minute), it shows as 'Your usual'. Personalization from history, no setup (D5).", "1 · Demo");
  await wait(7000);
  await page.check('[data-test="fewer"]');
  await cap("'Less on screen' is the person's switch (D1). The app does not claim to detect distress.", "1 · Demo");
  await wait(6000);
  await page.uncheck('[data-test="fewer"]');
  await page.click('[data-test="history"]');
  await page.waitForSelector(".session");
  await page.locator(".session .link").first().click().catch(() => {});
  await cap("History: what was saved, in plain words, plus Clear history.", "1 · Demo");
  await wait(7000);

  await page.goto(APP + "/?simulateFailure=1");
  await page.waitForSelector('[data-test="checkin-input"]');
  await page.type('[data-test="checkin-input"]', "I keep thinking it's all my fault", { delay: 40 });
  await cap("Failure case: ?simulateFailure=1 makes every model request fail.", "1 · Demo");
  await page.click('[data-test="checkin-send"]');
  await page.waitForSelector("text=isn't available right now");
  await wait(3000);
  await cap("The app shows a fixed fallback line. All four skills still work…", "1 · Demo");
  await wait(4500);
  await page.click('[data-test="crisis"]');
  await cap("…and Crisis support still opens (behavior check B1).", "1 · Demo");
  await wait(5500);
  await page.click('[data-test="crisis-panel"] button');

  // ---------------- PART 2: process: failure -> evidence -> decision
  const before = rowFor(path.join(ROOT, "docs/evidence/failure-s08/before-fix-mock-results.md"), "S08");
  const after = rowFor(path.join(ROOT, "docs/evidence/failure-s08/after-fix-mock-results.md"), "S08");
  const tbl = (r, cls) => `<table><tr><th>ID</th><th>Input</th><th>Expected</th><th>Observed</th><th>Result</th></tr>
    <tr><td>${esc(r[0])}</td><td>${esc(r[2])}</td><td><code>${esc(r[3])}</code></td><td><code>${esc(r[4])}</code></td><td class="${cls}">${esc(r[5])}</td></tr></table>`;
  await page.setContent(slide("Process: one failure → evidence → decision", `
    <h2>Failure: scenario S08 on the first evaluation run</h2>${tbl(before, "bad")}
    <p>A common idiom, "this exam is killing me", put the app into crisis mode and skipped the model.</p>`));
  await cap("Process screencast. On the first run of the 17 API scenarios, S08 failed: an everyday idiom triggered crisis mode.", "2 · Process");
  await wait(9000);
  await page.setContent(slide("Evidence: the pattern that matched", `
    <h2>shared/crisis.json, before</h2><pre>\\bkill(ing)? (myself|me)\\b</pre>
    <p>"kill me" was meant to catch danger, but "killing me" is far more often about exams.</p>
    <h2>Decision</h2><pre>\\bkill(ing)? myself\\b</pre>
    <p>Narrow the pattern. Keep the S09 over-trigger on negation ("I'm not suicidal…") on purpose: a false alarm only shows resources, a miss is worse, and the Crisis support button never depended on the regex.</p>`));
  await cap("Evidence: the regex in crisis.json. Decision: narrow it to 'myself' and accept the negation over-trigger. Crisis support never depends on this check.", "2 · Process");
  await wait(11000);
  await page.setContent(slide("After the fix", `${tbl(after, "good")}
    <p>All 17 API scenarios pass; unit test <code>test_crisis_patterns</code> now includes "my feet are killing me" → not crisis.</p>`));
  await cap("After the fix: S08 passes, 17/17 scenarios, and a unit test guards it.", "2 · Process");
  await wait(7000);

  // ---------------- PART 3: SQLite evidence
  const dbHtml = execSync(`python3 -c "
import sqlite3,html
c=sqlite3.connect('${path.join(ROOT, "backend", "steady.db")}')
def t(q):
    cur=c.execute(q);cols=[d[0] for d in cur.description]
    rows=''.join('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in r)+'</tr>' for r in cur.fetchall())
    return '<table><tr>'+''.join('<th>'+x+'</th>' for x in cols)+'</tr>'+rows+'</table>'
print('<h2>exercise_runs</h2>'+t('SELECT id,skill,chosen_via,status,steps_done,setup_ms,duration_ms,paused_ms,feedback FROM exercise_runs ORDER BY id'))
print('<h2>messages</h2>'+t('SELECT id,session_id,role,substr(content,1,55) AS content,source,crisis_flag,suggested_skill FROM messages ORDER BY id'))
print('<h2>model_calls</h2>'+t('SELECT id,purpose,provider,ok,latency_ms,error FROM model_calls ORDER BY id'))
"`).toString();
  await page.setContent(slide("Saved data: backend/steady.db (this recording)", dbHtml));
  await cap("SQLite after this demo: runs with status, measured duration and paused time (crisis time excluded), messages with their source, and the failed model calls (ok = 0).", "3 · Saved data");
  await wait(1500);
  await page.evaluate(() => window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" }));
  await wait(13000);

  await page.close();
  const video = await page.video().path();
  await ctx.close();
  await browser.close();
  fs.renameSync(video, path.join(OUT, "demo.webm"));
  console.log("saved", path.join(OUT, "demo.webm"));
})().catch((e) => { console.error(e); process.exit(1); });
