import {cleanup,render,screen,waitFor} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {UnifiedImport} from './UnifiedImport';
import {newProject} from './useProject';
import * as client from './client';
vi.mock('./client',()=>({pendingImports:vi.fn()}));
afterEach(()=>{cleanup();vi.resetAllMocks();});

it('does not query an unsaved project; starts recovery only after it exists without resetting import state',async()=>{
  const project=newProject();
  const props={project,busy:false,dirty:true,action:async(job:()=>Promise<unknown>)=>{await job();},prepare:async()=>project,onCommitted:vi.fn()};
  vi.mocked(client.pendingImports).mockResolvedValue(['saved-preview']);
  const {rerender}=render(<UnifiedImport {...props} persisted={false}/>);
  expect(client.pendingImports).not.toHaveBeenCalled();
  expect(screen.queryByRole('alert')).toBeNull();
  rerender(<UnifiedImport {...props} persisted/>);
  await screen.findByRole('button',{name:'Resume saved import 1'});
  expect(client.pendingImports).toHaveBeenCalledExactlyOnceWith(project.id);
});

it('still reports a genuine saved-project recovery failure',async()=>{
  const project=newProject();
  vi.mocked(client.pendingImports).mockRejectedValue(Error('actual request failed'));
  render(<UnifiedImport project={project} persisted busy={false} dirty={false} action={async()=>{}} prepare={async()=>project} onCommitted={vi.fn()}/>);
  await waitFor(()=>expect(screen.getByRole('alert').textContent).toContain('Saved import previews could not be loaded'));
});
