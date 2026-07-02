import { ExternalLink } from "lucide-react";
import { CompanyBadge } from "@/components/CompanyBadge";
import { formatDateTime, getCompanies } from "@/lib/jobs";

export default function CompaniesPage() {
  const companies = getCompanies();

  return (
    <div className="grid gap-5">
      <div>
        <h1 className="text-3xl font-semibold text-ink">Companies</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
          Configured public career sources and the active postings found during the latest sync.
        </p>
      </div>
      <section className="overflow-hidden rounded-lg border border-line bg-white shadow-subtle">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-line text-sm">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Company</th>
                <th className="px-4 py-3">Group</th>
                <th className="px-4 py-3">Source</th>
                <th className="px-4 py-3">Active jobs</th>
                <th className="px-4 py-3">Last synced</th>
                <th className="px-4 py-3">Career page</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {companies.length > 0 ? (
                companies.map((company) => (
                  <tr key={company.slug}>
                    <td className="px-4 py-3 font-medium text-ink">{company.name}</td>
                    <td className="px-4 py-3">
                      <CompanyBadge group={company.company_group} />
                    </td>
                    <td className="px-4 py-3 text-slate-600">{company.source_type}</td>
                    <td className="px-4 py-3 text-slate-600">{company.active_job_count}</td>
                    <td className="px-4 py-3 text-slate-600">
                      {formatDateTime(company.last_synced)}
                    </td>
                    <td className="px-4 py-3">
                      <a
                        href={company.career_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 font-medium text-accent hover:text-teal-800"
                      >
                        Open
                        <ExternalLink aria-hidden="true" className="h-4 w-4" />
                      </a>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="px-4 py-8 text-center text-muted" colSpan={6}>
                    No company sync data yet. Run the crawler to populate this table.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
