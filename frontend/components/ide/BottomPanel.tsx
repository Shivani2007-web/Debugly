"use client";

// Tabbed bottom panel: Output (stdout/stderr/errors) and Tests (per-case).
// Auto-focuses the Tests tab after a submit, Output after a plain run.

import { useEffect, useState } from "react";
import type { ExecutionResult } from "@/types/execution";
import { OutputTerminal } from "./OutputTerminal";
import { TestResults } from "./TestResults";

type Tab = "output" | "tests";

interface BottomPanelProps {
  result: ExecutionResult | null;
  // Which tab to prefer after the latest action.
  preferredTab: Tab;
  resultVersion: number;
}

export function BottomPanel({ result, preferredTab, resultVersion }: BottomPanelProps) {
  const [tab, setTab] = useState<Tab>("output");

  // Follow the action: show tests after submit, output after run.
  useEffect(() => {
    setTab(preferredTab);
  }, [preferredTab, resultVersion]);

  const failedBadge =
    result && result.total_count > 0 && result.passed_count < result.total_count;

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center gap-1 border-b border-white/10 bg-panelAlt/40 px-2">
        <TabButton active={tab === "output"} onClick={() => setTab("output")}>
          Output
        </TabButton>
        <TabButton active={tab === "tests"} onClick={() => setTab("tests")}>
          Tests
          {failedBadge && (
            <span className="ml-1.5 h-1.5 w-1.5 rounded-full bg-rose-400" />
          )}
        </TabButton>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {tab === "output" ? (
          <OutputTerminal result={result} />
        ) : (
          <TestResults result={result} />
        )}
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center px-3 py-2 text-sm font-medium transition ${
        active
          ? "border-b-2 border-accent text-slate-100"
          : "text-slate-500 hover:text-slate-300"
      }`}
    >
      {children}
    </button>
  );
}
