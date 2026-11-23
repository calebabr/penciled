/** @type {import('jest').Config} */
module.exports = {
  preset: 'jest-expo',
  roots: ['<rootDir>/src', '<rootDir>/eslint-rules'],
  testPathIgnorePatterns: ['/node_modules/', '/__fixtures__/'],
};
