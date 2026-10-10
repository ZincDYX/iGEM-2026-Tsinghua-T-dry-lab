import { act, renderHook } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { useDocuments } from "./useDocuments";

beforeEach(() => localStorage.clear());
it('starts a new workspace with Inputs only and restores the last selected document', () => {
  const first=renderHook(()=>useDocuments('new-workspace',false,vi.fn()));
  expect(first.result.current.tab).toBe('inputs');
  expect(first.result.current.openDocuments).toEqual(['inputs']);
  act(()=>first.result.current.setTab('plan'));
  first.unmount();
  const restored=renderHook(()=>useDocuments('new-workspace',false,vi.fn()));
  expect(restored.result.current.tab).toBe('plan');
});
it("keeps Settings and Plugins open across navigation and restores the workspace", () => {
  const blocked = vi.fn();
  const first = renderHook(() => useDocuments("workspace-a", false, blocked));
  act(() => first.result.current.setTab("settings"));
  act(() => first.result.current.setTab("plugins"));
  act(() => first.result.current.setTab("plan"));
  expect(first.result.current.openDocuments).toContain("settings");
  expect(first.result.current.openDocuments).toContain("plugins");
  first.unmount();
  const second = renderHook(() => useDocuments("workspace-a", false, blocked));
  expect(second.result.current.openDocuments).toContain("settings");
  act(() => second.result.current.closeDocument("settings"));
  expect(second.result.current.openDocuments).not.toContain("settings");
});
it("blocks dirty document close and does not leak documents between workspaces", () => {
  const blocked = vi.fn();
  const hook = renderHook(({ workspace, dirty }) => useDocuments(workspace, dirty, blocked),
    { initialProps: { workspace: "a", dirty: true } });
  act(() => hook.result.current.setTab("settings"));
  act(() => hook.result.current.closeDocument("inputs"));
  expect(blocked).toHaveBeenCalledOnce();
  expect(hook.result.current.openDocuments).toContain("inputs");
  hook.rerender({ workspace: "b", dirty: false });
  expect(hook.result.current.openDocuments).not.toContain("settings");
  hook.rerender({ workspace: "a", dirty: false });
  expect(hook.result.current.openDocuments).toContain("settings");
});
