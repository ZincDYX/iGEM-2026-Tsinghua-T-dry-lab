import { afterEach, expect, it, vi } from "vitest";
import {
  defaultLayout,
  layoutBounds,
  loadLayout,
  persistLayout,
} from "./layout";
afterEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
});
it("constrains panes to a real viewport while keeping central space and saved preferences", () => {
  const input = { ...defaultLayout(), left: 2000, right: 2000, bottom: 2000 };
  const wide = layoutBounds(input, 1280, 850, 100, true);
  expect(wide.layout.left + wide.layout.right + 14).toBeLessThanOrEqual(980);
  expect(wide.layout.bottom).toBeLessThanOrEqual(850 - 34 - 100 - 24 - 180 - 7);
  const narrow = layoutBounds(input, 800, 600, 140, false);
  expect(narrow.narrow).toBe(true);
  expect(narrow.layout.left + 14).toBeLessThanOrEqual(500);
  expect(input.left).toBe(2000); // viewport clamp does not overwrite saved intent
});
it("invalid or unavailable storage cannot crash or introduce nonfinite dimensions", () => {
  localStorage.setItem(
    "fusionlab.layout",
    '{"left":1e999,"right":310,"bottom":165}',
  );
  expect(loadLayout()).toEqual(defaultLayout());
  vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
    throw new Error("fixture denial");
  });
  expect(loadLayout()).toEqual(defaultLayout());
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new Error("fixture denial");
  });
  expect(() => persistLayout(defaultLayout())).not.toThrow();
});
