"use client";

import { useEffect, useRef, useState } from "react";
import type { Job } from "@/lib/types";

type DescriptionFile = Record<string, { text: string; status: string; fetched_at: string }>;
const requests = new Map<string, Promise<DescriptionFile>>();

function loadDescriptions(path: string): Promise<DescriptionFile> {
  let request = requests.get(path);
  if (!request) {
    request = fetch(path).then((response) => {
      if (!response.ok) throw new Error("Description unavailable");
      return response.json() as Promise<DescriptionFile>;
    }).catch((error) => {
      requests.delete(path);
      throw error;
    });
    requests.set(path, request);
  }
  return request;
}

export function JobDescription({ job }: { job: Job }) {
  const [text, setText] = useState<string | null>(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  async function load() {
    if (!job.description_path || loading || text !== null) return;
    setLoading(true);
    setError(false);
    try {
      const records = await loadDescriptions(job.description_path);
      const body = records[job.id]?.text;
      if (!body) throw new Error("Posting text unavailable");
      if (mounted.current) setText(body);
    } catch {
      if (mounted.current) setError(true);
    } finally {
      if (mounted.current) setLoading(false);
    }
  }

  if (!job.description_path) {
    return <p className="mt-2 text-xs text-muted">Full job description unavailable. Check the official posting.</p>;
  }

  return (
    <details className="mt-3 text-sm text-slate-600" onToggle={(event) => { if (event.currentTarget.open) void load(); }}>
      <summary className="cursor-pointer font-medium text-accent hover:text-teal-800">
        {job.description_status === "full" ? "View full job description" : "View available job text"}
      </summary>
      {loading ? <p className="mt-2" role="status">Loading job description…</p> : null}
      {error ? <p className="mt-2 text-xs" role="alert">Could not load the job text. <button className="underline" onClick={() => void load()}>Retry</button> or check the official posting.</p> : null}
      {text ? <div className="mt-3 max-h-[32rem] max-w-4xl overflow-y-auto whitespace-pre-line rounded-md bg-slate-50 p-4 text-sm leading-6">{text}</div> : null}
      {job.description_status !== "full" ? <p className="mt-2 text-xs text-muted">Only partial text is available. Eligibility and sponsorship may be incomplete.</p> : null}
    </details>
  );
}
