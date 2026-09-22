/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        jurisly: {
          black: "#050505",
          ink: "#080808",
          surface: "#0D0D0F",
          panel: "#121214",
          gold: {
            50: "#F0D292",
            100: "#E5BF70",
            200: "#D6AA55",
            300: "#C99A3D",
            400: "#B9832F",
            500: "#B98227",
          },
          muted: "#A7A7A7",
          dim: "#737373",
        },
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', "Georgia", "serif"],
        sans: ['"DM Sans"', "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 24px 80px rgba(0,0,0,0.55), 0 0 0 1px rgba(214,170,85,0.18)",
        gold: "0 8px 30px rgba(185,130,39,0.35)",
      },
      backgroundImage: {
        "gold-button":
          "linear-gradient(135deg, #B98227 0%, #E8C06A 50%, #B98227 100%)",
        "login-glow":
          "radial-gradient(ellipse at 20% 30%, rgba(185,130,39,0.18), transparent 55%), radial-gradient(ellipse at 80% 20%, rgba(214,170,85,0.08), transparent 45%)",
      },
    },
  },
  plugins: [],
};
