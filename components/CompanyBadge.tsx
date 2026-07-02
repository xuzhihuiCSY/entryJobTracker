type CompanyBadgeProps = {
  group: string;
};

const groupLabel: Record<string, string> = {
  big_tech: "Big Tech",
  startup: "Startup",
  public: "Public",
  private: "Private",
  other: "Other"
};

export function CompanyBadge({ group }: CompanyBadgeProps) {
  const label = groupLabel[group] ?? group.replaceAll("_", " ");
  return (
    <span className="inline-flex items-center rounded-md border border-line bg-white px-2 py-1 text-xs font-medium capitalize text-slate-700">
      {label}
    </span>
  );
}
