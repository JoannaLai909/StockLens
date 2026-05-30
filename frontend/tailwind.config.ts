import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#eff6ff",
          100: "#dbeafe",
          500: "#0f6fe8",
          600: "#0960cf",
          700: "#0757bd",
        },
        success: "#149b55",
        danger:  "#ef4444",
        warning: "#f59e0b",
        surface: "#f0f4f9",
      },
      fontFamily: {
        sans: ["Inter", "Noto Sans TC", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
