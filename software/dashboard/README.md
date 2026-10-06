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

`pnpm desktop` starts the Tauri development shell. `pnpm desktop:build` builds with local frontend resources. Desktop mode defaults to **local**, without any built-in server. Rust supervises the same Python backend, not another scientific implementation. A portable distribution uses sibling `python/python.exe` and `resources/src`; source development expects `.venv` at the repository root. `FUSIONLAB_PYTHON`, `FUSIONLAB_ROOT` and `FUSIONLAB_DATA_DIR` explicitly select the environment/source/data when needed.

The desktop Settings page offers an optional SSH backend. Users supply their own SSH alias and remote API port, save, then restart. Settings are stored in the user's application data directory, never the repository. OpenSSH uses existing authentication/known_hosts and refuses unknown/changed host keys; private keys are never packaged. The desktop owns only its tunnel, not the remote backend, and does not start remote services. Closing the desktop ends its own local backend/process group or its own tunnel. No previous browser/port-forward process is required.

Build a portable Windows package with `scripts/package_windows_desktop.py` using a byte-exact committed source tar, an official CPython Windows embeddable archive, a matching ABI dependency directory and the built native exe. Preserve `FusionLab.exe`, `python` and `resources` together; this is a portable folder/ZIP, not a single-file runtime or signed installer. WebView2 is required. Licensed predictors, GPU weights and private project data are not distributed; unavailable jobs retain explicit errors. Other OS native builds are unverified.

The default Scientist view hides raw workflows/configuration. Developer mode exposes typed bindings, dynamic shards, node errors, immutable snapshots and provenance. Natural-language task text is recorded, but this initial UI does not claim an LLM is connected. Sequence properties, declared assembly composition and the explicit supported pathway model can run without an LLM.

Full design, formula boundaries, license details and remaining features: [platform guide](../../docs/fusionlab_platform.md).
