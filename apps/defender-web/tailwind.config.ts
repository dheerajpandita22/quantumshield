import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        quantum: {
          50:  "#f0f4ff",
          100: "#e0eaff",
          200: "#c7d7fe",
          300: "#a5b8fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
          950: "#1e1b4b",
        },
        cyber: {
          bg:     "#0a0e1a",
          surface:"#0f1629",
          border: "#1e2d4a",
          text:   "#e2e8f0",
          muted:  "#64748b",
          accent: "#00d4ff",
          green:  "#10b981",
          yellow: "#f59e0b",
          red:    "#ef4444",
          purple: "#8b5cf6",
        },
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Fira Code", "Consolas", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        glow: {
          "0%": { boxShadow: "0 0 5px #6366f1, 0 0 10px #6366f1" },
          "100%": { boxShadow: "0 0 10px #6366f1, 0 0 30px #6366f1, 0 0 60px #6366f1" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
