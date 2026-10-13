import {useState} from 'react';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import type {ProjectView,ModuleMethodView} from '../contracts/generated';
import {ModuleParameters} from './ModuleParameters';
afterEach(cleanup);
// Admission/editor fixture, not measured biological evidence or a numerical oracle.
const parameter={parameter_id:'software',name:'declared',value:5,unit:'s^-1',source_type:'wetlab',source_reference:'SOFTWARE_ONLY',
  review_status:'approved',approved_by:'SOFTWARE_REVIEW',validation_flags:['SOFTWARE_REVIEW'],parameter_version:1,
  derivation_type:'direct_measurement',derived_from:[],notes:'Fixture',construct_id:null,condition_id:null};
const project={id:'SOFTWARE_EDITOR_SAMPLE',scientific_project:{config:{parameters:[parameter]}}} as unknown as ProjectView;
const method={parameter_records:[parameter],parameter_requirements:[],parameter_source_options:{},methods:[]} as unknown as ModuleMethodView;
it('empty value is not zero; a new version retains the immutable original and cannot inherit its approval',async()=>{
  const changed=vi.fn();
  function Editor(){const [draft,setDraft]=useState(project);return <ModuleParameters project={draft} method={method} frozen={false} onScalarChange={async()=>{}} onChange={async value=>{changed(value);setDraft(value);}}/>;}
  render(<Editor/>);fireEvent.click(screen.getByRole('button',{name:'Edit declared'}));
  fireEvent.change(screen.getByLabelText('Value for declared'),{target:{value:''}});
  fireEvent.click(screen.getByRole('button',{name:'Save parameter'}));
  expect(changed).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText('Value for declared'),{target:{value:'0'}});
  fireEvent.click(screen.getByRole('button',{name:'Save parameter'}));
  await vi.waitFor(()=>expect(screen.queryByLabelText('Value for declared')).toBeNull());
  const records=changed.mock.calls[0][0].scientific_project.config.parameters;
  expect(records[0]).toEqual(parameter);
  expect(records[1]).toMatchObject({value:0,unit:'s^-1',review_status:'extracted',approved_by:null,validation_flags:['requires_human_approval_before_model_use'],parameter_version:2,supersedes:'software',source_reference:'SOFTWARE_ONLY'});
});
it('derived and frozen values have no override controls or irrelevant metadata form',()=>{
  render(<ModuleParameters project={project} method={{...method,parameter_records:[{...parameter,derivation_type:'model_fit',derived_from:['observed']} ]}} frozen={false} onChange={async()=>{}} onScalarChange={async()=>{}}/>);
  expect(screen.getByText(/calculated result/)).toBeTruthy();
  expect(screen.queryByRole('button',{name:'Edit declared'})).toBeNull();
  expect(screen.queryByRole('button',{name:'Choose existing source'})).toBeNull();
  expect(screen.queryByLabelText(/DOI|review status|timestamp/i)).toBeNull();
});
