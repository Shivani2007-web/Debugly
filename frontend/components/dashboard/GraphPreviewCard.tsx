"use client";

// Compact navigation card for the knowledge graph. The full interactive graph
// lives on its own route; this just invites the student there. Shows a real
// count of graph nodes when available (not fabricated).

import Link from "next/link";

interface Props {
  href: string;
  nodeCount: number;
  isEmpty: boolean;
}

export function GraphPreviewCard({ href, nodeCount, isEmpty }: Props) {
  return (
    <section className="rounded-xl border border-white/10 bg-panelAlt/40 p-5">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        Knowledge Graph
      </h2>
      <p className="mt-3 text-sm leading-relaxed text-slate-300">
        See how Debugly connects your mistakes, concepts, interventions and
        progress.
      </p>
      {!isEmpty && (
        <p className="mt-1 text-xs text-slate-500">
          {nodeCount} connected node{nodeCount !== 1 ? "s" : ""} in your journey so far.
        </p>
      )}

      {/* tiny decorative node motif (presentation only) */}
      <div className="mt-4 flex items-center gap-2" aria-hidden>
        {["#6ea8fe", "#c3a6ff", "#ff8787", "#63e6be", "#69db7c"].map((c, i) => (
          <div key={i} className="flex items-center">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: c }} />
            {i < 4 && <span className="h-px w-5 bg-white/10" />}
          </div>
        ))}
      </div>

      <Link
        href={href}
        className="mt-4 inline-block rounded-md bg-panel px-4 py-2 text-sm font-medium text-slate-200 ring-1 ring-white/10 transition hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
      >
        Explore Knowledge Graph →
      </Link>
    </section>
  );
}
