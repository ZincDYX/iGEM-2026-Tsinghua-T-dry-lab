import { DesktopConnectionPanel } from "../DesktopConnectionPanel";
import type { Goal } from "../types";
import type { RuntimeInfoView } from "../contracts/generated";
import { LazyJson } from "../contracts/LazyJson";
import { defaultLayout, type Layout } from "./layout";

export function LocalSettings({
  layout,
  onLayout,
  info,
  onRefresh,
  goal, mode, onGoal, onMode,
}: {
  layout: Layout;
  onLayout: (value: Layout) => void;
  info?: RuntimeInfoView;
  onRefresh: () => void;
  goal: Goal; mode:"template"|"hybrid"; onGoal:(value:Goal)=>void; onMode:(value:"template"|"hybrid")=>void;
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
      <h3>Planning preferences</h3>
      <label>Analysis entry point<select aria-label="Analysis entry point" value={goal} onChange={e=>onGoal(e.target.value as Goal)}>
        <option value="fusion_screen">Fusion sequence statistics</option><option value="m1_sequence_checks">M1 sequence checks</option><option value="scientific_pipeline">M1–M4 scientific pipeline</option><option value="assembly_review">Assembly inventory</option><option value="pathway_simulation">Uploaded pathway</option>
      </select></label>
      <label>Planner source<select aria-label="Planner source" value={mode} onChange={e=>onMode(e.target.value as "template"|"hybrid")}><option value="template">Built-in plan</option><option value="hybrid" disabled={info?.capabilities.hybrid_planning!=="ready"}>Configured model</option></select></label>
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
