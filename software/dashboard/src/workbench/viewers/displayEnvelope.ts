/** Display-only original-point selection. No averaging, interpolation or fill. */
export function displayEnvelope(
  values: readonly (number | null)[],
  target = 4000,
  selected?: number,
): number[] {
  if (values.length <= target) return values.map((_, index) => index);
  const indices = new Set<number>();
  const width = Math.ceil(values.length / Math.max(1, Math.floor(target / 4)));
  for (let start = 0; start < values.length; start += width) {
    const end = Math.min(values.length, start + width);
    indices.add(start);
    indices.add(end - 1);
    let minimum: number | undefined, maximum: number | undefined;
    for (let i = start; i < end; i++) {
      const value = values[i];
      if (value === null) {
        // Keep each missing run and its finite neighbours: Plotly must never
        // connect across an omitted gap, including a gap at a bucket boundary.
        if (i === 0 || values[i - 1] !== null) {
          indices.add(i);
          if (i) indices.add(i - 1);
        }
        if (i === values.length - 1 || values[i + 1] !== null) {
          indices.add(i);
          if (i + 1 < values.length) indices.add(i + 1);
        }
      } else {
        if (minimum === undefined || value < values[minimum]!) minimum = i;
        if (maximum === undefined || value > values[maximum]!) maximum = i;
      }
    }
    if (minimum !== undefined) indices.add(minimum);
    if (maximum !== undefined) indices.add(maximum);
  }
  if (selected !== undefined && selected >= 0 && selected < values.length)
    indices.add(selected);
  return [...indices].sort((a, b) => a - b);
}
