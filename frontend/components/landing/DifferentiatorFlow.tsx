// The core differentiator: a learner's mistakes become their learning path.
// Presentation-only vertical flow using the product identity.

const STEPS = [
  { label: "Repeated mistake", tone: "attention" },
  { label: "Misconception detected", tone: "neutral" },
  { label: "Socratic intervention", tone: "accent" },
  { label: "Personalized challenge", tone: "accent" },
  { label: "Independent success", tone: "success" },
  { label: "Mastery improves", tone: "success" },
] as const;

const TONE: Record<string, string> = {
  attention: "border-rose-500/30 bg-rose-500/10 text-rose-200",
  neutral: "border-white/10 bg-panelAlt/60 text-slate-200",
  accent: "border-accent/30 bg-accentMuted/15 text-accent",
  success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-200",
};

export function DifferentiatorFlow() {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center">
      {STEPS.map((s, i) => (
        <div key={s.label} className="flex w-full flex-col items-center">
          <div
            className={`w-full rounded-lg border px-4 py-3 text-center text-sm font-medium ${TONE[s.tone]}`}
          >
            {s.label}
          </div>
          {i < STEPS.length - 1 && (
            <span className="my-1 text-slate-600" aria-hidden>
              ↓
            </span>
          )}
        </div>
      ))}
    </div>
  );
}
