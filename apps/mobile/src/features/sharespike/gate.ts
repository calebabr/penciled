// The SP-3 share spike runs in dev builds, or in a release build compiled with
// EXPO_PUBLIC_SHARE_SPIKE=1 (for timing without Metro, e.g. a TestFlight build made for the
// spike). Store builds without the flag never see it: /share-spike redirects home and incoming
// shares are left alone (the real ingest lands in a later sprint).
export function isShareSpikeEnabled(): boolean {
  return __DEV__ || process.env.EXPO_PUBLIC_SHARE_SPIKE === '1';
}
