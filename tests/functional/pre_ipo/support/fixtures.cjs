const { test: base, expect } = require('@playwright/test');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { UI } = require('./ui.cjs');
function session() {
  if (!process.env.PROFSUR_E2E_SESSION) throw new Error('BLOCKED: Run through scripts/run_pre_ipo_functional.py; arbitrary URLs are prohibited.');
  const s = JSON.parse(fs.readFileSync(process.env.PROFSUR_E2E_SESSION, 'utf8'));
  const u = new URL(s.baseURL);
  if (s.marker !== 'PROFSUR_DISPOSABLE_E2E_V1' || !['127.0.0.1', 'localhost'].includes(u.hostname))
    throw new Error('Unsafe E2E session');
  return s;
}
const test = base.extend({
  ui: async ({ page }, use, info) => {
    const s = session();
    const { profile, theme } = info.project.metadata;
    const account = JSON.parse(fs.readFileSync(s.credentialsFile, 'utf8'))[profile];
    const ui = new UI(page, s, info, account, theme);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    // Authentication deliberately precedes tracing. Passwords are never reporter attachments.
    await ui.login();
    await page.context().tracing.start({ screenshots: true, snapshots: true, sources: false });
    ui.tracing = true;
    try { await use(ui); }
    finally {
      await info.attach('browser-errors', { body: Buffer.from(JSON.stringify(errors)), contentType: 'application/json' });
      await page.screenshot({ path: info.outputPath('final-screen.png'), fullPage: true }).catch(() => {});
      if (info.status !== info.expectedStatus) {
        const trace = info.outputPath('trace.zip');
        await page.context().tracing.stop({ path: trace });
        await info.attach('trace', { path: trace, contentType: 'application/zip' });
      } else await page.context().tracing.stop();
      expect(errors, 'Uncaught browser exceptions').toEqual([]);
      await expect(page.getByTestId('stException'), 'Streamlit exception').toHaveCount(0);
    }
  },
});
function audit(args) {
  const s = session();
  const r = spawnSync(s.python, [path.join(s.suiteRoot, 'support/storage_audit.py'), '--session', process.env.PROFSUR_E2E_SESSION, ...args],
    { encoding: 'utf8', windowsHide: true });
  if (r.status !== 0) throw new Error(`Storage verification failed: ${r.stderr || r.stdout}`);
  return JSON.parse(r.stdout);
}
module.exports = { test, expect, session, audit };
