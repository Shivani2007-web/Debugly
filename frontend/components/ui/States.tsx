"use client";

// Shared loading / error / empty state primitives used across the dashboard,
// teacher view, and IDE panels for a consistent, polished feel.

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div
      className="flex h-48 flex-col items-center justify-center gap-3 text-sm text-slate-500"
      data-testid="state-loading"
    >
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-white/10 border-t-accent" />
      {label}
    </div>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div
      className="flex h-48 flex-col items-center justify-center gap-3"
      data-testid="state-error"
    >
      <p className="max-w-md rounded-md bg-rose-500/10 px-4 py-3 text-center text-sm text-rose-300">
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-md bg-accentMuted px-4 py-2 text-sm text-white transition hover:bg-accent hover:text-panel"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  title,
  hint,
}: {
  title: string;
  hint?: string;
}) {
  return (
    <div
      className="flex h-48 flex-col items-center justify-center gap-2 text-center"
      data-testid="state-empty"
    >
      <p className="text-sm font-medium text-slate-300">{title}</p>
      {hint && <p className="max-w-sm text-xs text-slate-500">{hint}</p>}
    </div>
  );
}
