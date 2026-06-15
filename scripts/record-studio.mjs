#!/usr/bin/env node
/**
 * Studio recording driver using npm/pnpm-based Playwright.
 *
 * Run from WSL inside chief-engineer/:
 *   npx playwright install chromium   # one-time
 *   node scripts/record-studio.mjs
 *
 * This script:
 *   - Sources the Cap CLI skill so `cap` is available.
 *   - Checks/starts a Cap screen recording if none is running.
 *   - Connects to an existing Chrome CDP window (launched by record-studio.sh).
 *   - Clicks WARM UP and waits for the ZeroGPU model.
 *   - Drives the demo beats with generous waits.
 *   - Leaves the raw .cap project in Cap Desktop Studio (no export).
 */
import { exec, execSync } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';
import { chromium } from 'playwright';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT = resolve(__dirname, '..');

const SPACE_URL = process.env.CHIEF_ENGINEER_SPACE_URL || 'https://node.microfactory.space';
const CDP_URL = process.env.CDP_URL || 'http://172.25.144.1:9222';
const CAP_FPS = '60';
const WARMUP_WAIT_MS = 35000;
const INFERENCE_WAIT_MS = 10000;
const PAUSE_S = Number(process.argv.find(a => a.startsWith('--pause='))?.split('=')[1] || 3);
const BEAT_ARG = process.argv.find(a => a.startsWith('--beat='))?.split('=')[1] || 'all';

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

function capBin() {
  try {
    return execSync('which cap', { encoding: 'utf8' }).trim();
  } catch {
    return '/mnt/c/Users/kyleb/AppData/Local/Cap/cap-cli.exe';
  }
}

function cap(args, timeoutMs = 120000) {
  return new Promise((resolve, reject) => {
    exec(`${capBin()} ${args.join(' ')}`, { timeout: timeoutMs, encoding: 'utf8' }, (err, stdout, stderr) => {
      resolve({ err, stdout, stderr, ok: !err });
    });
  });
}

function capJson(args) {
  const r = execSync(`${capBin()} ${args.join(' ')}`, { encoding: 'utf8', timeout: 120000 });
  for (const line of r.split('\n')) {
    const t = line.trim();
    if (t.startsWith('{') && t.endsWith('}')) {
      try { return JSON.parse(t); } catch { }
    }
  }
  return null;
}

function isRecording() {
  try {
    const status = capJson(['status', '--json']);
    if (status?.recording || status?.status === 'recording') return true;
  } catch { }
  try {
    const list = capJson(['list', '--json']);
    if (list?.recordings) {
      for (const r of list.recordings) {
        if (['recording', 'in-progress'].includes(r.state)) return true;
      }
    }
  } catch { }
  return false;
}

function startRecording() {
  if (isRecording()) {
    console.log('  ✓ Cap is already recording');
    return null;
  }
  const targets = capJson(['targets', '--json']);
  const screens = targets?.screens || [];
  const screen = screens.find(s => s.primary) || screens[0];
  if (!screen) throw new Error('no Cap screen target');
  console.log(`  starting Cap recording (screen ${screen.id})...`);
  const rec = capJson(['record', 'start', '--screen', String(screen.id), '--fps', CAP_FPS, '--detach', '--json']);
  if (!rec) throw new Error('failed to start Cap recording');
  console.log(`  ✓ Cap recording started (${rec.recordingId || '?'})`);
  return rec;
}

async function openOverride(page) {
  const popup = page.locator('#ce-popup-override');
  if (!(await popup.isVisible().catch(() => false))) {
    await page.locator('#ce-override').first().click().catch(() => { });
    await sleep(300);
  }
}

async function closeOverride(page) {
  const popup = page.locator('#ce-popup-override');
  if (await popup.isVisible().catch(() => false)) {
    await page.locator('#ce-popup-override .ce-popup-close').first().click().catch(() => { });
    await sleep(200);
  }
}

async function setSensors(page, t, h) {
  const inputs = page.locator('#ce-popup-override .ce-num input');
  await inputs.nth(0).fill(String(t)).catch(() => { });
  await inputs.nth(0).dispatchEvent('change').catch(() => { });
  await inputs.nth(1).fill(String(h)).catch(() => { });
  await inputs.nth(1).dispatchEvent('change').catch(() => { });
}

async function pill(page, value) {
  await page.locator('.ce-pills label', { hasText: value }).first().click();
}

async function warmModel(page) {
  console.log('  warming the model (WARM UP)...');
  await page.goto(`${SPACE_URL}/?__theme=dark`, { waitUntil: 'domcontentloaded' });
  await sleep(2000);
  await page.locator('#ce-warm').first().click({ timeout: 5000 }).catch(() => {
    console.log('  ⚠ WARM UP button not found — proceeding anyway');
  });
  console.log(`  waiting ${WARMUP_WAIT_MS / 1000}s for model load...`);
  await sleep(WARMUP_WAIT_MS);
  console.log('  warm-up complete');
}

