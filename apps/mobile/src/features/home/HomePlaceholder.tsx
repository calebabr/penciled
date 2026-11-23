import { StyleSheet, Text, View } from 'react-native';

import { space, type, useColors } from '../../theme';
import { InkButton } from '../../ui/InkButton';

type Props = {
  onOpenSp13?: () => void;
  onOpenShareSpike?: () => void;
};

export function HomePlaceholder({ onOpenSp13, onOpenShareSpike }: Props) {
  const colors = useColors();
  return (
    <View style={[styles.root, { backgroundColor: colors.desk }]}>
      <Text style={[styles.title, { color: colors.graphite }]}>Penciled</Text>
      <Text style={[styles.body, { color: colors.graphiteSoft }]}>
        New screenshots will show up here as drafts.
      </Text>
      {onOpenSp13 ? <InkButton label="Open SP-13 smoke test" onPress={onOpenSp13} /> : null}
      {onOpenShareSpike ? <InkButton label="Open SP-3 share spike" onPress={onOpenShareSpike} /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    padding: space[4],
    gap: space[3],
    justifyContent: 'center',
  },
  title: {
    ...type.cardTitle,
  },
  body: {
    ...type.body,
  },
});
