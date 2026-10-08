import { useEffect, useState } from "react";
import * as api from "./api";

export function DesktopConnectionPanel() {
  const [settings, setSettings] = useState<api.DesktopSettings>();
  const [message, setMessage] = useState("");
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    if (api.isDesktop())
      api
        .getDesktopSettings()
        .then((value) => {
          if (active) setSettings(value);
        })
        .catch((error) => {
          if (active)
            setMessage(
              "Settings request failed. Check private maintenance diagnostics.",
            );
        });
    return () => {
      active = false;
    };
  }, []);
  if (!api.isDesktop()) return null;
  return (
    <section aria-label="Compute location">
      <h3>Compute location (applies next launch)</h3>
      <p>
        Current connection:{" "}
        {api.backendMode === "https" ? "remote HTTPS API" : "local"}.
      </p>
      {settings && (
        <>
          <label>
            Compute mode
            <select
              aria-label="Compute mode"
              disabled={busy}
              value={settings.mode}
              onChange={(event) =>
                setSettings({
                  ...settings,
                  mode: event.target.value as "local" | "https",
                })
              }
            >
              <option value="local">Local (default)</option>
              <option value="https">Remote HTTPS API</option>
            </select>
          </label>
          {settings.mode === "https" && (
            <fieldset disabled={busy}>
              <legend>Existing FusionLab HTTPS API</legend>
              <label>
                HTTPS API base URL
                <input
                  aria-label="HTTPS API base URL"
                  type="url"
                  value={settings.api_url}
                  onChange={(event) =>
                    setSettings({ ...settings, api_url: event.target.value })
                  }
                />
              </label>
              <label>
                Access token
                <input
                  aria-label="Access token"
                  type="password"
                  autoComplete="off"
                  value={token}
                  onChange={(event) => setToken(event.target.value)}
                />
              </label>
              <p>
                {settings.has_access_token
                  ? "A token is saved privately. Leave blank to keep it for this endpoint."
                  : "No saved access token."}
              </p>
              <details>
                <summary>Private certificate authority (optional)</summary>
                <label>
                  PEM CA file path
                  <input
                    aria-label="PEM CA file path"
                    value={settings.ca_file}
                    onChange={(event) =>
                      setSettings({ ...settings, ca_file: event.target.value })
                    }
                  />
                </label>
                <p>
                  Leave blank for system trust. A private CA file still requires
                  valid certificates and matching hostnames.
                </p>
              </details>
            </fieldset>
          )}
          <p>
            Remote mode requires compatible FusionLab APIs; it does not move
            local projects or start local scientific jobs. Certificate
            verification stays enabled. Saving applies on restart, not
            immediately.
          </p>
          <button
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                const { has_access_token, ...values } = settings;
                await api.saveDesktopSettings({
                  ...values,
                  ...(token ? { access_token: token } : {}),
                });
                setToken("");
                setSettings(await api.getDesktopSettings());
                setMessage(
                  "Connection settings saved. Restart to apply; the current connection is unchanged.",
                );
              } catch {
                setMessage(
                  "Connection settings not saved. Check HTTPS URL, access token and optional CA file.",
                );
              } finally {
                setBusy(false);
              }
            }}
          >
            Save connection settings
          </button>
        </>
      )}
      <p role="status">{message}</p>
      <p>
        Settings stay in local user data, outside the repository. Default mode
        does not connect to a remote service.
      </p>
    </section>
  );
}
