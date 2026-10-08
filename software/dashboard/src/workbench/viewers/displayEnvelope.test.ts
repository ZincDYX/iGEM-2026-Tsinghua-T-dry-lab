import { describe, expect, it } from "vitest";
import { displayEnvelope } from "./displayEnvelope";

describe("display-only envelope", () => {
  it("keeps original extrema, endpoints and selected source index", () => {
    const values = Array.from({ length: 100000 }, (_, i) => i % 100);
    values[23456] = -500;
    values[78901] = 1000;
    const indices = displayEnvelope(values, 4000, 33333);
    expect(indices).toContain(23456);
    expect(indices).toContain(78901);
    expect(indices).toContain(33333);
    expect(indices[0]).toBe(0);
    expect(indices.at(-1)).toBe(99999);
    expect(indices.length).toBeLessThanOrEqual(4001);
  });
  it("never removes a gap or turns a real zero into missing data", () => {
    const values: (number | null)[] = Array(10000).fill(0);
    values.fill(null, 4998, 5003);
    const indices = displayEnvelope(values);
    for (const index of [4997, 4998, 5002, 5003])
      expect(indices).toContain(index);
    expect(values[indices[0]]).toBe(0);
    expect(indices.map((i) => values[i])).toContain(null);
    expect(displayEnvelope([0, null, 2])).toEqual([0, 1, 2]);
  });
});
