"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { DEFAULT_FILTERS, filterJobs, isEntryLevel, uniqueValues } from "@/lib/filters";
import type { Job, JobFilterState, JobSort } from "@/lib/types";
import { JobCard } from "@/components/JobCard";

type JobFiltersProps = {
  jobs: Job[];
  initialFilters?: Partial<JobFilterState>;
  emptyMessage?: string;
  defaultEntryOnly?: boolean;
};

const PAGE_SIZE_OPTIONS = [25, 50, 100];
const APPLIED_STORAGE_KEY = "entryJobTracker.appliedJobIds";
const MARK_ON_CLICK_STORAGE_KEY = "entryJobTracker.markOnApplyClick";

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
  emptyMessage = "No matching jobs found.",
  defaultEntryOnly = false
}: JobFiltersProps) {
  const [filters, setFilters] = useState<JobFilterState>({
    ...DEFAULT_FILTERS,
    ...initialFilters
  });
  const [entryOnly, setEntryOnly] = useState(defaultEntryOnly);
  const [markOnApplyClick, setMarkOnApplyClick] = useState(false);
  const [hideApplied, setHideApplied] = useState(false);
  const [appliedJobIds, setAppliedJobIds] = useState<Set<string>>(new Set());
  const [appliedLoaded, setAppliedLoaded] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const options = useMemo(
    () => ({
      companies: uniqueValues(jobs, "company"),
      categories: uniqueValues(jobs, "category"),
      levels: uniqueValues(jobs, "level")
    }),
    [jobs]
  );

  const baseVisibleJobs = useMemo(() => filterJobs(jobs, filters), [jobs, filters]);
  const visibleJobs = useMemo(() => {
    const levelFilteredJobs =
      entryOnly && filters.level === "all"
        ? baseVisibleJobs.filter((job) => isEntryLevel(job))
        : baseVisibleJobs;
    if (!hideApplied) return levelFilteredJobs;
    return levelFilteredJobs.filter((job) => !appliedJobIds.has(job.id));
  }, [appliedJobIds, baseVisibleJobs, entryOnly, filters.level, hideApplied]);
  const totalPages = Math.max(1, Math.ceil(visibleJobs.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const pageStart = (currentPage - 1) * pageSize;
  const pageJobs = visibleJobs.slice(pageStart, pageStart + pageSize);
  const showingStart = visibleJobs.length === 0 ? 0 : pageStart + 1;
  const showingEnd = Math.min(pageStart + pageSize, visibleJobs.length);

  useEffect(() => {
    setPage(1);
  }, [filters, jobs, pageSize, entryOnly, hideApplied]);

  useEffect(() => {
    setPage((current) => Math.min(current, totalPages));
  }, [totalPages]);

  useEffect(() => {
    try {
      const storedValue = window.localStorage.getItem(APPLIED_STORAGE_KEY);
      const parsedValue = storedValue ? JSON.parse(storedValue) : [];
      if (Array.isArray(parsedValue)) {
        setAppliedJobIds(new Set(parsedValue.filter((value) => typeof value === "string")));
      }
      setMarkOnApplyClick(window.localStorage.getItem(MARK_ON_CLICK_STORAGE_KEY) === "true");
    } catch {
      setAppliedJobIds(new Set());
      setMarkOnApplyClick(false);
    } finally {
      setAppliedLoaded(true);
    }
  }, []);

  useEffect(() => {
    if (!appliedLoaded) return;
    window.localStorage.setItem(APPLIED_STORAGE_KEY, JSON.stringify(Array.from(appliedJobIds)));
  }, [appliedJobIds, appliedLoaded]);

  useEffect(() => {
    if (!appliedLoaded) return;
    window.localStorage.setItem(MARK_ON_CLICK_STORAGE_KEY, String(markOnApplyClick));
  }, [appliedLoaded, markOnApplyClick]);

  function handleAppliedChange(jobId: string, isApplied: boolean) {
    setAppliedJobIds((current) => {
      const next = new Set(current);
      if (isApplied) {
        next.add(jobId);
      } else {
        next.delete(jobId);
      }
      return next;
    });
  }

  return (
    <div className="grid gap-5">
      <section className="rounded-lg border border-line bg-white p-4 shadow-subtle">
        <div className="mb-4 flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-semibold text-ink">Level focus</p>
            <p className="mt-1 text-xs text-muted">
              Entry focus includes Intern, New Grad, Entry, and Early Career roles.
            </p>
          </div>
          <div className="inline-flex w-fit rounded-md border border-line bg-slate-50 p-1">
            <button
              type="button"
              onClick={() => setEntryOnly(true)}
              className={`rounded px-3 py-1.5 text-sm font-medium ${
                entryOnly ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-950"
              }`}
            >
              Entry focus
            </button>
            <button
              type="button"
              onClick={() => setEntryOnly(false)}
              className={`rounded px-3 py-1.5 text-sm font-medium ${
                !entryOnly ? "bg-slate-900 text-white" : "text-slate-600 hover:text-slate-950"
              }`}
            >
              All levels
            </button>
          </div>
        </div>
        <div className="mb-4 flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-semibold text-ink">Application status</p>
            <p className="mt-1 text-xs text-muted">
              Applied jobs are saved in this browser.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label className="inline-flex w-fit cursor-pointer items-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
              <input
                type="checkbox"
                checked={markOnApplyClick}
                onChange={(event) => setMarkOnApplyClick(event.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-accent focus:ring-accent"
              />
              Mark on click
            </label>
            <label className="inline-flex w-fit cursor-pointer items-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
              <input
                type="checkbox"
                checked={hideApplied}
                onChange={(event) => setHideApplied(event.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-accent focus:ring-accent"
              />
              Hide already applied
              {appliedJobIds.size > 0 ? (
                <span className="rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-600">
                  {appliedJobIds.size}
                </span>
              ) : null}
            </label>
          </div>
        </div>
        <div className="grid gap-3 lg:grid-cols-[minmax(18rem,1.4fr)_repeat(4,minmax(10rem,1fr))]">
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
            label="Company"
            value={filters.company}
            options={options.companies}
            onChange={(company) => setFilters((current) => ({ ...current, company }))}
          />
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
              <option value="entry_first">Entry roles first</option>
              <option value="company_asc">Company</option>
              <option value="title_asc">Title</option>
            </select>
          </label>
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
            onClick={() => {
              setFilters({ ...DEFAULT_FILTERS, ...initialFilters });
              setEntryOnly(defaultEntryOnly);
              setHideApplied(false);
            }}
            className="h-9 rounded-md border border-line bg-white px-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Reset
          </button>
        </div>
      </div>

      <section className="grid gap-3">
        {pageJobs.length > 0 ? (
          pageJobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              isApplied={appliedJobIds.has(job.id)}
              onAppliedChange={handleAppliedChange}
              markOnApplyClick={markOnApplyClick}
            />
          ))
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
