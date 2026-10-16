import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { usePlanController } from "./usePlanController";

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

describe("proposal generation boundaries", () => {
  it("passes the saved typed project through once and publishes its result", async () => {
    const { result } = renderHook(usePlanController);
    const project = { id: "software-only", revision: 2 };
    const request = vi.fn(async (saved: typeof project) => saved.revision);
    const publish = vi.fn();
    await result.current.guarded(
      { current: 1 },
      async () => project,
      request,
      publish,
    );
    expect(request).toHaveBeenCalledExactlyOnceWith(project);
    expect(publish).toHaveBeenCalledExactlyOnceWith(2);
  });

  it("does not request a plan when save fails or the input changes during save", async () => {
    const { result } = renderHook(usePlanController);
    const request = vi.fn(async () => "unused");
    const publish = vi.fn();
    const generation = { current: 1 };
    await result.current.guarded(
      generation,
      async () => undefined,
      request,
      publish,
    );
    const saved = deferred<{ id: string }>();
    const pending = result.current.guarded(
      generation,
      () => saved.promise,
      request,
      publish,
    );
    generation.current++;
    saved.resolve({ id: "stale" });
    await pending;
    expect(request).not.toHaveBeenCalled();
    expect(publish).not.toHaveBeenCalled();
  });

  it("never publishes an obsolete response after proposal invalidation", async () => {
    const { result } = renderHook(usePlanController);
    const response = deferred<string>();
    const request = vi.fn(() => response.promise);
    const publish = vi.fn();
    const pending = result.current.guarded(
      { current: 1 },
      async () => ({ id: "saved" }),
      request,
      publish,
    );
    await vi.waitFor(() => expect(request).toHaveBeenCalledOnce());
    result.current.invalidate();
    response.resolve("outdated proposal");
    await pending;
    expect(publish).not.toHaveBeenCalled();
  });
});
