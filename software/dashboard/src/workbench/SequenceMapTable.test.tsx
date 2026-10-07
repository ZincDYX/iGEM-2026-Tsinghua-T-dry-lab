import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import evidence from "../../../../tests/fixtures/r7_sequence_display/parent_result.json";
import { parsePublic } from "../contracts/validation";
import { SequenceMapTable } from "./SequenceMapTable";

function recordedPage(failed = false) {
  // Display already recorded values; no feature/ProtParam calculation.
  const items = evidence.node.output.items;
  return parsePublic("NodePage", {
    node: {
      id: "sequences",
      parent_id: null,
      status: "succeeded",
      attempts: 0,
      output: null,
      error: null,
      inputs: null,
    },
    offset: 0,
    limit: 20,
    total_records: 12,
    artifact: { id: "parent", hash: "a".repeat(64) },
    sequence_map: {
      schema_version: "sequence-metrics-map-view-v1",
      run_id: "recorded-run",
      project_id: "recorded-project",
      snapshot_hash: "b".repeat(64),
      parent_node_id: "sequences",
      parent_attempt: 0,
      parent_artifact_id: "parent",
      parent_artifact_sha256: "a".repeat(64),
      tool_identity: { version: "1" },
      total_count: 12,
      offset: 0,
      rows: items.map((value, index) => ({
        node_id: `sequences[${index}]`,
        sequence_id: value.id,
        sequence_sha256: value.features.sequence_sha256,
        attempt: 1,
        status: failed && index === 0 ? "failed" : "succeeded",
        artifact_id: `child-${index}`,
        artifact_sha256: "c".repeat(64),
        metrics:
          failed && index === 0
            ? null
            : { schema_version: "sequence-metrics-v1", ...value },
        issue: failed && index === 0 ? "failed" : null,
      })),
    },
  }).sequence_map!;
}

afterEach(cleanup);
describe("original twelve-record sequence map display", () => {
  it("shows registered rows and original values, filters and selects a child", () => {
    const select = vi.fn();
    render(<SequenceMapTable value={recordedPage()} onSelect={select} />);
    expect(screen.getAllByRole("row")).toHaveLength(13);
    expect(screen.queryByText("SHA-256")).toBeNull();
    expect(screen.queryByText("b".repeat(64))).toBeNull();
    expect(
      screen.queryByText(
        evidence.node.output.items[0].features.sequence_sha256,
      ),
    ).toBeNull();
    const first = screen.getByRole("button", {
      name: "FUSN_1_214_from_wetlab_snapgene",
    });
    expect(
      within(first.closest("tr")!).getByText("214", { exact: true }),
    ).toBeTruthy();
    expect(screen.queryByText(/未知、旧版本/)).toBeNull();
    fireEvent.click(first);
    expect(select).toHaveBeenCalledWith("sequences[0]");
    fireEvent.change(screen.getByLabelText("Filter sequence metrics"), {
      target: { value: "FUSN_1_214" },
    });
    expect(screen.getAllByRole("row")).toHaveLength(2);
    expect(screen.getByText(/12 registered children/)).toBeTruthy();
  });
  it("failed child remains a row with no invented zero or inherited metrics", () => {
    render(<SequenceMapTable value={recordedPage(true)} onSelect={() => {}} />);
    const row = screen
      .getByRole("button", { name: "FUSN_1_214_from_wetlab_snapgene" })
      .closest("tr")!;
    expect(within(row).getByText("failed / failed")).toBeTruthy();
    expect(within(row).queryByText("214", { exact: true })).toBeNull();
    expect(within(row).queryByText("0", { exact: true })).toBeNull();
    expect(screen.getAllByRole("row")).toHaveLength(13);
  });
});
