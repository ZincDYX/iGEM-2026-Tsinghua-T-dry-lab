"""Normal original FuzDrop form use; no CAPTCHA solving or token injection.

Run in an optional private browser environment. Save the submission intent and
native response before interpretation; unknown submissions are not repeated.
"""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import shutil
import sys

from .jpred_runner import _save_state


def _previous_response(state_file, protocol, digest):
    if not state_file.exists():
        return None
    state=json.loads(state_file.read_text())
    if state['protocol']!=protocol or state['input_sha256']!=digest:
        raise ValueError('FuzDrop_saved_submission_identity_mismatch')
    if state['status']=='prepared' and not state.get('response_file'):
        # This durable state precedes both the normal page visit and the POST
        # intent. A failed page visit is not an unknown accepted submission.
        return None
    if not state.get('response_file') or not Path(state['response_file']).is_file():
        raise ValueError('FuzDrop_submission_unknown_reconcile_do_not_resubmit')
    if state.get('http_status')!=200:
        raise ValueError('FuzDrop_official_form_failed_or_requires_human_verification')
    return Path(state['response_file'])


def _open_form(page):
    # Deferred external resources can delay DOMContentLoaded while the actual
    # official form is already interactive. Commit + visible input is required.
    page.goto('https://fuzdrop.bio.unipd.it/',wait_until='commit',timeout=60000)
    page.locator('#floatingTextarea2').wait_for(state='visible',timeout=180000)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fasta',type=Path,required=True)
    parser.add_argument('--record',required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--state-file',type=Path,required=True)
    args=parser.parse_args()
    lines=[line.strip() for line in args.fasta.read_text().splitlines() if line.strip()]
    if not lines or lines[0]!='>'+args.record or any(line.startswith('>') for line in lines[1:]):
        raise ValueError('FuzDrop_requires_one_exact_FASTA_record')
    sequence=''.join(lines[1:])
    if len(sequence)<45 or set(sequence)-set('ACDEFGHIKLMNPQRSTVWY'):
        raise ValueError('FuzDrop_requires_at_least_45_standard_residues_no_padding')
    digest=sha256(sequence.encode()).hexdigest()
    output=args.output_dir.resolve();output.mkdir(parents=True,exist_ok=True)
    state_file=args.state_file.resolve();state_file.parent.mkdir(parents=True,exist_ok=True)
    protocol='fuzdrop-original-official-form-v1'
    raw=_previous_response(state_file,protocol,digest)
    if raw is not None:
        state=json.loads(state_file.read_text())
    else:
        from playwright.sync_api import sync_playwright
        raw=output/'fuzdrop.json'
        state=dict(protocol=protocol,input_sha256=digest,status='prepared')
        _save_state(state_file,state)
        with sync_playwright() as playwright:
            browser=playwright.chromium.launch(headless=True)
            page=None
            try:
                page=browser.new_page()
                _open_form(page)
                page.locator('#floatingTextarea2').fill('>'+args.record+'\n'+sequence+'\n')
                state['status']='submitting';_save_state(state_file,state)
                with page.expect_response(lambda r: r.url=='https://fuzpred.bio.unipd.it/api/submit_protein',timeout=600000) as pending:
                    page.get_by_role('button',name='Submit',exact=True).click()
                response=pending.value
                raw.write_bytes(response.body())  # Retain original bytes, including failures.
                state['response_file']=str(raw);state['http_status']=response.status
                state['status']='response_saved';_save_state(state_file,state)
                if response.status!=200:
                    raise ValueError('FuzDrop_official_form_failed_or_requires_human_verification')
            finally:
                # Private native page diagnostics help reconcile a failed form;
                # do not export embedded job tokens or retry unknown POSTs.
                if page is not None and not page.is_closed():
                    (output/'official-page-private.html').write_text(page.content())
                    page.screenshot(path=str(output/'official-page-private.png'),full_page=True)
                browser.close()
    data=json.loads(raw.read_text())
    if data.get('sequence')!=sequence or not isinstance(data.get('result'),list) or 'pLLPS' not in data:
        raise ValueError('FuzDrop_native_response_not_complete_for_exact_input')
    score=float(data['pLLPS'])
    if not math.isfinite(score) or not 0<=score<=1:
        raise ValueError('FuzDrop_native_global_probability_invalid')
    target=output/'fuzdrop.json'
    if raw!=target:shutil.copyfile(raw,target)
    record=dict(tool_name='FuzDrop',tool_version=protocol,origin='automated',returncode=0,
        command=[sys.executable,*sys.argv],input_sha256=digest,output_sha256=sha256(target.read_bytes()).hexdigest(),
        native_format='fuzdrop_response_json',source_reference='https://fuzdrop.bio.unipd.it/',
        native_binary_version=None,service_protocol_version=protocol,
        version_scope='Observed original website protocol; server binary version not exposed.')
    target.with_suffix('.run.json').write_text(json.dumps(record,indent=2))
    state['status']='native_response_saved_not_scientific_acceptance';_save_state(state_file,state)
    print(json.dumps(dict(status=state['status'],input_length=len(sequence))))


if __name__=='__main__':main()
