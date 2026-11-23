import { Stack } from 'expo-router';
import { ShareIntentProvider } from 'expo-share-intent';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

import { ShareSpikeRouter } from '../src/features/sharespike/ShareSpikeRouter';
import { useColors } from '../src/theme';

export default function RootLayout() {
  const colors = useColors();
  return (
    <ShareIntentProvider>
      <GestureHandlerRootView style={{ flex: 1 }}>
        <Stack
          screenOptions={{
            contentStyle: { backgroundColor: colors.desk },
            headerStyle: { backgroundColor: colors.desk },
            headerTintColor: colors.graphite,
          }}
        />
        {/* SP-3: dev / spike builds route incoming shares to /share-spike; no-op in store builds. */}
        <ShareSpikeRouter />
        <StatusBar style="auto" />
      </GestureHandlerRootView>
    </ShareIntentProvider>
  );
}
