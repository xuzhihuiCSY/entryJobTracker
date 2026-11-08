const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const ts = require("typescript");
const source = fs.readFileSync(path.join(__dirname, "../lib/job-trends.ts"), "utf8");
const compiled = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020}}).outputText;
const mod = {exports: {}};
new Function("exports", "module", compiled)(mod.exports, mod);
const {visibleHistory, bigFiveJobTrend, jobGrowth, snapshotChanges, trendBounds} = mod.exports;
const point = (date, total_jobs) => ({date, total_jobs});
const data = [point("2026-10-01", 100), point("2026-10-31", 130), point("2026-11-05", 120), point("2026-11-06", 125)];
assert.deepEqual(visibleHistory(data, 7), data.slice(1));
assert.deepEqual(visibleHistory(data, 30), data.slice(1));
assert.deepEqual(visibleHistory(data, "all"), data);
assert.deepEqual(visibleHistory([], 7), []);
assert.deepEqual(jobGrowth(data), {change: 25, percent: 25});
assert.deepEqual(jobGrowth(data.slice(1)), {change: -5, percent: -5 / 130 * 100});
assert.deepEqual(jobGrowth([point("2026-11-01", 0), point("2026-11-02", 10)]), {change: 10, percent: null});
assert.deepEqual(jobGrowth(data.slice(0, 1)), {change: null, percent: null});
assert.deepEqual([...snapshotChanges(data).values()], [null, 30, -10, 5]);
const withoutMeta = { "apple:custom": 15, "microsoft:custom": 5, "google:custom": 175, "amazon:custom": 75 };
const five = { ...withoutMeta, "meta:custom": 25 };
const coverageHistory = [
  { ...point("2026-10-01", 340), comparable_jobs: { ...withoutMeta, "meta:legacy": 70 } },
  { ...point("2026-10-08", 295), comparable_jobs: five },
  point("2026-10-20", 300),
  { ...point("2026-11-04", 270), comparable_jobs: withoutMeta },
  { ...point("2026-11-05", 1195), comparable_jobs: { ...five, "meta:custom": 0, "new:ashby": 925 } },
  { ...point("2026-11-06", 1226), comparable_jobs: { ...five, "amazon:custom": 76, "new:ashby": 930 } },
  { ...point("2026-11-07", 1205), comparable_jobs: { ...withoutMeta, "new:ashby": 935 } }
];
const all = bigFiveJobTrend(coverageHistory, "all");
assert.deepEqual(all, [point("2026-10-08", 295), point("2026-11-05", 270), point("2026-11-06", 296)]);
const recent = bigFiveJobTrend(coverageHistory, 7);
assert.deepEqual(recent, all.slice(1));
assert.deepEqual([...snapshotChanges(recent).values()], [null, 26]);
assert.deepEqual(bigFiveJobTrend(coverageHistory.slice(0, 4), 7), []);
assert.deepEqual(bigFiveJobTrend(data, "all"), []);
for (const values of [[], [0], [100, 100], [-5, -5], [-10, 0, 20]]) {
  const [low, high] = trendBounds(values, true);
  assert(Number.isFinite(low) && Number.isFinite(high) && high > low);
  assert(low <= 0 && high >= 0);
}
console.log("job growth range, percentage, missing-day, and zero-baseline tests passed");
