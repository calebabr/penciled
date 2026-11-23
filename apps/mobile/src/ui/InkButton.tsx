import { Pressable, StyleSheet, Text } from 'react-native';

import { hit, radius, space, type, useColors } from '../theme';

type Props = {
  label: string;
  onPress: () => void;
  disabled?: boolean;
};

// Token-only primary button (placeholder for CMP-BUTTON). Uses theme tokens exclusively so the
// no-raw-style-values lint has real code to check in src/ui.
export function InkButton({ label, onPress, disabled = false }: Props) {
  const colors = useColors();
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      style={[styles.base, { backgroundColor: colors.ink }]}
    >
      <Text style={[styles.label, { color: colors.onInk }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    minHeight: hit.min,
    paddingHorizontal: space[4],
    paddingVertical: space[3],
    borderRadius: radius.button,
    alignItems: 'center',
    justifyContent: 'center',
  },
  label: {
    ...type.headline,
  },
});
