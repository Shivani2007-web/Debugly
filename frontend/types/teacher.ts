// Mirrors backend app/models/teacher.py and app/models/reuse.py.

export interface CommonMisconception {
  misconception_key: string;
  concept_key: string;
  students_affected: number;
  total_occurrences: number;
  persistent_students: number;
}

export interface ConceptWeakness {
  concept_key: string;
  average_mastery: number;
  students_practicing: number;
  students_with_gap: number;
}

export interface StudentNeedingAttention {
  user_id: string;
  overall_mastery: number;
  persistent_gap_count: number;
  reason: string;
}

export interface StudentListEntry {
  user_id: string;
  overall_mastery: number;
  concept_count: number;
  persistent_gaps: string[];
}

export interface TeacherOverview {
  class_size: number;
  average_mastery: number;
  common_misconceptions: CommonMisconception[];
  concept_weaknesses: ConceptWeakness[];
  students_needing_attention: StudentNeedingAttention[];
  is_empty: boolean;
}

export interface StudentDetail {
  user_id: string;
  overall_mastery: number;
  concepts: Record<string, unknown>[];
  misconceptions: Record<string, unknown>[];
  recent_events: Record<string, unknown>[];
  found: boolean;
}

// ---- Smart Reuse ----
export type ReuseVerdict = "allowed" | "flagged" | "unrestricted";

export interface ReuseCheckRequest {
  user_id: string;
  task_id?: string | null;
  start_line: number;
  end_line: number;
  char_count?: number;
  source?: string;
  session_id?: string | null;
}

export interface ReuseCheckResponse {
  verdict: ReuseVerdict;
  overlaps: string[];
  message: string;
  allowed: boolean;
  learning_critical_overlap: boolean;
}
