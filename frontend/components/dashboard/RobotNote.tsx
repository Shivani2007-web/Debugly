"use client";

// Small contextual robot note for dashboards. Deliberately compact (no large
// illustration). Only rendered when there is a truthful message to show.

export function RobotNote({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div className="flex items-center gap-3 rounded-xl border border-accent/20 bg-accentMuted/10 px-4 py-3">
      <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-panel text-lg" aria-hidden>
        🤖
      </span>
      <p className="text-sm text-slate-200">{message}</p>
    </div>
  );
}
