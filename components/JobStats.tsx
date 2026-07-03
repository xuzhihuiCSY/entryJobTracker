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
    <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <div key={item.label} className="rounded-lg border border-line bg-white p-4 shadow-subtle">
            <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-md bg-slate-100 text-slate-700">
              <Icon aria-hidden="true" className="h-5 w-5" />
            </div>
            <div className="text-2xl font-semibold text-ink">{item.value}</div>
            <div className="mt-1 text-sm text-muted">{item.label}</div>
          </div>
        );
      })}
      <p className="sm:col-span-2 lg:col-span-4 text-sm text-muted">
        Last updated: <LocalDateTime value={stats.last_updated} />
      </p>
    </section>
  );
}
