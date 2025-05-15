/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class", // Enable class-based dark mode
  content: ["./templates/**/*.html", "./static/js/**/*.js"],
  theme: {
    extend: {
      // Add custom colors or extensions if needed
      colors: {
        // Example: Define some grays for better control
        gray: {
          50: "#FAFAFA",
          100: "#F5F5F5",
          200: "#EEEEEE",
          300: "#E0E0E0",
          400: "#BDBDBD",
          500: "#9E9E9E",
          600: "#757575",
          700: "#616161",
          800: "#424242", // Darker gray for panel backgrounds in dark mode
          850: "#303030", // Even darker for main area background in dark mode
          900: "#212121", // Darkest gray
        },
      },
    },
  },
  plugins: [],
};
