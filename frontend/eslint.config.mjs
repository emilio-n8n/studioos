import { defineConfig, globalIgnores } from "eslint/config";
import nextjs from "eslint-config-next";

const eslintConfig = defineConfig([
  ...nextjs,
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
