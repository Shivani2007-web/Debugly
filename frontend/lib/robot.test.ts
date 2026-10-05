// Scenario 5: the frontend correctly maps tutor responses and app events to
// robot states.

import { describe, it, expect } from "vitest";
import { robotForEvent, robotForTutor, robotForExecution } from "./robot";
import type { TutorResponse } from "@/types/tutor";
import type { ExecutionResult } from "@/types/execution";

function tutor(partial: Partial<TutorResponse>): TutorResponse {
  return {
    message: "",
    hint_level: 1,
    question: null,
    options: [],
    explanation: null,
    robot_state: "idle",
    next_action: "continue",
    is_fallback: false,
    grounded_in: null,
    ...partial,
  };
}

function exec(partial: Partial<ExecutionResult>): ExecutionResult {
  return {
    status: "success",
    stdout: "",
    stderr: "",
    error: null,
    test_results: [],
    passed_count: 0,
    total_count: 0,
    duration_ms: 0,
    truncated: false,
    ...partial,
  };
}

describe("robotForEvent", () => {
  it("maps execution failure to concerned", () => {
    expect(robotForEvent("execution_failure")).toBe("concerned");
  });
  it("maps wrong answer to encouraging", () => {
    expect(robotForEvent("wrong_answer")).toBe("encouraging");
  });
  it("maps successful correction to happy", () => {
    expect(robotForEvent("successful_correction")).toBe("happy");
  });
  it("maps challenge completion to celebrating", () => {
    expect(robotForEvent("challenge_complete")).toBe("celebrating");
  });
  it("maps thinking and idle", () => {
    expect(robotForEvent("thinking")).toBe("thinking");
    expect(robotForEvent("idle")).toBe("idle");
  });
});

describe("robotForTutor", () => {
  it("trusts the tutor's authoritative robot_state", () => {
    expect(robotForTutor(tutor({ robot_state: "celebrating" }))).toBe("celebrating");
    expect(robotForTutor(tutor({ robot_state: "concerned" }))).toBe("concerned");
  });
});

describe("robotForExecution", () => {
  it("passing tests -> happy", () => {
    expect(robotForExecution(exec({ status: "success", total_count: 3, passed_count: 3 }))).toBe("happy");
  });
  it("clean run with no tests -> idle", () => {
    expect(robotForExecution(exec({ status: "success", total_count: 0 }))).toBe("idle");
  });
  it("failures -> concerned", () => {
    expect(robotForExecution(exec({ status: "test_failed" }))).toBe("concerned");
    expect(robotForExecution(exec({ status: "runtime_error" }))).toBe("concerned");
    expect(robotForExecution(exec({ status: "syntax_error" }))).toBe("concerned");
    expect(robotForExecution(exec({ status: "timeout" }))).toBe("concerned");
  });
  it("internal error -> sad", () => {
    expect(robotForExecution(exec({ status: "internal_error" }))).toBe("sad");
  });
});
