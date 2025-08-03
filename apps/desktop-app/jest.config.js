module.exports = {
  testEnvironment: 'jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/electron_app/src/$1',
  },
  transform: {
    '^.+\.(ts|tsx)$': 'ts-jest',
  },
};