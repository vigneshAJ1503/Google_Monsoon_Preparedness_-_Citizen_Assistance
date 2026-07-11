import { test } from '@playwright/test';

const BASE_URL = 'http://localhost';

test('Debug - check badge', async ({ page }) => {
  await page.goto(BASE_URL);
  await page.waitForLoadState('networkidle');
  
  // Setup
  await page.click('button:has-text("Settings")');
  await page.waitForLoadState('networkidle');
  const numberInputs = page.locator('input[type="number"]');
  await numberInputs.nth(0).fill('11.0168');
  await numberInputs.nth(1).fill('76.9558');
  await numberInputs.nth(2).fill('3');
  await page.click('button:has-text("Save profile context")');
  await page.waitForTimeout(2000);
  
  // Go to preparedness
  await page.click('button:has-text("Personalized Plan")');
  await page.waitForLoadState('networkidle');
  
  // Generate plan
  await page.click('button:has-text("Generate Preparedness Plan")');
  
  // Wait and print page content
  await page.waitForTimeout(15000);
  
  // Check for badge elements
  const badges = await page.locator('.badge').all();
  console.log('=== BADGES ===');
  for (const badge of badges) {
    const text = await badge.textContent();
    const className = await badge.getAttribute('class');
    console.log(`badge: "${text}", class: ${className}`);
  }
  
  // Check for risk level text
  const text = await page.textContent('body');
  const lines = text.split('\n');
  for (const line of lines) {
    if (line.includes('Risk') || line.includes('LOW') || line.includes('MODERATE') || line.includes('HIGH') || line.includes('SEVERE')) {
      console.log('RISK LINE:', line.trim());
    }
  }
});