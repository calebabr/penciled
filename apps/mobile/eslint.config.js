// ESLint flat config for apps/mobile.
const { defineConfig } = require('eslint/config');
const expoConfig = require('eslint-config-expo/flat');
const globals = require('globals');

const noRawStyleValues = require('./eslint-rules/no-raw-style-values');

module.exports = defineConfig([
  expoConfig,
  {
    ignores: ['dist/**', '.expo/**', 'android/**', 'ios/**', 'coverage/**', 'expo-env.d.ts'],
  },
  {
    // Node-side files: config, the custom rule and its Jest tests.
    files: ['eslint-rules/**/*.js', '*.config.js'],
    languageOptions: {
      sourceType: 'commonjs',
      globals: { ...globals.node, ...globals.jest },
    },
  },
  {
    plugins: {
      penciled: { rules: { 'no-raw-style-values': noRawStyleValues } },
    },
  },
  {
    // Token-only zones (BUILD_HANDOFF §1.7 rule 5). src/theme.ts is deliberately excluded.
    files: ['src/ui/**/*.{ts,tsx,js,jsx}', 'src/features/**/*.{ts,tsx,js,jsx}'],
    ignores: ['src/theme.ts'],
    rules: {
      'penciled/no-raw-style-values': 'error',
    },
  },
]);
