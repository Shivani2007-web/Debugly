"use client";

// A compact strip of summary metrics derived ONLY from real dashboard data
// (see deriveSummaryMetrics). No invented timeframe — these are totals from the
// learner profile. Metrics with no data are simply shown as 0, never faked.

import type { ConceptProgress } from "@/types/dashboard";
import { deriveSummaryMetrics } from "@/lib/dashboard";

export function SummaryStrip({ concepts }: { concepts: ConceptProgress[] }) {
  const m = deriveSummaryMetrics(concepts);

  const stats: { label: string; value: string }[] = [
    { label: "Problems solved", value: String(m.problemsSolved) },
    { label: "Concepts practiced", value: String(m.conceptsPracticed) },
    { label: "Independent wins", value: String(m.independentSuccess) },
  ];

  return (
    <div className="grid grid-cols-3 gap-3">
      {stats.map((s) => (
        <div
          key={s.label}
          className="rounded-xl border border-white/10 bg-panelAlt/40 p-4 text-center"
        >
          <p className="text-2xl font-bold tabular-nums text-slate-100">{s.value}</p>
          <p className="mt-1 text-xs text-slate-500">{s.label}</p>
        </div>
      ))}
    </div>
  );
}
