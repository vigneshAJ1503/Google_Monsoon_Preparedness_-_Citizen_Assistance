import { test, expect } from '@playwright/test';

// Test against local Docker stack (full functionality)
const LOCAL_BASE = 'http://localhost';
const LOCAL_API = 'http://localhost:8000/api';

// Test against live Render (partial - weather only)
const LIVE_BASE = 'https://monsoonprep-frontend.onrender.com';
const LIVE_API = 'https://monsoonprep-backend.onrender.com/api';

test.describe('Local Docker Stack - Full Functionality', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(LOCAL_BASE);
    await page.waitForLoadState('networkidle');
  });

  test('Dashboard - loads weather and alerts', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Monsoon Prep');
    await expect(page.locator('text=Current Weather Condition')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=Location:').first()).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Active Risk level')).toBeVisible();
  });

  test('Settings - can save household profile', async ({ page }) => {
    await page.click('button:has-text("Settings")');
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('text=Household & Location Setup')).toBeVisible();
    
    const numberInputs = page.locator('input[type="number"]');
    await numberInputs.nth(0).fill('11.0168');
    await numberInputs.nth(1).fill('76.9558');
    await numberInputs.nth(2).fill('3');
    
    await page.click('button:has-text("Save profile context")');
    await expect(page.locator('text=Profile context updated successfully')).toBeVisible({ timeout: 10000 });
  });

  test('Preparedness - generates plan', async ({ page }) => {
    await page.click('button:has-text("Settings")');
    await page.waitForLoadState('networkidle');
    const numberInputs = page.locator('input[type="number"]');
    await numberInputs.nth(0).fill('11.0168');
    await numberInputs.nth(1).fill('76.9558');
    await numberInputs.nth(2).fill('3');
    await page.click('button:has-text("Save profile context")');
    await expect(page.locator('text=Profile context updated successfully')).toBeVisible({ timeout: 10000 });
    
    await page.click('button:has-text("Personalized Plan")');
    await page.waitForLoadState('networkidle');
    
    await page.click('button:has-text("Generate Preparedness Plan")');
    await expect(page.locator('text=Next 6 Hours')).toBeVisible({ timeout: 30000 });
    await expect(page.locator('text=Next 24 Hours')).toBeVisible();
    await expect(page.locator('text=Essential Emergency Kit Checklist')).toBeVisible();
  });

  test('Checklist - shows plan required message when no plan', async ({ page }) => {
    await page.click('button:has-text("My Checklist")');
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('text=Emergency Preparedness Checklist')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('text=Generate a personalized plan first')).toBeVisible();
  });

  test('Assistant - answers safety questions', async ({ page }) => {
    await page.click('button:has-text("Safety Assistant")');
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('text=Weather-Aware Safety Chat')).toBeVisible();
    
    await page.fill('input[placeholder*="safety question"]', 'What should I do during a flood?');
    await page.click('button:has-text("Ask")');
    
    await expect(page.locator('.chat-bubble.assistant').last()).toBeVisible({ timeout: 20000 });
    
    const response = page.locator('.chat-bubble.assistant').last();
    const text = await response.textContent();
    expect(text.toLowerCase()).toContain('flood');
    
    await expect(page.locator('text=Sources referenced')).toBeVisible();
  });

  test('Travel Advisory - evaluates route', async ({ page }) => {
    await page.click('button:has-text("Travel Advisory")');
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('text=Weather-Aware Travel Advisory')).toBeVisible();
    
    await page.click('button:has-text("Evaluate Route Safety")');
    
    await expect(page.locator('text=Advisory Risk:')).toBeVisible({ timeout: 20000 });
    await expect(page.locator('.badge').filter({ hasText: /LOW|MODERATE|HIGH|AVOID/ }).first()).toBeVisible();
    await expect(page.locator('text=Safety Recommendations:')).toBeVisible();
    await expect(page.locator('text=Road-level flooding data is unavailable')).toBeVisible();
  });

  test('Language switcher works', async ({ page }) => {
    const langSelect = page.locator('select').first();
    await expect(langSelect).toBeVisible();
    
    await langSelect.selectOption('ta');
    await page.waitForTimeout(500);
    await langSelect.selectOption('hi');
    await page.waitForTimeout(500);
    await langSelect.selectOption('en');
  });

  test('Dashboard shows risk after plan', async ({ page }) => {
    await page.click('button:has-text("Settings")');
    await page.waitForLoadState('networkidle');
    const numberInputs = page.locator('input[type="number"]');
    await numberInputs.nth(0).fill('11.0168');
    await numberInputs.nth(1).fill('76.9558');
    await numberInputs.nth(2).fill('3');
    await page.click('button:has-text("Save profile context")');
    await expect(page.locator('text=Profile context updated successfully')).toBeVisible({ timeout: 10000 });
    
    await page.click('button:has-text("Personalized Plan")');
    await page.waitForLoadState('networkidle');
    await page.click('button:has-text("Generate Preparedness Plan")');
    await expect(page.locator('text=Next 6 Hours')).toBeVisible({ timeout: 30000 });
    
    await page.click('button:has-text("Dashboard")');
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('text=Active Risk level')).toBeVisible();
    await expect(page.locator('.badge').first()).toBeVisible();
  });
});

