import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: '#eef2f8',
        surface: '#ffffff',
        primary: {
          DEFAULT: '#5b6dff',
          dark: '#4a5ae0',
        },
        secondary: '#00b7a8',
        accent: '#ff8a5c',
        ethics: '#f6c343',
        text: '#1d2437',
        muted: '#717a95',
        border: '#dbe3f4',
      },
      fontFamily: {
        sans: ['Pretendard', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
export default config
