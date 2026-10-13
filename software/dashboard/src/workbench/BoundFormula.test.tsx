import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { BoundFormula } from "./BoundFormula";
import { ModuleParameters } from "./ModuleParameters";
import type { ModuleMethodView, ProjectView } from "../contracts/generated";
afterEach(cleanup);
const tree = {
  kind: "binary",
  operator: "add",
  left: { kind: "variable", name: "x" },
  right: {
    kind: "binary",
    operator: "multiply",
    left: { kind: "variable", name: "x" },
    right: { kind: "constant", value: 2 },
  },
};
it("repeated symbols use one exact input; Enter saves, no-op and Escape never save, constants are not editors", async () => {
  const save = vi.fn().mockResolvedValue(undefined),
    value = 0.1234567890123456;
  const view = render(
    <BoundFormula
      tree={tree}
      variables={{ x: { value, unit: "1" } }}
      frozen={false}
      onSave={save}
    />,
  );
  expect(screen.getAllByRole("button", { name: "Edit x" })).toHaveLength(2);
  fireEvent.click(screen.getAllByRole("button", { name: "Edit x" })[0]);
  expect(screen.getByLabelText("Value for x")).toHaveProperty(
    "value",
    String(value),
  );
  fireEvent.keyDown(screen.getByLabelText("Value for x"), { key: "Enter" });
  expect(save).not.toHaveBeenCalled();
  fireEvent.click(screen.getAllByRole("button", { name: "Edit x" })[1]);
  fireEvent.change(screen.getByLabelText("Value for x"), {
    target: { value: ".75" },
  });
  fireEvent.keyDown(screen.getByLabelText("Value for x"), { key: "Escape" });
  expect(save).not.toHaveBeenCalled();
  fireEvent.click(screen.getAllByRole("button", { name: "Edit x" })[0]);
  fireEvent.change(screen.getByLabelText("Value for x"), {
    target: { value: ".625" },
  });
  fireEvent.keyDown(screen.getByLabelText("Value for x"), { key: "Enter" });
  await waitFor(() => expect(save).toHaveBeenCalledWith("x", 0.625, "1"));
  view.rerender(
    <BoundFormula
      tree={tree}
      variables={{ x: { value: 0.625, unit: "1" } }}
      frozen={false}
      onSave={save}
    />,
  );
  expect(
    screen
      .getAllByRole("button", { name: "Edit x" })
      .map((button) => button.textContent),
  ).toEqual(["0.625", "0.625"]);
  expect(screen.queryByRole("button", { name: "Edit 2" })).toBeNull();
  view.rerender(
    <BoundFormula
      tree={tree}
      variables={{ x: { value: 0.625, unit: "1", readOnly: true } }}
      frozen={false}
      onSave={save}
    />,
  );
  expect(screen.queryByRole("button", { name: "Edit x" })).toBeNull();
});
it("a typed embedded quantity and its registry record advance together without overwriting the source", async () => {
  // Software-only binding fixture. No model/solver is run.
  const original = {
    parameter_id: "old",
    name: "pool_volume",
    value: 0.1234567890123456,
    unit: "L",
    parameter_version: 1,
    review_status: "approved",
    approved_by: "fixture",
    notes: "SOFTWARE_ONLY",
    supersedes: null,
    source_reference: "SOFTWARE_ONLY",
    uncertainty: null,
  };
  const quantity = {
    parameter_id: "old",
    value: original.value,
    unit: "L",
    source_reference: "SOFTWARE_ONLY",
  };
  const project = {
    id: "p",
    scientific_project: {
      config: {
        parameters: [original],
        stages: {
          m4_reaction: {
            compartment_requests: { example: { volume: quantity } },
          },
        },
      },
    },
  } as unknown as ProjectView;
  const method = {
    parameter_records: [original],
    parameter_requirements: [],
    parameter_source_options: {},
    parameter_model_paths: {
      old: [
        ["stages", "m4_reaction", "compartment_requests", "example", "volume"],
      ],
    },
    formula_inputs: [],
    methods: [],
  } as unknown as ModuleMethodView;
  const save = vi.fn().mockResolvedValue(undefined);
  render(
    <ModuleParameters
      project={project}
      method={method}
      frozen={false}
      onChange={save}
      onScalarChange={vi.fn()}
    />,
  );
  fireEvent.click(screen.getByRole("button", { name: "Edit pool_volume" }));
  fireEvent.change(screen.getByLabelText("Value for pool_volume"), {
    target: { value: ".25" },
  });
  fireEvent.keyDown(screen.getByLabelText("Value for pool_volume"), {
    key: "Enter",
  });
  await waitFor(() => expect(save).toHaveBeenCalled());
  const config = save.mock.calls[0][0].scientific_project.config,
    next = config.parameters[1];
  expect(config.parameters[0]).toEqual(original);
  expect(next).toMatchObject({
    value: 0.25,
    unit: "L",
    supersedes: "old",
    parameter_version: 2,
    review_status: "extracted",
    approved_by: null,
  });
  expect(config.stages.m4_reaction.compartment_requests.example.volume).toEqual(
    { ...quantity, value: 0.25, parameter_id: next.parameter_id },
  );
  expect(project.scientific_project!.config.parameters).toEqual([original]);
  expect(quantity.value).toBe(original.value);
});
