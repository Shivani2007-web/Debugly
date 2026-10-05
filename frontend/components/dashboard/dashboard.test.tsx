// @vitest-environment jsdom
import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, cleanup, waitFor } from "@testing-library/react";
import { MasteryGauge } from "./MasteryGauge";
import { SummaryStrip } from "./SummaryStrip";
import { FocusAreas } from "./FocusAreas";
import { ContinueLearning } from "./ContinueLearning";
import { ActivityTimeline } from "./ActivityTimeline";
import { GraphPreviewCard } from "./GraphPreviewCard";
import { RobotNote } from "./RobotNote";
import { KnowledgeGraph } from "@/components/graph/KnowledgeGraph";
import { DashboardView } from "./DashboardView";
import type {
  Bottleneck,
  ConceptProgress,
  DashboardResponse,
  KnowledgeGraph as KG,
  RecommendedChallenge,
} from "@/types/dashboard";
import { api } from "@/lib/api/endpoints";

afterEach(cleanup);

const overall = {
  indicator: 42.5,
  band: "developing" as const,
  label: "Debugly Mastery Indicator",
  disclaimer: "An indicator, not a validated measure.",
  trend: [
    { concept_key: "list_indexing", mastery: 10, at: "2026-01-01T00:00:00Z" },
    { concept_key: "list_indexing", mastery: 42.5, at: "2026-01-02T00:00:00Z" },
  ],
};

const concepts: ConceptProgress[] = [
  {
    concept_key: "list_indexing", mastery: 30, band: "emerging",
    attempts: 4, successful_attempts: 2, has_persistent_gap: true,
    hint_dependency: 0.5, trend: [],
  },
  {
    concept_key: "loops", mastery: 70, band: "proficient",
    attempts: 3, successful_attempts: 3, has_persistent_gap: false,
    hint_dependency: 0, trend: [],
  },
];

const bottlenecks: Bottleneck[] = [
  {
    concept_key: "list_indexing", misconception_key: "off_by_one",
    occurrences: 3, persistent: true, hint_dependency: 0.5,
    recovery_successes: 2, concept_mastery: 30,
  },
];

const recommendation: RecommendedChallenge = {
  available: true, concept_key: "list_indexing", concept_name: "list_indexing",
  misconception_key: "off_by_one", misconception_name: "Off-by-one",
  difficulty: "beginner", task_type: "fix_the_bug",
  learning_objective: "Transfer the concept to a new problem.", reason: "persistent misconception",
};

describe("MasteryGauge", () => {
  it("renders the indicator value and subtle disclaimer", () => {
    render(<MasteryGauge overall={overall} />);
    expect(screen.getByText("Debugly Mastery")).toBeInTheDocument();
    expect(screen.getByText("43")).toBeInTheDocument(); // rounded
    expect(screen.getByText(/indicator, not a validated/i)).toBeInTheDocument();
  });
});

describe("SummaryStrip", () => {
  it("derives totals from real concept data", () => {
    render(<SummaryStrip concepts={concepts} />);
    // problems solved = 2 + 3 = 5
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("Problems solved")).toBeInTheDocument();
    expect(screen.getByText("Concepts practiced")).toBeInTheDocument();
  });
});

describe("FocusAreas", () => {
  it("renders focus areas with a persistent-gap tag and recovery note", () => {
    render(<FocusAreas bottlenecks={bottlenecks} />);
    expect(screen.getByText("List Indexing")).toBeInTheDocument();
    expect(screen.getByText(/persistent gap/i)).toBeInTheDocument();
    expect(screen.getByText(/recovering/i)).toBeInTheDocument();
  });
  it("shows a gentle empty state", () => {
    render(<FocusAreas bottlenecks={[]} />);
    expect(screen.getByText(/nothing to focus on/i)).toBeInTheDocument();
  });
});

