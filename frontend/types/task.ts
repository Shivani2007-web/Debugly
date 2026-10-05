// Mirrors backend app/models/task.py.

import type { TestResult } from "./execution";

export interface TestCase {
  name: string;
  function_name: string;
  args: unknown[];
  kwargs: Record<string, unknown>;
  expected: unknown;
  hidden: boolean;
}

export interface ReuseZone {
  kind: "reusable" | "editable" | "learning_critical";
  start_line: number;
  end_line: number;
}

export interface Task {
  id: string;
  title: string;
  prompt: string;
  starter_code: string;
  test_cases: TestCase[];
  concept_keys: string[];
  reuse_zones: ReuseZone[];
}

export interface TaskSummary {
  id: string;
  title: string;
  prompt: string;
}

// Re-export for convenience in components that render results next to tasks.
export type { TestResult };
