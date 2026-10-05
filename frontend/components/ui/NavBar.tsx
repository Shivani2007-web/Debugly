"use client";

// Consistent product navigation shared across pages. Compact, matching the IDE
// navbar identity. There is no auth/role system, so the Teacher link is kept
// visually secondary (muted + divider) rather than presented as a primary
// student destination.

import Link from "next/link";

type NavKey = "ide" | "dashboard" | "challenges" | "graph" | "teacher";

interface NavBarProps {
  // Optional user id so learner-scoped links target the active student.
  userId?: string;
  active?: NavKey;
}

export function NavBar({ userId = "demo-ava", active }: NavBarProps) {
  const item = (href: string, label: string, key: NavKey, secondary = false) => (
    <Link
      href={href}
      aria-current={active === key ? "page" : undefined}
      className={`rounded-md px-3 py-1.5 text-sm transition focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/60 ${
        active === key
          ? "bg-white/10 text-slate-100"
          : secondary
            ? "text-slate-500 hover:text-slate-300"
            : "text-slate-400 hover:text-slate-200"
      }`}
    >
      {label}
    </Link>
  );

  return (
    <nav className="flex items-center gap-1 border-b border-white/10 bg-panelAlt/40 px-4 py-2">
      <Link
        href="/"
        className="mr-3 flex items-center gap-2 rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
        aria-label="Debugly home"
      >
        <span className="grid h-6 w-6 place-items-center rounded-md bg-accentMuted text-xs font-bold text-white">
          D
        </span>
        <span className="text-base font-semibold text-slate-100">Debugly</span>
      </Link>

      {item("/ide/sum-list", "IDE", "ide")}
      {item(`/dashboard/${userId}`, "Dashboard", "dashboard")}
      {item(`/dashboard/${userId}#continue-learning`, "Challenges", "challenges")}
      {item(`/dashboard/${userId}/knowledge-graph`, "Knowledge Graph", "graph")}

      <span className="mx-1 h-4 w-px bg-white/10" aria-hidden />
      {item("/teacher", "Teacher", "teacher", true)}
    </nav>
  );
}
