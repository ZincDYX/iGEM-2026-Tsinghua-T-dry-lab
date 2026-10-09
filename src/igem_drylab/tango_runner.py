"""Execute a user-authorized TANGO binary with explicit experimental settings."""
import argparse
from pathlib import Path
import subprocess


def main():
    from Bio import SeqIO
    from .constructs.linker_features import normalize_amino_acid_sequence
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executable",type=Path,required=True)
    parser.add_argument("--fasta",type=Path,required=True)
    parser.add_argument("--record",required=True)
    parser.add_argument("--output-dir",type=Path,required=True)
    parser.add_argument("--ph",type=float,required=True)
    parser.add_argument("--temperature-k",type=float,required=True)
    parser.add_argument("--ionic-strength-m",type=float,required=True)
    parser.add_argument("--ct",choices=("N","Y"),required=True)
    parser.add_argument("--nt",choices=("N","A","S"),required=True)
    args=parser.parse_args()
    if not 0<=args.ph<=14 or args.temperature_k<=0 or args.ionic_strength_m<0:
        parser.error("pH, Kelvin temperature and molar ionic strength must be physically valid")
    records=[r for r in SeqIO.parse(args.fasta,"fasta") if r.id==args.record]
    if len(records)!=1:
        raise ValueError("TANGO_requires_exactly_one_complete_input_record")
    sequence=normalize_amino_acid_sequence(str(records[0].seq))
    args.output_dir.mkdir(parents=True,exist_ok=True)
    argv=[str(args.executable.resolve()),"sequence_input",f"ct={args.ct}",f"nt={args.nt}",f"ph={args.ph}",
        f"te={args.temperature_k}",f"io={args.ionic_strength_m}",f"seq={sequence}"]
    completed=subprocess.run(argv,cwd=args.output_dir,capture_output=True,text=True,check=True)
    if not (args.output_dir/"sequence_input.out").is_file():
        raise ValueError("TANGO_returned_no_actual_per_residue_output")
    print(completed.stdout)


if __name__=="__main__":
    main()
