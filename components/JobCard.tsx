import { AlertTriangle, ExternalLink, MapPin } from "lucide-react";
import { CompanyBadge } from "@/components/CompanyBadge";
import type { Job } from "@/lib/types";

type JobCardProps = {
  job: Job;
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
  if (value === "strong") return "Visa signal: strong";
  if (value === "not_likely") return "Visa: not likely";
  return "Visa: unknown";
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

export function JobCard({ job }: JobCardProps) {
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
              {job.location_raw || "Location not listed"}
            </span>
            <span className="capitalize">{job.remote_type}</span>
            <span>{relativeTime(job.first_seen)}</span>
            <span>{sourceLabel(job.source_platform)}</span>
          </div>
          {job.description_snippet ? (
            <p className="mt-3 line-clamp-2 text-sm leading-6 text-slate-600">
              {job.description_snippet}
            </p>
          ) : null}
          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            <span className="rounded-md bg-slate-100 px-2 py-1 text-slate-700">
              {visaLabel(job.visa_signal)}
            </span>
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
        </div>
        <a
          href={job.apply_url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-teal-800"
        >
          Apply
          <ExternalLink aria-hidden="true" className="h-4 w-4" />
        </a>
      </div>
    </article>
  );
}
