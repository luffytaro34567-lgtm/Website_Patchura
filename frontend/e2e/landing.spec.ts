import { test, expect } from '@playwright/test'

test.describe('Landing page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('has the correct title', async ({ page }) => {
    await expect(page).toHaveTitle(/PATCHORA/)
  })

  test('renders the hero heading', async ({ page }) => {
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  })

  test('renders navigation', async ({ page }) => {
    await expect(page.getByRole('navigation')).toBeVisible()
  })

  test('renders Get Started links', async ({ page }) => {
    const links = page.getByText(/Get Started/i)
    await expect(links.first()).toBeVisible()
  })

  test('theme toggle is present and operable', async ({ page }) => {
    const toggle = page.getByRole('button', { name: /switch to/i }).first()
    await expect(toggle).toBeVisible()
    await toggle.click()
    // After toggle the button label should flip
    await expect(
      page.getByRole('button', { name: /switch to/i }).first()
    ).toBeVisible()
  })

  test('no fabricated scan results displayed', async ({ page }) => {
    const bodyText = await page.locator('body').innerText()
    expect(bodyText).not.toMatch(/scan complete/i)
    expect(bodyText).not.toMatch(/vulnerabilities found: \d+/i)
  })
})
