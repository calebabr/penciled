import { fireEvent, render, screen } from '@testing-library/react-native';

import { palette } from '../../theme';
import { InkButton } from '../InkButton';

describe('InkButton', () => {
  it('renders its label and calls onPress', async () => {
    const onPress = jest.fn();
    await render(<InkButton label="Add" onPress={onPress} />);
    await fireEvent.press(screen.getByRole('button', { name: 'Add' }));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it('does not call onPress when disabled', async () => {
    const onPress = jest.fn();
    await render(<InkButton label="Add" onPress={onPress} disabled />);
    await fireEvent.press(screen.getByRole('button', { name: 'Add' }));
    expect(onPress).not.toHaveBeenCalled();
  });
});

describe('theme palette', () => {
  it('defines the same token names for light and dark', () => {
    expect(Object.keys(palette.dark).sort()).toEqual(Object.keys(palette.light).sort());
  });
});
