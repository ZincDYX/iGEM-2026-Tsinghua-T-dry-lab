import {cleanup, fireEvent, render, screen} from '@testing-library/react';
import {afterEach, expect, it, vi} from 'vitest';
import {WorkflowControls} from './WorkflowControls';
afterEach(cleanup);
const actions = {onPrimary:vi.fn(),onPause:vi.fn(),onCancel:vi.fn(),onRetry:vi.fn(),onReview:vi.fn()};
const state = {disabled:false,startDisabled:false,pausePending:false,executing:false,cancellable:false,retryable:false,frozen:false};

it('one Review plan is shown alongside checking or starting, without stage-review shortcuts',()=>{
  render(<WorkflowControls {...actions} {...state} primary="check"/>);
  fireEvent.click(screen.getByRole('button',{name:'Review plan'}));
  expect(actions.onReview).toHaveBeenCalledOnce();
  expect(screen.getAllByRole('button').map(button=>button.textContent)).toEqual(['Check inputs','Review plan']);
  cleanup();
  render(<WorkflowControls {...actions} {...state} primary="review"/>);
  expect(screen.getAllByRole('button',{name:'Review plan'})).toHaveLength(1);
});

it('a recorded run cannot expose draft review or start actions, even if another proposal is accepted',()=>{
  render(<WorkflowControls {...actions} {...state} primary="start" frozen/>);
  expect(screen.queryByRole('button')).toBeNull();
  expect(screen.getByText('Recorded run. Its workflow and execution settings are read-only.')).toBeTruthy();
});

it('review waits for the selected workflow without disabling input checks',()=>{
  render(<WorkflowControls {...actions} {...state} primary="check" reviewDisabled/>);
  expect(screen.getByRole('button',{name:'Review plan'})).toHaveProperty('disabled',true);
  expect(screen.getByRole('button',{name:'Check inputs'})).toHaveProperty('disabled',false);
  cleanup();
  render(<WorkflowControls {...actions} {...state} primary="review" reviewDisabled/>);
  expect(screen.getByRole('button',{name:'Review plan'})).toHaveProperty('disabled',true);
});

it('frozen active and recoverable runs retain only their actual control actions',()=>{
  render(<WorkflowControls {...actions} {...state} primary="running" frozen executing cancellable pausePending/>);
  expect(screen.getByRole('button',{name:'Pause run'})).toHaveProperty('disabled',true);
  fireEvent.click(screen.getByRole('button',{name:'Cancel run'}));
  expect(actions.onCancel).toHaveBeenCalledOnce();
  expect(screen.queryByRole('button',{name:'Review plan'})).toBeNull();
  cleanup();
  render(<WorkflowControls {...actions} {...state} primary="resume" frozen/>);
  expect(screen.getByRole('button',{name:'Resume run'})).toHaveProperty('disabled',false);
});
