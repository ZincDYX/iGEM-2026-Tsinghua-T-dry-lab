import { useRef } from "react";
/** Generation is captured before any save and checked after every await. */
export function usePlanController() {
  const generation = useRef(0);
  function invalidate() {
    ++generation.current;
  }
  async function guarded<Saved, T>(
    inputGeneration: { current: number },
    save: () => Promise<Saved | undefined>,
    request: (saved: Saved) => Promise<T>,
    publish: (value: T) => void,
  ) {
    const inputStamp = inputGeneration.current;
    const planStamp = generation.current;
    const current = () =>
      inputStamp === inputGeneration.current &&
      planStamp === generation.current;
    const saved = await save();
    if (!saved || !current()) return;
    const value = await request(saved);
    if (current()) publish(value);
  }
  return { generation, invalidate, guarded };
}
