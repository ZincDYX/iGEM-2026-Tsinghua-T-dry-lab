import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DesktopConnectionPanel } from "./DesktopConnectionPanel";
import * as api from "./api";
vi.mock("./api", () => ({
  backendMode: "local",
  isDesktop: () => true,
  getDesktopSettings: vi.fn(),
  saveDesktopSettings: vi.fn(),
}));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
describe("desktop connection choice", () => {
  it("loads a local default with no prefilled server and only saves an explicit choice", async () => {
    vi.mocked(api.getDesktopSettings).mockResolvedValue({
      mode: "local",
      api_url: "",
      ca_file: "",
      has_access_token: false,
    });
    vi.mocked(api.saveDesktopSettings).mockResolvedValue();
    render(<DesktopConnectionPanel />);
    const mode = await screen.findByLabelText("Compute mode");
    expect((mode as HTMLSelectElement).value).toBe("local");
    expect(screen.queryByLabelText("User SSH 别名")).toBeNull();
    expect(api.saveDesktopSettings).not.toHaveBeenCalled();
    expect(
      (screen.getByText("Remote HTTPS API") as HTMLOptionElement).disabled,
    ).toBe(false);
    fireEvent.click(screen.getByText("Save connection settings"));
    await waitFor(() =>
      expect(api.saveDesktopSettings).toHaveBeenCalledWith({
        mode: "local",
        api_url: "",
        ca_file: "",
      }),
    );
    expect(
      await screen.findByText(/current connection is unchanged/),
    ).toBeTruthy();
  });
  it("retains a useful rejection message rather than claiming connection changed", async () => {
    vi.mocked(api.getDesktopSettings).mockResolvedValue({
      mode: "local",
      api_url: "",
      ca_file: "",
      has_access_token: false,
    });
    vi.mocked(api.saveDesktopSettings).mockRejectedValue("invalid SSH alias");
    render(<DesktopConnectionPanel />);
    await screen.findByLabelText("Compute mode");
    fireEvent.click(screen.getByText("Save connection settings"));
    expect(
      await screen.findByText(
        "Connection settings not saved. Check HTTPS URL, access token and optional CA file.",
      ),
    ).toBeTruthy();
    expect(screen.queryByText(/Connection settings saved/)).toBeNull();
  });
  it("asks privately for a new token once, clears it after save and never loads one", async () => {
    const initial = {
      mode: "https" as const,
      api_url: "https://example.invalid",
      ca_file: "",
      has_access_token: true,
    };
    vi.mocked(api.getDesktopSettings).mockResolvedValue(initial);
    vi.mocked(api.saveDesktopSettings).mockResolvedValue();
    render(<DesktopConnectionPanel />);
    const input = (await screen.findByLabelText(
      "Access token",
    )) as HTMLInputElement;
    expect(input.type).toBe("password");
    expect(input.value).toBe("");
    fireEvent.change(input, {
      target: { value: "SOFTWARE_TEST_NOT_REAL_ACCESS" },
    });
    fireEvent.click(screen.getByText("Save connection settings"));
    await waitFor(() =>
      expect(api.saveDesktopSettings).toHaveBeenCalledWith({
        mode: "https",
        api_url: initial.api_url,
        ca_file: "",
        access_token: "SOFTWARE_TEST_NOT_REAL_ACCESS",
      }),
    );
    await waitFor(() => expect(input.value).toBe(""));
    expect(screen.queryByText("SOFTWARE_TEST_NOT_REAL_ACCESS")).toBeNull();
  });
  it("keeps the existing token only when no replacement was entered", async () => {
    vi.mocked(api.getDesktopSettings).mockResolvedValue({
      mode: "https",
      api_url: "https://example.invalid",
      ca_file: "",
      has_access_token: true,
    });
    vi.mocked(api.saveDesktopSettings).mockResolvedValue();
    render(<DesktopConnectionPanel />);
    await screen.findByLabelText("Access token");
    fireEvent.click(screen.getByText("Save connection settings"));
    await waitFor(() =>
      expect(api.saveDesktopSettings).toHaveBeenCalledWith({
        mode: "https",
        api_url: "https://example.invalid",
        ca_file: "",
      }),
    );
  });
});
