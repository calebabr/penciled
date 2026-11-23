import { Redirect, Stack } from 'expo-router';

import { isShareSpikeEnabled } from '../src/features/sharespike/gate';
import { ShareSpikeScreen } from '../src/features/sharespike/ShareSpikeScreen';

// SP-3 share-extension spike screen: dev / spike builds only. Store builds redirect home.
export default function ShareSpikeRoute() {
  if (!isShareSpikeEnabled()) return <Redirect href="/" />;
  return (
    <>
      <Stack.Screen options={{ title: 'SP-3 share spike' }} />
      <ShareSpikeScreen />
    </>
  );
}