describe("ContinueLearning", () => {
  it("renders the recommendation with CTA", () => {
    render(<ContinueLearning recommendation={recommendation} />);
    expect(screen.getByText("Continue Learning")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /start challenge/i })).toBeInTheDocument();
  });
  it("shows unavailable state", () => {
    render(
      <ContinueLearning
        recommendation={{
          available: false, concept_key: null, concept_name: null,
          misconception_key: null, misconception_name: null, difficulty: null,
          task_type: null, learning_objective: null, reason: null,
        }}
      />,
    );
    expect(screen.getByText(/Debugly will recommend/i)).toBeInTheDocument();
  });
});

describe("ActivityTimeline", () => {
  it("renders meaningful events", () => {
    render(
      <ActivityTimeline
        timeline={[
          { event_type: "misconception_detected", concept_key: "list_indexing",
            misconception_key: "off_by_one", error_type: null, hint_level: null,
            difficulty: null, label: "Misconception detected: off by one",
            at: new Date().toISOString() },
        ]}
      />,
    );
    expect(screen.getByText(/misconception detected: off by one/i)).toBeInTheDocument();
  });
});

describe("GraphPreviewCard", () => {
  it("renders a navigation card with node count", () => {
    render(<GraphPreviewCard href="/dashboard/u/knowledge-graph" nodeCount={7} isEmpty={false} />);
    expect(screen.getByText("Knowledge Graph")).toBeInTheDocument();
    expect(screen.getByText(/7 connected nodes/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /explore knowledge graph/i })).toBeInTheDocument();
  });
});

describe("RobotNote", () => {
  it("renders a message when present", () => {
    render(<RobotNote message="You're improving!" />);
    expect(screen.getByText("You're improving!")).toBeInTheDocument();
  });
  it("renders nothing when null", () => {
    const { container } = render(<RobotNote message={null} />);
    expect(container).toBeEmptyDOMElement();
  });
});

describe("KnowledgeGraph", () => {
  const graph: KG = {
    user_id: "u", is_empty: false,
    nodes: [
      { id: "student:u", type: "student", label: "You", healthy: null, meta: {} },
      { id: "concept:list_indexing", type: "concept", label: "List Indexing", healthy: false, meta: { mastery: 30 } },
      { id: "mis:x", type: "misconception", label: "Off-by-one", healthy: false, meta: { occurrences: 3 } },
    ],
    edges: [
      { source: "student:u", target: "concept:list_indexing", relation: "struggles_with" },
      { source: "concept:list_indexing", target: "mis:x", relation: "has_misconception" },
    ],
  };

  it("renders nodes", () => {
    render(<KnowledgeGraph graph={graph} />);
    expect(screen.getByTestId("graph-canvas")).toBeInTheDocument();
    expect(screen.getAllByTestId(/graph-node-/).length).toBeGreaterThanOrEqual(3);
  });
});

describe("DashboardView", () => {
  const dashboard: DashboardResponse = {
    user_id: "demo-ava", is_new_learner: false, overall,
    concepts, bottlenecks, timeline: [],
    recommended_challenge: recommendation,
  };
  const graph: KG = { user_id: "demo-ava", is_empty: false, nodes: [], edges: [] };

  it("shows loading then renders the greeting + sections with real data", async () => {
    vi.spyOn(api, "dashboard").mockResolvedValue(dashboard);
    vi.spyOn(api, "knowledgeGraph").mockResolvedValue(graph);
    render(<DashboardView userId="demo-ava" />);
    expect(screen.getByTestId("dashboard-loading")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId("dashboard")).toBeInTheDocument());
    // Personalised greeting derived from the user id.
    expect(screen.getByText(/, Ava/)).toBeInTheDocument();
    expect(screen.getByText("Continue Learning")).toBeInTheDocument();
    expect(screen.getByText("Focus Areas")).toBeInTheDocument();
  });

  it("shows an error state when the API fails", async () => {
    vi.spyOn(api, "dashboard").mockRejectedValue(new Error("down"));
    vi.spyOn(api, "knowledgeGraph").mockRejectedValue(new Error("down"));
    render(<DashboardView userId="demo-ava" />);
    await waitFor(() => expect(screen.getByTestId("dashboard-error")).toBeInTheDocument());
  });
});
