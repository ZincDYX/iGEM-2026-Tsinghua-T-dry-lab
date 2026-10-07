import { useEffect, useRef, useState } from "react";
import type { Data, Layout } from "plotly.js";

export function PlotViewer({
  data,
  title,
  xLabel,
  yLabel,
  onPoint,
  dataIdentity,
}: {
  data: Data[];
  title: string;
  xLabel: string;
  yLabel: string;
  onPoint?: (index: number) => void;
  dataIdentity: string;
}) {
  const root = useRef<HTMLDivElement>(null);
  const [error, setError] = useState("");
  const callback = useRef(onPoint);
  callback.current = onPoint;
  const [instance, setInstance] = useState<{
    target: HTMLDivElement;
    plotly: (typeof import("plotly.js-strict-dist-min"))["default"];
  }>();
  const updates = useRef(Promise.resolve());
  useEffect(() => {
    let active = true;
    let dispose: undefined | (() => void);
    const target = document.createElement("div");
    target.style.height = "100%";
    root.current?.appendChild(target);
    setError("");
    async function load() {
      const module = await import("plotly.js-strict-dist-min");
      if (!active) return;
      const plotly = module.default;
      const chart = await plotly.newPlot(
        target,
        [],
        {},
        {
          responsive: true,
          displaylogo: false,
          modeBarButtonsToRemove: ["sendDataToCloud"],
          locale: "en-US",
        },
      );
      dispose = () => plotly.purge(target);
      if (!active) {
        dispose();
        return;
      }
      const click = (event: Readonly<import("plotly.js").PlotMouseEvent>) => {
        if (active) callback.current?.(event.points[0].pointIndex);
      };
      chart.on("plotly_click", click);
      dispose = () => {
        chart.removeAllListeners("plotly_click");
        plotly.purge(target);
      };
      setInstance({ target, plotly });
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
      target.remove();
    };
  }, []);
  useEffect(() => {
    if (!instance) return;
    let active = true;
    const layout: Partial<Layout> = {
      title: { text: title },
      xaxis: { title: { text: xLabel } },
      yaxis: { title: { text: yLabel } },
      uirevision: dataIdentity,
      margin: { t: 45, b: 60, l: 70, r: 20 },
      autosize: true,
    };
    // Serialize updates; selection is a react update, not a new instance.
    updates.current = updates.current
      .then(async () => {
        if (active && instance.target.isConnected)
          await instance.plotly.react(instance.target, data, layout);
      })
      .catch(() => {
        if (active)
          setError("Plot update failed; the original table remains available.");
      });
    return () => {
      active = false;
    };
  }, [instance, data, title, xLabel, yLabel, dataIdentity]);
  return (
    <section aria-label={title}>
      {error && <p role="alert">{error}</p>}
      <div ref={root} style={{ height: 320, width: "100%" }} />
    </section>
  );
}
