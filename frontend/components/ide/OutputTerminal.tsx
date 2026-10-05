"use client";

// Terminal view: stdout, stderr and structured error for the latest execution.

import type { ExecutionResult } from "@/types/execution";

export function OutputTerminal({ result }: { result: ExecutionResult | null }) {
  if (!result) {
    return (
      <div className="p-4 font-mono text-sm text-slate-600">
        Run or submit your code to see output here.
      </div>
    );
  }

  const hasError = result.error !== null;

  return (
    <div className="space-y-3 p-4 font-mono text-sm">
      {result.stdout && (
        <section>
          <p className="mb-1 text-xs uppercase tracking-wide text-slate-500">stdout</p>
          <pre className="whitespace-pre-wrap break-words text-slate-200">
            {result.stdout}
          </pre>
        </section>
      )}

      {result.stderr && (
        <section>
          <p className="mb-1 text-xs uppercase tracking-wide text-slate-500">stderr</p>
          <pre className="whitespace-pre-wrap break-words text-amber-300">
            {result.stderr}
          </pre>
        </section>
      )}

      {hasError && (
        <section className="rounded-md bg-rose-500/10 p-3 ring-1 ring-rose-500/20">
          <p className="font-semibold text-rose-300">
            {result.error?.error_type ?? "Error"}
            {result.error?.line != null && (
              <span className="ml-2 text-rose-400/80">line {result.error.line}</span>
            )}
          </p>
          {result.error?.message && (
            <p className="mt-1 whitespace-pre-wrap break-words text-rose-200/90">
              {result.error.message}
            </p>
          )}
        </section>
      )}

      {!result.stdout && !result.stderr && !hasError && (
        <p className="text-slate-600">No output.</p>
      )}

      <p className="pt-2 text-xs text-slate-600">
        Finished in {result.duration_ms} ms
        {result.truncated && " · output truncated"}
      </p>
    </div>
  );
}
