"""Original catGRANULE web-form driver, with durable known-job recovery.

This is the observed official form protocol, not a documented public API or
local model. Never send another submission after an ambiguous acknowledgement.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit, urlunsplit, urljoin

import requests
from Bio import SeqIO

from .jpred_runner import _save_state
from .llps_artifacts import read_native_llps


def _accepted(response):
    url = response["url"]
    parts = urlsplit(url)
    if parts.hostname != "crg-webservice.s3.amazonaws.com" or not parts.path.startswith("/submissions/"):
        raise ValueError("catGRANULE_unrecognized_original_result_host")
    return str(response["task_id"]), urlunsplit(("https", parts.netloc, parts.path, parts.query, ""))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fasta", required=True, type=Path)
    parser.add_argument("--record", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--state-file", required=True, type=Path)
    args = parser.parse_args()
    records = list(SeqIO.parse(args.fasta, "fasta"))
    if len(records) != 1 or records[0].id != args.record:
        raise ValueError("catGRANULE_requires_one_exact_input_record")
    sequence = str(records[0].seq)
    if any(aa not in "ACDEFGHIKLMNPQRSTVWY" for aa in sequence):
        raise ValueError("catGRANULE_requires_standard_amino_acids")
    digest = sha256(sequence.encode()).hexdigest()
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=True)
    state_file = args.state_file.resolve(); state_file.parent.mkdir(parents=True, exist_ok=True)
    protocol = "catgranule2016-official-form-v1"
    if state_file.is_file():
        state = json.loads(state_file.read_text())
        if state["protocol"] != protocol or state["input_sha256"] != digest:
            raise ValueError("catGRANULE_saved_job_input_or_protocol_changed")
        if not state.get("job_id"):
            ack = Path(state["acknowledgement_file"])
            if ack.is_file():
                state["job_id"], state["result_url"] = _accepted(json.loads(ack.read_text()))
                _save_state(state_file, state)
            else:
                raise ValueError("catGRANULE_submission_unknown_do_not_resubmit")
    else:
        ack = output/"acknowledgement.json"
        state = dict(protocol=protocol, input_sha256=digest, status="submitting", acknowledgement_file=str(ack))
        _save_state(state_file, state)
        attributes = dict(email="", algorithm="catGRANULES", submission_title="FusionLab original IDR",
            protein_seq=f">{args.record}\n{sequence}\n", command="catGRANULES.py -text=Yes -output_dir=<output_dir>",
            type_submit="text", title="FusionLab original IDR", type_algorithm="old")
        (output/"request.json").write_text(json.dumps(attributes, indent=2))
        response = requests.post("https://tools.tartaglialab.com/form_submit",
            files={"type_submit": (None, "text"), "attributes": (None, json.dumps(attributes))}, timeout=(10, 40))
        ack.write_bytes(response.content)
        response.raise_for_status()
        state["job_id"], state["result_url"] = _accepted(response.json())
        state["status"] = "submitted"; _save_state(state_file, state)
    index = requests.get(state["result_url"], timeout=(10, 30))
    index.raise_for_status(); (output/"native-index.html").write_bytes(index.content)
    if 'scores.txt' not in index.text:
        state["status"] = "waiting_for_result"; _save_state(state_file, state)
        print(json.dumps({"job_id": state["job_id"], "status": state["status"]}))
        return
    for name in ("prot.fa", "scores.txt", "profiles.txt"):
        response = requests.get(urljoin(state["result_url"], name), timeout=(10, 30))
        response.raise_for_status(); (output/name).write_bytes(response.content)
    native = read_native_llps(output/"scores.txt", format="catgranule2016_scores",
        sequence=sequence, sequence_file=output/"prot.fa", record_id=args.record)
    record = dict(tool_name="catGRANULE_2016", tool_version=protocol, origin="automated", returncode=0,
        command=[sys.executable, *sys.argv], input_sha256=digest, output_sha256=sha256((output/"scores.txt").read_bytes()).hexdigest(),
        native_format="catgranule2016_scores", sequence_file=str(output/"prot.fa"), record_id=args.record,
        job_id=state["job_id"], version_scope="Observed original service protocol; server model binary version not exposed.")
    (output/"scores.run.json").write_text(json.dumps(record, indent=2))
    state["status"] = "validated_not_published"; _save_state(state_file, state)
    print(json.dumps({"job_id": state["job_id"], "raw_score": native["raw_score"], "status": state["status"]}))


if __name__ == "__main__":
    main()
