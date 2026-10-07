import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { PlanPanel } from "./PlanPanel";
import { defaultPolicy } from "./client";
import type {
  RunSummaryView,
  ScientificPrecheckView,
} from "../contracts/generated";
afterEach(cleanup);

it("keeps job completion separate from missing evidence and revision-bound precheck", () => {
  const workflow: RunSummaryView["workflow"] = {
    id: "software",
    name: "software",
    description: "Recorded fixture only",
    version: "1",
    execution_policy: defaultPolicy(),
    nodes: [
      {
        id: "m4",
        label: "M4",
        tool_id: "project.m4",
        depends_on: [],
        inputs: {},
        map: null,
      },
    ],
  };
  const run: RunSummaryView = {
    id: "run",
    name: "Recorded software run",
    project_id: "p",
    status: "succeeded",
    snapshot_hash: "s",
    created_at: "fixture",
    updated_at: "fixture",
    control: null,
    heartbeat: null,
    state_version: 1,
    event_cursor: 1,
    project_revision: 1,
    workflow,
    tools: {},
    artifacts: [],
    nodes: [
      {
        id: "m4",
        parent_id: null,
        status: "succeeded",
        attempts: 1,
        tool_id: "project.m4",
        label: "M4",
        scientific_summary: {
          module: "m4",
          record_count: 2,
          status_counts: { insufficient_data: 2 },
          numerically_solved_count: 0,
          evidence_ready_count: 0,
          missing_input_count: 2,
          claim_scope: "NOT_A_PREDICTION",
        },
      },
    ],
  };
  const check: ScientificPrecheckView = {
    project_id: "p",
    project_revision: 2,
    input_sha256: "a".repeat(64),
    missing: [],
    limitations: [],
    scope: "declared_inputs_and_parameter_contracts_only",
    final_stage_gates_required: true,
    scientific_approval_granted: false,
  };
  render(
    <PlanPanel
      workflow={workflow}
      run={run}
      selected="m4"
      onSelect={() => {}}
      inputCheck={check}
    />,
  );
  expect(screen.getByText("Missing evidence")).toBeTruthy();
  expect(
    screen.getByText(/Numerically solved: 0\/2 · Evidence ready: 0\/2/),
  ).toBeTruthy();
  expect(screen.getByText("Not checked for these inputs")).toBeTruthy();
  expect(screen.queryByText(/validated|yield:|ranking:/i)).toBeNull();
});
