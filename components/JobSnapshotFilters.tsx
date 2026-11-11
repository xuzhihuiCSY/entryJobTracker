"use client";

import { useEffect, useMemo, useState } from "react";
import { JobFilters } from "@/components/JobFilters";
import { isFresh } from "@/lib/filters";
import type { Job } from "@/lib/types";

const CACHE_MS = 5 * 60 * 1000;
let request: Promise<Job[]> | undefined;
let loadedAt = 0;

function loadJobs(): Promise<Job[]> {
  if (!request || (loadedAt > 0 && Date.now() - loadedAt >= CACHE_MS)) {
    loadedAt = 0;
    request = fetch("/data/jobs.json").then(async (response) => {
      if (!response.ok) throw new Error("Job snapshot unavailable");
      const jobs: Job[] = await response.json();
      if (!Array.isArray(jobs)) throw new Error("Invalid job snapshot");
      loadedAt = Date.now();
      return jobs;
    }).catch((error) => {
      request = undefined;
      throw error;
    });
  }
  return request;
}

type JobSnapshotFiltersProps = {
  defaultEntryOnly?: boolean;
  freshHours?: number;
};

export function JobSnapshotFilters({ defaultEntryOnly, freshHours }: JobSnapshotFiltersProps) {
  const [snapshot, setSnapshot] = useState<Job[] | "error" | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    void loadJobs().then(
      (jobs) => { if (active) setSnapshot(jobs); },
      () => { if (active) setSnapshot("error"); }
    );
    return () => { active = false; };
  }, [attempt]);

  const jobs = useMemo(() => {
    if (!Array.isArray(snapshot)) return [];
    return freshHours === undefined ? snapshot : snapshot.filter((job) => isFresh(job, freshHours));
  }, [snapshot, freshHours]);

  if (snapshot === null) return <p className="text-sm text-muted" role="status">Loading jobs…</p>;
  if (snapshot === "error") {
    return (
      <p className="text-sm text-slate-700" role="alert">
        Could not load jobs.{" "}
        <button type="button" className="font-medium text-accent underline" onClick={() => {
          setSnapshot(null);
          setAttempt((current) => current + 1);
        }}>Retry</button>
      </p>
    );
  }
  return <JobFilters jobs={jobs} defaultEntryOnly={defaultEntryOnly} emptyMessage={freshHours === undefined ? undefined : "No fresh jobs in this time window."} />;
}
