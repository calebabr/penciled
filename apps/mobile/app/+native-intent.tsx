import { isShareSpikeEnabled } from '../src/features/sharespike/gate';

// iOS: the expo-share-intent extension opens the app with `penciled://dataUrl=<key>#<type>`.
// That is not a route, so without this rewrite Expo Router shows "Unmatched route". The share
// payload itself is read by expo-share-intent from the App Group, not from this path.
// Dev / spike builds go to the SP-3 spike screen; store builds go home (real ingest: later sprint).
export function redirectSystemPath({ path }: { path: string; initial: boolean }): string {
  try {
    if (path.includes('dataUrl=')) return isShareSpikeEnabled() ? '/share-spike' : '/';
    return path;
  } catch {
    return '/';
  }
}
