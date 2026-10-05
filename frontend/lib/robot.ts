// Robot-state mapping: translates app events and tutor responses into one of
// the seven robot states. Kept pure and standalone so it is unit-testable and
// the single source of truth for how the UI reacts.

import type { ExecutionResult } from "@/types/execution";
import type { RobotState, TutorResponse } from "@/types/tutor";

// Event-driven states the frontend owns locally (not from the tutor).
export type RobotEvent =
  | "idle"
  | "thinking" // a request is in flight
  | "execution_failure" // code failed to run / tests failed
  | "wrong_answer" // student answered a tutor question incorrectly
  | "successful_correction" // tests now pass after a prior failure
  | "challenge_complete"; // reserved for Phase 6

export function robotForEvent(event: RobotEvent): RobotState {
  switch (event) {
    case "thinking":
      return "thinking";
    case "execution_failure":
      return "concerned";
    case "wrong_answer":
      return "encouraging";
    case "successful_correction":
      return "happy";
    case "challenge_complete":
      return "celebrating";
    case "idle":
    default:
      return "idle";
  }
}

// A tutor response already carries an authoritative robot_state; trust it.
export function robotForTutor(resp: TutorResponse): RobotState {
  return resp.robot_state;
}

// Derive the robot state from an execution result (used right after run/submit,
// before any tutor interaction).
export function robotForExecution(result: ExecutionResult): RobotState {
  switch (result.status) {
    case "success":
      // All tests passed (or clean run).
      return result.total_count > 0 ? "happy" : "idle";
    case "test_failed":
    case "runtime_error":
    case "syntax_error":
    case "timeout":
      return "concerned";
    case "internal_error":
    default:
      return "sad";
  }
}
