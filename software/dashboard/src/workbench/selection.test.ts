import { describe, expect, it } from "vitest";
import type { RunSummaryView } from "../contracts/generated";
import { matchesRun, selectRunNode } from "./selection";

const run = {
  id: "frozen-run",
  project_id: "project",
  snapshot_hash: "a".repeat(64),
  nodes: [{ id: "m1", attempts: 2 }],
} as RunSummaryView;

describe("typed selection identity", () => {
  it("a same-ID proposal never selects historical output", () => {
    expect(
      matchesRun(
        { kind: "proposal-node", proposalId: "draft", nodeId: "m1" },
        run,
        "project",
      ),
    ).toBe(false);
    expect(
      matchesRun(
        {
          kind: "resource",
          projectId: "project",
          fileId: "file",
          sha256: "a".repeat(64),
        },
        run,
        "project",
      ),
    ).toBe(false);
  });
  it("all frozen identity components must match, not only the node string", () => {
    const selection = selectRunNode(run, "m1");
    expect(matchesRun(selection, run, "project")).toBe(true);
    for (const changed of [
      { ...run, id: "other" },
      { ...run, project_id: "other" },
      { ...run, snapshot_hash: "b".repeat(64) },
      { ...run, nodes: [{ ...run.nodes[0], attempts: 3 }] },
    ])
      expect(matchesRun(selection, changed, "project")).toBe(false);
    expect(matchesRun(selection, run, "other")).toBe(false);
    expect(selectRunNode(run, "missing")).toBeUndefined();
  });
});
