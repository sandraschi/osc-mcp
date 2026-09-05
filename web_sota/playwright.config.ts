import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 20000,
  webServer: {
    command: "npx vite --port 10766 --host 127.0.0.1",
    port: 10766,
    reuseExistingServer: true,
  },
  use: {
    baseURL: "http://127.0.0.1:10766",
    trace: "on-first-retry",
  },
});
