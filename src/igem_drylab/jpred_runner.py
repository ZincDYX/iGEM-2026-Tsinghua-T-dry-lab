"""Run the official JPred client, retaining remote job identity for retries."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from urllib.request import urlopen


def main():
    from Bio import SeqIO
    from .constructs.linker_features import parse_secondary_structure_output
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", required=True)
    parser.add_argument("--fasta", type=Path, required=True)
    parser.add_argument("--record", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--state-file", type=Path, help="Persistent per-node job identity across workflow attempts")
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
        run = subprocess.run(argv, capture_output=True, text=True, timeout=1800)
        (output / log).write_text(run.stdout + "\n" + run.stderr)
        run.check_returncode()
        return run.stdout
    version = invoke([args.client, "--version"], "client-version.log").strip()
    if state_file.exists():
        state = json.loads(state_file.read_text())
        if state["input_sha256"] != digest or state["client_version"] != version:
            raise ValueError("JPred saved remote job differs from current input/client")
    else:
        command = [args.client, "submit", "--mode=single", "--format=fasta",
                   "--file=" + str(args.fasta.resolve()), "--rest=" + rest]
        raw = invoke(command, "submit.log")
        jobs = set(re.findall(r"jp_[A-Za-z0-9]+", raw))
        if len(jobs) != 1 or "Accepted" not in raw:
            raise ValueError("JPred did not accept a unique real job; client exit zero is insufficient")
        state = dict(job_id=jobs.pop(), input_sha256=digest, client_version=version,
                     submit_command=command)
        state_file.write_text(json.dumps(state, indent=2))
    command = [args.client, "get_results", "--jobid=" + state["job_id"],
               "--results=" + str(output / "results"), "--extract", "--attempts=60", "--wait=10",
               "--rest=" + rest, "--jpred4=" + root]
    invoke(command, "retrieve.log")
    directory = output / "results" / state["job_id"]
    raw = directory / (state["job_id"] + ".jnet")
    companion = directory / (state["job_id"] + ".seq")
    retrieval_route = "official_client"
    if not raw.is_file() or not companion.is_file():
        # REST status sometimes returns an empty 200 for a finished job;
        # use that same job's published original files, not substitute data.
        directory.mkdir(parents=True, exist_ok=True)
        for target in (raw, companion):
            with urlopen(root + "/results/" + state["job_id"] + "/" + target.name, timeout=60) as response:
                target.write_bytes(response.read())
        retrieval_route = "published_original_result_files"
    tool_version = "JPred4; official client " + version
    record = dict(tool_name="JPred", tool_version=tool_version, origin="automated",
                  input_sha256=digest, output_sha256=sha256(raw.read_bytes()).hexdigest(),
                  command=command, returncode=0, job_id=state["job_id"],
                  retrieval_route=retrieval_route,
                  source=root + "/results/" + state["job_id"] + "/")
    raw.with_suffix(".run.json").write_text(json.dumps(record, indent=2))
    evidence = parse_secondary_structure_output(raw, tool_name="JPred", tool_version=tool_version,
                                               input_sha256=digest, sequence_file=companion)
    (output / "secondary.json").write_text(evidence.model_dump_json(indent=2))
    print(json.dumps(dict(job_id=state["job_id"], status="predicted_not_experiment", ss_fraction=evidence.ss_fraction)))


if __name__ == "__main__":
    main()
