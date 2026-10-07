import { useEffect, useState } from "react";
import * as api from "./api";

export function DesktopConnectionPanel() {
  const [settings, setSettings] = useState<api.DesktopSettings>();
  const [message, setMessage] = useState("");
  useEffect(() => {
    let active = true;
    if (api.isDesktop())
      api
        .getDesktopSettings()
        .then((value) => {
          if (active) setSettings(value);
        })
        .catch((error) => {
          if (active) setMessage("Settings request failed. Check private maintenance diagnostics.");
        });
    return () => {
      active = false;
    };
  }, []);
  if (!api.isDesktop()) return null;
  return (
    <section aria-label="Compute location">
      <h3>Compute location (applies next launch)</h3>
      {settings && (
        <>
          <label>
            Compute mode
            <select
              aria-label="Compute mode"
              value={settings.mode}
              onChange={(event) =>
                setSettings({
                  ...settings,
                  mode: event.target.value as "local" | "ssh",
                })
              }
            >
              <option value="local">Local (default)</option>
              <option value="ssh" disabled>
                Remote (authenticated session unavailable)
              </option>
            </select>
          </label>
          <p>
            Remote configuration is privately managed. Application
            authentication is not connected; this mode does not start SSH or
            send anonymous API requests.
          </p>
          <button
            onClick={async () => {
              try {
                await api.saveDesktopSettings(settings);
                setMessage(
                  "Connection settings saved. Restart to apply; the current connection is unchanged.",
                );
              } catch (error) {
                setMessage("Settings request failed. Check private maintenance diagnostics.");
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
        does not start SSH。
      </p>
    </section>
  );
}
