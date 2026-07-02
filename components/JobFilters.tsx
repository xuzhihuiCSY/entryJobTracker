"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { DEFAULT_FILTERS, filterJobs, uniqueValues } from "@/lib/filters";
import type { Job, JobFilterState, JobSort } from "@/lib/types";
import { JobCard } from "@/components/JobCard";

type JobFiltersProps = {
  jobs: Job[];
  initialFilters?: Partial<JobFilterState>;
  emptyMessage?: string;
};

const PAGE_SIZE_OPTIONS = [25, 50, 100];

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

function paginationWindow(currentPage: number, totalPages: number): number[] {
  const size = Math.min(5, totalPages);
  let start = Math.max(1, currentPage - Math.floor(size / 2));
  const end = Math.min(totalPages, start + size - 1);
  start = Math.max(1, end - size + 1);
  return Array.from({ length: end - start + 1 }, (_, index) => start + index);
}

function PaginationControls({
  page,
  totalPages,
  onPageChange
}: {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}) {
  const pages = paginationWindow(page, totalPages);

  return (
    <nav className="flex flex-wrap items-center gap-1" aria-label="Pagination">
      <button
        type="button"
        onClick={() => onPageChange(Math.max(1, page - 1))}
        disabled={page === 1}
        className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-line bg-white text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-45"
        aria-label="Previous page"
      >
        <ChevronLeft aria-hidden="true" className="h-4 w-4" />
      </button>
      {pages[0] > 1 ? (
        <>
          <button
            type="button"
            onClick={() => onPageChange(1)}
            className="h-9 min-w-9 rounded-md border border-line bg-white px-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            1
          </button>
          {pages[0] > 2 ? <span className="px-2 text-sm text-muted">...</span> : null}
        </>
      ) : null}
      {pages.map((pageNumber) => (
        <button
          key={pageNumber}
          type="button"
          onClick={() => onPageChange(pageNumber)}
          className={`h-9 min-w-9 rounded-md px-3 text-sm font-medium ${
            pageNumber === page
              ? "bg-slate-900 text-white"
              : "border border-line bg-white text-slate-700 hover:bg-slate-50"
          }`}
          aria-current={pageNumber === page ? "page" : undefined}
        >
          {pageNumber}
        </button>
      ))}
      {pages[pages.length - 1] < totalPages ? (
        <>
          {pages[pages.length - 1] < totalPages - 1 ? (
            <span className="px-2 text-sm text-muted">...</span>
          ) : null}
          <button
            type="button"
            onClick={() => onPageChange(totalPages)}
            className="h-9 min-w-9 rounded-md border border-line bg-white px-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            {totalPages}
          </button>
        </>
      ) : null}
      <button
        type="button"
        onClick={() => onPageChange(Math.min(totalPages, page + 1))}
        disabled={page === totalPages}
        className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-line bg-white text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-45"
        aria-label="Next page"
      >
        <ChevronRight aria-hidden="true" className="h-4 w-4" />
      </button>
    </nav>
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
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

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
  const totalPages = Math.max(1, Math.ceil(visibleJobs.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const pageStart = (currentPage - 1) * pageSize;
  const pageJobs = visibleJobs.slice(pageStart, pageStart + pageSize);
  const showingStart = visibleJobs.length === 0 ? 0 : pageStart + 1;
  const showingEnd = Math.min(pageStart + pageSize, visibleJobs.length);

  useEffect(() => {
    setPage(1);
  }, [filters, jobs, pageSize]);

  useEffect(() => {
    setPage((current) => Math.min(current, totalPages));
  }, [totalPages]);

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

      <div className="flex flex-col gap-3 rounded-lg border border-line bg-white p-3 shadow-subtle sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-slate-700">
            Showing {showingStart}-{showingEnd} of {visibleJobs.length} jobs
          </p>
          <p className="mt-1 text-xs text-muted">
            Page {currentPage} of {totalPages}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="flex items-center gap-2 text-sm font-medium text-slate-700">
            Per page
            <select
              value={pageSize}
              onChange={(event) => setPageSize(Number(event.target.value))}
              className="h-9 rounded-md border border-line bg-white px-2 text-sm text-ink outline-none focus:border-accent focus:ring-2 focus:ring-teal-100"
            >
              {PAGE_SIZE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={() => setFilters({ ...DEFAULT_FILTERS, ...initialFilters })}
            className="h-9 rounded-md border border-line bg-white px-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Reset
          </button>
        </div>
      </div>

      <section className="grid gap-3">
        {pageJobs.length > 0 ? (
          pageJobs.map((job) => <JobCard key={job.id} job={job} />)
        ) : (
          <div className="rounded-lg border border-dashed border-line bg-white p-8 text-center text-sm text-muted">
            {emptyMessage}
          </div>
        )}
      </section>

      {visibleJobs.length > pageSize ? (
        <div className="flex flex-col gap-3 rounded-lg border border-line bg-white p-3 shadow-subtle sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-muted">
            Showing {showingStart}-{showingEnd} of {visibleJobs.length}
          </p>
          <PaginationControls page={currentPage} totalPages={totalPages} onPageChange={setPage} />
        </div>
      ) : null}
    </div>
  );
}
