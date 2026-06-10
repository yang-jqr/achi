import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0d1117",
        surface: "#161b22",
        border: "#30363d",
        muted: "#8b949e",
        accent: "#58a6ff",
        "accent-green": "#3fb950",
        "accent-orange": "#d2991d",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
export default config;