import { useEffect, useRef, useState } from "react";
import { createPluginUI } from "molstar/lib/mol-plugin-ui";
import { createRoot, type Root } from "react-dom/client";
import { DefaultPluginUISpec } from "molstar/lib/mol-plugin-ui/spec";
import { PluginSpec } from "molstar/lib/mol-plugin/spec";
import { PluginBehaviors } from "molstar/lib/mol-plugin/behavior";
import { PluginConfig } from "molstar/lib/mol-plugin/config";
import type { PluginUIContext } from "molstar/lib/mol-plugin-ui/context";
import {
  StructureElement,
  StructureProperties,
} from "molstar/lib/mol-model/structure";
import { ColorTheme } from "molstar/lib/mol-theme/color";
import { Color } from "molstar/lib/mol-util/color";
import { applyStructureInteractivity } from "molstar/lib/extensions/plugin/interactivity";
import "molstar/build/viewer/molstar.css";
import { requestBinary, requestJson } from "../../api";
import { parsePublic } from "../../contracts/validation";
import type { StructurePage } from "../../contracts/generated";

export function StructureViewer({
  fileId,
  projectId,
  allowReference = true,
}: {
  fileId: string;
  projectId: string;
  allowReference?: boolean;
}) {
  const root = useRef<HTMLDivElement>(null);
  const plugin = useRef<PluginUIContext | undefined>(undefined);
  const [meta, setMeta] = useState<StructurePage>();
  const [error, setError] = useState("");
  const [chain, setChain] = useState("");
  const [offset, setOffset] = useState(0);
  const [ready, setReady] = useState(false);
  const [displayBusy, setDisplayBusy] = useState(false);
  const [representation, setRepresentation] = useState("cartoon");
  const [colorMode, setColorMode] = useState("chain");
  const [reference, setReference] = useState<string>();
  useEffect(() => {
    const controller = new AbortController();
    let owned: PluginUIContext | undefined;
    let reactRoot: Root | undefined;
    setError("");
    setMeta(undefined);
    setReady(false);
    setReference(undefined);
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
      setReady(true);
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
  useEffect(() => {
    if (ready && colorMode !== "chain") void display(representation, colorMode);
  }, [meta?.offset]);
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
  async function display(type: string, mode: string) {
    const owned = plugin.current;
    if (!owned || !meta) return;
    setDisplayBusy(true);
    try {
      const colors: Record<string, number> = {
        enzyme: 0x2878b5,
        scaffold: 0x7b4ab8,
        idr: 0xe69f00,
        linker: 0x009e73,
        ligand_tail: 0xcc79a7,
        tag: 0xd55e00,
      };
      const factory: ColorTheme.Factory<{}, "group"> = () => ({
        factory,
        props: {},
        granularity: "group",
        description:
          "Registered annotations on the current residue page only; unknown residues gray.",
        color: (location) => {
          if (!StructureElement.Location.is(location)) return Color(0xaaaaaa);
          const annotation = meta.annotations.find(
            (a) =>
              a.residue.model === String(location.unit.model.modelNum) &&
              a.residue.chain ===
                StructureProperties.chain.auth_asym_id(location) &&
              a.residue.residue_number ===
                String(StructureProperties.residue.auth_seq_id(location)) &&
              a.residue.insertion_code ===
                StructureProperties.residue.pdbx_PDB_ins_code(location),
          );
          if (
            mode === "confidence" &&
            annotation?.plddt !== null &&
            annotation?.plddt !== undefined
          )
            return Color.interpolate(
              Color(0xd73027),
              Color(0x4575b4),
              annotation.plddt / 100,
            );
          if (mode === "region" && annotation?.region)
            return Color(colors[annotation.region]);
          return Color(0xaaaaaa);
        },
      });
      const theme: ColorTheme.Provider<{}> = {
        name: "fusionlab-registered-page",
        label: "Registered annotation page",
        category: ColorTheme.Category.Validation,
        factory,
        getParams: () => ({}),
        defaultValues: {},
        isApplicable: (ctx) => !!ctx.structure,
      };
      const registry = owned.representation.structure.themes.colorThemeRegistry;
      const previousTheme = registry.get(theme.name);
      if (registry.has(previousTheme)) registry.remove(previousTheme);
      registry.add(theme);
      const components =
        owned.managers.structure.hierarchy.current.structures.flatMap(
          (s) => s.components,
        );
      await owned.managers.structure.component.removeRepresentations(
        components,
      );
      for (const component of components) {
        await owned.builders.structure.representation.addRepresentation(
          component.cell,
          {
            type: owned.representation.structure.registry.get(type),
            color:
              mode === "chain"
                ? owned.representation.structure.themes.colorThemeRegistry.get(
                    "chain-id",
                  )
                : theme,
          },
        );
      }
      if (plugin.current === owned) {
        setRepresentation(type);
        setColorMode(mode);
      }
    } catch {
      if (plugin.current === owned)
        setError(
          "Representation unavailable; registered values and originals are retained.",
        );
    } finally {
      if (plugin.current === owned) setDisplayBusy(false);
    }
  }
  return (
    <section>
      <p>
        Coordinate-only view. B-factor is not pLDDT. Confidence,
        fusion/reference mapping and pockets are shown only from a hash-bound
        annotation source. No inferred overlays or activity claims.
      </p>
      {error && <p role="alert">{error}</p>}
      <label>
        Representation
        <select
          aria-label="Representation"
          disabled={!ready || displayBusy}
          value={representation}
          onChange={(e) => void display(e.target.value, colorMode)}
        >
          <option value="cartoon">Cartoon</option>
          <option value="molecular-surface">Surface</option>
          <option value="ball-and-stick">Sticks / atoms</option>
        </select>
      </label>
      <label>
        Color source
        <select
          aria-label="Color source"
          disabled={!ready || displayBusy}
          value={colorMode}
          onChange={(e) => void display(representation, e.target.value)}
        >
          <option value="chain">Chain</option>
          <option
            value="region"
            disabled={
              meta?.mapping_status !==
              "source_registered_not_scientific_approval"
            }
          >
            Registered parts (current page)
          </option>
          <option
            value="confidence"
            disabled={
              meta?.confidence_status !==
              "source_registered_not_scientific_approval"
            }
          >
            Registered pLDDT (current page)
          </option>
        </select>
      </label>
      <button
        disabled={!ready}
        onClick={() => plugin.current?.managers.camera.reset()}
      >
        Reset structure view
      </button>
      <p>
        Display {representation} / {colorMode}. Annotation coloring uses the
        currently loaded residue page; other residues are gray. Continuous pLDDT
        color scale: red 0 to blue 100, no approval thresholds. Rotate/zoom/pan
        in the viewport; no new geometry or alignment is computed.
      </p>
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
                Fusion FASTA {meta.fusion_sequence_id ?? "Not registered"} ·
                SHA-256 {meta.fusion_sequence_file_sha256 ?? "Not registered"}
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
                <th>Registered clash</th>
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
                    <td>
                      {annotation?.clash
                        ? "Yes — select residue to highlight"
                        : "Not registered"}
                    </td>
                    <td>{annotation?.plddt ?? "Not registered"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {allowReference &&
            meta.annotations
              .filter((a) => a.reference_file_id)
              .map((a, i) => (
                <button
                  key={i}
                  onClick={() => setReference(a.reference_file_id!)}
                >
                  Open registered reference {a.reference_residue?.chain}:
                  {a.reference_residue?.residue_number}
                </button>
              ))}
          {reference && (
            <section>
              <h3>
                Registered reference — independent coordinates, not aligned
              </h3>
              <button onClick={() => setReference(undefined)}>
                Close reference
              </button>
              <StructureViewer
                key={reference}
                projectId={projectId}
                fileId={reference}
                allowReference={false}
              />
            </section>
          )}
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
