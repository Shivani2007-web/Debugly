// Mirrors backend app/models/tutor.py.

import type { DetectedMisconception } from "./misconception";

export type RobotState =
  | "idle"
  | "thinking"
  | "concerned"
  | "encouraging"
  | "happy"
  | "celebrating"
  | "sad";

export type NextAction =
  | "answer_question"
  | "request_next_hint"
  | "try_again"
  | "continue";

export type TutorInteractionType = "hint" | "explain" | "feedback";

export interface PriorAttempt {
  attempt_number: number;
  error_type?: string | null;
  passed: boolean;
}

export interface TutorRequest {
  session_id: string;
  interaction?: TutorInteractionType;
  misconception?: DetectedMisconception | null;
  task_prompt?: string | null;
  error_type?: string | null;
  error_message?: string | null;
  student_answer?: string | null;
  answer_was_correct?: boolean | null;
  prior_attempts?: PriorAttempt[];
}

export interface TutorResponse {
  message: string;
  hint_level: 1 | 2 | 3 | 4 | null;
  question: string | null;
  options: string[];
  explanation: string | null;
  robot_state: RobotState;
  next_action: NextAction;
  is_fallback: boolean;
  grounded_in: string | null;
}
