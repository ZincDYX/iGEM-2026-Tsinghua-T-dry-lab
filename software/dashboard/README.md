# FusionLab frontend and desktop shell

Use the [root README](../../README.md) for supported versions, locked installation,
build and public-case commands. The single [evidence index](../../docs/best_software_evidence.md)
records actual verification and remaining limitations.

From this directory: pnpm install --frozen-lockfile, pnpm dev --host 127.0.0.1,
pnpm test and pnpm build. Start the Python backend separately for browser
development. pnpm test:e2e uses the maintained HTTP/workbench configuration
and an existing Edge browser; FUSIONLAB_TEST_DATA selects a dedicated test
database. Legacy scientific browser fixtures are a separate configuration.

pnpm desktop is native development; pnpm desktop:build embeds production assets.
The root release entry uses cargo build --release --locked --features
custom-protocol, then the existing portable packager. Plain release without
custom-protocol is not the packaged desktop. Preserve FusionLab.exe, python
and resources together. WebView2 is required; other OS builds are unverified.

Desktop defaults to Local with its owned Python backend and SQLite.
Optional remote settings use an existing compatible HTTPS API and access token,
not SSH. Settings stay in user application data. Windows DPAPI protects tokens;
private CA PEM is explicit. Closing stops owned local processes, not remote services.

The frontend calls the same backend methods and displays typed objects.
Unknown evidence stays unknown. Licensed predictors, GPU weights and private
data are not bundled. Optional LLM proposals do not replace scientific review.

Project-authored frontend/native code: Apache-2.0. Third-party attribution:
[THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt).
