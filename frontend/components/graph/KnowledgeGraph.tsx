"use client";

// Lightweight interactive knowledge graph. No heavy graph lib: a deterministic
// layered SVG layout (student at top -> outcome at bottom) with wheel-zoom,
// drag-pan, and click-to-select node details. Bottleneck nodes are visually
// distinguished from healthy ones.

import { useMemo, useRef, useState } from "react";
import type { KnowledgeGraph as KG, GraphNode } from "@/types/dashboard";
import { NODE_TYPE_COLOR, layoutGraph, type LaidOutNode } from "@/lib/dashboard";

export function KnowledgeGraph({ graph }: { graph: KG }) {
  const [selected, setSelected] = useState<GraphNode | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const dragRef = useRef<{ x: number; y: number } | null>(null);

  const { nodes, width, height, nodeById } = useMemo(() => {
    const laid = layoutGraph(graph.nodes);
    const map = new Map(laid.nodes.map((n) => [n.id, n]));
    return { ...laid, nodeById: map };
  }, [graph.nodes]);

  if (graph.is_empty) {
    return (
      <section className="rounded-xl bg-panelAlt/40 p-5 ring-1 ring-white/10">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Knowledge Graph
        </h2>
        <p className="mt-3 text-sm text-slate-500">
          Your learning graph will grow here as you practice, hit misconceptions,
          get hints, and solve challenges.
        </p>
      </section>
    );
  }

  const onWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    setZoom((z) => Math.max(0.4, Math.min(2.5, z - e.deltaY * 0.001)));
  };
  const onDown = (e: React.MouseEvent) => {
    dragRef.current = { x: e.clientX - pan.x, y: e.clientY - pan.y };
  };
  const onMove = (e: React.MouseEvent) => {
    if (!dragRef.current) return;
    setPan({ x: e.clientX - dragRef.current.x, y: e.clientY - dragRef.current.y });
  };
  const onUp = () => {
    dragRef.current = null;
  };

  return (
    <section className="rounded-xl bg-panelAlt/40 p-5 ring-1 ring-white/10">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Knowledge Graph
        </h2>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <button
            onClick={() => setZoom((z) => Math.min(2.5, z + 0.2))}
            className="rounded bg-white/5 px-2 py-1 hover:bg-white/10"
            aria-label="zoom in"
          >
            +
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(0.4, z - 0.2))}
            className="rounded bg-white/5 px-2 py-1 hover:bg-white/10"
            aria-label="zoom out"
          >
            −
          </button>
          <button
            onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}
            className="rounded bg-white/5 px-2 py-1 hover:bg-white/10"
          >
            reset
          </button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_220px]">
        <div
          className="relative h-[420px] overflow-hidden rounded-lg bg-panel/60 ring-1 ring-white/5"
          onWheel={onWheel}
          onMouseDown={onDown}
          onMouseMove={onMove}
          onMouseUp={onUp}
          onMouseLeave={onUp}
          style={{ cursor: dragRef.current ? "grabbing" : "grab" }}
          data-testid="graph-canvas"
        >
          <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
            <g transform={`translate(${pan.x} ${pan.y}) scale(${zoom})`}>
              {/* edges */}
              {graph.edges.map((e, i) => {
                const s = nodeById.get(e.source);
                const t = nodeById.get(e.target);
                if (!s || !t) return null;
                return (
                  <line
                    key={i}
                    x1={s.x}
                    y1={s.y}
                    x2={t.x}
                    y2={t.y}
                    stroke="#3a3a4a"
                    strokeWidth={1.5}
                  />
                );
              })}
              {/* nodes */}
              {nodes.map((n) => (
                <GraphNodeDot
                  key={n.id}
                  node={n}
                  selected={selected?.id === n.id}
                  onSelect={() => setSelected(n)}
                />
              ))}
            </g>
          </svg>
        </div>

        <NodeDetails node={selected} />
      </div>
    </section>
  );
}

function GraphNodeDot({
  node,
  selected,
  onSelect,
}: {
  node: LaidOutNode;
  selected: boolean;
  onSelect: () => void;
}) {
  const color = NODE_TYPE_COLOR[node.type];
  const isBottleneck = node.healthy === false;
  const r = node.type === "student" ? 16 : 11;
  return (
    <g
      transform={`translate(${node.x} ${node.y})`}
      onClick={(e) => { e.stopPropagation(); onSelect(); }}
      style={{ cursor: "pointer" }}
      data-testid={`graph-node-${node.type}`}
    >
      <circle
        r={r}
        fill={color}
        stroke={isBottleneck ? "#ff6b6b" : selected ? "#fff" : "transparent"}
        strokeWidth={isBottleneck ? 3 : selected ? 2 : 0}
      />
      {isBottleneck && <circle r={r + 5} fill="none" stroke="#ff6b6b" strokeWidth={1} opacity={0.4} />}
      <text
        x={0}
        y={r + 13}
        textAnchor="middle"
        className="fill-slate-300"
        style={{ fontSize: 10 }}
      >
        {node.label.length > 22 ? node.label.slice(0, 20) + "…" : node.label}
      </text>
    </g>
  );
}

function NodeDetails({ node }: { node: GraphNode | null }) {
  if (!node) {
    return (
      <div className="rounded-lg bg-panel/60 p-3 text-xs text-slate-500 ring-1 ring-white/5">
        Click a node to see details.
      </div>
    );
  }
  return (
    <div className="rounded-lg bg-panel/60 p-3 ring-1 ring-white/5" data-testid="node-details">
      <p className="text-[10px] uppercase tracking-wide text-slate-500">{node.type}</p>
      <p className="mt-1 text-sm font-semibold text-slate-100">{node.label}</p>
      {node.healthy === false && (
        <p className="mt-1 text-xs text-rose-300">⚠ bottleneck</p>
      )}
      {node.healthy === true && (
        <p className="mt-1 text-xs text-emerald-300">✓ healthy</p>
      )}
      {Object.keys(node.meta).length > 0 && (
        <dl className="mt-2 space-y-1 text-xs">
          {Object.entries(node.meta).map(([k, v]) => (
            <div key={k} className="flex justify-between gap-2">
              <dt className="text-slate-500">{k.replace(/_/g, " ")}</dt>
              <dd className="text-slate-300">{String(v)}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}
