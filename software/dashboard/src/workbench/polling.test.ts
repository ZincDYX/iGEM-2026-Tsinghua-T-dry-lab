import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { pollVersioned } from "./polling";
beforeEach(() => {
  vi.spyOn(document, "hidden", "get").mockReturnValue(false);
});
afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

it("does not overlap slow requests, rejects old versions and stops terminal polling", async () => {
  vi.useFakeTimers();
  let finish!: (value: { state_version: number; status: string }) => void;
  const load = vi.fn(
    () =>
      new Promise<{ state_version: number; status: string }>((resolve) => {
        finish = resolve;
      }),
  );
  const accept = vi.fn();
  const stop = pollVersioned({ load, accept, fail: vi.fn(), interval: 10 });
  await vi.advanceTimersByTimeAsync(100);
  expect(load).toHaveBeenCalledTimes(1);
  finish({ state_version: 5, status: "running" });
  await vi.advanceTimersByTimeAsync(10);
  finish({ state_version: 4, status: "succeeded" });
  await vi.advanceTimersByTimeAsync(10);
  expect(accept).toHaveBeenCalledTimes(1);
  finish({ state_version: 6, status: "succeeded" });
  await vi.advanceTimersByTimeAsync(100);
  expect(load).toHaveBeenCalledTimes(3);
  expect(accept).toHaveBeenCalledTimes(2);
  stop();
  vi.useRealTimers();
});
it("an identity switch aborts and discards the previous request", async () => {
  let finish!: (value: { state_version: number; status: string }) => void;
  let signal!: AbortSignal;
  const accept = vi.fn();
  const stop = pollVersioned({
    load: (s) => {
      signal = s;
      return new Promise((resolve) => {
        finish = resolve;
      });
    },
    accept,
    fail: vi.fn(),
  });
  stop();
  expect(signal.aborted).toBe(true);
  finish({ state_version: 9, status: "running" });
  await Promise.resolve();
  expect(accept).not.toHaveBeenCalled();
});

it("deduplicates unchanged versions without missing a later terminal update", async () => {
  vi.useFakeTimers();
  const load = vi
    .fn()
    .mockResolvedValueOnce({ state_version: 1, status: "running" })
    .mockResolvedValueOnce({ state_version: 1, status: "running" })
    .mockResolvedValue({ state_version: 2, status: "succeeded" });
  const accept = vi.fn();
  const stop = pollVersioned({ load, accept, fail: vi.fn(), interval: 10 });
  await vi.advanceTimersByTimeAsync(100);
  expect(load).toHaveBeenCalledTimes(3);
  expect(accept).toHaveBeenCalledTimes(2);
  stop();
});
