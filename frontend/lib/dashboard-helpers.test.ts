import { describe, it, expect } from "vitest";
import {
  deriveRobotMessage,
  deriveSummaryMetrics,
  displayNameFromUserId,
  greetingPrefix,
} from "./dashboard";

describe("displayNameFromUserId", () => {
  it("strips demo- prefix and capitalises", () => {
    expect(displayNameFromUserId("demo-ava")).toBe("Ava");
  });
  it("handles underscores/separators", () => {
    expect(displayNameFromUserId("student_7")).toBe("Student");
  });
  it("falls back to 'there' for empty/unknown", () => {
    expect(displayNameFromUserId("")).toBe("there");
    expect(displayNameFromUserId(null)).toBe("there");
    expect(displayNameFromUserId("demo-")).toBe("there");
  });
});

describe("greetingPrefix", () => {
  it("maps hours to greetings", () => {
    expect(greetingPrefix(new Date("2026-01-01T09:00:00"))).toBe("Good morning");
    expect(greetingPrefix(new Date("2026-01-01T14:00:00"))).toBe("Good afternoon");
    expect(greetingPrefix(new Date("2026-01-01T20:00:00"))).toBe("Good evening");
  });
});

describe("deriveSummaryMetrics", () => {
  it("derives totals only from real concept data", () => {
    const m = deriveSummaryMetrics([
      { successful_attempts: 2, attempts: 4, hint_dependency: 0.5 },
      { successful_attempts: 3, attempts: 3, hint_dependency: 0 },
      { successful_attempts: 0, attempts: 0, hint_dependency: 0 }, // not practiced
    ]);
    expect(m.problemsSolved).toBe(5);
    expect(m.conceptsPracticed).toBe(2); // the two with attempts > 0
    expect(m.independentSuccess).toBe(1); // loops: 0 hint dependency + success
    expect(m.usesHints).toBe(true);
  });

  it("is all-zero for a learner with no attempts", () => {
    const m = deriveSummaryMetrics([]);
    expect(m).toEqual({
      problemsSolved: 0,
      conceptsPracticed: 0,
      independentSuccess: 0,
      usesHints: false,
    });
  });
});

describe("deriveRobotMessage", () => {
  it("welcomes a new learner", () => {
    expect(
      deriveRobotMessage({ isNewLearner: true, recoveryTotal: 0, persistentCount: 0, overallMastery: 0 }),
    ).toMatch(/welcome/i);
  });
  it("celebrates recovery when there is real recovery evidence", () => {
    expect(
      deriveRobotMessage({ isNewLearner: false, recoveryTotal: 2, persistentCount: 1, overallMastery: 30 }),
    ).toMatch(/improving/i);
  });
  it("returns null when there is nothing truthful to say", () => {
    expect(
      deriveRobotMessage({ isNewLearner: false, recoveryTotal: 0, persistentCount: 0, overallMastery: 40 }),
    ).toBeNull();
  });
});
