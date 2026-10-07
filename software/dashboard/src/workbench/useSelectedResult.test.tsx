import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { NodePage, RunSummaryView } from "../contracts/generated";
import * as client from "./client";
import { useSelectedResult } from "./useSelectedResult";
vi.mock("./client", () => ({ node: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
function run(
  id = "run-a",
  attempt = 1,
  hash = "artifact-a",
  projectId = "project-a",
): RunSummaryView {
  return {
    id,
    name: "Recorded software run",
    project_id: projectId,
    status: "succeeded",
    snapshot_hash: "snapshot",
    created_at: "fixture",
    updated_at: "fixture",
    control: null,
    heartbeat: null,
    state_version: 1,
    event_cursor: 1,
    project_revision: 1,
    tools: {},
    workflow: {
      id: "fixture",
      name: "fixture",
      description: "software only",
      version: "1",
      execution_policy: {
        target_node_id: null,
        max_completed_stages: null,
        checkpoints_before: [],
        checkpoints_after: [],
        allowed_tools: [],
        max_tool_calls: 1,
        stop_after_seconds: null,
        memory_limit_mb: null,
      },
      nodes: [
        {
          id: "m4",
          label: "m4",
          tool_id: "project.m4",
          inputs: {},
          depends_on: [],
          map: null,
        },
      ],
    },
    nodes: ["m1", "m4"].map((id) => ({
      id,
      parent_id: null,
      status: "succeeded",
      attempts: attempt,
      tool_id: "project." + id,
      label: id,
      scientific_summary: null,
    })),
    artifacts: ["m1", "m4"].map((node_id) => ({
      id: node_id + hash,
      run_id: id,
      node_id,
      hash,
      name: "result.json",
      upstream: [],
      metadata: {},
    })),
  };
}
function page(node: string, attempt = 1, hash = "artifact-a"): NodePage {
  return {
    node: {
      id: node,
      parent_id: null,
      status: "succeeded",
      attempts: attempt,
      output: { module: node, fixture: "software only" },
      error: null,
      inputs: null,
    },
    offset: 0,
    limit: 20,
    total_records: 1,
    artifact: { id: "fixture", hash },
    sequence_map: null,
  };
}
it("drops old projection synchronously and ignores a late response after rapid node/project/run switches", async () => {
  let finishOld!: (value: NodePage) => void;
  vi.mocked(client.node)
    .mockResolvedValueOnce(page("m4"))
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finishOld = resolve;
        }),
    )
    .mockResolvedValueOnce(page("m4"));
  const hook = renderHook(
    ({ run, selected, projectId }) =>
      useSelectedResult(run, projectId, selected),
    { initialProps: { run: run(), selected: "m4", projectId: "project-a" } },
  );
  await waitFor(() =>
    expect(hook.result.current.data?.node.output?.module).toBe("m4"),
  );
  hook.rerender({ run: run(), selected: "m1", projectId: "project-a" });
  expect(hook.result.current.data).toBeUndefined();
  hook.rerender({
    run: run("run-b", 1, "artifact-a", "project-b"),
    selected: "m4",
    projectId: "project-b",
  });
  await waitFor(() =>
    expect(hook.result.current.data?.node.output?.module).toBe("m4"),
  );
  await act(async () => {
    finishOld(page("m1"));
  });
  expect(hook.result.current.data?.node.id).toBe("m4");
});
it("attempt/hash changes invalidate cached output and reject mismatched server identity", async () => {
  vi.mocked(client.node)
    .mockResolvedValueOnce(page("m4"))
    .mockResolvedValueOnce(page("m4", 1, "artifact-a"));
  const hook = renderHook(
    ({ run }) => useSelectedResult(run, "project-a", "m4"),
    { initialProps: { run: run() } },
  );
  await waitFor(() => expect(hook.result.current.data?.node.attempts).toBe(1));
  hook.rerender({ run: run("run-a", 2, "artifact-b") });
  expect(hook.result.current.data).toBeUndefined();
  await waitFor(() =>
    expect(hook.result.current.error).toContain("identity changed"),
  );
  expect(hook.result.current.data).toBeUndefined();
});
