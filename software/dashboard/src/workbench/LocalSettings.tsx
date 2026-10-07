import { DesktopConnectionPanel } from "../DesktopConnectionPanel";
import type { RuntimeInfoView } from "../contracts/generated";
import { LazyJson } from "../contracts/LazyJson";
import { defaultLayout, type Layout } from "./layout";

export function LocalSettings({
  layout,
  onLayout,
  info,
  onRefresh,
}: {
  layout: Layout;
  onLayout: (value: Layout) => void;
  info?: RuntimeInfoView;
  onRefresh: () => void;
}) {
  return (
    <section>
      <h2>Local layout and capabilities</h2>
      <p>
        Drag separators, use arrow keys, or double-click to reset. Layout stays
        local and do not change scientific inputs.
      </p>
      <label>
        Table density
        <select
          value={layout.density}
          onChange={(e) =>
            onLayout({
              ...layout,
              density:
                e.target.value === "comfortable" ? "comfortable" : "compact",
            })
          }
        >
          <option value="compact">Compact</option>
          <option value="comfortable">Comfortable</option>
        </select>
      </label>
      <label>
        Theme
        <select
          value={layout.theme}
          onChange={(e) =>
            onLayout({
              ...layout,
              theme: e.target.value === "dark" ? "dark" : "light",
            })
          }
        >
          <option value="light">Light</option>
          <option value="dark">Dark</option>
        </select>
      </label>
      <button onClick={() => onLayout(defaultLayout())}>Reset layout</button>
      <DesktopConnectionPanel />
      <button onClick={onRefresh}>Refresh connection and capabilities</button>
      {info && (
        <LazyJson
          value={info}
          label="Public protocol, capabilities and resource state"
        />
      )}
    </section>
  );
}
