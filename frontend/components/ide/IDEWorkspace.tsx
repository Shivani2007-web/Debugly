"use client";

// The IDE workspace: loads a task, owns code + result state, and wires the
// Run/Submit actions to the backend. Layout: task (left) · editor + output
// (center) · tutor placeholder (right, reserved for Phase 4).

import dynamic from "next/dynamic";
import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import type { Task } from "@/types/task";
import type { ExecutionResult } from "@/types/execution";
import { TaskPanel } from "./TaskPanel";
import { RunControls } from "./RunControls";
import { BottomPanel } from "./BottomPanel";
import { TutorPanel } from "@/components/tutor/TutorPanel";

// Monaco must load client-side only (it touches `window`).
const CodeEditor = dynamic(
  () => import("./CodeEditor").then((m) => m.CodeEditor),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full items-center justify-center text-sm text-slate-500">
        Loading editor…
      </div>
    ),
  },
);

export function IDEWorkspace({ taskId }: { taskId: string }) {
  const [task, setTask] = useState<Task | null>(null);
  const [code, setCode] = useState<string>("");
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [preferredTab, setPreferredTab] = useState<"output" | "tests">("output");
  const [resultVersion, setResultVersion] = useState(0);

  // Load the task + seed the editor with starter code.
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const t = await api.getTask(taskId);
        if (!active) return;
        setTask(t);
        setCode(t.starter_code);
      } catch (err) {
        if (!active) return;
        setLoadError(
          err instanceof ApiError ? err.message : "Failed to load task.",
        );
      }
    })();
    return () => {
      active = false;
    };
  }, [taskId]);

  const showResult = useCallback(
    (r: ExecutionResult, tab: "output" | "tests") => {
      setResult(r);
      setPreferredTab(tab);
      setResultVersion((v) => v + 1);
    },
    [],
  );

  const handleRun = useCallback(async () => {
    setBusy(true);
    try {
      const r = await api.runCode({ code });
      showResult(r, "output");
    } catch (err) {
      showResult(
        {
          status: "internal_error",
          stdout: "",
          stderr:
            err instanceof ApiError ? err.message : "Request failed.",
          error: null,
          test_results: [],
          passed_count: 0,
          total_count: 0,
          duration_ms: 0,
          truncated: false,
        },
        "output",
      );
    } finally {
      setBusy(false);
    }
  }, [code, showResult]);

  const handleSubmit = useCallback(async () => {
    setBusy(true);
    try {
      const r = await api.submitCode({ code, task_id: taskId });
      // A syntax error has no tests to show; keep the user on Output.
      showResult(r, r.status === "syntax_error" ? "output" : "tests");
    } catch (err) {
      showResult(
        {
          status: "internal_error",
          stdout: "",
          stderr: err instanceof ApiError ? err.message : "Request failed.",
          error: null,
          test_results: [],
          passed_count: 0,
          total_count: 0,
          duration_ms: 0,
          truncated: false,
        },
        "output",
      );
    } finally {
      setBusy(false);
    }
  }, [code, taskId, showResult]);

  const handleReset = useCallback(() => {
    if (task) setCode(task.starter_code);
  }, [task]);

  if (loadError) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="rounded-md bg-rose-500/10 px-4 py-3 text-sm text-rose-300">
          {loadError} — is the backend running?
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-panel text-slate-100">
      {/* Top bar */}
      <header className="flex shrink-0 items-center gap-3 border-b border-white/10 px-4 py-2">
        <span className="bg-gradient-to-r from-accent to-indigo-400 bg-clip-text text-lg font-bold text-transparent">
          Debugly
        </span>
        <span className="text-sm text-slate-500">{task?.title ?? "…"}</span>
      </header>

      {/* Body: three columns */}
      <div className="flex min-h-0 flex-1">
        {/* Left: task */}
        <aside className="w-72 shrink-0 border-r border-white/10 bg-panelAlt/30">
          <TaskPanel task={task} />
        </aside>

        {/* Center: editor + controls + bottom panel */}
        <main className="flex min-w-0 flex-1 flex-col">
          <div className="flex shrink-0 items-center border-b border-white/10 px-3 py-2">
            <RunControls
              onRun={handleRun}
              onSubmit={handleSubmit}
              onReset={handleReset}
              busy={busy}
            />
          </div>

          <div className="min-h-0 flex-[3] border-b border-white/10">
            <CodeEditor value={code} onChange={setCode} readOnly={busy} />
          </div>

          <div className="min-h-0 flex-[2]">
            <BottomPanel
              result={result}
              preferredTab={preferredTab}
              resultVersion={resultVersion}
            />
          </div>
        </main>

        {/* Right: the robot tutor (Phase 4). */}
        <aside className="hidden w-80 shrink-0 border-l border-white/10 bg-panelAlt/30 lg:block">
          <TutorPanel
            sessionId={taskId}
            taskPrompt={task?.prompt ?? ""}
            code={code}
            lastResult={result}
            resultVersion={resultVersion}
          />
        </aside>
      </div>
    </div>
  );
}
