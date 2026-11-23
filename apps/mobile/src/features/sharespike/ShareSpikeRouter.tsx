import { useRootNavigationState, useRouter } from 'expo-router';
import { useShareIntentContext } from 'expo-share-intent';
import { useEffect, useRef } from 'react';

import { isShareSpikeEnabled } from './gate';
import { recordReceipt } from './store';

// Mounted once in the root layout. In dev / spike builds an incoming share is timed, recorded
// (content-free) and the app is sent to /share-spike. In store builds it renders nothing and does
// nothing; the real ingest replaces this in a later sprint.
export function ShareSpikeRouter() {
  if (!isShareSpikeEnabled()) return null;
  return <ShareSpikeRouterInner />;
}

function ShareSpikeRouterInner() {
  const { hasShareIntent, shareIntent, resetShareIntent } = useShareIntentContext();
  const router = useRouter();
  const navReady = Boolean(useRootNavigationState()?.key);
  const wantsNav = useRef(false);

  useEffect(() => {
    if (!hasShareIntent) return;
    const receivedAtMs = performance.now();
    const files = (shareIntent.files ?? []).map((f) => ({ path: f.path, mimeType: f.mimeType }));
    recordReceipt(files, receivedAtMs);
    wantsNav.current = true;
    // Clear the native side too, so a later foreground does not re-deliver the same share.
    resetShareIntent(true);
    // resetShareIntent is recreated every render by the library; keying on the intent is enough.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasShareIntent, shareIntent]);

  useEffect(() => {
    if (!navReady || !wantsNav.current) return;
    wantsNav.current = false;
    router.navigate('/share-spike');
  });

  return null;
}
