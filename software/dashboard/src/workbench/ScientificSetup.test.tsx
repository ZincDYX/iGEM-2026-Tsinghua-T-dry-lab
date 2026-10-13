import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import type {ProjectView} from '../contracts/generated';
import {ConstructObject} from './ScientificInputForms';
afterEach(cleanup);
const records=['A','B'].map(construct_id=>({construct_id,host:'original host',review_status:'approved',m1_review:{decision:'approved'}}));
const project={id:'SOFTWARE_ONLY',scientific_project:{config:{inputs:{constructs:[],construct_records:records}}}} as unknown as ProjectView;
it('editing only the selected construct clears its review, without mutating other evidence or the saved project',()=>{
  const change=vi.fn();
  render(<ConstructObject project={project} selected="record:A" onChange={change}/>);
  expect(screen.queryByLabelText('Construct host')).toBeNull();
  fireEvent.click(screen.getByRole('button',{name:'Correct declaration'}));
  fireEvent.change(screen.getByLabelText('Construct host'),{target:{value:'new host'}});
  const updated=change.mock.calls[0][0].scientific_project.config.inputs.construct_records;
  expect(updated[0]).toEqual({...records[0],host:'new host',review_status:'extracted',m1_review:null});
  expect(updated[1]).toEqual(records[1]);
  expect(project.scientific_project!.config.inputs.construct_records).toEqual(records);
});
it('viewing a different construct retains the approval attached to its identity and does not open a schema form',()=>{
  const change=vi.fn(),view=render(<ConstructObject project={project} selected="record:B" onChange={change}/>);
  expect(screen.getByText(/Host: original host — approved/)).toBeTruthy();
  view.rerender(<ConstructObject project={project} selected="record:A" onChange={change}/>);
  expect(screen.getByRole('heading',{name:'A'})).toBeTruthy();
  expect(change).not.toHaveBeenCalled();
  expect(screen.queryByRole('textbox')).toBeNull();
});
