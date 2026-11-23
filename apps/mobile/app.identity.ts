// CONFIRMED by builder 2026-11-23; hard to change after SPR-03 creates store records.
// Single source for the app's store identifiers. app.config.ts reads these values.
export const identity = {
  name: 'Penciled',
  slug: 'penciled',
  scheme: 'penciled',
  iosBundleId: 'app.penciled',
  androidPackage: 'app.penciled',
  iosAppGroup: 'group.app.penciled',
} as const;
