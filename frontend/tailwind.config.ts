// frontend/tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'brand-primary': '#3B82F6', // Màu xanh dương chính
        'brand-secondary': '#10B981', // Màu xanh lá cây cho các element khác
        'brand-light-blue': '#EFF6FF', // Màu nền nhạt cho các item được chọn
        'brand-background': '#F9FAFB', // Màu nền chung của khu vực chat
      },
      animation: {
        'pulse-fast': 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'), // Plugin để style form đẹp hơn
    require('@tailwindcss/typography'), // Plugin cho class 'prose' để style markdown
  ],
}
export default config