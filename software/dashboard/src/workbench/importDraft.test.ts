import { expect, it } from "vitest";
import { parsePublic } from "../contracts/validation";
import { mergeImportDraft } from "./importDraft";

const sequence = (id: string, value: string) => ({
  id,
  sequence: value,
  role: "protein",
});
const project = () =>
  parsePublic("ProjectView", {
    id: "software-only",
    name: "Import regression",
    revision: 2,
    description: "",
    sequences: [sequence("old", "AAA"), sequence("conflict", "GGG")],
    assemblies: [],
    conditions: {},
    pathway: null,
    datasets: [],
    scientific_project: null,
    runtime_profile_ref: null,
    parent_run_id: null,
    parent_snapshot_sha256: null,
    files: [],
  });
const preview = (sequences: ReturnType<typeof sequence>[]) =>
  parsePublic("ImportView", {
    kind: "fasta",
    patch: { sequences },
    file: {
      id: "new-file",
      file_id: "new-file",
      name: "second.fasta",
      path: "asset:new-file",
      sha256: "a".repeat(64),
    },
  });

it("appends a second FASTA and keeps original order and sequences", () => {
  const original = project();
  const result = mergeImportDraft(original, preview([sequence("new", "TTT")]));
  expect(result.sequences.map((s) => s.id)).toEqual(["old", "conflict", "new"]);
  expect(original.sequences).toHaveLength(2);
});
it("requires explicit collision choices and keeps, replaces or separates", () => {
  const original = project(),
    imported = preview([sequence("conflict", "CCC")]);
  expect(() => mergeImportDraft(original, imported)).toThrow("Choose how");
  expect(
    mergeImportDraft(original, imported, { conflict: "keep" }).sequences[1]
      .sequence,
  ).toBe("GGG");
  expect(
    mergeImportDraft(original, imported, { conflict: "replace" }).sequences[1]
      .sequence,
  ).toBe("CCC");
  const separate = mergeImportDraft(original, imported, {
    conflict: "separate",
  });
  expect(separate.sequences.map((s) => s.id)).toEqual([
    "old",
    "conflict",
    "conflict-import-2",
  ]);
  expect(separate.sequences[1].sequence).toBe("GGG");
});
it("links identical IDs without duplicating and reserves a new separate identifier", () => {
  const original = project();
  const same = mergeImportDraft(original, preview([sequence("old", "AAA")]));
  expect(same.sequences).toHaveLength(2);
  original.sequences.push(sequence("conflict-import-2", "DDD"));
  const result = mergeImportDraft(
    original,
    preview([sequence("conflict", "CCC")]),
    { conflict: "separate" },
  );
  expect(result.sequences.at(-1)?.id).toBe("conflict-import-3");
});
