import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { LazyJson, readableData } from "./LazyJson";
afterEach(cleanup);
it("displays scientific values and sources without internal fingerprints; does not alter the original", async () => {
  const original = {
    snapshot_hash: "b".repeat(64),
    formula_version: "internal-v1",
    schema_version: "internal-v1",
    raw_data_sha256: "a".repeat(64),
    parameter_ids: ["internal-parameter"],
    construct_id: "FTH1-fusion",
    condition_id: "actual-condition",
    sequence: "A".repeat(64),
    source_reference: "https://doi.org/10.2210/pdb3AJO/pdb",
    coordinate_reference: "asset:internal-file",
    measured: [0, null, 1.25],
    unit: "uM",
  };
  const before = JSON.stringify(original);
  render(<LazyJson value={original} />);
  fireEvent.click(screen.getByText("Data and provenance"));
  const data = JSON.parse(
    (await screen.findByText(/FTH1-fusion/)).textContent!,
  );
  expect(data.measured).toEqual([0, null, 1.25]);
  expect(data.unit).toBe("uM");
  expect(data.sequence).toBe("A".repeat(64));
  expect(data.source_reference).toBe(original.source_reference);
  expect(data.coordinate_reference).toBe("Attached file");
  expect(data).not.toHaveProperty("raw_data_sha256");
  expect(data).not.toHaveProperty("snapshot_hash");
  expect(data).not.toHaveProperty("parameter_ids");
  expect(JSON.stringify(original)).toBe(before);
  expect(
    readableData({
      constant: 0,
      nested: { implementation_sha256: "hidden", temperature_c: 25 },
    }),
  ).toContain("25");
});
