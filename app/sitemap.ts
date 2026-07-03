import type { MetadataRoute } from "next";
import { getLastUpdated } from "@/lib/jobs";
import { SITE_URL } from "@/lib/site";

const routes = [
  { path: "/", priority: 1 },
  { path: "/jobs", priority: 0.9 },
  { path: "/fresh", priority: 0.8 },
  { path: "/big-tech", priority: 0.8 },
  { path: "/companies", priority: 0.6 },
  { path: "/trust", priority: 0.6 }
];

export default function sitemap(): MetadataRoute.Sitemap {
  const stats = getLastUpdated();
  const lastModified = stats.last_updated ? new Date(stats.last_updated) : new Date();

  return routes.map((route) => ({
    url: `${SITE_URL}${route.path}`,
    lastModified,
    changeFrequency: route.path === "/fresh" || route.path === "/jobs" ? "daily" : "weekly",
    priority: route.priority
  }));
}
