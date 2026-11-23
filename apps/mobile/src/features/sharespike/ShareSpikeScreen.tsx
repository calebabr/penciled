import { useCallback } from 'react';
import { type LayoutChangeEvent, ScrollView, StyleSheet, Text, View } from 'react-native';

import { border, radius, space, type, useColors } from '../../theme';
import { InkButton } from '../../ui/InkButton';
import { READING_BUDGET_MS, SPIKE_TARGET, formatTable, summarize } from './stats';
import { clearSamples, markReadingVisible, useShareSpikeState } from './store';

// SP-3 spike screen (dev / spike builds only). Shows a "Reading…" placeholder card the moment a
// share arrives (its layout time is the "Reading visible" measurement), then the running
// timing table for the builder to copy. Content-free: no image, file name or path is shown.
export function ShareSpikeScreen() {
  const colors = useColors();
  const { samples, pendingN } = useShareSpikeState();
  const summary = summarize(samples);
  const latest = samples.at(-1);

  const onPlaceholderLayout = useCallback(
    (_e: LayoutChangeEvent) => {
      if (pendingN === null) return;
      const n = pendingN;
      // Next frame ≈ first paint of the placeholder.
      requestAnimationFrame(() => markReadingVisible(n));
    },
    [pendingN],
  );

  return (
    <ScrollView
      style={{ backgroundColor: colors.desk }}
      contentContainerStyle={styles.content}
      accessibilityLabel="Share spike"
    >
      {pendingN !== null ? (
        <View
          key={`pending-${pendingN}`}
          onLayout={onPlaceholderLayout}
          style={[styles.card, { borderColor: colors.hairline, backgroundColor: colors.sheet }]}
          testID="sharespike-reading"
        >
          <Text style={[styles.cardTitle, { color: colors.graphite }]}>Reading…</Text>
          <Text style={[styles.detail, { color: colors.graphiteSoft }]}>Share {pendingN}</Text>
        </View>
      ) : (
        <View style={[styles.card, { borderColor: colors.hairline, backgroundColor: colors.sheet }]}>
          <Text style={[styles.cardTitle, { color: colors.graphite }]}>
            {latest ? `Share ${latest.n} received` : 'Waiting for a share'}
          </Text>
          <Text style={[styles.detail, { color: colors.graphiteSoft }]}>
            {latest
              ? `${latest.mimeType} · files ${latest.fileCount} · readable ${
                  latest.uriReadable === null ? '?' : latest.uriReadable ? 'yes' : 'no'
                }`
              : 'Share one screenshot to Penciled from Photos or the screenshot thumbnail.'}
          </Text>
        </View>
      )}

      <Text style={[styles.count, { color: colors.graphite }]} testID="sharespike-count">
        {summary.count} / {SPIKE_TARGET}
      </Text>
      <Text style={[styles.detail, { color: colors.graphiteSoft }]}>
        Within {READING_BUDGET_MS} ms of start/foreground: {summary.withinBudget} / {summary.measured}. Times are
        measured in JS: native launch before the bundle starts is not included (cold rows).
      </Text>

      <View style={[styles.table, { borderColor: colors.hairline, backgroundColor: colors.sheet }]}>
        <Text selectable style={[styles.mono, { color: colors.graphite }]} testID="sharespike-table">
          {formatTable(samples)}
        </Text>
      </View>

      <InkButton label="Clear samples" onPress={clearSamples} disabled={samples.length === 0} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: {
    padding: space[4],
    gap: space[3],
  },
  card: {
    borderWidth: border.width,
    borderRadius: radius.card,
    padding: space[4],
    gap: space[1],
  },
  cardTitle: {
    ...type.headline,
  },
  count: {
    ...type.dateLine,
  },
  detail: {
    ...type.footnote,
  },
  table: {
    borderWidth: border.width,
    borderRadius: radius.field,
    padding: space[3],
  },
  mono: {
    ...type.caption,
    fontVariant: ['tabular-nums'],
  },
});
