# Original Mpipi (2021)

The original author code is public at [Figshare](https://doi.org/10.6084/m9.figshare.16772812)
and [Cambridge's author deposit](https://www.repository.cam.ac.uk/items/35c30a45-f343-4fa2-bf85-6aa2984d1169).
Use the direct file URL recorded in `third_party/README.md`; an inaccessible metadata API
does not establish that the source archive is unavailable. Do not substitute Mpipi-Recharged.

Build LAMMPS **patch_10Mar2021**, enabling **USER-MISC** and **MOLECULE**, exactly as the
author's README specifies. The installed deployment needs the compiled executable and
the selected inputs; example trajectories/build intermediates are not model weights.
Keep licensed/private infrastructure and command configuration outside the repository.

The backend runner `python -m igem_drylab.mpipi --executable <original-lammps>
--archive <verified-supporting-code.zip> --case <rg|coexistence> --output-dir <new-job-directory>`
copies the author's inputs byte-for-byte and runs their complete requested steps:

An MPI build can use explicit `--mpi-executable <mpiexec> --mpi-ranks <ranks>`;
the rank count is a deployment choice, not a changed model parameter. The author
warns that parallel random-seed streams need not yield identical trajectories.

- `rg`: K25, 500,000,000 steps; the author reference reports about 7 hours on four MPI ranks.
- `coexistence`: hnRNPA1, 500,000 equilibration plus 4,000,000 production steps. The README
  says 300 K, while its actual script sets **310 K**. We retain 310 K and report the discrepancy;
  changing it requires a separately documented method decision.

`simulation.mpipi_original` uses the existing persistent engine and private `mpipi` ToolConfig.
Its command template runs the above module with `--case {case}` and `--output-dir {output_dir}`;
the executable/archive are backend deployment constants, not executable browser inputs.
It is non-idempotent: an interrupted scientific simulation is not blindly rerun, and
workflow-state recovery must not be called scientific checkpoint continuation. The
original Rg script writes native restart files; a reviewed continuation protocol is still
needed before using them. Timeout stops the wrapper's owned native process tree.

`igem.m1.parse_mpipi` is a real stdio MCP parser. `origin=author_reference` explicitly labels
the author's supplied output; `origin=executed_job` requires an actual matching execution
record and unchanged input bytes. It retains mass-weighted gyration in angstrom and
chunk mass density in g/cm³. A requested equilibration window requires an explicit
analysis source; it does not manufacture a confidence interval from correlated frames.
Phase-region averaging, conversion to project concentration, and an M1 ranking score
are not guessed. Partial exports/time-limited runs are not reported as complete.

The native tests use the actual original binary and unmodified author interaction table.
They independently check analytic Wang–Frenkel energy and force, original Debye screening,
non-default exponent order, last coefficient override, charge signs and cutoffs.
Set `FUSIONLAB_ORIGINAL_LAMMPS` and `FUSIONLAB_MPIPI_ARCHIVE` in the server test environment.
These are **run-0 force-field verification tests**, not shortened reproductions of the
author's long simulations or evidence that the project's fusion construct forms LLPS.
CI explicitly skips native verification when these optional external artifacts are absent;
the separate server tool run must show those tests actually passed.

Project simulation still requires explicit sequence/type mapping, temperature, screening,
concentration/chain count, box, time, independent seeds, equilibration/phase-region policy,
and the definition of the scalar used by the original M1 ranking. Author benchmark
conditions are not automatically transferred to a fusion construct.
