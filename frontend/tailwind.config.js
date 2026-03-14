/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Dark tech magazine palette
        bg: {
          primary: '#0f172a',    // slate-900
          secondary: '#1e293b',  // slate-800
          tertiary: '#334155',   // slate-700
        },
        accent: {
          DEFAULT: '#14b8a6',    // teal-500
          light: '#2dd4bf',      // teal-400
          dark: '#0d9488',       // teal-600
        },
        text: {
          primary: '#f1f5f9',    // slate-100
          secondary: '#94a3b8',  // slate-400
          muted: '#64748b',      // slate-500
        },
        border: {
          DEFAULT: '#334155',    // slate-700
          light: '#475569',      // slate-600
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'ui-monospace', 'monospace'],
      },
      typography: (theme) => ({
        invert: {
          css: {
            '--tw-prose-body': theme('colors.slate[300]'),
            '--tw-prose-headings': theme('colors.slate[100]'),
            '--tw-prose-lead': theme('colors.slate[400]'),
            '--tw-prose-links': theme('colors.teal[400]'),
            '--tw-prose-bold': theme('colors.slate[100]'),
            '--tw-prose-counters': theme('colors.slate[400]'),
            '--tw-prose-bullets': theme('colors.teal[400]'),
            '--tw-prose-hr': theme('colors.slate[700]'),
            '--tw-prose-quotes': theme('colors.slate[100]'),
            '--tw-prose-quote-borders': theme('colors.teal[500]'),
            '--tw-prose-captions': theme('colors.slate[400]'),
            '--tw-prose-code': theme('colors.teal[300]'),
            '--tw-prose-pre-code': theme('colors.slate[200]'),
            '--tw-prose-pre-bg': theme('colors.slate[800]'),
            '--tw-prose-th-borders': theme('colors.slate[600]'),
            '--tw-prose-td-borders': theme('colors.slate[700]'),
          },
        },
      }),
    },
  },
  plugins: [],
}
