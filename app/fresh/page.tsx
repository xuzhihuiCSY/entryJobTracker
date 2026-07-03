import type { Metadata } from "next";
import { FreshJobsClient } from "@/app/fresh/FreshJobsClient";
import { getJobs } from "@/lib/jobs";

export const metadata: Metadata = {
  title: "Fresh Tech Jobs",
  description:
    "See newly discovered U.S. tech job postings from the latest sync windows: 24 hours, 48 hours, and 7 days.",
  alternates: {
    canonical: "/fresh"
  }
};

export default function FreshPage() {
  return <FreshJobsClient jobs={getJobs()} />;
}
