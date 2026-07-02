import type { Job, JobFilterState } from "@/lib/types";

export const ENTRY_LEVELS = ["Intern", "New Grad", "Entry", "Early Career"];

export const DEFAULT_FILTERS: JobFilterState = {
  query: "",
  category: "all",
  level: "all",
  companyGroup: "all",
  remoteType: "all",
  visaSignal: "all",
  excludeCitizenship: false,
  excludeClearance: false,
  sort: "first_seen_desc"
};

export function isFresh(job: Job, hours: number): boolean {
  const seenAt = Date.parse(job.first_seen);
  if (Number.isNaN(seenAt)) {
    return false;
  }
  return Date.now() - seenAt <= hours * 60 * 60 * 1000;
}

export function isEntryLevel(job: Job): boolean {
  return ENTRY_LEVELS.includes(job.level);
}

export function filterJobs(jobs: Job[], filters: JobFilterState): Job[] {
  const query = filters.query.trim().toLowerCase();

  const filtered = jobs.filter((job) => {
    const haystack = `${job.company} ${job.title} ${job.location_raw}`.toLowerCase();
    if (query && !haystack.includes(query)) return false;
    if (filters.category !== "all" && job.category !== filters.category) return false;
    if (filters.level !== "all" && job.level !== filters.level) return false;
    if (filters.companyGroup !== "all" && job.company_group !== filters.companyGroup) return false;
    if (filters.remoteType !== "all" && job.remote_type !== filters.remoteType) return false;
    if (filters.visaSignal !== "all" && job.visa_signal !== filters.visaSignal) return false;
    if (filters.excludeCitizenship && job.requires_citizenship) return false;
    if (filters.excludeClearance && job.requires_clearance) return false;
    return true;
  });

  return sortJobs(filtered, filters.sort);
}

export function sortJobs(jobs: Job[], sort: JobFilterState["sort"]): Job[] {
  return [...jobs].sort((a, b) => {
    if (sort === "company_asc") {
      return a.company.localeCompare(b.company) || a.title.localeCompare(b.title);
    }
    if (sort === "title_asc") {
      return a.title.localeCompare(b.title) || a.company.localeCompare(b.company);
    }
    return Date.parse(b.first_seen) - Date.parse(a.first_seen);
  });
}

export function uniqueValues(jobs: Job[], key: keyof Job): string[] {
  return Array.from(new Set(jobs.map((job) => String(job[key])).filter(Boolean))).sort();
}
