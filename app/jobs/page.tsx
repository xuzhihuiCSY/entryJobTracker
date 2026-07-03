import type { Metadata } from "next";
import { JobFilters } from "@/components/JobFilters";
import { getJobs } from "@/lib/jobs";

export const metadata: Metadata = {
  title: "Entry-Focused Tech Jobs",
  description:
    "Browse U.S. intern, new grad, entry-level, and early-career software, data, and ML job postings.",
  alternates: {
    canonical: "/jobs"
  }
};

export default function JobsPage() {
  const jobs = getJobs();

  return (
    <div className="grid gap-5">
      <div>
        <h1 className="text-3xl font-semibold text-ink">Entry-Focused Jobs</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
          Starts with intern, new grad, entry, and early-career roles. Switch to all levels when
          you want to browse the full active dataset.
        </p>
      </div>
      <JobFilters jobs={jobs} defaultEntryOnly />
    </div>
  );
}
