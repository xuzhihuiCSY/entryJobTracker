"use client";

import { useEffect, useState } from "react";
import type { Company } from "@/lib/types";

export function CompanySyncStatus({ company }: { company: Company }) {
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 60_000);
    return () => window.clearInterval(timer);
  }, []);
  const maxAge = company.sync_priority === 1 ? 12 : company.sync_priority === 2 ? 48 : 24 * 14;
  const lastSuccess = Date.parse(company.last_synced);
  const stale = now !== null && Number.isFinite(lastSuccess) && now - lastSuccess > maxAge * 3600_000;
  let label = "Not yet verified";
  let style = "bg-slate-100 text-slate-700";
  if (company.enabled === false) label = "Disabled";
  else if (company.sync_status === "failed") { label = stale ? "Fetch failed · stale" : "Fetch failed"; style = "bg-rose-50 text-rose-800"; }
  else if (stale) { label = "Stale"; style = "bg-amber-50 text-amber-800"; }
  else if (company.sync_status === "success") { label = "Synced"; style = "bg-emerald-50 text-emerald-800"; }
  return (
    <div className="max-w-48">
      <span className={`inline-block rounded-md px-2 py-1 text-xs font-medium ${style}`}>{label}</span>
      {company.sync_status === "failed" ? <p className="mt-1 text-xs text-muted">Previous postings retained.</p> : null}
      {company.last_error ? <p className="mt-1 text-xs text-muted">{company.last_error}</p> : null}
    </div>
  );
}
