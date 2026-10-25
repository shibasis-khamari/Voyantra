/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ['Newsreader', 'Georgia', 'serif'],
        display: ['Newsreader', 'Georgia', 'serif'],
        sans: ['Plus Jakarta Sans', 'sans-serif'],
      },
      colors: {
        brand: {
          50: '#f4f6fa',
          100: '#e4e8f0',
          200: '#c5cee0',
          300: '#94a4c2',
          400: '#5c6e8e',
          500: '#35455e',
          600: '#28354a',
          700: '#1b2538', // Primary Deep Indigo Navy
          800: '#111c2e',
          900: '#051022',
        },
        terracotta: {
          DEFAULT: '#e05a38', // Warm Terracotta Sunset
          light: '#fd6f4b',
          dark: '#ab3516',
          subtle: '#ffdad2',
        },
        sandstone: {
          DEFAULT: '#e7dfd5', // Muted Sandstone
          light: '#efeeeb',
          canvas: '#faf8f5', // Soft Warm Linen
          recessed: '#f3efea',
        }
      }
    },
  },
  plugins: [],
}
