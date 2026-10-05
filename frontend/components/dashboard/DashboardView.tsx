"use client";

// The student dashboard. Presentation redesign over the SAME Phase 7 endpoints
// (dashboard + knowledge-graph). No data logic here: every metric comes from
// the backend payload. Handles loading / error / empty states and a manual
// refresh so updated learner state is reflected after activity.

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import type { DashboardResponse, KnowledgeGraph as KG } from "@/types/dashboard";
import {
  deriveRobotMessage,
  displayNameFromUserId,
  greetingPrefix,
} from "@/lib/dashboard";
import { MasteryGauge } from "./MasteryGauge";
import { ContinueLearning } from "./ContinueLearning";
import { FocusAreas } from "./FocusAreas";
import { ActivityTimeline } from "./ActivityTimeline";
import { SummaryStrip } from "./SummaryStrip";
import { GraphPreviewCard } from "./GraphPreviewCard";
import { RobotNote } from "./RobotNote";
import { LoadingState, ErrorState } from "@/components/ui/States";

type Phase = "loading" | "ready" | "error";

export function DashboardView({ userId }: { userId: string }) {
  const [phase, setPhase] = useState<Phase>("loading");
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [graph, setGraph] = useState<KG | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const load = useCallback(async () => {
    setPhase("loading");
    setError(null);
    try {
      const [d, g] = await Promise.all([
        api.dashboard(userId),
        api.knowledgeGraph(userId),
      ]);
      setDashboard(d);
      setGraph(g);
      setPhase("ready");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load dashboard.");
      setPhase("error");
    }
  }, [userId]);

  useEffect(() => {
    void load();
  }, [load]);

  const startChallenge = useCallback(async () => {
    setStarting(true);
    try {
      await api.generateChallenge({ user_id: userId });
      await load();
    } catch {
      /* non-fatal for the dashboard */
    } finally {
      setStarting(false);
    }
  }, [userId, load]);

  if (phase === "loading") {
    return (
      <div data-testid="dashboard-loading">
        <LoadingState label="Loading your dashboard…" />
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div data-testid="dashboard-error">
        <ErrorState
          message={`${error ?? "Error"} — is the backend running?`}
          onRetry={() => void load()}
        />
      </div>
    );
  }

  if (!dashboard || !graph) return null;

  const name = displayNameFromUserId(userId);
  const recoveryTotal = dashboard.bottlenecks.reduce(
    (s, b) => s + b.recovery_successes,
    0,
  );
  const robotMessage = deriveRobotMessage({
    isNewLearner: dashboard.is_new_learner,
    recoveryTotal,
    persistentCount: dashboard.bottlenecks.filter((b) => b.persistent).length,
    overallMastery: dashboard.overall.indicator,
  });

  return (
    <div className="mx-auto max-w-6xl px-4 py-8" data-testid="dashboard">
      {/* Greeting */}
      <header className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 sm:text-3xl">
            {greetingPrefix()}, {name} <span aria-hidden>👋</span>
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            {dashboard.is_new_learner
              ? "Your debugging journey starts here."
              : "Here's how your debugging journey is progressing."}
          </p>
        </div>
        <button
          onClick={() => void load()}
          className="rounded-md bg-panelAlt px-3 py-2 text-sm text-slate-300 ring-1 ring-white/10 transition hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
          data-testid="dashboard-refresh"
        >
          ↻ Refresh
        </button>
      </header>

      {robotMessage && (
        <div className="mb-5">
          <RobotNote message={robotMessage} />
        </div>
      )}

      {/* Top row: mastery hero + summary + continue learning */}
      <div className="grid gap-5 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <MasteryGauge overall={dashboard.overall} />
        </div>
        <div className="flex flex-col gap-5 lg:col-span-2">
          <SummaryStrip concepts={dashboard.concepts} />
          <ContinueLearning
            recommendation={dashboard.recommended_challenge}
            onStart={startChallenge}
            busy={starting}
          />
        </div>
      </div>

      {/* Second row: focus areas + knowledge graph preview */}
      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <FocusAreas bottlenecks={dashboard.bottlenecks} />
        <GraphPreviewCard
          href={`/dashboard/${userId}/knowledge-graph`}
          nodeCount={graph.nodes.length}
          isEmpty={graph.is_empty}
        />
      </div>

      {/* Recent activity */}
      <div className="mt-5">
        <ActivityTimeline timeline={dashboard.timeline} />
      </div>
    </div>
  );
}
