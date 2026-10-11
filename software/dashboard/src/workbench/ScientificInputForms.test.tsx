import { useState } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import type { ProjectView } from "../contracts/generated";
import { ScientificInputForms } from "./ScientificInputForms";
const request = vi.hoisted(() => vi.fn());
vi.mock("../api", () => ({ requestJson: request }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// Focused editor-state stub, not a valid public project/save or biological evidence.
// Actual complete Pydantic imports and save are tested through HTTP separately.
const sample = {
  id: "SOFTWARE_EDITOR_SAMPLE",
  scientific_project: {
    config: {
      inputs: { constructs: [] },
      parameters: [
        {
          parameter_id: "software",
          name: "declared",
          value: 5,
          unit: "s^-1",
          source_type: "wetlab",
          source_reference: "SOFTWARE_ONLY",
          doi: null,
          evidence_text: null,
          evidence_location: null,
          construct_id: null,
          condition_id: null,
          uncertainty: null,
          review_status: "approved",
          approved_by: "SOFTWARE_REVIEW_STATE",
          parameter_version: 1,
          validation_flags: ["SOFTWARE_REVIEW_STATE"],
        },
      ],
    },
  },
} as unknown as ProjectView;

it("override retains approved source; blank is not zero and the candidate cannot inherit approval", () => {
  const changed = vi.fn();
  function Editor() {
    const [project, setProject] = useState(sample);
    return (
      <ScientificInputForms
        project={project}
        section="parameters"
        onChange={(value) => {
          changed(value);
          setProject(value);
        }}
      />
    );
  }
  render(<Editor />);
  expect(screen.getByLabelText('declared v1 value',{exact:true}).matches(':disabled')).toBe(true);
  fireEvent.change(screen.getByLabelText('Reason for parameter override'),{target:{value:'SOFTWARE_ONLY correction'}});
  fireEvent.click(screen.getByRole('button',{name:'Create override for declared'}));
  const replacement = changed.mock.calls.at(-1)![0].scientific_project.config.parameters[1];
  const input = screen.getByLabelText(`declared v${replacement.parameter_version} value`, { exact: true });
  fireEvent.change(input, { target: { value: "" } });
  let p = changed.mock.calls.at(-1)![0].scientific_project.config.parameters[1];
  expect(p.value).toBe("");
  expect(p).toMatchObject({
    review_status: "extracted",
    approved_by: null,
    validation_flags: [],
    parameter_version: 2,
    supersedes: 'software',
  });
  fireEvent.change(input, { target: { value: "0" } });
  p = changed.mock.calls.at(-1)![0].scientific_project.config.parameters[1];
  expect(p.value).toBe(0);
  expect(p.parameter_version).toBe(2);
  expect(changed.mock.calls.at(-1)![0].scientific_project.config.parameters[0]).toEqual(sample.scientific_project!.config.parameters[0]);
  expect(request).not.toHaveBeenCalled();
});

it("new numeric record has no implicit value, unit or source", () => {
  render(
    <ScientificInputForms
      project={sample}
      section="parameters"
      onChange={vi.fn()}
    />,
  );
  expect(screen.getByLabelText("Numeric parameter value")).toHaveProperty(
    "value",
    "",
  );
  expect(screen.getByLabelText("Explicit parameter unit")).toHaveProperty(
    "value",
    "",
  );
  expect(
    screen.getByRole("button", { name: "Validate and add to draft" }),
  ).toHaveProperty("disabled", true);
  expect(request).not.toHaveBeenCalled();
});
