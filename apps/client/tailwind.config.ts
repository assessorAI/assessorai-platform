import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1536px",
      },
    },
    extend: {
      fontSize: {
        "2.5xl": "2rem", // 2rem = 32px
      },
      spacing: {
        "spacing-0": "0rem",
        "spacing-xxs": "0.25rem",
        "spacing-xs": "0.5rem",
        "spacing-sm": "1rem",
        "spacing-md": "1.5rem",
        "spacing-lg": "2rem",
        "spacing-xl": "2.5rem",
        "spacing-2xl": "3rem",
        "spacing-3xl": "3.5rem",
        "spacing-4xl": "4rem",
        "spacing-5xl": "4.5rem",
        "spacing-6xl": "5rem",
      },
      screens: {
        "2xl": "1536px",
        "4xl": "2048px",
      },
      fontFamily: {
        sans: ["Noto Sans", "system-ui", "sans-serif"],
        title: ["Sora", "system-ui", "sans-serif"],
        sora: ["Sora", "system-ui", "sans-serif"],
        noto: ["Noto Sans", "system-ui", "sans-serif"],
      },
      colors: {
        "brand-primary": "hsl(var(--brand-primary))",
        "brand-accent": "hsl(var(--brand-accent))",
        "brand-accent-60": "hsl(var(--brand-accent-60))",
        "brand-accent-40": "hsl(var(--brand-accent-40))",
        "brand-accent-20": "hsl(var(--brand-accent-20))",
        "brand-secondary": "hsl(var(--brand-secondary))",
        "brand-secondary-120": "hsl(var(--brand-secondary-120))",
        "brand-secondary-60": "hsl(var(--brand-secondary-60))",
        "brand-secondary-40": "hsl(var(--brand-secondary-40))",
        "brand-secondary-20": "hsl(var(--brand-secondary-20))",
        "brand-gray-100": "hsl(var(--brand-gray-100))",
        "brand-gray-200": "hsl(var(--brand-gray-200))",
        "brand-gray-400": "hsl(var(--brand-gray-400))",
        "brand-gray-500": "hsl(var(--brand-gray-500))",
        "brand-alert": "hsl(var(--brand-alert))",
        "brand-notice": "hsl(var(--brand-notice))",
        "brand-success": "hsl(var(--brand-success))",
        "brand-placeholder": "hsl(var(--brand-placeholder))",
        "brand-border": "hsl(var(--brand-border))",
        "brand-text-bold": "hsl(var(--brand-primary-text-bold))",
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        chart: {
          "1": "hsl(var(--chart-1))",
          "2": "hsl(var(--chart-2))",
          "3": "hsl(var(--chart-3))",
          "4": "hsl(var(--chart-4))",
          "5": "hsl(var(--chart-5))",
        },
        sidebar: {
          DEFAULT: "hsl(var(--sidebar-background))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: {
            height: "0",
          },
          to: {
            height: "var(--radix-accordion-content-height)",
          },
        },
        "accordion-up": {
          from: {
            height: "var(--radix-accordion-content-height)",
          },
          to: {
            height: "0",
          },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
