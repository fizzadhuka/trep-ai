/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Existing tokens — kept so components already using them keep working.
        "tmobile-magenta": "#E20074",
        "tmobile-black":   "#000000",
        "tmobile-berry":   "#861B54",
        "tmobile-gray":    "#6A6A6A",
        "tmobile-dark":    "#0A0A0A",

        // Design system tokens. Magenta is the one official Un-carrier value
        // (#E20074); hover and muted are derived from it rather than guessed
        // per component, so a button and a badge can't drift apart.
        magenta: {
          DEFAULT: '#E20074',
          hover:   '#C9006A',
          muted:   '#E2007420',
        },
        berry:      '#A0135D',
        watermelon: '#EE3E96',

        // Surface ramp. Four steps of near-black rather than one flat colour —
        // cards need to read as raised against the page without a light border.
        brand: {
          black:          '#000000',
          surface:        '#111111',
          card:           '#1A1A1A',
          border:         '#222222',
          'border-light': '#333333',
        },

        // `text-secondary` is brand Dark Gray, so muted UI copy stays on-brand
        // instead of drifting into arbitrary zinc values.
        text: {
          primary:   '#FFFFFF',
          secondary: '#6A6A6A',
          muted:     '#E8E8E8',
        },

        status: {
          success: '#22C55E',
          error:   '#EF4444',
          warning: '#F59E0B',
          info:    '#3B82F6',
        },
      },

      fontFamily: {
        // TeleNeo is the T-Mobile brand face; Inter is the fallback on
        // machines without it licensed and installed.
        sans: ['TeleNeo', 'Inter', 'system-ui', 'sans-serif'],
      },

      backgroundImage: {
        'magenta-gradient': 'linear-gradient(135deg, #E20074 0%, #A0135D 100%)',
        'dark-gradient':    'linear-gradient(180deg, #111111 0%, #000000 100%)',
      },

      animation: {
        'pulse-magenta': 'pulse-magenta 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in':       'fade-in 0.3s ease-out',
        'slide-up':      'slide-up 0.4s ease-out',
        'step-complete': 'step-complete 0.5s ease-out',
      },

      keyframes: {
        'pulse-magenta': {
          '0%, 100%': { opacity: 1 },
          '50%':      { opacity: 0.5 },
        },
        'fade-in': {
          '0%':   { opacity: 0 },
          '100%': { opacity: 1 },
        },
        'slide-up': {
          '0%':   { opacity: 0, transform: 'translateY(12px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
        // Used when an execution step flips to complete — the slight overshoot
        // is what makes the change register without needing a colour flash.
        'step-complete': {
          '0%':   { transform: 'scale(0.8)', opacity: 0 },
          '60%':  { transform: 'scale(1.1)' },
          '100%': { transform: 'scale(1)', opacity: 1 },
        },
      },
    },
  },
  plugins: [],
}
