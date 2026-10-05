"use client";

// The right-side tutor panel: robot companion + diagnosis summary + progressive
// hint UI. It owns the tutor conversation state and the robot state, reacting
// to the latest execution result handed down from the IDE.

import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api/endpoints";
import { ApiError } from "@/lib/api/client";
import type { ExecutionResult } from "@/types/execution";
import type { DetectedMisconception } from "@/types/misconception";
import type { RobotState, TutorResponse } from "@/types/tutor";
import { robotForEvent, robotForExecution } from "@/lib/robot";
import { RobotCompanion } from "./RobotCompanion";
import { HintPanel } from "./HintPanel";

interface TutorPanelProps {
  sessionId: string;
  taskPrompt: string;
  code: string;
  // The latest execution result (null until the student runs/submits).
  lastResult: ExecutionResult | null;
  resultVersion: number;
}

export function TutorPanel({
  sessionId,
  taskPrompt,
  code,
  lastResult,
  resultVersion,
}: TutorPanelProps) {
  const [robotState, setRobotState] = useState<RobotState>("idle");
  const [robotMessage, setRobotMessage] = useState<string | null>(null);
  const [misconception, setMisconception] = useState<DetectedMisconception | null>(null);
  const [tutorResponse, setTutorResponse] = useState<TutorResponse | null>(null);
  const [busy, setBusy] = useState(false);

  // React to a fresh execution: diagnose, then set robot + reset tutor thread.
  useEffect(() => {
    if (!lastResult) return;
    let active = true;

    (async () => {
      // Clean success → celebrate/encourage; if a prior misconception was being
      // worked on, send correction feedback.
      if (
        lastResult.status === "success" &&
        lastResult.total_count > 0 &&
        lastResult.passed_count === lastResult.total_count
      ) {
        if (misconception) {
          await sendFeedback(misconception);
        } else {
          setRobotState("happy");
          setRobotMessage("All tests passed. Nice work!");
        }
        return;
      }

      // Otherwise, run diagnosis to find the misconception to teach.
      setRobotState(robotForExecution(lastResult));
      setBusy(true);
      try {
        const diag = await api.diagnose({
          code,
          execution_result: lastResult,
          session_id: sessionId,
        });
        if (!active) return;
        const top = diag.misconceptions[0] ?? null;
        setMisconception(top);
        setTutorResponse(null);
        if (top) {
          setRobotState("concerned");
          setRobotMessage(`I think this is about ${top.concept.toLowerCase()}.`);
        } else {
          setRobotMessage("Let's look at what happened.");
        }
      } catch {
        if (active) setRobotMessage(null);
      } finally {
        if (active) setBusy(false);
      }
    })();

    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resultVersion]);

  const applyTutor = useCallback((resp: TutorResponse) => {
    setTutorResponse(resp);
    setRobotState(resp.robot_state);
    setRobotMessage(resp.message);
  }, []);

  const requestHint = useCallback(async () => {
    setBusy(true);
    setRobotState(robotForEvent("thinking"));
    try {
      const resp = await api.tutorHint({
        session_id: sessionId,
        misconception,
        task_prompt: taskPrompt,
        error_type: lastResult?.error?.error_type ?? null,
        error_message: lastResult?.error?.message ?? null,
      });
      applyTutor(resp);
    } catch (err) {
      setRobotState("sad");
      setRobotMessage(
        err instanceof ApiError ? "I couldn't reach the tutor." : "Something went wrong.",
      );
    } finally {
      setBusy(false);
    }
  }, [sessionId, misconception, taskPrompt, lastResult, applyTutor]);

  const answerQuestion = useCallback(
    async (answer: string, correct: boolean) => {
      setBusy(true);
      setRobotState(robotForEvent("thinking"));
      try {
        const resp = await api.tutorHint({
          session_id: sessionId,
          misconception,
          task_prompt: taskPrompt,
          student_answer: answer,
          answer_was_correct: correct,
        });
        applyTutor(resp);
      } catch {
        setRobotState("sad");
        setRobotMessage("Something went wrong.");
      } finally {
        setBusy(false);
      }
    },
    [sessionId, misconception, taskPrompt, applyTutor],
  );

  const explain = useCallback(async () => {
    setBusy(true);
    setRobotState(robotForEvent("thinking"));
    try {
      const resp = await api.tutorExplain({
        session_id: sessionId,
        misconception,
        task_prompt: taskPrompt,
      });
      applyTutor(resp);
    } catch {
      setRobotState("sad");
      setRobotMessage("Something went wrong.");
    } finally {
      setBusy(false);
    }
  }, [sessionId, misconception, taskPrompt, applyTutor]);

  async function sendFeedback(m: DetectedMisconception) {
    setBusy(true);
    try {
      const resp = await api.tutorFeedback({
        session_id: sessionId,
        misconception: m,
        task_prompt: taskPrompt,
      });
      applyTutor(resp);
      setMisconception(null); // cleared the issue
    } catch {
      setRobotState("celebrating");
      setRobotMessage("All tests passed. 🎉");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-4">
      <div className="rounded-xl bg-panelAlt/40 p-4 ring-1 ring-white/5">
        <RobotCompanion state={robotState} message={robotMessage} />
      </div>

      {misconception && (
        <div className="rounded-lg bg-panel/60 p-3 text-xs ring-1 ring-white/5">
          <p className="font-semibold text-slate-300">
            {misconception.concept}: {misconception.misconception}
          </p>
          <p className="mt-1 text-slate-500">
            confidence {Math.round(misconception.confidence * 100)}%
            {misconception.lines.length > 0 && ` · line ${misconception.lines.join(", ")}`}
          </p>
        </div>
      )}

      <HintPanel
        response={tutorResponse}
        busy={busy}
        onRequestHint={requestHint}
        onAnswer={answerQuestion}
        onExplain={explain}
      />

      {misconception && !tutorResponse && (
        <button
          onClick={requestHint}
          disabled={busy}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:opacity-50"
        >
          Ask the tutor for a hint
        </button>
      )}
    </div>
  );
}
