import { useEffect, useRef, useState } from "react";
import { createPluginUI } from "molstar/lib/mol-plugin-ui";
import { createRoot, type Root } from "react-dom/client";
import { DefaultPluginUISpec } from "molstar/lib/mol-plugin-ui/spec";
import { PluginSpec } from "molstar/lib/mol-plugin/spec";
import { PluginBehaviors } from "molstar/lib/mol-plugin/behavior";
import { PluginConfig } from "molstar/lib/mol-plugin/config";
import type { PluginUIContext } from "molstar/lib/mol-plugin-ui/context";
import { applyStructureInteractivity } from "molstar/lib/extensions/plugin/interactivity";
import "molstar/build/viewer/molstar.css";
import { requestBinary, requestJson } from "../../api";
import { parsePublic } from "../../contracts/validation";
import type { StructurePage } from "../../contracts/generated";

export function StructureViewer({
  fileId,
  projectId,
}: {
  fileId: string;
  projectId: string;
}) {
  const root = useRef<HTMLDivElement>(null);
  const plugin = useRef<PluginUIContext | undefined>(undefined);
  const [meta, setMeta] = useState<StructurePage>();
  const [error, setError] = useState("");
  const [chain, setChain] = useState("");
  const [offset, setOffset] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    let owned: PluginUIContext | undefined;
    let reactRoot: Root | undefined;
    setError("");
    setMeta(undefined);
    setOffset(0);
    async function load() {
      const [raw, response] = await Promise.all([
        requestJson(
          `/files/${encodeURIComponent(fileId)}/structure-metadata?project_id=${encodeURIComponent(projectId)}&limit=100`,
          undefined,
          controller.signal,
        ),
        requestBinary(
          `/files/${encodeURIComponent(fileId)}/structure-preview?project_id=${encodeURIComponent(projectId)}`,
          undefined,
          controller.signal,
        ),
      ]);
      const metadata = parsePublic("StructurePage", raw);
      const data = await response.text();
      if (controller.signal.aborted || !root.current) return;
      if (
        metadata.identity.file_id !== fileId ||
        metadata.identity.project_id !== projectId
      )
        throw new Error("Wrong resource identity.");
      setMeta(metadata);
      setChain(metadata.chains[0] ?? "");
      const spec = DefaultPluginUISpec();
      spec.actions = [];
      // No remote/download actions or network custom properties.
      spec.behaviors = [
        PluginSpec.Behavior(PluginBehaviors.Representation.HighlightLoci),
        PluginSpec.Behavior(PluginBehaviors.Representation.SelectLoci),
        PluginSpec.Behavior(
          PluginBehaviors.Representation.DefaultLociLabelProvider,
        ),
        PluginSpec.Behavior(PluginBehaviors.Camera.FocusLoci),
        PluginSpec.Behavior(PluginBehaviors.Camera.CameraControls),
        PluginSpec.Behavior(PluginBehaviors.CustomProps.StructureInfo),
      ];
      spec.layout = { initial: { isExpanded: false, showControls: false } };
      spec.components = {
        controls: { left: "none", right: "none", top: "none", bottom: "none" },
        remoteState: "none",
        disableDragOverlay: true,
      };
      spec.config = [
        [PluginConfig.VolumeStreaming.Enabled, false],
        [PluginConfig.Viewport.ShowExpand, false],
      ];
      owned = await createPluginUI({
        target: root.current,
        spec,
        render: (element, target) => {
          reactRoot = createRoot(target);
          reactRoot.render(element);
        },
      });
      if (controller.signal.aborted) {
        owned.dispose();
        return;
      }
      plugin.current = owned;
      const source = await owned.builders.data.rawData({
        data,
        label: "Authorized coordinate-only preview",
      });
      const trajectory = await owned.builders.structure.parseTrajectory(
        source,
        metadata.format as "pdb" | "mmcif",
      );
      await owned.builders.structure.hierarchy.applyPreset(
        trajectory,
        "all-models",
        { representationPreset: "polymer-and-ligand" },
      );
      if (controller.signal.aborted) return;
      setMeta(metadata);
      setChain(metadata.chains[0] ?? "");
    }
    void load().catch(() => {
      if (!controller.signal.aborted)
        setError(
          "Structure display unavailable. WebGL is required; the original source remains available.",
        );
    });
    return () => {
      controller.abort();
      reactRoot?.unmount();
      owned?.dispose();
      plugin.current = undefined;
    };
  }, [fileId, projectId]);
  useEffect(() => {
    if (!offset && (!meta || meta.offset === 0)) return;
    const controller = new AbortController();
    void requestJson(
      `/files/${encodeURIComponent(fileId)}/structure-metadata?project_id=${encodeURIComponent(projectId)}&offset=${offset}&limit=100`,
      undefined,
      controller.signal,
    )
      .then((raw) => {
        if (!controller.signal.aborted) {
          const next = parsePublic("StructurePage", raw);
          if (
            next.identity.file_id !== fileId ||
            next.identity.project_id !== projectId ||
            next.identity.source_sha256 !== meta?.identity.source_sha256
          )
            throw new Error("Resource identity changed.");
          setMeta(next);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) setError("Residue page unavailable.");
      });
    return () => controller.abort();
  }, [offset, fileId, projectId]);
  function focus(
    chainId: string,
    residue?: string,
    insertion?: string,
    model?: string,
  ) {
    if (!plugin.current) return;
    applyStructureInteractivity(plugin.current, {
      action: ["select", "focus"],
      expression: (builder) =>
        builder.struct.generator.atomGroups({
          ...(model
            ? {
                "entity-test": builder.core.rel.eq([
                  builder.struct.atomProperty.core.modelIndex(),
                  meta?.models.indexOf(model),
                ]),
              }
            : {}),
          "chain-test": builder.core.rel.eq([
            builder.struct.atomProperty.macromolecular.auth_asym_id(),
            chainId,
          ]),
          ...(residue
            ? {
                "residue-test": builder.core.logic.and([
                  builder.core.rel.eq([
                    builder.struct.atomProperty.macromolecular.auth_seq_id(),
                    Number(residue),
                  ]),
                  builder.core.rel.eq([
                    builder.struct.atomProperty.macromolecular.pdbx_PDB_ins_code(),
                    insertion ?? "",
                  ]),
                ]),
              }
            : {}),
        }),
    });
  }
  return (
    <section>
      <p>
        Coordinate-only view. B-factor is not pLDDT. Confidence,
        fusion/reference mapping and pockets are shown only from a hash-bound
        annotation source. No inferred overlays or activity claims.
      </p>
      {error && <p role="alert">{error}</p>}
      <div
        ref={root}
        className="structure-canvas"
        style={{ position: "relative", height: 420 }}
      />
      {meta && (
        <>
          <p>Source SHA-256 {meta.identity.source_sha256}</p>
          <p>
            Mapping: {meta.mapping_status}; pocket: {meta.pocket_status};
            confidence: {meta.confidence_status}.
          </p>
          {meta.annotation_file_id && (
            <details>
              <summary>Annotation provenance (original source text)</summary>
              <p>
                {meta.annotation_source_reference} ·{" "}
                {meta.annotation_source_tool}{" "}
                {meta.annotation_source_tool_version} ·{" "}
                {meta.annotation_file_id} · SHA-256 {meta.annotation_sha256}
              </p>
              <p>
                Registered display source, not scientific approval. Reference
                coordinates are not automatically aligned.
              </p>
            </details>
          )}
          <label>
            Chain
            <select
              value={chain}
              onChange={(e) => {
                setChain(e.target.value);
                focus(e.target.value);
              }}
            >
              {meta.chains.map((c) => (
                <option key={c} value={c}>
                  {c || "(blank chain)"}
                </option>
              ))}
            </select>
          </label>
          <table>
            <thead>
              <tr>
                <th>Model</th>
                <th>Chain</th>
                <th>Residue / insertion code</th>
                <th>Name</th>
                <th>Fusion position / region</th>
                <th>Reference residue</th>
                <th>Registered pocket</th>
                <th>pLDDT (registered source)</th>
              </tr>
            </thead>
            <tbody>
              {meta.residues.map((r, i) => {
                const annotation = meta.annotations.find(
                  (a) => JSON.stringify(a.residue) === JSON.stringify(r),
                );
                return (
                  <tr key={i}>
                    <td>{r.model}</td>
                    <td>{r.chain}</td>
                    <td>
                      <button
                        onClick={() =>
                          focus(
                            r.chain,
                            r.residue_number,
                            r.insertion_code,
                            r.model,
                          )
                        }
                      >
                        {r.residue_number}
                        {r.insertion_code}
                      </button>
                    </td>
                    <td>{r.residue_name}</td>
                    <td>
                      {annotation?.full_fusion_position ?? "Not registered"} /{" "}
                      {annotation?.region ?? "Not registered"}
                    </td>
                    <td>
                      {annotation?.reference_residue
                        ? `${annotation.reference_residue.model}:${annotation.reference_residue.chain}:${annotation.reference_residue.residue_number}${annotation.reference_residue.insertion_code} · ${annotation.reference_sha256}`
                        : "Not registered"}
                    </td>
                    <td>
                      {annotation?.pocket
                        ? "Yes — select residue to highlight"
                        : "Not registered"}
                    </td>
                    <td>{annotation?.plddt ?? "Not registered"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <button
            disabled={!offset}
            onClick={() => setOffset(Math.max(0, offset - 100))}
          >
            Previous residues
          </button>
          <button
            disabled={offset + 100 >= meta.total}
            onClick={() => setOffset(offset + 100)}
          >
            Next residues
          </button>
          <p>
            {offset + 1}–{offset + meta.residues.length} / {meta.total}
          </p>
        </>
      )}
    </section>
  );
}
