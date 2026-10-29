/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        serif: ['"Instrument Serif"', 'Georgia', 'serif'],
        display: ['"Instrument Serif"', 'Georgia', 'serif'],
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
      },
      colors: {
        brand: {
          50: '#f0fdfa',
          100: '#ccfbf1',
          200: '#99f6e4',
          300: '#5eead4',
          400: '#2dd4bf',
          500: '#14b8a6',
          600: '#0d946e', // Vibrant Ocean Teal from Logo
          700: '#005458', // Deep Oceanic Pine from Logo
          800: '#003e42', // Rich Pine Navy
          900: '#001838', // Midnight Marine Navy from Logo
          950: '#000b2c', // Deep Midnight from Logo
        },
        terracotta: {
          DEFAULT: '#ea580c', // Radiant Sunset Terracotta
          light: '#fd8922',   // Logo Warm Saffron Highlight
          dark: '#c2410c',
          subtle: '#ffedd5',
        },
        sandstone: {
          DEFAULT: '#e7dfd5', // Muted Coastal Sandstone
          light: '#f3f0ea',
          canvas: '#faf8f5',  // Soft Warm Linen
          recessed: '#efeae3',
        }
      }
    },
  },
  plugins: [],
}
