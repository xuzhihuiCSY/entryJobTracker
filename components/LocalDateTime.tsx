"use client";

import { useEffect, useState } from "react";

type LocalDateTimeProps = {
  value: string;
};

function formatLocalDateTime(value: string): string {
  if (!value) return "Not synced yet";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not synced yet";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZoneName: "short"
  }).format(date);
}

export function LocalDateTime({ value }: LocalDateTimeProps) {
  const [label, setLabel] = useState("Loading local time...");

  useEffect(() => {
    setLabel(formatLocalDateTime(value));
  }, [value]);

  return <time dateTime={value || undefined}>{label}</time>;
}
