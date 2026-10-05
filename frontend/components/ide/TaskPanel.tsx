"use client";

// Left-panel task description. Shows the prompt and the visible test cases
// (hidden ones are listed by name only, inputs withheld).

import type { Task } from "@/types/task";

export function TaskPanel({ task }: { task: Task | null }) {
  if (!task) {
    return (
      <div className="p-4 text-sm text-slate-500">Loading task…</div>
    );
  }

  const visible = task.test_cases.filter((t) => !t.hidden);
  const hiddenCount = task.test_cases.length - visible.length;

  return (
    <div className="flex h-full flex-col overflow-y-auto p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        Task
      </h2>
      <h3 className="mt-1 text-lg font-semibold text-slate-100">{task.title}</h3>

      <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-300">
        {task.prompt}
      </p>

      {task.concept_keys.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {task.concept_keys.map((c) => (
            <span
              key={c}
              className="rounded-full bg-accentMuted/30 px-2 py-0.5 text-xs text-accent ring-1 ring-accent/20"
            >
              {c.replace(/_/g, " ")}
            </span>
          ))}
        </div>
      )}

      <div className="mt-6">
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Test cases
        </h4>
        <ul className="mt-2 space-y-1 text-sm text-slate-400">
          {visible.map((t) => (
            <li key={t.name} className="flex items-center gap-2">
              <span className="text-slate-600">•</span>
              {t.name}
            </li>
          ))}
          {hiddenCount > 0 && (
            <li className="text-slate-600">+ {hiddenCount} hidden test case(s)</li>
          )}
        </ul>
      </div>
    </div>
  );
}
