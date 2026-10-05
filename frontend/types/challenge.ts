// Mirrors backend app/models/challenge.py (student-safe view + request DTOs).
// NOTE: no hidden-answer fields exist here — the backend never sends them.

export type Difficulty = "beginner" | "developing" | "intermediate" | "advanced";

export type ChallengeType =
  | "fix_the_bug"
  | "complete_the_code"
  | "predict_the_output"
  | "small_build_task";

export interface VisibleTest {
  name: string;
}

export interface ChallengeView {
  id: string;
  title: string;
  description: string;
  concept: string;
  difficulty: Difficulty;
  task_type: ChallengeType;
  starter_code: string;
  predict_code: string | null;
  learning_objective: string;
  hints_available: number;
  visible_tests: VisibleTest[];
  total_tests: number;
}

export interface GenerateChallengeRequest {
  user_id: string;
  concept_key?: string | null;
  task_type?: ChallengeType | null;
  session_id?: string | null;
}

export interface SubmitChallengeRequest {
  user_id: string;
  code?: string | null;
  predicted_output?: string | null;
  attempts?: number;
  hints_used?: number;
  duration_ms?: number;
  session_id?: string | null;
}

export interface SubmitChallengeResponse {
  passed: boolean;
  passed_count: number;
  total_count: number;
  test_feedback: { name: string; passed: boolean }[];
  message: string;
  new_mastery: number | null;
}
