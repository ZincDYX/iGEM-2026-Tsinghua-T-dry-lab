import type { PrimaryCommand } from './workbenchCommands';
import { commandLabels } from './workbenchCommands';

/** Run/scope controls belong to Workflow, not the global toolbar or menus. */
export function WorkflowControls({primary, disabled, startDisabled, pausePending, executing, cancellable, retryable, canSelectStage, onPrimary, onPause, onCancel, onRetry, onStep, onTarget}: {
  primary: PrimaryCommand; disabled: boolean; startDisabled: boolean; pausePending: boolean; executing: boolean; cancellable: boolean; retryable: boolean; canSelectStage: boolean;
  onPrimary: () => void; onPause: () => void; onCancel: () => void; onRetry: () => void; onStep: () => void; onTarget: () => void;
}) {
  return <section className="workflow-run-controls" aria-label="Workflow run controls">
    <button disabled={disabled || primary === 'running' || primary === 'start' && startDisabled} onClick={onPrimary}>{commandLabels[primary]}</button>
    <button disabled={disabled || executing} onClick={onStep}>Review stage-by-stage plan</button>
    <button disabled={disabled || executing || !canSelectStage} onClick={onTarget}>Review run to selected stage</button>
    {executing && <button disabled={disabled || pausePending} onClick={onPause}>Pause run</button>}
    {cancellable && <button disabled={disabled} onClick={onCancel}>Cancel run</button>}
    {retryable && <button disabled={disabled} onClick={onRetry}>Retry selected node</button>}
  </section>;
}
