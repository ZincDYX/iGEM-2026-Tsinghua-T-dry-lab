import type { RunSummaryView, Workflow, ScientificPrecheckView } from '../contracts/generated';
import type { ScientificStageSummary } from '../contracts/RunSummaryView.generated';
import { jobLabels } from './messages.en';

/** A saved run belongs to its exact semantic workflow, never an edited graph. */
export function matchingRun(workflow: Workflow, run?: RunSummaryView) {
  return run && JSON.stringify(run.workflow) === JSON.stringify(workflow) ? run : undefined;
}

export function inputCheckLabel(toolId: string, inputCheck?: ScientificPrecheckView, run?: RunSummaryView) {
  if (!inputCheck || (run && (run.project_id !== inputCheck.project_id || run.project_revision !== inputCheck.project_revision)))
    return 'Not checked for these inputs';
  const stages = ['m1', 'm2', 'm3', 'm4', 'm5'];
  if (!stages.some(stage => toolId === `project.${stage}`)) return 'Not checked for this tool';
  return `${inputCheck.missing.filter(item => toolId === `project.${item.stage}`).length} known omissions · r${inputCheck.project_revision}`;
}

/** Shared presentation only: every count comes from the backend's assessment. */
export function ModuleScientificStatus({summary, experimentalValidation, compact = false}: {
  summary?: ScientificStageSummary | null; experimentalValidation?: string; compact?: boolean;
}) {
  return <span className="module-scientific-status">
    {!compact && !!summary?.record_count && (summary.evidence_ready_count < summary.record_count || summary.missing_input_count > 0) && <span>Missing evidence</span>}
    <span>Numerical results: {summary?.record_count ? `${summary.numerically_solved_count}/${summary.record_count} solved` : 'Not assessed'}</span>
    <span>Evidence: {summary?.record_count ? `${summary.evidence_ready_count}/${summary.record_count} ready` : 'Not assessed'}</span>
    <span>Run experimental validation: {experimentalValidation?.replaceAll('_', ' ') ?? 'Not assessed'}</span>
    {summary && !compact && <>
      <span>Missing inputs: {summary.missing_input_count}</span>
      <span>{Object.entries(summary.status_counts).map(([status, count]) => `${status.replaceAll('_', ' ')}: ${count}`).join('; ') || 'No scientific records'}</span>
      <span>Scope: {summary.claim_scope ?? 'Not recorded'}</span>
    </>}
  </span>;
}

export function ModuleStatus({run, nodeId}: {run?: RunSummaryView; nodeId: string}) {
  const state = run?.nodes.find(node => node.id === nodeId);
  return <span className="module-status">
    <span>Job: {state ? jobLabels[state.status] ?? state.status : 'Not started'}</span>
    <ModuleScientificStatus summary={state?.scientific_summary}
      experimentalValidation={run?.scientific_assessment.experimental_validation} compact/>
  </span>;
}
