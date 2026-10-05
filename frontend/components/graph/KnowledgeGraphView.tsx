"use client";

// Dedicated knowledge-graph page body. Fetches the SAME Phase 7
// knowledge-graph endpoint and renders the existing interactive SVG graph.
// No graph data logic here — purely presentation + fetch/loading/error states.

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import type { KnowledgeGraph as KG } from "@/types/dashboard";
import { KnowledgeGraph } from "./KnowledgeGraph";
import { displayNameFromUserId } from "@/lib/dashboard";
import { LoadingState, ErrorState } from "@/components/ui/States";

export function KnowledgeGraphView({ userId }: { userId: string }) {
  const [phase, setPhase] = useState<"loading" | "ready" | "error">("loading");
  const [graph, setGraph] = useState<KG | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setPhase("loading");
    setError(null);
    try {
      setGraph(await api.knowledgeGraph(userId));
      setPhase("ready");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load the graph.");
      setPhase("error");
    }
  }, [userId]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <header className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 sm:text-3xl">
            Your Knowledge Graph
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            See how Debugly understands your learning journey — from mistakes to
            mastery.
          </p>
        </div>
        <Link
          href={`/dashboard/${userId}`}
          className="rounded-md bg-panelAlt px-3 py-2 text-sm text-slate-300 ring-1 ring-white/10 transition hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
        >
          ← Back to dashboard
        </Link>
      </header>

      {/* Legend of the Student -> ... -> Outcome chain */}
      <div className="mb-4 flex flex-wrap gap-x-4 gap-y-2 text-xs text-slate-500">
        {[
          ["#6ea8fe", "Student"],
          ["#c3a6ff", "Concept"],
          ["#ff8787", "Misconception"],
          ["#ffd43b", "Evidence"],
          ["#63e6be", "Intervention"],
          ["#74c0fc", "Challenge"],
          ["#69db7c", "Outcome"],
        ].map(([c, label]) => (
          <span key={label} className="inline-flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: c }} />
            {label}
          </span>
        ))}
      </div>

      {phase === "loading" && <LoadingState label="Building your graph…" />}
      {phase === "error" && (
        <ErrorState message={`${error ?? "Error"} — is the backend running?`} onRetry={load} />
      )}
      {phase === "ready" && graph && <KnowledgeGraph graph={graph} />}
    </div>
  );
}
