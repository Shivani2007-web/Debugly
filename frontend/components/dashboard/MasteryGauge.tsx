"use client";

// Section A — the headline Debugly Mastery Indicator with a radial gauge and
// a sparkline trend. Clearly labeled as an indicator, not a validated score.

import type { OverallMastery } from "@/types/dashboard";
import { BAND_LABEL, BAND_RING } from "@/lib/dashboard";

export function MasteryGauge({ overall }: { overall: OverallMastery }) {
  const pct = Math.max(0, Math.min(100, overall.indicator));
  const radius = 54;
  const circ = 2 * Math.PI * radius;
  const dash = (pct / 100) * circ;
  const color = BAND_RING[overall.band];

  const trend = overall.trend.map((t) => t.mastery);

  return (
    <section className="flex h-full flex-col rounded-xl border border-white/10 bg-panelAlt/40 p-5">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        Debugly Mastery
      </h2>

      <div className="mt-4 flex flex-col items-center">
        <div className="relative h-36 w-36 shrink-0">
          <svg viewBox="0 0 128 128" className="h-full w-full -rotate-90">
            <circle cx="64" cy="64" r={radius} fill="none" stroke="#2a2a38" strokeWidth="10" />
            <circle
              cx="64"
              cy="64"
              r={radius}
              fill="none"
              stroke={color}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={`${dash} ${circ}`}
              style={{ transition: "stroke-dasharray 0.6s ease" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-4xl font-bold text-slate-100">{pct.toFixed(0)}</span>
            <span className="text-xs text-slate-500">/ 100</span>
          </div>
        </div>

        <p className="mt-3 text-lg font-semibold" style={{ color }}>
          {BAND_LABEL[overall.band]}
        </p>
        {trend.length > 1 && <Sparkline values={trend} color={color} />}
      </div>

      <p className="mt-auto pt-4 text-[11px] leading-relaxed text-slate-600">
        {overall.disclaimer}
      </p>
    </section>
  );
}

function Sparkline({ values, color }: { values: number[]; color: string }) {
  const w = 160;
  const h = 36;
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const span = max - min || 1;
  const pts = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * w;
      const y = h - ((v - min) / span) * h;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg width={w} height={h} className="mt-2" aria-label="mastery trend">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}
