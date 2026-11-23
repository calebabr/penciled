// src/theme.ts: the only source of design tokens (UI.md §2, §7.2).
// This is the ONLY file where raw colour literals and raw numeric style values are allowed.
// Components in src/ui and src/features import from here; ESLint (penciled/no-raw-style-values)
// fails the build otherwise. SPR-01 stub: the full type scale, contrast pairs and Increase
// Contrast overrides land with the theme sprint.
import { useColorScheme } from 'react-native';

export const palette = {
  light: {
    desk: '#E8EBEE',
    sheet: '#FFFFFF',
    sheetRaised: '#FFFFFF',
    sunken: '#DDE1E6',
    graphite: '#2A2E35',
    graphiteSoft: '#5A616B',
    hairline: '#CDD3D9',
    ink: '#22398F',
    onInk: '#FFFFFF',
    inkFlood: 'rgba(34,57,143,0.14)',
    highlighter: '#FFE36E',
    onHighlighter: '#2A2E35',
    correction: '#B3261E',
    toastBg: '#2A2E35',
    toastText: '#FFFFFF',
  },
  dark: {
    desk: '#14171B',
    sheet: '#1D2126',
    sheetRaised: '#262B31',
    sunken: '#101316',
    graphite: '#E4E7EB',
    graphiteSoft: '#A3AAB4',
    hairline: '#343A42',
    ink: '#9EB3FF',
    onInk: '#14171B',
    inkFlood: 'rgba(158,179,255,0.18)',
    highlighter: '#5A4A0C',
    onHighlighter: '#FFE36E',
    correction: '#F2B8B5',
    toastBg: '#E4E7EB',
    toastText: '#14171B',
  },
} as const;

export type ColorName = keyof typeof palette.light;
export type Colors = { readonly [K in ColorName]: string };

export const space = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32, 10: 40 } as const;
export const radius = { sheet: 28, card: 16, button: 12, field: 10, thumb: 6, mark: 3, chip: 999 } as const;
export const border = { width: 1.5, widthHC: 2 } as const;
export const hit = { min: 44 } as const;

// Font family names as registered by expo-font (config plugin embeds the files; useFonts
// loads the same files at runtime in dev). Casual statics are NOT in @expo-google-fonts/recursive
// (Google Fonts serves the default Linear instance only); see docs/spikes/SP-13.md.
export const fontFamily = {
  linear500: 'Recursive_500Medium',
  linear600: 'Recursive_600SemiBold',
  system: undefined,
} as const;

export const type = {
  cardTitle: { fontFamily: fontFamily.linear600, fontSize: 20, lineHeight: 26 },
  dateLine: { fontFamily: fontFamily.linear600, fontSize: 22, lineHeight: 28, fontVariant: ['tabular-nums'] },
  fieldValue: { fontFamily: fontFamily.linear500, fontSize: 17, lineHeight: 22, fontVariant: ['tabular-nums'] },
  headline: { fontSize: 17, lineHeight: 22, fontWeight: '600' },
  body: { fontSize: 17, lineHeight: 22, fontWeight: '400' },
  footnote: { fontSize: 13, lineHeight: 18, fontWeight: '400' },
  caption: { fontSize: 12, lineHeight: 16, fontWeight: '500' },
} as const;

export const motion = {
  check: 120,
  flood: 260,
  dry: 300,
  fade: 150,
  spring: { damping: 18, stiffness: 220 },
} as const;

export function useColors(): Colors {
  return useColorScheme() === 'dark' ? palette.dark : palette.light;
}
