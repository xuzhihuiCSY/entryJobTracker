import type { Metadata } from "next";
import Link from "next/link";
import { CheckCircle2, Clock3, ExternalLink, ShieldCheck } from "lucide-react";
import { LocalDateTime } from "@/components/LocalDateTime";
import { getLastUpdated } from "@/lib/jobs";

export const metadata: Metadata = {
  title: "Trust",
  description:
    "How US Tech Entry Jobs Tracker collects public job postings, preserves first-seen timestamps, and links candidates to official career pages.",
  alternates: {
    canonical: "/trust"
  }
};

const practices = [
  {
    title: "Official apply links",
    description:
      "Job cards link to company career pages or official public posting systems whenever an official URL is available.",
    icon: ExternalLink
  },
  {
    title: "Preserved first-seen time",
    description:
      "Fresh jobs use a stored first_seen timestamp, so older roles are not treated as new on every sync.",
    icon: Clock3
  },
  {
    title: "Classification is transparent",
    description:
      "Roles are tagged by title and posting text into categories such as SDE, Frontend, ML, Data, Intern, New Grad, Entry, Mid, Senior, and Manager.",
    icon: CheckCircle2
  },
  {
    title: "No affiliation claims",
    description:
      "This site is an independent tracker and is not affiliated with Amazon, Google, Microsoft, Meta, Apple, NVIDIA, or other listed companies.",
    icon: ShieldCheck
  }
];

export default function TrustPage() {
  const stats = getLastUpdated();

  return (
    <div className="grid gap-6">
      <section className="grid gap-3">
        <p className="text-sm font-semibold uppercase tracking-wide text-accent">Trust</p>
        <h1 className="max-w-3xl text-3xl font-semibold leading-tight text-ink">
          How this job tracker keeps listings useful and verifiable
        </h1>
        <p className="max-w-3xl text-sm leading-6 text-muted">
          US Tech Entry Jobs Tracker collects public postings, normalizes them into a searchable
          static dataset, and sends candidates back to official application pages.
        </p>
      </section>

      <section className="grid gap-3 sm:grid-cols-2">
        {practices.map((item) => {
          const Icon = item.icon;
          return (
            <article key={item.title} className="rounded-lg border border-line bg-white p-4 shadow-subtle">
              <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-md bg-slate-100 text-slate-700">
                <Icon aria-hidden="true" className="h-5 w-5" />
              </div>
              <h2 className="text-base font-semibold text-ink">{item.title}</h2>
              <p className="mt-2 text-sm leading-6 text-muted">{item.description}</p>
            </article>
          );
        })}
      </section>

      <section className="rounded-lg border border-line bg-white p-4 shadow-subtle">
        <h2 className="text-lg font-semibold text-ink">Current sync status</h2>
        <dl className="mt-4 grid gap-3 sm:grid-cols-3">
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Last updated
            </dt>
            <dd className="mt-1 text-sm text-slate-700">
              <LocalDateTime value={stats.last_updated} />
            </dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Active jobs
            </dt>
            <dd className="mt-1 text-sm text-slate-700">{stats.total_jobs}</dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Sources synced
            </dt>
            <dd className="mt-1 text-sm text-slate-700">{stats.sources_synced}</dd>
          </div>
        </dl>
      </section>

      <section className="rounded-lg border border-line bg-white p-4 text-sm leading-6 text-muted shadow-subtle">
        Job postings can expire or change between syncs. Use the official apply link as the source
        of truth before applying. To inspect currently tracked companies, visit{" "}
        <Link href="/companies" className="font-medium text-accent hover:text-teal-800">
          Companies
        </Link>
        .
      </section>
    </div>
  );
}
