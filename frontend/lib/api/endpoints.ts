// Typed endpoint functions. Components call these instead of using the raw
// client, keeping the surface area of the backend contract in one module.

import { apiClient } from "./client";
import type { HealthResponse } from "@/types/health";
import type { Task, TaskSummary } from "@/types/task";
import type {
  ExecutionResult,
  RunRequest,
  SubmitRequest,
} from "@/types/execution";
import type { DiagnosisResult } from "@/types/misconception";
import type { TutorRequest, TutorResponse } from "@/types/tutor";
import type {
  BehaviorEvent,
  ConceptMastery,
  EventRecordRequest,
  LearnerSummary,
  MasteryTrendPoint,
  RecentMisconception,
  Recommendation,
} from "@/types/profile";
import type {
  ChallengeView,
  GenerateChallengeRequest,
  SubmitChallengeRequest,
  SubmitChallengeResponse,
} from "@/types/challenge";
import type { DashboardResponse, KnowledgeGraph } from "@/types/dashboard";
import type {
  ReuseCheckRequest,
  ReuseCheckResponse,
  StudentDetail,
  StudentListEntry,
  TeacherOverview,
} from "@/types/teacher";

export const api = {
  health: () => apiClient.get<HealthResponse>("/health"),

  // ---- Tasks ----
  listTasks: () => apiClient.get<TaskSummary[]>("/tasks"),
  getTask: (taskId: string) => apiClient.get<Task>(`/tasks/${taskId}`),

  // ---- Execution ----
  runCode: (body: RunRequest) =>
    apiClient.post<ExecutionResult>("/execution/run", body),
  submitCode: (body: SubmitRequest) =>
    apiClient.post<ExecutionResult>("/execution/submit", body),

  // ---- Analysis (Phase 3) ----
  diagnose: (body: {
    code: string;
    execution_result?: unknown;
    task_id?: string;
    session_id?: string;
  }) => apiClient.post<DiagnosisResult>("/analysis/diagnose", body),

  // ---- Tutor (Phase 4) ----
  tutorHint: (body: TutorRequest) =>
    apiClient.post<TutorResponse>("/tutor/hint", body),
  tutorExplain: (body: TutorRequest) =>
    apiClient.post<TutorResponse>("/tutor/explain", body),
  tutorFeedback: (body: TutorRequest) =>
    apiClient.post<TutorResponse>("/tutor/feedback", body),

  // ---- Behavior tracking (Phase 5) ----
  recordEvent: (body: EventRecordRequest) =>
    apiClient.post<{ recorded: number; total_events: number }>(
      "/behavior/event",
      body,
    ),
  recordEvents: (events: EventRecordRequest[]) =>
    apiClient.post<{ recorded: number; total_events: number }>(
      "/behavior/events",
      { events },
    ),

  // ---- Learner profile (Phase 5, read-only) ----
  learnerSummary: (userId: string) =>
    apiClient.get<LearnerSummary>(`/profile/${userId}/summary`),
  conceptMastery: (userId: string) =>
    apiClient.get<ConceptMastery[]>(`/profile/${userId}/mastery`),
  recentMisconceptions: (userId: string) =>
    apiClient.get<RecentMisconception[]>(`/profile/${userId}/misconceptions`),
  recentEvents: (userId: string, limit = 20) =>
    apiClient.get<BehaviorEvent[]>(`/profile/${userId}/events?limit=${limit}`),
  masteryTrend: (userId: string, conceptKey?: string) =>
    apiClient.get<MasteryTrendPoint[]>(
      `/profile/${userId}/trend${conceptKey ? `?concept_key=${conceptKey}` : ""}`,
    ),
  recommendations: (userId: string) =>
    apiClient.get<Recommendation[]>(`/profile/${userId}/recommendations`),

  // ---- Challenges (Phase 6) ----
  generateChallenge: (body: GenerateChallengeRequest) =>
    apiClient.post<ChallengeView>("/challenges/generate", body),
  getChallenge: (challengeId: string) =>
    apiClient.get<ChallengeView>(`/challenges/${challengeId}`),
  submitChallenge: (challengeId: string, body: SubmitChallengeRequest) =>
    apiClient.post<SubmitChallengeResponse>(
      `/challenges/${challengeId}/submit`,
      body,
    ),

  // ---- Learner analytics (Phase 7, read-only) ----
  dashboard: (userId: string) =>
    apiClient.get<DashboardResponse>(`/learner/dashboard?user_id=${userId}`),
  knowledgeGraph: (userId: string) =>
    apiClient.get<KnowledgeGraph>(`/learner/knowledge-graph?user_id=${userId}`),

  // ---- Teacher (Phase 9, read-only) ----
  teacherOverview: () => apiClient.get<TeacherOverview>("/teacher/overview"),
  teacherStudents: () => apiClient.get<StudentListEntry[]>("/teacher/students"),
  teacherStudentDetail: (userId: string) =>
    apiClient.get<StudentDetail>(`/teacher/student/${userId}`),

  // ---- Smart Reuse (Phase 9) ----
  checkReuse: (body: ReuseCheckRequest) =>
    apiClient.post<ReuseCheckResponse>("/reuse/check", body),

  // ---- Demo mode (Phase 9) ----
  seedDemo: () =>
    apiClient.post<{ seeded_students: string[]; count: number }>("/demo/seed"),
};
