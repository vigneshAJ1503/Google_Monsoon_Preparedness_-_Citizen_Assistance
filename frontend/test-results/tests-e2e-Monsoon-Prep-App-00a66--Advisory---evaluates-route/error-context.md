# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests/e2e.spec.js >> Monsoon Prep App - Core E2E Tests >> Travel Advisory - evaluates route
- Location: tests/e2e.spec.js:117:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=LOW').or(locator('text=MODERATE')).or(locator('text=HIGH')).or(locator('text=AVOID'))
Expected: visible
Error: strict mode violation: locator('text=LOW').or(locator('text=MODERATE')).or(locator('text=HIGH')).or(locator('text=AVOID')) resolved to 3 elements:
    1) <span class="badge low">LOW</span> aka getByText('LOW', { exact: true })
    2) <p>Road-level flooding data is unavailable, so I can…</p> aka getByText('Road-level flooding data is')
    3) <li>Avoid low-lying routes and underpasses prone to f…</li> aka getByText('Avoid low-lying routes and')

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('text=LOW').or(locator('text=MODERATE')).or(locator('text=HIGH')).or(locator('text=AVOID'))

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
      - button "Settings" [ref=e27] [cursor=pointer]:
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
      - generic [ref=e39]:
        - heading "Weather-Aware Travel Advisory" [level=2] [ref=e40]
        - generic [ref=e41]:
          - generic [ref=e42]:
            - generic [ref=e43]:
              - generic [ref=e44]: Origin Address / City
              - textbox "Coimbatore" [ref=e45]
              - generic [ref=e46]: "Default coords: 11.0168, 76.9558"
            - generic [ref=e47]:
              - generic [ref=e48]: Destination Address / City
              - textbox "Chennai" [ref=e49]
              - generic [ref=e50]: "Default coords: 13.0827, 80.2707"
          - button "Evaluate Route Safety" [active] [ref=e51] [cursor=pointer]
      - generic [ref=e52]:
        - generic [ref=e53]:
          - heading "Advisory Risk:" [level=3] [ref=e54]
          - generic [ref=e55]: LOW
        - generic [ref=e56]:
          - generic [ref=e57]:
            - heading "Origin Weather (North Coimbatore Flyover, Gandhipuram, Ward 51, Central Zone, Coimbatore, Coimbatore North, Coimbatore, Tamil Nadu, 641001, India)" [level=4] [ref=e58]
            - paragraph [ref=e59]: "Condition: drizzle, Rain: 0.1mm"
          - generic [ref=e60]:
            - heading "Destination Weather (Raja Muthiah Road, CMWSSB Division 58, Ward 58, Zone 5 Royapuram, Chennai Corporation, Chennai, Tamil Nadu, 600001, India)" [level=4] [ref=e61]
            - paragraph [ref=e62]: "Condition: cloudy, Forecast: 0.7mm"
        - generic [ref=e63]:
          - img [ref=e64]
          - generic [ref=e66]:
            - heading "Important travel notice" [level=4] [ref=e67]
            - paragraph [ref=e68]: Road-level flooding data is unavailable, so I cannot verify that this route is clear. Always avoid crossing waterlogged subways or underpasses.
        - generic [ref=e69]:
          - heading "Safety Recommendations:" [level=4] [ref=e70]
          - list [ref=e71]:
            - listitem [ref=e72]: Check local media or traffic updates before starting.
            - listitem [ref=e73]: Ensure vehicle tires and wipers are fully functional.
            - listitem [ref=e74]: Avoid low-lying routes and underpasses prone to flooding.
```

# Test source

```ts
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
  74  |     await page.fill('input[placeholder="11.0168"]', '11.0168');
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
> 126 |     await expect(page.locator('text=LOW').or(page.locator('text=MODERATE')).or(page.locator('text=HIGH')).or(page.locator('text=AVOID'))).toBeVisible();
      |                                                                                                                                           ^ Error: expect(locator).toBeVisible() failed
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
  175 |     await page.waitForLoadState('networkidle');
  176 |     
  177 |     await expect(page.locator('text=Active Risk level')).toBeVisible();
  178 |     await expect(page.locator('text=LOW').or(page.locator('text=MODERATE')).or(page.locator('text=HIGH')).or(page.locator('text=SEVERE'))).toBeVisible();
  179 |     await expect(page.locator('text=Do Now').or(page.locator('text=உடனடியாக செய்ய வேண்டியவை')).or(page.locator('text=अभी करें'))).toBeVisible();
  180 |   });
  181 | });
  182 | 
  183 | test.describe('API Health Checks', () => {
  184 |   test('Health endpoint', async ({ request }) => {
  185 |     const response = await request.get('http://localhost:8000/api/health');
  186 |     expect(response.ok()).toBeTruthy();
  187 |     const data = await response.json();
  188 |     expect(data.status).toBe('healthy');
  189 |   });
  190 | 
  191 |   test('Weather endpoint', async ({ request }) => {
  192 |     const response = await request.get('http://localhost:8000/api/weather?latitude=11.0168&longitude=76.9558');
  193 |     expect(response.ok()).toBeTruthy();
  194 |     const data = await response.json();
  195 |     expect(data.data_available).toBeTruthy();
  196 |   });
  197 | 
  198 |   test('Alerts endpoint', async ({ request }) => {
  199 |     const response = await request.get('http://localhost:8000/api/alerts?latitude=11.0168&longitude=76.9558');
  200 |     expect(response.ok()).toBeTruthy();
  201 |   });
  202 | 
  203 |   test('Preparedness plan endpoint', async ({ request }) => {
  204 |     const response = await request.post('http://localhost:8000/api/preparedness/plan', {
  205 |       data: {
  206 |         location_lat: 11.0168, location_lng: 76.9558, location_name: 'Coimbatore',
  207 |         household_size: 3, has_children: true, has_elderly: false, has_pets: true,
  208 |         housing_type: 'apartment', has_vehicle: true, accessibility_needs: '', preferred_language: 'en'
  209 |       }
  210 |     });
  211 |     expect(response.ok()).toBeTruthy();
  212 |     const data = await response.json();
  213 |     expect(data.risk_summary).toBeDefined();
  214 |   });
  215 | 
  216 |   test('Assistant endpoint', async ({ request }) => {
  217 |     const response = await request.post('http://localhost:8000/api/assistant/ask', {
  218 |       data: { question: 'What should I do during a flood?', household_id: null }
  219 |     });
  220 |     expect(response.ok()).toBeTruthy();
  221 |     const data = await response.json();
  222 |     expect(data.answer).toBeDefined();
  223 |   });
  224 | 
  225 |   test('Travel advisory endpoint', async ({ request }) => {
  226 |     const response = await request.post('http://localhost:8000/api/travel/advisory', {
```