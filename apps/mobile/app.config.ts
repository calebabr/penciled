import path from 'node:path';

import type { ExpoConfig } from 'expo/config';

import { identity } from './app.identity.ts';

// Recursive statics come from @expo-google-fonts/recursive (OFL-1.1). Resolve the package
// instead of hard-coding node_modules paths, because npm workspaces hoist it to the root.
const recursiveDir = path.dirname(require.resolve('@expo-google-fonts/recursive/package.json'));
const recursiveFont = (file: string) => path.join(recursiveDir, file);

// iOS share extension target (expo-share-intent). The bundle ID must be a child of the app's
// bundle ID; EAS creates it on the first iOS build together with the App Group.
const iosShareExtensionBundleId = `${identity.iosBundleId}.share-extension`;

// One session at a time owns this file (BUILD_HANDOFF §1.7 rule 10).
// Native/plugin changes here require a new EAS dev build; batch them.
const config: ExpoConfig = {
  name: identity.name,
  slug: identity.slug,
  scheme: identity.scheme,
  version: '0.1.0',
  orientation: 'portrait',
  icon: './assets/icon.png',
  userInterfaceStyle: 'automatic',
  // No `newArchEnabled` key: on SDK 58 / RN 0.88 the New Architecture is the only architecture
  // (the key was removed from ExpoConfig), so every native dep must run on it.
  ios: {
    bundleIdentifier: identity.iosBundleId,
    supportsTablet: false,
    // ITSAppUsesNonExemptEncryption = false: the app uses only standard HTTPS (exempt), so
    // TestFlight uploads do not stall on the export-compliance question.
    config: {
      usesNonExemptEncryption: false,
    },
    // The App Group entitlement (`group.app.penciled`) is written by the expo-share-intent
    // plugin below (`iosAppGroupIdentifier`) for both the app and the extension. Declaring it
    // here as well produced a duplicate entry in the entitlements array.
  },
  android: {
    package: identity.androidPackage,
    adaptiveIcon: {
      backgroundColor: '#E8EBEE',
      foregroundImage: './assets/android-icon-foreground.png',
      backgroundImage: './assets/android-icon-background.png',
      monochromeImage: './assets/android-icon-monochrome.png',
    },
    predictiveBackGestureEnabled: false,
    // Store builds must not request what the app never uses (apps/mobile/STATUS.md, SPR-03).
    // WRITE_EXTERNAL_STORAGE is merged in by expo-media-library and expo-file-system even
    // though we never save media. SYSTEM_ALERT_WINDOW is trimmed by
    // ./plugins/withReleasePermissionTrim.js instead, so the debug manifest keeps it.
    blockedPermissions: ['android.permission.WRITE_EXTERNAL_STORAGE'],
  },
  plugins: [
    'expo-router',
    'expo-dev-client',
    'expo-sqlite',
    'expo-secure-store',
    'expo-image',
    'expo-asset',
    [
      'expo-font',
      {
        fonts: [
          recursiveFont('500Medium/Recursive_500Medium.ttf'),
          recursiveFont('600SemiBold/Recursive_600SemiBold.ttf'),
        ],
      },
    ],
    [
      'expo-calendar',
      {
        calendarPermission: 'Penciled adds the events you confirm to your calendar.',
        remindersPermission: false,
      },
    ],
    [
      'expo-media-library',
      {
        photosPermission: 'Penciled reads new screenshots so it can suggest calendar events.',
        savePhotosPermission: false,
        isAccessMediaLocationEnabled: false,
        granularPermissions: ['photo'],
      },
    ],
    'expo-notifications',
    [
      'expo-share-intent',
      {
        // Images only, one at a time (F1: share = one screenshot; bulk goes through the
        // 20-image import). With MaxCount 1 the extension is hidden when 2+ items are selected.
        iosActivationRules: {
          NSExtensionActivationSupportsImageWithMaxCount: 1,
        },
        iosAppGroupIdentifier: identity.iosAppGroup,
        iosShareExtensionBundleIdentifier: iosShareExtensionBundleId,
        // Plugin default, set explicitly so it is easy to flip. First fallback if the source app
        // freezes after sharing in a release build (expo-share-intent #217 / #231): set false
        // (the extension then flashes a modal before opening the app). See STATUS.md, SPR-03.
        iosHideView: true,
        // ACTION_SEND image/* only; no SEND_MULTIPLE (androidMultiIntentFilters) to match iOS.
        androidIntentFilters: ['image/*'],
      },
    ],
    './plugins/withReleasePermissionTrim.js',
  ],
  experiments: {
    typedRoutes: true,
  },
  owner: 'cjabrantes',
  extra: {
    appGroup: identity.iosAppGroup,
    // EAS project created by `eas init` on 2026-11-23 (owner cjabrantes). Not a secret.
    eas: {
      projectId: '371f39ba-68b3-477e-a8b6-d0f509be3066',
    },
  },
};

export default config;
