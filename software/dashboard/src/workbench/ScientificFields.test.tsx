import { useState } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { ScientificFields, type FieldSchema } from "./ScientificFields";
afterEach(cleanup);
it("uses field labels and leaves technical identities out of the editable form", () => {
  const change = () => { throw Error("Display changed scientific input"); };
  const { container } = render(<ScientificFields
    schema={{ type: "object", properties: {
      concentration: { type: "number", title: "Measured concentration" },
      source_sha256: { type: "string" },
    }, required: ["concentration", "source_sha256"] }} definitions={{}}
    value={{ concentration: 0, source_sha256: "b".repeat(64) }} onChange={change}
    path="scientific_project.config.inputs.measurement" files={[]} />);
  expect(container.textContent).toContain("Measured concentration");
  expect(container.textContent).not.toContain("scientific_project.config");
  expect(container.textContent).not.toContain("source_sha256");
  expect(container.textContent).not.toContain("b".repeat(64));
  expect(screen.getByRole("spinbutton").getAttribute("value")).toBe("0");
});
it("a missing nullable declaration is an exact navigation target, not an invented value", () => {
  const { container } = render(
    <ScientificFields
      schema={{ anyOf: [{ type: "number" }, { type: "null" }] }}
      definitions={{}}
      value={null}
      onChange={() => {
        throw Error("Navigation supplied a value");
      }}
      path="config.missing"
      files={[]}
    />,
  );
  const target = container.querySelector(
    '[data-input-path="config.missing"]',
  ) as HTMLInputElement;
  expect(target.type).toBe("checkbox");
  expect(target.checked).toBe(false);
  expect(screen.queryByRole("spinbutton")).toBeNull();
});
it("preserves explicit array order and adds blank numbers, not zero or objects", () => {
  function View() {
    const [v, set] = useState<unknown>([2, 3]);
    return (
      <>
        <ScientificFields
          schema={{ type: "array", items: { type: "number" } }}
          definitions={{}}
          value={v}
          onChange={set}
          path="parts"
          files={[]}
        />
        <output>{JSON.stringify(v)}</output>
      </>
    );
  }
  render(<View />);
  fireEvent.click(screen.getByText("Parts (2)"));
  fireEvent.click(screen.getByText("Move Parts 2 up"));
  expect(screen.getByRole("status").textContent).toBe("[3,2]");
  fireEvent.click(screen.getByText("Add Parts item"));
  expect(screen.getByRole("status").textContent).toBe('[3,2,""]');
});
it("displays protected review metadata without an editable approval control", () => {
  render(
    <ScientificFields
      schema={{
        type: "string",
        enum: ["extracted", "approved"],
        readOnly: true,
      }}
      definitions={{}}
      value="extracted"
      onChange={() => {
        throw Error("Approval edited");
      }}
      path="review_status"
      files={[]}
    />,
  );
  expect(screen.getByRole("status").textContent).toBe('"extracted"');
  expect(screen.queryByRole("combobox")).toBeNull();
});
it("schema types and choices do not supply numeric defaults; blank is not zero", () => {
  const source = {
    type: "object",
    required: ["n", "mode"],
    properties: {
      n: { type: "number", default: 24 },
      mode: { type: "string", enum: ["explicitA", "explicitB"] },
    },
  } as FieldSchema;
  function View() {
    const [v, set] = useState({});
    return (
      <>
        <ScientificFields
          schema={source}
          definitions={{}}
          value={v}
          onChange={(x) => set(x as object)}
          path="config"
          files={[]}
        />
        <output>{JSON.stringify(v)}</output>
      </>
    );
  }
  render(<View />);
  expect((screen.getByLabelText("config.n") as HTMLInputElement).value).toBe(
    "",
  );
  expect(
    (screen.getByLabelText("config.mode") as HTMLSelectElement).value,
  ).toBe("");
  fireEvent.change(screen.getByLabelText("config.n"), {
    target: { value: "0" },
  });
  expect(screen.getByRole("status").textContent).toBe('{"n":0}');
  fireEvent.change(screen.getByLabelText("config.n"), {
    target: { value: "" },
  });
  expect(screen.getByRole("status").textContent).toBe('{"n":""}');
});
it("union numeric mode survives clearing without interpreting a blank as zero", () => {
  function View() {
    const [v, set] = useState<unknown>("");
    return (
      <>
        <ScientificFields
          schema={{ anyOf: [{ type: "string" }, { type: "number" }] }}
          definitions={{}}
          value={v}
          onChange={set}
          path="condition"
          files={[]}
        />
        <output>{JSON.stringify(v)}</output>
      </>
    );
  }
  render(<View />);
  fireEvent.change(screen.getByLabelText("Condition value type"), {
    target: { value: "1" },
  });
  expect((screen.getByLabelText("condition") as HTMLInputElement).type).toBe(
    "number",
  );
  fireEvent.change(screen.getByLabelText("condition"), {
    target: { value: "2" },
  });
  fireEvent.change(screen.getByLabelText("condition"), {
    target: { value: "" },
  });
  expect((screen.getByLabelText("condition") as HTMLInputElement).type).toBe(
    "number",
  );
  expect(screen.getByRole("status").textContent).toBe('""');
});
