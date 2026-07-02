import Link from "next/link";
import { ArrowRight, Building2, Clock3, Landmark, ListChecks } from "lucide-react";
import { JobStats } from "@/components/JobStats";
import { getLastUpdated } from "@/lib/jobs";

const actions = [
  { href: "/jobs", label: "Browse Jobs", icon: ListChecks },
  { href: "/fresh", label: "Fresh Jobs", icon: Clock3 },
  { href: "/big-tech", label: "Big Tech Early Career", icon: Landmark },
  { href: "/companies", label: "Companies", icon: Building2 }
];

export default function HomePage() {
  const stats = getLastUpdated();

  return (
    <div className="grid gap-8">
      <section className="grid gap-6 py-8 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-accent">
            Curated tracker
          </p>
          <h1 className="mt-3 max-w-4xl text-4xl font-semibold leading-tight text-ink sm:text-5xl">
            US Tech Entry Jobs Tracker
          </h1>
          <p className="mt-4 max-w-2xl text-lg leading-8 text-slate-600">
            Curated U.S. SDE, DS, ML, and Data job links for interns, new grads, and
            early-career candidates.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            {actions.map((action) => {
              const Icon = action.icon;
              return (
                <Link
                  key={action.href}
                  href={action.href}
                  className="inline-flex items-center gap-2 rounded-md bg-white px-4 py-2.5 text-sm font-semibold text-slate-800 shadow-subtle ring-1 ring-line hover:bg-slate-50"
                >
                  <Icon aria-hidden="true" className="h-4 w-4" />
                  {action.label}
                  <ArrowRight aria-hidden="true" className="h-4 w-4" />
                </Link>
              );
            })}
          </div>
        </div>
        <div className="rounded-lg border border-line bg-white p-5 shadow-subtle">
          <div className="h-56 rounded-md border border-slate-200 bg-[linear-gradient(90deg,#e2e8f0_1px,transparent_1px),linear-gradient(#e2e8f0_1px,transparent_1px)] bg-[size:28px_28px] p-4">
            <div className="grid h-full content-between">
              <div className="flex items-center justify-between">
                <span className="rounded-md bg-teal-700 px-3 py-1 text-xs font-semibold text-white">
                  Active links
                </span>
                <span className="rounded-md bg-white px-3 py-1 text-xs font-medium text-slate-700 shadow-subtle">
                  JSON powered
                </span>
              </div>
              <div className="grid gap-2">
                <div className="h-3 w-10/12 rounded bg-slate-300" />
                <div className="h-3 w-8/12 rounded bg-slate-200" />
                <div className="h-3 w-9/12 rounded bg-slate-200" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <JobStats stats={stats} />

      <section className="rounded-lg border border-line bg-white p-4 text-sm leading-6 text-slate-600 shadow-subtle">
        We link to official career pages and public job postings. We are not affiliated with
        these companies. Job availability can change quickly.
      </section>
    </div>
  );
}
