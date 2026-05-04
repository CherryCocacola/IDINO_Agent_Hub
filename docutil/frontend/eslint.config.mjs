import nextConfig from "eslint-config-next";
import tseslint from "typescript-eslint";
import importPlugin from "eslint-plugin-import";
import prettierConfig from "eslint-config-prettier";

export default tseslint.config(
  // Ignore patterns (must be first)
  {
    ignores: [
      ".next/",
      "node_modules/",
      "dist/",
      "out/",
      "playwright-report/",
      "test-results/",
      "e2e/",
      "*.config.{js,mjs,ts}",
      "postcss.config.mjs",
      "take-screenshot.mjs",
    ],
  },

  // Next.js recommended rules (flat config)
  ...nextConfig,

  // TypeScript strict rules
  ...tseslint.configs.strict,

  // Prettier — disables conflicting ESLint formatting rules
  prettierConfig,

  // Project-wide settings
  {
    files: ["**/*.{ts,tsx}"],
    plugins: {
      import: importPlugin,
    },
    rules: {
      // ── Unused variables ──
      "@typescript-eslint/no-unused-vars": [
        "error",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
          caughtErrorsIgnorePattern: "^_",
        },
      ],

      // ── Import order (builtin → external → internal → parent → sibling) ──
      "import/order": [
        "error",
        {
          groups: ["builtin", "external", "internal", "parent", "sibling", "index"],
          pathGroups: [
            {
              pattern: "@/**",
              group: "internal",
              position: "before",
            },
          ],
          pathGroupsExcludedImportTypes: ["builtin"],
          "newlines-between": "always",
          alphabetize: { order: "asc", caseInsensitive: true },
        },
      ],

      // ── Stricter TypeScript rules (relax a few too noisy for React) ──
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-non-null-assertion": "warn",
      "@typescript-eslint/no-empty-object-type": "off",
      "@typescript-eslint/no-invalid-void-type": "off",

      // ── General quality ──
      "no-console": ["warn", { allow: ["warn", "error"] }],
      eqeqeq: ["error", "always"],
      "prefer-const": "error",
    },
  },
);
