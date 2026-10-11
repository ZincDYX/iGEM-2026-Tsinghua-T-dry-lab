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
  Model,
} from "molstar/lib/mol-model/structure";
import { ColorTheme } from "molstar/lib/mol-theme/color";
import { Color } from "molstar/lib/mol-util/color";
import { Mat4 } from "molstar/lib/mol-math/linear-algebra";
import { StateTransforms } from "molstar/lib/mol-plugin-state/transforms";
import { applyStructureInteractivity } from "molstar/lib/extensions/plugin/interactivity";
import "molstar/build/viewer/molstar.css";
import { requestBinary, requestJson } from "../../api";
import { parsePublicAsync as parsePublic } from "../../contracts/validation";
import type { StructurePage } from "../../contracts/generated";

const residueKey = (
  model: string,
  chain: string,
  number: string,
  insertion: string,
) => JSON.stringify([model, chain, number, insertion]);

export function StructureViewer({
  fileId,
  projectId,
}: { fileId: string; projectId: string }) {
  const [reference, setReference] = useState<string>();
  useEffect(() => setReference(undefined), [fileId, projectId]);
  return <section aria-label="Structure viewer">
    {reference && <><h3>Registered reference — independent coordinates, not aligned</h3>
      <button onClick={() => setReference(undefined)}>Return to original structure</button></>}
    <CoordinateViewer key={reference ?? fileId} fileId={reference ?? fileId} projectId={projectId}
      allowReference={!reference} onReference={setReference}/>
  </section>;
}

