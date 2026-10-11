import { useEffect, useRef, useState } from "react";
import {
  defaultLayout,
  layoutBounds,
  loadLayout,
  persistLayout,
  type Dimension,
  type Layout,
} from "./layout";

export function useWorkbenchLayout() {
  const root = useRef<HTMLDivElement>(null);
  const [preferences, setPreferences] = useState(loadLayout);
  const [viewport, setViewport] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
    toolbar: 100,
  });
  const [inspectorOpen, setInspectorOpen] = useState(
    false,
  );
  const [bottomOpen, setBottomOpen] = useState(false);
  useEffect(() => {
    const measure = () => {
      const toolbar =
        root.current
          ?.querySelector(".workbench-toolbar")
          ?.getBoundingClientRect().height ?? 100;
      setViewport({
        width: window.innerWidth,
        height: window.innerHeight,
        toolbar,
      });
    };
    const observer = new ResizeObserver(measure);
    if (root.current) observer.observe(root.current);
    const toolbar = root.current?.querySelector(".workbench-toolbar");
    if (toolbar) observer.observe(toolbar);
    window.addEventListener("resize", measure);
    measure();
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, []);
  const view = layoutBounds(
    preferences,
    viewport.width,
    viewport.height,
    viewport.toolbar,
    inspectorOpen,
  );
  useEffect(() => {
    if (view.narrow) setInspectorOpen(false);
  }, [view.narrow]);
  function update(value: Layout, save = true) {
    setPreferences(value);
    if (save) persistLayout(value);
  }
  function resize(key: Dimension, value: number, save: boolean) {
    const next = {
      ...preferences,
      [key]: Math.max(
        view.bounds[key].min,
        Math.min(view.bounds[key].max, value),
      ),
    };
    update(next, save);
  }
  return {
    ...view,
    root,
    inspectorOpen,
    setInspectorOpen,
    bottomOpen,
    setBottomOpen,
    update,
    resize,
    defaults: defaultLayout(),
  };
}
