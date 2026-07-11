import { test } from '@playwright/test';

const BASE_URL = 'http://localhost';

test('Debug - check checklist with plan', async ({ page }) => {
  await page.goto(BASE_URL);
  await page.waitForLoadState('networkidle');
  
  // Setup
  await page.click('button:has-text("Settings")');
  await page.waitForLoadState('networkidle');
  const numberInputs = page.locator('input[type="number"]');
  await numberInputs.nth(0).fill('11.0168');
  await numberInputs.nth(1).fill('76.9558');
  await numberInputs.nth(2).fill('2');
  await page.click('button:has-text("Save profile context")');
  await page.waitForTimeout(2000);
  
  // Generate plan
  await page.click('button:has-text("Personalized Plan")');
  await page.waitForLoadState('networkidle');
  await page.click('button:has-text("Generate Preparedness Plan")');
  await page.waitForTimeout(15000);
  
  // Check if plan shows on preparedness tab
  const planText = await page.textContent('body');
  console.log('=== PREPAREDNESS TAB ===');
  console.log(planText);
  
  // Go to checklist
  await page.click('button:has-text("My Checklist")');
  await page.waitForLoadState('networkidle');
  
  const checklistText = await page.textContent('body');
  console.log('=== CHECKLIST TAB ===');
  console.log(checklistText);
});