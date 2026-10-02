const react = require("eslint-plugin-react");
const reactHooks = require("eslint-plugin-react-hooks");
const tsEslint = require("@typescript-eslint/eslint-plugin");
const tsParser = require("@typescript-eslint/parser");

module.exports = {
  languageOptions: {
    ecmaVersion: 2024,
    sourceType: "module",
    parser: tsParser,
    parserOptions: {
      ecmaFeatures: { jsx: true },
    },
  },
  plugins: [react, reactHooks, tsEslint],
  rules: {
    ...react.configs.recommended.rules,
    ...reactHooks.configs.recommended.rules,
    "react-hooks/exhaustive-deps": "warn",
    "@typescript-eslint/indent": ["error", 2],
    "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
  },
};