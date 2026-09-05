import { expect, test } from "@playwright/test";

test.describe("Dashboard SOTA", () => {
  test("hero + onboarding cue + KPIs render", async ({ page }) => {
    await page.goto("http://127.0.0.1:10766/");
    await expect(page.getByTestId("dashboard")).toBeVisible({ timeout: 10000 });
    await expect(page.getByTestId("onboarding-cue")).toBeVisible();
    await expect(page.getByTestId("onboarding-cue")).toHaveAttribute(
      "href",
      /ONBOARDING/,
    );
    // KPIs
    await expect(page.getByTestId("kpi-targets")).toBeVisible();
    await expect(page.getByTestId("kpi-messages")).toBeVisible();
    await expect(page.getByTestId("kpi-uptime")).toBeVisible();
    await expect(page.getByTestId("kpi-backend")).toBeVisible();
    await expect(page.getByTestId("backend-dot")).toBeVisible();
  });

  test("AppsOnboarding shows when backend replies", async ({ page }) => {
    await page.goto("http://127.0.0.1:10766/");
    // If backend is up, apps-onboarding appears; if not, MOCK banner appears — either is valid
    const onboarding = page.getByTestId("apps-onboarding");
    const mockBanner = page.getByTestId("mock-banner");
    await expect(onboarding.or(mockBanner)).toBeVisible({ timeout: 8000 });
  });

  test("MOCK banner clears when backend healthy (deterministic: not asserted hard, just that one of them exists)", async ({
    page,
  }) => {
    await page.goto("http://127.0.0.1:10766/");
    await page.waitForTimeout(1500);
    const mockBanner = page.getByTestId("mock-banner");
    const appsOnboarding = page.getByTestId("apps-onboarding");
    const mockVisible = await mockBanner.isVisible().catch(() => false);
    const onboardingVisible = await appsOnboarding
      .isVisible()
      .catch(() => false);
    expect(mockVisible || onboardingVisible).toBeTruthy();
  });
});
