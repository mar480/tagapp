import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1, retries: 0,
  timeout: 30_000, reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:4173', trace: 'retain-on-failure',
    launchOptions: { executablePath: process.env.TAGGER_BROWSER_EXECUTABLE } },
  webServer: [
    { command: '"$TAGGER_TEST_PYTHON" ../api/manage.py runserver 127.0.0.1:8011 --noreload',
      url: 'http://127.0.0.1:8011/health/', reuseExistingServer: false },
    { command: 'npm run dev -- --port 4173', url: 'http://127.0.0.1:4173', reuseExistingServer: false,
      env: { TAGGER_DEV_API: 'http://127.0.0.1:8011' } },
  ],
});
