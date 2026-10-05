// Mirrors backend app/models/behavior.py (read-side DTOs + event input).

export type BehaviorEventType =
  | "code_execution"
  | "submission"
  | "syntax_error"
  | "runtime_error"
  | "test_failure"
  | "successful_execution"
  | "region_repeatedly_modified"
  | "hint_requested"
  | "hint_level_reached"
  | "tutor_question_answered"
  | "tutor_answer_correct"
  | "tutor_answer_incorrect"
  | "successful_correction"
  | "misconception_detected"
  | "challenge_attempt"
  | "code_reuse_paste";

export interface EventRecordRequest {
  user_id: string;
  session_id?: string | null;
  event_type: BehaviorEventType;
  concept_key?: string | null;
  misconception_key?: string | null;
  error_type?: string | null;
  hint_level?: number | null;
  difficulty?: string | null;
  payload?: Record<string, unknown>;
}

export interface ConceptMastery {
  concept_key: string;
  mastery: number;
  attempts: number;
  successful_attempts: number;
  has_persistent_gap: boolean;
  hint_dependency: number;
}

export interface RecentMisconception {
  concept_key: string;
  misconception_key: string;
  occurrences: number;
  persistent: boolean;
}

export interface Recommendation {
  concept_key: string;
  reason: string;
  suggested_difficulty: string;
}

export interface LearnerSummary {
  user_id: string;
  overall_mastery: number;
  concept_count: number;
  total_events: number;
  concepts: ConceptMastery[];
  persistent_gaps: string[];
  is_new_learner: boolean;
}

export interface MasteryTrendPoint {
  concept_key: string;
  mastery: number;
  at: string;
}

export interface BehaviorEvent {
  user_id: string;
  session_id?: string | null;
  event_type: BehaviorEventType;
  concept_key?: string | null;
  misconception_key?: string | null;
  error_type?: string | null;
  hint_level?: number | null;
  difficulty?: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}
