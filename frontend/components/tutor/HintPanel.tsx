"use client";

// Progressive hint UI. Renders the current TutorResponse (message, Socratic
// question, options, explanation) and offers the next action: answer the
// question, request the next hint level, or try again in the editor.

import { useState } from "react";
import type { TutorResponse } from "@/types/tutor";

interface HintPanelProps {
  response: TutorResponse | null;
  busy: boolean;
  onRequestHint: () => void;
  onAnswer: (answer: string, correct: boolean) => void;
  onExplain: () => void;
}

const LEVEL_LABEL: Record<number, string> = {
  1: "Level 1 · Question",
  2: "Level 2 · Direction",
  3: "Level 3 · Concept",
  4: "Level 4 · Guidance",
};

export function HintPanel({
  response,
  busy,
  onRequestHint,
  onAnswer,
  onExplain,
}: HintPanelProps) {
  const [freeAnswer, setFreeAnswer] = useState("");

  if (!response) {
    return (
      <div className="rounded-lg bg-panelAlt/50 p-4 text-sm text-slate-400 ring-1 ring-white/5">
        Run or submit your code. If Debugly spots a misconception, your tutor
        will help you reason through it here.
      </div>
    );
  }

  const atMaxLevel = response.hint_level === 4;

  return (
    <div className="space-y-3">
      <div className="rounded-lg bg-panelAlt/70 p-4 ring-1 ring-white/10">
        {response.hint_level && (
          <div className="mb-2 flex items-center gap-2">
            <span className="rounded-full bg-accentMuted/30 px-2 py-0.5 text-xs font-medium text-accent ring-1 ring-accent/20">
              {LEVEL_LABEL[response.hint_level]}
            </span>
            {response.is_fallback && (
              <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] uppercase text-slate-500">
                offline tutor
              </span>
            )}
          </div>
        )}

        <p className="text-sm leading-relaxed text-slate-100">{response.message}</p>

        {response.question && (
          <p className="mt-3 rounded-md bg-panel/60 p-3 text-sm italic text-accent">
            {response.question}
          </p>
        )}

        {response.explanation && (
          <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-300">
            {response.explanation}
          </p>
        )}
      </div>

      {/* Options for a multiple-choice Socratic question. */}
      {response.question && response.options.length > 0 && (
        <div className="space-y-2">
          {response.options.map((opt, i) => (
            <button
              key={i}
              disabled={busy}
              onClick={() => onAnswer(opt, i === 0)}
              className="w-full rounded-md bg-panelAlt px-3 py-2 text-left text-sm text-slate-200 ring-1 ring-white/10 transition hover:bg-white/10 disabled:opacity-50"
            >
              {opt}
            </button>
          ))}
        </div>
      )}

      {/* Free-text answer for an open Socratic question. */}
      {response.next_action === "answer_question" &&
        response.options.length === 0 && (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!freeAnswer.trim()) return;
              // We can't grade free text deterministically here; treat as an
              // attempt and let the student escalate if still stuck.
              onAnswer(freeAnswer.trim(), true);
              setFreeAnswer("");
            }}
            className="flex gap-2"
          >
            <input
              value={freeAnswer}
              onChange={(e) => setFreeAnswer(e.target.value)}
              disabled={busy}
              placeholder="Your thinking…"
              className="flex-1 rounded-md bg-panel px-3 py-2 text-sm text-slate-100 ring-1 ring-white/10 outline-none focus:ring-accent/40"
            />
            <button
              type="submit"
              disabled={busy}
              className="rounded-md bg-accentMuted px-3 py-2 text-sm font-medium text-white transition hover:bg-accent hover:text-panel disabled:opacity-50"
            >
              Send
            </button>
          </form>
        )}

      <div className="flex flex-wrap gap-2">
        <button
          onClick={onRequestHint}
          disabled={busy || atMaxLevel}
          className="rounded-md bg-accentMuted px-3 py-1.5 text-sm font-medium text-white transition hover:bg-accent hover:text-panel disabled:cursor-not-allowed disabled:opacity-40"
          title={atMaxLevel ? "You've reached the most detailed hint" : undefined}
        >
          {atMaxLevel ? "Max hint reached" : "I need another hint"}
        </button>
        <button
          onClick={onExplain}
          disabled={busy}
          className="rounded-md px-3 py-1.5 text-sm text-slate-400 transition hover:text-slate-200 disabled:opacity-50"
        >
          Explain the concept
        </button>
      </div>
    </div>
  );
}
