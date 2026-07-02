"use client";

import { useMemo, useState } from "react";
import { Search } from "lucide-react";
import { DEFAULT_FILTERS, filterJobs, uniqueValues } from "@/lib/filters";
import type { Job, JobFilterState, JobSort } from "@/lib/types";
import { JobCard } from "@/components/JobCard";

type JobFiltersProps = {
  jobs: Job[];
  initialFilters?: Partial<JobFilterState>;
  emptyMessage?: string;
};

function SelectField({
  label,
  value,
  options,
  onChange
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-1 text-sm font-medium text-slate-700">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 rounded-md border border-line bg-white px-3 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-teal-100"
      >
        <option value="all">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option.replaceAll("_", " ")}
          </option>
        ))}
      </select>
    </label>
  );
}

export function JobFilters({
  jobs,
  initialFilters,
  emptyMessage = "No matching jobs found."
}: JobFiltersProps) {
  const [filters, setFilters] = useState<JobFilterState>({
    ...DEFAULT_FILTERS,
    ...initialFilters
  });

  const options = useMemo(
    () => ({
      categories: uniqueValues(jobs, "category"),
      levels: uniqueValues(jobs, "level"),
      companyGroups: uniqueValues(jobs, "company_group"),
      remoteTypes: uniqueValues(jobs, "remote_type"),
      visaSignals: uniqueValues(jobs, "visa_signal")
    }),
    [jobs]
  );

  const visibleJobs = useMemo(() => filterJobs(jobs, filters), [jobs, filters]);

  return (
    <div className="grid gap-5">
      <section className="rounded-lg border border-line bg-white p-4 shadow-subtle">
        <div className="grid gap-3 lg:grid-cols-[minmax(16rem,1.4fr)_repeat(3,minmax(10rem,1fr))]">
          <label className="grid gap-1 text-sm font-medium text-slate-700">
            Search
            <span className="relative">
              <Search
                aria-hidden="true"
                className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
              />
              <input
                value={filters.query}
                onChange={(event) =>
                  setFilters((current) => ({ ...current, query: event.target.value }))
                }
                placeholder="Company, title, or location"
                className="h-10 w-full rounded-md border border-line bg-white pl-9 pr-3 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-teal-100"
              />
            </span>
          </label>
          <SelectField
            label="Category"
            value={filters.category}
            options={options.categories}
            onChange={(category) => setFilters((current) => ({ ...current, category }))}
          />
          <SelectField
            label="Level"
            value={filters.level}
            options={options.levels}
            onChange={(level) => setFilters((current) => ({ ...current, level }))}
          />
          <SelectField
            label="Company group"
            value={filters.companyGroup}
            options={options.companyGroups}
            onChange={(companyGroup) =>
              setFilters((current) => ({ ...current, companyGroup }))
            }
          />
          <SelectField
            label="Remote"
            value={filters.remoteType}
            options={options.remoteTypes}
            onChange={(remoteType) => setFilters((current) => ({ ...current, remoteType }))}
          />
          <SelectField
            label="Visa"
            value={filters.visaSignal}
            options={options.visaSignals}
            onChange={(visaSignal) => setFilters((current) => ({ ...current, visaSignal }))}
          />
          <label className="grid gap-1 text-sm font-medium text-slate-700">
            Sort
            <select
              value={filters.sort}
              onChange={(event) =>
                setFilters((current) => ({ ...current, sort: event.target.value as JobSort }))
              }
              className="h-10 rounded-md border border-line bg-white px-3 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-teal-100"
            >
              <option value="first_seen_desc">First seen newest</option>
              <option value="company_asc">Company</option>
              <option value="title_asc">Title</option>
            </select>
          </label>
          <div className="flex flex-col justify-end gap-2 text-sm text-slate-700">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={filters.excludeCitizenship}
                onChange={(event) =>
                  setFilters((current) => ({
                    ...current,
                    excludeCitizenship: event.target.checked
                  }))
                }
                className="h-4 w-4 rounded border-line text-accent"
              />
              Exclude citizenship required
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={filters.excludeClearance}
                onChange={(event) =>
                  setFilters((current) => ({
                    ...current,
                    excludeClearance: event.target.checked
                  }))
                }
                className="h-4 w-4 rounded border-line text-accent"
              />
              Exclude clearance required
            </label>
          </div>
        </div>
      </section>

      <div className="flex items-center justify-between gap-3">
        <p className="text-sm font-medium text-slate-700">{visibleJobs.length} jobs</p>
        <button
          type="button"
          onClick={() => setFilters({ ...DEFAULT_FILTERS, ...initialFilters })}
          className="rounded-md border border-line bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Reset
        </button>
      </div>

      <section className="grid gap-3">
        {visibleJobs.length > 0 ? (
          visibleJobs.map((job) => <JobCard key={job.id} job={job} />)
        ) : (
          <div className="rounded-lg border border-dashed border-line bg-white p-8 text-center text-sm text-muted">
            {emptyMessage}
          </div>
        )}
      </section>
    </div>
  );
}
