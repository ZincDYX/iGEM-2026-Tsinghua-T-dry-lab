import {fireEvent,render,screen} from '@testing-library/react';
import {expect,it,vi} from 'vitest';
import {WorkbenchMenus} from './WorkbenchMenus';

it('keeps one menu open and closes it on escape, outside click and selection',()=>{
  const action=vi.fn();
  const view=render(<WorkbenchMenus file={[{label:'Save fixture',action}]} view={[{label:'Show fixture',action}]} tools={[]} help={[]}/>);
  fireEvent.click(screen.getByText('File'));
  expect(view.container.querySelectorAll('details[open]')).toHaveLength(1);
  fireEvent.click(screen.getByText('View'));
  expect(view.container.querySelectorAll('details[open]')).toHaveLength(1);
  expect(screen.getByText('File').closest('details')?.hasAttribute('open')).toBe(false);
  fireEvent.keyDown(screen.getByText('View'),{key:'Escape'});
  expect(view.container.querySelectorAll('details[open]')).toHaveLength(0);
  fireEvent.click(screen.getByText('File'));
  fireEvent.click(screen.getByRole('menuitem',{name:'Save fixture'}));
  expect(action).toHaveBeenCalledOnce();
  expect(view.container.querySelectorAll('details[open]')).toHaveLength(0);
  fireEvent.click(screen.getByText('File'));
  fireEvent.pointerDown(document.body);
  expect(view.container.querySelectorAll('details[open]')).toHaveLength(0);
});
