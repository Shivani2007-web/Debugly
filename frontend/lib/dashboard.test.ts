import { describe, it, expect } from "vitest";
import {
  BAND_LABEL,
  NODE_TYPE_LAYER,
  formatConceptName,
  isBottleneckNode,
  layoutGraph,
} from "./dashboard";
import type { GraphNode } from "@/types/dashboard";

function node(id: string, type: GraphNode["type"], healthy: boolean | null = null): GraphNode {
  return { id, type, label: id, healthy, meta: {} };
}

describe("dashboard helpers", () => {
  it("labels every mastery band", () => {
    expect(BAND_LABEL.strong).toBe("Strong");
    expect(Object.keys(BAND_LABEL)).toHaveLength(5);
  });

  it("formats concept names", () => {
    expect(formatConceptName("list_indexing")).toBe("List Indexing");
  });

  it("flags unhealthy nodes as bottlenecks", () => {
    expect(isBottleneckNode(node("a", "concept", false))).toBe(true);
    expect(isBottleneckNode(node("b", "concept", true))).toBe(false);
    expect(isBottleneckNode(node("c", "concept", null))).toBe(false);
  });
});

describe("layoutGraph", () => {
  it("positions nodes in layers top to bottom by type", () => {
    const { nodes, height } = layoutGraph([
      node("student:1", "student"),
      node("concept:x", "concept"),
      node("mis:x", "misconception"),
    ]);
    const student = nodes.find((n) => n.type === "student")!;
    const concept = nodes.find((n) => n.type === "concept")!;
    const mis = nodes.find((n) => n.type === "misconception")!;
    // student above concept above misconception.
    expect(student.y).toBeLessThan(concept.y);
    expect(concept.y).toBeLessThan(mis.y);
    expect(height).toBeGreaterThan(0);
  });

  it("spreads multiple nodes in the same layer horizontally", () => {
    const { nodes } = layoutGraph([
      node("concept:a", "concept"),
      node("concept:b", "concept"),
    ]);
    const xs = nodes.map((n) => n.x);
    expect(xs[0]).not.toBe(xs[1]);
  });

  it("has a layer for every node type", () => {
    const types: GraphNode["type"][] = [
      "student", "concept", "misconception", "evidence",
      "intervention", "challenge", "outcome",
    ];
    for (const t of types) expect(NODE_TYPE_LAYER[t]).toBeGreaterThanOrEqual(0);
  });
});
