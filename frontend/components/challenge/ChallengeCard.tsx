"use client";

// Personalized challenge UI. Fix-the-Bug (and other code challenges) load the
// starter code into Monaco and submit for grading via the backend, which feeds
// the result into mastery. Predict-the-Output uses a text answer. No hidden
// answers are ever present client-side.

import dynamic from "next/dynamic";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import type {
  ChallengeView,
  SubmitChallengeResponse,
} from "@/types/challenge";
import {
  CHALLENGE_TYPE_LABEL,
  DIFFICULTY_COLOR,
  DIFFICULTY_LABEL,
  isCodeChallenge,
} from "@/lib/challenge";

const CodeEditor = dynamic(
  () => import("@/components/ide/CodeEditor").then((m) => m.CodeEditor),
  { ssr: false },
);

interface ChallengeCardProps {
  userId: string;
  // When provided, loads this challenge; otherwise generates a personalized one.
  challengeId?: string;
  onSolved?: (newMastery: number | null) => void;
}

export function ChallengeCard({ userId, challengeId, onSolved }: ChallengeCardProps) {
  const [challenge, setChallenge] = useState<ChallengeView | null>(null);
  const [code, setCode] = useState("");
  const [predicted, setPredicted] = useState("");
  const [result, setResult] = useState<SubmitChallengeResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attempts, setAttempts] = useState(0);

  const load = useCallback(async () => {
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const c = challengeId
        ? await api.getChallenge(challengeId)
        : await api.generateChallenge({ user_id: userId });
      setChallenge(c);
      setCode(c.starter_code);
      setPredicted("");
      setAttempts(0);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load challenge.");
    } finally {
      setBusy(false);
    }
  }, [challengeId, userId]);

  useEffect(() => {
    void load();
  }, [load]);

  const submit = useCallback(async () => {
    if (!challenge) return;
    setBusy(true);
    setError(null);
    const nextAttempts = attempts + 1;
    setAttempts(nextAttempts);
    try {
      const isCode = isCodeChallenge(challenge.task_type);
      const resp = await api.submitChallenge(challenge.id, {
        user_id: userId,
        code: isCode ? code : null,
        predicted_output: isCode ? null : predicted,
        attempts: nextAttempts,
      });
      setResult(resp);
      if (resp.passed) onSolved?.(resp.new_mastery);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Submission failed.");
    } finally {
      setBusy(false);
    }
  }, [challenge, attempts, userId, code, predicted, onSolved]);

  if (error) {
    return (
      <div className="rounded-lg bg-rose-500/10 p-4 text-sm text-rose-300">
        {error}
      </div>
    );
  }

  if (!challenge) {
    return <div className="p-4 text-sm text-slate-500">Loading challenge…</div>;
  }

  const isCode = isCodeChallenge(challenge.task_type);

  return (
    <div className="flex flex-col gap-4">
      <header>
        <div className="flex items-center gap-2">
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${DIFFICULTY_COLOR[challenge.difficulty]}`}
          >
            {DIFFICULTY_LABEL[challenge.difficulty]}
          </span>
          <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs text-slate-400">
            {CHALLENGE_TYPE_LABEL[challenge.task_type]}
          </span>
          <span className="text-xs text-slate-500">· {challenge.concept}</span>
        </div>
        <h3 className="mt-2 text-lg font-semibold text-slate-100">{challenge.title}</h3>
        <p className="mt-1 whitespace-pre-wrap text-sm text-slate-300">
          {challenge.description}
        </p>
        {challenge.learning_objective && (
          <p className="mt-2 text-xs italic text-slate-500">
            🎯 {challenge.learning_objective}
          </p>
        )}
      </header>

      {isCode ? (
        <div className="h-64 overflow-hidden rounded-md ring-1 ring-white/10">
          <CodeEditor value={code} onChange={setCode} readOnly={busy} />
        </div>
      ) : (
        <div className="space-y-2">
          {challenge.predict_code && (
            <pre className="overflow-x-auto rounded-md bg-panel p-3 font-mono text-sm text-slate-200 ring-1 ring-white/10">
              {challenge.predict_code}
            </pre>
          )}
          <textarea
            value={predicted}
            onChange={(e) => setPredicted(e.target.value)}
            disabled={busy}
            placeholder="Type the exact output…"
            className="h-24 w-full rounded-md bg-panel p-3 font-mono text-sm text-slate-100 ring-1 ring-white/10 outline-none focus:ring-accent/40"
          />
        </div>
      )}

      {challenge.visible_tests.length > 0 && (
        <div className="text-xs text-slate-500">
          Tests: {challenge.visible_tests.map((t) => t.name).join(" · ")}
          {challenge.total_tests > challenge.visible_tests.length &&
            ` (+${challenge.total_tests - challenge.visible_tests.length} hidden)`}
        </div>
      )}

      <div className="flex items-center gap-2">
        <button
          onClick={submit}
          disabled={busy}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:opacity-50"
        >
          Submit solution
        </button>
        <button
          onClick={load}
          disabled={busy}
          className="rounded-md px-3 py-2 text-sm text-slate-400 transition hover:text-slate-200 disabled:opacity-50"
        >
          New challenge
        </button>
      </div>

      {result && (
        <div
          className={`rounded-md p-3 text-sm ring-1 ${
            result.passed
              ? "bg-emerald-500/10 text-emerald-300 ring-emerald-500/20"
              : "bg-rose-500/10 text-rose-200 ring-rose-500/20"
          }`}
        >
          <p className="font-medium">{result.message}</p>
          {result.total_count > 0 && (
            <p className="mt-1 text-xs opacity-80">
              {result.passed_count}/{result.total_count} tests passed
            </p>
          )}
          {result.new_mastery != null && (
            <p className="mt-1 text-xs opacity-80">
              Mastery now: {result.new_mastery}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
