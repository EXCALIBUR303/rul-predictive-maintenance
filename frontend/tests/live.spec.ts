import { test, expect } from "@playwright/test";
test("API-backed what-if, error and retry", async ({ page }) => {
  test.skip(
    !process.env.LIVE_UI_URL,
    "Run with an API-enabled UI and LIVE_UI_URL",
  );
  await page.goto(process.env.LIVE_UI_URL!);
  await expect(page.getByText("API WHAT-IF", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Explore an engine" }).click();
  const request = page.waitForRequest(
    (r) => r.url().endsWith("/api/predict") && r.method() === "POST",
  );
  await page.getByRole("button", { name: "Run what-if" }).click();
  const sent = await request;
  expect(sent.postDataJSON().rows).toHaveLength(30);
  await expect(page.getByRole("status")).toContainText("xgboost:");
  await page.getByRole("slider", { name: "Sensor 2 adjustment" }).fill("5");
  await expect(page.getByRole("status")).toContainText("Inputs changed");
  await page.route("**/api/predict", (r) =>
    r.fulfill({
      status: 400,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Artifact unavailable" }),
    }),
  );
  await page.getByRole("button", { name: "Run what-if" }).click();
  await expect(
    page.getByRole("alert").filter({ hasText: "Artifact unavailable" }),
  ).toHaveCount(1);
  await page.unroute("**/api/predict");
  await page.getByRole("button", { name: "Retry prediction" }).click();
  await expect(page.getByRole("status")).toContainText("xgboost:");
  await expect(
    page.getByRole("alert").filter({ hasText: "Artifact unavailable" }),
  ).toHaveCount(0);
});
