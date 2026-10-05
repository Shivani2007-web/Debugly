// Small presentational status indicator used on the Phase 1 landing page.

type State = "ok" | "down" | "pending";

const STYLES: Record<State, string> = {
  ok: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30",
  down: "bg-rose-500/15 text-rose-300 ring-rose-500/30",
  pending: "bg-amber-500/15 text-amber-300 ring-amber-500/30",
};

const DOT: Record<State, string> = {
  ok: "bg-emerald-400",
  down: "bg-rose-400",
  pending: "bg-amber-400 animate-pulse",
};

export function StatusPill({ state, label }: { state: State; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium ring-1 ${STYLES[state]}`}
    >
      <span className={`h-2 w-2 rounded-full ${DOT[state]}`} />
      {label}
    </span>
  );
}
