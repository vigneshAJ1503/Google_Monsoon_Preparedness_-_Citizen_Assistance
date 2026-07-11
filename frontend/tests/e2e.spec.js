import { test, expect } from '@playwright/test';

const BASE_URL = 'http://localhost';

test.describe('Monsoon Prep App - E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
  });

  test('Dashboard - loads weather and alerts', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Monsoon Prep');
    
    await expect(page.locator('text=Current Weather Condition')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=Location:').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=No active verified alerts reported').or(page.locator('text=Verified Alert Active'))).toBeVisible();
  });

  test('Navigation tabs work', async ({ page }) => {
    const tabs = ['Dashboard', 'Personalized Plan', 'My Checklist', 'Safety Assistant', 'Travel Advisory', 'Settings'];
    
    for (const tab of tabs) {
      await page.click(`button:has-text("${tab}")`);
      await page.waitForTimeout(500);
    }
  });

  test('Settings - can configure household profile', async ({ page }) => {
    await page.click('button:has-text("Settings")');
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('text=Household & Location Setup')).toBeVisible();
    
    // Fill location - use label-based selector
    await page.fill('label:has-text("Latitude") + input', '11.0168');
    await page.fill('label:has-text("Longitude") + input', '76.9558');
    
    // Household size
    await page.fill('label:has-text("Household size") + input', '4');
    
    // Housing type
    await page.selectOption('label:has-text("Housing type") + select', 'independent_house');
    
    // Checkboxes
    await page.check('label:has-text("Children present") >> input');
    await page.check('label:has-text("Pets present") >> input');
    
    // Save
    await page.click('button:has-text("Save profile context")');
    await expect(page.locator('text=Profile context updated successfully')).toBeVisible({ timeout: 10000 });
  });

  test('Preparedness - generates personalized plan', async ({ page }) => {
    // Setup household
    await page.click('button:has-text("Settings")');
    await page.waitForLoadState('networkidle');
    await page.fill('label:has-text("Latitude") + input', '11.0168');
    await page.fill('label:has-text("Longitude") + input', '76.9558');
    await page.fill('label:has-text("Household size") + input', '3');
    await page.click('button:has-text("Save profile context")');
    await expect(page.locator('text=Profile context updated successfully')).toBeVisible({ timeout: 10000 });
    
    // Go to preparedness and generate
    await page.click('button:has-text("Personalized Plan")');
    await page.waitForLoadState('networkidle');
    await page.click('button:has-text("Generate Preparedness Plan")');
    
    // Wait for plan sections
    await expect(page.locator('text=Do Now')).toBeVisible({ timeout: 25000 });
    await expect(page.locator('text=Next 6 Hours')).toBeVisible();
    await expect(page.locator('text=Next 24 Hours')).toBeVisible();
    await expect(page.locator('text=Essential Emergency Kit Checklist')).toBeVisible();
    
    // Verify risk level
    await expect(page.locator('text=LOW').or(page.locator('text=MODERATE')).or(page.locator('text=HIGH')).or(page.locator('text=SEVERE'))).toBeVisible();
  });

  test('Checklist - displays persistent checklist with progress', async ({ page }) => {
    // Setup household
    await page.click('button:has-text("Settings")');
    await page.waitForLoadState('networkidle');
    await page.fill('label:has-text("Latitude") + input', '11.0168');
    await page.fill('label:has-text("Longitude") + input', '76.9558');
    await page.fill('label:has-text("Household size") + input', '2');
    await page.click('button:has-text("Save profile context")');
    await expect(page.locator('text=Profile context updated successfully')).toBeVisible({ timeout: 10000 });
    
    // Generate plan
    await page.click('button:has-text("Personalized Plan")');
    await page.waitForLoadState('networkidle');
    await page.click('button:has-text("Generate Preparedness Plan")');
    await expect(page.locator('text=Do Now')).toBeVisible({ timeout: 25000 });
    
    // Go to checklist
    await page.click('button:has-text("My Checklist")');
    await page.waitForLoadState('networkidle');
    
    // Checklist loads
    await expect(page.locator('text=Emergency Preparedness Checklist')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Overall checklist completion')).toBeVisible();
    
    // Toggle first item
    const firstCheckbox = page.locator('input[type="checkbox"]').first();
    await firstCheckbox.click();
    
    // Progress updates
    await expect(page.locator('text=8.3%').or(page.locator('text=1/'))).toBeVisible({ timeout: 5000 });
  });

  test('Assistant - answers safety questions', async ({ page }) => {
    await page.click('button:has-text("Safety Assistant")');
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('text=Weather-Aware Safety Chat')).toBeVisible();
    
    // Type and submit question
    await page.fill('input[placeholder*="safety question"]', 'What should I do during a flood?');
    await page.click('button:has-text("Ask")');
    
    // Wait for response
    await expect(page.locator('.chat-bubble.assistant').last()).toBeVisible({ timeout: 20000 });
    
    // Verify response content
    const response = page.locator('.chat-bubble.assistant').last();
    const text = await response.textContent();
    expect(text.toLowerCase()).toContain('flood');
    
    // Sources displayed
    await expect(page.locator('text=Sources referenced')).toBeVisible();
  });

  test('Travel Advisory - evaluates route safety', async ({ page }) => {
    await page.click('button:has-text("Travel Advisory")');
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('text=Weather-Aware Travel Advisory')).toBeVisible();
    
    // Submit with defaults
    await page.click('button:has-text("Evaluate Route Safety")');
    
    // Wait for advisory
    await expect(page.locator('text=Advisory Risk:')).toBeVisible({ timeout: 20000 });
    
    // Check risk level - use the badge specifically
    await expect(page.locator('.badge').filter({ hasText: /LOW|MODERATE|HIGH|AVOID/ }).first()).toBeVisible();
    
    // Check recommendations
    await expect(page.locator('text=Safety Recommendations:')).toBeVisible();
    
    // Check limitations
    await expect(page.locator('text=Important travel notice')).toBeVisible();
    await expect(page.locator('text=Road-level flooding data is unavailable')).toBeVisible();
  });

  test('Language switching - changes UI language', async ({ page }) => {
    const langSelect = page.locator('select').first();
    await expect(langSelect).toBeVisible();
    
    await langSelect.selectOption('ta');
    await page.waitForTimeout(1000);
    
    await langSelect.selectOption('hi');
    await page.waitForTimeout(1000);
    
    await langSelect.selectOption('en');
  });

  test('Geolocation - detects user location', async ({ page }) => {
    await page.click('button:has-text("Settings")');
    await page.waitForLoadState('networkidle');
    
    await page.context().grantPermissions(['geolocation']);
    
    await page.evaluate(() => {
      navigator.geolocation.getCurrentPosition = (success) => {
        success({ coords: { latitude: 11.0168, longitude: 76.9558 } });
      };
    });
    
    await page.click('button:has-text("Use my coordinates")');
    await page.waitForTimeout(3000);
  });

  test('Dashboard - risk summary shows after plan generation', async ({ page }) => {
    // Setup and generate plan
    await page.click('button:has-text("Settings")');
    await page.waitForLoadState('networkidle');
    await page.fill('label:has-text("Latitude") + input', '11.0168');
    await page.fill('label:has-text("Longitude") + input', '76.9558');
    await page.fill('label:has-text("Household size") + input', '3');
    await page.click('button:has-text("Save profile context")');
    await expect(page.locator('text=Profile context updated successfully')).toBeVisible({ timeout: 10000 });
    
    await page.click('button:has-text("Personalized Plan")');
    await page.waitForLoadState('networkidle');
    await page.click('button:has-text("Generate Preparedness Plan")');
    await expect(page.locator('text=Do Now')).toBeVisible({ timeout: 25000 });
    
    // Back to dashboard
    await page.click('button:has-text("Dashboard")');
    await page.waitForLoadState('networkidle');
    
    // Risk summary visible
    await expect(page.locator('text=Active Risk level')).toBeVisible();
    await expect(page.locator('text=LOW').or(page.locator('text=MODERATE')).or(page.locator('text=HIGH')).or(page.locator('text=SEVERE'))).toBeVisible();
    await expect(page.locator('text=Do Now')).toBeVisible();
  });
});

