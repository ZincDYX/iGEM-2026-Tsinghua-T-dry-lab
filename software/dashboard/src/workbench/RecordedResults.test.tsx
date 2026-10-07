import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { M5View } from "./M5View";
import { ScanViewer } from "./viewers/ScanViewer";

// Independent, already-recorded software samples. No scientific stage is run.
const mocks = vi.hoisted(() => ({ plot: vi.fn(), request: vi.fn() }));
vi.mock("./viewers/PlotViewer", () => ({
  PlotViewer: (props: unknown) => {
    mocks.plot(props);
    return <div data-testid="plot" />;
  },
}));
vi.mock("../api", () => ({ requestJson: mocks.request }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

const identity = {
  experiment_id: "software",
  construct_id: "construct",
  condition_id: "condition",
  replicate_id: "replicate",
};
function record() {
  return {
    ...identity,
    metabolite_comparisons: {
      "13": {
        comparison_status: "endpoint_only",
        fit: null,
        display_series: {
          ...identity,
          schema_version: "m5-comparison-series-v1",
          raw_data_sha256: "a".repeat(64),
          compartment: "intracellular",
          concentration_basis: "cell_volume",
          time_unit: "h",
          concentration_unit: "uM",
          source_time_unit: "min",
          source_concentration_unit: "mM",
          comparison_adapter: "legacy_trajectory",
          time: [0, 1, 2],
          observed: [0, 0.5, 6],
          predicted: [0, 2, 4],
          residual_observed_minus_predicted: [null, null, 2],
          censor_mask: ["below_lod", "below_lod", "quantified"],
          lod: 1,
          loq: 2,
          observation_kind: "concentration",
          uncertainty: [0.1, 0.2, 0.3],
          uncertainty_type: "sd",
          parameter_approval: "not_granted_by_display",
        },
      },
    },
  };
}

it("M5 preserves recorded zeros and censor bounds, residual nulls, and uncertainty without fitting", async () => {
  render(<M5View record={record()} />);
  await screen.findAllByTestId("plot");
  const plots = mocks.plot.mock.calls.map(([props]) => props);
  const main = plots.find((p) => p.title.includes("observations"));
  expect(main.data[0].y).toEqual([0, 2, 4]);
  expect(main.data[1].y).toEqual([null, null, 6]);
  expect(main.data[1].error_y.array).toEqual([0, 0, 0.3]);
  expect(main.data[2].y).toEqual([1, 1, null]);
  expect(plots.find((p) => p.title.includes("residuals")).data[0].y).toEqual([
    null,
    null,
    2,
  ]);
  expect(main.yLabel).toContain("uM");
  expect(screen.getByText(/not a prediction confidence band/)).toBeTruthy();
  fireEvent.click(screen.getAllByRole("row")[3]);
  expect(screen.getAllByRole("row")[3].getAttribute("aria-selected")).toBe(
    "true",
  );
});

it("M5 refuses different experiment identity and never reconstructs legacy summary curves", () => {
  const source = record();
  source.condition_id = "other";
  const view = render(<M5View record={source} />);
  expect(screen.getByRole("alert").textContent).toContain("identity differs");
  expect(mocks.plot).not.toHaveBeenCalled();
  view.rerender(
    <M5View
      record={{ ...identity, metabolite_comparisons: { "13": { fit: null } } }}
    />,
  );
  expect(screen.getByText(/No curve regenerated/)).toBeTruthy();
  expect(mocks.plot).not.toHaveBeenCalled();
});

function scan() {
  return {
    schema_version: "display-finite-scan-v1",
    identity: {
      project_id: "p",
      file_id: "f",
      source_sha256: "b".repeat(64),
      run_id: null,
      snapshot_hash: null,
      node_id: null,
      attempt: null,
      candidate_id: null,
      construct_id: null,
      condition_id: null,
    },
    offset: 0,
    total: 2,
    has_more: false,
    decision_id: "software",
    decision_scope: "formal_conditional_mechanism",
    objective: "yield_abs",
    metric_definition: "recorded yield",
    metric_unit: "1",
    comparison_contract: null,
    points: [
      {
        ordinal: 0,
        candidate_id: "a",
        site_ratio: 1,
        dense_oc_dmt_ratio: 0,
        status: "valid",
        feasible: true,
        metric_value: 0,
        reason_codes: [],
      },
      {
        ordinal: 1,
        candidate_id: "b",
        site_ratio: 2,
        dense_oc_dmt_ratio: null,
        status: "valid",
        feasible: false,
        metric_value: null,
        reason_codes: ["comparison_contract_differs"],
      },
    ],
    ranking_performed: false,
    claim_scope: "source_reported_scan_not_execution_or_parameter_approval",
  };
}

it("F3 shows exact zero/null, units, blocked row and point-table selection without ranking", async () => {
  mocks.request.mockResolvedValue(scan());
  render(<ScanViewer projectId="p" fileId="f" />);
  await screen.findByText("comparison_contract_differs");
  const plot = mocks.plot.mock.calls.at(-1)![0];
  expect(plot.data[0].y).toEqual([0, null]);
  expect(plot.data[0].x).toEqual([1, 2]);
  expect(plot.yLabel).toBe("recorded yield (1)");
  expect(screen.getAllByRole("row")).toHaveLength(3);
  fireEvent.click(screen.getAllByRole("row")[2]);
  expect(screen.getAllByRole("row")[2].getAttribute("aria-selected")).toBe(
    "true",
  );
  expect(
    screen.getByText(/no synthetic continuous scan or global optimum claim/),
  ).toBeTruthy();
});

it("F3 refuses an authorized response with a different source identity", async () => {
  const source = scan();
  source.identity.project_id = "stranger";
  mocks.request.mockResolvedValue(source);
  render(<ScanViewer projectId="p" fileId="f" />);
  await waitFor(() =>
    expect(screen.getByRole("alert").textContent).toContain("incompatible"),
  );
  expect(mocks.plot).not.toHaveBeenCalled();
});
