/** One in-flight request, explicit version ordering, cancellation on identity change. */
export function pollVersioned<
  T extends { state_version: number; status: string },
>(options: {
  load: (signal: AbortSignal) => Promise<T>;
  accept: (value: T) => void;
  fail: (reason: unknown) => void;
  interval?: number;
  initialVersion?: number;
}) {
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  let version = options.initialVersion ?? -1;
  const stopped = new Set([
    "succeeded",
    "failed",
    "paused",
    "cancelled",
    "interrupted",
  ]);
  async function next() {
    try {
      const value = await options.load(controller.signal);
      if (controller.signal.aborted) return;
      if (value.state_version >= version) {
        version = value.state_version;
        options.accept(value);
        if (stopped.has(value.status)) return;
      }
    } catch (reason) {
      if (controller.signal.aborted) return;
      options.fail(reason);
    }
    if (!controller.signal.aborted)
      timer = setTimeout(next, options.interval ?? 1200);
  }
  void next();
  return () => {
    controller.abort();
    clearTimeout(timer);
  };
}
