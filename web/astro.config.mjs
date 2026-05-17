import { defineConfig } from "astro/config";
import react from "@astrojs/react";

export default defineConfig({
  site: process.env.PAGES_SITE ?? "http://localhost:4321",
  base: process.env.PAGES_BASE ?? "",
  output: "static",
  trailingSlash: "ignore",
  integrations: [react()],
  markdown: {
    syntaxHighlight: "shiki",
    shikiConfig: { theme: "github-dark-dimmed" },
  },
});
