import { useEffect, useRef } from "react";
import type { Dimension } from "./layout";

export function Splitter({
  dimension,
  value,
  min,
  max,
  onChange,
  defaultValue,
}: {
  dimension: Dimension;
  value: number;
  min: number;
  max: number;
  onChange: (value: number, save: boolean) => void;
  defaultValue: number;
}) {
  const horizontal = dimension === "bottom",
    direction = -1;
  const drag = useRef<
    | {
        pointer: number;
        start: number;
        size: number;
        latest: number;
        target: HTMLElement;
        selection: string;
      }
    | undefined
  >(undefined);
  const frame = useRef<number | undefined>(undefined);
  const change = useRef(onChange);
  change.current = onChange;
  function finish(restore = false, save = true) {
    const current = drag.current;
    if (!current) return;
    drag.current = undefined;
    cancelAnimationFrame(frame.current ?? 0);
    frame.current = undefined;
    if (current.target.hasPointerCapture(current.pointer))
      current.target.releasePointerCapture(current.pointer);
    document.body.style.userSelect = current.selection;
    change.current(restore ? current.size : current.latest, save);
  }
  useEffect(() => () => finish(true, false), []);
  const label =
    dimension === "right"
        ? "Inspector"
        : "Bottom pane";
  return (
    <div
      className={`splitter splitter-${dimension}`}
      role="separator"
      tabIndex={0}
      aria-label={label}
      aria-orientation={horizontal ? "horizontal" : "vertical"}
      aria-controls={
        dimension === "right"
            ? "workspace-inspector"
            : "workspace-bottom"
      }
      aria-valuenow={Math.round(value)}
      aria-valuemin={Math.round(min)}
      aria-valuemax={Math.round(max)}
      aria-valuetext={`${Math.round(value)} pixels`}
      onPointerDown={(event) => {
        if (event.button !== 0 || drag.current) return;
        event.preventDefault();
        event.currentTarget.focus();
        event.currentTarget.setPointerCapture(event.pointerId);
        drag.current = {
          pointer: event.pointerId,
          start: horizontal ? event.clientY : event.clientX,
          size: value,
          latest: value,
          target: event.currentTarget,
          selection: document.body.style.userSelect,
        };
        document.body.style.userSelect = "none";
      }}
      onPointerMove={(event) => {
        const current = drag.current;
        if (!current || current.pointer !== event.pointerId) return;
        current.latest = Math.max(
          min,
          Math.min(
            max,
            current.size +
              direction *
                ((horizontal ? event.clientY : event.clientX) - current.start),
          ),
        );
        if (frame.current === undefined)
          frame.current = requestAnimationFrame(() => {
            frame.current = undefined;
            if (drag.current) change.current(drag.current.latest, false);
          });
      }}
      onPointerUp={() => finish()}
      onPointerCancel={() => finish(true)}
      onLostPointerCapture={() => finish(true)}
      onDoubleClick={() => onChange(defaultValue, true)}
      onKeyDown={(event) => {
        if (event.key === "Escape" && drag.current) {
          event.preventDefault();
          finish(true);
          return;
        }
        const increase = horizontal ? "ArrowDown" : "ArrowRight",
          decrease = horizontal ? "ArrowUp" : "ArrowLeft";
        if (event.key !== increase && event.key !== decrease) return;
        event.preventDefault();
        onChange(
          Math.max(
            min,
            Math.min(
              max,
              value +
                (event.key === increase ? 1 : -1) *
                  direction *
                  (event.shiftKey ? 32 : 8),
            ),
          ),
          true,
        );
      }}
    />
  );
}
