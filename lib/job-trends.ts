import type { JobHistoryPoint } from "./types";

export type TrendRange = 7 | 30 | 90 | "all";
export const DAY_MS = 86_400_000;
export type TrendPoint = Pick<JobHistoryPoint, "date" | "total_jobs">;

export const BIG_FIVE_COMPANIES = {
  apple: "Apple",
  microsoft: "Microsoft",
  google: "Google",
  amazon: "Amazon",
  meta: "Meta"
} as const;

export function visibleHistory(history: JobHistoryPoint[], range: TrendRange): JobHistoryPoint[] {
  if (!history.length || range === "all") return history;
  const end = Date.parse(`${history[history.length - 1].date}T00:00:00Z`);
  const start = end - (range - 1) * DAY_MS;
  return history.filter((point) => Date.parse(`${point.date}T00:00:00Z`) >= start);
}

export function bigFiveJobTrend(history: JobHistoryPoint[], range: TrendRange): TrendPoint[] {
  const companies = Object.keys(BIG_FIVE_COMPANIES);
  // Use the latest complete snapshot to keep the same sources across every range.
  let keys: string[] = [];
  for (let i = history.length - 1; i >= 0; i--) {
    const sourceKeys = Object.keys(history[i].comparable_jobs ?? {});
    keys = companies.flatMap((slug) => sourceKeys.find((key) => key.startsWith(`${slug}:`)) ?? []);
    if (keys.length === companies.length) break;
  }
  if (keys.length !== companies.length) return [];

  return visibleHistory(history, range).flatMap(({ date, comparable_jobs: counts }) => {
    if (!counts || !keys.every((key) => Object.prototype.hasOwnProperty.call(counts, key))) return [];
    return [{ date, total_jobs: keys.reduce((total, key) => total + counts[key], 0) }];
  });
}

export function jobGrowth(history: TrendPoint[]) {
  if (history.length < 2) return { change: null, percent: null };
  const first = history[0].total_jobs;
  const change = history[history.length - 1].total_jobs - first;
  return { change, percent: first === 0 ? null : (change / first) * 100 };
}

export function snapshotChanges(history: TrendPoint[]): Map<string, number | null> {
  return new Map(history.map((point, index) => [
    point.date, index === 0 ? null : point.total_jobs - history[index - 1].total_jobs
  ]));
}

export function trendBounds(values: number[], includeZero = false): [number, number] {
  if (!values.length) return [0, 1];
  let low = Math.min(...values);
  let high = Math.max(...values);
  if (includeZero) {
    low = Math.min(0, low);
    high = Math.max(0, high);
  }
  const padding = Math.max(1, Math.ceil((high - low || Math.abs(high)) * 0.12));
  return [includeZero || low < 0 ? low - padding : Math.max(0, low - padding), high + padding];
}
