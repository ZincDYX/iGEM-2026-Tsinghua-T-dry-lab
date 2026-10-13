import { useState } from "react";
import type { ProjectView, ImportView } from "../contracts/generated";
import { linkStructureAnnotations } from "./client";

export function StructureAnnotationLinker({
  project,
  disabled,
  action,
  onPreview,
  targetFileId,
}: {
  project: ProjectView;
  disabled: boolean;
  action: (job: () => Promise<unknown>) => Promise<void>;
  onPreview: (value: ImportView) => void;
  targetFileId?:string;
}) {
  const [source, setSource] = useState("");
  const [target, setTarget] = useState(targetFileId??"");
  const [reference, setReference] = useState("");
  const [sequence, setSequence] = useState("");
  const [sequenceId, setSequenceId] = useState("");
  const structures = project.files.filter((file) =>
    /\.(pdb|cif|mmcif|bcif)$/i.test(file.name),
  );
  const options = (files: ProjectView["files"]) =>
    files.map((file) => (
      <option key={file.id} value={file.id}>
        {file.name}
      </option>
    ));
  return (
    <details>
      <summary>Link structure annotation source</summary>
      <p>
        Import and save the files first. Choose the files the annotation
        describes; the backend manages their identities. Residue positions,
        confidence values and transforms must come from your source, not
        inferred here.
      </p>
      <fieldset disabled={disabled}>
        <label>
          Annotation JSON source
          <select
            aria-label="Annotation JSON source"
            value={source}
            onChange={(e) => setSource(e.target.value)}
          >
            <option value="">Choose source</option>
            {options(
              project.files.filter((file) => /\.json$/i.test(file.name)),
            )}
          </select>
        </label>
        {!targetFileId&&<label>
          Target structure
          <select
            aria-label="Annotation target structure"
            value={target}
            onChange={(e) => setTarget(e.target.value)}
          >
            <option value="">Choose target</option>
            {options(structures)}
          </select>
        </label>}
        <label>
          Reference structure (if declared)
          <select
            aria-label="Annotation reference structure"
            value={reference}
            onChange={(e) => setReference(e.target.value)}
          >
            <option value="">Not selected</option>
            {options(structures)}
          </select>
        </label>
        <label>
          Fusion FASTA (if positions are declared)
          <select
            aria-label="Annotation fusion FASTA"
            value={sequence}
            onChange={(e) => setSequence(e.target.value)}
          >
            <option value="">Not selected</option>
            {options(
              project.files.filter((file) =>
                /\.(fasta|fa|faa)$/i.test(file.name),
              ),
            )}
          </select>
        </label>
        {sequence && (
          <label>
            FASTA record name
            <input
              aria-label="Annotation FASTA record name"
              value={sequenceId}
              onChange={(e) => setSequenceId(e.target.value)}
            />
          </label>
        )}
        <button
          disabled={!source || !target || (!!sequence && !sequenceId.trim())}
          onClick={() =>
            void action(async () => {
              onPreview(
                await linkStructureAnnotations({
                  project_id: project.id,
                  expected_revision: project.revision,
                  source_file_id: source,
                  target_file_id: target,
                  reference_file_id: reference || null,
                  sequence_file_id: sequence || null,
                  sequence_id: sequence ? sequenceId.trim() : null,
                }),
              );
            })
          }
        >
          Check annotation file links
        </button>
      </fieldset>
      <p>
        Confirmation adds a linked file to the draft and keeps the original
        unchanged. A different existing annotation set is not silently replaced.
      </p>
    </details>
  );
}
