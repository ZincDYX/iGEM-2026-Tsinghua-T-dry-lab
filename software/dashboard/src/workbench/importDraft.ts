import type { ProjectView, ImportView } from "../contracts/generated";
import { parsePublic } from "../contracts/validation";

export type ConflictChoice = "keep" | "replace" | "separate";
type Sequence = ProjectView["sequences"][number];

export function importedSequences(
  project: ProjectView,
  preview: ImportView,
): Sequence[] {
  // Reuse the generated project contract rather than a second FASTA schema.
  if (!Array.isArray(preview.patch.sequences)) return [];
  return parsePublic("ProjectView", {
    ...project,
    sequences: preview.patch.sequences,
  }).sequences;
}

export function sequenceConflicts(project: ProjectView, incoming: Sequence[]) {
  return incoming.filter((item) =>
    project.sequences.some(
      (existing) =>
        existing.id === item.id && !sameSequenceContext(existing, item),
    ),
  );
}

function sameSequenceContext(first: Sequence, second: Sequence): boolean {
  return first.sequence === second.sequence &&
    (first.localization_context ?? 'cytosolic') === (second.localization_context ?? 'cytosolic');
}

export function mergeImportDraft(
  project: ProjectView,
  preview: ImportView,
  choices: Record<string, ConflictChoice> = {},
): ProjectView {
  const patch = preview.patch;
  const sequences = [...project.sequences];
  const incoming = importedSequences(project, preview);
  const linkedIds = new Map(incoming.map(item => [item.id, item.id as string | null]));
  if (new Set(incoming.map((item) => item.id)).size !== incoming.length)
    throw new Error(
      "Imported sequence identifiers must be unique within a file.",
    );
  for (const item of incoming) {
    const index = sequences.findIndex((existing) => existing.id === item.id);
    if (index < 0) {
      sequences.push(item);
      continue;
    }
    if (sameSequenceContext(sequences[index], item)) continue;
    const choice = choices[item.id];
    if (!choice) throw new Error(`Choose how to resolve sequence ${item.id}.`);
    if (choice === "replace") sequences[index] = item;
    if (choice === 'keep') linkedIds.set(item.id, null);
    if (choice === "separate") {
      let suffix = 2;
      while (
        sequences.some(
          (existing) => existing.id === `${item.id}-import-${suffix}`,
        )
      )
        ++suffix;
      sequences.push({ ...item, id: `${item.id}-import-${suffix}` });
      linkedIds.set(item.id, `${item.id}-import-${suffix}`);
    }
  }
  return parsePublic("ProjectView", {
    ...project,
    ...patch,
    sequences,
    files: project.files.some((file) => file.id === preview.file.id)
      ? project.files
      : [...project.files, preview.file],
    datasets: Array.isArray(patch.datasets)
      ? [...project.datasets, ...patch.datasets.map((row) => {
          if (row.kind !== 'genbank_design') return row;
          const design = parsePublic('GenBankDesign', row);
          return {...design, cds_proteins: design.cds_proteins.map(binding => ({...binding,
            sequence_id: binding.sequence_id === null ? null : linkedIds.get(binding.sequence_id) ?? null}))};
        })]
      : project.datasets,
  });
}
