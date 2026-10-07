import {cleanup, fireEvent, render, screen, waitFor} from "@testing-library/react";
import {afterEach, describe, expect, it, vi} from "vitest";
import {DesktopConnectionPanel} from "./DesktopConnectionPanel";
import * as api from "./api";
vi.mock("./api", () => ({isDesktop: () => true, getDesktopSettings: vi.fn(), saveDesktopSettings:vi.fn()}));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
describe("desktop connection choice", () => {
  it("loads a local default with no prefilled server and only saves an explicit choice", async () => {
    vi.mocked(api.getDesktopSettings).mockResolvedValue({mode:"local",ssh_host:"",remote_port:8780});
    vi.mocked(api.saveDesktopSettings).mockResolvedValue();
    render(<DesktopConnectionPanel />);
    const mode = await screen.findByLabelText("Compute mode");
    expect((mode as HTMLSelectElement).value).toBe("local");
    expect(screen.queryByLabelText("User SSH 别名")).toBeNull();
    expect(api.saveDesktopSettings).not.toHaveBeenCalled();
    expect((screen.getByText("Remote (authenticated session unavailable)") as HTMLOptionElement).disabled).toBe(true);
    fireEvent.click(screen.getByText("Save connection settings"));
    await waitFor(() => expect(api.saveDesktopSettings).toHaveBeenCalledWith({mode:"local",ssh_host:"",remote_port:8780}));
    expect(await screen.findByText(/current connection is unchanged/)).toBeTruthy();
  });
  it("retains a useful rejection message rather than claiming connection changed", async () => {
    vi.mocked(api.getDesktopSettings).mockResolvedValue({mode:"local",ssh_host:"",remote_port:8780});
    vi.mocked(api.saveDesktopSettings).mockRejectedValue("invalid SSH alias");
    render(<DesktopConnectionPanel />);
    await screen.findByLabelText("Compute mode");
    fireEvent.click(screen.getByText("Save connection settings"));
    expect(await screen.findByText("Settings request failed. Check private maintenance diagnostics.")).toBeTruthy();
    expect(screen.queryByText(/Connection settings saved/)).toBeNull();
  });
});
