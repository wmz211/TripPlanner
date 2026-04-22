/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Cormorant Garant"', '"Noto Sans SC"', 'serif'],
        sans: ['"DM Sans"', '"Noto Sans SC"', 'sans-serif'],
      },
      colors: {
        sand: { DEFAULT: '#faf7f2', dark: '#f0e9df' },
        terracotta: { DEFAULT: '#c2624a', light: '#e8836b' },
        gold: { DEFAULT: '#b5882a', light: '#d4a84b' },
        teal: { DEFAULT: '#2d6a6a', light: '#3d8c8c' },
        ink: { DEFAULT: '#1c1917', muted: '#78716c' },
      },
      borderRadius: { '2xl': '1.25rem', '3xl': '1.75rem' },
    },
  },
  plugins: [],
}
