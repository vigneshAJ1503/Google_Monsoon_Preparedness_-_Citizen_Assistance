# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests/e2e.spec.js >> Monsoon Prep App - Core E2E Tests >> Checklist - loads and tracks progress
- Location: tests/e2e.spec.js:70:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('input[placeholder="11.0168"]')

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - generic [ref=e5]:
      - img [ref=e6]
      - heading "Monsoon Prep & Assistance" [level=1] [ref=e8]
    - navigation "Main Navigation" [ref=e9]:
      - button "Dashboard" [ref=e10] [cursor=pointer]:
        - img [ref=e11]
        - text: Dashboard
      - button "Personalized Plan" [ref=e14] [cursor=pointer]:
        - img [ref=e15]
        - text: Personalized Plan
      - button "My Checklist" [ref=e17] [cursor=pointer]:
        - img [ref=e18]
        - text: My Checklist
      - button "Safety Assistant" [ref=e21] [cursor=pointer]:
        - img [ref=e22]
        - text: Safety Assistant
      - button "Travel Advisory" [ref=e24] [cursor=pointer]:
        - img [ref=e25]
        - text: Travel Advisory
      - button "Settings" [active] [ref=e27] [cursor=pointer]:
        - img [ref=e28]
        - text: Settings
    - generic [ref=e31]:
      - img [ref=e32]
      - combobox [ref=e36]:
        - option "English" [selected]
        - option "தமிழ் (Tamil)"
        - option "हिन्दी (Hindi)"
  - main [ref=e37]:
    - generic [ref=e38]:
      - heading "Household & Location Setup" [level=2] [ref=e39]
      - generic [ref=e40]:
        - generic [ref=e41]:
          - generic [ref=e42]:
            - generic [ref=e43]: Latitude
            - spinbutton [ref=e44]: "11.0168"
          - generic [ref=e45]:
            - generic [ref=e46]: Longitude
            - spinbutton [ref=e47]: "76.9558"
        - button "Use my coordinates" [ref=e49] [cursor=pointer]:
          - img [ref=e50]
          - text: Use my coordinates
        - generic [ref=e53]:
          - generic [ref=e54]:
            - generic [ref=e55]: Household size
            - spinbutton [ref=e56]: "3"
          - generic [ref=e57]:
            - generic [ref=e58]: Housing type
            - combobox [ref=e59]:
              - option "Apartment" [selected]
              - option "Independent House"
              - option "Ground Floor Apartment/House"
              - option "Kutcha House (Mud/thatch)"
              - option "Low-lying slum structure"
              - option "Temporary Shelter/Tent"
        - generic [ref=e60]:
          - generic [ref=e61] [cursor=pointer]:
            - checkbox "Children present" [ref=e62]
            - generic [ref=e63]: Children present
          - generic [ref=e64] [cursor=pointer]:
            - checkbox "Elderly present" [ref=e65]
            - generic [ref=e66]: Elderly present
          - generic [ref=e67] [cursor=pointer]:
            - checkbox "Pets present" [ref=e68]
            - generic [ref=e69]: Pets present
          - generic [ref=e70] [cursor=pointer]:
            - checkbox "Vehicle present" [ref=e71]
            - generic [ref=e72]: Vehicle present
        - generic [ref=e73]:
          - generic [ref=e74]: Accessibility needs details
          - textbox [ref=e75]
        - button "Save profile context" [ref=e76] [cursor=pointer]
