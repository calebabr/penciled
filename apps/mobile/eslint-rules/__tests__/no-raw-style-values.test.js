/**
 * @jest-environment node
 */
'use strict';

const path = require('node:path');
const { ESLint, RuleTester } = require('eslint');

const rule = require('../no-raw-style-values');

const ruleTester = new RuleTester({
  languageOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
    parserOptions: { ecmaFeatures: { jsx: true } },
  },
});

describe('penciled/no-raw-style-values (rule unit)', () => {
  ruleTester.run('no-raw-style-values', rule, {
    valid: [
      { code: "const s = StyleSheet.create({ a: { color: colors.ink, padding: space[4] } });" },
      { code: "const el = <View style={{ backgroundColor: colors.desk, flex: 1, margin: 0 }} />;" },
      { code: "const label = 'Order #123';" },
      { code: "const s = StyleSheet.create({ a: { borderColor: 'transparent' } });" },
      { code: "const spring = { damping: 18 };" },
    ],
    invalid: [
      { code: "const s = StyleSheet.create({ a: { color: '#fff' } });", errors: [{ messageId: 'rawColor' }] },
      { code: "const c = '#22398F';", errors: [{ messageId: 'rawColor' }] },
      { code: "const c = '#22398F80';", errors: [{ messageId: 'rawColor' }] },
      { code: "const el = <View style={{ backgroundColor: 'rgba(0,0,0,0.5)' }} />;", errors: [{ messageId: 'rawColor' }] },
      { code: 'const c = `hsl(${h}, 50%, 50%)`;', errors: [{ messageId: 'rawColor' }] },
      { code: "const el = <Text style={{ color: 'red' }} />;", errors: [{ messageId: 'namedColor' }] },
      { code: "const s = StyleSheet.create({ a: { padding: 16 } });", errors: [{ messageId: 'rawNumber' }] },
      { code: "const el = <View style={[base, { marginTop: -8 }]} />;", errors: [{ messageId: 'rawNumber' }] },
      {
        code: "const el = <ScrollView contentContainerStyle={{ gap: 12 }} />;",
        errors: [{ messageId: 'rawNumber' }],
      },
    ],
  });
});

describe('apps/mobile ESLint config scoping', () => {
  const cwd = path.resolve(__dirname, '..', '..');
  // Load the real flat config with require(): ESLint's own config-file loader uses a dynamic
  // import(), which Jest's VM does not support without --experimental-vm-modules.
  const eslint = new ESLint({
    cwd,
    overrideConfigFile: true,
    overrideConfig: require('../../eslint.config.js'),
  });
  const RULE = 'penciled/no-raw-style-values';

  const badUi = [
    "import { View } from 'react-native';",
    '',
    'export function Bad() {',
    "  return <View style={{ backgroundColor: '#ffffff' }} />;",
    '}',
    '',
  ].join('\n');

  const goodUi = [
    "import { View } from 'react-native';",
    '',
    "import { useColors } from '../theme';",
    '',
    'export function Good() {',
    '  const colors = useColors();',
    '  return <View style={{ backgroundColor: colors.sheet }} />;',
    '}',
    '',
  ].join('\n');

  async function ruleHits(code, relPath) {
    const [result] = await eslint.lintText(code, { filePath: path.join(cwd, relPath) });
    return result.messages.filter((m) => m.ruleId === RULE);
  }

  it('fails on a raw hex in src/ui', async () => {
    const hits = await ruleHits(badUi, 'src/ui/__fixtures__/BadHex.tsx');
    expect(hits).toHaveLength(1);
    expect(hits[0].severity).toBe(2);
  });

  it('fails on a raw hex in src/features', async () => {
    expect(await ruleHits(badUi, 'src/features/__fixtures__/BadHex.tsx')).toHaveLength(1);
  });

  it('passes on a theme token in src/ui', async () => {
    expect(await ruleHits(goodUi, 'src/ui/__fixtures__/GoodToken.tsx')).toHaveLength(0);
  });

  it('does not apply to src/theme.ts', async () => {
    expect(await ruleHits("export const c = '#FFFFFF';\n", 'src/theme.ts')).toHaveLength(0);
  });
});
