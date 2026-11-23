import path from 'node:path';

import type { ExpoConfig } from 'expo/config';

import { identity } from './app.identity.ts';

// Recursive statics come from @expo-google-fonts/recursive (OFL-1.1). Resolve the package
// instead of hard-coding node_modules paths, because npm workspaces hoist it to the root.
const recursiveDir = path.dirname(require.resolve('@expo-google-fonts/recursive/package.json'));
const recursiveFont = (file: string) => path.join(recursiveDir, file);

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
    entitlements: {
      'com.apple.security.application-groups': [identity.iosAppGroup],
    },
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
        iosActivationRules: {
          NSExtensionActivationSupportsImageWithMaxCount: 1,
        },
        androidIntentFilters: ['image/*'],
        iosAppGroupIdentifier: identity.iosAppGroup,
      },
    ],
  ],
  experiments: {
    typedRoutes: true,
  },
  extra: {
    appGroup: identity.iosAppGroup,
  },
};

export default config;
