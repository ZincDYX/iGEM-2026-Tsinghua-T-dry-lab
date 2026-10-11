import type { PrimaryCommand } from './workbenchCommands';
import { commandLabels } from './workbenchCommands';

/** Run/scope controls belong to Workflow, not the global toolbar or menus. */
export function WorkflowControls({primary, disabled, startDisabled,reviewDisabled=false, pausePending, executing, cancellable, retryable, frozen, onPrimary, onPause, onCancel, onRetry, onReview}: {
  primary: PrimaryCommand; disabled: boolean; startDisabled: boolean; pausePending: boolean; executing: boolean; cancellable: boolean; retryable: boolean; frozen: boolean;
  reviewDisabled?:boolean;
  onPrimary: () => void; onPause: () => void; onCancel: () => void; onRetry: () => void; onReview: () => void;
}) {
  return <section className="workflow-run-controls" aria-label="Workflow run controls">
    {(!frozen || primary === 'resume' || primary === 'running') && <button disabled={disabled || primary === 'running' || primary === 'start' && startDisabled || primary === 'review' && reviewDisabled} onClick={onPrimary}>{commandLabels[primary]}</button>}
    {!frozen && primary !== 'review' && <button disabled={disabled || executing || reviewDisabled} onClick={onReview}>Review plan</button>}
    {frozen && !executing && primary !== 'resume' && <p>Recorded run. Its workflow and execution settings are read-only.</p>}
    {executing && <button disabled={disabled || pausePending} onClick={onPause}>Pause run</button>}
    {cancellable && <button disabled={disabled} onClick={onCancel}>Cancel run</button>}
    {retryable && <button disabled={disabled} onClick={onRetry}>Retry selected node</button>}
  </section>;
}