test.describe('API Health Checks', () => {
  test('Health endpoint responds', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/health');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('Weather endpoint returns data', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/weather?latitude=11.0168&longitude=76.9558');
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.data_available).toBeTruthy();
  });

  test('Alerts endpoint responds', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/alerts?latitude=11.0168&longitude=76.9558');
    expect(response.ok()).toBeTruthy();
  });

  test('Preparedness plan endpoint works', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/preparedness/plan', {
      data: {
        location_lat: 11.0168,
        location_lng: 76.9558,
        location_name: 'Coimbatore',
        household_size: 3,
        has_children: true,
        has_elderly: false,
        has_pets: true,
        housing_type: 'apartment',
        has_vehicle: true,
        accessibility_needs: '',
        preferred_language: 'en'
      }
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.risk_summary).toBeDefined();
  });

  test('Assistant endpoint works', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/assistant/ask', {
      data: { question: 'What should I do during a flood?', household_id: null }
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.answer).toBeDefined();
  });

  test('Travel advisory endpoint works', async ({ request }) => {
    const response = await request.post('http://localhost:8000/api/travel/advisory', {
      data: {
        origin_lat: 11.0168,
        origin_lng: 76.9558,
        dest_lat: 13.0827,
        dest_lng: 80.2707,
        preferred_language: 'en'
      }
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.risk_level).toBeDefined();
  });
});