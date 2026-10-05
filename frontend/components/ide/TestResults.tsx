"use client";

// Test-results view: per-case pass/fail with expected vs actual and any error.

import type { ExecutionResult, TestResult } from "@/types/execution";

function format(value: unknown): string {
  if (value === null || value === undefined) return "None";
  if (typeof value === "string") return JSON.stringify(value);
  return JSON.stringify(value);
}

function Row({ test }: { test: TestResult }) {
  return (
    <li className="rounded-md bg-panelAlt/60 p-3 ring-1 ring-white/5">
      <div className="flex items-center gap-2">
        <span className={test.passed ? "text-emerald-400" : "text-rose-400"}>
          {test.passed ? "✓" : "✗"}
        </span>
        <span className="text-sm font-medium text-slate-200">{test.name}</span>
        {test.hidden && (
          <span className="rounded bg-white/5 px-1.5 py-0.5 text-[10px] uppercase text-slate-500">
            hidden
          </span>
        )}
      </div>

      {!test.passed && (
        <div className="mt-2 space-y-1 pl-6 font-mono text-xs">
          {test.error ? (
            <p className="text-rose-300">
              {test.error.error_type}: {test.error.message}
            </p>
          ) : (
            <>
              <p className="text-slate-400">
                expected:{" "}
                <span className="text-emerald-300">{format(test.expected)}</span>
              </p>
              <p className="text-slate-400">
                actual: <span className="text-rose-300">{format(test.actual)}</span>
              </p>
            </>
          )}
        </div>
      )}
    </li>
  );
}

export function TestResults({ result }: { result: ExecutionResult | null }) {
  if (!result || result.test_results.length === 0) {
    if (result && result.status === "syntax_error") {
      return (
        <div className="p-4 text-sm text-rose-300">
          Code could not compile — fix the syntax error, then submit again.
        </div>
      );
    }
    return (
      <div className="p-4 text-sm text-slate-600">
        Submit your code to run it against the test cases.
      </div>
    );
  }

  const allPassed = result.passed_count === result.total_count;

  return (
    <div className="p-4">
      <div
        className={`mb-3 inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium ${
          allPassed
            ? "bg-emerald-500/15 text-emerald-300"
            : "bg-rose-500/15 text-rose-300"
        }`}
      >
        {result.passed_count} / {result.total_count} tests passed
      </div>

      <ul className="space-y-2">
        {result.test_results.map((t) => (
          <Row key={t.name} test={t} />
        ))}
      </ul>
    </div>
  );
}
