import { AlertTriangle, ExternalLink, MapPin } from "lucide-react";
import { CompanyBadge } from "@/components/CompanyBadge";
import { JobDescription } from "@/components/JobDescription";
import type { Job } from "@/lib/types";

type JobCardProps = {
  job: Job;
  isApplied?: boolean;
  onAppliedChange?: (jobId: string, isApplied: boolean) => void;
  markOnApplyClick?: boolean;
};

function relativeTime(value: string): string {
  const date = Date.parse(value);
  if (Number.isNaN(date)) return "first seen unknown";
  const seconds = Math.max(1, Math.floor((Date.now() - date) / 1000));
  const units: Array<[Intl.RelativeTimeFormatUnit, number]> = [
    ["day", 86400],
    ["hour", 3600],
    ["minute", 60]
  ];
  const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
  for (const [unit, unitSeconds] of units) {
    if (seconds >= unitSeconds) {
      return rtf.format(-Math.floor(seconds / unitSeconds), unit);
    }
  }
  return "just now";
}

function visaLabel(value: string): string {
  if (value === "strong") return "Sponsorship stated";
  if (value === "not_likely") return "No sponsorship stated";
  if (value === "conditional") return "Sponsorship: conditional";
  return "Sponsorship: unknown";
}

function sourceLabel(value: string): string {
  const labels: Record<string, string> = {
    ashby: "Ashby",
    greenhouse: "Greenhouse",
    lever: "Lever",
    custom_amazon: "Amazon Jobs",
    custom_apple: "Apple Jobs",
    custom_google: "Google Careers",
    custom_meta_jobsyn: "Meta Careers",
    custom_microsoft: "Microsoft Careers",
    custom_nvidia: "NVIDIA Careers"
  };
  return labels[value] ?? value.replaceAll("_", " ");
}

export function JobCard({
  job,
  isApplied = false,
  onAppliedChange,
  markOnApplyClick = false
}: JobCardProps) {
  const hasMultipleLocations = Boolean(job.location_count && job.location_count > 1);
  const locationText = hasMultipleLocations
    ? `${job.location_count} locations`
    : job.location_raw || "Location not listed";

  return (
    <article className="rounded-lg border border-line bg-white p-4 shadow-subtle">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <CompanyBadge group={job.company_group} />
            <span className="rounded-md bg-teal-50 px-2 py-1 text-xs font-medium text-teal-800">
              {job.category}
            </span>
            <span className="rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-800">
              {job.level}
            </span>
          </div>
          <h2 className="mt-3 text-lg font-semibold leading-snug text-ink">{job.title}</h2>
          <p className="mt-1 text-sm font-medium text-slate-700">{job.company}</p>
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted">
            <span className="inline-flex items-center gap-1">
              <MapPin aria-hidden="true" className="h-4 w-4" />
              {hasMultipleLocations ? "Locations: " : ""}
              {locationText}
            </span>
            <span className="capitalize">{job.remote_type}</span>
            <span>{relativeTime(job.first_seen)}</span>
            <span>{sourceLabel(job.source_platform)}</span>
          </div>
          {hasMultipleLocations && job.locations?.length ? (
            <details className="mt-2 text-sm text-muted">
              <summary className="cursor-pointer text-accent hover:text-teal-800">View locations</summary>
              <div className="mt-2 flex flex-wrap gap-2">
                {job.locations.map((location) => (
                  <span key={location} className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-700">
                    {location}
                  </span>
                ))}
              </div>
            </details>
          ) : null}
          {job.description_snippet ? (
            <p className="mt-3 line-clamp-2 text-sm leading-6 text-slate-600">
              {job.description_snippet}
            </p>
          ) : null}
          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            {job.phd_requirement && job.phd_requirement !== "unknown" ? (
              <span
                title={job.phd_evidence}
                className={`rounded-md px-2 py-1 ${
                  job.phd_requirement === "required"
                    ? "bg-amber-50 text-amber-800"
                    : "bg-slate-100 text-slate-700"
                }`}
              >
                {job.phd_requirement === "required"
                  ? "PhD required"
                  : job.phd_requirement === "preferred"
                    ? "PhD preferred"
                    : "PhD optional / alternative accepted"}
              </span>
            ) : null}
            <span title={job.visa_evidence} className="rounded-md bg-slate-100 px-2 py-1 text-slate-700">
              {visaLabel(job.visa_signal)}
            </span>
            <label
              className={`inline-flex cursor-pointer items-center gap-1.5 rounded-md px-2 py-1 font-medium ${
                isApplied ? "bg-emerald-50 text-emerald-800" : "bg-slate-100 text-slate-700"
              }`}
            >
              <input
                type="checkbox"
                checked={isApplied}
                onChange={(event) => onAppliedChange?.(job.id, event.target.checked)}
                className="h-3.5 w-3.5 rounded border-slate-300 text-accent focus:ring-accent"
              />
              {isApplied ? "Already applied" : "Mark applied"}
            </label>
            {job.requires_citizenship ? (
              <span className="inline-flex items-center gap-1 rounded-md bg-amber-50 px-2 py-1 font-medium text-amber-800">
                <AlertTriangle aria-hidden="true" className="h-3.5 w-3.5" />
                Citizenship required
              </span>
            ) : null}
            {job.requires_clearance ? (
              <span className="inline-flex items-center gap-1 rounded-md bg-rose-50 px-2 py-1 font-medium text-rose-800">
                <AlertTriangle aria-hidden="true" className="h-3.5 w-3.5" />
                Clearance required
              </span>
            ) : null}
          </div>
          {job.phd_evidence ? (
            <details className="mt-2 text-xs leading-5 text-muted">
              <summary className="cursor-pointer text-accent hover:text-teal-800">Education requirement evidence</summary>
              <p className="mt-1 max-w-3xl">{job.phd_evidence}</p>
            </details>
          ) : null}
          {job.visa_evidence || job.citizenship_evidence || job.clearance_evidence ? (
            <details className="mt-2 text-xs leading-5 text-muted">
              <summary className="cursor-pointer text-accent hover:text-teal-800">Work authorization evidence</summary>
              {[job.visa_evidence, job.citizenship_evidence, job.clearance_evidence].filter(Boolean).map((evidence, index) => <p key={index} className="mt-1 max-w-3xl">{evidence}</p>)}
            </details>
          ) : null}
          <JobDescription job={job} />
        </div>
        <a
          href={job.apply_url}
          target="_blank"
          rel="noreferrer"
          onClick={() => {
            if (markOnApplyClick) onAppliedChange?.(job.id, true);
          }}
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-800"
        >
          Apply
          <ExternalLink aria-hidden="true" className="h-4 w-4" />
        </a>
      </div>
    </article>
  );
}
