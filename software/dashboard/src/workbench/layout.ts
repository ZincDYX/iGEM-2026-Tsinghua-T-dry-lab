export interface Layout {
  left: number;
  right: number;
  bottom: number;
  density: "compact" | "comfortable";
  theme: "light" | "dark";
}
export type Dimension = "left" | "right" | "bottom";
export const defaultLayout = (): Layout => ({
  left: 225,
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
      [value.left, value.right, value.bottom].every(
        (item) =>
          typeof item === "number" &&
          Number.isFinite(item) &&
          item >= 60 &&
          item <= 2000,
      )
    )
      return {
        ...defaultLayout(),
        left: value.left,
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
  const leftMin = Math.min(180, Math.max(100, width - center - 14));
  const rightMin = narrow ? Math.min(260, width - 32) : 260;
  const clamp = (n: number, min: number, max: number) =>
    Math.max(min, Math.min(n, max));
  const left = clamp(
    value.left,
    leftMin,
    Math.max(
      leftMin,
      Math.min(
        420,
        width - center - 14 - (!narrow && inspector ? rightMin : 0),
      ),
    ),
  );
  const right = clamp(
    value.right,
    rightMin,
    Math.max(
      rightMin,
      Math.min(560, narrow ? width - 32 : width - center - left - 14),
    ),
  );
  const bottomMax = Math.max(
    80,
    Math.min(420, height - 34 - toolbar - 24 - 180 - 7),
  );
  const bottom = clamp(value.bottom, 80, bottomMax);
  return {
    layout: { ...value, left, right, bottom },
    narrow,
    bounds: {
      left: {
        min: leftMin,
        max: Math.max(
          leftMin,
          Math.min(
            420,
            width - center - 14 - (!narrow && inspector ? right : 0),
          ),
        ),
      },
      right: {
        min: rightMin,
        max: Math.max(
          rightMin,
          Math.min(560, narrow ? width - 32 : width - center - left - 14),
        ),
      },
      bottom: { min: 80, max: bottomMax },
    },
  };
}
