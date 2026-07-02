import { JobFilters } from "@/components/JobFilters";
import { getJobs } from "@/lib/jobs";

export default function JobsPage() {
  const jobs = getJobs();

  return (
    <div className="grid gap-5">
      <div>
        <h1 className="text-3xl font-semibold text-ink">All Jobs</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
          Search and filter active public postings collected from configured company sources.
        </p>
      </div>
      <JobFilters jobs={jobs} />
    </div>
  );
}