```

# Test source

```ts
  1   | import { test, expect } from '@playwright/test';
  2   | 
  3   | const BASE_URL = 'http://localhost';
  4   | 
  5   | test.describe('Monsoon Prep App - Core E2E Tests', () => {
  6   |   test.beforeEach(async ({ page }) => {
  7   |     await page.goto(BASE_URL);
  8   |     await page.waitForLoadState('networkidle');
  9   |   });
  10  | 
  11  |   test('Dashboard - loads weather and alerts', async ({ page }) => {
  12  |     await expect(page.locator('h1')).toContainText('Monsoon Prep');
  13  |     await expect(page.locator('text=Current Weather Condition')).toBeVisible({ timeout: 15000 });
  14  |     await expect(page.locator('text=Location:').first()).toBeVisible({ timeout: 10000 });
  15  |     await expect(page.locator('text=No active verified alerts reported').or(page.locator('text=Verified Alert Active'))).toBeVisible();
  16  |   });
  17  | 
  18  |   test('Navigation tabs work', async ({ page }) => {
  19  |     const tabs = ['Dashboard', 'Personalized Plan', 'My Checklist', 'Safety Assistant', 'Travel Advisory', 'Settings'];
  20  |     for (const tab of tabs) {
  21  |       await page.click(`button:has-text("${tab}")`);
  22  |       await page.waitForTimeout(300);
  23  |     }
  24  |   });
  25  | 
  26  |   test('Settings - can save household profile', async ({ page }) => {
  27  |     await page.click('button:has-text("Settings")');
  28  |     await page.waitForLoadState('networkidle');
  29  |     
  30  |     await expect(page.locator('text=Household & Location Setup')).toBeVisible();
  31  |     
  32  |     // Fill lat/lng
  33  |     await page.fill('input[placeholder="11.0168"]', '11.0168');
  34  |     await page.fill('input[placeholder="76.9558"]', '76.9558');
  35  |     
  36  |     // Fill household size
  37  |     await page.fill('input[type="number"]', '3');
  38  |     
  39  |     // Save
  40  |     await page.click('button:has-text("Save profile context")');
  41  |     await expect(page.locator('text=Profile context updated successfully')).toBeVisible({ timeout: 10000 });
  42  |   });
  43  | 
  44  |   test('Preparedness - generates plan', async ({ page }) => {
  45  |     // Setup household
  46  |     await page.click('button:has-text("Settings")');
  47  |     await page.waitForLoadState('networkidle');
  48  |     await page.fill('input[placeholder="11.0168"]', '11.0168');
  49  |     await page.fill('input[placeholder="76.9558"]', '76.9558');
  50  |     await page.fill('input[type="number"]', '3');
  51  |     await page.click('button:has-text("Save profile context")');
  52  |     await expect(page.locator('text=Profile context updated successfully')).toBeVisible({ timeout: 10000 });
  53  |     
  54  |     // Go to preparedness
  55  |     await page.click('button:has-text("Personalized Plan")');
  56  |     await page.waitForLoadState('networkidle');
  57  |     
  58  |     // Generate plan
  59  |     await page.click('button:has-text("Generate Preparedness Plan")');
  60  |     
  61  |     // Wait for plan - use more flexible selectors
  62  |     await expect(page.locator('text=Do Now').or(page.locator('text=உடனடியாக செய்ய வேண்டியவை')).or(page.locator('text=अभी करें'))).toBeVisible({ timeout: 30000 });
  63  |     await expect(page.locator('text=Next 6 Hours').or(page.locator('text=அगले 6 घंटे'))).toBeVisible();
  64  |     await expect(page.locator('text=Essential Emergency Kit Checklist')).toBeVisible();
  65  |     
  66  |     // Risk level should show
  67  |     await expect(page.locator('text=LOW').or(page.locator('text=MODERATE')).or(page.locator('text=HIGH')).or(page.locator('text=SEVERE'))).toBeVisible();
  68  |   });
  69  | 
  70  |   test('Checklist - loads and tracks progress', async ({ page }) => {
  71  |     // Setup
  72  |     await page.click('button:has-text("Settings")');
  73  |     await page.waitForLoadState('networkidle');
> 74  |     await page.fill('input[placeholder="11.0168"]', '11.0168');
      |                ^ Error: page.fill: Test timeout of 30000ms exceeded.
  75  |     await page.fill('input[placeholder="76.9558"]', '76.9558');
  76  |     await page.fill('input[type="number"]', '2');
  77  |     await page.click('button:has-text("Save profile context")');
  78  |     await expect(page.locator('text=Profile context updated successfully')).toBeVisible({ timeout: 10000 });
  79  |     
  80  |     // Generate plan
  81  |     await page.click('button:has-text("Personalized Plan")');
  82  |     await page.waitForLoadState('networkidle');
  83  |     await page.click('button:has-text("Generate Preparedness Plan")');
  84  |     await expect(page.locator('text=Do Now').or(page.locator('text=உடனடியாக செய்ய வேண்டியவை')).or(page.locator('text=अभी करें'))).toBeVisible({ timeout: 30000 });
  85  |     
  86  |     // Go to checklist
  87  |     await page.click('button:has-text("My Checklist")');
  88  |     await page.waitForLoadState('networkidle');
  89  |     
  90  |     await expect(page.locator('text=Emergency Preparedness Checklist')).toBeVisible({ timeout: 10000 });
  91  |     await expect(page.locator('text=Overall checklist completion')).toBeVisible();
  92  |     
  93  |     // Toggle first item
  94  |     const firstCheckbox = page.locator('input[type="checkbox"]').first();
  95  |     await firstCheckbox.click();
  96  |     await expect(page.locator('text=8.3%').or(page.locator('text=1/'))).toBeVisible({ timeout: 5000 });
  97  |   });
  98  | 
  99  |   test('Assistant - answers safety questions', async ({ page }) => {
  100 |     await page.click('button:has-text("Safety Assistant")');
  101 |     await page.waitForLoadState('networkidle');
  102 |     
  103 |     await expect(page.locator('text=Weather-Aware Safety Chat')).toBeVisible();
  104 |     
  105 |     await page.fill('input[placeholder*="safety question"]', 'What should I do during a flood?');
  106 |     await page.click('button:has-text("Ask")');
  107 |     
  108 |     await expect(page.locator('.chat-bubble.assistant').last()).toBeVisible({ timeout: 20000 });
  109 |     
  110 |     const response = page.locator('.chat-bubble.assistant').last();
  111 |     const text = await response.textContent();
  112 |     expect(text.toLowerCase()).toContain('flood');
  113 |     
  114 |     await expect(page.locator('text=Sources referenced')).toBeVisible();
  115 |   });
  116 | 
  117 |   test('Travel Advisory - evaluates route', async ({ page }) => {
  118 |     await page.click('button:has-text("Travel Advisory")');
  119 |     await page.waitForLoadState('networkidle');
  120 |     
  121 |     await expect(page.locator('text=Weather-Aware Travel Advisory')).toBeVisible();
  122 |     
  123 |     await page.click('button:has-text("Evaluate Route Safety")');
  124 |     
  125 |     await expect(page.locator('text=Advisory Risk:')).toBeVisible({ timeout: 20000 });
  126 |     await expect(page.locator('text=LOW').or(page.locator('text=MODERATE')).or(page.locator('text=HIGH')).or(page.locator('text=AVOID'))).toBeVisible();
  127 |     await expect(page.locator('text=Safety Recommendations:')).toBeVisible();
  128 |     await expect(page.locator('text=Road-level flooding data is unavailable')).toBeVisible();
  129 |   });
  130 | 
  131 |   test('Language switcher works', async ({ page }) => {
  132 |     const langSelect = page.locator('select').first();
  133 |     await expect(langSelect).toBeVisible();
  134 |     
  135 |     await langSelect.selectOption('ta');
  136 |     await page.waitForTimeout(500);
  137 |     await langSelect.selectOption('hi');
  138 |     await page.waitForTimeout(500);
  139 |     await langSelect.selectOption('en');
  140 |   });
  141 | 
  142 |   test('Geolocation button works', async ({ page }) => {
  143 |     await page.click('button:has-text("Settings")');
  144 |     await page.waitForLoadState('networkidle');
  145 |     
  146 |     await page.context().grantPermissions(['geolocation']);
  147 |     
  148 |     await page.evaluate(() => {
  149 |       navigator.geolocation.getCurrentPosition = (success) => {
  150 |         success({ coords: { latitude: 11.0168, longitude: 76.9558 } });
  151 |       };
  152 |     });
  153 |     
  154 |     await page.click('button:has-text("Use my coordinates")');
  155 |     await page.waitForTimeout(2000);
  156 |   });
  157 | 
  158 |   test('Dashboard shows risk after plan', async ({ page }) => {
  159 |     // Setup + generate plan
  160 |     await page.click('button:has-text("Settings")');
  161 |     await page.waitForLoadState('networkidle');
  162 |     await page.fill('input[placeholder="11.0168"]', '11.0168');
  163 |     await page.fill('input[placeholder="76.9558"]', '76.9558');
  164 |     await page.fill('input[type="number"]', '3');
  165 |     await page.click('button:has-text("Save profile context")');
  166 |     await expect(page.locator('text=Profile context updated successfully')).toBeVisible({ timeout: 10000 });
  167 |     
  168 |     await page.click('button:has-text("Personalized Plan")');
  169 |     await page.waitForLoadState('networkidle');
  170 |     await page.click('button:has-text("Generate Preparedness Plan")');
  171 |     await expect(page.locator('text=Do Now').or(page.locator('text=உடனடியாக செய்ய வேண்டியவை')).or(page.locator('text=अभी करें'))).toBeVisible({ timeout: 30000 });
  172 |     
  173 |     // Back to dashboard
  174 |     await page.click('button:has-text("Dashboard")');
```