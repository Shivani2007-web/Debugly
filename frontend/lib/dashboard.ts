// Pure dashboard + graph presentation helpers (testable, no React).

import type { GraphNode, GraphNodeType, MasteryBand } from "@/types/dashboard";

export const BAND_LABEL: Record<MasteryBand, string> = {
  not_started: "Not started",
  emerging: "Emerging",
  developing: "Developing",
  proficient: "Proficient",
  strong: "Strong",
};

export const BAND_COLOR: Record<MasteryBand, string> = {
  not_started: "text-slate-400",
  emerging: "text-rose-300",
  developing: "text-amber-300",
  proficient: "text-sky-300",
  strong: "text-emerald-300",
};

export const BAND_RING: Record<MasteryBand, string> = {
  not_started: "#64748b",
  emerging: "#fb7185",
  developing: "#fbbf24",
  proficient: "#38bdf8",
  strong: "#34d399",
};

// Node styling by type for the knowledge graph.
export const NODE_TYPE_COLOR: Record<GraphNodeType, string> = {
  student: "#6ea8fe",
  concept: "#c3a6ff",
  misconception: "#ff8787",
  evidence: "#ffd43b",
  intervention: "#63e6be",
  challenge: "#74c0fc",
  outcome: "#69db7c",
};

// Vertical layer index for the layered DAG layout (top -> bottom).
export const NODE_TYPE_LAYER: Record<GraphNodeType, number> = {
  student: 0,
  concept: 1,
  misconception: 2,
  evidence: 3,
  intervention: 4,
  challenge: 5,
  outcome: 6,
};

export interface LaidOutNode extends GraphNode {
  x: number;
  y: number;
}

/**
 * Deterministic layered layout: group nodes by type-layer and spread each
 * layer horizontally. Returns positioned nodes plus the canvas size.
 */
export function layoutGraph(
  nodes: GraphNode[],
  opts: { width?: number; layerHeight?: number } = {},
): { nodes: LaidOutNode[]; width: number; height: number } {
  const width = opts.width ?? 760;
  const layerHeight = opts.layerHeight ?? 110;

  const byLayer = new Map<number, GraphNode[]>();
  for (const n of nodes) {
    const layer = NODE_TYPE_LAYER[n.type];
    const arr = byLayer.get(layer) ?? [];
    arr.push(n);
    byLayer.set(layer, arr);
  }

  const laid: LaidOutNode[] = [];
  let maxLayer = 0;
  for (const [layer, layerNodes] of byLayer) {
    maxLayer = Math.max(maxLayer, layer);
    const gap = width / (layerNodes.length + 1);
    layerNodes.forEach((n, i) => {
      laid.push({ ...n, x: gap * (i + 1), y: layer * layerHeight + 50 });
    });
  }

  return { nodes: laid, width, height: (maxLayer + 1) * layerHeight + 60 };
}

export function isBottleneckNode(node: GraphNode): boolean {
  // A node is a visual bottleneck when explicitly unhealthy.
  return node.healthy === false;
}

export function formatConceptName(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Derive a friendly display name from a user id. This is pure string
 * formatting of an identifier the backend already provides — NOT fabricated
 * profile data. e.g. "demo-ava" -> "Ava", "student_7" -> "Student 7".
 * Falls back to "there" so greetings read naturally for unknown ids.
 */
export function displayNameFromUserId(userId: string | null | undefined): string {
  if (!userId) return "there";
  const raw = userId.replace(/^demo-/i, "").trim();
  if (!raw) return "there";
  const first = raw.split(/[-_\s]+/)[0];
  if (!first) return "there";
  return first.charAt(0).toUpperCase() + first.slice(1);
}

export function greetingPrefix(date = new Date()): string {
  const h = date.getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

/**
 * Summary metrics for the dashboard, derived ONLY from fields the backend
 * already returns on DashboardResponse. No timeframe is invented (there is no
 * weekly window in the data), so these are lifetime totals from the profile.
 */
export interface SummaryMetrics {
  problemsSolved: number;      // sum of successful_attempts across concepts
  conceptsPracticed: number;   // concepts with at least one attempt
  independentSuccess: number;  // concepts solved without hint reliance (hint_dependency === 0)
  usesHints: boolean;          // whether any concept shows hint reliance
}

export function deriveSummaryMetrics(
  concepts: {
    successful_attempts: number;
    attempts: number;
    hint_dependency: number;
  }[],
): SummaryMetrics {
  const practiced = concepts.filter((c) => c.attempts > 0);
  return {
    problemsSolved: practiced.reduce((sum, c) => sum + c.successful_attempts, 0),
    conceptsPracticed: practiced.length,
    independentSuccess: practiced.filter(
      (c) => c.hint_dependency === 0 && c.successful_attempts > 0,
    ).length,
    usesHints: practiced.some((c) => c.hint_dependency > 0),
  };
}

/**
 * Derive a contextual robot message from REAL learner state only. Returns null
 * when there is nothing truthful to say (so the UI shows no message rather than
 * a fabricated one).
 */
export function deriveRobotMessage(args: {
  isNewLearner: boolean;
  recoveryTotal: number;      // sum of recovery_successes across bottlenecks
  persistentCount: number;    // number of persistent gaps
  overallMastery: number;
}): string | null {
  if (args.isNewLearner) {
    return "Welcome! Start a task and I'll help you learn from your mistakes.";
  }
  if (args.recoveryTotal > 0) {
    return "You're improving — you've solved problems without hints since your last correction.";
  }
  if (args.persistentCount > 0) {
    return "Let's keep working on your focus areas. Small steps add up.";
  }
  if (args.overallMastery >= 60) {
    return "Strong progress across your concepts. Keep it going!";
  }
  return null;
}
