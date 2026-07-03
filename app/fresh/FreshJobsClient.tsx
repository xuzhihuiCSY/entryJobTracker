"use client";

import { useMemo, useState } from "react";
import { JobFilters } from "@/components/JobFilters";
import { isFresh } from "@/lib/filters";
import type { Job } from "@/lib/types";

const windows = [
  { label: "24h", hours: 24 },
  { label: "48h", hours: 48 },
  { label: "7d", hours: 24 * 7 }
];

type FreshJobsClientProps = {
  jobs: Job[];
};

export function FreshJobsClient({ jobs }: FreshJobsClientProps) {
  const [hours, setHours] = useState(24);
  const freshJobs = useMemo(() => jobs.filter((job) => isFresh(job, hours)), [hours, jobs]);

  return (
    <div className="grid gap-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-semibold text-ink">Fresh Jobs</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
            Newly discovered active postings based on the preserved first_seen timestamp.
          </p>
        </div>
        <div className="inline-flex w-fit rounded-md border border-line bg-white p-1 shadow-subtle">
          {windows.map((window) => (
            <button
              key={window.hours}
              type="button"
              onClick={() => setHours(window.hours)}
              className={`rounded px-3 py-1.5 text-sm font-medium ${
                hours === window.hours ? "bg-slate-900 text-white" : "text-slate-600"
              }`}
            >
              {window.label}
            </button>
          ))}
        </div>
      </div>
      <JobFilters jobs={freshJobs} emptyMessage="No fresh jobs in this time window." />
    </div>
  );
}
