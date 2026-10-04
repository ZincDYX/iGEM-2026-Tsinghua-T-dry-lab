# FusionLab frontend / desktop shell

Use Python >= 3.10 with the repository's `.[software]` dependencies, Node supported by Vite, and pnpm **10.30.3** (fixed in package.json).

```powershell
# Repository root
.venv/Scripts/python -m igem_drylab.cli software serve --port 8780 --data-dir outputs/platform

# A second terminal, in software/dashboard
pnpm install --frozen-lockfile
pnpm dev --host 127.0.0.1
```

`pnpm build` and `pnpm test` verify the frontend. `pnpm test:e2e` uses an existing Edge browser and dedicated local test services (ports 8789/5189). `FUSIONLAB_TEST_DATA` selects a test database directory; tests add their own projects and do not delete existing projects.

`pnpm desktop` starts the Tauri development shell. `pnpm desktop:build` builds with local frontend resources. Rust supervises the same Python backend, not another scientific implementation. Use `FUSIONLAB_PYTHON`, `FUSIONLAB_ROOT` and `FUSIONLAB_DATA_DIR` to select the source environment/data explicitly. Default source execution expects `.venv` at the repository root. Windows native build/start/close are tested; other OS native builds are unverified.

The default Scientist view hides raw workflows/configuration. Developer mode exposes typed bindings, dynamic shards, node errors, immutable snapshots and provenance. Natural-language task text is recorded, but this initial UI does not claim an LLM is connected. Sequence properties, declared assembly composition and the explicit supported pathway model can run without an LLM.

Full design, formula boundaries, license details and remaining features: [platform guide](../../docs/fusionlab_platform.md).
