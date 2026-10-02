import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "@typescript-eslint/eslint-plugin";
import tsparser from "@typescript-eslint/parser";
import js from "eslint-plugin-js";

const plugins = [react, reactHooks, tseslint, js];

const languageOptions = {
  ecmaVersion: 2024,
  sourceType: "module",
  parser: tsparser,
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
  },
};

const rules = {
  ...react.configs.recommended.rules,
  ...reactHooks.configs.recommended.rules,
  "@typescript-eslint/indent": ["error", 2],
  "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
  "react-hooks/exhaustive-deps": "warn",
  ...js.configs.recommended.rules,
};

export default tseslint.config(
  { files: ["**/*.{ts,tsx,js,jsx}"], languageOptions, rules },
  ...tseslint.configs.recommended
);