function CoordinateViewer({
  fileId,
  projectId,
  allowReference = true,
  onReference,
}: {
  fileId: string;
  projectId: string;
  allowReference?: boolean;
  onReference: (id: string) => void;
}) {
  const root = useRef<HTMLDivElement>(null);
  const plugin = useRef<PluginUIContext | undefined>(undefined);
  const sourceModels = useRef(
    new Map<string, { source: string; number: number }>(),
  );
  const [meta, setMeta] = useState<StructurePage>();
  const annotationIndex = useRef(
    new Map<string, StructurePage["annotations"][number]>(),
  );
  const [annotationsReady, setAnnotationsReady] = useState(false);
  const [error, setError] = useState("");
  const [chain, setChain] = useState("");
  const [offset, setOffset] = useState(0);
  const [ready, setReady] = useState(false);
  const [displayBusy, setDisplayBusy] = useState(false);
  const [representation, setRepresentation] = useState("cartoon");
  const [colorMode, setColorMode] = useState("chain");
  const overlayRoot = useRef<string>(undefined);
  const overlayRequest = useRef<AbortController>(undefined);
  const [overlayIndex, setOverlayIndex] = useState<number>();
  useEffect(() => {
    const controller = new AbortController();
    let owned: PluginUIContext | undefined;
    let reactRoot: Root | undefined;
    setError("");
    setMeta(undefined);
    setReady(false);
    setAnnotationsReady(false);
    annotationIndex.current.clear();
    setOverlayIndex(undefined);
    overlayRoot.current = undefined;
    setOffset(0);
    sourceModels.current.clear();
    async function load() {
      const [raw, response, annotationRaw] = await Promise.all([
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
        requestJson(
          `/files/${encodeURIComponent(fileId)}/structure-annotations?project_id=${encodeURIComponent(projectId)}`,
          undefined,
          controller.signal,
        ),
      ]);
      const metadata = await parsePublic("StructurePage", raw);
      const fullAnnotations = await parsePublic("StructurePage", annotationRaw);
      const data = await response.text();
      if (controller.signal.aborted || !root.current) return;
      if (
        metadata.identity.file_id !== fileId ||
        metadata.identity.project_id !== projectId
      )
        throw new Error("Wrong resource identity.");
      if (
        fullAnnotations.identity.project_id !== projectId ||
        fullAnnotations.identity.file_id !== fileId ||
        fullAnnotations.identity.source_sha256 !==
          metadata.identity.source_sha256 ||
        fullAnnotations.annotation_sha256 !== metadata.annotation_sha256 ||
        fullAnnotations.annotation_scope !== "full_model"
      )
        throw new Error("Annotation source identity changed.");
      annotationIndex.current = new Map(
        fullAnnotations.annotations.map((a) => [
          residueKey(
            a.residue.model,
            a.residue.chain,
            a.residue.residue_number,
            a.residue.insertion_code,
          ),
          a,
        ]),
      );
      setAnnotationsReady(true);
      setMeta(metadata);
      setChain(metadata.chains[0] ?? "");
      // Molstar's UI initialization promise can remain pending after a failed
      // WebGL mount. Detect an unavailable browser before mounting that UI,
      // while keeping the already loaded source/annotation table usable.
      const probe = document.createElement('canvas');
      const graphics = probe.getContext('webgl2') ?? probe.getContext('webgl');
      if (!graphics) throw Error('WebGL is unavailable.');
      graphics.getExtension('WEBGL_lose_context')?.loseContext();
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
      if (trajectory.obj?.data.frameCount !== metadata.models.length)
        throw new Error("Coordinate model identity differs from metadata.");
      await owned.builders.structure.hierarchy.applyPreset(
        trajectory,
        "all-models",
        { representationPreset: "polymer-and-ligand" },
      );
      if (controller.signal.aborted) return;
      // PDB model numbers are renumbered by Mol*. Bind parsed frame identity
      // to the original, source-ordered metadata instead of equating numbers.
      for (const structure of owned.managers.structure.hierarchy.current
        .structures) {
        for (const model of structure.cell.obj!.data.models) {
          const sourceModel =
            metadata.models[Model.TrajectoryInfo.get(model).index];
          if (sourceModel === undefined)
            throw new Error("Unknown coordinate model.");
          sourceModels.current.set(model.id, {
            source: sourceModel,
            number: model.modelNum,
          });
        }
      }
      setMeta(metadata);
      setChain(metadata.chains[0] ?? "");
      setReady(true);
    }
    void load().catch(() => {
      if (!controller.signal.aborted) {
        reactRoot?.unmount();
        reactRoot = undefined;
        owned?.dispose();
        owned = undefined;
        plugin.current = undefined;
        setError(
          "Structure display unavailable. WebGL is required; the original source remains available.",
        );
      }
    });
    return () => {
      controller.abort();
      overlayRequest.current?.abort();
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
      .then(async (raw) => {
        if (!controller.signal.aborted) {
          const next = await parsePublic("StructurePage", raw);
          if(controller.signal.aborted)return;
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
    const modelNumber =
      model === undefined
        ? undefined
        : [...sourceModels.current.values()].find(
            (value) => value.source === model,
          )?.number;
    if (model !== undefined && modelNumber === undefined) return;
    applyStructureInteractivity(plugin.current, {
      action: ["select", "focus"],
      expression: (builder) =>
        builder.struct.generator.atomGroups({
          ...(model
            ? {
                "entity-test": builder.core.rel.eq([
                  builder.struct.atomProperty.core.modelIndex(),
                  modelNumber,
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
  function focusRegistered(kind: "pocket" | "clash") {
    const owned = plugin.current;
    if (!owned) return;
    const modelNumbers = new Map(
      [...sourceModels.current.values()].map((m) => [m.source, m.number]),
    );
    const groups = new Map<
      string,
      { model: number; chain: string; residues: string[] }
    >();
    for (const annotation of annotationIndex.current.values()) {
      if (!annotation[kind]) continue;
      const r = annotation.residue,
        model = modelNumbers.get(r.model);
      if (model === undefined) continue;
      const key = JSON.stringify([model, r.chain]);
      let group = groups.get(key);
      if (!group) {
        group = { model, chain: r.chain, residues: [] };
        groups.set(key, group);
      }
      group.residues.push(Number(r.residue_number) + "|" + r.insertion_code);
    }
    if (!groups.size) return;
    // One indexed membership test per atom, not a complete atom scan per residue.
    applyStructureInteractivity(owned, {
      action: ["select", "focus"],
      expression: (builder) =>
        builder.struct.combinator.merge(
          [...groups.values()].map((group) =>
            builder.struct.generator.atomGroups({
              "entity-test": builder.core.rel.eq([
                builder.struct.atomProperty.core.modelIndex(),
                group.model,
              ]),
              "chain-test": builder.core.rel.eq([
                builder.struct.atomProperty.macromolecular.auth_asym_id(),
                group.chain,
              ]),
              "residue-test": builder.core.set.has([
                builder.core.type.set(group.residues),
                builder.core.str.concat([
                  builder.core.str.concat([
                    builder.core.type.str([
                      builder.struct.atomProperty.macromolecular.auth_seq_id(),
                    ]),
                    "|",
                  ]),
                  builder.struct.atomProperty.macromolecular.pdbx_PDB_ins_code(),
                ]),
              ]),
            }),
          ),
        ),
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
          "Verified full-model annotation index; unknown residues gray.",
        color: (location) => {
          if (!StructureElement.Location.is(location)) return Color(0xaaaaaa);
          const annotation = annotationIndex.current.get(
            residueKey(
              sourceModels.current.get(location.unit.model.id)?.source ?? "",
              StructureProperties.chain.auth_asym_id(location),
              String(StructureProperties.residue.auth_seq_id(location)),
              StructureProperties.residue.pdbx_PDB_ins_code(location),
            ),
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
        name: "fusionlab-registered-model",
        label: "Registered full-model annotations",
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
        owned.managers.structure.hierarchy.current.structures.flatMap((s) =>
          s.cell.obj?.data.models.some((model) =>
            sourceModels.current.has(model.id),
          )
            ? s.components
            : [],
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
  async function showOverlay(index?: number) {
    const owned = plugin.current;
    if (!owned || !meta) return;
    overlayRequest.current?.abort();
    const controller = new AbortController();
    overlayRequest.current = controller;
    setDisplayBusy(true);
    try {
      if (overlayRoot.current) {
        await owned.build().delete(overlayRoot.current).commit();
        overlayRoot.current = undefined;
        setOverlayIndex(undefined);
      }
      if (index === undefined) return;
      const overlay = meta.overlays[index];
      const query = `?project_id=${encodeURIComponent(projectId)}`;
      const [raw, response] = await Promise.all([
        requestJson(
          `/files/${encodeURIComponent(overlay.reference_file_id)}/structure-metadata${query}&limit=1`,
          undefined,
          controller.signal,
        ),
        requestBinary(
          `/files/${encodeURIComponent(overlay.reference_file_id)}/structure-preview${query}`,
          undefined,
          controller.signal,
        ),
      ]);
      const referenceMeta = await parsePublic("StructurePage", raw);
      if (
        referenceMeta.identity.file_id !== overlay.reference_file_id ||
        referenceMeta.identity.project_id !== projectId ||
        referenceMeta.identity.source_sha256 !== overlay.reference_sha256 ||
        overlay.target_sha256 !== meta.identity.source_sha256
      )
        throw Error("Overlay source identity changed.");
      const data = await response.text();
      if (controller.signal.aborted || plugin.current !== owned) return;
      const source = await owned.builders.data.rawData({
        data,
        label: "Registered reference overlay",
      });
      overlayRoot.current = source.ref;
      const trajectory = await owned.builders.structure.parseTrajectory(
        source,
        referenceMeta.format as "pdb" | "mmcif",
      );
      if (trajectory.obj?.data.frameCount !== referenceMeta.models.length)
        throw Error("Overlay model identity changed.");
      const matrix = Mat4.transpose(
        Mat4(),
        Mat4.fromArray(Mat4(), overlay.matrix.flat(), 0),
      );
      for (let frame = 0; frame < referenceMeta.models.length; frame++) {
        const model = await owned.builders.structure.createModel(trajectory, {
          modelIndex: frame,
        });
        const structure = await owned.builders.structure.createStructure(model);
        const transformed = await owned
          .build()
          .to(structure)
          .apply(StateTransforms.Model.TransformStructureConformation, {
            transform: {
              name: "matrix",
              params: { data: matrix, transpose: false },
            },
          })
          .commit();
        const component =
          await owned.builders.structure.tryCreateComponentStatic(
            transformed,
            "all",
          );
        if (component)
          await owned.builders.structure.representation.addRepresentation(
            component,
            {
              type: "ball-and-stick",
              color: "uniform",
              colorParams: { value: Color(0xe69f00) },
            },
          );
      }
      if (controller.signal.aborted || plugin.current !== owned) return;
      setOverlayIndex(index);
      owned.managers.camera.reset();
    } catch {
      if (plugin.current === owned && !controller.signal.aborted) {
        if (overlayRoot.current)
          await owned.build().delete(overlayRoot.current).commit();
        overlayRoot.current = undefined;
        setOverlayIndex(undefined);
        setError(
          "Registered overlay unavailable; independent coordinates and sources remain available.",
        );
      }
    } finally {
      if (plugin.current === owned) setDisplayBusy(false);
    }
  }
  async function exportImage() {
    const owned = plugin.current;
    if (!owned?.helpers.viewportScreenshot) return;
    setDisplayBusy(true);
    try {
      await owned.helpers.viewportScreenshot.download('registered-structure.png');
    } catch {
      if (plugin.current === owned) setError('Image export failed; coordinates and registered sources are unchanged.');
    } finally {
      if (plugin.current === owned) setDisplayBusy(false);
    }
  }
  return (
    <section>
      <p>
        Coordinate-only view. B-factor is not pLDDT. Confidence,
        fusion/reference mapping and pockets are shown only from a linked
        annotation source. No inferred overlays or activity claims.
      </p>
      {error && <p role="alert">{error}</p>}
      <div
        ref={root}
        className="structure-canvas"
        data-state={ready ? 'ready' : error ? 'unavailable' : 'loading'}
        style={{ position: "relative", height: 420 }}
      />
      <label>
        Representation
        <select
          aria-label="Representation"
          disabled={!ready || !annotationsReady || displayBusy}
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
            Registered parts (full model)
          </option>
          <option
            value="confidence"
            disabled={
              meta?.confidence_status !==
              "source_registered_not_scientific_approval"
            }
          >
            Registered pLDDT (full model)
          </option>
        </select>
      </label>
      <button
        disabled={!ready}
        onClick={() => plugin.current?.managers.camera.reset()}
      >
        Reset structure view
      </button>
      <button disabled={!ready || displayBusy} onClick={() => void exportImage()}>Export structure image</button>
      <p>
        Display {representation} / {colorMode}.{" "}
        {annotationsReady
          ? "Full-model annotations loaded; unannotated residues are gray."
          : "Loading full-model annotations…"}{" "}
        Continuous pLDDT color scale: red 0 to blue 100, no approval thresholds.
        Rotate/zoom/pan in the viewport; no new geometry or alignment is
        computed.
      </p>
      {allowReference &&
        meta?.overlays.map((overlay, index) => (
          <section key={index}>
            <button
              disabled={!ready || displayBusy}
              onClick={() =>
                void showOverlay(overlayIndex === index ? undefined : index)
              }
            >
              {overlayIndex === index ? "Hide" : "Show"} registered reference
              overlay {index + 1}
            </button>
            <p>
              Source {overlay.source_reference} · {overlay.source_tool}{" "}
              {overlay.source_tool_version} · Recorded reference overlay (Å).
            </p>
          </section>
        ))}
      {meta && (
        <>
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
                {meta.annotation_source_tool_version}
              </p>
              <p>Fusion FASTA {meta.fusion_sequence_id ?? "Not registered"}</p>
              <p>
                Registered display source, not scientific approval. Reference
                coordinates are not automatically aligned.
              </p>
            </details>
          )}
          <label>
            Chain
            <select
              aria-label="Chain"
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
          {(["pocket", "clash"] as const).map((kind) => (
            <button
              key={kind}
              disabled={
                !ready ||
                ![...annotationIndex.current.values()].some((a) => a[kind])
              }
              onClick={() => focusRegistered(kind)}
            >
              Select all registered {kind} residues (full model)
            </button>
          ))}
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
                const annotation = annotationIndex.current.get(
                  residueKey(
                    r.model,
                    r.chain,
                    r.residue_number,
                    r.insertion_code,
                  ),
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
                        ? `${annotation.reference_residue.model}:${annotation.reference_residue.chain}:${annotation.reference_residue.residue_number}${annotation.reference_residue.insertion_code}`
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
                  onClick={() => onReference(a.reference_file_id!)}
                >
                  Open registered reference {a.reference_residue?.chain}:
                  {a.reference_residue?.residue_number}
                </button>
              ))}
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
