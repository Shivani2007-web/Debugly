"use client";

// "Continue Learning" — the prominent next-step action. The recommendation
// comes entirely from the Phase 6 selector (via the dashboard payload); the
// frontend NEVER chooses the challenge. The CTA triggers the existing generate
// endpoint through the parent handler.

import type { RecommendedChallenge } from "@/types/dashboard";
import { DIFFICULTY_COLOR, DIFFICULTY_LABEL } from "@/lib/challenge";
import { formatConceptName } from "@/lib/dashboard";
import type { Difficulty } from "@/types/challenge";

interface Props {
  recommendation: RecommendedChallenge;
  onStart?: () => void;
  busy?: boolean;
}

export function ContinueLearning({ recommendation, onStart, busy }: Props) {
  if (!recommendation.available) {
    return (
      <section
        id="continue-learning"
        className="rounded-xl border border-white/10 bg-panelAlt/40 p-5"
      >
        <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Continue Learning
        </h2>
        <p className="mt-3 text-sm text-slate-500">
          Practice a few tasks and Debugly will recommend a targeted challenge
          based on where you&apos;re struggling.
        </p>
      </section>
    );
  }

  const difficulty = recommendation.difficulty as Difficulty | null;

  return (
    <section
      id="continue-learning"
      className="rounded-xl border border-accent/20 bg-gradient-to-br from-accentMuted/15 to-panelAlt/40 p-5"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-accent">
          Continue Learning
        </h2>
        {difficulty && (
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${DIFFICULTY_COLOR[difficulty]}`}
          >
            {DIFFICULTY_LABEL[difficulty]}
          </span>
        )}
      </div>

      <h3 className="mt-3 text-lg font-semibold text-slate-100">
        {recommendation.concept_name
          ? formatConceptName(recommendation.concept_name)
          : "Next challenge"}
      </h3>

      {recommendation.learning_objective && (
        <p className="mt-1 text-sm leading-relaxed text-slate-300">
          {recommendation.learning_objective}
        </p>
      )}
      {recommendation.misconception_name && (
        <p className="mt-1 text-xs text-slate-500">
          Targeting: {recommendation.misconception_name}
        </p>
      )}

      <button
        onClick={onStart}
        disabled={busy}
        className="mt-4 rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
      >
        {busy ? "Starting…" : "Start Challenge →"}
      </button>
    </section>
  );
}
