// Static, presentation-only preview of the Debugly IDE. No live functionality —
// it visually communicates Problem -> Editor -> Test Results -> AI Tutor using
// the product's dark identity. Nothing here calls the backend.

import { RobotCompanion } from "@/components/tutor/RobotCompanion";

export function ProductPreview() {
  return (
    <div
      className="overflow-hidden rounded-xl border border-white/10 bg-panel shadow-2xl shadow-black/40"
      role="img"
      aria-label="Preview of the Debugly coding environment: a task, a code editor, test results, and the AI tutor."
    >
      {/* window chrome */}
      <div className="flex items-center gap-2 border-b border-white/10 bg-panelAlt/60 px-4 py-2">
        <span className="h-3 w-3 rounded-full bg-rose-400/70" />
        <span className="h-3 w-3 rounded-full bg-amber-400/70" />
        <span className="h-3 w-3 rounded-full bg-emerald-400/70" />
        <span className="ml-3 text-xs text-slate-500">Debugly — sum_list.py</span>
      </div>

      <div className="grid gap-0 md:grid-cols-[180px_1fr_240px]">
        {/* Problem */}
        <div className="border-b border-white/10 p-4 md:border-b-0 md:border-r">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">Problem</p>
          <p className="mt-2 text-sm font-medium text-slate-200">Sum a list of numbers</p>
          <p className="mt-1 text-xs text-slate-500">
            Return the sum of all numbers in the list.
          </p>
        </div>

        {/* Editor + results */}
        <div className="flex min-w-0 flex-col border-b border-white/10 md:border-b-0 md:border-r">
          <pre className="flex-1 overflow-x-auto p-4 font-mono text-xs leading-relaxed text-slate-300">
            <code>{`def sum_list(numbers):
    total = 0
    for i in range(len(numbers) + 1):
        total += numbers[i]
    return total`}</code>
          </pre>
          <div className="border-t border-white/10 bg-panelAlt/40 px-4 py-2">
            <span className="inline-flex items-center gap-2 rounded-full bg-rose-500/15 px-2.5 py-0.5 text-xs font-medium text-rose-300 ring-1 ring-rose-500/25">
              ● 2 / 4 tests passed
            </span>
          </div>
        </div>

        {/* AI tutor */}
        <div className="flex flex-col items-center justify-center gap-3 p-4">
          <RobotCompanion state="concerned" message="Let's look at what happened." />
          <div className="rounded-md bg-panelAlt/60 px-3 py-2 text-center text-xs text-slate-400 ring-1 ring-white/10">
            Debugly spotted a loop boundary that reaches one step too far.
          </div>
        </div>
      </div>
    </div>
  );
}
