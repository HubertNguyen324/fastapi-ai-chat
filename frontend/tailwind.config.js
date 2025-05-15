module.exports = {
  // Enable dark mode using a class strategy
  darkMode: "class", // or 'media' if you prefer OS-level preference
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}", // Adjust if your Vue components are elsewhere
    "./components/**/*.{vue,js,ts,jsx,tsx}", // Path to your Vue components
  ],
  theme: {
    extend: {
      // Extend colors for your specific UI theme
      colors: {
        primary: {
          light: "#6D28D9", // Example primary color (purple)
          DEFAULT: "#5B21B6",
          dark: "#4C1D95",
        },
        secondary: {
          light: "#EC4899", // Example secondary color (pink)
          DEFAULT: "#DB2777",
          dark: "#BE185D",
        },
        // Background colors for different elements
        "sidebar-bg-light": "#F3F4F6", // Light mode sidebar
        "sidebar-bg-dark": "#1F2937", // Dark mode sidebar
        "chat-bg-light": "#FFFFFF", // Light mode chat area
        "chat-bg-dark": "#111827", // Dark mode chat area
        "input-bg-light": "#F9FAFB", // Light mode input area
        "input-bg-dark": "#374151", // Dark mode input area
        "message-user-bg-light": "#E0E7FF", // User message bubble light
        "message-user-bg-dark": "#312E81", // User message bubble dark
        "message-ai-bg-light": "#F3F4F6", // AI message bubble light
        "message-ai-bg-dark": "#4B5563", // AI message bubble dark
      },
      // Extend spacing, typography, or other theme aspects as needed
      spacing: {
        72: "18rem",
        80: "20rem",
        96: "24rem",
      },
      borderRadius: {
        xl: "1rem", // Larger rounded corners
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"], // Setting Inter as the default sans-serif font
      },
    },
  },
  plugins: [
    // Add any Tailwind CSS plugins here
    // require('@tailwindcss/forms'), // Example: for better default form styling
  ],
};
