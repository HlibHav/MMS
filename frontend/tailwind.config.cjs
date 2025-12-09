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
          50: "#f0f9ff",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
        },
        success: {
          500: "#10b981",
          600: "#059669",
        },
        warning: {
          500: "#f59e0b",
          600: "#d97706",
        },
        error: {
          500: "#ef4444",
          600: "#dc2626",
        },
        gray: {
          50: "#f9fafb",
          100: "#f3f4f6",
          500: "#6b7280",
          900: "#111827",
        },
        surface: {
          50: "#f9fafb",
          100: "#f3f4f6",
          200: "#e5e7eb",
          300: "#d1d5db",
        },
        slate: {
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
        },
        border: "#e5e7eb",
        muted: "#6b7280",
      },
      fontFamily: {
        sans: ["Inter", ...defaultTheme.fontFamily.sans],
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.25rem",
      },
      boxShadow: {
        card: "0 8px 28px rgba(15, 23, 42, 0.08)",
        hover: "0 12px 32px rgba(15, 23, 42, 0.12)",
      },
      spacing: {
        18: "4.5rem",
        22: "5.5rem",
      },
      maxWidth: {
        content: "1200px",
        wide: "1400px",
      },
      transitionTimingFunction: {
        "soft-out": "cubic-bezier(0.22, 1, 0.36, 1)",
      },
    },
  },
  plugins: [forms, typography],
};
