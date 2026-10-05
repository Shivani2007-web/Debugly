import { describe, it, expect } from "vitest";
import {
  CHALLENGE_TYPE_LABEL,
  DIFFICULTY_COLOR,
  DIFFICULTY_LABEL,
  isCodeChallenge,
} from "./challenge";

describe("challenge helpers", () => {
  it("labels all difficulties", () => {
    expect(DIFFICULTY_LABEL.beginner).toBe("Beginner");
    expect(DIFFICULTY_LABEL.advanced).toBe("Advanced");
    expect(Object.keys(DIFFICULTY_COLOR)).toHaveLength(4);
  });

  it("labels all challenge types", () => {
    expect(CHALLENGE_TYPE_LABEL.fix_the_bug).toBe("Fix the Bug");
    expect(CHALLENGE_TYPE_LABEL.predict_the_output).toBe("Predict the Output");
    expect(Object.keys(CHALLENGE_TYPE_LABEL)).toHaveLength(4);
  });

  it("identifies code challenges", () => {
    expect(isCodeChallenge("fix_the_bug")).toBe(true);
    expect(isCodeChallenge("complete_the_code")).toBe(true);
    expect(isCodeChallenge("small_build_task")).toBe(true);
    expect(isCodeChallenge("predict_the_output")).toBe(false);
  });
});
