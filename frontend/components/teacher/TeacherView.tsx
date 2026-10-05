"use client";

// Teacher dashboard: class-level analytics composed from the read-only
// /api/teacher endpoints. Includes a demo-seed button so the view has data
// during a presentation, and a drill-down into any student's journey.

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import type { StudentDetail, TeacherOverview } from "@/types/teacher";
import { formatConceptName } from "@/lib/dashboard";
import { LoadingState, ErrorState, EmptyState } from "@/components/ui/States";

export function TeacherView() {
  const [phase, setPhase] = useState<"loading" | "ready" | "error">("loading");
  const [overview, setOverview] = useState<TeacherOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<StudentDetail | null>(null);
  const [seeding, setSeeding] = useState(false);

  const load = useCallback(async () => {
    setPhase("loading");
    setError(null);
    try {
      setOverview(await api.teacherOverview());
      setPhase("ready");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load class data.");
      setPhase("error");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const seed = useCallback(async () => {
    setSeeding(true);
    try {
      await api.seedDemo();
      await load();
    } catch {
      /* non-fatal */
    } finally {
      setSeeding(false);
    }
  }, [load]);

  const openStudent = useCallback(async (userId: string) => {
    try {
      setSelected(await api.teacherStudentDetail(userId));
    } catch {
      /* ignore */
    }
  }, []);

  if (phase === "loading") return <LoadingState label="Loading class analytics…" />;
  if (phase === "error") return <ErrorState message={error ?? "Error"} onRetry={load} />;
  if (!overview) return null;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8" data-testid="teacher">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-100 sm:text-3xl">
            Class Overview
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Understand where your students are struggling and where they&apos;re improving.
          </p>
        </div>
        <button
          onClick={seed}
          disabled={seeding}
          className="rounded-md bg-panelAlt px-3 py-2 text-sm text-slate-300 ring-1 ring-white/10 hover:bg-white/10 disabled:opacity-50"
        >
          {seeding ? "Seeding…" : "Load demo class"}
        </button>
      </header>

      {overview.is_empty ? (
        <EmptyState
          title="No class activity yet"
          hint="Click “Load demo class” to populate a sample cohort, or have students start practicing."
        />
      ) : (
        <>
          <div className="mb-5 grid gap-4 sm:grid-cols-3">
            <Stat label="Students" value={String(overview.class_size)} />
            <Stat label="Avg mastery" value={overview.average_mastery.toFixed(0)} />
            <Stat
              label="Need attention"
              value={String(overview.students_needing_attention.length)}
              alert={overview.students_needing_attention.length > 0}
            />
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <section className="rounded-xl border border-white/10 bg-panelAlt/40 p-5">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Most Common Misconceptions
              </h2>
              <ul className="mt-3 space-y-2">
                {overview.common_misconceptions.slice(0, 6).map((m) => (
                  <li key={`${m.misconception_key}:${m.concept_key}`} className="flex items-center justify-between text-sm">
                    <span className="text-slate-200">
                      {m.misconception_key.replace(/_/g, " ")}
                      <span className="ml-2 text-xs text-slate-500">
                        {formatConceptName(m.concept_key)}
                      </span>
                    </span>
                    <span className="tabular-nums text-slate-400">
                      {m.students_affected} student{m.students_affected !== 1 ? "s" : ""}
                      {m.persistent_students > 0 && (
                        <span className="ml-1 text-rose-300">· {m.persistent_students} stuck</span>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            </section>

            <section className="rounded-xl border border-white/10 bg-panelAlt/40 p-5">
              <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Weakest Concepts
              </h2>
              <ul className="mt-3 space-y-2">
                {overview.concept_weaknesses.slice(0, 6).map((w) => (
                  <li key={w.concept_key} className="text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-200">{formatConceptName(w.concept_key)}</span>
                      <span className="tabular-nums text-slate-400">{w.average_mastery.toFixed(0)}</span>
                    </div>
                    <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-white/5">
                      <div
                        className="h-full rounded-full bg-amber-400"
                        style={{ width: `${Math.max(0, Math.min(100, w.average_mastery))}%` }}
                      />
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          </div>

          <section className="mt-5 rounded-xl border border-white/10 bg-panelAlt/40 p-5">
            <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
              Students Needing Attention
            </h2>
            {overview.students_needing_attention.length === 0 ? (
              <p className="mt-3 text-sm text-slate-500">Everyone's on track. 🎉</p>
            ) : (
              <ul className="mt-3 space-y-2">
                {overview.students_needing_attention.map((s) => (
                  <li key={s.user_id}>
                    <button
                      onClick={() => openStudent(s.user_id)}
                      className="flex w-full items-center justify-between rounded-lg bg-rose-500/10 p-3 text-left ring-1 ring-rose-500/20 transition hover:bg-rose-500/15"
                    >
                      <span className="text-sm font-medium text-slate-100">{s.user_id}</span>
                      <span className="text-xs text-rose-200">
                        mastery {s.overall_mastery.toFixed(0)} · {s.reason}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {selected && selected.found && (
            <StudentDrawer detail={selected} onClose={() => setSelected(null)} />
          )}
        </>
      )}
    </div>
  );
}

function Stat({ label, value, alert }: { label: string; value: string; alert?: boolean }) {
  return (
    <div className="rounded-xl border border-white/10 bg-panelAlt/40 p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${alert ? "text-rose-300" : "text-slate-100"}`}>
        {value}
      </p>
    </div>
  );
}

function StudentDrawer({ detail, onClose }: { detail: StudentDetail; onClose: () => void }) {
  return (
    <div className="mt-5 rounded-xl bg-panel/80 p-5 ring-1 ring-accent/30" data-testid="student-drawer">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-100">{detail.user_id}</h3>
        <div className="flex items-center gap-3">
          <Link
            href={`/dashboard/${detail.user_id}`}
            className="rounded-md bg-accentMuted px-3 py-1.5 text-xs font-medium text-white transition hover:bg-accent hover:text-panel focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
          >
            View full profile →
          </Link>
          <button onClick={onClose} className="text-sm text-slate-400 hover:text-slate-200">
            close
          </button>
        </div>
      </div>
      <p className="mt-1 text-sm text-slate-400">Overall mastery {detail.overall_mastery.toFixed(0)}</p>

      <div className="mt-3 grid gap-4 md:grid-cols-2">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Misconceptions</p>
          <ul className="mt-1 space-y-1 text-sm text-slate-300">
            {detail.misconceptions.length === 0 && <li className="text-slate-500">None recorded.</li>}
            {detail.misconceptions.map((m, i) => (
              <li key={i}>
                {String(m["misconception_key"]).replace(/_/g, " ")} ·{" "}
                {String(m["occurrences"])}×{m["persistent"] ? " (persistent)" : ""}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">Recent activity</p>
          <ul className="mt-1 space-y-1 text-xs text-slate-400">
            {detail.recent_events.slice(0, 8).map((e, i) => (
              <li key={i}>{String(e["event_type"]).replace(/_/g, " ")}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

