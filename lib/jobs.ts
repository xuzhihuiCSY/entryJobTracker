import fs from "node:fs";
import path from "node:path";
import { isEntryLevel, isFresh, sortJobs } from "@/lib/filters";
import type { Company, Job, LastUpdated } from "@/lib/types";

const dataDir = path.join(process.cwd(), "public", "data");

function readJsonFile<T>(fileName: string, fallback: T): T {
  const filePath = path.join(dataDir, fileName);
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf8")) as T;
  } catch {
    return fallback;
  }
}

export function getJobs(): Job[] {
  return readJsonFile<Job[]>("jobs.json", []);
}

export function getCompanies(): Company[] {
  return readJsonFile<Company[]>("companies.json", []);
}

export function getLastUpdated(): LastUpdated {
  return readJsonFile<LastUpdated>("last_updated.json", {
    last_updated: "",
    total_jobs: 0,
    big_tech_jobs: 0,
    fresh_24h_jobs: 0,
    sources_synced: 0
  });
}

export function getFreshJobs(hours = 24): Job[] {
  return sortJobs(getJobs().filter((job) => isFresh(job, hours)), "first_seen_desc");
}

export function getBigTechEntryJobs(): Job[] {
  return sortJobs(
    getJobs().filter(
      (job) => job.company_group === "big_tech" && job.is_us_based && isEntryLevel(job)
    ),
    "first_seen_desc"
  );
}

export function formatDateTime(value: string): string {
  if (!value) return "Not synced yet";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not synced yet";
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}
