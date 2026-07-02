export type CompanyGroup = "big_tech" | "startup" | "public" | "private" | "other";

export type JobCategory =
  | "SDE"
  | "DS"
  | "ML"
  | "Data Engineer"
  | "AI Engineer"
  | "Backend"
  | "Frontend"
  | "Full Stack"
  | "Cloud"
  | "DevOps"
  | "Quant"
  | "Other";

export type JobLevel =
  | "Intern"
  | "New Grad"
  | "Entry"
  | "Early Career"
  | "Mid"
  | "Senior"
  | "Staff"
  | "Manager"
  | "Unknown";

export type RemoteType = "onsite" | "hybrid" | "remote" | "unknown";
export type VisaSignal = "strong" | "not_likely" | "unknown";

export type Job = {
  id: string;
  company: string;
  company_slug: string;
  company_group: CompanyGroup | string;
  title: string;
  category: JobCategory | string;
  level: JobLevel | string;
  location_raw: string;
  city: string;
  state: string;
  country: string;
  is_us_based: boolean;
  remote_type: RemoteType | string;
  apply_url: string;
  source_url: string;
  source_platform: string;
  first_seen: string;
  last_checked: string;
  requires_citizenship: boolean;
  requires_clearance: boolean;
  visa_signal: VisaSignal | string;
  description_snippet: string;
};

export type Company = {
  name: string;
  slug: string;
  company_group: CompanyGroup | string;
  career_url: string;
  source_type: string;
  active_job_count: number;
  last_synced: string;
};

export type LastUpdated = {
  last_updated: string;
  total_jobs: number;
  big_tech_jobs: number;
  fresh_24h_jobs: number;
  sources_synced: number;
};

export type JobSort = "first_seen_desc" | "entry_first" | "company_asc" | "title_asc";

export type JobFilterState = {
  query: string;
  company: string;
  category: string;
  level: string;
  sort: JobSort;
};
