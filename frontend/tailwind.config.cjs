/** @type {import('tailwindcss').Config} */
const defaultTheme = require("tailwindcss/defaultTheme");
const forms = require("@tailwindcss/forms");
const typography = require("@tailwindcss/typography");

module.exports = {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#e6f3ff",
          100: "#cce7ff",
          200: "#99ceff",
          300: "#66b6ff",
          400: "#339dff",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          800: "#024a74",
          900: "#012c47",
        },
        surface: {
          50: "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
        },
        slate: {
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
        },
        success: {
          50: "#ecfdf3",
          500: "#10b981",
          600: "#059669",
          700: "#047857",
        },
        warning: {
          50: "#fffaeb",
          500: "#f59e0b",
          600: "#d97706",
          700: "#b45309",
        },
        error: {
          50: "#fef2f2",
          500: "#ef4444",
          600: "#dc2626",
          700: "#b91c1c",
        },
        border: "#e2e8f0",
        muted: "#6b7280",
      },
      fontFamily: {
        sans: ["Inter", ...defaultTheme.fontFamily.sans],
      },
      borderRadius: {
        xl: "1rem",
      },
      boxShadow: {
        card: "0 4px 24px rgba(15, 23, 42, 0.08)",
        hover: "0 16px 40px rgba(15, 23, 42, 0.12)",
      },
      spacing: {
        18: "4.5rem",
        22: "5.5rem",
      },
      maxWidth: {
        content: "1200px",
      },
      transitionTimingFunction: {
        "soft-out": "cubic-bezier(0.22, 1, 0.36, 1)",
      },
    },
  },
  plugins: [forms, typography],
};
