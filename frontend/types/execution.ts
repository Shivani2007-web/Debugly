// Mirrors backend app/models/execution.py.

export type ExecutionStatus =
  | "success"
  | "test_failed"
  | "syntax_error"
  | "runtime_error"
  | "timeout"
  | "internal_error";

export interface ErrorInfo {
  error_type: string | null;
  message: string | null;
  line: number | null;
  traceback: string | null;
}

export interface TestResult {
  name: string;
  passed: boolean;
  expected: unknown;
  actual: unknown;
  error: ErrorInfo | null;
  hidden: boolean;
}

export interface ExecutionResult {
  status: ExecutionStatus;
  stdout: string;
  stderr: string;
  error: ErrorInfo | null;
  test_results: TestResult[];
  passed_count: number;
  total_count: number;
  duration_ms: number;
  truncated: boolean;
}

export interface RunRequest {
  code: string;
  session_id?: string;
}

export interface SubmitRequest {
  code: string;
  task_id?: string;
  session_id?: string;
}
