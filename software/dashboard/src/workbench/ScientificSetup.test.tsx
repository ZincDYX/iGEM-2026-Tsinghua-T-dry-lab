import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { ProjectView } from "../contracts/generated";
import { ScientificSettings } from "./ScientificSetup";
import type { FieldSchema } from "./ScientificFields";

afterEach(cleanup);
const records = ["A", "B"].map((construct_id) => ({
  construct_id,
  host: "original host",
  review_status: "approved",
  m1_review: { decision: "approved" },
}));
const schema: FieldSchema = {
  properties: { stages: { type: "object", properties: {} } },
  $defs: {
    InputsConfig: {
      type: "object",
      required: ["construct_records"],
      properties: {
        construct_records: {
          type: "array",
          items: {
            type: "object",
            required: ["construct_id", "host", "review_status", "m1_review"],
            properties: {
              construct_id: { type: "string" },
              host: { type: "string" },
              review_status: { type: "string", readOnly: true },
              m1_review: { type: "object", readOnly: true },
            },
          },
        },
      },
    },
  },
};
function setup() {
  const project = {
    files: [],
    scientific_project: {
      evidence_files: [],
      config: { stages: {}, inputs: { construct_records: records } },
    },
  } as unknown as ProjectView;
  const change = vi.fn();
  render(
    <ScientificSettings project={project} schema={schema} onChange={change} />,
  );
  fireEvent.click(
    screen.getByText("Model controls and additional input declarations"),
  );
  fireEvent.click(
    screen.getByText("scientific_project.config.inputs.construct_records (2)"),
  );
  return { project, change };
}
it("editing a reviewed record clears only that record's approvals without mutating the saved draft", () => {
  const { project, change } = setup();
  fireEvent.change(
    screen.getByLabelText(
      "scientific_project.config.inputs.construct_records.0.host",
    ),
    { target: { value: "new host" } },
  );
  const updated =
    change.mock.calls[0][0].scientific_project.config.inputs.construct_records;
  expect(updated[0]).toEqual({
    ...records[0],
    host: "new host",
    review_status: "extracted",
    m1_review: null,
  });
  expect(updated[1]).toEqual(records[1]);
  expect(project.scientific_project!.config.inputs.construct_records).toEqual(
    records,
  );
});
it("reordering existing records preserves reviews associated with their identities", () => {
  const { change } = setup();
  fireEvent.click(
    screen.getByText(
      "Move scientific_project.config.inputs.construct_records 2 up",
    ),
  );
  expect(
    change.mock.calls[0][0].scientific_project.config.inputs.construct_records,
  ).toEqual([records[1], records[0]]);
});
