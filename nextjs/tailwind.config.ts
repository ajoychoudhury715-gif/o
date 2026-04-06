import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'medical-blue': {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#c9e2fd',
          300: '#a8d1fc',
          400: '#82b5f8',
          500: '#6a9df6',
          600: '#4a7ef5',
          700: '#2563eb',
          800: '#1e40af',
          900: '#1e3a8a',
        },
      },
      backdropFilter: {
        'blur-xl': 'blur(20px)',
      },
    },
  },
  plugins: [],
}
export default config
