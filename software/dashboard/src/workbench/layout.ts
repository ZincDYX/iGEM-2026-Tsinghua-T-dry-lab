export interface Layout {
  right: number;
  bottom: number;
  density: "compact" | "comfortable";
  theme: "light" | "dark";
}
export type Dimension = "right" | "bottom";
export const defaultLayout = (): Layout => ({
  right: 310,
  bottom: 165,
  density: "compact",
  theme: "light",
});
export function loadLayout(): Layout {
  try {
    const value = JSON.parse(
      localStorage.getItem("fusionlab.layout") ?? "null",
    );
    if (
      value &&
      [value.right, value.bottom].every(
        (item) =>
          typeof item === "number" &&
          Number.isFinite(item) &&
          item >= 60 &&
          item <= 2000,
      )
    )
      return {
        ...defaultLayout(),
        right: value.right,
        bottom: value.bottom,
        density: value.density === "comfortable" ? "comfortable" : "compact",
        theme: value.theme === "dark" ? "dark" : "light",
      };
  } catch {
    /* Local storage is optional view state. */
  }
  return defaultLayout();
}
export function persistLayout(value: Layout) {
  try {
    localStorage.setItem("fusionlab.layout", JSON.stringify(value));
  } catch {
    /* Storage denial must not interrupt the workbench. */
  }
}
export function layoutBounds(
  value: Layout,
  width: number,
  height: number,
  toolbar: number,
  inspector: boolean,
) {
  const narrow = width < 1100,
    center = Math.min(300, Math.max(160, width - 140 - 14));
  const rightMin = Math.min(260, Math.max(160, width - 32));
  const clamp = (n: number, min: number, max: number) => Math.max(min, Math.min(n, max));
  const rightMax = Math.max(rightMin, Math.min(560, narrow ? width - 32 : width - center - 7));
  const right = clamp(value.right, rightMin, rightMax);
  const bottomMax = Math.max(
    80,
    Math.min(420, height - 34 - toolbar - 24 - 180 - 7),
  );
  const bottom = clamp(value.bottom, 80, bottomMax);
  return {
    layout: { ...value, right, bottom },
    narrow,
    bounds: {
      right: {min: rightMin, max: rightMax},
      bottom: { min: 80, max: bottomMax },
    },
  };
}
