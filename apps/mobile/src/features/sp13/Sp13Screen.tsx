import { useFonts } from '@expo-google-fonts/recursive/useFonts';
import { Recursive_500Medium } from '@expo-google-fonts/recursive/500Medium';
import { Recursive_600SemiBold } from '@expo-google-fonts/recursive/600SemiBold';
import { FlashList } from '@shopify/flash-list';
import { useShareIntentContext } from 'expo-share-intent';
import { useCallback, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import Animated, { useAnimatedStyle, useSharedValue, withTiming } from 'react-native-reanimated';
import { scheduleOnRN } from 'react-native-worklets';

import { border, motion, radius, space, type, useColors } from '../../theme';
import { InkButton } from '../../ui/InkButton';
import {
  PROBE_LABELS,
  PROBE_ORDER,
  type ProbeId,
  type ProbeResult,
  probeCalendar,
  probeMediaLibrary,
  probeMlkit,
  probeSecureStore,
  probeSqlite,
} from './probes';

type Results = Partial<Record<ProbeId, ProbeResult>>;

const LIST_ITEMS = Array.from({ length: 50 }, (_, i) => ({ id: String(i) }));

export function Sp13Screen() {
  const colors = useColors();
  const [results, setResults] = useState<Results>({});
  const [running, setRunning] = useState(false);
  const [listLoaded, setListLoaded] = useState<number | null>(null);
  const [fontsLoaded, fontError] = useFonts({ Recursive_500Medium, Recursive_600SemiBold });
  const share = useShareIntentContext();
  const progress = useSharedValue(0);
  const animatedStyle = useAnimatedStyle(() => ({ opacity: progress.value }));

  const record = useCallback((id: ProbeId, result: ProbeResult) => {
    setResults((prev) => ({ ...prev, [id]: result }));
  }, []);

  const runReanimated = useCallback(
    () =>
      new Promise<ProbeResult>((resolve) => {
        const timeout = setTimeout(() => resolve({ ok: false, detail: 'animation callback timed out' }), 3000);
        const done = (finished: boolean) => {
          clearTimeout(timeout);
          resolve({ ok: finished, detail: `withTiming finished=${finished}` });
        };
        progress.value = 0;
        progress.value = withTiming(1, { duration: motion.flood }, (finished) => {
          'worklet';
          scheduleOnRN(done, finished === true);
        });
      }),
    [progress],
  );

  const runAll = useCallback(async () => {
    setRunning(true);
    setResults({});
    record('sqlite', await probeSqlite());
    record('mlkit', await probeMlkit());
    record('flashlist', {
      ok: listLoaded !== null,
      detail: listLoaded !== null ? `rendered; onLoad ${Math.round(listLoaded)} ms` : 'onLoad not fired',
    });
    record('reanimated', await runReanimated());
    record('shareIntent', {
      ok: share.isReady && share.error === null,
      detail: `isReady=${share.isReady}; hasShareIntent=${share.hasShareIntent}; error=${share.error ? 'yes' : 'no'}`,
    });
    record('calendar', await probeCalendar());
    record('mediaLibrary', await probeMediaLibrary());
    record('secureStore', await probeSecureStore());
    record('font', {
      ok: fontsLoaded && !fontError,
      detail: fontError ? `error: ${fontError.name}` : `loaded=${fontsLoaded}`,
    });
    setRunning(false);
  }, [fontError, fontsLoaded, listLoaded, record, runReanimated, share]);

  const passed = PROBE_ORDER.filter((id) => results[id]?.ok).length;
  const ran = PROBE_ORDER.filter((id) => results[id]).length;

  return (
    <ScrollView
      style={{ backgroundColor: colors.desk }}
      contentContainerStyle={styles.content}
      accessibilityLabel="SP-13 smoke test"
    >
      <InkButton label={running ? 'Running…' : 'Run all SP-13 probes'} onPress={runAll} disabled={running} />
      <Text style={[styles.summary, { color: colors.graphite }]}>
        {ran === 0 ? 'Not run yet' : `${passed} / ${PROBE_ORDER.length} passed`}
      </Text>

      {PROBE_ORDER.map((id) => {
        const r = results[id];
        const status = r ? (r.ok ? 'PASS' : 'FAIL') : '—';
        const statusColor = r ? (r.ok ? colors.ink : colors.correction) : colors.graphiteSoft;
        return (
          <View key={id} style={[styles.row, { borderColor: colors.hairline, backgroundColor: colors.sheet }]}>
            <View style={styles.rowHead}>
              <Text style={[styles.rowLabel, { color: colors.graphite }]}>{PROBE_LABELS[id]}</Text>
              <Text style={[styles.rowStatus, { color: statusColor }]} testID={`sp13-status-${id}`}>
                {status}
              </Text>
            </View>
            {r ? <Text style={[styles.rowDetail, { color: colors.graphiteSoft }]}>{r.detail}</Text> : null}
          </View>
        );
      })}

      <Text style={[styles.sectionTitle, { color: colors.graphite }]}>Recursive (Linear 600 / 500)</Text>
      {fontsLoaded ? (
        <>
          <Text style={[styles.fontTitle, { color: colors.graphite }]}>Pizza Night</Text>
          <Text style={[styles.fontDate, { color: colors.graphite }]}>Thu, Jan 22 · 7:00 PM</Text>
        </>
      ) : (
        <Text style={[styles.rowDetail, { color: colors.graphiteSoft }]}>Loading fonts…</Text>
      )}

      <Text style={[styles.sectionTitle, { color: colors.graphite }]}>Reanimated</Text>
      <Animated.View style={[styles.animBox, { backgroundColor: colors.ink }, animatedStyle]} />

      <Text style={[styles.sectionTitle, { color: colors.graphite }]}>FlashList v2 (50 rows)</Text>
      <View style={[styles.listBox, { borderColor: colors.hairline }]}>
        <FlashList
          data={LIST_ITEMS}
          keyExtractor={(item) => item.id}
          nestedScrollEnabled
          onLoad={({ elapsedTimeInMs }) => setListLoaded(elapsedTimeInMs)}
          renderItem={({ item }) => (
            <Text style={[styles.listRow, { color: colors.graphite }]}>Row {item.id}</Text>
          )}
        />
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: {
    padding: space[4],
    gap: space[3],
  },
  summary: {
    ...type.headline,
  },
  row: {
    borderWidth: border.width,
    borderRadius: radius.field,
    padding: space[3],
    gap: space[1],
  },
  rowHead: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  rowLabel: {
    ...type.body,
  },
  rowStatus: {
    ...type.headline,
  },
  rowDetail: {
    ...type.footnote,
  },
  sectionTitle: {
    ...type.headline,
    marginTop: space[3],
  },
  fontTitle: {
    ...type.cardTitle,
  },
  fontDate: {
    ...type.dateLine,
  },
  animBox: {
    width: space[10],
    height: space[10],
    borderRadius: radius.button,
  },
  listBox: {
    height: space[10] * 5,
    borderWidth: border.width,
    borderRadius: radius.field,
  },
  listRow: {
    ...type.body,
    paddingHorizontal: space[3],
    paddingVertical: space[2],
  },
});
