"""Run JPred's REST service through jpredapi, retaining job identity for retries."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.request import urlopen
from urllib.error import HTTPError, URLError


def _save_state(path, state):
    """Atomic durable intent/acknowledgement; never overwrite with partial JSON."""
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(state, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def _accepted_job(raw):
    jobs = set(re.findall(r"jp_[A-Za-z0-9]+", raw))
    if len(jobs) != 1 or "Accepted" not in raw:
        raise ValueError("JPred did not accept a unique real job; client exit zero is insufficient")
    return jobs.pop()


def main():
    from Bio import SeqIO
    from .constructs.linker_features import parse_secondary_structure_output
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", required=True)
    parser.add_argument("--fasta", type=Path, required=True)
    parser.add_argument("--record", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--state-file", type=Path, help="Persistent per-node job identity across workflow attempts")
    parser.add_argument("--poll-once", action="store_true", help="Return waiting without holding a worker for remote computation")
    args = parser.parse_args()
    records = list(SeqIO.parse(args.fasta, "fasta"))
    if len(records) != 1 or records[0].id != args.record:
        raise ValueError("JPred requires exactly one selected full FASTA record")
    sequence = str(records[0].seq)
    if not 20 <= len(sequence) <= 800:
        raise ValueError("JPred sequence length must be 20–800; no padding is permitted")
    digest = sha256(sequence.encode()).hexdigest()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    rest = "https://www.compbio.dundee.ac.uk/jpred4/cgi-bin/rest"
    root = "https://www.compbio.dundee.ac.uk/jpred4"
    state_file = args.state_file.resolve() if args.state_file else output / "remote-job.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    def invoke(argv, log):
        run = subprocess.run(argv, capture_output=True, text=True, timeout=60 if args.poll_once else 1800)
        (output / log).write_text(run.stdout + "\n" + run.stderr)
        run.check_returncode()
        return run.stdout
    version = invoke([args.client, "--version"], "client-version.log").strip()
    if state_file.exists():
        state = json.loads(state_file.read_text())
        if state["input_sha256"] != digest or state["client_version"] != version:
            raise ValueError("JPred saved remote job differs from current input/client")
        if not state.get("job_id"):
            # A process may die after recording the response but before the ack.
            # Reconcile only its own original log; never send another POST.
            log = Path(state["acknowledgement_log"])
            if log.is_file():
                try:
                    state["job_id"] = _accepted_job(log.read_text())
                except ValueError:
                    pass
            if not state.get("job_id"):
                state["status"] = "submission_unknown"
                _save_state(state_file, state)
                raise ValueError("JPred submission acknowledgement unknown; reconcile the original job, do not resubmit")
            state["status"] = "submitted"
            _save_state(state_file, state)
    else:
        command = [args.client, "submit", "--mode=single", "--format=fasta",
                   "--file=" + str(args.fasta.resolve()), "--rest=" + rest]
        state = dict(protocol="jpred-known-job-v2", status="submitting", input_sha256=digest, client_version=version,
                     submit_command=command, acknowledgement_log=str(output / "submit.log"))
        _save_state(state_file, state)  # MUST precede the non-idempotent POST.
        try:
            raw = invoke(command, "submit.log")
            state["job_id"] = _accepted_job(raw)
        except Exception:
            state["status"] = "submission_unknown"
            _save_state(state_file, state)
            raise
        state["status"] = "submitted"
        _save_state(state_file, state)
    command = [args.client, "get_results", "--jobid=" + state["job_id"],
               "--results=" + str(output / "results"), "--extract", "--attempts=" + ("1" if args.poll_once else "60"), "--wait=10",
               "--rest=" + rest, "--jpred4=" + root]
    state["status"] = "retrieving"
    _save_state(state_file, state)
    invoke(command, "retrieve.log")
    directory = output / "results" / state["job_id"]
    raw = directory / (state["job_id"] + ".jnet")
    companion = directory / (state["job_id"] + ".seq")
    retrieval_route = "jpredapi_python_client"
    if not raw.is_file() or not companion.is_file():
        # REST status sometimes returns an empty 200 for a finished job;
        # use that same job's published original files, not substitute data.
        directory.mkdir(parents=True, exist_ok=True)
        for target in (raw, companion):
            try:
                with urlopen(root + "/results/" + state["job_id"] + "/" + target.name, timeout=60) as response:
                    target.write_bytes(response.read())
            except (HTTPError, URLError, TimeoutError) as error:
                if not args.poll_once or isinstance(error, HTTPError) and error.code not in {404, 429, 500, 502, 503, 504}:
                    raise
                state["status"] = "waiting_for_result"
                _save_state(state_file, state)
                print(json.dumps(dict(job_id=state["job_id"], status="waiting_for_result")))
                return
        retrieval_route = "published_original_result_files"
    tool_version = "JPred4; jpredapi Python client " + version
    record = dict(tool_name="JPred", tool_version=tool_version, origin="automated",
                  input_sha256=digest, output_sha256=sha256(raw.read_bytes()).hexdigest(),
                  command=command, returncode=0, job_id=state["job_id"],
                  retrieval_route=retrieval_route,
                  source=root + "/results/" + state["job_id"] + "/")
    raw.with_suffix(".run.json").write_text(json.dumps(record, indent=2))
    state["status"] = "parsing"
    _save_state(state_file, state)
    evidence = parse_secondary_structure_output(raw, tool_name="JPred", tool_version=tool_version,
                                               input_sha256=digest, sequence_file=companion)
    (output / "secondary.json").write_text(evidence.model_dump_json(indent=2))
    state["status"] = "validated_not_published"
    _save_state(state_file, state)
    print(json.dumps(dict(job_id=state["job_id"], status="predicted_not_experiment", ss_fraction=evidence.ss_fraction)))


if __name__ == "__main__":
    main()
