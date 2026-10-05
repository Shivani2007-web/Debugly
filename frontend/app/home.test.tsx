// @vitest-environment jsdom
import { describe, it, expect, afterEach } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import Home from "./page";

afterEach(cleanup);

describe("Homepage", () => {
  it("renders the product hero, not developer diagnostics", () => {
    render(<Home />);
    expect(screen.getByText(/Understand it\./i)).toBeInTheDocument();
    // The tagline appears in both the hero and the footer.
    expect(
      screen.getAllByText(/finds the misconception behind the mistake/i).length,
    ).toBeGreaterThanOrEqual(1);
    // The old connection-chain diagnostics must NOT be on the homepage.
    expect(screen.queryByText(/connection chain/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/project setup/i)).not.toBeInTheDocument();
  });

  it("has primary and secondary CTAs", () => {
    render(<Home />);
    const starts = screen.getAllByRole("link", { name: /start learning/i });
    expect(starts.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("link", { name: /explore dashboard/i })).toBeInTheDocument();
  });

  it("explains how Debugly works and the differentiator", () => {
    render(<Home />);
    expect(screen.getByText(/How Debugly works/i)).toBeInTheDocument();
    expect(screen.getByText(/learning path/i)).toBeInTheDocument();
    expect(screen.getByText(/Ready to understand your bugs/i)).toBeInTheDocument();
  });
});
