/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'gov-brown': '#3D2817',
        'gov-gold': '#D2691E',
        'gov-orange': '#FF6B00',
        'gov-amber': '#FF9F43',
        'gov-cream': '#F4F4F6',
        'gov-warm': '#F0EFEA',
      },
      fontFamily: {
        'gov': ['"Microsoft YaHei"', 'sans-serif'],
      },
      boxShadow: {
        'gov-card': '0 2px 12px rgba(0, 0, 0, 0.05)',
        'gov-hover': '0 4px 16px rgba(0, 0, 0, 0.1)',
      }
    },
  },
  plugins: [],
}