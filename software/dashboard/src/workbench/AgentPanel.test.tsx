import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { ProposalDiff, ProposalView } from "../contracts/generated";
import { AgentPanel } from "./AgentPanel";
import * as client from "./client";

vi.mock("./client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./client")>()),
  assistantHistory: vi.fn(),
  proposalDiff: vi.fn(),
}));
afterEach(cleanup);

async function showChanges(changes: ProposalDiff["changes"], formula = false) {
  const proposal: ProposalView = {
    id: "proposal",
    task_id: "proposal",
    project_id: "software-only",
    source: "validated_template",
    status: "proposed",
    objective: "",
    rationale: "Software presentation only",
    change_types: [],
    evidence: [],
    requested_stages: [],
    execution_stages: [],
    reused_artifacts: [],
    missing_inputs: [],
    limitations: [],
    scientific_actions: [],
    observation: null,
    reviewed_tool_labels: [],
    review_identity: null,
    previous_review_identity: null,
    confirmation: null,
    created_at: "fixture",
    workflow: {
      id: "workflow",
      name: "Software only",
      version: "1",
      description: "",
      execution_policy: client.defaultPolicy(),
      nodes: [
        {
          id: "node",
          label: "Readable module",
          tool_id: formula ? "workflow.custom_formula" : "project.m1",
          inputs: formula
            ? {
                spec: {
                  kind: "literal",
                  value: {
                    variables: { concentration: { value: 2, unit: "uM" } },
                  },
                },
              }
            : {},
          depends_on: [],
          map: null,
        },
      ],
    },
  };
  vi.mocked(client.assistantHistory).mockResolvedValue({
    project_id: proposal.project_id,
    messages: [],
    has_more: false,
  });
  vi.mocked(client.proposalDiff).mockResolvedValue({
    proposal_id: proposal.id,
    previous_proposal_id: null,
    changes,
    missing_inputs: [],
    evidence: [],
    limitations: [],
  });
  render(
    <AgentPanel
      proposal={proposal}
      projectId={proposal.project_id}
      objective=""
      mode="template"
      permission={false}
      busy={false}
      canPlan={true}
      onObjective={vi.fn()}
      onPermission={vi.fn()}
      onPropose={vi.fn()}
      onDecision={vi.fn()}
    />,
  );
  return screen.findByLabelText("Proposed changes");
}

it("keeps duplicate bindings grouped with human-readable module and permission changes", async () => {
  const binding = {
    kind: "binding" as const,
    target: "node.project",
    node_id: "node",
    input_name: "project",
    before: null,
    after: "fixture",
  };
  const panel = await showChanges([
    binding,
    binding,
    {
      kind: "dependency",
      target: "node",
      node_id: "node",
      input_name: null,
      before: "[]",
      after: "[upstream]",
    },
    {
      kind: "permission",
      target: "scope",
      node_id: null,
      input_name: null,
      before: null,
      after: "fixture",
    },
  ]);
  const items = within(panel).getAllByRole("listitem");
  expect(items).toHaveLength(2);
  expect(items[0].textContent).toBe(
    "Readable module — inputs: scientific input plan — dependencies updated",
  );
  expect(items[1].textContent).toBe(
    "Execution scope and tool permissions: all modules.",
  );
});

it("shows actual formula variable values instead of opaque binding payloads", async () => {
  const panel = await showChanges(
    [
      {
        kind: "binding",
        target: "node.spec",
        node_id: "node",
        input_name: "spec",
        before: null,
        after: "fixture",
      },
    ],
    true,
  );
  expect(panel.textContent).toContain("concentration = 2 uM");
});

it("does not imply that a prompt with no diff changed scientific parameters", async () => {
  const panel = await showChanges([]);
  expect(panel.textContent).toContain("No graph or permission changes.");
  expect(panel.textContent).toContain(
    "This prompt did not edit scientific parameters.",
  );
});
