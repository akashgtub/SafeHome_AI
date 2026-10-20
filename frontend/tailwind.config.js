/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        safehome: {
          primary: "#168653",
          deep: "#116B43",
          bg: "#EFF7F1",
          card: "#FFFFFF",
          text: "#182820",
          muted: "#68766D",
          border: "#E0EAE2",
          amber: "#F2B544",
          amberLight: "#FEF8EC",
          red: "#D9383A",
          redLight: "#FDF2F2",
          pillBg: "#E4F3E8",
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(24, 40, 32, 0.05), 0 1px 2px -1px rgba(24, 40, 32, 0.05)",
        cardHover: "0 4px 6px -1px rgba(24, 40, 32, 0.08), 0 2px 4px -2px rgba(24, 40, 32, 0.05)",
      }
    },
  },
  plugins: [],
}
