/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        parchment: '#faf8f5',
        softPaper: '#fdfbfa',
        'warm-mist': '#d1d1cd',
        ash: '#92918b',
        graphite: '#72706b',
        ink: '#27251e',
        pureBlack: '#000000',
        'brand-accent': '#3B4FC4',
      }
    },
  },
  plugins: [],
}
