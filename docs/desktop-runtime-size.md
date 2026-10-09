# Desktop runtime selection

The portable application includes the declared backend dependencies and the
`software` extra from `pyproject.toml`, plus their transitive requirements. The
release builder resolves installed wheel metadata, including platform and extra
markers, and copies their RECORD-owned runtime files. It does not copy the whole
development environment. Missing wheels or incompatible versions fail packaging.

Native NumPy/SciPy libraries, runtime data, public `numpy.testing` APIs,
distribution metadata and licenses remain included. Only the upstream NumPy/SciPy
`tests` directories and unselected development distributions are omitted.
`venv` and `ensurepip` remain available for isolated plugin environments.
On Windows embedded Python, each managed plugin has its own interpreter DLL and
`._pth` configuration: only standard-library paths are shared with the parent,
not the application's dependencies or source. Existing plugins made with the
old inherited-path launcher must be reinstalled before execution. Reinstall
repairs the launcher while preserving their own installed dependency files.
Scientific formulas, solver settings, sampling budgets and evidence requirements
are not changed by this selection.

SciPy solver/statistics/spatial imports occur when their calculation is requested,
not when a typed configuration or tool catalog is opened. The existing pipeline
exports remain available without importing the stage implementations for every
configuration import. This is import scheduling, not a second execution engine.

Native desktop startup waits at most 60 seconds for the actual backend readiness
message. This does not bypass authentication or advertise readiness before ASGI
initialization. Packaging import checks and the owned native desktop smoke test
must still pass. Measurements must name the machine/build and distinguish cached
startup timings from an actual cold-disk benchmark.
