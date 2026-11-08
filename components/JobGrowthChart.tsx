"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import { BIG_FIVE_COMPANIES, DAY_MS, jobGrowth, snapshotChanges, trendBounds, type TrendPoint, type TrendRange } from "@/lib/job-trends";

const number = new Intl.NumberFormat("en-US");
const date = (value: string) => new Date(`${value}T00:00:00Z`).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
const signed = (value: number) => `${value > 0 ? "+" : ""}${number.format(value)}`;
const HEIGHT = 244, LEFT = 54, RIGHT = 20, TOP = 18, BOTTOM = 38;

export function JobGrowthChart({ trends }: { trends: Record<TrendRange, TrendPoint[]> }) {
  const [range, setRange] = useState<TrendRange>(30);
  const [mode, setMode] = useState<"total" | "change">("total");
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [width, setWidth] = useState(620);
  const plot = useRef<SVGSVGElement>(null);
  const points = trends[range];
  useEffect(() => {
    if (!plot.current) return;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(200, Math.round(entry.contentRect.width))));
    observer.observe(plot.current);
    return () => observer.disconnect();
  }, [points.length]);
  const gradient = useId().replace(/:/g, "");
  const changes = useMemo(() => snapshotChanges(points), [points]);
  const growth = jobGrowth(points);
  const latest = points[points.length - 1];
  const selected = points.find((point) => point.date === selectedDate) ?? latest;
  const index = selected ? points.indexOf(selected) : -1;
  const change = selected ? changes.get(selected.date) : null;
  const times = points.map((point) => Date.parse(`${point.date}T00:00:00Z`));
  const start = times[0] ?? 0, end = times[times.length - 1] ?? 0;
  const values = points.map((point) => mode === "total" ? point.total_jobs : changes.get(point.date) ?? 0);
  const [min, max] = trendBounds(values, mode === "change");
  const x = (i: number) => end === start ? (width + LEFT - RIGHT) / 2 : LEFT + (times[i] - start) / (end - start) * (width - LEFT - RIGHT);
  const y = (value: number) => TOP + (max - value) / (max - min) * (HEIGHT - TOP - BOTTOM);
  // Don't draw an invented curve through days with no recorded snapshot.
  const line = points.map((_, i) => `${i === 0 || times[i] - times[i - 1] > DAY_MS ? "M" : "L"}${x(i)},${y(values[i])}`).join(" ");
  const labels = [...new Set([0, Math.floor((points.length - 1) / 2), points.length - 1])].filter((i) => i >= 0);
  const barWidth = Math.max(2, Math.min(26, (width - LEFT - RIGHT) / Math.max(1, (end - start) / DAY_MS + 1) * 0.65));

  return (
    <section aria-labelledby={`${gradient}-title`} className="min-w-0 rounded-xl border border-line bg-white p-5 shadow-subtle sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id={`${gradient}-title`} className="text-sm font-semibold text-slate-700">Big Five job trends</h2>
          <p className="mt-1 text-3xl font-semibold tracking-tight text-ink">{latest ? number.format(latest.total_jobs) : "—"}<span className="ml-2 text-sm font-normal tracking-normal text-slate-500">active jobs</span></p>
        </div>
        <div aria-label="Chart time range" className="flex rounded-lg bg-slate-100 p-1">
          {([7, 30, 90, "all"] as TrendRange[]).map((value) => (
            <button key={value} type="button" aria-pressed={range === value} onClick={() => { setRange(value); setSelectedDate(null); }} className={`rounded-md px-2.5 py-1.5 text-xs font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-700 ${range === value ? "bg-white text-teal-800 shadow-sm" : "text-slate-500 hover:text-slate-800"}`}>{value === "all" ? "All" : `${value}D`}</button>
          ))}
        </div>
      </div>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <p className={`text-sm font-semibold ${growth.change !== null && growth.change < 0 ? "text-rose-700" : "text-teal-700"}`}>
          {growth.change === null ? "Building history" : `${signed(growth.change)} jobs${growth.percent === null ? "" : ` (${growth.percent > 0 ? "+" : ""}${growth.percent.toFixed(1)}%)`}`}
          <span className="ml-1 font-normal text-slate-500">{points.length > 1 ? `since ${date(points[0].date)}` : points.length === 1 ? "· one recorded day" : "· awaiting snapshots"}</span>
        </p>
        <div aria-label="Chart metric" className="flex gap-3 text-xs">
          {([['total', 'Active jobs'], ['change', 'Net change']] as const).map(([value, label]) => (
            <button key={value} type="button" aria-pressed={mode === value} onClick={() => setMode(value)} className={`border-b-2 pb-1 font-semibold focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-700 ${mode === value ? "border-teal-700 text-teal-800" : "border-transparent text-slate-500 hover:text-slate-800"}`}>{label}</button>
          ))}
        </div>
      </div>

      <p className="mt-2 text-xs text-slate-500">{Object.values(BIG_FIVE_COMPANIES).join(" · ")}</p>
      {!points.length ? <div className="flex h-56 items-center justify-center text-center text-sm text-slate-500">No complete Big Five snapshots in this range.</div> : <>
        <svg ref={plot} viewBox={`0 0 ${width} ${HEIGHT}`} style={{ height: HEIGHT }} className="mt-4 w-full rounded-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-teal-700" role="group" aria-roledescription="interactive chart" aria-label={`${mode === "total" ? "Active jobs" : "Net change per snapshot"}, ${date(points[0].date)} to ${date(latest.date)}. Use left and right arrow keys to explore snapshots.`} tabIndex={0}
          onKeyDown={(event) => {
            let next = index;
            if (event.key === "ArrowLeft") next = Math.max(0, index - 1);
            else if (event.key === "ArrowRight") next = Math.min(points.length - 1, index + 1);
            else if (event.key === "Home") next = 0;
            else if (event.key === "End") next = points.length - 1;
            else return;
            event.preventDefault(); setSelectedDate(points[next].date);
          }}
          onPointerMove={(event) => {
            const bounds = event.currentTarget.getBoundingClientRect();
            const target = (event.clientX - bounds.left) / bounds.width * width;
            const nearest = points.reduce((best, _, i) => Math.abs(x(i) - target) < Math.abs(x(best) - target) ? i : best, 0);
            setSelectedDate(points[nearest].date);
          }} onPointerLeave={() => setSelectedDate(null)}>
          <defs><linearGradient id={gradient} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#0f766e" stopOpacity=".2" /><stop offset="100%" stopColor="#0f766e" stopOpacity="0" /></linearGradient></defs>
          {[0, 1, 2, 3].map((tick) => { const value = min + (max - min) * tick / 3; return <g key={tick}><line x1={LEFT} x2={width - RIGHT} y1={y(value)} y2={y(value)} stroke="#e2e8f0" strokeDasharray="3 4" /><text x={LEFT - 9} y={y(value) + 4} textAnchor="end" fontSize="11" fill="#64748b">{number.format(Math.round(value))}</text></g>; })}
          {mode === "total" ? <>
            {points.map((_, i) => i > 0 && times[i] - times[i - 1] === DAY_MS ? <path key={points[i].date} d={`M${x(i - 1)},${y(min)} L${x(i - 1)},${y(values[i - 1])} L${x(i)},${y(values[i])} L${x(i)},${y(min)} Z`} fill={`url(#${gradient})`} /> : null)}
            <path d={line} stroke="#0f766e" strokeWidth="2.5" fill="none" strokeLinejoin="round" />
            {points.map((point, i) => <circle key={point.date} cx={x(i)} cy={y(values[i])} r={i === index ? 4.5 : 2.5} fill="#0f766e" stroke="white" strokeWidth="1.5"><title>{`${point.date}: ${number.format(point.total_jobs)} active jobs`}</title></circle>)}
          </> : <>
            <line x1={LEFT} x2={width - RIGHT} y1={y(0)} y2={y(0)} stroke="#94a3b8" />
            {points.map((point, i) => changes.get(point.date) == null ? null : <rect key={point.date} x={x(i) - barWidth / 2} y={Math.min(y(0), y(values[i]))} width={barWidth} height={Math.max(1, Math.abs(y(values[i]) - y(0)))} rx="2" fill={values[i] < 0 ? "#e11d48" : "#0f766e"} opacity={i === index ? 1 : 0.7}><title>{`${point.date}: ${signed(values[i])} jobs vs previous snapshot`}</title></rect>)}
          </>}
          {index >= 0 && <line x1={x(index)} x2={x(index)} y1={TOP} y2={HEIGHT - BOTTOM} stroke="#64748b" strokeDasharray="3 4" opacity=".5" />}
          {labels.map((i) => <text key={i} x={x(i)} y={HEIGHT - 12} textAnchor={points.length === 1 ? "middle" : i === 0 ? "start" : i === points.length - 1 ? "end" : "middle"} fontSize="11" fill="#64748b">{date(points[i].date)}</text>)}
        </svg>
        <div aria-live="polite" aria-atomic="true" className="min-h-12 rounded-md bg-slate-50 px-3 py-2 text-xs leading-5 text-slate-600">
          <span className="font-semibold text-slate-800">{date(selected.date)}, {selected.date.slice(0, 4)} · {number.format(selected.total_jobs)} jobs</span>
          {change != null && <span> · {signed(change)} vs previous snapshot</span>}
        </div>
        {points.length === 1 && <p className="mt-2 text-xs text-slate-500">Growth appears after the next recorded day.</p>}
        <details className="mt-3 text-xs text-slate-500">
          <summary className="w-fit cursor-pointer hover:text-slate-800">View snapshot data</summary>
          <div className="mt-2 max-h-52 overflow-auto"><table className="w-full text-left"><caption className="sr-only">Daily job counts in the selected range</caption><thead><tr><th scope="col" className="py-1">Date (UTC)</th><th scope="col">Active jobs</th><th scope="col">Net change</th></tr></thead><tbody>{points.map((point) => <tr key={point.date} className="border-t border-slate-100"><td className="py-1">{point.date}</td><td>{number.format(point.total_jobs)}</td><td>{changes.get(point.date) == null ? "—" : signed(changes.get(point.date)!)}</td></tr>)}</tbody></table></div>
        </details>
      </>}
      <p className="mt-3 text-[11px] leading-5 text-slate-500">Each point uses the same five sources as the latest complete snapshot. Days without comparable counts for all five are skipped. Counts reflect the tracker’s collection rules.</p>
    </section>
  );
}
