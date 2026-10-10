import type {RunSummaryView} from '../contracts/generated';
import {statusLabel} from './PlanPanel';
const labels:Record<string,string>={all_recorded_solved:'Recorded calculations completed',all_recorded_ready:'Recorded evidence ready',
  partial_or_blocked:'Incomplete or blocked',not_recorded:'Not recorded',not_established:'Not established'};
export function RunAssessment({run}:{run:RunSummaryView}){
  const state=run.scientific_assessment;
  return <dl aria-label="Independent run assessments" className="run-assessment">
    <dt>Job</dt><dd>{statusLabel(run.status)}</dd>
    <dt>Numerical checks</dt><dd>{labels[state.numerical_state]??'Not recorded'}</dd>
    <dt>Scientific evidence</dt><dd>{labels[state.evidence_state]??'Not recorded'}</dd>
    <dt>Experimental validation</dt><dd>{labels[state.experimental_validation]??'Not established'}</dd>
  </dl>;
}
