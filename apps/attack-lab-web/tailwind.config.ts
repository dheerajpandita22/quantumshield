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
        lab: {
          bg:      "#0a0d12",
          surface: "#0e1218",
          border:  "#1a2030",
          text:    "#e2e8f0",
          muted:   "#64748b",
          accent:  "#f97316",
          green:   "#10b981",
          yellow:  "#f59e0b",
          red:     "#ef4444",
          orange:  "#f97316",
        },
      },
    },
  },
  plugins: [],
};
export default config;
