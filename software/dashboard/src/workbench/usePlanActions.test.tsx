import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { ActionView } from "../contracts/generated";
import * as client from "./client";
import { usePlanActions } from "./usePlanActions";
vi.mock("./client", () => ({ actions: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});
const row = (seq: number): ActionView => ({
  seq,
  proposal_id: null,
  run_id: null,
  action: "SOFTWARE_FIXTURE",
  actor: "fixture",
  timestamp: "fixture",
});
it("drains bounded pages, continues cursor and explicitly marks the 500-row retained window", async () => {
  vi.mocked(client.actions).mockImplementation(async (_id, after = 0) =>
    Array.from({ length: Math.min(100, 650 - after) }, (_, i) =>
      row(after + i + 1),
    ),
  );
  const fail = vi.fn();
  const hook = renderHook(() => usePlanActions("project-a", "v1", fail));
  await waitFor(() => expect(hook.result.current.items).toHaveLength(500));
  expect(client.actions).toHaveBeenCalledTimes(5);
  expect(hook.result.current.hasMore).toBe(true);
  expect(hook.result.current.trimmed).toBe(false);
  act(() => hook.result.current.loadMore());
  await waitFor(() => expect(hook.result.current.items.at(-1)?.seq).toBe(650));
  expect(hook.result.current.items[0].seq).toBe(151);
  expect(hook.result.current.trimmed).toBe(true);
  expect(hook.result.current.hasMore).toBe(false);
  expect(fail).not.toHaveBeenCalled();
});
it("does not advance the new project cursor from an old response", async () => {
  let old!: (rows: ActionView[]) => void;
  vi.mocked(client.actions)
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          old = resolve;
        }),
    )
    .mockResolvedValueOnce([row(1)]);
  const fail = vi.fn();
  const hook = renderHook(({ id }) => usePlanActions(id, "v1", fail), {
    initialProps: { id: "project-a" },
  });
  hook.rerender({ id: "project-b" });
  await waitFor(() => expect(hook.result.current.items).toHaveLength(1));
  await act(async () => old([row(999)]));
  expect(hook.result.current.items.map((item) => item.seq)).toEqual([1]);
  expect(fail).not.toHaveBeenCalled();
});
