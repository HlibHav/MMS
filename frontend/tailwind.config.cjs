/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
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
          200: "#e5e7eb",
          500: "#6b7280",
          900: "#111827",
        },
      },
      boxShadow: {
        card: "0 1px 3px rgba(0,0,0,0.06)",
        hover: "0 10px 30px rgba(0,0,0,0.08)",
      },
    },
  },
  plugins: [],
};
