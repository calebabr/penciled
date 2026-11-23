import { Redirect, Stack } from 'expo-router';

import { Sp13Screen } from '../src/features/sp13/Sp13Screen';

// SP-13 smoke screen: dev builds only. Release builds redirect home.
export default function Sp13Route() {
  if (!__DEV__) return <Redirect href="/" />;
  return (
    <>
      <Stack.Screen options={{ title: 'SP-13 matrix' }} />
      <Sp13Screen />
    </>
  );
}
