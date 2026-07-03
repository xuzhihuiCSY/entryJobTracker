import Link from "next/link";
import { SITE_NAME, SITE_NAV_ITEMS } from "@/lib/site";

export function Footer() {
  return (
    <footer className="mt-10 border-t border-line bg-white">
      <div className="mx-auto grid w-full max-w-7xl gap-5 px-4 py-6 text-sm sm:px-6 lg:grid-cols-[1fr_auto] lg:items-start lg:px-8">
        <div>
          <p className="font-semibold text-ink">{SITE_NAME}</p>
          <p className="mt-2 max-w-2xl leading-6 text-muted">
            Public career-posting tracker for U.S. tech candidates. We link to official
            career pages and are not affiliated with the companies listed.
          </p>
        </div>
        <nav className="flex flex-wrap gap-x-4 gap-y-2" aria-label="Footer navigation">
          {SITE_NAV_ITEMS.map((item) => (
            <Link key={item.href} href={item.href} className="text-slate-600 hover:text-slate-950">
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </footer>
  );
}
