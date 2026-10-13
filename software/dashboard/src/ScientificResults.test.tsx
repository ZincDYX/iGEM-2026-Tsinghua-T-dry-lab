import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { adaptSteadyResult, ScientificResults } from "./ScientificResults";
import {M2Metrics} from './workbench/ScreenResultTables';
import type { Run } from "./types";

afterEach(cleanup);
it('M1 ranking exposes missing policy without fake scores or raw provenance',()=>{
  render(<ScientificResults run={run('ranking',{status:'blocked',missing:['reviewed_ranking_policy'],
    ranked_IDR_candidate_ids:[],candidate_count:272},'method.m1.rank')}/>);
  expect(screen.getByRole('heading',{name:'M1 batch ranking'})).toBeTruthy();
  expect(screen.getByText('Required: reviewed ranking policy')).toBeTruthy();
  expect(screen.queryByRole('table')).toBeNull();
  expect(screen.queryByText(/not supported.*Export/i)).toBeNull();
});
it('adapts known M1 map parents into readable candidates, not scheduling entries',()=>{
  render(<ScientificResults run={run('decisions',{items:['fusionA','linkerA'].map(candidate_id=>({
    schema_version:'m1-method-check-v1',candidate_id,verdict:'blocked',missing:['IUPred2A','IUPred2A'],
    precheck:{sequence_kind:'full_fusion',features:{length:20,gs_fraction:.4,sequence_sha256:'PRIVATE_HASH'}}
  }))},'method.m1.decision')}/>);
  expect(screen.getByRole('heading',{name:'M1 candidates'})).toBeTruthy();
  expect(screen.getByRole('button',{name:'fusionA'})).toBeTruthy();
  expect(screen.getByRole('button',{name:'linkerA'})).toBeTruthy();
  expect(screen.getByText('Glycine / serine fraction')).toBeTruthy();
  expect(screen.queryByText(/Unknown\/legacy|PRIVATE_HASH/)).toBeNull();
  expect(screen.getByText('Missing evidence: IUPred2A')).toBeTruthy();
});
it('blocked M2 has no empty metrics table or fake structure',()=>{
  render(<M2Metrics record={{status:'insufficient_data',missing_inputs:['Predicted fusion structure'],core_ca_rmsd_angstrom:null,missing_metrics:[],reference_structure_id:'2PDZ'}}/>);
  expect(screen.getByRole('heading',{name:'Structure calculation blocked'})).toBeTruthy();
  expect(screen.queryByRole('table')).toBeNull();
  expect(screen.queryByText(/Missing metrics:/)).toBeNull();
});
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
    expect(screen.getByText(/not supported.*Export/i)).toBeTruthy();
    expect(screen.queryByRole("table")).toBeNull();
    cleanup();
  }
});
