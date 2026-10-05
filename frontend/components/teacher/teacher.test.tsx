// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import { TeacherView } from "./TeacherView";
import { LoadingState, ErrorState, EmptyState } from "@/components/ui/States";
import { api } from "@/lib/api/endpoints";
import type { TeacherOverview } from "@/types/teacher";

afterEach(cleanup);

const populated: TeacherOverview = {
  class_size: 5,
  average_mastery: 48,
  is_empty: false,
  common_misconceptions: [
    { misconception_key: "off_by_one", concept_key: "list_indexing", students_affected: 2, total_occurrences: 7, persistent_students: 2 },
  ],
  concept_weaknesses: [
    { concept_key: "list_indexing", average_mastery: 30, students_practicing: 2, students_with_gap: 2 },
  ],
  students_needing_attention: [
    { user_id: "demo-dia", overall_mastery: 20, persistent_gap_count: 1, reason: "low overall mastery, a persistent gap" },
  ],
};

describe("shared state primitives", () => {
  it("renders loading", () => {
    render(<LoadingState />);
    expect(screen.getByTestId("state-loading")).toBeInTheDocument();
  });
  it("renders error with retry", () => {
    const onRetry = vi.fn();
    render(<ErrorState message="boom" onRetry={onRetry} />);
    expect(screen.getByTestId("state-error")).toBeInTheDocument();
    screen.getByRole("button", { name: /retry/i }).click();
    expect(onRetry).toHaveBeenCalled();
  });
  it("renders empty", () => {
    render(<EmptyState title="nothing here" hint="do something" />);
    expect(screen.getByTestId("state-empty")).toBeInTheDocument();
    expect(screen.getByText("nothing here")).toBeInTheDocument();
  });
});

describe("TeacherView", () => {
  it("shows loading then class analytics", async () => {
    vi.spyOn(api, "teacherOverview").mockResolvedValue(populated);
    render(<TeacherView />);
    await waitFor(() => expect(screen.getByTestId("teacher")).toBeInTheDocument());
    expect(screen.getByText("Class Overview")).toBeInTheDocument();
    expect(screen.getByText(/off by one/i)).toBeInTheDocument();
    expect(screen.getByText("demo-dia")).toBeInTheDocument();
  });

  it("shows empty-class state", async () => {
    vi.spyOn(api, "teacherOverview").mockResolvedValue({
      class_size: 0, average_mastery: 0, is_empty: true,
      common_misconceptions: [], concept_weaknesses: [], students_needing_attention: [],
    });
    render(<TeacherView />);
    await waitFor(() => expect(screen.getByText(/no class activity yet/i)).toBeInTheDocument());
  });

  it("shows error state when the API fails", async () => {
    vi.spyOn(api, "teacherOverview").mockRejectedValue(new Error("down"));
    render(<TeacherView />);
    await waitFor(() => expect(screen.getByTestId("state-error")).toBeInTheDocument());
  });

  it("drills into a student on click", async () => {
    vi.spyOn(api, "teacherOverview").mockResolvedValue(populated);
    vi.spyOn(api, "teacherStudentDetail").mockResolvedValue({
      user_id: "demo-dia", overall_mastery: 20, found: true,
      concepts: [], misconceptions: [{ misconception_key: "off_by_one", occurrences: 4, persistent: true }],
      recent_events: [{ event_type: "runtime_error" }],
    });
    render(<TeacherView />);
    await waitFor(() => expect(screen.getByText("demo-dia")).toBeInTheDocument());
    screen.getByText("demo-dia").click();
    await waitFor(() => expect(screen.getByTestId("student-drawer")).toBeInTheDocument());
  });
});
