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
    const mode = await screen.findByLabelText("计算模式");
    expect((mode as HTMLSelectElement).value).toBe("local");
    expect(screen.queryByLabelText("用户 SSH 别名")).toBeNull();
    expect(api.saveDesktopSettings).not.toHaveBeenCalled();
    fireEvent.change(mode,{target:{value:"ssh"}});
    expect((screen.getByLabelText("用户 SSH 别名") as HTMLInputElement).value).toBe("");
    fireEvent.change(screen.getByLabelText("用户 SSH 别名"),{target:{value:"my-research-host"}});
    fireEvent.click(screen.getByText("保存连接设置"));
    await waitFor(() => expect(api.saveDesktopSettings).toHaveBeenCalledWith({mode:"ssh",ssh_host:"my-research-host",remote_port:8780}));
    expect(await screen.findByText(/当前连接没有改变/)).toBeTruthy();
  });
  it("retains a useful rejection message rather than claiming connection changed", async () => {
    vi.mocked(api.getDesktopSettings).mockResolvedValue({mode:"local",ssh_host:"",remote_port:8780});
    vi.mocked(api.saveDesktopSettings).mockRejectedValue("invalid SSH alias");
    render(<DesktopConnectionPanel />);
    await screen.findByLabelText("计算模式");
    fireEvent.click(screen.getByText("保存连接设置"));
    expect(await screen.findByText("invalid SSH alias")).toBeTruthy();
    expect(screen.queryByText(/连接设置已保存/)).toBeNull();
  });
});
