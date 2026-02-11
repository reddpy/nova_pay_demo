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
        sidebar: {
          DEFAULT: "#1a1a2e",
          hover: "#25254a",
          active: "#2d2d5e",
        },
        nova: {
          50: "#eef7ff",
          100: "#d9edff",
          200: "#bce0ff",
          300: "#8ecdff",
          400: "#59b0ff",
          500: "#3b8dff",
          600: "#1e6cf5",
          700: "#1758e1",
          800: "#1947b6",
          900: "#1a3f8f",
          950: "#152857",
        },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;
