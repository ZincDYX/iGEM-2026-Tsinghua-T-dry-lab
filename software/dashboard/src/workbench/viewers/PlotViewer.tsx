import { useEffect, useRef, useState } from "react";
import type { Data, Layout, PlotlyHTMLElement } from "plotly.js";

export function PlotViewer({
  data,
  title,
  xLabel,
  yLabel,
  onPoint,
}: {
  data: Data[];
  title: string;
  xLabel: string;
  yLabel: string;
  onPoint?: (index: number) => void;
}) {
  const root = useRef<HTMLDivElement>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    let dispose: undefined | (() => void);
    const target = root.current;
    setError("");
    async function load() {
      const module = await import("plotly.js-strict-dist-min");
      if (!active || !target) return;
      const plotly = module.default;
      const layout: Partial<Layout> = {
        title: { text: title },
        xaxis: { title: { text: xLabel } },
        yaxis: { title: { text: yLabel } },
        margin: { t: 45, b: 60, l: 70, r: 20 },
        autosize: true,
      };
      const chart = await plotly.newPlot(target, data, layout, {
        responsive: true,
        displaylogo: false,
        modeBarButtonsToRemove: ["sendDataToCloud"],
        locale: "en-US",
      });
      dispose = () => plotly.purge(target);
      if (!active) {
        dispose();
        return;
      }
      chart.on("plotly_click", (event) => {
        if (active && onPoint) onPoint(event.points[0].pointIndex);
      });
    }
    void load().catch(() => {
      if (active)
        setError(
          "Plot display failed. The original table and authorized source remain available.",
        );
    });
    return () => {
      active = false;
      dispose?.();
    };
  }, [data, title, xLabel, yLabel, onPoint]);
  return (
    <section aria-label={title}>
      {error && <p role="alert">{error}</p>}
      <div ref={root} style={{ height: 320, width: "100%" }} />
    </section>
  );
}
