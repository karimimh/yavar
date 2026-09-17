import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { expect, test, vi } from "vitest";
import Home from "./page";

vi.mock("@/lib/api", () => ({
  api: vi.fn(async () => ({
    disclaimer_fa: "سندباکس",
    capabilities: [
      {
        slug: "public_research",
        name_fa: "پژوهش",
        description_fa: "مقایسه آزمایشی",
        status_label_fa: "محدود — آزمایشی",
        sandbox: true,
        required_user_steps_fa: "انتخاب شما",
      },
    ],
  })),
}));

test("landing states supported actions and sandbox honesty", async () => {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <Home />
    </QueryClientProvider>,
  );
  expect(await screen.findByRole("heading", { name: "یاور" })).toBeInTheDocument();
  expect(screen.getByText(/آزمایشی/)).toBeInTheDocument();
  expect(screen.getByText("اقدامات پشتیبانی‌شده")).toBeInTheDocument();
  expect(await screen.findByText("پژوهش")).toBeInTheDocument();
});
