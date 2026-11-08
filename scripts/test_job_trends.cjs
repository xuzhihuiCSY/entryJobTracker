const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const ts = require("typescript");
const source = fs.readFileSync(path.join(__dirname, "../lib/job-trends.ts"), "utf8");
const compiled = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020}}).outputText;
const mod = {exports: {}};
new Function("exports", "module", compiled)(mod.exports, mod);
const {visibleHistory, comparableJobTrend, jobGrowth, snapshotChanges, trendBounds} = mod.exports;
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
const coverageHistory = [
  { ...point("2026-10-01", 152), comparable_jobs: { "a:greenhouse": 100, "b:ashby": 50, "c:workday": 2 } },
  point("2026-10-20", 160),
  { ...point("2026-11-05", 1030), comparable_jobs: { "a:greenhouse": 105, "c:workday": 0, "new:ashby": 925 } },
  { ...point("2026-11-06", 1254), comparable_jobs: { "a:greenhouse": 103, "b:workday": 215, "c:workday": 6, "new:ashby": 930 } }
];
const all = comparableJobTrend(coverageHistory, "all");
assert.equal(all.companyCount, 2);
assert.deepEqual(all.points.map(p => [p.date, p.total_jobs]), [["2026-10-01", 102], ["2026-11-05", 105], ["2026-11-06", 109]]);
const recent = comparableJobTrend(coverageHistory, 7);
assert.equal(recent.companyCount, 3);
assert.deepEqual([...snapshotChanges(recent.points).values()], [null, 9]);
assert.deepEqual(comparableJobTrend(data, "all"), { companyCount: 0, points: [] });
for (const values of [[], [0], [100, 100], [-5, -5], [-10, 0, 20]]) {
  const [low, high] = trendBounds(values, true);
  assert(Number.isFinite(low) && Number.isFinite(high) && high > low);
  assert(low <= 0 && high >= 0);
}
console.log("job growth range, percentage, missing-day, and zero-baseline tests passed");
