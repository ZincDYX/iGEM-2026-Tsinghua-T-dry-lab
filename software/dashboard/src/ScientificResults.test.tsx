import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { adaptSteadyResult, ScientificResults } from "./ScientificResults";
import type { Run } from "./types";

afterEach(cleanup);
// Contract-only fixtures. Real HTTP/MCP numeric output is covered by Playwright.
const base = { schema_version: "m4-steady-state-v1", model_kind: "markdown_steady_state",
  formula_version: "m4-step0-step8-2026-09-27", status: "blocked", warnings: ["missing_required_outlet"] };
function run(id: string, output: unknown, tool = "igem.m4.solve_steady_state") {
  return { id: "run", nodes: [{ id, parent_id: null, status: "succeeded", output }],
    snapshot: { workflow: { nodes: [{ id, tool_id: tool }] } } } as unknown as Run;
}
it("tool identity survives arbitrary node names and blocked success is not a prediction", () => {
  for (const id of ["pathway", "renamed"]) {
    render(<ScientificResults run={run(id, {ok:true, result:base})} />);
    expect(screen.getByRole("heading", {name: "M4 Original-formula steady state"})).toBeTruthy();
    expect(screen.getByText(/No valid prediction/)).toBeTruthy();
    expect(screen.getByText("missing_required_outlet")).toBeTruthy();
    expect(screen.queryByRole("table")).toBeNull();
    cleanup();
  }
});
it("unknown, old, incomplete and failed MCP envelopes fall back without zeros or exceptions", () => {
  for (const output of [{ok:false,result:base}, {ok:true,result:{...base,status:"valid"}},
      {ok:true,result:{...base,schema_version:"future"}}, null]) {
    expect(adaptSteadyResult("igem.m4.solve_steady_state", output)).toBeNull();
    render(<ScientificResults run={run("pathway", output)} />);
    expect(screen.getByText(/Unknown\/legacy\/incomplete/)).toBeTruthy();
    expect(screen.queryByRole("table")).toBeNull();
    cleanup();
  }
});
