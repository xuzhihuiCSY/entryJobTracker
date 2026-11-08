import { Clock3, Landmark, RefreshCw, Rows3 } from "lucide-react";
import { LocalDateTime } from "@/components/LocalDateTime";
import type { LastUpdated } from "@/lib/types";

type JobStatsProps = {
  stats: LastUpdated;
};

export function JobStats({ stats }: JobStatsProps) {
  const items = [
    { label: "Total active jobs", value: stats.total_jobs, icon: Rows3 },
    { label: "Big Tech jobs", value: stats.big_tech_jobs, icon: Landmark },
    { label: "Fresh within 24h", value: stats.fresh_24h_jobs, icon: Clock3 },
    { label: "Sources synced", value: stats.sources_synced, icon: RefreshCw }
  ];

  return (
    <section aria-labelledby="tracker-overview" className="mt-6">
      <h2 id="tracker-overview" className="text-sm font-semibold text-slate-700">Tracker overview</h2>
      <div className="mt-2 grid grid-cols-2 gap-3">
        {items.map(({ label, value, icon: Icon }) => (
          <div key={label} className="rounded-lg border border-line bg-white p-3 shadow-subtle sm:px-4">
            <div className="flex items-center justify-between gap-2">
              <div className="text-2xl font-semibold tabular-nums text-ink">{value.toLocaleString("en-US")}</div>
              <Icon aria-hidden="true" className="h-5 w-5 shrink-0 text-slate-500" />
            </div>
            <div className="mt-1 text-sm text-muted">{label}</div>
          </div>
        ))}
      </div>
      <p className="mt-2 text-xs text-muted">
        Last updated: <LocalDateTime value={stats.last_updated} />
      </p>
    </section>
  );
}
