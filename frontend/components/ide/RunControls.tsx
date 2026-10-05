"use client";

// Run / Submit / Reset controls. Pure presentational; the page owns the
// handlers and the busy state.

interface RunControlsProps {
  onRun: () => void;
  onSubmit: () => void;
  onReset: () => void;
  busy: boolean;
}

export function RunControls({ onRun, onSubmit, onReset, busy }: RunControlsProps) {
  return (
    <div className="flex items-center gap-2">
      <button
        onClick={onRun}
        disabled={busy}
        className="rounded-md bg-panelAlt px-4 py-1.5 text-sm font-medium text-slate-200 ring-1 ring-white/10 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-50"
      >
        ▶ Run
      </button>
      <button
        onClick={onSubmit}
        disabled={busy}
        className="rounded-md bg-emerald-600 px-4 py-1.5 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
      >
        ✓ Submit
      </button>
      <button
        onClick={onReset}
        disabled={busy}
        className="ml-auto rounded-md px-3 py-1.5 text-sm text-slate-400 transition hover:text-slate-200 disabled:opacity-50"
      >
        Reset
      </button>
      {busy && <span className="text-sm text-amber-300">running…</span>}
    </div>
  );
}
