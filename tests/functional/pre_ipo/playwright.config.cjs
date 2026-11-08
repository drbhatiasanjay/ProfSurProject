const { defineConfig } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');
const sessionPath = process.env.PROFSUR_E2E_SESSION;
// Listing is allowed without a running app; executing fixtures requires the launcher.
const session = sessionPath ? JSON.parse(fs.readFileSync(sessionPath, 'utf8')) : null;
const profiles = ['profsurkumar', 'skumar', 'drbhatia', 'sbhatia', 'e2e_new_researcher'];
module.exports = defineConfig({
  testDir: './specs', fullyParallel: false, workers: 1, retries: 0,
  timeout: 180000, expect: { timeout: 20000 }, forbidOnly: true,
  outputDir: session ? path.join(session.runDir, 'artifacts') : './test-results',
  reporter: [['list'], [require.resolve('./support/reporter.cjs')],
    ['html', { outputFolder: session ? path.join(session.runDir, 'html-report') : './playwright-report', open: 'never' }]],
  use: { browserName: 'chromium', headless: process.env.PROFSUR_E2E_HEADLESS === '1', acceptDownloads: true,
    viewport: { width: 1510, height: 1050 }, trace: 'off', video: 'off', screenshot: 'only-on-failure',
    baseURL: session?.baseURL },
  projects: profiles.flatMap(profile => ['dark', 'light'].map(theme => ({
    name: `${profile}-${theme}`, metadata: { profile, theme },
    testIgnore: profile === 'sbhatia' ? /(?:workflow|ingestion|review|models|lifecycle|corpus|reference)\.spec\.cjs/ :
      (profile !== 'drbhatia' || theme !== 'dark') ? /corpus\.spec\.cjs/ : undefined,
    grepInvert: process.env.PROFSUR_E2E_CORPUS === '1' ? undefined : /@corpus/,
  }))),
});
