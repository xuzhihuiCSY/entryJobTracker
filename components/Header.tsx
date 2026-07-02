"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BriefcaseBusiness } from "lucide-react";

const navItems = [
  { href: "/", label: "Home" },
  { href: "/jobs", label: "Jobs" },
  { href: "/fresh", label: "Fresh" },
  { href: "/big-tech", label: "Big Tech" },
  { href: "/companies", label: "Companies" }
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="border-b border-line bg-white/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-3 px-4 py-4 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <Link href="/" className="flex items-center gap-2 text-base font-semibold text-ink">
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-accent text-white">
            <BriefcaseBusiness aria-hidden="true" className="h-5 w-5" />
          </span>
          US Tech Entry Jobs Tracker
        </Link>
        <nav className="flex flex-wrap gap-1">
          {navItems.map((item) => {
            const active =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-md px-3 py-2 text-sm font-medium transition ${
                  active
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
