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
  | "Security"
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
export type VisaSignal = "strong" | "not_likely" | "conditional" | "unknown";
export type VisaFilter = "all" | "strong" | "exclude_no_sponsorship" | "not_likely" | "conditional" | "unknown";
export type PhDRequirement = "required" | "preferred" | "optional" | "unknown";
export type PhDFilter = "exclude_required" | "all" | "required";

export type Job = {
  id: string;
  company: string;
  company_slug: string;
  company_group: CompanyGroup | string;
  title: string;
  category: JobCategory | string;
  level: JobLevel | string;
  phd_requirement?: PhDRequirement;
  phd_evidence?: string;
  location_raw: string;
  locations?: string[];
  location_count?: number;
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
  citizenship_evidence?: string;
  requires_clearance: boolean;
  clearance_evidence?: string;
  visa_signal: VisaSignal | string;
  visa_evidence?: string;
  description_status?: "full" | "summary" | "missing";
  description_path?: string;
  description_fetched_at?: string;
  description_snippet: string;
};

export type Company = {
  name: string;
  slug: string;
  company_group: CompanyGroup | string;
  career_url: string;
  source_type: string;
  enabled?: boolean;
  sync_priority?: number;
  sync_status?: "success" | "failed" | "disabled" | "unknown";
  last_attempted?: string;
  last_error?: string;
  full_description_count?: number;
  active_job_count: number;
  last_synced: string;
};

export type LastUpdated = {
  last_updated: string;
  total_jobs: number;
  big_tech_jobs: number;
  fresh_24h_jobs: number;
  sources_synced: number;
  sources_attempted?: number;
  sources_failed?: number;
  failed_companies?: string[];
  full_description_jobs?: number;
  last_attempted?: string;
  sync_status?: "success" | "partial" | "failed";
};

export type JobHistoryPoint = {
  date: string;
  recorded_at: string;
  total_jobs: number;
  companies_with_jobs: number;
  failed_sources?: number;
};

export type JobSort = "first_seen_desc" | "entry_first" | "company_asc" | "title_asc";

export type JobFilterState = {
  query: string;
  company: string;
  category: string;
  level: string;
  phd: PhDFilter;
  visa: VisaFilter;
  hideCitizenshipRequired: boolean;
  hideClearanceRequired: boolean;
  sort: JobSort;
};
