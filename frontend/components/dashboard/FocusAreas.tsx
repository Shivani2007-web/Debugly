"use client";

// "Focus Areas" — the learner's actual weakest concepts/misconceptions
// (Phase 7 bottleneck data). Restrained attention styling: red/pink is used
// ONLY for genuine persistent gaps, so students aren't made to feel punished.

import type { Bottleneck } from "@/types/dashboard";
import { BAND_RING, formatConceptName } from "@/lib/dashboard";

export function FocusAreas({ bottlenecks }: { bottlenecks: Bottleneck[] }) {
  return (
    <section className="rounded-xl border border-white/10 bg-panelAlt/40 p-5">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        Focus Areas
      </h2>

      {bottlenecks.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">
          Nothing to focus on right now — no misconceptions detected yet.
        </p>
      ) : (
        <ul className="mt-3 space-y-3">
          {bottlenecks.map((b) => (
            <li
              key={`${b.concept_key}:${b.misconception_key}`}
              className={`rounded-lg border p-3 ${
                b.persistent
                  ? "border-rose-500/25 bg-rose-500/[0.06]"
                  : "border-white/10 bg-panel/50"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-100">
                  {formatConceptName(b.concept_key)}
                </span>
                <span className="text-xs tabular-nums text-slate-400">
                  {b.concept_mastery.toFixed(0)} · {bandName(b.concept_mastery)}
                </span>
              </div>

              {/* progress bar */}
              <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-white/5">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${Math.max(0, Math.min(100, b.concept_mastery))}%`,
                    backgroundColor: barColor(b.concept_mastery),
                  }}
                />
              </div>

              <div className="mt-2 flex items-center justify-between">
                <span className="text-xs text-slate-400">
                  {b.misconception_key.replace(/_/g, " ")}
                </span>
                {b.persistent ? (
                  <span className="rounded bg-rose-500/15 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-rose-300">
                    persistent gap
                  </span>
                ) : (
                  <span className="text-[10px] uppercase tracking-wide text-slate-600">
                    seen {b.occurrences}×
                  </span>
                )}
              </div>

              {b.recovery_successes > 0 && (
                <p className="mt-1.5 text-xs text-emerald-300">
                  ↑ Recovering — {b.recovery_successes} unaided success
                  {b.recovery_successes !== 1 ? "es" : ""} since your correction.
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function bandName(m: number): string {
  if (m >= 85) return "Strong";
  if (m >= 60) return "Proficient";
  if (m >= 35) return "Developing";
  return "Emerging";
}

function barColor(m: number): string {
  if (m >= 85) return BAND_RING.strong;
  if (m >= 60) return BAND_RING.proficient;
  if (m >= 35) return BAND_RING.developing;
  return BAND_RING.emerging;
}
