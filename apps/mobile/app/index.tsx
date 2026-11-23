import { Stack, useRouter } from 'expo-router';

import { HomePlaceholder } from '../src/features/home/HomePlaceholder';
import { isShareSpikeEnabled } from '../src/features/sharespike/gate';

// SCR-HOME placeholder (SPR-01). The real feed lands in a later sprint.
export default function Index() {
  const router = useRouter();
  return (
    <>
      <Stack.Screen options={{ title: 'Screenshots' }} />
      <HomePlaceholder
        onOpenSp13={__DEV__ ? () => router.push('/sp13') : undefined}
        onOpenShareSpike={isShareSpikeEnabled() ? () => router.push('/share-spike') : undefined}
      />
    </>
  );
}
