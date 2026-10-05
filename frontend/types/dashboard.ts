// Mirrors backend app/models/dashboard.py.

import type { MasteryTrendPoint } from "./profile";

export type MasteryBand =
  | "not_started"
  | "emerging"
  | "developing"
  | "proficient"
  | "strong";

export interface OverallMastery {
  indicator: number;
  band: MasteryBand;
  label: string;
  disclaimer: string;
  trend: MasteryTrendPoint[];
}

export interface ConceptProgress {
  concept_key: string;
  mastery: number;
  band: MasteryBand;
  attempts: number;
  successful_attempts: number;
  has_persistent_gap: boolean;
  hint_dependency: number;
  trend: number[];
}

export interface Bottleneck {
  concept_key: string;
  misconception_key: string;
  occurrences: number;
  persistent: boolean;
  hint_dependency: number;
  recovery_successes: number;
  concept_mastery: number;
}

export interface TimelineEvent {
  event_type: string;
  concept_key: string | null;
  misconception_key: string | null;
  error_type: string | null;
  hint_level: number | null;
  difficulty: string | null;
  label: string;
  at: string;
}

export interface RecommendedChallenge {
  available: boolean;
  concept_key: string | null;
  concept_name: string | null;
  misconception_key: string | null;
  misconception_name: string | null;
  difficulty: string | null;
  task_type: string | null;
  learning_objective: string | null;
  reason: string | null;
}

export interface DashboardResponse {
  user_id: string;
  is_new_learner: boolean;
  overall: OverallMastery;
  concepts: ConceptProgress[];
  bottlenecks: Bottleneck[];
  timeline: TimelineEvent[];
  recommended_challenge: RecommendedChallenge;
}

// ---- Knowledge graph ----

export type GraphNodeType =
  | "student"
  | "concept"
  | "misconception"
  | "evidence"
  | "intervention"
  | "challenge"
  | "outcome";

export interface GraphNode {
  id: string;
  type: GraphNodeType;
  label: string;
  healthy: boolean | null;
  meta: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
}

export interface KnowledgeGraph {
  user_id: string;
  is_empty: boolean;
  nodes: GraphNode[];
  edges: GraphEdge[];
}
