"""Run the real public GFP sequence through stdio MCP and an independent oracle."""
import argparse
import asyncio
from hashlib import md5, sha256
import json
import math
import os
from pathlib import Path
import platform
import sys

from Bio import SeqIO
from Bio.SeqUtils.ProtParam import ProteinAnalysis
from mcp import Client
from mcp.client.stdio import StdioServerParameters


async def calculate(sequence):
    parameters = StdioServerParameters(command=sys.executable,
        args=['-B', '-m', 'igem_drylab.mcp.server'], env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    async with Client(parameters, read_timeout_seconds=60) as client:
        result = await client.call_tool('igem.m1.compute_features', {'sequence': sequence})
        if result.is_error:
            raise RuntimeError('Public case MCP calculation failed: '+str(result.content))
        return result.structured_content['result']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    case = Path(__file__).resolve().parents[1]/'examples/public_gfp'
    source = json.loads((case/'source.json').read_text())
    record = SeqIO.read(case/'P42212.fasta', 'fasta')
    sequence = str(record.seq)
    if len(sequence) != source['sequence_length'] or md5(sequence.encode()).hexdigest().upper() != source['source_sequence_md5']:
        raise ValueError('Case sequence differs from the original UniProt metadata.')
    features = asyncio.run(calculate(sequence))
    analysis = ProteinAnalysis(sequence)
    # ProtParam is an independent implementation of the same Kyte-Doolittle
    # mean, not a self-comparison or a biological experimental validation.
    if not math.isclose(features['mean_hydropathy'], analysis.gravy(), abs_tol=1e-12):
        raise ValueError('MCP result disagrees with independent Biopython GRAVY.')
    if features['length'] != len(sequence) or features['sequence_sha256'] != sha256(sequence.encode()).hexdigest():
        raise ValueError('MCP result belongs to a different sequence.')
    args.output.mkdir(parents=True, exist_ok=True)
    result = {'source': source, 'python': platform.python_version(),
              'calculation': 'real stdio MCP igem.m1.compute_features',
              'features': features, 'independent_protparam_gravy': analysis.gravy(),
              'oracle_passed': True, 'formal_m1_pass': False,
              'limits': ['No fusion, topology, LLPS, enzyme activity or complete M1–M4 validation is established.']}
    (args.output/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    report = ('# Public GFP sequence analysis\n\n'
        'Input: UniProt P42212, sequence version 1 (238 residues).\n\n'
        'Executed the real stdio MCP sequence-feature tool; the Kyte–Doolittle mean '
        'agrees with independent Biopython ProtParam.\n\n'
        f"Mean hydropathy: {features['mean_hydropathy']:.6f}. Net charge proxy: {features['net_charge_proxy']:.6f}.\n\n"
        'These are sequence descriptors, not a formal M1 pass or evidence of assembly, LLPS or activity.\n\n'
        'Data: [UniProt canonical FASTA](https://rest.uniprot.org/uniprotkb/P42212.fasta); '
        '[original sequence paper](https://doi.org/10.1016/0378-1119(92)90691-H).\n')
    (args.output/'REPORT.md').write_text(report, encoding='utf-8')
    print(json.dumps({'public_case': 'passed', 'actual_mcp': True, 'length': len(sequence), 'formal_m1_pass': False}))


if __name__ == '__main__':
    main()