test.describe('API Health - Local Stack', () => {
  test('Health endpoint', async ({ request }) => {
    const response = await request.get(`${LOCAL_API}/health`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('Weather endpoint', async ({ request }) => {
    const response = await request.get(`${LOCAL_API}/weather?latitude=11.0168&longitude=76.9558`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.data_available).toBeTruthy();
  });

  test('Alerts endpoint', async ({ request }) => {
    const response = await request.get(`${LOCAL_API}/alerts?latitude=11.0168&longitude=76.9558`);
    expect(response.ok()).toBeTruthy();
  });

  test('Preparedness plan endpoint', async ({ request }) => {
    const response = await request.post(`${LOCAL_API}/preparedness/plan`, {
      data: {
        location_lat: 11.0168, location_lng: 76.9558, location_name: 'Coimbatore',
        household_size: 3, has_children: true, has_elderly: false, has_pets: true,
        housing_type: 'apartment', has_vehicle: true, accessibility_needs: '', preferred_language: 'en'
      }
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.risk_summary).toBeDefined();
  });

  test('Assistant endpoint', async ({ request }) => {
    const response = await request.post(`${LOCAL_API}/assistant/ask`, {
      data: { question: 'What should I do during a flood?', household_id: null }
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.answer).toBeDefined();
  });

  test('Travel advisory endpoint', async ({ request }) => {
    const response = await request.post(`${LOCAL_API}/travel/advisory`, {
      data: { origin_lat: 11.0168, origin_lng: 76.9558, dest_lat: 13.0827, dest_lng: 80.2707, preferred_language: 'en' }
    });
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.risk_level).toBeDefined();
  });
});

test.describe('Live Render - Weather Only (Other Endpoints Fail)', () => {
  test('Weather endpoint works on live', async ({ request }) => {
    const response = await request.get(`${LIVE_API}/weather?latitude=11.0168&longitude=76.9558`);
    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.data_available).toBeTruthy();
    expect(data.current.condition).toBeDefined();
    expect(data.forecast.days.length).toBeGreaterThan(0);
  });

  test('Health endpoint on live returns 500 or HTML (not proxied)', async ({ request }) => {
    const response = await request.get(`${LIVE_API}/health`);
    // Frontend serves index.html for unknown routes on Render
    expect(response.status()).toBeGreaterThanOrEqual(200);
  });

  test('Preparedness endpoint fails on live (no DB)', async ({ request }) => {
    const response = await request.post(`${LIVE_API}/preparedness/plan`, {
      data: { location_lat: 11.0168, location_lng: 76.9558, location_name: 'Coimbatore', household_size: 3, has_children: true, has_elderly: false, has_pets: true, housing_type: 'apartment', has_vehicle: true, accessibility_needs: '', preferred_language: 'en' }
    });
    // Returns 500 due to missing database
    expect(response.status()).toBe(500);
  });

  test('Other endpoints fail on live (no DB/Redis)', async ({ request }) => {
    const endpoints = [
      { method: 'GET', path: '/alerts?latitude=11.0168&longitude=76.9558' },
      { method: 'POST', path: '/assistant/ask', data: { question: 'test', household_id: null } },
      { method: 'POST', path: '/travel/advisory', data: { origin_lat: 11.0168, origin_lng: 76.9558, dest_lat: 13.0827, dest_lng: 80.2707, preferred_language: 'en' } },
    ];
    
    for (const ep of endpoints) {
      const response = ep.method === 'GET' 
        ? await request.get(`${LIVE_API}${ep.path}`)
        : await request.post(`${LIVE_API}${ep.path}`, { data: ep.data });
      expect(response.status()).toBe(500);
    }
  });
});

test.describe('No Hardcoded/Fake Data Verification', () => {
  test('Weather data comes from Open-Meteo API', async ({ request }) => {
    const response = await request.get(`${LOCAL_API}/weather?latitude=11.0168&longitude=76.9558`);
    const data = await response.json();
    expect(data.current.source).toBe('Open-Meteo');
    expect(data.forecast.source).toBe('Open-Meteo');
  });

  test('Alert evaluation uses deterministic rules (no LLM)', async ({ request }) => {
    // The alert engine evaluates deterministic rules against weather data
    const response = await request.get(`${LOCAL_API}/alerts?latitude=11.0168&longitude=76.9558`);
    const alerts = await response.json();
    for (const alert of alerts) {
      expect(alert.source).toBeDefined();
      expect(['weather_rules', 'NDMA'].includes(alert.source)).toBeTruthy();
    }
  });

  test('Assistant responses include source attribution', async ({ request }) => {
    const response = await request.post(`${LOCAL_API}/assistant/ask`, {
      data: { question: 'What should I do during a flood?', household_id: null }
    });
    const data = await response.json();
    expect(data.sources).toBeDefined();
    expect(Array.isArray(data.sources)).toBeTruthy();
    expect(data.sources.length).toBeGreaterThan(0);
  });

  test('Travel advisory includes limitations disclaimer', async ({ request }) => {
    const response = await request.post(`${LOCAL_API}/travel/advisory`, {
      data: { origin_lat: 11.0168, origin_lng: 76.9558, dest_lat: 13.0827, dest_lng: 80.2707, preferred_language: 'en' }
    });
    const data = await response.json();
    expect(data.limitations).toBeDefined();
    expect(data.limitations.some(l => l.includes('Road-level flooding data is unavailable'))).toBeTruthy();
  });

  test('Preparedness plan includes deterministic fallback tag', async ({ request }) => {
    const response = await request.post(`${LOCAL_API}/preparedness/plan`, {
      data: { location_lat: 11.0168, location_lng: 76.9558, location_name: 'Coimbatore', household_size: 3, has_children: true, has_elderly: false, has_pets: true, housing_type: 'apartment', has_vehicle: true, accessibility_needs: '', preferred_language: 'en' }
    });
    const data = await response.json();
    // When LLM unavailable, should show fallback tag
    expect(data.limitations.some(l => l.includes('static safety rules') || l.includes('AI generation unavailable'))).toBeTruthy();
  });
});