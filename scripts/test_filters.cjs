const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const ts = require("typescript");

// Compile the actual pure filter module so these regressions run without a
// browser or a second copy of its matching logic.
const source = fs.readFileSync(path.join(__dirname, "../lib/filters.ts"), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 }
}).outputText;
const filtersModule = { exports: {} };
new Function("exports", "module", compiled)(filtersModule.exports, filtersModule);
const { DEFAULT_FILTERS, filterJobs } = filtersModule.exports;

const base = {
  company: "Example", title: "Research Engineer", location_raw: "New York, NY",
  category: "ML", level: "Entry", first_seen: "2026-11-05T12:00:00Z"
};
const jobs = [
  { ...base, id: "phd-only", phd_requirement: "required" },
  { ...base, id: "masters-or-phd", phd_requirement: "optional" },
  { ...base, id: "phd-preferred", phd_requirement: "preferred" },
  { ...base, id: "unknown", phd_requirement: "unknown" },
  { ...base, id: "legacy" }
];
assert.deepEqual(filterJobs(jobs, DEFAULT_FILTERS).map(j => j.id), [
  "masters-or-phd", "phd-preferred", "unknown", "legacy"
]);
assert.equal(filterJobs(jobs, { ...DEFAULT_FILTERS, phd: "all" }).length, 5);
assert.deepEqual(filterJobs(jobs, { ...DEFAULT_FILTERS, phd: "required" }).map(j => j.id), ["phd-only"]);
assert.equal(filterJobs(jobs, { ...DEFAULT_FILTERS, phd: "required", category: "SDE" }).length, 0);
assert.equal(filterJobs(jobs, { ...DEFAULT_FILTERS, query: "New York" }).length, 4);
console.log("filter regression tests passed");

const authorizationJobs = [
  { ...base, id: "sponsor", visa_signal: "strong", requires_citizenship: false, requires_clearance: false },
  { ...base, id: "no-sponsor", visa_signal: "not_likely", requires_citizenship: false, requires_clearance: false },
  { ...base, id: "conditional", visa_signal: "conditional", requires_citizenship: false, requires_clearance: false },
  { ...base, id: "unknown", visa_signal: "unknown", requires_citizenship: true, requires_clearance: false },
  { ...base, id: "clearance", visa_signal: "unknown", requires_citizenship: false, requires_clearance: true },
  { ...base, id: "legacy" }
];
assert.equal(filterJobs(authorizationJobs, DEFAULT_FILTERS).length, 6);
assert.deepEqual(filterJobs(authorizationJobs, { ...DEFAULT_FILTERS, visa: "strong" }).map(j => j.id), ["sponsor"]);
assert.equal(filterJobs(authorizationJobs, { ...DEFAULT_FILTERS, visa: "exclude_no_sponsorship" }).length, 5);
assert.deepEqual(filterJobs(authorizationJobs, { ...DEFAULT_FILTERS, visa: "conditional" }).map(j => j.id), ["conditional"]);
assert.equal(filterJobs(authorizationJobs, { ...DEFAULT_FILTERS, visa: "unknown" }).length, 3);
assert.deepEqual(filterJobs(authorizationJobs, { ...DEFAULT_FILTERS, hideCitizenshipRequired: true, hideClearanceRequired: true, visa: "unknown" }).map(j => j.id), ["legacy"]);
console.log("authorization filter regression tests passed");
