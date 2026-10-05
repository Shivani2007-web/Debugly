"use client";

// The Debugly robot companion. A compact SVG whose face, color and motion
// change with its state. Framer Motion drives the transitions and per-state
// idle/active animations. This is the visual representation of the tutoring
// interaction, not decoration.

import { motion, AnimatePresence, type TargetAndTransition } from "framer-motion";
import type { RobotState } from "@/types/tutor";

interface RobotCompanionProps {
  state: RobotState;
  message?: string | null;
}

// Per-state accent color and a short caption.
const STATE_STYLE: Record<RobotState, { color: string; glow: string; caption: string }> = {
  idle: { color: "#6ea8fe", glow: "rgba(110,168,254,0.3)", caption: "Ready when you are." },
  thinking: { color: "#c3a6ff", glow: "rgba(195,166,255,0.4)", caption: "Thinking…" },
  concerned: { color: "#ffd43b", glow: "rgba(255,212,59,0.35)", caption: "Hmm, let's look closer." },
  encouraging: { color: "#63e6be", glow: "rgba(99,230,190,0.4)", caption: "You're close — keep going!" },
  happy: { color: "#69db7c", glow: "rgba(105,219,124,0.45)", caption: "Nice!" },
  celebrating: { color: "#ffa94d", glow: "rgba(255,169,77,0.5)", caption: "LET'S GOOO! 🎉" },
  sad: { color: "#ff8787", glow: "rgba(255,135,135,0.4)", caption: "Something went wrong." },
};

// Body animation per state.
const bodyAnim: Record<RobotState, TargetAndTransition> = {
  idle: { y: [0, -3, 0], transition: { duration: 3, repeat: Infinity, ease: "easeInOut" } },
  thinking: { rotate: [-2, 2, -2], transition: { duration: 1.4, repeat: Infinity, ease: "easeInOut" } },
  concerned: { x: [0, -2, 2, 0], transition: { duration: 0.8, repeat: Infinity } },
  encouraging: { y: [0, -5, 0], transition: { duration: 0.9, repeat: Infinity, ease: "easeInOut" } },
  happy: { scale: [1, 1.06, 1], transition: { duration: 0.7, repeat: Infinity, ease: "easeInOut" } },
  celebrating: {
    rotate: [-6, 6, -6],
    y: [0, -8, 0],
    transition: { duration: 0.5, repeat: Infinity, ease: "easeInOut" },
  },
  sad: { y: [0, 2, 0], transition: { duration: 2.5, repeat: Infinity, ease: "easeInOut" } },
};

function Eyes({ state }: { state: RobotState }) {
  // Different eye shapes convey emotion.
  if (state === "happy" || state === "celebrating") {
    return (
      <>
        <path d="M20 30 q5 -6 10 0" stroke="#0b0b12" strokeWidth="3" fill="none" strokeLinecap="round" />
        <path d="M50 30 q5 -6 10 0" stroke="#0b0b12" strokeWidth="3" fill="none" strokeLinecap="round" />
      </>
    );
  }
  if (state === "sad" || state === "concerned") {
    return (
      <>
        <circle cx="25" cy="32" r="4" fill="#0b0b12" />
        <circle cx="55" cy="32" r="4" fill="#0b0b12" />
        <path d="M20 24 l10 3 M60 24 l-10 3" stroke="#0b0b12" strokeWidth="2.5" strokeLinecap="round" />
      </>
    );
  }
  // idle / thinking / encouraging — round attentive eyes.
  return (
    <>
      <circle cx="25" cy="30" r="5" fill="#0b0b12" />
      <circle cx="55" cy="30" r="5" fill="#0b0b12" />
    </>
  );
}

function Mouth({ state }: { state: RobotState }) {
  if (state === "celebrating" || state === "happy") {
    return <path d="M28 46 q12 12 24 0" stroke="#0b0b12" strokeWidth="3" fill="none" strokeLinecap="round" />;
  }
  if (state === "sad") {
    return <path d="M28 50 q12 -10 24 0" stroke="#0b0b12" strokeWidth="3" fill="none" strokeLinecap="round" />;
  }
  if (state === "concerned") {
    return <line x1="30" y1="48" x2="50" y2="48" stroke="#0b0b12" strokeWidth="3" strokeLinecap="round" />;
  }
  if (state === "encouraging") {
    return <path d="M30 46 q10 6 20 0" stroke="#0b0b12" strokeWidth="3" fill="none" strokeLinecap="round" />;
  }
  // idle / thinking
  return <path d="M32 47 q8 4 16 0" stroke="#0b0b12" strokeWidth="2.5" fill="none" strokeLinecap="round" />;
}

export function RobotCompanion({ state, message }: RobotCompanionProps) {
  const style = STATE_STYLE[state];

  return (
    <div className="flex flex-col items-center gap-3">
      <AnimatePresence mode="wait">
        <motion.div
          key={state}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          transition={{ duration: 0.25 }}
          className="relative"
          style={{ filter: `drop-shadow(0 0 16px ${style.glow})` }}
        >
          <motion.svg
            width="104"
            height="104"
            viewBox="0 0 80 80"
            animate={bodyAnim[state]}
            aria-label={`Robot is ${state}`}
            role="img"
          >
            {/* Antenna */}
            <line x1="40" y1="6" x2="40" y2="14" stroke={style.color} strokeWidth="3" strokeLinecap="round" />
            <motion.circle
              cx="40"
              cy="5"
              r="3"
              fill={style.color}
              animate={{ opacity: state === "thinking" ? [0.3, 1, 0.3] : 1 }}
              transition={{ duration: 1, repeat: state === "thinking" ? Infinity : 0 }}
            />
            {/* Head */}
            <rect x="10" y="14" width="60" height="52" rx="14" fill={style.color} />
            <rect x="16" y="20" width="48" height="40" rx="10" fill="#f4f6ff" />
            <Eyes state={state} />
            <Mouth state={state} />
            {/* Ears */}
            <rect x="4" y="30" width="6" height="16" rx="3" fill={style.color} />
            <rect x="70" y="30" width="6" height="16" rx="3" fill={style.color} />
          </motion.svg>
        </motion.div>
      </AnimatePresence>

      <AnimatePresence mode="wait">
        <motion.p
          key={message || style.caption}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.2 }}
          className="max-w-[14rem] text-center text-sm text-slate-300"
        >
          {message || style.caption}
        </motion.p>
      </AnimatePresence>
    </div>
  );
}