async function beatLoad(page) {
  await page.getByRole('tab', { name: 'LOAD' }).click();
  await sleep(500);
  await openOverride(page);
  await setSensors(page, 28, 60);
  await closeOverride(page);
  await pill(page, 'PLA');
  await sleep(500);
  await page.locator('#ce-benchy').first().click();
  await sleep(2500);
}

async function beatSlice(page) {
  await page.locator('#ce-run').first().click();
  await sleep(INFERENCE_WAIT_MS);
  console.log('  waiting for reasoning to land...');
  await sleep(4000);
}

async function beatSecondOpinion(page) {
  await page.locator("input[type=radio][value='Second Opinion']").first().check();
  await sleep(5000);
}

async function beatScrub(page) {
  const sliders = page.locator('input[type=range]');
  const count = await sliders.count();
  const sl = sliders.nth(count - 1);
  for (const v of [8, 18, 30, 40]) {
    await sl.fill(String(v));
    await sl.dispatchEvent('input');
    await sl.dispatchEvent('change');
    await sleep(1200);
  }
}

async function beatPlacement(page) {
  await page.getByRole('tab', { name: 'LOAD' }).click();
  await sleep(500);
  await pill(page, 'ABS');
  await openOverride(page);
  await pill(page, 'corner');
  await closeOverride(page);
  await page.locator('#ce-benchy').first().click();
  await sleep(500);
  await page.locator('#ce-run').first().click();
  await sleep(INFERENCE_WAIT_MS);
  console.log('  waiting for placement reasoning...');
  await sleep(4000);
}

async function beatClimbingJob(page) {
  await page.getByRole('tab', { name: 'LOAD' }).click();
  await sleep(500);
  await openOverride(page);
  await setSensors(page, 30, 65);
  await closeOverride(page);
  await pill(page, 'PETG');
  await page.locator('#ce-benchy').first().click();
  await sleep(2500);
  await page.locator('#ce-run').first().click();
  await sleep(INFERENCE_WAIT_MS);
  console.log('  waiting for climbing-job reasoning...');
  await sleep(4000);
}

async function beatPrintLoop(page) {
  await page.getByRole('tab', { name: 'PRINT' }).click();
  await sleep(500);
  await page.locator('#ce-print-run, #ce-print').first().click();
  console.log('  waiting for print simulation + curve...');
  await sleep(10000);
}

async function beatReview(page) {
  await page.getByRole('tab', { name: 'REVIEW' }).click();
  await sleep(5000);
}

const BEATS = {
  '3': [beatLoad, beatSlice],
  'scrub': [beatLoad, beatSlice, beatScrub],
  'second': [beatLoad, beatSlice, beatSecondOpinion],
  'placement': [beatPlacement],
  'climb': [beatClimbingJob, beatPrintLoop, beatReview],
  'loop': [beatPrintLoop, beatReview],
  'all': [beatLoad, beatSlice, beatSecondOpinion, beatScrub, beatPlacement, beatClimbingJob, beatPrintLoop, beatReview],
};

async function main() {
  console.log(`\n=== RECORD (studio) via npm/pnpm playwright ===\n`);
  console.log(`  CDP URL: ${CDP_URL}`);
  console.log(`  beat:    ${BEAT_ARG}\n`);

  const rec = startRecording();
  if (!rec && !isRecording()) {
    console.error('  ✗ could not confirm an active Cap recording');
    process.exit(1);
  }
  const recId = rec?.recordingId;

  console.log(`  connecting to Chrome CDP at ${CDP_URL}...`);
  const browser = await chromium.connectOverCDP(CDP_URL);
  const context = browser.contexts()[0] || await browser.newContext();
  const page = context.pages()[0] || await context.newPage();
  await page.setViewportSize({ width: 1707, height: 1067 });

  await warmModel(page);

  console.log('  navigating to Space for recording take...');
  await page.goto(`${SPACE_URL}/?__theme=dark`, { waitUntil: 'domcontentloaded' });
  await sleep(2000);

  const steps = BEATS[BEAT_ARG];
  if (!steps) {
    console.error(`Unknown beat: ${BEAT_ARG}`);
    process.exit(1);
  }
  for (let i = 0; i < steps.length; i++) {
    console.log(`  [${i + 1}/${steps.length}] ${steps[i].name}`);
    await steps[i](page);
    console.log(`  pausing ${PAUSE_S}s between beats...`);
    await sleep(PAUSE_S * 1000);
  }

  console.log('  beats complete — holding 4s for closing shot...');
  await sleep(4000);
  await browser.close();

  console.log('\n=== STUDIO MODE DONE ===');
  console.log('  Cap is still recording. Stop it manually in Cap Desktop, or run:');
  console.log(`    cap record stop${recId ? ` --id ${recId}` : ''}`);
  console.log('  The raw .cap project can now be edited/exported from Cap Desktop Studio.');
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
