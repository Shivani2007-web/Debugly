"use client";

// Live connection-chain widget for Phase 1: polls the backend health endpoint
// and renders the status of the frontend -> backend -> MongoDB chain.

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import type { HealthResponse } from "@/types/health";
import { StatusPill } from "./StatusPill";

type Phase = "loading" | "loaded" | "error";

export function ConnectionStatus() {
  const [phase, setPhase] = useState<Phase>("loading");
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const check = useCallback(async () => {
    try {
      const result = await api.health();
      setData(result);
      setPhase("loaded");
      setError(null);
    } catch (err) {
      setData(null);
      setPhase("error");
      setError(err instanceof ApiError ? err.message : "Unknown error");
    }
  }, []);

  useEffect(() => {
    void check();
    const id = setInterval(check, 5000);
    return () => clearInterval(id);
  }, [check]);

  const backendState =
    phase === "loading" ? "pending" : phase === "loaded" ? "ok" : "down";
  const dbState =
    phase !== "loaded"
      ? phase === "loading"
        ? "pending"
        : "down"
      : data?.database === "connected"
        ? "ok"
        : "down";

  return (
    <div className="w-full max-w-md rounded-xl bg-panelAlt p-6 ring-1 ring-white/10">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">
        Connection chain
      </h2>

      <ul className="space-y-3">
        <li className="flex items-center justify-between">
          <span className="text-slate-200">Frontend</span>
          <StatusPill state="ok" label="running" />
        </li>
        <li className="flex items-center justify-between">
          <span className="text-slate-200">Backend (FastAPI)</span>
          <StatusPill
            state={backendState}
            label={
              backendState === "ok"
                ? "reachable"
                : backendState === "pending"
                  ? "checking…"
                  : "unreachable"
            }
          />
        </li>
        <li className="flex items-center justify-between">
          <span className="text-slate-200">Database (MongoDB)</span>
          <StatusPill
            state={dbState}
            label={
              dbState === "ok"
                ? "connected"
                : dbState === "pending"
                  ? "checking…"
                  : "disconnected"
            }
          />
        </li>
      </ul>

      {error && (
        <p className="mt-4 rounded-md bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
          {error} — is the backend running on the configured API base URL?
        </p>
      )}

      <button
        onClick={() => void check()}
        className="mt-5 w-full rounded-md bg-accentMuted px-4 py-2 text-sm font-medium text-white transition hover:bg-accent hover:text-panel"
      >
        Re-check now
      </button>
    </div>
  );
}
