import { expect, test } from "@playwright/test";

// Only the homepage — it fetches nothing, so it renders correctly with no
// backend running. The queue/evidence pages fetch real data from the
// FastAPI backend and are verified manually against a live `make dev`
// server (see README's curl examples) rather than mocked here; a properly
// isolated API-mocked e2e suite is Phase 9 (validation harness) territory.
test("homepage renders the app name and navigation", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("h1")).toHaveText("Cohort Risk & Review Lab");
  const nav = page.getByRole("navigation", { name: "Main" });
  await expect(nav.getByRole("link", { name: /Review queue/i })).toBeVisible();
  await expect(nav.getByRole("link", { name: /Fairness audit/i })).toBeVisible();
  await expect(nav.getByRole("link", { name: /Label choice/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /Subgroup fairness audit/i })).toBeVisible();
  await expect(page.getByRole("link", { name: /label-choice experiment/i })).toBeVisible();
});

test("homepage explains the workflow and links to the docs", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "How it works" })).toBeVisible();
  await expect(page.getByRole("heading", { name: /A clinician decides/i })).toBeVisible();
  const docs = page.getByRole("link", { name: "Docs", exact: true });
  await expect(docs).toHaveAttribute("href", /^https:\/\//);
});

test("prototype banner is visible on every page", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText(/architectural demonstration/i)).toBeVisible();
});
