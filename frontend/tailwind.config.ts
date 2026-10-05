import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Developer-oriented dark palette (original, VS Code-inspired not copied).
        panel: "#1e1e26",
        panelAlt: "#252533",
        accent: "#6ea8fe",
        accentMuted: "#3b5bdb",
      },
    },
  },
  plugins: [],
};

export default config;
