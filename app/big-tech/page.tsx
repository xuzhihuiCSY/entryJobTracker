import { JobFilters } from "@/components/JobFilters";
import { getBigTechEntryJobs } from "@/lib/jobs";

export default function BigTechPage() {
  const jobs = getBigTechEntryJobs();

  return (
    <div className="grid gap-5">
      <div>
        <h1 className="text-3xl font-semibold text-ink">Big Tech Early Career</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
          U.S.-based Big Tech roles classified as Intern, New Grad, Entry, or Early Career.
        </p>
      </div>
      <JobFilters
        jobs={jobs}
        emptyMessage="No Big Tech early-career roles are currently available in the data file."
      />
    </div>
  );
}
