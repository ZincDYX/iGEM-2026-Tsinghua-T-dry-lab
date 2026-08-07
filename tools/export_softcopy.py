#!/usr/bin/env python3
import argparse
import datetime as dt
import os
from pathlib import Path
from typing import List, Tuple

ENC = 'utf-8'

EXCLUDES = {'.git', '__pycache__', '.venv', 'venv', 'env', 'site-packages', '.mypy_cache', '.pytest_cache'}

def list_py_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for p in root.rglob('*.py'):
        parts = set(p.parts)
        if any(ex in parts for ex in EXCLUDES):
            continue
        files.append(p)
    files.sort()
    return files

def read_file_lines(p: Path) -> List[str]:
    try:
        text = p.read_text(encoding=ENC, errors='ignore')
        # normalize to \n endings in memory
        return text.splitlines()
    except Exception:
        return []

def build_flat_lines(files: List[Path], root: Path) -> Tuple[List[str], List[Tuple[str, int]]]:
    flat: List[str] = []
    counts: List[Tuple[str, int]] = []
    for fp in files:
        rel = str(fp.relative_to(root))
        lines = read_file_lines(fp)
        counts.append((rel, len(lines)))
        header = f"==== FILE: {rel} ===="
        flat.append(header)
        for i, line in enumerate(lines, 1):
            flat.append(f"{i:6d}: {line}")
        flat.append("")
    return flat, counts

def paginate(flat: List[str], lpp: int, front_pages: int, back_pages: int) -> List[str]:
    total_lines = len(flat)
    front_n = min(front_pages * lpp, total_lines)
    back_n = min(back_pages * lpp, max(0, total_lines - front_n))
    front = flat[:front_n]
    back = flat[-back_n:] if back_n > 0 else []
    out: List[str] = []
    pg = 1
    def add_pages(block: List[str], label: str, start_pg: int) -> int:
        nonlocal out
        pg = start_pg
        for i in range(0, len(block), lpp):
            page = block[i:i+lpp]
            out.append(f"\f\n--- {label} PAGE {pg} ---")
            out.extend(page)
            pg += 1
        return pg
    pg = add_pages(front, 'FRONT', pg)
    add_pages(back, 'BACK', pg)
    return out

def write_text(path: Path, lines: List[str]):
    path.write_text('\n'.join(lines) + '\n', encoding=ENC)

def main():
    ap = argparse.ArgumentParser(description='Export Python sources to softcopy print (front+back pages).')
    ap.add_argument('--root', default='.', help='project root path')
    ap.add_argument('--lpp', type=int, default=50, help='lines per page')
    ap.add_argument('--front', type=int, default=30, help='number of front pages')
    ap.add_argument('--back', type=int, default=30, help='number of back pages')
    ap.add_argument('--outdir', default='docs/softcopy', help='output directory')
    args = ap.parse_args()

    root = Path(args.root).resolve()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    files = list_py_files(root)
    # prioritize our package first
    files = [p for p in files if 'CatalystOptimizationSystem' in p.parts] + [p for p in files if 'CatalystOptimizationSystem' not in p.parts]

    flat, counts = build_flat_lines(files, root)
    now = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # write counts
    counts_lines = [f"{rel}\t{n}" for rel, n in counts]
    write_text(outdir / 'Line_Counts.txt', counts_lines)

    # write full
    header = [
        f"Export Time: {now}",
        f"Root: {root}",
        f"Files: {len(files)}",
        f"Total Lines: {len(flat)}",
        f"LPP: {args.lpp}",
        "",
    ]
    write_text(outdir / 'Source_Full.txt', header + flat)

    # write front+back
    fb = paginate(flat, args.lpp, args.front, args.back)
    fb_header = header + [f"Front Pages: {args.front}", f"Back Pages: {args.back}", ""]
    write_text(outdir / 'Source_Pages_FrontBack.txt', fb_header + fb)

    print(f"Done. Files written to {outdir}")

if __name__ == '__main__':
    main()
