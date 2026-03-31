/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
      animation: { shimmer: 'shimmer 1.5s ease-in-out infinite' },
      keyframes: {
        shimmer: { '0%,100%': { opacity: 0.5 }, '50%': { opacity: 1 } },
      },
    },
  },
  plugins: [],
};
