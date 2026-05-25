import globals from "globals";

export default [
  {
    ignores: [
      "**/node_modules/**",
      "**/dist/**",
      "**/build/**",
      "**/venv/**",
      "**/.venv/**",
      "**/.pytest_cache/**",
      "**/__pycache__/**",
      "**/*.min.js",
      "**/*.bundle.js",
      "**/coverage/**",
      "**/.cache/**",
      "**/temp/**",
      "**/temp_miara_extract/**",
    ],
  },
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    rules: {
      // General JavaScript rules
      "prefer-const": "warn",
      "no-unused-vars": "warn",
      "no-console": "warn",
      "no-debugger": "warn",
      "no-empty": "warn",
      "no-irregular-whitespace": "warn",
      "no-case-declarations": "warn",
      "no-fallthrough": "warn",
      "no-mixed-spaces-and-tabs": "warn",
      "no-redeclare": "warn",
      "no-undef": "warn",
      "no-unreachable": "warn",
      "no-useless-escape": "warn",
    },
  },
];
