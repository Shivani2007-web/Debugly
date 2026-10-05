// Challenge presentation helpers (pure, testable).

import type { ChallengeType, Difficulty } from "@/types/challenge";

export const DIFFICULTY_LABEL: Record<Difficulty, string> = {
  beginner: "Beginner",
  developing: "Developing",
  intermediate: "Intermediate",
  advanced: "Advanced",
};

export const DIFFICULTY_COLOR: Record<Difficulty, string> = {
  beginner: "bg-emerald-500/15 text-emerald-300 ring-emerald-500/30",
  developing: "bg-sky-500/15 text-sky-300 ring-sky-500/30",
  intermediate: "bg-amber-500/15 text-amber-300 ring-amber-500/30",
  advanced: "bg-rose-500/15 text-rose-300 ring-rose-500/30",
};

export const CHALLENGE_TYPE_LABEL: Record<ChallengeType, string> = {
  fix_the_bug: "Fix the Bug",
  complete_the_code: "Complete the Code",
  predict_the_output: "Predict the Output",
  small_build_task: "Small Build Task",
};

// Which challenge types are solved by writing/editing code in the editor.
export function isCodeChallenge(type: ChallengeType): boolean {
  return (
    type === "fix_the_bug" ||
    type === "complete_the_code" ||
    type === "small_build_task"
  );
}
