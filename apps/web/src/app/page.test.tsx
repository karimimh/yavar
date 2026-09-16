import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import Home from "./page";

test("renders the development placeholder", () => {
  render(<Home />);
  expect(screen.getByRole("heading", { name: "Yavar" })).toBeInTheDocument();
  expect(
    screen.getByText("Development environment is running."),
  ).toBeInTheDocument();
});
