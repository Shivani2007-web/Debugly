import Link from "next/link";
import { NavBar } from "@/components/ui/NavBar";
import { ProductPreview } from "@/components/landing/ProductPreview";
import { DifferentiatorFlow } from "@/components/landing/DifferentiatorFlow";

const DEMO_USER = "demo-ava";

const STEPS = [
  { n: "01", title: "Code", body: "Write and debug normally." },
  {
    n: "02",
    title: "Understand",
    body: "Debugly analyzes your errors and debugging behavior to identify the underlying misconception.",
  },
  {
    n: "03",
    title: "Learn",
    body: "A Socratic AI tutor guides you toward the answer instead of simply giving it away.",
  },
  {
    n: "04",
    title: "Improve",
    body: "Your learner profile adapts future practice to the concepts you need most.",
  },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-panel text-slate-100">
      <NavBar />

      {/* HERO */}
      <section className="mx-auto max-w-5xl px-6 pb-10 pt-16 text-center">
        <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-panelAlt/50 px-3 py-1 text-xs text-slate-400">
          AI tutor for Python learners
        </span>
        <h1 className="mt-5 text-4xl font-bold tracking-tight text-slate-100 sm:text-5xl">
          Don&apos;t just fix the bug.{" "}
          <span className="bg-gradient-to-r from-accent to-indigo-400 bg-clip-text text-transparent">
            Understand it.
          </span>
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-300">
          An AI tutor that finds the misconception behind the mistake.
        </p>
        <p className="mx-auto mt-3 max-w-2xl text-sm leading-relaxed text-slate-500">
          Debugly analyzes how you code and debug, identifies the concepts behind
          repeated mistakes, and guides you toward understanding instead of
          simply giving you the answer.
        </p>

        <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/ide/sum-list"
            className="rounded-md bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
          >
            Start Learning →
          </Link>
          <Link
            href={`/dashboard/${DEMO_USER}`}
            className="rounded-md bg-panelAlt px-5 py-2.5 text-sm font-medium text-slate-200 ring-1 ring-white/10 transition hover:bg-white/10 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
          >
            Explore Dashboard
          </Link>
        </div>
      </section>

      {/* PRODUCT PREVIEW */}
      <section className="mx-auto max-w-5xl px-6 pb-20">
        <ProductPreview />
      </section>

      {/* HOW DEBUGLY WORKS */}
      <section className="border-y border-white/10 bg-panelAlt/20 py-16">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="text-center text-sm font-semibold uppercase tracking-widest text-slate-400">
            How Debugly works
          </h2>
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((s) => (
              <div key={s.n} className="rounded-lg border border-white/10 bg-panel/60 p-5">
                <span className="text-sm font-semibold text-accent">{s.n}</span>
                <h3 className="mt-2 text-base font-semibold text-slate-100">{s.title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-400">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CORE DIFFERENTIATOR */}
      <section className="py-20">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="text-center text-2xl font-bold tracking-tight text-slate-100 sm:text-3xl">
            Your mistakes become your{" "}
            <span className="bg-gradient-to-r from-accent to-indigo-400 bg-clip-text text-transparent">
              learning path.
            </span>
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-center text-sm text-slate-500">
            Debugly turns repeated errors into a guided path from confusion to mastery —
            not just a corrected line of code.
          </p>
          <div className="mt-10">
            <DifferentiatorFlow />
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="border-t border-white/10 bg-panelAlt/20 py-16">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="text-2xl font-bold tracking-tight text-slate-100 sm:text-3xl">
            Ready to understand your bugs?
          </h2>
          <div className="mt-6">
            <Link
              href="/ide/sum-list"
              className="inline-block rounded-md bg-emerald-600 px-6 py-3 text-sm font-semibold text-white transition hover:bg-emerald-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
            >
              Start Learning →
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-white/10 px-6 py-6 text-center text-xs text-slate-600">
        Debugly · an AI tutor that finds the misconception behind the mistake ·{" "}
        <Link href="/dev/health" className="hover:text-slate-400">
          system status
        </Link>
      </footer>
    </main>
  );
}
