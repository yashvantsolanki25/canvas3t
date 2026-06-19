import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import GalleryGrid from "../GalleryGrid";

describe("GalleryGrid", () => {
  it("renders placeholder when empty", () => {
    render(<GalleryGrid paintings={[]} />);
    expect(screen.getByText(/No paintings yet/)).toBeInTheDocument();
  });
});

