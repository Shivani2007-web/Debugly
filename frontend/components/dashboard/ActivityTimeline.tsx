"use client";

// Section D — meaningful learning-activity timeline (no keystrokes).

import type { TimelineEvent } from "@/types/dashboard";

const ICON: Record<string, string> = {
  submission: "📤",
  code_execution: "▶️",
  syntax_error: "⚠️",
  runtime_error: "💥",
  test_failure: "✗",
  successful_execution: "✓",
  hint_requested: "💡",
  hint_level_reached: "💡",
  tutor_answer_correct: "🗣️",
  tutor_answer_incorrect: "🗣️",
  successful_correction: "🔧",
  misconception_detected: "🧠",
  challenge_attempt: "🎯",
};

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime();
  const diff = Date.now() - then;
  if (Number.isNaN(diff)) return "";
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function ActivityTimeline({ timeline }: { timeline: TimelineEvent[] }) {
  return (
    <section className="rounded-xl bg-panelAlt/40 p-5 ring-1 ring-white/10">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        Learning Activity
      </h2>

      {timeline.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">No activity recorded yet.</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {timeline.map((e, i) => (
            <li key={i} className="flex items-start gap-3 text-sm">
              <span className="mt-0.5 w-5 shrink-0 text-center">
                {ICON[e.event_type] ?? "•"}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-slate-200">{e.label}</p>
                {e.concept_key && (
                  <p className="text-xs text-slate-500">
                    {e.concept_key.replace(/_/g, " ")}
                    {e.error_type && ` · ${e.error_type}`}
                  </p>
                )}
              </div>
              <span className="shrink-0 text-xs text-slate-600">{timeAgo(e.at)}</span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
