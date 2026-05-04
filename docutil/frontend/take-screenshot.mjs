import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1400, height: 900 },
  deviceScaleFactor: 2,  // Higher DPI for better rendering
});
const page = await context.newPage();

// Collect console logs
page.on('console', msg => console.log('PAGE LOG:', msg.text()));
page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

// Login page - wait longer for JS to execute
console.log('Navigating to login page...');
await page.goto('http://localhost:3003/login', { waitUntil: 'load' });
console.log('Page loaded, waiting for network idle...');
await page.waitForLoadState('networkidle');
console.log('Network idle, waiting 5 more seconds for CSS...');
await page.waitForTimeout(5000);

// Force all CSS to be computed
await page.evaluate(() => {
  document.body.offsetHeight;  // Force reflow
});

// Check if the correct text is visible
const hasKorean = await page.locator('text=아이디').count();
console.log('Korean text "아이디" found:', hasKorean, 'times');

const hasDocUtil = await page.locator('text=DocUtil').count();
console.log('DocUtil text found:', hasDocUtil, 'times');

// Check CSS loading
const cssLoaded = await page.evaluate(() => {
  const styles = document.querySelectorAll('link[rel="stylesheet"]');
  return Array.from(styles).map(s => s.href);
});
console.log('Loaded stylesheets:', cssLoaded);

// Check computed style on primary element
const primaryColor = await page.evaluate(() => {
  const el = document.querySelector('.text-primary');
  if (el) {
    return window.getComputedStyle(el).color;
  }
  return 'No .text-primary element found';
});
console.log('Primary text color:', primaryColor);

await page.screenshot({ path: 'screenshot-login.png', fullPage: true });
console.log('Login screenshot saved');

await browser.close();
