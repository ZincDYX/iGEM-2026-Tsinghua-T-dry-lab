import { useEffect, useState } from "react";
import type { NodePage, RunSummaryView } from "../contracts/generated";
import * as client from "./client";

export function useSelectedResult(
  run: RunSummaryView | undefined,
  projectId: string | undefined,
  selected: string,
) {
  const [offset, setOffset] = useState(0);
  const [state, setState] = useState<{
    key: string;
    data?: NodePage;
    error?: string;
  }>();
  const current = run?.nodes.find((node) => node.id === selected),
    artifact = run?.artifacts.find((item) => item.node_id === selected);
  const identity = JSON.stringify([
    projectId,
    run?.id,
    selected,
    current?.attempts,
    artifact?.hash,
  ]);
  const key = JSON.stringify([identity, offset, current?.status]);
  useEffect(() => {
    setOffset(0);
  }, [identity]);
  useEffect(() => {
    const controller = new AbortController();
    if (!run || run.project_id !== projectId || !selected || !current) return;
    client
      .node(run.id, selected, offset, controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return;
        if (
          data.node.id !== selected ||
          data.node.attempts !== current.attempts ||
          data.offset !== offset ||
          data.artifact?.hash !== artifact?.hash
        )
          throw new Error(
            "Result identity changed. Refresh the run; stale results are not displayed.",
          );
        setState({ key, data });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setState({
            key,
            error: error instanceof Error ? error.message : "Stage read failed",
          });
      });
    return () => controller.abort();
  }, [key]);
  // Projection is invalidated during render, not a later effect frame.
  return {
    data: state?.key === key ? state.data : undefined,
    error: state?.key === key ? state.error : undefined,
    offset,
    setOffset,
    identity,
  };
}
