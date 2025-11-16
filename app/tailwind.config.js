/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'lightning-yellow': '#FFEB3B',
        'lightning-yellow-dark': '#FFC107',
        'cosmic-dark': '#0A0E27',
        'mid-navy': '#1A2332',
        'dark-navy': '#0F1419',
        'light-blue': '#4FC3F7',
        'light-blue-dark': '#0288D1',
        'glass-white': 'rgba(255, 255, 255, 0.05)',
        'glass-border': 'rgba(255, 255, 255, 0.1)',
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
