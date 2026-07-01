/** @type {import('tailwindcss').Config} */
export default {
  // `darkMode: "class"` is wired up so a dark theme can be dropped in later by
  // toggling a `dark` class — but for now we ship light only.
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Brand accent — amber #f5b942
        brand: {
          DEFAULT: "#f5b942",
          50: "#fef8ec",
          100: "#fdedc9",
          200: "#fbdd8e",
          300: "#f8c95a",
          400: "#f5b942",
          500: "#e79f1f",
          600: "#cc7f16",
          700: "#a95f16",
          800: "#8a4b19",
          900: "#733e18",
        },
        // Neutral surface tokens (from CSS variables in index.css)
        background: "var(--background)",
        surface: "var(--surface)",
        foreground: "var(--foreground)",
        muted: "var(--muted)",
        border: "var(--border)",
      },
      borderRadius: {
        xl: "0.9rem",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
